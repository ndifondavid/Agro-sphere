import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from app.extensions import db
from app.models import User

ADMIN_EMAIL = os.environ.get("AGROSPHERE_ADMIN_EMAIL", "ndifondavidkenei@gmail.com")
ADMIN_PASSWORD = os.environ.get("AGROSPHERE_ADMIN_PASSWORD")


def provision_admin():
    if not ADMIN_PASSWORD:
        raise RuntimeError("Set AGROSPHERE_ADMIN_PASSWORD before provisioning the admin.")

    app = create_app()
    with app.app_context():
        admin = User.query.filter_by(role="admin").first()
        email_owner = User.query.filter_by(email=ADMIN_EMAIL).first()

        if email_owner is not None and email_owner is not admin:
            raise RuntimeError(f"The admin email is already used by user id {email_owner.id}.")

        if admin is None:
            admin = User(name="System Administrator", email=ADMIN_EMAIL, role="admin")
            db.session.add(admin)
        else:
            admin.name = "System Administrator"
            admin.email = ADMIN_EMAIL
            admin.role = "admin"

        admin.set_password(ADMIN_PASSWORD)
        db.session.commit()
        print(f"Admin account ready: {admin.email} (role: {admin.role})")


if __name__ == "__main__":
    provision_admin()
