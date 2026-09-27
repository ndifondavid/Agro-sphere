from datetime import date

from app import create_app
from app.extensions import db
from app.models.crop import Crop
from app.models.farm import Farm
from app.models.listing import Listing
from app.models.user import User


def make_app():
    app = create_app("config.TestingConfig")
    with app.app_context():
        db.drop_all()
        db.create_all()
    return app


def make_admin(email="admin@example.com", password="StrongPass1"):
    user = User(name="Admin One", email=email, role="admin")
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def make_buyer(email="buyer@example.com", password="StrongPass1"):
    user = User(name="Buyer One", email=email, role="buyer")
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def test_admin_can_deactivate_and_reactivate_user():
    app = make_app()
    with app.app_context():
        make_admin()
        buyer = make_buyer()
        buyer_id = buyer.id

    with app.test_client() as admin_client:
        admin_client.post(
            "/auth/login",
            data={"email": "admin@example.com", "password": "StrongPass1"},
            follow_redirects=True,
        )

        response = admin_client.post(f"/admin/users/{buyer_id}/toggle-status", follow_redirects=True)
        assert response.status_code == 200
        with app.app_context():
            assert User.query.get(buyer_id).is_active is False

        with app.test_client() as buyer_client:
            login_response = buyer_client.post(
                "/auth/login",
                data={"email": "buyer@example.com", "password": "StrongPass1"},
                follow_redirects=True,
            )
            assert login_response.status_code == 200
            assert b"deactivated" in login_response.data.lower()

        response = admin_client.post(f"/admin/users/{buyer_id}/toggle-status", follow_redirects=True)
        assert response.status_code == 200
        with app.app_context():
            assert User.query.get(buyer_id).is_active is True


def test_admin_can_remove_marketplace_listing():
    app = make_app()
    with app.app_context():
        admin = make_admin(email="admin2@example.com")
        farmer = User(name="Farmer One", email="farmer@example.com", role="farmer")
        farmer.set_password("StrongPass1")
        db.session.add(farmer)
        db.session.commit()

        farm = Farm(owner_id=farmer.id, name="Green Valley Farm", location="Nairobi")
        db.session.add(farm)
        db.session.commit()

        crop = Crop(farm_id=farm.id, crop_type="Tomatoes")
        db.session.add(crop)
        db.session.commit()

        listing = Listing(
            farmer_id=farmer.id,
            crop_type=crop.crop_type,
            harvest_date=date(2026, 9, 15),
            quantity=120,
            price=2500,
            package_size="medium basket",
            package_unit="basket",
            availability_status="available",
        )
        db.session.add(listing)
        db.session.commit()
        listing_id = listing.id

    with app.test_client() as admin_client:
        admin_client.post(
            "/auth/login",
            data={"email": "admin2@example.com", "password": "StrongPass1"},
            follow_redirects=True,
        )

        response = admin_client.post(f"/admin/listings/{listing_id}/delete", follow_redirects=True)
        assert response.status_code == 200
        assert Listing.query.get(listing_id) is None
