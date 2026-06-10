from fastapi.testclient import TestClient

from backend.main import app
from backend.tests.conftest import workbook_bytes


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
