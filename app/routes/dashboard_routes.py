"""
Farmer Dashboard route (FR-1.4, FR-4.3; SDS Section 6.2 - Farmer Dashboard).

Summary cards: total farms, recent scans, disease alerts; analytics section
below summarizing disease frequency over time (rendered with Chart.js).
"""
from flask import Blueprint, render_template
from flask_login import login_required, current_user

from app.models.farm import Farm
from app.models.scan import Scan

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.route("/")
@login_required
def index():
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
