"""
FARM table (SDS Section 4.2.3 / 4.2.4).

    id         INTEGER PK AUTOINCREMENT
    owner_id   INTEGER FK -> USER.id, NOT NULL
    name       TEXT NOT NULL
    location   TEXT NOT NULL
    image_path TEXT

An index on farm.owner_id speeds up loading "all farms for this user" on the
Farmer Dashboard (SDS Section 4.2.5).
"""
from app.extensions import db


class Farm(db.Model):
    __tablename__ = "farm"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    name = db.Column(db.Text, nullable=False)
    location = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=True)
    farm_size = db.Column(db.Text, nullable=True)
    image_path = db.Column(db.Text, nullable=True)

    crops = db.relationship("Crop", backref="farm", lazy=True, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Farm id={self.id} name={self.name!r}>"
