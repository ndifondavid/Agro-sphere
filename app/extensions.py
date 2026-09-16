"""Shared Flask extension instances (avoids circular imports between app/__init__.py and models)."""
import sqlite3

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from sqlalchemy import event
from sqlalchemy.engine import Engine


@event.listens_for(Engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
	if isinstance(dbapi_connection, sqlite3.Connection):
		cursor = dbapi_connection.cursor()
		cursor.execute("PRAGMA foreign_keys=ON")
		cursor.close()

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
