from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user

from app.models.user import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        if not email or not password:
            flash("Please enter your email and password.", "danger")
            return render_template("auth/login.html")

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            if user.is_buyer():
                logout_user()
                flash("Buyer access is restricted. Please use a farmer or admin account.", "warning")
                return redirect(url_for("public.landing"))

            login_user(user)
            flash("Login successful", "success")

            if user.is_farmer():
                return redirect(url_for("dashboard.index"))
            if user.is_admin():
                return redirect(url_for("admin.index"))
            return redirect(url_for("public.landing"))

        flash("Invalid email or password.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        role = (request.form.get("role") or "farmer").strip().lower()

        if not name or not email or not password:
            flash("Please complete all fields.", "danger")
            return render_template("auth/register.html")

        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "danger")
            return render_template("auth/register.html")

        user = User(name=name, email=email, role=role)
        user.set_password(password)
        from app.extensions import db

        db.session.add(user)
        db.session.commit()

        flash("Account created successfully", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")
