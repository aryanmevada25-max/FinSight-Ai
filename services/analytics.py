from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select

from models import db
from models.expense import Expense
from models.income import Income


ZERO = Decimal("0.00")


def month_bounds(day: date) -> tuple[date, date]:
    start = day.replace(day=1)
    end = day.replace(day=monthrange(day.year, day.month)[1])
    return start, end


def decimal_sum(statement) -> Decimal:
    return db.session.scalar(statement) or ZERO


def income_total(user_id: int, start: date | None = None, end: date | None = None):
    statement = select(func.coalesce(func.sum(Income.amount), ZERO)).where(
        Income.user_id == user_id
    )
    if start:
        statement = statement.where(Income.income_date >= start)
    if end:
        statement = statement.where(Income.income_date <= end)
    return decimal_sum(statement)


def expense_total(user_id: int, start: date | None = None, end: date | None = None):
    statement = select(func.coalesce(func.sum(Expense.amount), ZERO)).where(
        Expense.user_id == user_id
    )
    if start:
        statement = statement.where(Expense.expense_date >= start)
    if end:
        statement = statement.where(Expense.expense_date <= end)
    return decimal_sum(statement)


def recent_transactions(user_id: int, limit: int = 5) -> list[dict[str, object]]:
    expenses = db.session.scalars(
        select(Expense)
        .where(Expense.user_id == user_id)
        .order_by(Expense.expense_date.desc(), Expense.id.desc())
        .limit(limit)
    ).all()
    incomes = db.session.scalars(
        select(Income)
        .where(Income.user_id == user_id)
        .order_by(Income.income_date.desc(), Income.id.desc())
        .limit(limit)
    ).all()

    transactions = [
        {
            "date_obj": record.expense_date,
            "created_at": record.created_at,
            "id": record.id,
            "date": record.expense_date,
            "type": "Expense",
            "category": record.category,
            "description": record.description,
            "amount": -record.amount,
        }
        for record in expenses
    ]
    transactions.extend(
        {
            "date_obj": record.income_date,
            "created_at": record.created_at,
            "id": record.id,
            "date": record.income_date,
            "type": "Income",
            "category": record.source,
            "description": record.description,
            "amount": record.amount,
        }
        for record in incomes
    )
    transactions.sort(
        key=lambda item: (item["date_obj"], item["created_at"], item["id"]),
        reverse=True,
    )
    return transactions[:limit]


def transactions_in_range(
    user_id: int,
    start: date | None = None,
    end: date | None = None,
) -> list[dict[str, object]]:
    expense_statement = select(Expense).where(Expense.user_id == user_id)
    income_statement = select(Income).where(Income.user_id == user_id)

    if start:
        expense_statement = expense_statement.where(Expense.expense_date >= start)
        income_statement = income_statement.where(Income.income_date >= start)
    if end:
        expense_statement = expense_statement.where(Expense.expense_date <= end)
        income_statement = income_statement.where(Income.income_date <= end)

    expenses = db.session.scalars(expense_statement).all()
    incomes = db.session.scalars(income_statement).all()
    transactions = [
        {
            "date_obj": record.expense_date,
            "created_at": record.created_at,
            "id": record.id,
            "date": record.expense_date,
            "type": "Expense",
            "category": record.category,
            "description": record.description,
            "amount": -record.amount,
        }
        for record in expenses
    ]
    transactions.extend(
        {
            "date_obj": record.income_date,
            "created_at": record.created_at,
            "id": record.id,
            "date": record.income_date,
            "type": "Income",
            "category": record.source,
            "description": record.description,
            "amount": record.amount,
        }
        for record in incomes
    )
    transactions.sort(
        key=lambda item: (item["date_obj"], item["created_at"], item["id"]),
        reverse=True,
    )
    return transactions


def expense_categories(user_id: int) -> list[dict[str, object]]:
    rows = db.session.execute(
        select(Expense.category, func.coalesce(func.sum(Expense.amount), ZERO))
        .where(Expense.user_id == user_id)
        .group_by(Expense.category)
        .order_by(func.sum(Expense.amount).desc())
    ).all()
    return [{"category": category, "total": total} for category, total in rows]


def monthly_spending(user_id: int, today: date, months: int = 6):
    values = []
    cursor = today.replace(day=1)
    for _ in range(months):
        start, end = month_bounds(cursor)
        values.append(
            {
                "label": start.strftime("%b %Y"),
                "total": expense_total(user_id, start, end),
            }
        )
        cursor = (start - timedelta(days=1)).replace(day=1)
    return list(reversed(values))


def weekly_spending(user_id: int, today: date, weeks: int = 4):
    values = []
    week_start = today - timedelta(days=today.weekday())
    for index in range(weeks):
        start = week_start - timedelta(days=7 * index)
        end = start + timedelta(days=6)
        values.append(
            {
                "label": f"{start.strftime('%d %b')}–{end.strftime('%d %b')}",
                "total": expense_total(user_id, start, end),
            }
        )
    return list(reversed(values))


def dashboard_chart_data(user_id: int, today: date) -> dict[str, object]:
    total_income = income_total(user_id)
    total_expenses = expense_total(user_id)
    categories = expense_categories(user_id)
    monthly = monthly_spending(user_id, today)
    weekly = weekly_spending(user_id, today)

    return {
        "incomeVsExpense": {
            "labels": ["Income", "Expenses"],
            "values": [float(total_income), float(total_expenses)],
        },
        "expenseCategories": {
            "labels": [item["category"] for item in categories],
            "values": [float(item["total"]) for item in categories],
        },
        "monthlySpending": {
            "labels": [item["label"] for item in monthly],
            "values": [float(item["total"]) for item in monthly],
        },
        "weeklySpending": {
            "labels": [item["label"] for item in weekly],
            "values": [float(item["total"]) for item in weekly],
        },
    }


def financial_summary(user, today: date | None = None) -> dict[str, object]:
    today = today or date.today()
    month_start, month_end = month_bounds(today)
    monthly_budget = user.monthly_budget or ZERO
    monthly_expenses = expense_total(user.id, month_start, month_end)
    monthly_income = income_total(user.id, month_start, month_end)
    total_income = income_total(user.id)
    total_expenses = expense_total(user.id)
    categories = expense_categories(user.id)
    top_category = categories[0] if categories else None
    budget_percentage = (
        int((monthly_expenses / monthly_budget) * 100)
        if monthly_budget > 0
        else 0
    )

    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "balance": total_income - total_expenses,
        "monthly_income": monthly_income,
        "monthly_expenses": monthly_expenses,
        "monthly_savings": monthly_income - monthly_expenses,
        "monthly_budget": monthly_budget,
        "budget_remaining": monthly_budget - monthly_expenses,
        "budget_percentage": budget_percentage,
        "top_expense_category": top_category,
        "expense_categories": categories,
        "recent_transactions": recent_transactions(user.id, 8),
    }
