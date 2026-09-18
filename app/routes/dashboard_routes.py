"""
Farmer Dashboard route (FR-1.4, FR-4.3; SDS Section 6.2 - Farmer Dashboard).

Summary cards: total farms, recent scans, disease alerts; analytics section
below summarizing disease frequency over time (rendered with Chart.js).
"""
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from app.models.farm import Farm
from app.models.scan import Scan

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.route("/")
@login_required
def index():
    if current_user.is_buyer():
        flash("Buyer accounts do not have access to the dashboard.", "warning")
        return redirect(url_for("public.landing"))
    if not current_user.is_farmer():
        return "Access denied: farmer account required.", 403

    farms = Farm.query.filter_by(owner_id=current_user.id).all()
    farm_ids = [f.id for f in farms]
    crop_ids = [c.id for f in farms for c in f.crops]
    recent_scans = (
        Scan.query.filter(Scan.crop_id.in_(crop_ids))
        .order_by(Scan.timestamp.desc())
        .limit(10)
        .all()
        if crop_ids
        else []
    )

    return render_template(
        "dashboard/index.html",
        farms=farms,
        recent_scans=recent_scans,
        total_farms=len(farms),
        total_scans=len(recent_scans),
    )


@dashboard_bp.route("/settings")
@login_required
def settings():
    if current_user.is_buyer():
        flash("Buyer accounts do not have access to the dashboard.", "warning")
        return redirect(url_for("public.landing"))
    if not current_user.is_farmer():
        return "Access denied: farmer account required.", 403

    return render_template("dashboard/settings.html")


@dashboard_bp.route("/notifications")
@login_required
def notifications():
    if current_user.is_buyer():
        flash("Buyer accounts do not have access to the dashboard.", "warning")
        return redirect(url_for("public.landing"))
    if not current_user.is_farmer():
        return "Access denied: farmer account required.", 403

    return render_template("dashboard/notifications.html")


@dashboard_bp.route("/help")
@login_required
def help_page():
    if current_user.is_buyer():
        flash("Buyer accounts do not have access to the dashboard.", "warning")
        return redirect(url_for("public.landing"))
    if not current_user.is_farmer():
        return "Access denied: farmer account required.", 403

    return render_template("dashboard/help.html")


@dashboard_bp.route("/treatment-details")
@login_required
def treatment_details():
    if current_user.is_buyer():
        flash("Buyer accounts do not have access to the dashboard.", "warning")
        return redirect(url_for("public.landing"))
    if not current_user.is_farmer():
        return "Access denied: farmer account required.", 403

    return render_template("dashboard/treatment_details.html", farmer_name=current_user.name)
