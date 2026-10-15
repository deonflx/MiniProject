import re
from decimal import Decimal, InvalidOperation

def parse_amount(value):
    """Parse various string representations of amounts (e.g. '50k', '1.5m', '50,000') into float."""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float, Decimal)):
        return float(value)
    normalized = str(value).strip().lower().replace(",", "")
    multiplier = 1
    if normalized.endswith("k"):
        multiplier, normalized = 1000, normalized[:-1]
    elif normalized.endswith("m"):
        multiplier, normalized = 1_000_000, normalized[:-1]
    normalized = re.sub(r"[^0-9.]", "", normalized)
    try:
        return float(Decimal(normalized) * multiplier)
    except (InvalidOperation, ValueError):
        return None
