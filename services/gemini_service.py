from __future__ import annotations

from decimal import Decimal
import warnings

from flask import current_app

from utils.helpers import format_currency


def _money(value: Decimal) -> str:
    return format_currency(value)


def build_local_advice(summary: dict[str, object]) -> list[str]:
    advice = []
    monthly_income = summary["monthly_income"]
    monthly_expenses = summary["monthly_expenses"]
    monthly_savings = summary["monthly_savings"]
    monthly_budget = summary["monthly_budget"]
    budget_remaining = summary["budget_remaining"]
    budget_percentage = summary["budget_percentage"]
    top_category = summary["top_expense_category"]

    if monthly_income == 0 and monthly_expenses == 0:
        return [
            "Add your income and expenses to unlock personalized budget insights.",
            "Set a monthly budget so the advisor can compare spending against your plan.",
            "Start by tracking recurring bills first; they usually explain most monthly cash flow.",
        ]

    if monthly_budget == 0:
        advice.append(
            "Set a monthly budget to make your spending progress measurable."
        )
    elif budget_remaining < 0:
        advice.append(
            f"You are {_money(abs(budget_remaining))} over budget this month. "
            "Pause non-essential spending and review recent expenses."
        )
    elif budget_percentage >= 80:
        advice.append(
            f"You have used {budget_percentage}% of your monthly budget. "
            "Keep discretionary purchases tight for the rest of the month."
        )
    else:
        advice.append(
            f"You still have {_money(budget_remaining)} left in your monthly budget."
        )

    if monthly_savings > 0:
        advice.append(
            f"You are currently saving {_money(monthly_savings)} this month. "
            "Consider moving part of it to a separate savings or investment account."
        )
    elif monthly_income > 0:
        advice.append(
            "Your monthly expenses are matching or exceeding income. "
            "Look for one recurring cost to reduce before adding new spending."
        )

    if top_category:
        advice.append(
            f"Your largest expense category is {top_category['category']} "
            f"at {_money(top_category['total'])}. Review this area first for savings."
        )

    return advice[:5]


def build_prompt(summary: dict[str, object]) -> str:
    top_category = summary["top_expense_category"] or {}
    return (
        "You are a concise personal finance budgeting assistant. "
        "Give 4 practical, safe, non-investment-specific budgeting suggestions.\n"
        f"Total income: {_money(summary['total_income'])}\n"
        f"Total expenses: {_money(summary['total_expenses'])}\n"
        f"Balance: {_money(summary['balance'])}\n"
        f"Monthly income: {_money(summary['monthly_income'])}\n"
        f"Monthly expenses: {_money(summary['monthly_expenses'])}\n"
        f"Monthly savings: {_money(summary['monthly_savings'])}\n"
        f"Monthly budget: {_money(summary['monthly_budget'])}\n"
        f"Budget used: {summary['budget_percentage']}%\n"
        f"Top expense category: {top_category.get('category', 'None')}\n"
    )


def generate_budget_advice(summary: dict[str, object]) -> dict[str, object]:
    api_key = current_app.config.get("GEMINI_API_KEY")
    if not api_key:
        return {
            "provider": "Local Advisor",
            "advice": build_local_advice(summary),
            "used_gemini": False,
        }

    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=FutureWarning)
            import google.generativeai as genai
        from google.api_core.retry import Retry

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            current_app.config.get("GEMINI_MODEL", "gemini-3.5-flash")
        )
        response = model.generate_content(
            build_prompt(summary),
            request_options={
                "retry": Retry(initial=1, maximum=2, multiplier=1.5, deadline=6),
                "timeout": 6,
            },
        )
        text = (response.text or "").strip()
        advice = [
            line.lstrip("-•0123456789. ").strip()
            for line in text.splitlines()
            if line.strip()
        ]
        return {
            "provider": "Gemini",
            "advice": advice[:6] or build_local_advice(summary),
            "used_gemini": True,
        }
    except Exception as exc:
        current_app.logger.debug("Gemini budget advice unavailable: %s", exc)
        return {
            "provider": "Local Advisor",
            "advice": build_local_advice(summary),
            "used_gemini": False,
        }
