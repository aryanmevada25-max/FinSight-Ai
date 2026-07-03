from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required

from services.analytics import financial_summary
from services.gemini_service import generate_budget_advice
from utils.helpers import format_currency


ai = Blueprint("ai", __name__, url_prefix="/ai")


@ai.route("/advisor")
@login_required
def index():
    return redirect(url_for("ui.app", path="advisor"))


def legacy_index():
    summary = financial_summary(current_user)
    advisor = generate_budget_advice(summary)
    return render_template(
        "ai_advisor.html",
        advisor=advisor,
        summary=summary,
        format_currency=format_currency,
    )
