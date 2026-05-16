from datetime import date

from infrastructure.dates import is_in_cycle, parse_date


def test_parse_date_sheet_format():
    assert parse_date("03/10/2025") == date(2025, 3, 10)


def test_parse_date_letterboxd_format():
    assert parse_date("2025-03-10") == date(2025, 3, 10)


def test_is_in_cycle_between_two_dates():
    cycle_start = date(2025, 3, 1)
    cycle_end = date(2025, 3, 15)
    assert is_in_cycle("2025-03-10", cycle_start, cycle_end)
    assert not is_in_cycle("2025-02-28", cycle_start, cycle_end)
    assert not is_in_cycle("2025-03-16", cycle_start, cycle_end)


def test_is_in_cycle_first_film_has_no_start_date():
    cycle_end = date(2025, 3, 15)
    assert is_in_cycle("2020-01-01", None, cycle_end)
