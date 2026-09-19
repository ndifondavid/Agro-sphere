"""
Farm & Crop Management routes (FR-2.x; SDS Section 4 - Farm, Crop classes).

Every Crop belongs to exactly one Farm, and every Farm belongs to exactly one
User (SDS Section 4.2.2 - ER Diagram cardinality).
"""
import os
import uuid
import re
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user

from app.extensions import db
from app.models.farm import Farm
from app.models.crop import Crop
from app.utils.decorators import roles_required
from app.utils.validators import require_fields, allowed_image_file, is_within_max_size

farm_bp = Blueprint("farm", __name__, url_prefix="/farms")


def save_uploaded_image(file_obj):
    if file_obj is None or not file_obj.filename:
        return None

    allowed_ext = current_app.config["ALLOWED_IMAGE_EXTENSIONS"]
    if not allowed_image_file(file_obj.filename, allowed_ext):
        raise ValueError("Unsupported file type. Please upload a PNG or JPG image.")

    if not is_within_max_size(file_obj, current_app.config["MAX_CONTENT_LENGTH"]):
        raise ValueError("Image is too large.")

    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)
    ext = file_obj.filename.rsplit(".", 1)[1].lower()
    stored_name = f"{uuid.uuid4().hex}.{ext}"
    stored_path = os.path.join(upload_dir, stored_name)
    file_obj.save(stored_path)
    return f"images/uploads/{stored_name}"


def farm_area_value(farm):
    match = re.search(r"\d+(?:\.\d+)?", farm.farm_size or "")
    return float(match.group()) if match else 0


def parse_planting_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Please enter a valid planting date.")


@farm_bp.route("/")
@login_required
@roles_required("farmer")
def list_farms():
    if current_user.is_buyer():
        flash("Buyer accounts do not have access to the farms dashboard.", "warning")
        return redirect(url_for("public.landing"))
    farms = Farm.query.filter_by(owner_id=current_user.id).all()
    farm_cards = []
    for farm in farms:
        crop_names = [crop.crop_type for crop in farm.crops]
        first_crop = crop_names[0] if crop_names else "No crop added yet"
        if len(farm.crops) == 0:
            status = "Needs setup"
            health_style = "neutral"
        else:
            status = "Healthy"
            health_style = "healthy"
        farm_cards.append({
            "farm": farm,
            "crop_name": first_crop,
            "crop_count": len(farm.crops),
            "status": status,
            "status_class": health_style,
            "location": farm.location,
        })
    total_area = sum(farm_area_value(item["farm"]) for item in farm_cards)
    healthy_farms = sum(item["status_class"] == "healthy" for item in farm_cards)
    return render_template(
        "dashboard/farms.html",
        farms=farm_cards,
        total_area=total_area,
        healthy_farms=healthy_farms,
        attention_farms=max(len(farm_cards) - healthy_farms, 0),
    )


@farm_bp.route("/new", methods=["GET", "POST"])
@login_required
@roles_required("farmer")
def create_farm():
    if request.method == "POST":
        missing = require_fields(request.form, ["name", "location"])
        if missing:
            flash("Farm name and location are required.", "danger")
            return render_template("dashboard/farm_form.html")

        try:
            image_path = save_uploaded_image(request.files.get("photo"))
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template("dashboard/farm_form.html")

        farm = Farm(
            owner_id=current_user.id,
            name=request.form["name"].strip(),
            location=request.form["location"].strip(),
            description=request.form.get("description", "").strip() or None,
            farm_size=request.form.get("farm_size", "").strip() or None,
            image_path=image_path,
        )
        db.session.add(farm)
        db.session.commit()
        flash("Farm created.", "success")
        return redirect(url_for("farm.list_farms"))

    return render_template("dashboard/farm_form.html")


@farm_bp.route("/<int:farm_id>/crops/new", methods=["GET", "POST"])
@login_required
@roles_required("farmer")
def create_crop(farm_id):
    farm = Farm.query.filter_by(id=farm_id, owner_id=current_user.id).first_or_404()

    if request.method == "POST":
        missing = require_fields(request.form, ["crop_type"])
        if missing:
            flash("Crop type is required.", "danger")
            return render_template("dashboard/crop_form.html", farm=farm)

        try:
            image_path = save_uploaded_image(request.files.get("photo"))
            planting_date = parse_planting_date(request.form.get("planting_date"))
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template("dashboard/crop_form.html", farm=farm)

        crop = Crop(
            farm_id=farm.id,
            crop_type=request.form["crop_type"].strip(),
            planting_date=planting_date,
            variety=request.form.get("variety", "").strip() or None,
            description=request.form.get("description", "").strip() or None,
            image_path=image_path,
        )
        db.session.add(crop)
        db.session.commit()
        flash("Crop added.", "success")
        return redirect(url_for("farm.farm_details", farm_id=farm.id))

    return render_template("dashboard/crop_form.html", farm=farm)


@farm_bp.route("/<int:farm_id>/details")
@login_required
@roles_required("farmer")
def farm_details(farm_id):
    farm = Farm.query.filter_by(id=farm_id, owner_id=current_user.id).first_or_404()
    return render_template("dashboard/farm_details.html", farm=farm)


@farm_bp.route("/<int:farm_id>/manage", methods=["GET", "POST"])
@login_required
@roles_required("farmer")
def manage_farm(farm_id):
    farm = Farm.query.filter_by(id=farm_id, owner_id=current_user.id).first_or_404()

    if request.method == "POST":
        action = request.form.get("action")

        if action == "update_farm":
            farm.name = request.form.get("name", farm.name).strip() or farm.name
            farm.location = request.form.get("location", farm.location).strip() or farm.location
            farm.description = request.form.get("description", "").strip() or None
            farm.farm_size = request.form.get("farm_size", "").strip() or None

            try:
                uploaded = save_uploaded_image(request.files.get("photo"))
                if uploaded:
                    farm.image_path = uploaded
            except ValueError as exc:
                flash(str(exc), "danger")
                return render_template("dashboard/farm_manage.html", farm=farm)

            db.session.commit()
            flash("Farm details updated.", "success")
            return redirect(url_for("farm.manage_farm", farm_id=farm.id))

        if action == "add_crop":
            missing = require_fields(request.form, ["crop_type"])
            if missing:
                flash("Crop type is required.", "danger")
                return render_template("dashboard/farm_manage.html", farm=farm)

            try:
                image_path = save_uploaded_image(request.files.get("crop_photo"))
                planting_date = parse_planting_date(request.form.get("planting_date"))
            except ValueError as exc:
                flash(str(exc), "danger")
                return render_template("dashboard/farm_manage.html", farm=farm)

            crop = Crop(
                farm_id=farm.id,
                crop_type=request.form["crop_type"].strip(),
                planting_date=planting_date,
                variety=request.form.get("variety", "").strip() or None,
                description=request.form.get("description", "").strip() or None,
                image_path=image_path,
            )
            db.session.add(crop)
            db.session.commit()
            flash("Crop added to the farm.", "success")
            return redirect(url_for("farm.manage_farm", farm_id=farm.id))

    return render_template("dashboard/farm_manage.html", farm=farm)


@farm_bp.route("/<int:farm_id>/crops/<int:crop_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required("farmer")
def edit_crop(farm_id, crop_id):
    farm = Farm.query.filter_by(id=farm_id, owner_id=current_user.id).first_or_404()
    crop = Crop.query.filter_by(id=crop_id, farm_id=farm.id).first_or_404()

    if request.method == "POST":
        missing = require_fields(request.form, ["crop_type"])
        if missing:
            flash("Crop type is required.", "danger")
            return render_template("dashboard/crop_edit.html", farm=farm, crop=crop)
        try:
            crop.planting_date = parse_planting_date(request.form.get("planting_date"))
            uploaded = save_uploaded_image(request.files.get("photo"))
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template("dashboard/crop_edit.html", farm=farm, crop=crop)

        crop.crop_type = request.form["crop_type"].strip()
        crop.variety = request.form.get("variety", "").strip() or None
        crop.description = request.form.get("description", "").strip() or None
        if uploaded:
            crop.image_path = uploaded
        db.session.commit()
        flash("Crop updated.", "success")
        return redirect(url_for("farm.manage_farm", farm_id=farm.id))

    return render_template("dashboard/crop_edit.html", farm=farm, crop=crop)


@farm_bp.route("/<int:farm_id>/crops/<int:crop_id>/delete", methods=["POST"])
@login_required
@roles_required("farmer")
def delete_crop(farm_id, crop_id):
    farm = Farm.query.filter_by(id=farm_id, owner_id=current_user.id).first_or_404()
    crop = Crop.query.filter_by(id=crop_id, farm_id=farm.id).first_or_404()
    db.session.delete(crop)
    db.session.commit()
    flash("Crop deleted.", "success")
    return redirect(url_for("farm.manage_farm", farm_id=farm.id))
