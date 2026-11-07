import re
from datetime import date, timedelta

from dateutil import parser as du_parser
from dateutil.relativedelta import relativedelta

NUMBER_WORDS = {
    "a": 1,
    "an": 1,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
}


def _parse_amount(s: str) -> int:
    s = s.lower()
    if s in NUMBER_WORDS:
        return NUMBER_WORDS[s]
    return int(s)


def _apply_delta(base: date, amount: int, unit: str, forward: bool) -> date:
    sign = 1 if forward else -1
    if "day" in unit:
        return base + timedelta(days=amount * sign)
    elif "week" in unit:
        return base + timedelta(weeks=amount * sign)
    elif "month" in unit:
        return base + relativedelta(months=amount * sign)
    elif "year" in unit:
        return base + relativedelta(years=amount * sign)
    raise ValueError(f"Unknown unit: {unit}")


def parse(s: str, today: date | None = None) -> date:
    """Parse a natural language date string into a datetime.date object."""
    if not s or not isinstance(s, str) or not s.strip():
        raise ValueError("Empty or whitespace string provided.")

    if today is None:
        today = date.today()

    cleaned = s.strip().lower()

    if cleaned == "today":
        return today
    if cleaned == "tomorrow":
        return today + timedelta(days=1)
    if cleaned == "yesterday":
        return today - timedelta(days=1)
    if cleaned == "last week":
        return today - timedelta(weeks=1)
    if cleaned == "last month":
        return today - relativedelta(months=1)
    if cleaned == "last year":
        return today - relativedelta(years=1)

    num_pattern = r"(?:\d+|" + "|".join(NUMBER_WORDS.keys()) + ")"

    # 1. Match "in [amount] [unit]"
    m = re.match(
        r"^in\s+("
        + num_pattern
        + r")\s+(day|days|week|weeks|month|months|year|years)$",
        cleaned,
    )
    if m:
        return _apply_delta(today, _parse_amount(m.group(1)), m.group(2), forward=True)

    # 2. Match "[amount] [unit] from now" or "[amount] [unit] from today"
    m = re.match(
        r"^("
        + num_pattern
        + r")\s+(day|days|week|weeks|month|months|year|years)\s+from\s+(?:now|today)$",
        cleaned,
    )
    if m:
        return _apply_delta(today, _parse_amount(m.group(1)), m.group(2), forward=True)

    # 3. Match "[amount] [unit] ago"
    m = re.match(
        r"^("
        + num_pattern
        + r")\s+(day|days|week|weeks|month|months|year|years)\s+ago$",
        cleaned,
    )
    if m:
        return _apply_delta(today, _parse_amount(m.group(1)), m.group(2), forward=False)

    # 4. Match offset: "[amount] [unit] before/after [base]"
    m = re.match(
        r"^("
        + num_pattern
        + r")\s+(day|days|week|weeks|month|months|year|years)\s+(before|after)\s+(.+)$",
        cleaned,
    )
    if m:
        amount = _parse_amount(m.group(1))
        unit = m.group(2)
        direction = m.group(3)
        base_str = m.group(4)

        try:
            base_date = parse(base_str, today=today)
        except ValueError as exc:
            raise ValueError(f"Could not parse base date: {base_str}") from exc

        return _apply_delta(base_date, amount, unit, forward=(direction == "after"))

    weekdays = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }

    # 5. Match "next [weekday]"
    m = re.match(r"^next\s+([a-z]+)$", cleaned)
    if m:
        day_name = m.group(1)
        if day_name in weekdays:
            target_wd = weekdays[day_name]
            current_wd = today.weekday()
            days_ahead = (target_wd - current_wd) % 7
            if days_ahead == 0:
                days_ahead = 7
            return today + timedelta(days=days_ahead)

    # 6. Match "last [weekday]"
    m = re.match(r"^last\s+([a-z]+)$", cleaned)
    if m:
        day_name = m.group(1)
        if day_name in weekdays:
            target_wd = weekdays[day_name]
            current_wd = today.weekday()
            days_ago = (current_wd - target_wd) % 7
            if days_ago == 0:
                days_ago = 7
            return today - timedelta(days=days_ago)

    # 7. Fallback to dateutil parser for absolute/fuzzy dates
    try:
        parsed_dt = du_parser.parse(s, fuzzy=True)
        return parsed_dt.date()
    except Exception as exc:
        raise ValueError(f"Could not recognize date string: {s}") from exc
