import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
SCHEMA_DIR = BASE_DIR / "schemas"
ROOT_SCHEMA = SCHEMA_DIR / "FatcaCrs_v2.2.xsd"
GENERATED_DIR = BASE_DIR / "data" / "generated"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)
FRONTEND_DIST_DIR = Path(
    os.getenv("FRONTEND_DIST_DIR", PROJECT_DIR / "frontend" / "dist")
).resolve()
FRONTEND_INDEX = FRONTEND_DIST_DIR / "index.html"
FRONTEND_ASSETS_DIR = FRONTEND_DIST_DIR / "assets"
REQUIRE_FRONTEND = os.getenv("REQUIRE_FRONTEND", "").lower() in {
    "1",
    "true",
    "yes",
}

EXPECTED_SHEET = "Accounts to report - IRD"
FINANCIAL_INSTITUTION_IN_COLUMNS = {
    "financial institution in",
    "financial institution's in",
    "financial institution identification number",
    "financialinstitutionin",
    "fi in",
    "fiin",
    "institution in",
    "reporting fi in",
}
EXPECTED_COLUMNS = {
    "account #": "account_number",
    "account number": "account_number",
    "name": "first_name",
    "first name": "first_name",
    "surname": "surname",
    "last name": "surname",
    "date of birth": "date_of_birth",
    "address": "address",
    "country": "country",
    "tin #": "tin",
    "tin": "tin",
    "account status": "account_status",
    "accountstatus": "account_status",
    "dormant": "dormant_account",
    "is dormant": "dormant_account",
    "isdormant": "dormant_account",
    "dormant account": "dormant_account",
    "dormantaccount": "dormant_account",
    "closed": "closed_account",
    "is closed": "closed_account",
    "isclosed": "closed_account",
    "account closed": "closed_account",
    "accountclosed": "closed_account",
    "closed account": "closed_account",
    "closedaccount": "closed_account",
    "undocumented": "undocumented_account",
    "is undocumented": "undocumented_account",
    "isundocumented": "undocumented_account",
    "undocumented account": "undocumented_account",
    "undocumentedaccount": "undocumented_account",
    "interest & dividend paid": "payment",
    "account balance 31st/12/2025": "account_balance",
}
REQUIRED_ACCOUNT_FIELDS = {
    "account_number",
    "first_name",
    "surname",
    "date_of_birth",
    "address",
    "country",
    "tin",
    "payment",
    "account_balance",
}

NS_OECD_FTC = "urn:fatcacrs:ties:v2"
NS_SFA_FTC = "urn:oecd:ties:fatcacrstypes:v2"
NS_SFA = "urn:oecd:ties:stffatcatypes:v2"
NS_XSI = "http://www.w3.org/2001/XMLSchema-instance"
