import io
import os
import tempfile

import joblib
import numpy as np
from PIL import Image

from app.ai.disease_detector import predict_disease


def _make_colab_model_artifacts(tmp_path):
    model_dir = tmp_path / "ai_model"
    model_dir.mkdir()

    crop_labels = ["Tomato", "Corn"]
    disease_labels = ["Healthy", "Leaf Blight"]
    joblib.dump(crop_labels, model_dir / "crop_encoder.pkl")
    joblib.dump(disease_labels, model_dir / "disease_encoder.pkl")

    from app.ai import disease_detector as dd

    model = dd._build_torch_model(num_crops=len(crop_labels), num_diseases=len(disease_labels), pretrained=False)
    torch = __import__("torch")
    torch.save(model.state_dict(), model_dir / "leafnet_resnet50.pth")
    return model_dir


def test_predict_disease_loads_colab_pytorch_model(tmp_path):
    model_dir = _make_colab_model_artifacts(tmp_path)
    image_path = tmp_path / "leaf.png"
    image = Image.new("RGB", (224, 224), color=(160, 180, 120))
    image.save(image_path)

    result = predict_disease(
        image_path=str(image_path),
        model_path=str(model_dir / "leafnet_resnet50.pth"),
        confidence_threshold=0.10,
    )

    assert result.predicted_disease
    assert 0.0 <= result.confidence_score <= 1.0
    assert result.is_demo_prediction is False


def test_predict_disease_uses_checkpoint_shape_when_encoders_mismatch(tmp_path):
    model_dir = tmp_path / "ai_model"
    model_dir.mkdir()

    disease_labels = ["Healthy", "Leaf Blight", "Powdery Mildew"]
    joblib.dump(disease_labels, model_dir / "disease_encoder.pkl")
    joblib.dump(["Crop A", "Crop B", "Crop C", "Crop D", "Crop E", "Crop F", "Crop G", "Crop H", "Crop I", "Crop J", "Crop K", "Crop L", "Crop M", "Crop N", "Crop O", "Crop P", "Crop Q", "Crop R", "Crop S", "Crop T"], model_dir / "crop_encoder.pkl")

    import torch
    import torch.nn as nn
    from torchvision import models

    class MultiOutputResNet(nn.Module):
        def __init__(self):
            super().__init__()
            self.backbone = models.resnet50(weights=None)
            self.backbone.fc = nn.Identity()
            in_features = 2048
            self.crop_head = nn.Sequential(
                nn.Linear(in_features, 256),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.Linear(256, 18),
            )
            self.disease_head = nn.Sequential(
                nn.Linear(in_features, 256),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.Linear(256, len(disease_labels)),
            )

        def forward(self, x):
            features = self.backbone(x)
            return self.crop_head(features), self.disease_head(features)

    model = MultiOutputResNet()
    torch.save(model.state_dict(), model_dir / "leafnet_resnet50.pth")

    image_path = tmp_path / "leaf.png"
    Image.new("RGB", (224, 224), color=(160, 180, 120)).save(image_path)

    result = predict_disease(
        image_path=str(image_path),
        model_path=str(model_dir),
        confidence_threshold=0.10,
    )

    assert result.is_demo_prediction is False
    assert result.predicted_disease
