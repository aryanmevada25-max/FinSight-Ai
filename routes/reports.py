from datetime import date

from flask import Blueprint, Response, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from services.analytics import expense_total, financial_summary, income_total
from services.analytics import transactions_in_range
from services.csv_service import transactions_to_csv
from services.pdf_service import transactions_to_pdf
from utils.helpers import format_currency


reports = Blueprint("reports", __name__, url_prefix="/reports")


def parse_report_date(value: str, label: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        flash(f"The {label} date is invalid.", "warning")
        return None


def report_context():
    start_value = request.args.get("start_date", "").strip()
    end_value = request.args.get("end_date", "").strip()
    start = parse_report_date(start_value, "start")
    end = parse_report_date(end_value, "end")

    if start and end and start > end:
        flash("The start date must be before the end date.", "warning")
        start = end = None

    transactions = transactions_in_range(current_user.id, start, end)
    summary = financial_summary(current_user)
    range_income = income_total(current_user.id, start, end)
    range_expenses = expense_total(current_user.id, start, end)

    return {
        "filters": {"start_date": start_value, "end_date": end_value},
        "transactions": transactions,
        "summary": summary,
        "range_income": range_income,
        "range_expenses": range_expenses,
        "range_balance": range_income - range_expenses,
    }


@reports.route("/")
@login_required
def index():
    return redirect(url_for("ui.app", path="reports"))


def legacy_index():
    context = report_context()
    return render_template(
        "reports.html",
        format_currency=format_currency,
        **context,
    )


@reports.route("/export.csv")
@login_required
def export_csv():
    context = report_context()
    csv_text = transactions_to_csv(context["transactions"])
    return Response(
        csv_text,
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=finance-report.csv"
        },
    )


@reports.route("/export.pdf")
@login_required
def export_pdf():
    context = report_context()
    pdf_bytes = transactions_to_pdf(
        context["transactions"], context["summary"]
    )
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=finance-report.pdf"
        },
    )
