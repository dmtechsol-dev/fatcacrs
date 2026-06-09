import hashlib
import re
from datetime import datetime, timezone

from backend.models import AccountRecord, ReportingSettings


def _clean(value: str, limit: int = 80) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "", value or "")
    return cleaned[:limit] or "NA"


def reporting_year(settings: ReportingSettings) -> str:
    return settings.reporting_period[:4]


def make_message_ref_id(settings: ReportingSettings) -> str:
    now = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    return (
        f"{settings.transmitting_country}{reporting_year(settings)}"
        f"{_clean(settings.sending_company_in)}{now}"
    )[:200]


def make_reporting_fi_doc_ref_id(settings: ReportingSettings) -> str:
    source = "|".join(
        [
            settings.reporting_fi_country,
            reporting_year(settings),
            settings.sending_company_in,
            settings.reporting_fi_tin,
            settings.reporting_fi_name,
        ]
    )
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()[:12]
    return (
        f"{settings.reporting_fi_country}{reporting_year(settings)}"
        f"{_clean(settings.sending_company_in)}-FI-{digest}"
    )[:200]


def make_account_doc_ref_id(
    record: AccountRecord, settings: ReportingSettings
) -> str:
    source = "|".join(
        [
            record.country,
            reporting_year(settings),
            settings.sending_company_in,
            record.account_number,
            str(record.row_number),
            record.first_name,
            record.surname,
        ]
    )
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()[:12]
    return (
        f"{_clean(record.country, 2)}{reporting_year(settings)}"
        f"{_clean(settings.sending_company_in)}-"
        f"{_clean(record.account_number)}-{record.row_number}-{digest}"
    )[:200]
