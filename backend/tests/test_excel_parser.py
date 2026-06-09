from datetime import datetime

from backend.excel_parser import parse_excel_bytes
from backend.tests.conftest import workbook_bytes


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
