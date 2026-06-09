from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
SCHEMA_DIR = BASE_DIR / "schemas"
ROOT_SCHEMA = SCHEMA_DIR / "FatcaCrs_v2.2.xsd"
GENERATED_DIR = BASE_DIR / "data" / "generated"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)

EXPECTED_SHEET = "Accounts to report - IRD"
EXPECTED_COLUMNS = {
    "account #": "account_number",
    "name": "first_name",
    "surname": "surname",
    "date of birth": "date_of_birth",
    "address": "address",
    "country": "country",
    "tin #": "tin",
    "account status": "account_status",
    "interest & dividend paid": "payment",
    "account balance 31st/12/2025": "account_balance",
}

NS_OECD_FTC = "urn:fatcacrs:ties:v2"
NS_SFA_FTC = "urn:oecd:ties:fatcacrstypes:v2"
NS_SFA = "urn:oecd:ties:stffatcatypes:v2"
NS_XSI = "http://www.w3.org/2001/XMLSchema-instance"
