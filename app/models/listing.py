"""
LISTING table (SDS Section 4.2.3 / 4.2.4).

    id                    INTEGER PK AUTOINCREMENT
    farmer_id             INTEGER FK -> USER.id, NOT NULL
    crop_type             TEXT NOT NULL
    harvest_date          DATE NOT NULL
    quantity              FLOAT NOT NULL
    price                 FLOAT NOT NULL
    availability_status   TEXT NOT NULL DEFAULT 'available'
    image_path            TEXT

Per Design Constraint (SDS Section 8): no payment or transaction fields exist
here - only availability status is tracked. An index on availability_status
speeds up the Buyer's browse/filter query (FR-6.3; SDS Section 4.2.5).
"""
from app.extensions import db

STATUS_AVAILABLE = "available"
STATUS_RESERVED = "reserved"
STATUS_SOLD = "sold"


class Listing(db.Model):
    __tablename__ = "listing"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    crop_type = db.Column(db.Text, nullable=False)
    harvest_date = db.Column(db.Date, nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    availability_status = db.Column(
        db.Text, nullable=False, default=STATUS_AVAILABLE, index=True
    )
    image_path = db.Column(db.Text, nullable=True)

    reservations = db.relationship(
        "Reservation", backref="listing", lazy=True, cascade="all, delete-orphan"
    )
    messages = db.relationship(
        "Message", backref="listing", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Listing id={self.id} crop_type={self.crop_type!r} status={self.availability_status!r}>"
