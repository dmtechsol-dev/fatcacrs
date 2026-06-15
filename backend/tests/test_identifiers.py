import pytest

from backend.identifiers import (
    make_account_doc_ref_id,
    make_message_ref_id,
    make_reporting_fi_doc_ref_id,
)


def test_doc_ref_id_uses_country_year_fi_in_and_sequence(settings):
    configured = settings.model_copy(
        update={
            "reporting_fi_country": "DM",
            "tax_year": "2025",
            "financial_institution_in": "FIIN",
        }
    )
    assert make_reporting_fi_doc_ref_id(configured) == "DM2025FIIN000000"
    assert make_account_doc_ref_id(configured, 1) == "DM2025FIIN000001"
    assert make_account_doc_ref_id(configured, 2) == "DM2025FIIN000002"


def test_doc_ref_sequence_range_is_enforced(settings):
    with pytest.raises(ValueError, match="start at 1"):
        make_account_doc_ref_id(settings, 0)
    with pytest.raises(ValueError, match="between 0 and 999999"):
        make_account_doc_ref_id(settings, 1000000)


def test_missing_fi_in_blocks_doc_ref_generation(settings):
    configured = settings.model_copy(
        update={"financial_institution_in": ""}
    )
    with pytest.raises(ValueError, match="has not been resolved"):
        make_account_doc_ref_id(configured, 1)


def test_configured_message_ref_id_is_preserved(settings):
    configured = settings.model_copy(
        update={"message_ref_id": "DM2025CUSTOMMESSAGE00001"}
    )
    assert make_message_ref_id(configured) == "DM2025CUSTOMMESSAGE00001"
