"""
AI-Based Disease Detection & Scan History routes (FR-3.x, FR-4.x).

Implements the sequence in SDS Section 5.1 (Figure 5) and the activity flow
in Section 5.2 (Figure 6): validate image -> call AI Tier -> persist Scan ->
display diagnosis. "Scan Leaf for Disease" includes "View Scan History &
Analytics" since every successful scan is written to history (FR-3.6).
"""
import os
import uuid

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user

from app.extensions import db
from app.models.crop import Crop
from app.models.scan import Scan
from app.utils.decorators import roles_required
from app.utils.validators import allowed_image_file, is_within_max_size
from app.ai.disease_detector import predict_disease

scan_bp = Blueprint("scan", __name__, url_prefix="/scan")


@scan_bp.route("/", methods=["GET", "POST"])
@login_required
@roles_required("farmer")
def scan_leaf():
    farms = current_user.farms
    crops = [c for f in farms for c in f.crops]

    if not farms:
        flash("Create a farm before scanning a crop.", "warning")
        return redirect(url_for("farm.create_farm"))

    if not crops:
        flash("Add at least one crop to your farm before scanning.", "warning")
        return redirect(url_for("farm.list_farms"))

    if request.method == "POST":
        crop_id = request.form.get("crop_id") or (crops[0].id if crops else None)
        photo = request.files.get("photo")

        # --- Input validation branch (FR-3.5) ---
        if not crop_id:
            flash("Please select a farm/crop for this scan.", "danger")
            return render_template("scan/scan.html", crops=crops)

        if photo is None or photo.filename == "":
            flash("Please choose a photo to scan.", "danger")
            return render_template("scan/scan.html", crops=crops)

        allowed_ext = current_app.config["ALLOWED_IMAGE_EXTENSIONS"]
        if not allowed_image_file(photo.filename, allowed_ext):
            flash("Unsupported file type. Please upload a PNG or JPG image.", "danger")
            return render_template("scan/scan.html", crops=crops)

        if not is_within_max_size(photo, current_app.config["MAX_CONTENT_LENGTH"]):
            flash("Image is too large.", "danger")
            return render_template("scan/scan.html", crops=crops)

        crop = Crop.query.get_or_404(int(crop_id))

        # --- Persist the uploaded image ---
        upload_dir = current_app.config["UPLOAD_FOLDER"]
        os.makedirs(upload_dir, exist_ok=True)
        ext = photo.filename.rsplit(".", 1)[1].lower()
        stored_name = f"{uuid.uuid4().hex}.{ext}"
        stored_path = os.path.join(upload_dir, stored_name)
        photo.save(stored_path)

        # --- AI Tier inference (FR-3.2) ---
        result = predict_disease(
            image_path=stored_path,
            model_path=current_app.config["AI_MODEL_PATH"],
            confidence_threshold=current_app.config["AI_CONFIDENCE_THRESHOLD"],
        )

        # --- Persist Scan record (FR-3.6) ---
        scan = Scan(
            crop_id=crop.id,
            image_path=os.path.join("images", "uploads", stored_name),
            predicted_disease=result.predicted_disease,
            confidence_score=result.confidence_score,
            recommendation=result.recommendation,
        )
        db.session.add(scan)
        db.session.commit()

        return render_template("scan/scan.html", crops=crops, scan=scan, crop=crop)

    return render_template("scan/scan.html", crops=crops, scan=None)


@scan_bp.route("/history")
@login_required
@roles_required("farmer")
def history():
    crop_ids = [c.id for f in current_user.farms for c in f.crops]
    scans = (
        Scan.query.filter(Scan.crop_id.in_(crop_ids)).order_by(Scan.timestamp.desc()).all()
        if crop_ids
        else []
    )
    return render_template("scan/history.html", scans=scans)
