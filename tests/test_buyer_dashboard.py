from app import create_app
from app.extensions import db
from app.models.user import User


def make_app():
    app = create_app("config.TestingConfig")
    with app.app_context():
        db.drop_all()
        db.create_all()
    return app


def test_buyer_dashboard_route_loads():
    app = make_app()
    with app.app_context():
        user = User(name="Buyer One", email="buyer@example.com", role="buyer")
        user.set_password("StrongPass1")
        db.session.add(user)
        db.session.commit()

    with app.test_client() as client:
        login = client.post(
            "/auth/login",
            data={"email": "buyer@example.com", "password": "StrongPass1"},
            follow_redirects=True,
        )
        assert login.status_code == 200

        dashboard = client.get("/marketplace/dashboard")
        assert dashboard.status_code == 200
        assert b"Buyer Dashboard" in dashboard.data
