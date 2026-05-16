"""Small helpers for comparing dates from Google Sheets and Letterboxd."""
from datetime import date, datetime


def parse_date(text: str) -> date | None:
    """Turn a date string into a ``date``, or ``None`` if it is empty or invalid.

    Handles Movies sheet format (03/10/2025) and Letterboxd format (2025-03-10).
    """
    if not text or not str(text).strip():
        return None

    text = str(text).strip()
    formats = ("%m/%d/%Y", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S")

    for fmt in formats:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass

    return None


def is_in_cycle(watch_date_str: str, cycle_start: date | None, cycle_end: date) -> bool:
    """True if someone watched during this club film cycle.

    A watch counts when it is:
      - on or after ``cycle_start`` (when the last film was completed), and
      - on or before ``cycle_end`` (when this film was completed).

    For the club's first film, pass ``cycle_start=None`` (no earlier film to compare).
    """
    watch_date = parse_date(watch_date_str)
    if watch_date is None:
        return False

    if cycle_start is not None and watch_date < cycle_start:
        return False

    if watch_date > cycle_end:
        return False

    return True
