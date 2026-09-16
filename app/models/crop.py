"""
CROP table (SDS Section 4.2.3 / 4.2.4).

    id             INTEGER PK AUTOINCREMENT
    farm_id        INTEGER FK -> FARM.id, NOT NULL
    crop_type      TEXT NOT NULL
    planting_date  DATE

An index on crop.farm_id speeds up loading a farm's crop list (SDS Section 4.2.5).
Every Scan is linked to a Crop, not directly to a User (FR-2.4).
"""
from app.extensions import db


class Crop(db.Model):
    __tablename__ = "crop"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    farm_id = db.Column(db.Integer, db.ForeignKey("farm.id"), nullable=False, index=True)
    crop_type = db.Column(db.Text, nullable=False)
    planting_date = db.Column(db.Date, nullable=True)

    scans = db.relationship("Scan", backref="crop", lazy=True, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Crop id={self.id} crop_type={self.crop_type!r}>"
