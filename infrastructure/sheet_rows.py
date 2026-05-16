"""Write sheet rows by header name so column order on the tab does not matter."""


def serialize_field_value(value) -> str:
    if isinstance(value, list):
        return ", ".join(str(v).strip() for v in value if str(v).strip())
    if value is None:
        return ""
    if hasattr(value, "value"):
        return value.value
    return str(value)


def row_values_by_headers(headers: list[str], fields: dict[str, object]) -> list[str]:
    row = []
    for header in headers:
        if not str(header).strip():
            row.append("")
            continue
        key = str(header).strip().lower()
        row.append(serialize_field_value(fields.get(key, "")))
    return row


def append_row_by_headers(sheet, fields: dict[str, object]):
    """Append one row; `fields` keys are lowercase (e.g. slug, voted_by)."""
    headers = sheet.row_values(1)
    sheet.append_row(row_values_by_headers(headers, fields))


def update_row_by_headers(sheet, row_index: int, fields: dict[str, object]):
    """Update an existing row; `fields` keys are lowercase."""
    headers = sheet.row_values(1)
    row = row_values_by_headers(headers, fields)
    sheet.update(f"A{row_index}:{_col_letter(len(headers))}{row_index}", [row])


def _col_letter(n: int) -> str:
    """1-based column index to Excel-style column letter."""
    result = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        result = chr(65 + remainder) + result
    return result
