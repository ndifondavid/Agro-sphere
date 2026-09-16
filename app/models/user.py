"""
USER table (SDS Section 4.2.3 / 4.2.4).

    id             INTEGER PK AUTOINCREMENT
    name           TEXT NOT NULL
    email          TEXT NOT NULL UNIQUE
    password_hash  TEXT NOT NULL
    role           TEXT NOT NULL - 'farmer', 'buyer', or 'admin'

Security design (SDS Section 7): passwords are hashed with Werkzeug's
generate_password_hash before being written to this table; plain-text
passwords are never persisted (NFR-2.1).
"""
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db, login_manager

ROLE_FARMER = "farmer"
ROLE_BUYER = "buyer"
ROLE_ADMIN = "admin"
VALID_ROLES = (ROLE_FARMER, ROLE_BUYER, ROLE_ADMIN)
REGISTRABLE_ROLES = (ROLE_FARMER, ROLE_BUYER)


class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, nullable=False, unique=True, index=True)
    password_hash = db.Column(db.Text, nullable=False)
    role = db.Column(db.Text, nullable=False)

    # Relationships
    farms = db.relationship("Farm", backref="owner", lazy=True, cascade="all, delete-orphan")
    listings = db.relationship("Listing", backref="farmer", lazy=True, cascade="all, delete-orphan")
    sent_messages = db.relationship(
        "Message", foreign_keys="Message.sender_id", backref="sender", lazy=True
    )
    received_messages = db.relationship(
        "Message", foreign_keys="Message.receiver_id", backref="receiver", lazy=True
    )
    reservations = db.relationship("Reservation", backref="buyer", lazy=True)

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    def is_farmer(self) -> bool:
        return self.role == ROLE_FARMER

    def is_buyer(self) -> bool:
        return self.role == ROLE_BUYER

    def is_admin(self) -> bool:
        return self.role == ROLE_ADMIN

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role!r}>"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
