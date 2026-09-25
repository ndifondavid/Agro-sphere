"""
Farmer Dashboard route (FR-1.4, FR-4.3; SDS Section 6.2 - Farmer Dashboard).

Summary cards: total farms, recent scans, disease alerts; analytics section
below summarizing disease frequency over time (rendered with Chart.js).
"""
import os
import uuid
import re
import json
from datetime import datetime, timedelta

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user

from app.extensions import db
from app.models.farm import Farm
from app.models.scan import Scan
from app.models.user import User
from app.utils.validators import allowed_image_file, is_within_max_size

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
    crop_count = sum(len(f.crops) for f in farms)
    crop_ids = [crop.id for farm in farms for crop in farm.crops]
    all_scans = (
        Scan.query.filter(Scan.crop_id.in_(crop_ids))
        .order_by(Scan.timestamp.desc())
        .all()
        if crop_ids
        else []
    )
    recent_scans = all_scans[:10]
    disease_scans = [scan for scan in all_scans if "healthy" not in scan.predicted_disease.lower()]
    healthy_scans = [scan for scan in all_scans if "healthy" in scan.predicted_disease.lower()]
    disease_count = len(disease_scans)
    healthy_count = len(healthy_scans)
    trend_start = datetime.utcnow().date() - timedelta(days=6)
    trend_data = []
    for offset in range(7):
        day = trend_start + timedelta(days=offset)
        day_scans = [scan for scan in all_scans if scan.timestamp.date() == day]
        trend_data.append({
            "label": day.strftime("%a"),
            "date": day.strftime("%b %d"),
            "count": len(day_scans),
        })
    trend_max = max((day["count"] for day in trend_data), default=0)
    total_farm_area = sum(
        float(re.search(r"\d+(?:\.\d+)?", farm.farm_size or "").group())
        for farm in farms
        if re.search(r"\d+(?:\.\d+)?", farm.farm_size or "")
    )

    return render_template(
        "dashboard/index.html",
        farms=farms,
        recent_scans=recent_scans,
        total_farms=len(farms),
        total_crops=crop_count,
        total_scans=len(all_scans),
        disease_count=disease_count,
        healthy_count=healthy_count,
        farm_area=total_farm_area,
        healthy_percentage=(0 if not all_scans else round((healthy_count / len(all_scans)) * 100, 1)),
        diseased_percentage=(0 if not all_scans else round((disease_count / len(all_scans)) * 100, 1)),
        trend_data=trend_data,
        trend_max=trend_max,
    )


@dashboard_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if current_user.is_buyer():
        flash("Buyer accounts do not have access to the dashboard.", "warning")
        return redirect(url_for("public.landing"))
    if not current_user.is_farmer():
        return "Access denied: farmer account required.", 403

    notification_names = (
        "disease_alert", "weather_warning", "community_reply", "weekly_report",
        "email_delivery", "sms_delivery", "whatsapp_delivery", "push_delivery",
    )
    preferences = json.loads(current_user.notification_preferences or "{}")

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()

        if not name or not email:
            flash("Name and email are required.", "danger")
            return render_template("dashboard/settings.html", notification_preferences=preferences)

        existing_user = User.query.filter(User.email == email, User.id != current_user.id).first()
        if existing_user:
            flash("That email address is already in use.", "danger")
            return render_template("dashboard/settings.html", notification_preferences=preferences)

        current_user.name = name
        current_user.email = email
        current_user.phone = (request.form.get("phone") or "").strip() or None
        current_user.farm_location = (request.form.get("farm_location") or "").strip() or None
        current_user.language = (request.form.get("language") or "English").strip()

        profile_photo = request.files.get("profile_photo")
        if profile_photo and profile_photo.filename:
            allowed_ext = current_app.config["ALLOWED_IMAGE_EXTENSIONS"]
            if not allowed_image_file(profile_photo.filename, allowed_ext):
                flash("Unsupported profile image. Please upload PNG, JPG, JPEG, or WebP.", "danger")
                return render_template("dashboard/settings.html", notification_preferences=preferences)
            if not is_within_max_size(profile_photo, current_app.config["MAX_CONTENT_LENGTH"]):
                flash("Profile image is too large.", "danger")
                return render_template("dashboard/settings.html", notification_preferences=preferences)

            upload_dir = current_app.config["UPLOAD_FOLDER"]
            os.makedirs(upload_dir, exist_ok=True)
            extension = profile_photo.filename.rsplit(".", 1)[1].lower()
            stored_name = f"profile-{uuid.uuid4().hex}.{extension}"
            profile_photo.save(os.path.join(upload_dir, stored_name))
            current_user.profile_image_path = f"images/uploads/{stored_name}"

        current_user.notification_preferences = json.dumps({
            preference: request.form.get(preference) == "on"
            for preference in notification_names
        })

        db.session.commit()
        flash("Profile changes saved. Settings saved.", "success")
        return redirect(url_for("dashboard.settings"))

    return render_template("dashboard/settings.html", notification_preferences=preferences)


@dashboard_bp.route("/notifications", methods=["GET", "POST"])
@login_required
def notifications():
    if current_user.is_buyer():
        flash("Buyer accounts do not have access to the dashboard.", "warning")
        return redirect(url_for("public.landing"))
    if not current_user.is_farmer():
        return "Access denied: farmer account required.", 403

    notification_names = (
        "disease_alert", "weather_warning", "community_reply", "weekly_report",
        "email_delivery", "sms_delivery", "whatsapp_delivery", "push_delivery",
    )
    preferences = json.loads(current_user.notification_preferences or "{}")

    if request.method == "POST":
        current_user.notification_preferences = json.dumps({
            preference: request.form.get(preference) == "on"
            for preference in notification_names
        })
        db.session.commit()
        flash("Notification preferences saved.", "success")
        return redirect(url_for("dashboard.notifications"))

    return render_template(
        "dashboard/notifications.html",
        notification_preferences=preferences,
    )


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


@dashboard_bp.route("/upgrade")
@login_required
def upgrade():
    return render_template("dashboard/upgrade.html")
