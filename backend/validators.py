from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation

from backend.identifiers import make_account_doc_ref_id
from backend.models import AccountRecord, ReportingSettings, ValidationSummary


def parse_decimal(value: str) -> Decimal | None:
    raw = (value or "").strip().replace(",", "")
    if not raw:
        return None
    try:
        return Decimal(raw)
    except InvalidOperation:
        return None


def is_valid_date(value: str) -> bool:
    if not value:
        return True
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def validate_record(record: AccountRecord) -> AccountRecord:
    errors: list[str] = []
    warnings: list[str] = []
    country = record.country.strip()
    balance = parse_decimal(record.account_balance)
    payment = parse_decimal(record.payment)

    if record.status_error:
        errors.append(record.status_error)
    if not record.account_number:
        errors.append("Missing account number.")
    if not record.first_name:
        errors.append("Missing first name.")
    if not record.surname:
        errors.append("Missing surname.")
    if not country:
        errors.append("Missing country code.")
    elif country == "-":
        errors.append("Country code '-' is not valid.")
    elif len(country) != 2 or not country.isalpha() or country != country.upper():
        errors.append("Country code must be exactly two uppercase letters.")

    if not record.account_balance:
        errors.append("Missing account balance.")
    elif balance is None:
        errors.append("Account balance must be numeric.")

    if record.date_of_birth and not is_valid_date(record.date_of_birth):
        errors.append("Date of birth must be a valid date in YYYY-MM-DD format.")

    if country and country != "US" and record.tin.strip() in {"", "-"}:
        warnings.append("TIN is missing for a non-US CRS account.")
    if not record.date_of_birth:
        warnings.append("Date of birth is missing.")
    if balance == Decimal("0"):
        warnings.append("Account balance is zero.")
    if payment is None or payment == Decimal("0"):
        warnings.append("Payment is missing or zero.")
    if len(record.address.strip()) < 12:
        warnings.append("Address appears short or incomplete.")

    return record.model_copy(
        update={
            "country": country,
            "errors": errors,
            "warnings": warnings,
        }
    )


def validate_records(
    records: list[AccountRecord],
    settings: ReportingSettings | None = None,
) -> list[AccountRecord]:
    validated = [validate_record(record) for record in records]
    if settings is None:
        return validated

    refs: dict[str, list[int]] = defaultdict(list)
    try:
        for index, _record in enumerate(validated, start=1):
            refs[make_account_doc_ref_id(settings, index)].append(index - 1)
    except ValueError as exc:
        message = f"Cannot generate DocRefId: {exc}"
        return [
            record.model_copy(
                update={"errors": [*record.errors, message]}
            )
            for record in validated
        ]
    duplicate_indexes = {
        index
        for indexes in refs.values()
        if len(indexes) > 1
        for index in indexes
    }
    if not duplicate_indexes:
        return validated

    result: list[AccountRecord] = []
    for index, record in enumerate(validated):
        if index in duplicate_indexes:
            result.append(
                record.model_copy(
                    update={
                        "errors": [
                            *record.errors,
                            "Generated DocRefId is duplicated.",
                        ]
                    }
                )
            )
        else:
            result.append(record)
    return result


def build_summary(records: list[AccountRecord]) -> ValidationSummary:
    countries = Counter(record.country or "(missing)" for record in records)
    closed = [record.closed_account for record in records]
    return ValidationSummary(
        total_records=len(records),
        valid_records=sum(not record.errors for record in records),
        error_records=sum(bool(record.errors) for record in records),
        warning_records=sum(bool(record.warnings) for record in records),
        country_breakdown=dict(sorted(countries.items())),
        closed_accounts=sum(closed),
        open_accounts=sum(not value for value in closed),
        dormant_accounts=sum(
            record.dormant_account or record.account_status
            for record in records
        ),
        undocumented_accounts=sum(
            record.undocumented_account for record in records
        ),
        missing_tin=sum(record.tin.strip() in {"", "-"} for record in records),
        missing_dob=sum(not record.date_of_birth for record in records),
        missing_balance=sum(not record.account_balance for record in records),
    )
