"""
AI Tier inference wrapper (SDS Section 2, Section 5.1, Design Constraints Section 8).

This module supports two trained-model formats:
1) legacy TensorFlow/Keras H5/keras files; and
2) the Colab-trained PyTorch artifact bundle saved as:
   - leafnet_resnet50.pth
   - disease_encoder.pkl (and optionally crop_encoder.pkl)

The Application Tier (app/routes/scan_routes.py) never touches ML libraries
directly; it only calls `predict_disease()` defined here, keeping the AI Tier
swappable/retrainable without touching web routes.
"""
import os
from dataclasses import dataclass
from typing import Optional

# Model is loaded lazily so the web app can start even before a trained
# model artifact exists on disk (useful for early sprints / local dev).
_model = None

DISEASE_RECOMMENDATIONS = {
    "Healthy": "No action needed. Continue routine monitoring.",
    "Leaf Blight": "Remove and destroy infected leaves; apply an appropriate fungicide.",
    "Powdery Mildew": "Improve air circulation and apply sulfur-based fungicide.",
    "Rust": "Prune infected foliage and apply a recommended rust-control fungicide.",
    "Leaf Spot": "Remove spotted leaves and use a protective fungicide where appropriate.",
    "Mosaic Virus": "Remove severely infected plants and avoid spreading sap between crops.",
    "Root Rot": "Improve drainage and avoid overwatering; remove affected plants.",
    "Unknown": "Confidence too low for a reliable diagnosis; consider rescanning with a clearer photo.",
}


def normalize_disease_name(value: Optional[str]) -> str:
    if value is None:
        return "Unknown"

    normalized = str(value).strip()
    if not normalized:
        return "Unknown"

    lowered = normalized.lower()
    if "healthy" in lowered:
        return "Healthy"
    if "powder" in lowered or "mildew" in lowered:
        return "Powdery Mildew"
    if "blight" in lowered:
        return "Leaf Blight"
    if "rust" in lowered:
        return "Rust"
    if "spot" in lowered:
        return "Leaf Spot"
    if "mosaic" in lowered or "virus" in lowered:
        return "Mosaic Virus"
    if "rot" in lowered:
        return "Root Rot"
    if "diseased" in lowered:
        return "Leaf Blight"
    if "unknown" in lowered:
        return "Unknown"
    return normalized


@dataclass
class PredictionResult:
    predicted_disease: str
    confidence_score: float
    recommendation: str
    is_demo_prediction: bool = False


class TorchModelWrapper:
    """Adapter so a PyTorch state_dict model can be used like a Keras model."""

    def __init__(self, model, label_names):
        self.model = model
        self.label_names = list(label_names)

    def predict(self, img_array):
        import numpy as np
        import torch

        tensor = torch.from_numpy(np.asarray(img_array, dtype=np.float32))
        if tensor.ndim == 4 and tensor.shape[0] == 1:
            tensor = tensor[0]

        # Keras-style input is (H, W, C); PyTorch expects (C, H, W).
        tensor = tensor.permute(2, 0, 1)

        mean = torch.tensor([0.485, 0.456, 0.406], dtype=tensor.dtype)
        std = torch.tensor([0.229, 0.224, 0.225], dtype=tensor.dtype)
        tensor = (tensor - mean[:, None, None]) / std[:, None, None]
        tensor = tensor.unsqueeze(0)

        self.model.eval()
        with torch.no_grad():
            outputs = self.model(tensor)
            if isinstance(outputs, (tuple, list)):
                disease_logits = outputs[1]
            else:
                disease_logits = outputs
            probabilities = torch.softmax(disease_logits, dim=1)

        probabilities = probabilities[0].cpu().numpy()
        if len(self.label_names) > 0 and len(probabilities) != len(self.label_names):
            probabilities = probabilities[: len(self.label_names)]

        return np.asarray([probabilities], dtype=np.float32)


def _resolve_model_artifact(model_path: str):
    if not model_path:
        return None

    if os.path.isdir(model_path):
        for candidate in (
            os.path.join(model_path, "leafnet_resnet50.pth"),
            os.path.join(model_path, "leafnet_resnet50.pt"),
            os.path.join(model_path, "disease_model.h5"),
            os.path.join(model_path, "model.h5"),
        ):
            if os.path.exists(candidate):
                return candidate
        return None

    if os.path.exists(model_path):
        return model_path

    parent_dir = os.path.dirname(model_path)
    if os.path.isdir(parent_dir):
        for candidate in (
            os.path.join(parent_dir, "leafnet_resnet50.pth"),
            os.path.join(parent_dir, "leafnet_resnet50.pt"),
            os.path.join(parent_dir, "disease_model.h5"),
            os.path.join(parent_dir, "model.h5"),
        ):
            if os.path.exists(candidate):
                return candidate

    return None


def _load_disease_labels(model_dir: str):
    labels_path = os.path.join(model_dir, "disease_encoder.pkl")
    if not os.path.exists(labels_path):
        return list(DISEASE_RECOMMENDATIONS.keys())

    try:
        import joblib

        labels = joblib.load(labels_path)
        if isinstance(labels, (list, tuple)):
            return [str(v) for v in labels]
        if hasattr(labels, "classes_"):
            return [str(v) for v in labels.classes_]
    except Exception:
        pass

    return list(DISEASE_RECOMMENDATIONS.keys())


def _build_torch_model(num_crops: int, num_diseases: int, pretrained: bool = False):
    import torch
    import torch.nn as nn
    from torchvision import models

    class MultiOutputResNet(nn.Module):
        def __init__(self, num_crops, num_diseases):
            super().__init__()
            self.backbone = models.resnet50(weights=models.ResNet50_Weights.DEFAULT if pretrained else None)
            for param in self.backbone.parameters():
                param.requires_grad = False

            in_features = self.backbone.fc.in_features
            self.backbone.fc = nn.Identity()

            self.crop_head = nn.Sequential(
                nn.Linear(in_features, 256),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.Linear(256, num_crops),
            )

            self.disease_head = nn.Sequential(
                nn.Linear(in_features, 256),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.Linear(256, num_diseases),
            )

        def forward(self, x):
            features = self.backbone(x)
            return self.crop_head(features), self.disease_head(features)

    return MultiOutputResNet(num_crops, num_diseases)


def _load_model(model_path: str):
    global _model
    if _model is not None:
        return _model

    resolved_path = _resolve_model_artifact(model_path)
    if not resolved_path:
        return None

    ext = os.path.splitext(resolved_path)[1].lower()

    if ext in {".pth", ".pt"}:
        try:
            import joblib
            import torch

            model_dir = os.path.dirname(resolved_path)
            disease_labels = _load_disease_labels(model_dir)

            state_dict = torch.load(resolved_path, map_location="cpu")
            if isinstance(state_dict, dict) and "model_state_dict" in state_dict:
                state_dict = state_dict["model_state_dict"]

            crop_head_key = None
            disease_head_key = None
            for key in state_dict.keys():
                if key.startswith("crop_head") and key.endswith("weight"):
                    if key.endswith(".3.weight") or crop_head_key is None:
                        crop_head_key = key
                if key.startswith("disease_head") and key.endswith("weight"):
                    if key.endswith(".3.weight") or disease_head_key is None:
                        disease_head_key = key

            if crop_head_key is not None:
                num_crops = int(state_dict[crop_head_key].shape[0])
            elif os.path.exists(os.path.join(model_dir, "crop_encoder.pkl")):
                crop_classes = joblib.load(os.path.join(model_dir, "crop_encoder.pkl"))
                if hasattr(crop_classes, "classes_"):
                    num_crops = len(crop_classes.classes_)
                else:
                    num_crops = len(crop_classes)
            else:
                num_crops = 1

            if disease_head_key is not None:
                num_diseases = int(state_dict[disease_head_key].shape[0])
            else:
                num_diseases = len(disease_labels)

            model = _build_torch_model(num_crops=num_crops, num_diseases=num_diseases, pretrained=False)
            model.load_state_dict(state_dict, strict=False)

            _model = TorchModelWrapper(model, disease_labels)
            return _model
        except Exception:
            _model = None
            return None

    try:
        from tensorflow.keras.models import load_model  # imported lazily (heavy dependency)

        _model = load_model(resolved_path)
        return _model
    except ImportError:
        # TensorFlow not installed in this environment; caller falls back to a demo result.
        _model = None
        return None


def _demo_prediction() -> PredictionResult:
    return PredictionResult(
        predicted_disease="Leaf Blight",
        confidence_score=0.924,
        recommendation="Remove infected leaves and dispose of them away from healthy plants. Apply a copper-based fungicide and improve airflow around the crop.",
        is_demo_prediction=True,
    )


def predict_disease(image_path: str, model_path: str, confidence_threshold: float = 0.60) -> PredictionResult:
    """
    Runs inference on a single leaf image and returns a structured prediction.

    Mirrors FR-3.1 - FR-3.6: the image is preprocessed, passed through the
    model, and the result (disease name + confidence + recommendation) is
    returned for the Application Tier to persist to the Scan table.
    """
    model = _load_model(model_path)

    if model is None or not _resolve_model_artifact(model_path):
        # Demo fallback for early project stages where the trained disease model is not yet available.
        return _demo_prediction()

    import numpy as np
    from PIL import Image
    from PIL import UnidentifiedImageError

    try:
        img = Image.open(image_path).convert("RGB")
        img = img.resize((224, 224))
        img_array = np.asarray(img, dtype=np.float32) / 255.0
        img_array = np.expand_dims(img_array, axis=0)
    except (UnidentifiedImageError, OSError, ValueError):
        return _demo_prediction()

    predictions = model.predict(img_array)
    class_index = int(np.argmax(predictions[0]))
    confidence = float(predictions[0][class_index])

    class_labels = list(DISEASE_RECOMMENDATIONS.keys())
    if hasattr(model, "label_names") and model.label_names:
        class_labels = model.label_names

    disease_name = class_labels[class_index] if class_index < len(class_labels) else "Unknown"
    disease_name = normalize_disease_name(disease_name)

    if confidence < confidence_threshold:
        disease_name = "Unknown"

    recommendation = DISEASE_RECOMMENDATIONS.get(disease_name)
    if recommendation is None:
        recommendation = DISEASE_RECOMMENDATIONS["Unknown"]

    return PredictionResult(
        predicted_disease=disease_name,
        confidence_score=round(confidence, 4),
        recommendation=recommendation,
        is_demo_prediction=False,
    )
