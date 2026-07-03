from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from forms.auth import LoginForm, RegistrationForm
from models import db
from models.user import User


auth = Blueprint("auth", __name__)


@auth.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    if request.method == "GET" and not current_app.config.get("TESTING"):
        return redirect(url_for("ui.app", path="register"))

    form = RegistrationForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        existing_user = db.session.scalar(
            select(User).where(func.lower(User.email) == email)
        )
        if existing_user:
            form.email.errors.append("An account with this email already exists.")
            return render_template("register.html", form=form)

        user = User(name=form.name.data.strip(), email=email)
        user.set_password(form.password.data)
        db.session.add(user)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            form.email.errors.append("An account with this email already exists.")
            return render_template("register.html", form=form)
        except SQLAlchemyError:
            db.session.rollback()
            flash("We could not create your account. Please try again.", "danger")
            return render_template("register.html", form=form), 500

        flash("Account created successfully. You can now log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html", form=form)


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    if request.method == "GET" and not current_app.config.get("TESTING"):
        return redirect(url_for("ui.app", path="login"))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = db.session.scalar(
            select(User).where(func.lower(User.email) == email)
        )

        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            flash(f"Welcome back, {user.name}.", "success")
            return redirect(url_for("dashboard.index"))

        flash("Invalid email address or password.", "danger")

    return render_template("login.html", form=form)


@auth.route("/logout", methods=["POST"])
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash("You have been logged out.", "info")
    return redirect(url_for("main.home"))
