from datetime import date
from decimal import Decimal

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func, or_, select
from sqlalchemy.exc import SQLAlchemyError

from forms.expense import ExpenseForm
from models import db
from models.expense import EXPENSE_CATEGORIES, Expense
from utils.helpers import format_currency


expense = Blueprint("expense", __name__, url_prefix="/expenses")


def get_owned_expense_or_404(expense_id: int) -> Expense:
    """Return an expense only when it belongs to the signed-in user."""
    record = db.session.scalar(
        select(Expense).where(
            Expense.id == expense_id,
            Expense.user_id == current_user.id,
        )
    )
    if record is None:
        abort(404)
    return record


def parse_date_filter(value: str, label: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        flash(f"The {label} date filter is invalid.", "warning")
        return None


def build_expense_query(
    search_term: str,
    category: str,
    start_date: date | None,
    end_date: date | None,
):
    statement = select(Expense).where(Expense.user_id == current_user.id)

    if search_term:
        pattern = f"%{search_term}%"
        statement = statement.where(
            or_(
                Expense.description.ilike(pattern),
                Expense.category.ilike(pattern),
            )
        )
    if category in EXPENSE_CATEGORIES:
        statement = statement.where(Expense.category == category)
    if start_date:
        statement = statement.where(Expense.expense_date >= start_date)
    if end_date:
        statement = statement.where(Expense.expense_date <= end_date)

    return statement.order_by(Expense.expense_date.desc(), Expense.id.desc())


@expense.route("/")
@login_required
def index():
    return redirect(url_for("ui.app", path="transactions"))


def legacy_index():
    search_term = request.args.get("q", "").strip()[:100]
    category = request.args.get("category", "").strip()
    start_date_value = request.args.get("start_date", "").strip()
    end_date_value = request.args.get("end_date", "").strip()
    start_date = parse_date_filter(start_date_value, "start")
    end_date = parse_date_filter(end_date_value, "end")

    if start_date and end_date and start_date > end_date:
        flash("The start date must be before the end date.", "warning")
        start_date = end_date = None

    expenses = db.session.scalars(
        build_expense_query(search_term, category, start_date, end_date)
    ).all()
    total = sum((record.amount for record in expenses), Decimal("0.00"))

    return render_template(
        "expenses.html",
        expenses=expenses,
        categories=EXPENSE_CATEGORIES,
        filters={
            "q": search_term,
            "category": category,
            "start_date": start_date_value,
            "end_date": end_date_value,
        },
        filtered_total=format_currency(total),
    )


@expense.route("/new", methods=["GET", "POST"])
@login_required
def create():
    form = ExpenseForm()
    if form.validate_on_submit():
        record = Expense(
            amount=form.amount.data,
            category=form.category.data,
            description=(form.description.data or "").strip() or None,
            expense_date=form.expense_date.data,
            user_id=current_user.id,
        )
        db.session.add(record)
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash("The expense could not be saved. Please try again.", "danger")
            return render_template("expense_form.html", form=form, expense=None), 500

        flash("Expense added successfully.", "success")
        return redirect(url_for("expense.index"))

    status_code = 422 if request.method == "POST" else 200
    return render_template("expense_form.html", form=form, expense=None), status_code


@expense.route("/<int:expense_id>/edit", methods=["GET", "POST"])
@login_required
def edit(expense_id: int):
    record = get_owned_expense_or_404(expense_id)
    form = ExpenseForm(obj=record)

    if form.validate_on_submit():
        record.amount = form.amount.data
        record.category = form.category.data
        record.description = (form.description.data or "").strip() or None
        record.expense_date = form.expense_date.data
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash("The expense could not be updated. Please try again.", "danger")
            return render_template("expense_form.html", form=form, expense=record), 500

        flash("Expense updated successfully.", "success")
        return redirect(url_for("expense.index"))

    status_code = 422 if request.method == "POST" else 200
    return render_template(
        "expense_form.html", form=form, expense=record
    ), status_code


@expense.route("/<int:expense_id>/delete", methods=["POST"])
@login_required
def delete(expense_id: int):
    record = get_owned_expense_or_404(expense_id)
    db.session.delete(record)
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash("The expense could not be deleted. Please try again.", "danger")
    else:
        flash("Expense deleted successfully.", "success")
    return redirect(url_for("expense.index"))
