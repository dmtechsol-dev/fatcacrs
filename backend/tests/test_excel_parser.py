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


def test_account_status_true_maps_only_to_dormant():
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
    assert record.dormant_account
    assert not record.closed_account
    assert not record.undocumented_account


def test_account_status_false_maps_to_active_only():
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
                "FALSE",
                0,
                1,
            ]
        ]
    )
    record = parse_excel_bytes(content)[0]
    assert not record.account_status
    assert not record.dormant_account
    assert not record.closed_account
    assert not record.undocumented_account


def test_missing_dormant_status_column_is_rejected():
    headers = [
        header
        for header in HEADERS
        if str(header).strip().lower() != "account status"
    ]
    row = [900, "A", "B", None, "A complete address", "GB", "TIN-1", 0, 1]
    with pytest.raises(ValueError, match="required dormant status column"):
        parse_excel_with_metadata(workbook_bytes([row], headers=headers))


@pytest.mark.parametrize("value", ["", None, "Maybe", "Dormant", "Closed"])
def test_blank_or_invalid_account_status_is_a_readable_record_error(value):
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
                value,
                0,
                1,
            ]
        ]
    )
    record = parse_excel_bytes(content)[0]
    assert "Invalid dormant Account Status value" in record.status_error


def test_dedicated_closed_and_undocumented_columns_do_not_change_dormant():
    headers = [*HEADERS, "Account Closed", "Undocumented Account"]
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
                "FALSE",
                0,
                1,
                "Yes",
                "1",
            ]
        ],
        headers=headers,
    )
    record = parse_excel_bytes(content)[0]
    assert not record.dormant_account
    assert record.closed_account
    assert record.undocumented_account


def test_conflicting_dormant_columns_are_rejected():
    headers = [*HEADERS, "IsDormant"]
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
                "FALSE",
            ]
        ],
        headers=headers,
    )
    record = parse_excel_bytes(content)[0]
    assert "dedicated dormant column conflict" in record.status_error


def test_missing_required_excel_field_is_reported():
    headers = [
        header
        for header in HEADERS
        if str(header).strip().lower() != "surname"
    ]
    with pytest.raises(ValueError, match="surname"):
        parse_excel_bytes(workbook_bytes([], headers=headers))


def test_financial_institution_in_is_read_from_workbook_column():
    headers = [*HEADERS, "Financial Institution IN"]
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
                "FALSE",
                0,
                1,
                "fiin",
            ]
        ],
        headers=headers,
    )
    result = parse_excel_with_metadata(content)
    assert result.financial_institution_in == "FIIN"


def test_conflicting_workbook_financial_institution_ins_are_rejected():
    headers = [*HEADERS, "FI IN"]
    rows = [
        [
            900,
            "A",
            "B",
            None,
            "A complete address",
            "GB",
            "TIN-1",
            "FALSE",
            0,
            1,
            "FIIN1",
        ],
        [
            901,
            "C",
            "D",
            None,
            "Another complete address",
            "GB",
            "TIN-2",
            "TRUE",
            0,
            2,
            "FIIN2",
        ],
    ]
    with pytest.raises(ValueError, match="multiple financial institution IN"):
        parse_excel_with_metadata(workbook_bytes(rows, headers=headers))


def test_invalid_workbook_financial_institution_in_is_rejected():
    headers = [*HEADERS, "FIIN"]
    row = [
        900,
        "A",
        "B",
        None,
        "A complete address",
        "GB",
        "TIN-1",
        "FALSE",
        0,
        1,
        "FI-IN",
    ]
    with pytest.raises(ValueError, match="letters and digits only"):
        parse_excel_with_metadata(workbook_bytes([row], headers=headers))
