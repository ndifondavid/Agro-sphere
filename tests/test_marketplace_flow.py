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


def make_buyer(email="buyer@example.com", password="StrongPass1"):
    user = User(name="Buyer One", email=email, role="buyer")
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def test_farmer_can_create_market_listing_visible_to_buyers():
    app = make_app()
    with app.app_context():
        farmer = make_farmer()
        make_buyer()
        farm = Farm(owner_id=farmer.id, name="Green Valley Farm", location="Nairobi")
        db.session.add(farm)
        db.session.commit()
        crop = Crop(farm_id=farm.id, crop_type="Tomatoes")
        db.session.add(crop)
        db.session.commit()
        farm_id = farm.id
        crop_id = crop.id

    with app.test_client() as farmer_client:
        farmer_client.post(
            "/auth/login",
            data={"email": "farmer@example.com", "password": "StrongPass1"},
            follow_redirects=True,
        )

        response = farmer_client.post(
            "/marketplace/new",
            data={
                "farm_id": str(farm_id),
                "crop_id": str(crop_id),
                "quantity": "120",
                "price": "500",
                "harvest_date": "2024-10-15",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"Listing created" in response.data or b"Tomatoes" in response.data

    with app.test_client() as buyer_client:
        buyer_login = buyer_client.post(
            "/auth/login",
            data={"email": "buyer@example.com", "password": "StrongPass1"},
            follow_redirects=True,
        )
        assert buyer_login.status_code == 200

        buyer_page = buyer_client.get("/marketplace/")
        assert buyer_page.status_code == 200
        assert b"Tomatoes" in buyer_page.data
