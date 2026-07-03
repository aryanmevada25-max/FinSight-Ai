from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from forms.profile import ProfileForm
from models import db
from models.user import User


profile = Blueprint("profile", __name__)


@profile.route("/profile", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "GET":
        return redirect(url_for("ui.app", path="profile"))

    form = ProfileForm(obj=current_user)

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        existing_user = db.session.scalar(
            select(User).where(
                func.lower(User.email) == email,
                User.id != current_user.id,
            )
        )
        if existing_user:
            form.email.errors.append("This email address is already in use.")
        else:
            current_user.name = form.name.data.strip()
            current_user.email = email
            current_user.currency = form.currency.data
            current_user.monthly_budget = form.monthly_budget.data
            try:
                db.session.commit()
            except SQLAlchemyError:
                db.session.rollback()
                flash("Profile could not be updated. Please try again.", "danger")
                return render_template("profile.html", form=form), 500

            flash("Profile updated successfully.", "success")
            return redirect(url_for("profile.index"))

    status_code = 422 if request.method == "POST" else 200
    return render_template("profile.html", form=form), status_code
