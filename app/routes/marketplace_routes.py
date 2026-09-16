"""
Crop Marketplace routes (FR-6.x; SDS Section 6.4 - Marketplace Browse Screen).

"Reserve Produce" extends "Message Farmer/Buyer": messaging is an optional
follow-on step after a reservation, not mandatory (FR-7.1).
No payment fields exist on Listing/Reservation (Design Constraint, Section 8).
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.extensions import db
from app.models.listing import Listing, STATUS_AVAILABLE, STATUS_RESERVED
from app.models.reservation import Reservation
from app.utils.decorators import roles_required
from app.utils.validators import require_fields

marketplace_bp = Blueprint("marketplace", __name__, url_prefix="/marketplace")


@marketplace_bp.route("/")
@login_required
def browse():
    crop_type = request.args.get("crop_type", "").strip()
    location = request.args.get("location", "").strip()

    query = Listing.query.filter_by(availability_status=STATUS_AVAILABLE)
    if crop_type:
        query = query.filter(Listing.crop_type.ilike(f"%{crop_type}%"))

    listings = query.order_by(Listing.harvest_date.desc()).all()
    return render_template("marketplace/browse.html", listings=listings)


@marketplace_bp.route("/new", methods=["GET", "POST"])
@login_required
@roles_required("farmer")
def create_listing():
    if request.method == "POST":
        missing = require_fields(request.form, ["crop_type", "harvest_date", "quantity", "price"])
        if missing:
            flash("All listing fields are required.", "danger")
            return render_template("marketplace/listing_form.html")

        listing = Listing(
            farmer_id=current_user.id,
            crop_type=request.form["crop_type"].strip(),
            harvest_date=request.form["harvest_date"],
            quantity=float(request.form["quantity"]),
            price=float(request.form["price"]),
        )
        db.session.add(listing)
        db.session.commit()
        flash("Listing created.", "success")
        return redirect(url_for("marketplace.browse"))

    return render_template("marketplace/listing_form.html")


@marketplace_bp.route("/<int:listing_id>/reserve", methods=["POST"])
@login_required
@roles_required("buyer")
def reserve(listing_id):
    listing = Listing.query.filter_by(id=listing_id, availability_status=STATUS_AVAILABLE).first_or_404()

    reservation = Reservation(listing_id=listing.id, buyer_id=current_user.id)
    listing.availability_status = STATUS_RESERVED
    db.session.add(reservation)
    db.session.commit()

    flash("Reservation requested.", "success")
    return redirect(url_for("marketplace.browse"))
