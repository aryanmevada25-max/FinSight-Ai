from datetime import date
from decimal import Decimal, InvalidOperation
import re

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_user, logout_user
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from models import db
from models.expense import EXPENSE_CATEGORIES, Expense
from models.income import INCOME_SOURCES, Income
from models.user import User
from services.analytics import dashboard_chart_data, financial_summary
from services.gemini_service import generate_budget_advice


api = Blueprint("api", __name__, url_prefix="/api")
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
CURRENCIES = {"INR": "₹", "USD": "$", "EUR": "€", "GBP": "£"}


def error(message: str, status: int = 400, fields=None):
    return jsonify({"ok": False, "message": message, "fields": fields or {}}), status


def require_user():
    if not current_user.is_authenticated:
        return error("Please log in to continue.", 401)
    return None


def number(value, field: str, allow_zero: bool = False):
    try:
        result = Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"Enter a valid {field}.") from None
    if result < 0 or (result == 0 and not allow_zero):
        raise ValueError(f"{field.capitalize()} must be greater than zero.")
    return result


def iso_date(value, field: str):
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        raise ValueError(f"Enter a valid {field} date.") from None


def transaction_json(item):
    amount = float(item["amount"])
    return {
        "id": item["id"],
        "type": item["type"].lower(),
        "category": item["category"],
        "description": item.get("description") or item["category"],
        "date": item["date"].isoformat(),
        "amount": amount,
        "status": "Completed",
    }


@api.get("/session")
def session():
    if not current_user.is_authenticated:
        return jsonify({"authenticated": False})
    return jsonify(
        {
            "authenticated": True,
            "user": {
                "id": current_user.id,
                "name": current_user.name,
                "email": current_user.email,
                "currency": current_user.currency,
                "currencySymbol": CURRENCIES.get(current_user.currency, "₹"),
            },
        }
    )


@api.post("/auth/login")
def login():
    if current_user.is_authenticated:
        return jsonify({"ok": True})
    payload = request.get_json(silent=True) or {}
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))
    if not EMAIL_PATTERN.fullmatch(email) or not password:
        return error("Enter a valid email address and password.", 422)
    user = db.session.scalar(select(User).where(func.lower(User.email) == email))
    if not user or not user.check_password(password):
        return error("Invalid email address or password.", 401)
    login_user(user, remember=bool(payload.get("remember")))
    return jsonify({"ok": True, "message": f"Welcome back, {user.name}."})


@api.post("/auth/register")
def register():
    if current_user.is_authenticated:
        return jsonify({"ok": True})
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "")).strip()
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))
    confirm = str(payload.get("confirmPassword", ""))
    fields = {}
    if len(name) < 2:
        fields["name"] = "Enter your full name."
    if not EMAIL_PATTERN.fullmatch(email):
        fields["email"] = "Enter a valid email address."
    if len(password) < 8:
        fields["password"] = "Use at least 8 characters."
    if password != confirm:
        fields["confirmPassword"] = "Passwords must match."
    if fields:
        return error("Please check the highlighted fields.", 422, fields)
    if db.session.scalar(select(User).where(func.lower(User.email) == email)):
        return error("An account with this email already exists.", 409, {"email": "Email already exists."})
    user = User(name=name, email=email, currency="INR")
    user.set_password(password)
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error("An account with this email already exists.", 409)
    except SQLAlchemyError:
        db.session.rollback()
        return error("We could not create your account.", 500)
    login_user(user)
    return jsonify({"ok": True, "message": "Your FinSight AI account is ready."}), 201


@api.post("/auth/logout")
def logout():
    logout_user()
    return jsonify({"ok": True})


@api.get("/dashboard")
def dashboard():
    unauthorized = require_user()
    if unauthorized:
        return unauthorized
    today = date.today()
    summary = financial_summary(current_user, today)
    charts = dashboard_chart_data(current_user.id, today)
    budget = float(summary["monthly_budget"])
    expenses = float(summary["monthly_expenses"])
    savings = float(summary["monthly_savings"])
    balance = float(summary["balance"])
    score = 45
    score += 18 if balance >= 0 else 0
    score += 18 if savings > 0 else 5
    score += 14 if budget and expenses <= budget else 4
    score += 5 if float(summary["monthly_income"]) > 0 else 0
    score = min(score, 98)
    categories = [
        {"name": item["category"], "spent": float(item["total"])}
        for item in summary["expense_categories"]
    ]
    recommendation = (
        f"Reduce {summary['top_expense_category']['category']} spending by 10% this month."
        if summary["top_expense_category"]
        else "Add your first transaction to unlock personalized AI insights."
    )
    return jsonify(
        {
            "user": {"name": current_user.name, "currency": current_user.currency},
            "date": today.isoformat(),
            "metrics": {
                "balance": balance,
                "income": float(summary["total_income"]),
                "expense": float(summary["total_expenses"]),
                "savings": savings,
            },
            "health": {
                "score": score,
                "insight": recommendation,
                "prediction": max(savings * 12, 0),
            },
            "budget": {
                "limit": budget,
                "spent": expenses,
                "percentage": summary["budget_percentage"],
                "categories": categories,
            },
            "charts": charts,
            "transactions": [transaction_json(item) for item in summary["recent_transactions"]],
        }
    )


@api.get("/transactions")
def transactions():
    unauthorized = require_user()
    if unauthorized:
        return unauthorized
    expenses = db.session.scalars(
        select(Expense).where(Expense.user_id == current_user.id).order_by(Expense.expense_date.desc(), Expense.id.desc())
    ).all()
    incomes = db.session.scalars(
        select(Income).where(Income.user_id == current_user.id).order_by(Income.income_date.desc(), Income.id.desc())
    ).all()
    return jsonify(
        {
            "expenses": [
                {"id": row.id, "amount": float(row.amount), "category": row.category, "description": row.description or "", "date": row.expense_date.isoformat()}
                for row in expenses
            ],
            "incomes": [
                {"id": row.id, "amount": float(row.amount), "source": row.source, "description": row.description or "", "date": row.income_date.isoformat()}
                for row in incomes
            ],
            "expenseCategories": EXPENSE_CATEGORIES,
            "incomeSources": INCOME_SOURCES,
        }
    )


def save_transaction(kind: str, record=None):
    payload = request.get_json(silent=True) or {}
    try:
        amount = number(payload.get("amount"), "amount")
        entry_date = iso_date(payload.get("date"), kind)
    except ValueError as exc:
        return error(str(exc), 422)
    description = str(payload.get("description", "")).strip()[:255] or None
    if kind == "expense":
        category = str(payload.get("category", ""))
        if category not in EXPENSE_CATEGORIES:
            return error("Choose a valid expense category.", 422)
        record = record or Expense(user_id=current_user.id)
        record.category, record.expense_date = category, entry_date
    else:
        source = str(payload.get("source", ""))
        if source not in INCOME_SOURCES:
            return error("Choose a valid income source.", 422)
        record = record or Income(user_id=current_user.id)
        record.source, record.income_date = source, entry_date
    record.amount, record.description = amount, description
    db.session.add(record)
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return error(f"The {kind} could not be saved.", 500)
    return jsonify({"ok": True, "id": record.id})


def owned(model, record_id):
    return db.session.scalar(select(model).where(model.id == record_id, model.user_id == current_user.id))


@api.post("/expenses")
def create_expense():
    unauthorized = require_user()
    return unauthorized or save_transaction("expense")


@api.put("/expenses/<int:record_id>")
def update_expense(record_id):
    unauthorized = require_user()
    if unauthorized:
        return unauthorized
    record = owned(Expense, record_id)
    return error("Expense not found.", 404) if not record else save_transaction("expense", record)


@api.delete("/expenses/<int:record_id>")
def delete_expense(record_id):
    return delete_transaction(Expense, record_id, "Expense")


@api.post("/incomes")
def create_income():
    unauthorized = require_user()
    return unauthorized or save_transaction("income")


@api.put("/incomes/<int:record_id>")
def update_income(record_id):
    unauthorized = require_user()
    if unauthorized:
        return unauthorized
    record = owned(Income, record_id)
    return error("Income not found.", 404) if not record else save_transaction("income", record)


@api.delete("/incomes/<int:record_id>")
def delete_income(record_id):
    return delete_transaction(Income, record_id, "Income")


def delete_transaction(model, record_id, label):
    unauthorized = require_user()
    if unauthorized:
        return unauthorized
    record = owned(model, record_id)
    if not record:
        return error(f"{label} not found.", 404)
    db.session.delete(record)
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return error(f"{label} could not be deleted.", 500)
    return jsonify({"ok": True})


@api.get("/budget")
def get_budget():
    unauthorized = require_user()
    if unauthorized:
        return unauthorized
    summary = financial_summary(current_user)
    return jsonify({"limit": float(summary["monthly_budget"]), "spent": float(summary["monthly_expenses"]), "percentage": summary["budget_percentage"]})


@api.put("/budget")
def update_budget():
    unauthorized = require_user()
    if unauthorized:
        return unauthorized
    try:
        current_user.monthly_budget = number((request.get_json(silent=True) or {}).get("amount"), "budget", True)
        db.session.commit()
    except ValueError as exc:
        return error(str(exc), 422)
    except SQLAlchemyError:
        db.session.rollback()
        return error("Budget could not be updated.", 500)
    return jsonify({"ok": True})


@api.get("/profile")
def get_profile():
    unauthorized = require_user()
    if unauthorized:
        return unauthorized
    return jsonify({"name": current_user.name, "email": current_user.email, "currency": current_user.currency, "monthlyBudget": float(current_user.monthly_budget or 0)})


@api.put("/profile")
def update_profile():
    unauthorized = require_user()
    if unauthorized:
        return unauthorized
    payload = request.get_json(silent=True) or {}
    name, email = str(payload.get("name", "")).strip(), str(payload.get("email", "")).strip().lower()
    currency = str(payload.get("currency", "INR"))
    if len(name) < 2 or not EMAIL_PATTERN.fullmatch(email) or currency not in CURRENCIES:
        return error("Enter valid profile details.", 422)
    duplicate = db.session.scalar(select(User).where(func.lower(User.email) == email, User.id != current_user.id))
    if duplicate:
        return error("This email address is already in use.", 409)
    try:
        budget = number(payload.get("monthlyBudget", 0), "budget", True)
        current_user.name, current_user.email = name, email
        current_user.currency, current_user.monthly_budget = currency, budget
        db.session.commit()
    except ValueError as exc:
        return error(str(exc), 422)
    except SQLAlchemyError:
        db.session.rollback()
        return error("Profile could not be updated.", 500)
    return jsonify({"ok": True})


@api.get("/advisor")
def advisor():
    unauthorized = require_user()
    if unauthorized:
        return unauthorized
    summary = financial_summary(current_user)
    result = generate_budget_advice(summary)
    return jsonify({"advice": result, "scoreContext": {"balance": float(summary["balance"]), "savings": float(summary["monthly_savings"])}})
