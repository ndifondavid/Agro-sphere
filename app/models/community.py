from datetime import datetime

from app.extensions import db


class CommunityPost(db.Model):
    __tablename__ = "community_post"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    author = db.relationship("User", backref=db.backref("community_posts", lazy=True))
    replies = db.relationship(
        "CommunityReply", backref="post", lazy=True, cascade="all, delete-orphan",
        order_by="CommunityReply.timestamp.asc()",
    )


class CommunityReply(db.Model):
    __tablename__ = "community_reply"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    post_id = db.Column(db.Integer, db.ForeignKey("community_post.id"), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    author = db.relationship("User", backref=db.backref("community_replies", lazy=True))