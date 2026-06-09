from fastapi.testclient import TestClient

from backend.main import app
from backend.tests.conftest import workbook_bytes


def test_health_reports_local_only():
    response = TestClient(app).get("/api/health")
    assert response.status_code == 200
    assert response.json()["localOnly"] is True


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
