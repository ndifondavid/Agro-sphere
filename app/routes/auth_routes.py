from flask import Blueprint, render_template, request, redirect, url_for, flash

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        if email and password:
            flash("Login successful", "success")
            return redirect(url_for("public.landing"))
        flash("Please enter your email and password.", "danger")
    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        if name and email and password:
            flash("Account created successfully", "success")
            return redirect(url_for("auth.login"))
        flash("Please complete all fields.", "danger")
    return render_template("auth/register.html")
