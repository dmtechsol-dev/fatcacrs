import pytest
from datetime import datetime

from backend.excel_parser import parse_excel_bytes, parse_excel_with_metadata
from backend.tests.conftest import HEADERS, workbook_bytes


def test_excel_parsing_and_date_conversion():
    content = workbook_bytes(
        [
            [
                900,
                " SEBASTIEN ",
                "SABIN",
                datetime(1968, 7, 9),
                "THE VALLEY, ANGUILLA",
                "gb",
                None,
                False,
                0,
                66.97,
            ]
        ]
    )
    records = parse_excel_bytes(content)
    assert len(records) == 1
    assert records[0].account_number == "900"
    assert records[0].first_name == "SEBASTIEN"
    assert records[0].country == "GB"
    assert records[0].date_of_birth == "1968-07-09"
    assert records[0].account_balance == "66.97"


def test_summary_row_is_ignored():
    content = workbook_bytes(
        [
            [900, "A", "B", None, "An address", "GB", None, False, 0, 1],
            [1, None, None, None, None, "True: 1", None, "False: 1", None, 1],
        ]
    )
    records = parse_excel_bytes(content)
    assert [record.account_number for record in records] == ["900"]


def test_explicit_status_columns_are_detected_and_normalized():
    headers = [
        *HEADERS,
        "IsDormant",
        "Closed",
        "IsUndocumented",
    ]
    content = workbook_bytes(
        [
            [
                900,
                "A",
                "B",
                None,
                "A complete address",
                "GB",
                "TIN-1",
                "Open",
                0,
                1,
                "Y",
                "FALSE",
                1,
            ]
        ],
        headers=headers,
    )
    result = parse_excel_with_metadata(content)
    record = result.records[0]
    assert record.dormant_account
    assert not record.closed_account
    assert record.undocumented_account
    assert result.status_mapping.dormant_account == "IsDormant"
    assert result.status_mapping.closed_account == "Closed"
    assert result.status_mapping.undocumented_account == "IsUndocumented"


def test_account_status_names_map_to_xsd_flags():
    content = workbook_bytes(
        [
            [
                900,
                "A",
                "B",
                None,
                "A complete address",
                "GB",
                "TIN-1",
                "Dormant Undocumented",
                0,
                1,
            ]
        ]
    )
    record = parse_excel_bytes(content)[0]
    assert record.dormant_account
    assert record.undocumented_account
    assert not record.closed_account


def test_true_account_status_maps_to_closed_account():
    content = workbook_bytes(
        [
            [
                900,
                "A",
                "B",
                None,
                "A complete address",
                "GB",
                "TIN-1",
                "TRUE",
                0,
                1,
            ]
        ]
    )
    record = parse_excel_bytes(content)[0]
    assert record.account_status
    assert record.closed_account


def test_missing_status_columns_default_false_with_warning():
    headers = [
        header
        for header in HEADERS
        if str(header).strip().lower() != "account status"
    ]
    row = [900, "A", "B", None, "A complete address", "GB", "TIN-1", 0, 1]
    result = parse_excel_with_metadata(workbook_bytes([row], headers=headers))
    record = result.records[0]
    assert not record.dormant_account
    assert not record.closed_account
    assert not record.undocumented_account
    assert any("default to false" in item for item in result.status_mapping.warnings)


def test_invalid_status_value_becomes_readable_record_error():
    content = workbook_bytes(
        [
            [
                900,
                "A",
                "B",
                None,
                "A complete address",
                "GB",
                "TIN-1",
                "Maybe",
                0,
                1,
            ]
        ]
    )
    record = parse_excel_bytes(content)[0]
    assert "Unsupported account status value 'Maybe'" in record.status_error


def test_missing_required_excel_field_is_reported():
    headers = [
        header
        for header in HEADERS
        if str(header).strip().lower() != "surname"
    ]
    with pytest.raises(ValueError, match="surname"):
        parse_excel_bytes(workbook_bytes([], headers=headers))
