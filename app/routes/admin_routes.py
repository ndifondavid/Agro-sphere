from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models.user import User
from app.models.farm import Farm
from app.models.listing import Listing
from app.utils.decorators import roles_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
@login_required
@roles_required("admin")
def index():
    return render_template(
        "admin/index.html",
        users=User.query.order_by(User.id.desc()).all(),
        listings=Listing.query.order_by(Listing.id.desc()).all(),
        farm_count=Farm.query.count(),
        listing_count=Listing.query.count(),
    )


@admin_bp.route("/users/<int:user_id>/toggle-status", methods=["POST"])
@login_required
@roles_required("admin")
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == "admin" and user.id != current_user.id:
        flash("You cannot deactivate another administrator account.", "warning")
        return redirect(url_for("admin.index"))

    user.is_active = not user.is_active
    db.session.commit()
    status_label = "reactivated" if user.is_active else "deactivated"
    flash(f"User {user.name} was {status_label}.", "success")
    return redirect(url_for("admin.index"))


@admin_bp.route("/listings/<int:listing_id>/delete", methods=["POST"])
@login_required
@roles_required("admin")
def delete_listing(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    db.session.delete(listing)
    db.session.commit()
    flash(f"Listing '{listing.crop_type}' was removed.", "success")
    return redirect(url_for("admin.index"))
