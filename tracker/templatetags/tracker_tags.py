from django import template
from decimal import Decimal

register = template.Library()

@register.filter(name='currency')
def currency_filter(value, symbol='₹'):
    """Formats numeric values into clean currency strings, e.g. ₹1,234.56"""
    if value is None or value == '':
        return f"{symbol}0.00"
    try:
        val = Decimal(str(value))
        return f"{symbol}{val:,.2f}"
    except Exception:
        return f"{symbol}{value}"

@register.filter(name='percentage')
def percentage_filter(value, total):
    """Calculates percentage of value from total."""
    try:
        v = Decimal(str(value))
        t = Decimal(str(total))
        if t <= 0:
            return 0
        return round((v / t) * 100, 1)
    except Exception:
        return 0

@register.filter(name='sub')
def sub_filter(value, arg):
    """Subtracts arg from value."""
    try:
        return Decimal(str(value)) - Decimal(str(arg))
    except Exception:
        return 0

@register.filter(name='abs_val')
def abs_val_filter(value):
    """Returns absolute value."""
    try:
        return abs(Decimal(str(value)))
    except Exception:
        return value

@register.filter(name='format_compact')
def format_compact(value, symbol='₹'):
    """Formats large numbers into K, M, etc."""
    try:
        val = float(value)
        if abs(val) >= 1_000_000:
            return f"{symbol}{val/1_000_000:.1f}M"
        if abs(val) >= 1_000:
            return f"{symbol}{val/1_000:.1f}k"
        return f"{symbol}{val:,.0f}"
    except Exception:
        return f"{symbol}{value}"
