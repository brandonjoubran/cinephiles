"""Write sheet rows by header name so column order on the tab does not matter."""


def serialize_field_value(value) -> str:
    if isinstance(value, list):
        return ", ".join(str(v).strip() for v in value if str(v).strip())
    if value is None:
        return ""
    if hasattr(value, "value"):
        return value.value
    return str(value)


def append_row_by_headers(sheet, fields: dict[str, object]):
    """Append one row; `fields` keys are lowercase (e.g. slug, voted_by)."""
    headers = sheet.row_values(1)
    row = []
    for header in headers:
        if not str(header).strip():
            row.append("")
            continue
        key = str(header).strip().lower()
        row.append(serialize_field_value(fields.get(key, "")))
    sheet.append_row(row)
