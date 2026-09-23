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
    is_listing_owner = current_user.is_farmer() and listing.farmer_id == current_user.id
    is_existing_buyer = current_user.is_buyer() and any(
        reservation.buyer_id == current_user.id for reservation in listing.reservations
    )
    if not (is_listing_owner or is_existing_buyer):
        return "Access denied.", 403

    if request.method == "POST":
        missing = require_fields(request.form, ["content", "receiver_id"])
        if missing:
            flash("Message content is required.", "danger")
        else:
            try:
                receiver_id = int(request.form["receiver_id"])
            except (TypeError, ValueError):
                receiver_id = None

            receiver = User.query.get(receiver_id) if receiver_id else None
            valid_receiver = (
                receiver is not None
                and receiver.id != current_user.id
                and (
                    (current_user.is_buyer() and receiver.id == listing.farmer_id)
                    or (
                        current_user.is_farmer()
                        and receiver.id in {
                            reservation.buyer_id for reservation in listing.reservations
                        }
                    )
                )
            )
            if not valid_receiver:
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
