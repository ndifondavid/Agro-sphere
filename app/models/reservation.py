"""
RESERVATION table (SDS Section 4.2.3 / 4.2.4).

    id           INTEGER PK AUTOINCREMENT
    listing_id   INTEGER FK -> LISTING.id, NOT NULL
    buyer_id     INTEGER FK -> USER.id, NOT NULL
    status       TEXT NOT NULL DEFAULT 'requested'
    timestamp    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP

No payment/transaction fields, per the Design Constraints in SDS Section 8;
only status is tracked (e.g. requested, confirmed).
"""
from datetime import datetime

from app.extensions import db

STATUS_REQUESTED = "requested"
STATUS_CONFIRMED = "confirmed"
STATUS_CANCELLED = "cancelled"


class Reservation(db.Model):
    __tablename__ = "reservation"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    listing_id = db.Column(db.Integer, db.ForeignKey("listing.id"), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    status = db.Column(db.Text, nullable=False, default=STATUS_REQUESTED)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Reservation id={self.id} listing_id={self.listing_id} status={self.status!r}>"
