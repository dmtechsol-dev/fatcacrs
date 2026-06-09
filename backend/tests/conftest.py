from io import BytesIO

import pytest
from openpyxl import Workbook

from backend.models import ReportingSettings


HEADERS = [
    "Account # ",
    "Name                         ",
    "Surname",
    "Date of Birth",
    "Address               ",
    "Country",
    "TIN #",
    "Account Status",
    "Interest & Dividend Paid",
    "Account Balance 31st/12/2025",
]


@pytest.fixture
def settings():
    return ReportingSettings(
        sending_company_in="DEMO123",
        reporting_fi_tin="DM-TIN-001",
        reporting_fi_tin_issued_by="DM",
        reporting_fi_name="Example Reporting Financial Institution",
        reporting_fi_address="1 Independence Street",
        reporting_fi_city="Roseau",
        reporting_fi_country="DM",
        transmitting_country="DM",
        receiving_country="DM",
        reporting_period="2025-12-31",
        currency="USD",
    )


def workbook_bytes(rows):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Accounts to report - IRD"
    sheet.append(HEADERS)
    for row in rows:
        sheet.append(row)
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()
