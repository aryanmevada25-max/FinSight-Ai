from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from utils.helpers import format_currency


def transactions_to_pdf(transactions: list[dict[str, object]], summary) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("FinSight AI - Report", styles["Title"]),
        Spacer(1, 12),
        Paragraph(
            (
                f"Income: {format_currency(summary['total_income'])} | "
                f"Expenses: {format_currency(summary['total_expenses'])} | "
                f"Balance: {format_currency(summary['balance'])}"
            ),
            styles["Normal"],
        ),
        Spacer(1, 16),
    ]

    rows = [["Date", "Type", "Category / Source", "Description", "Amount"]]
    for item in transactions:
        rows.append(
            [
                item["date"].strftime("%Y-%m-%d"),
                item["type"],
                item["category"],
                item.get("description") or "",
                format_currency(item["amount"]),
            ]
        )

    table = Table(rows, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#172554")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ]
        )
    )
    story.append(table)
    doc.build(story)
    return buffer.getvalue()
