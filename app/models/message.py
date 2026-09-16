"""
MESSAGE table (SDS Section 4.2.3 / 4.2.4).

    id            INTEGER PK AUTOINCREMENT
    sender_id     INTEGER FK -> USER.id, NOT NULL
    receiver_id   INTEGER FK -> USER.id, NOT NULL
    listing_id    INTEGER FK -> LISTING.id, NOT NULL
    content       TEXT NOT NULL
    timestamp     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP

Security design (SDS Section 7, NFR-2.4): message routes must check that both
sender and receiver are authenticated, registered accounts before a message
is created. An index on message.listing_id speeds up loading a message
thread for a specific listing (FR-7.3; SDS Section 4.2.5).
"""
from datetime import datetime

from app.extensions import db


class Message(db.Model):
    __tablename__ = "message"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    listing_id = db.Column(db.Integer, db.ForeignKey("listing.id"), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Message id={self.id} sender_id={self.sender_id} receiver_id={self.receiver_id}>"
