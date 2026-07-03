from decimal import Decimal, InvalidOperation


def format_currency(value, symbol: str = "₹") -> str:
    """Format a numeric value safely for display as currency."""
    try:
        amount = Decimal(str(value or 0))
    except (InvalidOperation, TypeError, ValueError):
        amount = Decimal("0.00")
    sign = "-" if amount < 0 else ""
    return f"{sign}{symbol}{abs(amount):,.2f}"
