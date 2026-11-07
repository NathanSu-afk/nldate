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


def parse(s: str, today: date | None = None) -> date:
    """Parse a natural language date string into a datetime.date object."""
    if not s or not s.strip():
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

    num_pattern = r"(?:\d+|" + "|".join(NUMBER_WORDS.keys()) + ")"

    # Match "in [amount] [unit]"
    match_in = re.match(
        r"^in\s+("
        + num_pattern
        + r")\s+(day|days|week|weeks|month|months|year|years)$",
        cleaned,
    )
    if match_in:
        amount = _parse_amount(match_in.group(1))
        unit = match_in.group(2)
        if "day" in unit:
            return today + timedelta(days=amount)
        elif "week" in unit:
            return today + timedelta(weeks=amount)
        elif "month" in unit:
            return today + relativedelta(months=amount)
        elif "year" in unit:
            return today + relativedelta(years=amount)

    # Match "[amount] [unit] ago"
    match_ago = re.match(
        r"^("
        + num_pattern
        + r")\s+(day|days|week|weeks|month|months|year|years)\s+ago$",
        cleaned,
    )
    if match_ago:
        amount = _parse_amount(match_ago.group(1))
        unit = match_ago.group(2)
        if "day" in unit:
            return today - timedelta(days=amount)
        elif "week" in unit:
            return today - timedelta(weeks=amount)
        elif "month" in unit:
            return today - relativedelta(months=amount)
        elif "year" in unit:
            return today - relativedelta(years=amount)

    # Match offset patterns like "[amount] [unit] before/after [base]"
    match_offset = re.match(
        r"^("
        + num_pattern
        + r")\s+(day|days|week|weeks|month|months|year|years)\s+(before|after)\s+(.+)$",
        cleaned,
    )
    if match_offset:
        amount = _parse_amount(match_offset.group(1))
        unit = match_offset.group(2)
        direction = match_offset.group(3)
        base_str = match_offset.group(4)

        try:
            base_date = parse(base_str, today=today)
        except ValueError as exc:
            raise ValueError(f"Could not parse base date: {base_str}") from exc

        delta = relativedelta()
        if "day" in unit:
            delta = relativedelta(days=amount)
        elif "week" in unit:
            delta = relativedelta(weeks=amount)
        elif "month" in unit:
            delta = relativedelta(months=amount)
        elif "year" in unit:
            delta = relativedelta(years=amount)

        return base_date - delta if direction == "before" else base_date + delta

    weekdays = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }
    match_next = re.match(r"^next\s+([a-z]+)$", cleaned)
    if match_next:
        day_name = match_next.group(1)
        if day_name in weekdays:
            target_wd = weekdays[day_name]
            current_wd = today.weekday()
            days_ahead = (target_wd - current_wd) % 7
            if days_ahead == 0:
                days_ahead = 7
            return today + timedelta(days=days_ahead)

    try:
        parsed_dt = du_parser.parse(s, fuzzy=True)
        return parsed_dt.date()
    except Exception as exc:
        raise ValueError(f"Could not recognize date string: {s}") from exc
