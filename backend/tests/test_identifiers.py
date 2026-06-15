import pytest

from backend.identifiers import (
    make_account_doc_ref_id,
    make_message_ref_id,
    make_reporting_fi_doc_ref_id,
)


def test_doc_ref_id_uses_country_year_tin_and_sequence(settings):
    configured = settings.model_copy(
        update={
            "reporting_fi_country": "DM",
            "tax_year": "2025",
            "reporting_fi_tin": "123-456-789",
        }
    )
    assert make_reporting_fi_doc_ref_id(configured) == "DM202512345678900000"
    assert make_account_doc_ref_id(configured, 1) == "DM202512345678900001"
    assert make_account_doc_ref_id(configured, 2) == "DM202512345678900002"


def test_doc_ref_sequence_range_is_enforced(settings):
    with pytest.raises(ValueError, match="start at 1"):
        make_account_doc_ref_id(settings, 0)
    with pytest.raises(ValueError, match="between 0 and 99999"):
        make_account_doc_ref_id(settings, 100000)


def test_configured_message_ref_id_is_preserved(settings):
    configured = settings.model_copy(
        update={"message_ref_id": "DM2025CUSTOMMESSAGE00001"}
    )
    assert make_message_ref_id(configured) == "DM2025CUSTOMMESSAGE00001"
