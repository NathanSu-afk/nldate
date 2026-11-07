from datetime import date

import pytest

from nldate import parse


def test_parse_absolute_date() -> None:
    ref = date(2025, 11, 1)
    assert parse("December 1st, 2025", today=ref) == date(2025, 12, 1)
    assert parse("2025-12-01", today=ref) == date(2025, 12, 1)


def test_parse_relative_days() -> None:
    ref = date(2025, 11, 1)
    assert parse("tomorrow", today=ref) == date(2025, 11, 2)
    assert parse("yesterday", today=ref) == date(2025, 10, 31)
    assert parse("in 3 days", today=ref) == date(2025, 11, 4)
    assert parse("5 days ago", today=ref) == date(2025, 10, 27)


def test_parse_offsets_before_after() -> None:
    ref = date(2025, 11, 1)
    assert parse("5 days before December 1st, 2025", today=ref) == date(2025, 11, 26)
    assert parse("1 week after December 1st, 2025", today=ref) == date(2025, 12, 8)


def test_parse_next_weekday() -> None:
    ref = date(2025, 11, 1)  # Saturday
    assert parse("next Tuesday", today=ref) == date(2025, 11, 4)


def test_parse_invalid_raises_value_error() -> None:
    with pytest.raises(ValueError):
        parse("")
    with pytest.raises(ValueError):
        parse("not a date at all 12345")
