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
from flask import Flask

from app.extensions import db, login_manager, migrate


def create_app(config_object: str = "config.DevelopmentConfig") -> Flask:
    """Application factory used by run.py / wsgi entry points and tests."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object)

    # Initialize extensions (Data Tier wiring)
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    register_blueprints(app)

    with app.app_context():
        db.create_all()

    return app


def register_blueprints(app: Flask) -> None:
    """Registers one blueprint per feature area (Application Tier route groups)."""
    from app.routes.auth_routes import auth_bp
    from app.routes.dashboard_routes import dashboard_bp
    from app.routes.farm_routes import farm_bp
    from app.routes.scan_routes import scan_bp
    from app.routes.marketplace_routes import marketplace_bp
    from app.routes.messaging_routes import messaging_bp
    from app.routes.community_routes import community_bp
    from app.routes.admin_routes import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(farm_bp)
    app.register_blueprint(scan_bp)
    app.register_blueprint(marketplace_bp)
    app.register_blueprint(messaging_bp)
    app.register_blueprint(community_bp)
    app.register_blueprint(admin_bp)
