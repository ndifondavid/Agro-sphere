"""
Messaging routes (FR-7.x; SDS Section 7 - NFR-2.4).

Message routes check that both sender and receiver are authenticated,
registered accounts before a message is created.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.extensions import db
from app.models.listing import Listing
from app.models.message import Message
from app.models.user import User
from app.utils.validators import require_fields

messaging_bp = Blueprint("messaging", __name__, url_prefix="/messages")


@messaging_bp.route("/listing/<int:listing_id>", methods=["GET", "POST"])
@login_required
def thread(listing_id):
    listing = Listing.query.get_or_404(listing_id)

    if request.method == "POST":
        missing = require_fields(request.form, ["content", "receiver_id"])
        if missing:
            flash("Message content is required.", "danger")
        else:
            receiver = User.query.get(int(request.form["receiver_id"]))
            if receiver is None:
                flash("Recipient not found.", "danger")
            else:
                message = Message(
                    sender_id=current_user.id,
                    receiver_id=receiver.id,
                    listing_id=listing.id,
                    content=request.form["content"].strip(),
                )
                db.session.add(message)
                db.session.commit()

        return redirect(url_for("messaging.thread", listing_id=listing.id))

    messages = (
        Message.query.filter_by(listing_id=listing.id).order_by(Message.timestamp.asc()).all()
    )
    return render_template("messaging/thread.html", listing=listing, messages=messages)
