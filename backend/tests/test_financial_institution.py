import pytest
from pydantic import ValidationError

from backend.financial_institution import (
    normalize_financial_institution_in,
    resolve_financial_institution_in,
)
from backend.models import ReportingSettings


def test_financial_institution_in_is_normalized_to_uppercase():
    assert normalize_financial_institution_in(" fiin123 ") == "FIIN123"


@pytest.mark.parametrize("value", ["FI-IN", "FI IN", "FI/IN", "FI_IN"])
def test_invalid_financial_institution_in_is_rejected(value):
    with pytest.raises(ValueError, match="letters and digits only"):
        normalize_financial_institution_in(value)


def test_invalid_app_setting_is_rejected(settings):
    payload = settings.model_dump()
    payload["financial_institution_in"] = "FI-IN"
    with pytest.raises(ValidationError, match="letters and digits only"):
        ReportingSettings.model_validate(payload)


def test_resolver_uses_workbook_then_settings_then_environment(monkeypatch):
    monkeypatch.setenv("FINANCIAL_INSTITUTION_IN", "ENVIN")
    assert (
        resolve_financial_institution_in("WORKBOOKIN", "APPIN")
        == "WORKBOOKIN"
    )
    assert resolve_financial_institution_in(None, "APPIN") == "APPIN"
    assert resolve_financial_institution_in(None, "") == "ENVIN"


def test_resolver_rejects_missing_financial_institution_in(monkeypatch):
    monkeypatch.delenv("FINANCIAL_INSTITUTION_IN", raising=False)
    with pytest.raises(ValueError, match="is required"):
        resolve_financial_institution_in(None, "")
