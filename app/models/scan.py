"""
SCAN table (SDS Section 4.2.3 / 4.2.4).

    id                  INTEGER PK AUTOINCREMENT
    crop_id             INTEGER FK -> CROP.id, NOT NULL
    image_path          TEXT NOT NULL
    predicted_disease   TEXT NOT NULL
    confidence_score    FLOAT NOT NULL
    recommendation      TEXT
    timestamp           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP

An index on scan.crop_id speeds up scan history and analytics queries
(FR-4.1, FR-4.3; SDS Section 4.2.5).
"""
from datetime import datetime

from app.extensions import db


class Scan(db.Model):
    __tablename__ = "scan"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    crop_id = db.Column(db.Integer, db.ForeignKey("crop.id"), nullable=False, index=True)
    image_path = db.Column(db.Text, nullable=False)
    predicted_disease = db.Column(db.Text, nullable=False)
    confidence_score = db.Column(db.Float, nullable=False)
    recommendation = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Scan id={self.id} disease={self.predicted_disease!r} confidence={self.confidence_score}>"
