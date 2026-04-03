from infrastructure.sheets_client import get_worksheet
from infrastructure.cache import cache


def _get_selected_rows() -> list[dict]:
    cached = cache.get("selected_rows")
    if cached is not None:
        return cached

    rows = get_worksheet("Selected").get_all_records()
    cache.set("selected_rows", rows)
    return rows


def get_selected_slugs() -> list[str]:
    return [row["SLUG"] for row in _get_selected_rows() if row.get("SLUG")]


def get_rotw_winners() -> list[str]:
    winners = []
    for row in _get_selected_rows():
        rotw = row.get("ROTW", "")
        if rotw:
            for name in rotw.split(","):
                name = name.strip()
                if name:
                    winners.append(name)
    return winners
