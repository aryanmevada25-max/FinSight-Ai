from decimal import Decimal

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from forms.income import IncomeForm
from models import db
from models.income import Income
from utils.helpers import format_currency


income = Blueprint("income", __name__, url_prefix="/income")


def get_owned_income_or_404(income_id: int) -> Income:
    """Return an income entry only when it belongs to the signed-in user."""
    record = db.session.scalar(
        select(Income).where(
            Income.id == income_id,
            Income.user_id == current_user.id,
        )
    )
    if record is None:
        abort(404)
    return record


@income.route("/")
@login_required
def index():
    return redirect(url_for("ui.app", path="transactions"))


def legacy_index():
    records = db.session.scalars(
        select(Income)
        .where(Income.user_id == current_user.id)
        .order_by(Income.income_date.desc(), Income.id.desc())
    ).all()
    total = sum((record.amount for record in records), Decimal("0.00"))
    return render_template(
        "income.html",
        incomes=records,
        total_income=format_currency(total),
    )


@income.route("/new", methods=["GET", "POST"])
@login_required
def create():
    form = IncomeForm()
    if form.validate_on_submit():
        record = Income(
            amount=form.amount.data,
            source=form.source.data,
            description=(form.description.data or "").strip() or None,
            income_date=form.income_date.data,
            user_id=current_user.id,
        )
        db.session.add(record)
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash("The income could not be saved. Please try again.", "danger")
            return render_template("income_form.html", form=form, income=None), 500

        flash("Income added successfully.", "success")
        return redirect(url_for("income.index"))

    status_code = 422 if request.method == "POST" else 200
    return render_template("income_form.html", form=form, income=None), status_code


@income.route("/<int:income_id>/edit", methods=["GET", "POST"])
@login_required
def edit(income_id: int):
    record = get_owned_income_or_404(income_id)
    form = IncomeForm(obj=record)

    if form.validate_on_submit():
        record.amount = form.amount.data
        record.source = form.source.data
        record.description = (form.description.data or "").strip() or None
        record.income_date = form.income_date.data
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash("The income could not be updated. Please try again.", "danger")
            return render_template("income_form.html", form=form, income=record), 500

        flash("Income updated successfully.", "success")
        return redirect(url_for("income.index"))

    status_code = 422 if request.method == "POST" else 200
    return render_template("income_form.html", form=form, income=record), status_code


@income.route("/<int:income_id>/delete", methods=["POST"])
@login_required
def delete(income_id: int):
    record = get_owned_income_or_404(income_id)
    db.session.delete(record)
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash("The income could not be deleted. Please try again.", "danger")
    else:
        flash("Income deleted successfully.", "success")
    return redirect(url_for("income.index"))
