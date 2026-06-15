from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from io import BytesIO
from typing import Any

from openpyxl import load_workbook
from openpyxl.utils.datetime import from_excel

from backend.config import (
    EXPECTED_COLUMNS,
    EXPECTED_SHEET,
    REQUIRED_ACCOUNT_FIELDS,
)
from backend.models import AccountRecord, StatusMappingInfo


TRUE_VALUES = {"true", "yes", "y", "1"}
FALSE_VALUES = {"", "false", "no", "n", "0", "open", "active"}
STATUS_LABELS = {"dormant", "closed", "undocumented"}


@dataclass(frozen=True)
class WorkbookParseResult:
    records: list[AccountRecord]
    status_mapping: StatusMappingInfo


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


def map_header(value: Any) -> str | None:
    normalized = normalize_header(value)
    if normalized.startswith("account balance"):
        return "account_balance"
    return EXPECTED_COLUMNS.get(normalized)


def normalize_status_indicator(value: Any, label: str) -> tuple[bool, str]:
    raw = _text(value).lower()
    if raw in TRUE_VALUES or raw == label:
        return True, ""
    if raw in FALSE_VALUES:
        return False, ""
    return False, (
        f"Unsupported {label} status value '{_text(value)}'. "
        "Use Yes/No, Y/N, TRUE/FALSE, 1/0, or the status name."
    )


def normalize_account_status(
    value: Any,
) -> tuple[bool, bool, bool, bool, str]:
    raw = _text(value).lower()
    if raw in TRUE_VALUES:
        return True, False, True, False, ""
    if raw in FALSE_VALUES:
        return False, False, False, False, ""

    tokens = {
        token
        for token in re.split(r"[\s,;/|]+", raw)
        if token
    }
    if tokens and tokens <= STATUS_LABELS:
        return (
            "closed" in tokens,
            "dormant" in tokens,
            "closed" in tokens,
            "undocumented" in tokens,
            "",
        )
    return False, False, False, False, (
        f"Unsupported account status value '{_text(value)}'. "
        "Use Open, Dormant, Closed, Undocumented, Yes/No, "
        "Y/N, TRUE/FALSE, or 1/0."
    )


def status_mapping_info(
    mapped_headers: dict[int, str],
    header_values: tuple[Any, ...],
) -> StatusMappingInfo:
    detected = {
        field: _text(header_values[index])
        for index, field in mapped_headers.items()
        if field
        in {
            "account_status",
            "dormant_account",
            "closed_account",
            "undocumented_account",
        }
    }
    warnings: list[str] = []
    if not detected:
        warnings.append(
            "No account status columns were detected. DormantAccount, "
            "ClosedAccount, and UndocumentedAccount default to false."
        )
    else:
        for field, label in (
            ("dormant_account", "DormantAccount"),
            ("closed_account", "ClosedAccount"),
            ("undocumented_account", "UndocumentedAccount"),
        ):
            if field not in detected:
                warnings.append(
                    f"No dedicated {label} column was detected. It defaults "
                    "to false unless the Account Status column indicates it."
                )
    return StatusMappingInfo(
        account_status=detected.get("account_status"),
        dormant_account=detected.get("dormant_account"),
        closed_account=detected.get("closed_account"),
        undocumented_account=detected.get("undocumented_account"),
        warnings=warnings,
    )


def is_summary_row(values: dict[str, Any]) -> bool:
    if _text(values.get("first_name")) or _text(values.get("surname")):
        return False
    combined = " ".join(_text(value) for value in values.values()).lower()
    return "true:" in combined or "false:" in combined


def parse_excel_with_metadata(content: bytes) -> WorkbookParseResult:
    workbook = load_workbook(BytesIO(content), read_only=True, data_only=True)
    if EXPECTED_SHEET not in workbook.sheetnames:
        raise ValueError(
            f"Workbook must contain a sheet named '{EXPECTED_SHEET}'."
        )

    sheet = workbook[EXPECTED_SHEET]
    header_values = next(sheet.iter_rows(min_row=1, max_row=1, values_only=True))
    mapped_headers: dict[int, str] = {}
    for index, header in enumerate(header_values):
        mapped = map_header(header)
        if mapped:
            mapped_headers[index] = mapped

    missing = sorted(REQUIRED_ACCOUNT_FIELDS - set(mapped_headers.values()))
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
        status_errors: list[str] = []
        (
            account_status,
            status_dormant,
            status_closed,
            status_undocumented,
            account_status_error,
        ) = normalize_account_status(values.get("account_status"))
        if account_status_error:
            status_errors.append(account_status_error)

        explicit_statuses: dict[str, bool] = {}
        for field, label in (
            ("dormant_account", "dormant"),
            ("closed_account", "closed"),
            ("undocumented_account", "undocumented"),
        ):
            if field not in values:
                continue
            normalized, status_error = normalize_status_indicator(
                values.get(field), label
            )
            explicit_statuses[field] = normalized
            if status_error:
                status_errors.append(status_error)

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
                account_status=account_status,
                dormant_account=(
                    status_dormant
                    or explicit_statuses.get("dormant_account", False)
                ),
                closed_account=(
                    status_closed
                    or explicit_statuses.get("closed_account", False)
                ),
                undocumented_account=(
                    status_undocumented
                    or explicit_statuses.get("undocumented_account", False)
                ),
                status_error=" ".join(status_errors),
                payment=_text(values["payment"]),
                account_balance=_text(values["account_balance"]),
            )
        )
    return WorkbookParseResult(
        records=records,
        status_mapping=status_mapping_info(mapped_headers, header_values),
    )


def parse_excel_bytes(content: bytes) -> list[AccountRecord]:
    return parse_excel_with_metadata(content).records
