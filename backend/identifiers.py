import re
from datetime import datetime, timezone

from backend.models import ReportingSettings


DOC_REF_SEQUENCE_WIDTH = 6
MAX_DOC_REF_SEQUENCE = (10**DOC_REF_SEQUENCE_WIDTH) - 1


def _clean(value: str, limit: int = 80) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "", value or "")
    return cleaned[:limit] or "NA"


def reporting_year(settings: ReportingSettings) -> str:
    return settings.tax_year


def make_message_ref_id(settings: ReportingSettings) -> str:
    if settings.message_ref_id:
        return settings.message_ref_id.strip()
    now = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    return (
        f"{settings.transmitting_country}{reporting_year(settings)}"
        f"{_clean(settings.sending_company_in)}{now}"
    )[:200]


def _doc_ref_prefix(settings: ReportingSettings) -> str:
    country = re.sub(r"[^A-Za-z0-9]", "", settings.reporting_fi_country).upper()
    financial_institution_in = settings.financial_institution_in
    if len(country) != 2:
        raise ValueError("Reporting country must contain exactly two letters.")
    if not financial_institution_in:
        raise ValueError("Financial institution IN has not been resolved.")
    return (
        f"{country}{reporting_year(settings)}{financial_institution_in}"
    )


def make_doc_ref_id(settings: ReportingSettings, sequence: int) -> str:
    if sequence < 0 or sequence > MAX_DOC_REF_SEQUENCE:
        raise ValueError(
            f"DocRefId sequence must be between 0 and {MAX_DOC_REF_SEQUENCE}."
        )
    doc_ref_id = (
        f"{_doc_ref_prefix(settings)}"
        f"{sequence:0{DOC_REF_SEQUENCE_WIDTH}d}"
    )
    if len(doc_ref_id) > 200:
        raise ValueError("Generated DocRefId exceeds 200 characters.")
    return doc_ref_id


def make_reporting_fi_doc_ref_id(settings: ReportingSettings) -> str:
    return make_doc_ref_id(settings, 0)


def make_account_doc_ref_id(
    settings: ReportingSettings, sequence: int
) -> str:
    if sequence < 1:
        raise ValueError("Account DocRefId sequence must start at 1.")
    return make_doc_ref_id(settings, sequence)
