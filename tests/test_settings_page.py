from io import BytesIO

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


def test_farmer_can_save_profile_changes():
    app = make_app()
    with app.app_context():
        make_farmer(email="profile-save@example.com")

    with app.test_client() as client:
        client.post(
            "/auth/login",
            data={"email": "profile-save@example.com", "password": "StrongPass1"},
        )
        response = client.post(
            "/dashboard/settings",
            data={
                "name": "Updated Farmer",
                "email": "profile-save@example.com",
                "phone": "+250 788 000 000",
                "farm_location": "Kigali, Rwanda",
                "language": "French",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert "Profile changes saved." in response.get_data(as_text=True)

        from app.models.user import User
        user = User.query.filter_by(email="profile-save@example.com").one()
        assert user.name == "Updated Farmer"
        assert user.phone == "+250 788 000 000"
        assert user.farm_location == "Kigali, Rwanda"
        assert user.language == "French"


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


def test_farmer_can_save_notification_preferences():
    app = make_app()
    with app.app_context():
        make_farmer(email="notifications-save@example.com")

    with app.test_client() as client:
        client.post(
            "/auth/login",
            data={"email": "notifications-save@example.com", "password": "StrongPass1"},
        )
        response = client.post(
            "/dashboard/notifications",
            data={"disease_alert": "on", "email_delivery": "on"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert "Notification preferences saved." in response.get_data(as_text=True)

        from app.models.user import User
        user = User.query.filter_by(email="notifications-save@example.com").one()
        assert '"disease_alert": true' in user.notification_preferences
        assert '"community_reply": false' in user.notification_preferences


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


def test_treatment_details_page_has_valid_settings_link():
    app = make_app()
    with app.app_context():
        make_farmer()

    with app.test_client() as client:
        client.post(
            "/auth/login",
            data={"email": "farmer@example.com", "password": "StrongPass1"},
            follow_redirects=True,
        )

        response = client.get("/dashboard/treatment-details")
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert 'href="/dashboard/settings"' in html


def test_dashboard_and_help_pages_do_not_use_placeholder_links():
    app = make_app()
    with app.app_context():
        make_farmer()

    with app.test_client() as client:
        client.post(
            "/auth/login",
            data={"email": "farmer@example.com", "password": "StrongPass1"},
            follow_redirects=True,
        )

        dashboard_response = client.get("/dashboard/")
        dashboard_html = dashboard_response.get_data(as_text=True)
        assert dashboard_response.status_code == 200
        assert 'href="#"' not in dashboard_html

        help_response = client.get("/dashboard/help")
        help_html = help_response.get_data(as_text=True)
        assert help_response.status_code == 200
        assert 'href="#"' not in help_html


def test_landing_page_links_point_to_real_sections():
    app = make_app()

    with app.test_client() as client:
        response = client.get("/")
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert 'href="#demo"' not in html
        assert 'href="#treatment"' not in html
        assert 'href="#how-it-works"' in html
        assert 'href="#features"' in html


def test_new_farmer_dashboard_starts_at_zero_until_data_is_added():
    app = make_app()
    with app.app_context():
        make_farmer(email="newfarmer@example.com")

    with app.test_client() as client:
        client.post(
            "/auth/login",
            data={"email": "newfarmer@example.com", "password": "StrongPass1"},
            follow_redirects=True,
        )

        response = client.get("/dashboard/")
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "Total Crops" in html
        assert "Disease Detections" in html
        assert "0" in html
        assert "12,450" not in html
        assert "136" not in html


def test_farmer_creation_forms_use_consistent_required_field_ux():
    app = make_app()
    with app.app_context():
        make_farmer()

    with app.app_context():
        from app.models.farm import Farm
        from app.extensions import db
        farm = Farm(owner_id=1, name="Demo Farm", location="Kigali")
        db.session.add(farm)
        db.session.commit()
        farm_id = farm.id

    with app.test_client() as client:
        login_response = client.post(
            "/auth/login",
            data={"email": "farmer@example.com", "password": "StrongPass1"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        response = client.get("/farms/new")
        assert response.status_code == 200
        farm_html = response.get_data(as_text=True)
        assert "Required fields are marked with *" in farm_html
        assert 'name="name"' in farm_html and 'required' in farm_html
        assert 'name="location"' in farm_html and 'required' in farm_html

        crop_response = client.get(f"/farms/{farm_id}/crops/new")
        assert crop_response.status_code == 200
        crop_html = crop_response.get_data(as_text=True)
        assert "Required fields are marked with *" in crop_html
        assert 'name="crop_type"' in crop_html and 'required' in crop_html


def test_farmer_can_create_farm_with_details_and_manage_page_loads():
    app = make_app()
    with app.app_context():
        make_farmer(email="detailfarmer@example.com")

    with app.test_client() as client:
        client.post(
            "/auth/login",
            data={"email": "detailfarmer@example.com", "password": "StrongPass1"},
            follow_redirects=True,
        )

        response = client.post(
            "/farms/new",
            data={
                "name": "Green Valley",
                "location": "Kigali",
                "farm_size": "24.5 hectares",
                "description": "Mixed vegetables and passion fruit farm.",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "Farm created." in html

        manage_response = client.get("/farms/1/manage")
        assert manage_response.status_code == 200
        manage_html = manage_response.get_data(as_text=True)
        assert "Manage Farm" in manage_html
        assert "Farm Details" in manage_html


def test_farmer_can_add_crop_with_description_and_variety():
    app = make_app()
    with app.app_context():
        farmer = make_farmer(email="cropfarmer@example.com")
        from app.models.farm import Farm
        farm = Farm(owner_id=farmer.id, name="North Farm", location="Rwamagana")
        db.session.add(farm)
        db.session.commit()

    with app.test_client() as client:
        client.post(
            "/auth/login",
            data={"email": "cropfarmer@example.com", "password": "StrongPass1"},
            follow_redirects=True,
        )

        response = client.post(
            "/farms/1/crops/new",
            data={
                "crop_type": "Tomatoes",
                "variety": "Roma",
                "description": "Strong fruiting variety for export market.",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "Crop added." in html


def test_farmer_can_upload_crop_picture_from_add_crop_form():
    app = make_app()
    with app.app_context():
        farmer = make_farmer(email="photo farmer@example.com")
        from app.models.farm import Farm
        farm = Farm(owner_id=farmer.id, name="Photo Farm", location="Musanze")
        db.session.add(farm)
        db.session.commit()

    with app.test_client() as client:
        client.post(
            "/auth/login",
            data={"email": "photo farmer@example.com", "password": "StrongPass1"},
            follow_redirects=True,
        )

        response = client.post(
            "/farms/1/crops/new",
            data={
                "crop_type": "Beans",
                "photo": (BytesIO(b"fake-jpeg-content"), "beans.jpg"),
            },
            content_type="multipart/form-data",
        )
        assert response.status_code == 302

        from app.models.crop import Crop
        crop = Crop.query.filter_by(farm_id=1).one()
        assert crop.image_path is not None
        assert crop.image_path.startswith("images/uploads/")


def test_manage_farm_add_crop_with_description_returns_confirmation():
    app = make_app()
    with app.app_context():
        farmer = make_farmer(email="manage description@example.com")
        from app.models.farm import Farm
        farm = Farm(owner_id=farmer.id, name="Managed Farm", location="Kigali")
        db.session.add(farm)
        db.session.commit()

    with app.test_client() as client:
        client.post(
            "/auth/login",
            data={"email": "manage description@example.com", "password": "StrongPass1"},
        )
        response = client.post(
            "/farms/1/manage",
            data={
                "action": "add_crop",
                "crop_type": "Carrots",
                "planting_date": "2026-09-19",
                "description": "Grows well in the north field.",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert "Crop added to the farm." in response.get_data(as_text=True)

        from app.models.crop import Crop
        crop = Crop.query.filter_by(farm_id=1).one()
        assert crop.planting_date.isoformat() == "2026-09-19"


def test_oversized_crop_picture_returns_helpful_error_page():
    app = make_app()
    with app.app_context():
        farmer = make_farmer(email="large photo@example.com")
        from app.models.farm import Farm
        farm = Farm(owner_id=farmer.id, name="Large Photo Farm", location="Kigali")
        db.session.add(farm)
        db.session.commit()

    with app.test_client() as client:
        client.post(
            "/auth/login",
            data={"email": "large photo@example.com", "password": "StrongPass1"},
        )
        response = client.post(
            "/farms/1/crops/new",
            data={
                "crop_type": "Large Photo Crop",
                "photo": (BytesIO(b"x" * (17 * 1024 * 1024)), "large.jpg"),
            },
            content_type="multipart/form-data",
        )
        assert response.status_code == 413
        assert "That image is too large" in response.get_data(as_text=True)


def test_buyer_marketplace_page_matches_clean_dashboard_layout():
    app = make_app()
    with app.app_context():
        buyer = User(name="Alex Kengne", email="buyer@example.com", role="buyer")
        buyer.set_password("StrongPass1")
        db.session.add(buyer)
        db.session.commit()

    with app.test_client() as client:
        client.post(
            "/auth/login",
            data={"email": "buyer@example.com", "password": "StrongPass1"},
            follow_redirects=True,
        )

        response = client.get("/marketplace/")
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "AgroMarket" in html
        assert "Search crops, farms, location..." in html
        assert "Home" in html
        assert "Market" in html
