from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required

from app.extensions import db
from app.models.community import CommunityPost, CommunityReply

community_bp = Blueprint("community", __name__, url_prefix="/community")


@community_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        content = (request.form.get("content") or "").strip()
        if not content:
            flash("Write a post before publishing.", "danger")
        else:
            db.session.add(CommunityPost(author_id=current_user.id, content=content))
            db.session.commit()
            flash("Post published.", "success")
        return redirect(url_for("community.index"))

    posts = CommunityPost.query.order_by(CommunityPost.timestamp.desc()).all()
    return render_template("community/index.html", posts=posts)


@community_bp.route("/<int:post_id>/replies", methods=["POST"])
@login_required
def reply(post_id):
    post = CommunityPost.query.get_or_404(post_id)
    content = (request.form.get("content") or "").strip()
    if not content:
        flash("Write a reply before publishing.", "danger")
    else:
        db.session.add(CommunityReply(post_id=post.id, author_id=current_user.id, content=content))
        db.session.commit()
        flash("Reply published.", "success")
    return redirect(url_for("community.index"))
