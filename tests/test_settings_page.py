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


def test_settings_page_loads_for_authenticated_farmer():
    app = make_app()
    with app.app_context():
        make_farmer()

    with app.test_client() as client:
        client.post(
            "/auth/login",
            data={"email": "farmer@example.com", "password": "StrongPass1"},
            follow_redirects=True,
        )

        response = client.get("/dashboard/settings")
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "Settings" in html
        assert "Profile" in html


def test_notifications_page_loads_for_authenticated_farmer():
    app = make_app()
    with app.app_context():
        make_farmer()

    with app.test_client() as client:
        client.post(
            "/auth/login",
            data={"email": "farmer@example.com", "password": "StrongPass1"},
            follow_redirects=True,
        )

        response = client.get("/dashboard/notifications")
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "Notifications" in html
        assert "Alert Types" in html


def test_help_page_loads_for_authenticated_farmer():
    app = make_app()
    with app.app_context():
        make_farmer()

    with app.test_client() as client:
        client.post(
            "/auth/login",
            data={"email": "farmer@example.com", "password": "StrongPass1"},
            follow_redirects=True,
        )

        response = client.get("/dashboard/help")
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "Help & Support" in html
        assert "Frequently Asked Questions" in html
