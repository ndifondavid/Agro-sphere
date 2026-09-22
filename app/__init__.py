"""
AgroSphere application factory.

Architecture (per AgroSphere_SDS.docx, Section 2 - System Architecture Design):
    Client Tier        -> browser-based UI (Jinja2 templates + Bootstrap, app/templates, app/static)
    Application Tier   -> Flask backend, organized into route groups ("blueprints") by feature (app/routes)
    AI Tier             -> separate inference wrapper around the trained TensorFlow/Keras model (app/ai)
    Data Tier           -> SQLite database accessed through SQLAlchemy models (app/models)

All client requests pass through this Application Tier; the browser never talks to the
AI model or the database directly, keeping access control centralized (FR-1.4, NFR-2.2).
"""
from flask import Flask, render_template
from flask_login import current_user
import json

from app.extensions import db, login_manager, migrate


def create_app(config_object: str = "config.DevelopmentConfig") -> Flask:
    """Application factory used by run.py / wsgi entry points and tests."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object)
    if config_object == "config.ProductionConfig":
        if not app.config.get("SECRET_KEY") or app.config["SECRET_KEY"] == "dev-secret-key-change-me":
            raise RuntimeError("SECRET_KEY must be set in production.")
        if not app.config.get("SQLALCHEMY_DATABASE_URI"):
            raise RuntimeError("DATABASE_URL must be set in production.")

    # Initialize extensions (Data Tier wiring)
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # Import models before create_all so SQLAlchemy knows every SDS table.
    from app import models  # noqa: F401

    register_blueprints(app)

    @app.context_processor
    def inject_header_notifications():
        if not current_user.is_authenticated or not (current_user.is_farmer() or current_user.is_buyer()):
            return {"header_notifications": []}

        from app.models.crop import Crop
        from app.models.farm import Farm
        from app.models.message import Message
        from app.models.listing import Listing
        from app.models.reservation import Reservation
        from app.models.scan import Scan

        notifications = []
        preferences = json.loads(current_user.notification_preferences or "{}") if current_user.notification_preferences else {}
        if current_user.is_farmer():
            scans = (
                Scan.query.join(Crop, Scan.crop_id == Crop.id)
                .join(Farm, Crop.farm_id == Farm.id)
                .filter(Farm.owner_id == current_user.id)
                .order_by(Scan.timestamp.desc())
                .limit(5)
                .all()
            )
            notifications.extend(
                {
                    "title": f"{scan.crop.crop_type} · {scan.crop.farm.name}",
                    "detail": f"{scan.predicted_disease} · {scan.confidence_score * 100:.0f}% confidence",
                    "timestamp": scan.timestamp,
                    "kind": "warning" if "healthy" not in scan.predicted_disease.lower() else "healthy",
                }
                for scan in scans
                if "healthy" in scan.predicted_disease.lower() or preferences.get("disease_alert", True)
            )

            reservations = (
                Reservation.query.join(Reservation.listing)
                .filter(Listing.farmer_id == current_user.id)
                .order_by(Reservation.timestamp.desc())
                .limit(5)
                .all()
            )
            notifications.extend(
                {
                    "title": f"Reservation for {reservation.listing.crop_type}",
                    "detail": f"{reservation.buyer.name} · {reservation.status.title()}",
                    "timestamp": reservation.timestamp,
                    "kind": "reservation",
                }
                for reservation in reservations
            )

        messages = (
            Message.query.filter_by(receiver_id=current_user.id)
            .order_by(Message.timestamp.desc())
            .limit(5)
            .all()
        )
        notifications.extend(
            {
                "title": f"Message from {message.sender.name}",
                "detail": message.content,
                "timestamp": message.timestamp,
                "kind": "message",
            }
            for message in messages
        )

        if current_user.is_buyer():
            reservations = (
                Reservation.query.filter_by(buyer_id=current_user.id)
                .order_by(Reservation.timestamp.desc())
                .limit(5)
                .all()
            )
            notifications.extend(
                {
                    "title": f"Reservation for {reservation.listing.crop_type}",
                    "detail": f"{reservation.listing.farmer.name} · {reservation.status.title()}",
                    "timestamp": reservation.timestamp,
                    "kind": "reservation",
                }
                for reservation in reservations
            )

        notifications.sort(key=lambda item: item["timestamp"], reverse=True)
        return {"header_notifications": notifications}

    @app.errorhandler(413)
    def request_entity_too_large(error):
        return render_template("errors/413.html"), 413

    with app.app_context():
        db.create_all()

    return app


def register_blueprints(app: Flask) -> None:
    """Registers one blueprint per feature area (Application Tier route groups)."""
    from app.routes.public_routes import public_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.dashboard_routes import dashboard_bp
    from app.routes.farm_routes import farm_bp
    from app.routes.scan_routes import scan_bp
    from app.routes.marketplace_routes import marketplace_bp
    from app.routes.messaging_routes import messaging_bp
    from app.routes.community_routes import community_bp
    from app.routes.admin_routes import admin_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(farm_bp)
    app.register_blueprint(scan_bp)
    app.register_blueprint(marketplace_bp)
    app.register_blueprint(messaging_bp)
    app.register_blueprint(community_bp)
    app.register_blueprint(admin_bp)
