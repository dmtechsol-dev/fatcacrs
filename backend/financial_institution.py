from __future__ import annotations

import os
import re


FINANCIAL_INSTITUTION_IN_ENV = "FINANCIAL_INSTITUTION_IN"
MAX_FINANCIAL_INSTITUTION_IN_LENGTH = 188


def normalize_financial_institution_in(
    value: str,
    *,
    source: str = "Financial institution IN",
) -> str:
    normalized = (value or "").strip().upper()
    if not normalized:
        raise ValueError(
            "Financial institution IN is required. Provide it in the uploaded "
            "workbook, app settings, or FINANCIAL_INSTITUTION_IN."
        )
    if not re.fullmatch(r"[A-Z0-9]+", normalized):
        raise ValueError(
            f"{source} must contain letters and digits only; spaces, slashes, "
            "hyphens, and other special characters are not allowed."
        )
    if len(normalized) > MAX_FINANCIAL_INSTITUTION_IN_LENGTH:
        raise ValueError(
            f"{source} exceeds the maximum supported length of "
            f"{MAX_FINANCIAL_INSTITUTION_IN_LENGTH} characters."
        )
    return normalized


def resolve_financial_institution_in(
    workbook_value: str | None,
    settings_value: str | None,
) -> str:
    candidates = (
        ("Uploaded workbook financial institution IN", workbook_value),
        ("Configured financial institution IN", settings_value),
        (
            "FINANCIAL_INSTITUTION_IN environment variable",
            os.getenv(FINANCIAL_INSTITUTION_IN_ENV),
        ),
    )
    for source, value in candidates:
        if value is not None and value.strip():
            return normalize_financial_institution_in(value, source=source)
    return normalize_financial_institution_in("")
