import pytest
from fastapi.testclient import TestClient

import backend.main as main_module
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
