"""
AI Tier inference wrapper (SDS Section 2, Section 5.1, Design Constraints Section 8).

This module wraps the trained TensorFlow/Keras model (a thin wrapper around a
pretrained network via transfer learning, per the 14-day timeline constraint).
The Application Tier (app/routes/scan_routes.py) never touches TensorFlow
directly; it only calls `predict_disease()` defined here, keeping the AI Tier
swappable/retrainable without touching web routes.

Sequence (SDS Section 5.1 / Figure 5):
    Farmer submits photo -> Flask validates -> AI Tier predicts -> result
    is persisted to the Scan table -> diagnosis is displayed.
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
    "Unknown": "Confidence too low for a reliable diagnosis; consider rescanning with a clearer photo.",
}


@dataclass
class PredictionResult:
    predicted_disease: str
    confidence_score: float
    recommendation: str


def _load_model(model_path: str):
    global _model
    if _model is not None:
        return _model
    try:
        from tensorflow.keras.models import load_model  # imported lazily (heavy dependency)

        if os.path.exists(model_path):
            _model = load_model(model_path)
    except ImportError:
        # TensorFlow not installed in this environment; caller falls back to a demo result.
        _model = None
    return _model


def _demo_prediction() -> PredictionResult:
    return PredictionResult(
        predicted_disease="Leaf Blight",
        confidence_score=0.924,
        recommendation="Remove infected leaves and dispose of them away from healthy plants. Apply a copper-based fungicide and improve airflow around the crop.",
    )


def predict_disease(image_path: str, model_path: str, confidence_threshold: float = 0.60) -> PredictionResult:
    """
    Runs inference on a single leaf image and returns a structured prediction.

    Mirrors FR-3.1 - FR-3.6: the image is preprocessed, passed through the
    model, and the result (disease name + confidence + recommendation) is
    returned for the Application Tier to persist to the Scan table.
    """
    model = _load_model(model_path)

    if model is None or not os.path.exists(model_path):
        # Demo fallback for early project stages where the trained disease model is not yet available.
        return _demo_prediction()

    from tensorflow.keras.preprocessing import image as keras_image
    import numpy as np

    img = keras_image.load_img(image_path, target_size=(224, 224))
    img_array = keras_image.img_to_array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)

    predictions = model.predict(img_array)
    class_index = int(np.argmax(predictions[0]))
    confidence = float(predictions[0][class_index])

    class_labels = list(DISEASE_RECOMMENDATIONS.keys())
    disease_name = class_labels[class_index] if class_index < len(class_labels) else "Unknown"

    if confidence < confidence_threshold:
        disease_name = "Unknown"

    return PredictionResult(
        predicted_disease=disease_name,
        confidence_score=round(confidence, 4),
        recommendation=DISEASE_RECOMMENDATIONS.get(disease_name, DISEASE_RECOMMENDATIONS["Unknown"]),
    )
