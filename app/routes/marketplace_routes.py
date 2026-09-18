"""
Crop Marketplace routes (FR-6.x; SDS Section 6.4 - Marketplace Browse Screen).

"Reserve Produce" extends "Message Farmer/Buyer": messaging is an optional
follow-on step after a reservation, not mandatory (FR-7.1).
No payment fields exist on Listing/Reservation (Design Constraint, Section 8).
"""
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.extensions import db
from app.models.crop import Crop
from app.models.farm import Farm
from app.models.listing import Listing, STATUS_AVAILABLE, STATUS_RESERVED
from app.models.reservation import Reservation
from app.utils.decorators import roles_required

marketplace_bp = Blueprint("marketplace", __name__, url_prefix="/marketplace")


@marketplace_bp.route("/")
@login_required
@roles_required("buyer")
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
    farms = Farm.query.filter_by(owner_id=current_user.id).all()
    if not farms:
        flash("Create a farm before listing crops to market.", "warning")
        return redirect(url_for("farm.create_farm"))

    if request.method == "POST":
        farm_id = request.form.get("farm_id")
        crop_id = request.form.get("crop_id")
        harvest_date = request.form.get("harvest_date")
        quantity = request.form.get("quantity")
        price = request.form.get("price")

        if not all([farm_id, crop_id, harvest_date, quantity, price]):
            flash("All listing fields are required.", "danger")
            return render_template("marketplace/listing_form.html", farms=farms)

        try:
            harvest_date_obj = datetime.strptime(harvest_date, "%Y-%m-%d").date()
        except ValueError:
            flash("Please enter a valid harvest date.", "danger")
            return render_template("marketplace/listing_form.html", farms=farms)

        farm = Farm.query.filter_by(id=farm_id, owner_id=current_user.id).first()
        crop = Crop.query.filter_by(id=crop_id, farm_id=farm.id).first() if farm else None
        if not farm or not crop:
            flash("Choose a valid farm and crop.", "danger")
            return render_template("marketplace/listing_form.html", farms=farms)

        listing = Listing(
            farmer_id=current_user.id,
            crop_type=crop.crop_type,
            harvest_date=harvest_date_obj,
            quantity=float(quantity),
            price=float(price),
            image_path=request.form.get("image_path") or None,
        )
        db.session.add(listing)
        db.session.commit()
        flash("Listing created and sent to the buyer marketplace.", "success")
        return redirect(url_for("farm.list_farms"))

    return render_template("marketplace/listing_form.html", farms=farms)


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
