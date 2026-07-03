from calendar import monthrange
from datetime import date
from decimal import Decimal

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from forms.budget import BudgetForm
from models import db
from models.expense import Expense
from utils.helpers import format_currency


budget = Blueprint("budget", __name__, url_prefix="/budget")


def calculate_budget_progress(monthly_budget: Decimal) -> dict[str, object]:
    """Return current user's monthly budget progress values."""
    today = date.today()
    month_start = today.replace(day=1)
    month_end = today.replace(day=monthrange(today.year, today.month)[1])
    spent = db.session.scalar(
        select(func.coalesce(func.sum(Expense.amount), Decimal("0.00"))).where(
            Expense.user_id == current_user.id,
            Expense.expense_date.between(month_start, month_end),
        )
    ) or Decimal("0.00")
    percentage = (
        int((spent / monthly_budget) * 100)
        if monthly_budget and monthly_budget > 0
        else 0
    )

    return {
        "spent": spent,
        "remaining": monthly_budget - spent,
        "percentage": percentage,
        "bar_percentage": min(percentage, 100),
    }


@budget.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "GET":
        return redirect(url_for("ui.app", path="budget"))

    form = BudgetForm(obj=current_user)

    if form.validate_on_submit():
        current_user.monthly_budget = form.monthly_budget.data
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash("The budget could not be saved. Please try again.", "danger")
            return render_template(
                "budget.html",
                form=form,
                progress=calculate_budget_progress(
                    current_user.monthly_budget or Decimal("0.00")
                ),
                format_currency=format_currency,
            ), 500

        flash("Monthly budget updated successfully.", "success")
        return redirect(url_for("budget.index"))

    status_code = 422 if request.method == "POST" else 200
    monthly_budget = current_user.monthly_budget or Decimal("0.00")
    return render_template(
        "budget.html",
        form=form,
        progress=calculate_budget_progress(monthly_budget),
        format_currency=format_currency,
    ), status_code
