"""
Authentication routes (FR-1.x; SDS Section 6.1 - Login/Registration Screen).

Session handling: Flask's signed session cookies manage login state via
Flask-Login; sessions are cleared on logout (FR-1.3, FR-1.6; SDS Section 7).
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from app.extensions import db
from app.models.user import User, VALID_ROLES
from app.utils.validators import require_fields

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        missing = require_fields(request.form, ["email", "password"])
        if missing:
            flash("Please fill in all fields.", "danger")
            return render_template("auth/login.html")

        user = User.query.filter_by(email=email).first()
        if user is None or not user.check_password(password):
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html")

        login_user(user)
        return redirect(url_for("dashboard.index"))

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        role = request.form.get("role") or ""

        missing = require_fields(request.form, ["name", "email", "password", "role"])
        if missing or role not in VALID_ROLES:
            flash("Please complete all fields with a valid role.", "danger")
            return render_template("auth/register.html")

        if User.query.filter_by(email=email).first() is not None:
            flash("An account with that email already exists.", "danger")
            return render_template("auth/register.html")

        user = User(name=name, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        return redirect(url_for("dashboard.index"))

    return render_template("auth/register.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
