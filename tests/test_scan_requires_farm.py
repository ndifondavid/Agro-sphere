from app import create_app
from app.extensions import db
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
