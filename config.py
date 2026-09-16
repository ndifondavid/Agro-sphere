"""
Application configuration.

Data Tier: SQLite for this version of the system (SDS Section 4.2.1 - Database Engine).
NFR-5.1 anticipates replacing SQLite with a production-grade engine (e.g. PostgreSQL);
because the object model (app/models) is decoupled from the storage layer, that migration
only requires changing SQLALCHEMY_DATABASE_URI, not the class design.
"""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")


class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Upload settings for leaf scan photos (FR-3.1)
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "app", "static", "images", "uploads")
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB max upload size
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg"}

    # AI Tier model location (SDS Section 2 - AI Tier)
    AI_MODEL_PATH = os.path.join(BASE_DIR, "ai_model", "disease_model.h5")
    AI_CONFIDENCE_THRESHOLD = 0.60


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(INSTANCE_DIR, "agrosphere.db")
    )


class TestingConfig(BaseConfig):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(INSTANCE_DIR, "agrosphere.db")
    )
