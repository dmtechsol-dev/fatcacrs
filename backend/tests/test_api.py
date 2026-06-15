import pytest
from fastapi.testclient import TestClient
from lxml import etree

import backend.main as main_module
from backend.main import app
from backend.models import AccountRecord, SchemaValidationResult
from backend.tests.conftest import HEADERS, workbook_bytes


def test_api_health_reports_service_status():
    response = TestClient(app).get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "fatca-crs-xml-generator"


def test_deployment_health_route():
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_root_returns_frontend_or_service_status():
    response = TestClient(app).get("/")
    assert response.status_code == 200
    if response.headers["content-type"].startswith("text/html"):
        assert "FC XML Studio" in response.text
    else:
        assert response.json()["status"] == "ok"
        assert response.json()["apiPrefix"] == "/api"


def test_frontend_route_uses_spa_fallback_when_build_exists():
    response = TestClient(app).get("/validation/review")
    if response.status_code == 200:
        assert response.headers["content-type"].startswith("text/html")
        assert "FC XML Studio" in response.text
    else:
        assert response.status_code == 503


def test_unknown_api_route_is_not_frontend_fallback():
    response = TestClient(app).get("/api/not-a-real-route")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}


def test_missing_frontend_asset_returns_404():
    response = TestClient(app).get("/assets/not-a-real-asset.js")
    assert response.status_code == 404


def test_required_frontend_blocks_startup_when_build_is_missing(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(main_module, "REQUIRE_FRONTEND", True)
    monkeypatch.setattr(main_module, "FRONTEND_INDEX", tmp_path / "index.html")
    monkeypatch.setattr(main_module, "FRONTEND_ASSETS_DIR", tmp_path / "assets")
    with pytest.raises(RuntimeError, match="Frontend build is required"):
        with TestClient(app):
            pass


def test_upload_endpoint_parses_workbook():
    content = workbook_bytes(
        [[900, "A", "B", None, "A complete address", "GB", None, False, 0, 1]]
    )
    response = TestClient(app).post(
        "/api/upload-excel",
        files={
            "file": (
                "accounts.xlsx",
                content,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["totalRecords"] == 1
    assert payload["records"][0]["rowNumber"] == 2
    assert payload["statusMapping"]["accountStatus"] == "Account Status"
    assert payload["financialInstitutionIn"] is None


def test_workbook_fi_in_takes_priority_for_doc_ref_ids(
    monkeypatch, settings
):
    monkeypatch.setenv("FINANCIAL_INSTITUTION_IN", "ENVIN")
    headers = [*HEADERS, "Financial Institution IN"]
    content = workbook_bytes(
        [
            [
                900,
                "A",
                "B",
                "1980-01-01",
                "A complete address",
                "GB",
                "TIN-1",
                "FALSE",
                10,
                100,
                "WORKBOOKIN",
            ]
        ],
        headers=headers,
    )
    client = TestClient(app)
    upload = client.post(
        "/api/upload-excel",
        files={
            "file": (
                "accounts.xlsx",
                content,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert upload.status_code == 200
    payload = upload.json()
    configured = settings.model_copy(
        update={"financial_institution_in": "APPIN"}
    )
    generation = client.post(
        "/api/generate-xml",
        json={
            "sessionId": payload["sessionId"],
            "records": payload["records"],
            "settings": configured.model_dump(by_alias=True),
        },
    )
    assert generation.status_code == 200
    refs = etree.fromstring(
        generation.json()["xmlPreview"].encode()
    ).xpath("//*[local-name()='DocRefId']/text()")
    assert refs == [
        "DM2025WORKBOOKIN000000",
        "DM2025WORKBOOKIN000001",
    ]


def test_app_setting_fi_in_takes_priority_over_environment(
    monkeypatch, settings
):
    monkeypatch.setenv("FINANCIAL_INSTITUTION_IN", "ENVIN")
    record = AccountRecord(
        row_number=2,
        account_number="900",
        first_name="A",
        surname="B",
        date_of_birth="1980-01-01",
        address="A complete address",
        country="GB",
        tin="TIN-1",
        payment="10",
        account_balance="100",
    )
    generation = TestClient(app).post(
        "/api/generate-xml",
        json={
            "records": [record.model_dump(by_alias=True)],
            "settings": settings.model_dump(by_alias=True),
        },
    )
    assert generation.status_code == 200
    assert "DM2025FIIN000001" in generation.json()["xmlPreview"]


def test_environment_fi_in_is_used_as_final_fallback(monkeypatch, settings):
    monkeypatch.setenv("FINANCIAL_INSTITUTION_IN", "ENVIN")
    configured = settings.model_copy(
        update={"financial_institution_in": ""}
    )
    record = AccountRecord(
        row_number=2,
        account_number="900",
        first_name="A",
        surname="B",
        date_of_birth="1980-01-01",
        address="A complete address",
        country="GB",
        tin="TIN-1",
        payment="10",
        account_balance="100",
    )
    generation = TestClient(app).post(
        "/api/generate-xml",
        json={
            "records": [record.model_dump(by_alias=True)],
            "settings": configured.model_dump(by_alias=True),
        },
    )
    assert generation.status_code == 200
    assert "DM2025ENVIN000001" in generation.json()["xmlPreview"]


def test_missing_fi_in_blocks_generation(monkeypatch, settings):
    monkeypatch.delenv("FINANCIAL_INSTITUTION_IN", raising=False)
    configured = settings.model_copy(
        update={"financial_institution_in": ""}
    )
    record = AccountRecord(
        row_number=2,
        account_number="900",
        first_name="A",
        surname="B",
        address="A complete address",
        country="GB",
        payment="10",
        account_balance="100",
    )
    response = TestClient(app).post(
        "/api/generate-xml",
        json={
            "records": [record.model_dump(by_alias=True)],
            "settings": configured.model_dump(by_alias=True),
        },
    )
    assert response.status_code == 422
    assert "Financial institution IN is required" in response.json()["detail"]


def test_invalid_xsd_blocks_download_unless_draft_is_explicit(
    monkeypatch, settings
):
    monkeypatch.setattr(
        main_module,
        "validate_xml",
        lambda *_args: SchemaValidationResult(
            status="invalid",
            valid=False,
            full_validation=True,
            message="Generated XML failed XSD validation.",
            errors=["Line 1: test schema failure"],
        ),
    )
    record = AccountRecord(
        row_number=2,
        account_number="900",
        first_name="A",
        surname="B",
        date_of_birth="1980-01-01",
        address="A complete address",
        country="GB",
        tin="TIN-1",
        payment="10",
        account_balance="100",
    )
    request = {
        "records": [record.model_dump(by_alias=True)],
        "settings": settings.model_dump(by_alias=True),
        "allowDraft": False,
    }
    client = TestClient(app)
    blocked = client.post("/api/generate-xml", json=request)
    assert blocked.status_code == 422
    assert "Full XSD validation did not pass" in blocked.json()["detail"]["message"]

    request["allowDraft"] = True
    draft = client.post("/api/generate-xml", json=request)
    assert draft.status_code == 200
    assert draft.json()["draft"]
    assert draft.json()["xml"]["fileName"].startswith("DRAFT_")


def test_api_keeps_dormant_and_closed_status_sources_separate(settings):
    headers = [*HEADERS, "Account Closed", "Undocumented Account"]
    content = workbook_bytes(
        [
            [
                900,
                "Dormant",
                "Holder",
                "1980-01-01",
                "A complete address",
                "GB",
                "TIN-1",
                "TRUE",
                10,
                100,
                "No",
                "No",
            ],
            [
                901,
                "Closed",
                "Holder",
                "1980-01-01",
                "A complete address",
                "GB",
                "TIN-2",
                "FALSE",
                10,
                100,
                "Yes",
                "No",
            ],
        ],
        headers=headers,
    )
    client = TestClient(app)
    upload = client.post(
        "/api/upload-excel",
        files={
            "file": (
                "accounts.xlsx",
                content,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert upload.status_code == 200
    payload = upload.json()
    generation = client.post(
        "/api/generate-xml",
        json={
            "sessionId": payload["sessionId"],
            "records": payload["records"],
            "settings": settings.model_dump(by_alias=True),
            "allowDraft": False,
        },
    )
    assert generation.status_code == 200
    account_numbers = etree.fromstring(
        generation.json()["xmlPreview"].encode()
    ).xpath("//*[local-name()='AccountNumber']")
    assert account_numbers[0].get("DormantAccount") == "true"
    assert account_numbers[0].get("ClosedAccount") == "false"
    assert account_numbers[0].get("UndocumentedAccount") == "false"
    assert account_numbers[1].get("DormantAccount") == "false"
    assert account_numbers[1].get("ClosedAccount") == "true"
    assert account_numbers[1].get("UndocumentedAccount") == "false"
