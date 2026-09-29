import io

from app import create_app
from app.extensions import db
from app.models.crop import Crop
from app.models.farm import Farm
from app.models.user import User


def make_app():
    app = create_app("config.TestingConfig")
    with app.app_context():
        db.drop_all()
        db.create_all()
    return app


def make_farmer(email="farmer@example.com", password="StrongPass1"):
    user = User(name="Farmer One", email=email, role="farmer")
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def test_scan_redirects_to_create_farm_when_user_has_no_farm():
    app = make_app()
    with app.app_context():
        make_farmer()

    with app.test_client() as client:
        response = client.post(
            "/auth/login",
            data={"email": "farmer@example.com", "password": "StrongPass1"},
            follow_redirects=True,
        )
        assert response.status_code == 200

        scan_response = client.get("/scan/", follow_redirects=True)
        assert scan_response.status_code == 200
        html = scan_response.get_data(as_text=True).lower()
        assert "create a farm" in html or "farm" in html


def test_scan_redirects_to_farms_when_user_has_farm_but_no_crops():
    app = make_app()
    with app.app_context():
        user = make_farmer(email="farmer2@example.com")
        from app.models.farm import Farm
        db.session.add(Farm(owner_id=user.id, name="Sunrise Farm", location="Nairobi"))
        db.session.commit()

    with app.test_client() as client:
        client.post(
            "/auth/login",
            data={"email": "farmer2@example.com", "password": "StrongPass1"},
            follow_redirects=True,
        )

        response = client.get("/scan/", follow_redirects=True)
        assert response.status_code == 200
        html = response.get_data(as_text=True).lower()
        assert "crop" in html or "farm" in html


def test_scan_history_normalizes_windows_style_image_paths():
    app = make_app()
    with app.app_context():
        user = make_farmer(email="windowspath@example.com")
        from app.models.scan import Scan

        farm = Farm(owner_id=user.id, name="Sunrise Farm", location="Nairobi")
        db.session.add(farm)
        db.session.flush()

        crop = Crop(farm_id=farm.id, crop_type="Tomatoes")
        db.session.add(crop)
        db.session.flush()

        scan = Scan(
            crop_id=crop.id,
            image_path=r"images\uploads\demo.jpg",
            predicted_disease="Leaf Blight",
            confidence_score=88.5,
            recommendation="Treat with copper spray.",
        )
        db.session.add(scan)
        db.session.commit()

    with app.test_client() as client:
        client.post(
            "/auth/login",
            data={"email": "windowspath@example.com", "password": "StrongPass1"},
            follow_redirects=True,
        )

        response = client.get("/scan/history")
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "images/uploads/demo.jpg" in html
        assert "images\\uploads\\demo.jpg" not in html


def test_scan_shows_demo_mode_banner_when_model_fallback_is_used():
    app = make_app()
    with app.app_context():
        farmer = make_farmer(email="demo-mode@example.com")
        farm = Farm(owner_id=farmer.id, name="Demo Valley Farm", location="Kigali")
        db.session.add(farm)
        db.session.commit()
        crop = Crop(farm_id=farm.id, crop_type="Tomato")
        db.session.add(crop)
        db.session.commit()
        crop_id = crop.id

    with app.test_client() as client:
        client.post(
            "/auth/login",
            data={"email": "demo-mode@example.com", "password": "StrongPass1"},
            follow_redirects=True,
        )

        response = client.post(
            "/scan/",
            data={
                "crop_id": str(crop_id),
                "photo": (io.BytesIO(b"fake-image-data"), "leaf.png"),
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "Demo Mode — no trained model loaded" in html


def test_predict_disease_normalizes_model_labels_to_known_names(tmp_path):
    model_dir = tmp_path / "ai_model"
    model_dir.mkdir()

    import joblib
    import torch
    import torch.nn as nn
    from torchvision import models

    disease_labels = ["Healthy", "Blight", "Rust"]
    joblib.dump(disease_labels, model_dir / "disease_encoder.pkl")
    joblib.dump(["Crop A", "Crop B", "Crop C"], model_dir / "crop_encoder.pkl")

    class MultiOutputResNet(nn.Module):
        def __init__(self):
            super().__init__()
            self.backbone = models.resnet50(weights=None)
            self.backbone.fc = nn.Identity()
            in_features = 2048
            self.crop_head = nn.Sequential(
                nn.Linear(in_features, 32),
                nn.ReLU(),
                nn.Linear(32, 3),
            )
            self.disease_head = nn.Sequential(
                nn.Linear(in_features, 32),
                nn.ReLU(),
                nn.Linear(32, len(disease_labels)),
            )

        def forward(self, x):
            features = self.backbone(x)
            return self.crop_head(features), self.disease_head(features)

    model = MultiOutputResNet()
    torch.save(model.state_dict(), model_dir / "leafnet_resnet50.pth")

    image_path = tmp_path / "leaf.png"
    from PIL import Image
    Image.new("RGB", (224, 224), color=(120, 160, 100)).save(image_path)

    result = __import__("app.ai.disease_detector", fromlist=["predict_disease"]).predict_disease(
        image_path=str(image_path),
        model_path=str(model_dir),
        confidence_threshold=0.10,
    )

    assert result.predicted_disease in {"Healthy", "Leaf Blight", "Rust"}
    assert result.recommendation != "Confidence too low for a reliable diagnosis; consider rescanning with a clearer photo."


def test_dashboard_recent_scan_card_shows_image_and_chart_rate(tmp_path):
    app = make_app()
    with app.app_context():
        user = make_farmer(email="dashboard-check@example.com")
        farm = Farm(owner_id=user.id, name="Green Valley", location="Kisumu")
        db.session.add(farm)
        db.session.commit()
        crop = Crop(farm_id=farm.id, crop_type="Tomato")
        db.session.add(crop)
        db.session.commit()
        scan = __import__("app.models.scan", fromlist=["Scan"]).Scan(
            crop_id=crop.id,
            image_path="images/uploads/demo.jpg",
            predicted_disease="Rust",
            confidence_score=0.87,
            recommendation="Monitor and spray.",
        )
        db.session.add(scan)
        db.session.commit()

    with app.test_client() as client:
        client.post(
            "/auth/login",
            data={"email": "dashboard-check@example.com", "password": "StrongPass1"},
            follow_redirects=True,
        )

        response = client.get("/dashboard/")
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "scan-thumb" in html
        assert "images/uploads/demo.jpg" in html
        assert "--healthy-rate" in html
