"""
Farm & Crop Management routes (FR-2.x; SDS Section 4 - Farm, Crop classes).

Every Crop belongs to exactly one Farm, and every Farm belongs to exactly one
User (SDS Section 4.2.2 - ER Diagram cardinality).
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.extensions import db
from app.models.farm import Farm
from app.models.crop import Crop
from app.utils.decorators import roles_required
from app.utils.validators import require_fields

farm_bp = Blueprint("farm", __name__, url_prefix="/farms")


@farm_bp.route("/")
@login_required
@roles_required("farmer")
def list_farms():
    farms = Farm.query.filter_by(owner_id=current_user.id).all()
    return render_template("dashboard/farms.html", farms=farms)


@farm_bp.route("/new", methods=["GET", "POST"])
@login_required
@roles_required("farmer")
def create_farm():
    if request.method == "POST":
        missing = require_fields(request.form, ["name", "location"])
        if missing:
            flash("Farm name and location are required.", "danger")
            return render_template("dashboard/farm_form.html")

        farm = Farm(
            owner_id=current_user.id,
            name=request.form["name"].strip(),
            location=request.form["location"].strip(),
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

        crop = Crop(
            farm_id=farm.id,
            crop_type=request.form["crop_type"].strip(),
            planting_date=request.form.get("planting_date") or None,
        )
        db.session.add(crop)
        db.session.commit()
        flash("Crop added.", "success")
        return redirect(url_for("farm.list_farms"))

    return render_template("dashboard/crop_form.html", farm=farm)
