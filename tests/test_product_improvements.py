from datetime import datetime

import pytest

from app import create_app
from app.extensions import db
from app.models.crop import Crop
from app.models.farm import Farm
from app.models.listing import Listing
from app.models.reservation import Reservation
from app.models.scan import Scan
from app.models.user import User


def make_app():
    app = create_app("config.TestingConfig")
    with app.app_context():
        db.drop_all()
        db.create_all()
    return app


def make_user(email, role):
    user = User(name=role.title(), email=email, role=role)
    user.set_password("StrongPass1")
    db.session.add(user)
    db.session.commit()
    return user


def login(client, email):
    return client.post(
        "/auth/login",
        data={"email": email, "password": "StrongPass1"},
        follow_redirects=True,
    )


def test_buyer_marketplace_does_not_show_farmer_sidebar_or_new_scan():
    app = make_app()
    with app.app_context():
        make_user("buyer@example.com", "buyer")

    with app.test_client() as client:
        login(client, "buyer@example.com")
        response = client.get("/marketplace/")
        html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "New Scan" not in html
    assert "Sidebar navigation" not in html
    assert "Reservations" in html


def test_farm_card_reports_recent_disease_attention():
    app = make_app()
    with app.app_context():
        farmer = make_user("farmer@example.com", "farmer")
        farm = Farm(owner_id=farmer.id, name="Green Valley", location="Kigali")
        db.session.add(farm)
        db.session.commit()
        crop = Crop(farm_id=farm.id, crop_type="Tomatoes")
        db.session.add(crop)
        db.session.commit()
        db.session.add(
            Scan(
                crop_id=crop.id,
                image_path="images/uploads/leaf.jpg",
                predicted_disease="Late blight",
                confidence_score=0.91,
                timestamp=datetime.utcnow(),
            )
        )
        db.session.commit()

    with app.test_client() as client:
        login(client, "farmer@example.com")
        response = client.get("/farms/")

    assert response.status_code == 200
    assert b"Needs attention" in response.data


def test_duplicate_active_reservation_is_rejected():
    app = make_app()
    with app.app_context():
        farmer = make_user("farmer@example.com", "farmer")
        buyer = make_user("buyer@example.com", "buyer")
        buyer_id = buyer.id
        listing = Listing(
            farmer_id=farmer.id,
            crop_type="Tomatoes",
            harvest_date=datetime(2026, 10, 1).date(),
            quantity=10,
            package_size="medium basket",
            package_unit="basket",
            price=500,
        )
        db.session.add(listing)
        db.session.commit()
        listing_id = listing.id

    with app.test_client() as client:
        login(client, "buyer@example.com")
        first = client.post(f"/marketplace/{listing_id}/reserve", follow_redirects=True)
        listing = Listing.query.get(listing_id)
        listing.availability_status = "available"
        db.session.commit()
        second = client.post(f"/marketplace/{listing_id}/reserve", follow_redirects=True)

    assert first.status_code == 200
    assert second.status_code == 200
    assert b"already have an active reservation" in second.data
    with app.app_context():
        assert Reservation.query.filter_by(buyer_id=buyer_id, listing_id=listing_id).count() == 1


def test_production_config_requires_secret_and_database(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app("config.ProductionConfig")
