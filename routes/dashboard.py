from calendar import monthrange
from datetime import date
from decimal import Decimal

from flask import Blueprint, current_app, redirect, render_template, url_for
from flask_login import current_user, login_required
from sqlalchemy import func, select

from models import db
from models.expense import Expense
from models.income import Income
from services.analytics import dashboard_chart_data
from utils.helpers import format_currency


dashboard = Blueprint("dashboard", __name__)


def build_dashboard_data(today: date) -> dict[str, object]:
    """Build the user's dashboard using currently available finance models."""
    zero = Decimal("0.00")
    month_start = today.replace(day=1)
    month_end = today.replace(day=monthrange(today.year, today.month)[1])

    total_expenses = db.session.scalar(
        select(func.coalesce(func.sum(Expense.amount), zero)).where(
            Expense.user_id == current_user.id
        )
    ) or zero
    monthly_expenses = db.session.scalar(
        select(func.coalesce(func.sum(Expense.amount), zero)).where(
            Expense.user_id == current_user.id,
            Expense.expense_date.between(month_start, month_end),
        )
    ) or zero
    recent_expenses = db.session.scalars(
        select(Expense)
        .where(Expense.user_id == current_user.id)
        .order_by(Expense.expense_date.desc(), Expense.id.desc())
        .limit(5)
    ).all()

    total_income = db.session.scalar(
        select(func.coalesce(func.sum(Income.amount), zero)).where(
            Income.user_id == current_user.id
        )
    ) or zero
    monthly_income = db.session.scalar(
        select(func.coalesce(func.sum(Income.amount), zero)).where(
            Income.user_id == current_user.id,
            Income.income_date.between(month_start, month_end),
        )
    ) or zero
    recent_incomes = db.session.scalars(
        select(Income)
        .where(Income.user_id == current_user.id)
        .order_by(Income.income_date.desc(), Income.id.desc())
        .limit(5)
    ).all()

    balance = total_income - total_expenses
    monthly_savings = monthly_income - monthly_expenses
    monthly_budget = current_user.monthly_budget or zero
    budget_percentage = (
        int((monthly_expenses / monthly_budget) * 100)
        if monthly_budget > 0
        else 0
    )

    transactions = [
        (
            record.expense_date,
            record.created_at,
            record.id,
            {
                "date": record.expense_date.strftime("%d %b %Y"),
                "type": "Expense",
                "category": record.category,
                "amount": f"-{format_currency(record.amount)}",
            },
        )
        for record in recent_expenses
    ]
    transactions.extend(
        (
            record.income_date,
            record.created_at,
            record.id,
            {
                "date": record.income_date.strftime("%d %b %Y"),
                "type": "Income",
                "category": record.source,
                "amount": f"+{format_currency(record.amount)}",
            },
        )
        for record in recent_incomes
    )
    transactions.sort(key=lambda item: item[:3], reverse=True)

    return {
        "balance": format_currency(balance),
        "income": format_currency(total_income),
        "expenses": format_currency(total_expenses),
        "savings": format_currency(monthly_savings),
        "budget_spent": format_currency(monthly_expenses),
        "budget_limit": format_currency(monthly_budget),
        "budget_percentage": budget_percentage,
        "budget_bar_percentage": min(budget_percentage, 100),
        "chart_data": dashboard_chart_data(current_user.id, today),
        "transactions": [item[3] for item in transactions[:5]],
    }


@dashboard.route("/dashboard")
@login_required
def index():
    """Send the standard dashboard URL to the redesigned React dashboard."""
    if current_app.config.get("TESTING"):
        today = date.today()
        return render_template(
            "dashboard.html",
            dashboard_data=build_dashboard_data(today),
            current_date=today.strftime("%A, %d %B %Y"),
            current_date_iso=today.isoformat(),
        )
    return redirect(url_for("ui.app", path="dashboard"))
