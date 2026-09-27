"""
Crop Marketplace routes (FR-6.x; SDS Section 6.4 - Marketplace Browse Screen).

"Reserve Produce" extends "Message Farmer/Buyer": messaging is an optional
follow-on step after a reservation, not mandatory (FR-7.1).
No payment fields exist on Listing/Reservation (Design Constraint, Section 8).
"""
import os
import uuid
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from sqlalchemy import or_

from app.extensions import db
from app.models.crop import Crop
from app.models.farm import Farm
from app.models.listing import Listing, STATUS_AVAILABLE, STATUS_RESERVED
from app.models.reservation import Reservation
from app.utils.decorators import roles_required
from app.utils.validators import allowed_image_file, is_within_max_size

marketplace_bp = Blueprint("marketplace", __name__, url_prefix="/marketplace")


def _build_database_products():
    listing_products = []
    for listing in Listing.query.filter_by(availability_status=STATUS_AVAILABLE).order_by(Listing.harvest_date.desc()).all():
        listing_products.append({
            "id": listing.id,
            "crop_type": listing.crop_type,
            "farm_name": listing.farmer.name if listing.farmer else "Local Farm",
            "location": (listing.farmer.farms[0].location if listing.farmer and listing.farmer.farms else "Cameroon"),
            "price": float(listing.price or 0),
            "health_score": 96,
            "verified": True,
            "quantity": int(listing.quantity or 0),
            "unit": listing.package_unit or "kg",
            "condition": f"{listing.package_size.title()} • Available",
            "delivery": "2-4 days",
            "rating": 4.8,
            "image": url_for("static", filename=listing.image_path) if listing.image_path else None,
        })
    return listing_products


def _market_products():
    return _build_database_products()


@marketplace_bp.route("/dashboard")
@login_required
@roles_required("buyer")
def buyer_dashboard():
    stats = [
        {"label": "Total Orders", "value": "24", "trend": "+12%"},
        {"label": "Saved Items", "value": "08", "trend": "+3"},
        {"label": "Total Spend", "value": "FCFA 1.2M", "trend": "+8%"},
        {"label": "Farm Visits", "value": "6", "trend": "+2"},
    ]
    recent_orders = [
        {"order": "AG-2048", "item": "Tomato crate", "status": "In transit", "date": "Today"},
        {"order": "AG-2021", "item": "Cassava tubers", "status": "Delivered", "date": "Yesterday"},
        {"order": "AG-1989", "item": "Rice harvest", "status": "Processing", "date": "2 days ago"},
    ]
    recommended = _market_products()[:3]
    healthy_crops = _market_products()[:4]
    return render_template(
        "marketplace/buyer_dashboard.html",
        stats=stats,
        recent_orders=recent_orders,
        recommended=recommended,
        healthy_crops=healthy_crops,
    )


@marketplace_bp.route("/product/<int:item_id>")
@login_required
@roles_required("buyer")
def product_detail(item_id):
    products = _market_products()
    product = next((product for product in products if product["id"] == item_id), None)
    if product is None:
        flash("No listings are available yet. Run python database/seed.py to add realistic marketplace data.", "info")
        return redirect(url_for("marketplace.browse"))
    related = products[:3]
    return render_template("marketplace/product_detail.html", product=product, related=related)


@marketplace_bp.route("/cart")
@login_required
@roles_required("buyer")
def cart():
    cart_items = [
        {"id": 1, "crop_type": "Tomato", "farm_name": "Green Valley Farm", "location": "Bamenda", "price": 150000, "quantity": 2, "image": "https://images.unsplash.com/photo-1546094096-0df4bcaaa337?auto=format&fit=crop&w=900&q=80"},
        {"id": 2, "crop_type": "Maize", "farm_name": "Mbingo Cooperative", "location": "Bamenda", "price": 110000, "quantity": 1, "image": "https://images.unsplash.com/photo-1501004318641-b39e6451bec6?auto=format&fit=crop&w=900&q=80"},
    ]
    return render_template("marketplace/cart.html", cart_items=cart_items)


@marketplace_bp.route("/checkout")
@login_required
@roles_required("buyer")
def checkout():
    return render_template("marketplace/checkout.html")


@marketplace_bp.route("/orders")
@login_required
@roles_required("buyer")
def orders():
    orders = [
        {"id": "AG-2048", "item": "Tomato crate", "status": "Active", "total": "FCFA 255,000", "eta": "3 days"},
        {"id": "AG-2021", "item": "Cassava tubers", "status": "Completed", "total": "FCFA 80,000", "eta": "Delivered"},
        {"id": "AG-1989", "item": "Rice harvest", "status": "Cancelled", "total": "FCFA 65,000", "eta": "Cancelled"},
    ]
    return render_template("marketplace/orders.html", orders=orders)


@marketplace_bp.route("/messages")
@login_required
@roles_required("buyer")
def messages():
    chats = [
        {"name": "Green Valley Farm", "preview": "We can deliver tomorrow morning.", "time": "2m ago", "unread": 2},
        {"name": "Mbingo Cooperative", "preview": "Your maize batch is ready.", "time": "18m ago", "unread": 0},
    ]
    return render_template("marketplace/messages.html", chats=chats)


@marketplace_bp.route("/wishlist")
@login_required
@roles_required("buyer")
def wishlist():
    products = _market_products()[:4]
    return render_template("marketplace/wishlist.html", products=products)


@marketplace_bp.route("/notifications")
@login_required
@roles_required("buyer")
def notifications():
    notifications = [
        {"title": "Order update", "detail": "Tomato crate is now in transit.", "time": "5 mins ago", "unread": True},
        {"title": "Marketplace alert", "detail": "Maize prices dropped by 8%.", "time": "1 hour ago", "unread": True},
        {"title": "Message", "detail": "Mbingo Cooperative responded to your inquiry.", "time": "Today", "unread": False},
    ]
    return render_template("marketplace/notifications.html", notifications=notifications)


@marketplace_bp.route("/profile")
@login_required
@roles_required("buyer")
def profile():
    return render_template("marketplace/profile.html")


@marketplace_bp.route("/help")
@login_required
@roles_required("buyer")
def buyer_help():
    return render_template("marketplace/help.html")


@marketplace_bp.route("/")
@login_required
@roles_required("buyer")
def browse():
    crop_type = request.args.get("crop_type", "").strip()
    location = request.args.get("location", "").strip()
    search = request.args.get("search", "").strip()
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)

    query = Listing.query.filter_by(availability_status=STATUS_AVAILABLE)
    if crop_type:
        query = query.filter(Listing.crop_type.ilike(f"%{crop_type}%"))
    if search or location:
        query = query.join(Farm, Farm.owner_id == Listing.farmer_id)
    if search:
        query = query.filter(
            or_(
                Listing.crop_type.ilike(f"%{search}%"),
                Farm.name.ilike(f"%{search}%"),
                Farm.location.ilike(f"%{search}%"),
            )
        )
    if location:
        query = query.filter(Farm.location.ilike(f"%{location}%"))
    if min_price is not None:
        query = query.filter(Listing.price >= min_price)
    if max_price is not None:
        query = query.filter(Listing.price <= max_price)

    listings = query.order_by(Listing.harvest_date.desc()).all()
    if not listings:
        flash("No listings are available yet. Run python database/seed.py to seed realistic crop listings for testing.", "info")
    return render_template(
        "marketplace/browse.html",
        listings=listings,
        search=search,
        crop_type=crop_type,
        location=location,
        min_price=min_price,
        max_price=max_price,
    )


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
        package_size = request.form.get("package_size", "medium basket").strip().lower()
        package_unit = request.form.get("package_unit", "basket").strip().lower()
        price = request.form.get("price")
        photo = request.files.get("photo")

        if not all([farm_id, crop_id, harvest_date, quantity, package_size, package_unit, price]):
            flash("All listing fields are required.", "danger")
            return render_template("marketplace/listing_form.html", farms=farms)

        if package_unit not in {"basket", "bucket"}:
            flash("Choose a valid package type.", "danger")
            return render_template("marketplace/listing_form.html", farms=farms)

        allowed_sizes = {
            "small": "small",
            "small basket": "small basket",
            "medium": "medium",
            "medium basket": "medium basket",
            "large": "large",
            "large basket": "large basket",
            "bucket": "bucket",
        }
        package_size = allowed_sizes.get(package_size)
        if package_size is None:
            flash("Choose a valid package size.", "danger")
            return render_template("marketplace/listing_form.html", farms=farms)

        try:
            harvest_date_obj = datetime.strptime(harvest_date, "%Y-%m-%d").date()
        except ValueError:
            flash("Please enter a valid harvest date.", "danger")
            return render_template("marketplace/listing_form.html", farms=farms)

        try:
            quantity_value = float(quantity)
            price_value = float(price)
        except (TypeError, ValueError):
            flash("Quantity and price must be valid numbers.", "danger")
            return render_template("marketplace/listing_form.html", farms=farms)

        if quantity_value <= 0 or price_value <= 0:
            flash("Quantity and price must be greater than zero.", "danger")
            return render_template("marketplace/listing_form.html", farms=farms)

        farm = Farm.query.filter_by(id=farm_id, owner_id=current_user.id).first()
        crop = Crop.query.filter_by(id=crop_id, farm_id=farm.id).first() if farm else None
        if not farm or not crop:
            flash("Choose a valid farm and crop.", "danger")
            return render_template("marketplace/listing_form.html", farms=farms)

        image_path = None
        if photo and photo.filename:
            allowed_ext = current_app.config["ALLOWED_IMAGE_EXTENSIONS"]
            if not allowed_image_file(photo.filename, allowed_ext):
                flash("Unsupported file type. Please upload a PNG or JPG image.", "danger")
                return render_template("marketplace/listing_form.html", farms=farms)

            if not is_within_max_size(photo, current_app.config["MAX_CONTENT_LENGTH"]):
                flash("Image is too large.", "danger")
                return render_template("marketplace/listing_form.html", farms=farms)

            upload_dir = current_app.config["UPLOAD_FOLDER"]
            os.makedirs(upload_dir, exist_ok=True)
            ext = photo.filename.rsplit(".", 1)[1].lower()
            stored_name = f"{uuid.uuid4().hex}.{ext}"
            stored_path = os.path.join(upload_dir, stored_name)
            photo.save(stored_path)
            image_path = f"images/uploads/{stored_name}"

        listing = Listing(
            farmer_id=current_user.id,
            crop_type=crop.crop_type,
            harvest_date=harvest_date_obj,
            quantity=quantity_value,
            package_size=package_size,
            package_unit=package_unit,
            price=price_value,
            image_path=image_path,
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

    existing_reservation = Reservation.query.filter(
        Reservation.listing_id == listing.id,
        Reservation.buyer_id == current_user.id,
        Reservation.status.in_(("requested", "confirmed")),
    ).first()
    if existing_reservation:
        flash("You already have an active reservation for this listing.", "warning")
        return redirect(url_for("marketplace.browse"))

    reservation = Reservation(listing_id=listing.id, buyer_id=current_user.id)
    listing.availability_status = STATUS_RESERVED
    db.session.add(reservation)
    db.session.commit()

    flash("Reservation requested.", "success")
    return redirect(url_for("marketplace.browse"))


@marketplace_bp.route("/reservations")
@login_required
def reservations():
    if current_user.is_farmer():
        reservations = (
            Reservation.query.join(Reservation.listing)
            .filter(Listing.farmer_id == current_user.id)
            .order_by(Reservation.timestamp.desc())
            .all()
        )
    elif current_user.is_buyer():
        reservations = Reservation.query.filter_by(buyer_id=current_user.id).order_by(Reservation.timestamp.desc()).all()
    else:
        return "Access denied.", 403
    return render_template("marketplace/reservations.html", reservations=reservations)


@marketplace_bp.route("/reservations/<int:reservation_id>/<status>", methods=["POST"])
@login_required
def update_reservation(reservation_id, status):
    reservation = Reservation.query.get_or_404(reservation_id)
    if status not in {"confirmed", "cancelled"}:
        flash("Invalid reservation status.", "danger")
        return redirect(url_for("marketplace.reservations"))
    is_farmer_owner = current_user.is_farmer() and reservation.listing.farmer_id == current_user.id
    is_buyer_owner = current_user.is_buyer() and reservation.buyer_id == current_user.id
    if not (is_farmer_owner or is_buyer_owner):
        return "Access denied.", 403
    reservation.status = status
    if status == "cancelled":
        reservation.listing.availability_status = STATUS_AVAILABLE
    elif status == "confirmed":
        reservation.listing.availability_status = STATUS_RESERVED
    db.session.commit()
    flash(f"Reservation {status}.", "success")
    return redirect(url_for("marketplace.reservations"))
