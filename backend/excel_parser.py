from __future__ import annotations

from datetime import date, datetime
from io import BytesIO
from typing import Any

from openpyxl import load_workbook
from openpyxl.utils.datetime import from_excel

from backend.config import EXPECTED_COLUMNS, EXPECTED_SHEET
from backend.models import AccountRecord


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def normalize_header(value: Any) -> str:
    return " ".join(_text(value).lower().split())


def normalize_date(value: Any, workbook_epoch=None) -> str:
    if value in (None, ""):
        return ""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, (int, float)) and workbook_epoch is not None:
        try:
            return from_excel(value, workbook_epoch).date().isoformat()
        except (TypeError, ValueError, OverflowError):
            return _text(value)
    raw = _text(value)
    for fmt in (
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d-%m-%Y",
        "%d.%m.%Y",
    ):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    return raw


def normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return _text(value).lower() in {"true", "yes", "y", "1", "closed"}


def is_summary_row(values: dict[str, Any]) -> bool:
    if _text(values.get("first_name")) or _text(values.get("surname")):
        return False
    combined = " ".join(_text(value) for value in values.values()).lower()
    return "true:" in combined or "false:" in combined


def parse_excel_bytes(content: bytes) -> list[AccountRecord]:
    workbook = load_workbook(BytesIO(content), read_only=True, data_only=True)
    if EXPECTED_SHEET not in workbook.sheetnames:
        raise ValueError(
            f"Workbook must contain a sheet named '{EXPECTED_SHEET}'."
        )

    sheet = workbook[EXPECTED_SHEET]
    header_values = next(sheet.iter_rows(min_row=1, max_row=1, values_only=True))
    mapped_headers: dict[int, str] = {}
    for index, header in enumerate(header_values):
        normalized = normalize_header(header)
        if normalized in EXPECTED_COLUMNS:
            mapped_headers[index] = EXPECTED_COLUMNS[normalized]

    missing = sorted(set(EXPECTED_COLUMNS.values()) - set(mapped_headers.values()))
    if missing:
        raise ValueError(
            "Workbook is missing required columns: " + ", ".join(missing)
        )

    records: list[AccountRecord] = []
    for row_number, row in enumerate(
        sheet.iter_rows(min_row=2, values_only=True), start=2
    ):
        values = {
            field: row[index] if index < len(row) else None
            for index, field in mapped_headers.items()
        }
        if is_summary_row(values):
            continue
        if not any(value not in (None, "") for value in values.values()):
            continue
        records.append(
            AccountRecord(
                row_number=row_number,
                account_number=_text(values["account_number"]),
                first_name=_text(values["first_name"]),
                surname=_text(values["surname"]),
                date_of_birth=normalize_date(
                    values["date_of_birth"], workbook.epoch
                ),
                address=_text(values["address"]),
                country=_text(values["country"]).upper(),
                tin=_text(values["tin"]),
                account_status=normalize_bool(values["account_status"]),
                payment=_text(values["payment"]),
                account_balance=_text(values["account_balance"]),
            )
        )
    return records
