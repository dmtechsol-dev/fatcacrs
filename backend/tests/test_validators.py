from backend.models import AccountRecord
from backend.validators import validate_record


def record(**changes):
    values = {
        "row_number": 2,
        "account_number": "900",
        "first_name": "A",
        "surname": "B",
        "date_of_birth": "1980-01-01",
        "address": "A complete address",
        "country": "GB",
        "tin": "TIN-1",
        "account_status": False,
        "payment": "10",
        "account_balance": "100",
    }
    values.update(changes)
    return AccountRecord(**values)


def test_missing_country_detected():
    result = validate_record(record(country=""))
    assert "Missing country code." in result.errors


def test_dash_country_detected():
    result = validate_record(record(country="-"))
    assert "Country code '-' is not valid." in result.errors


def test_missing_balance_detected():
    result = validate_record(record(account_balance=""))
    assert "Missing account balance." in result.errors


def test_invalid_date_detected():
    result = validate_record(record(date_of_birth="31/31/2025"))
    assert any("YYYY-MM-DD" in error for error in result.errors)
