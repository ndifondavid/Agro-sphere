from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user

from app.models.user import User, REGISTRABLE_ROLES

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("public.landing"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        remember = request.form.get("remember") == "1"

        if not email or not password:
            flash("Please enter your email and password.", "danger")
            return render_template("auth/login.html")

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            if not getattr(user, "is_active", True):
                flash("This account has been deactivated by an administrator.", "warning")
                return render_template("auth/login.html")

            login_user(user, remember=remember)
            flash("Login successful", "success")

            if user.is_buyer():
                return redirect(url_for("marketplace.browse"))
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

        if len(name) < 2:
            flash("Please enter a valid name with at least 2 characters.", "danger")
            return render_template("auth/register.html")

        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "danger")
            return render_template("auth/register.html")

        if role not in REGISTRABLE_ROLES:
            flash("Please choose a valid account role.", "danger")
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


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()

        if not email:
            flash("Please enter your email address.", "danger")
            return render_template("auth/forgot_password.html")

        user = User.query.filter_by(email=email).first()
        if user is not None:
            flash("If that email matches an account, a password reset link has been sent.", "success")
        else:
            flash("If that email matches an account, a password reset link has been sent.", "success")

        return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html")
