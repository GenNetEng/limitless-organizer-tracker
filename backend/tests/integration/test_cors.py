from fastapi.testclient import TestClient

from app.main import app


def test_allows_cross_origin_requests_from_configured_frontend_origin():
    client = TestClient(app)

    response = client.get("/healthz", headers={"Origin": "http://localhost:5173"})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_preflight_allows_get_to_status_history_from_frontend_origin():
    client = TestClient(app)

    response = client.options(
        "/api/status-history",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_preflight_allows_post_to_status_check_from_frontend_origin():
    client = TestClient(app)

    response = client.options(
        "/api/status-check",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "POST" in response.headers["access-control-allow-methods"]


def test_preflight_allows_put_to_admin_config_from_frontend_origin():
    client = TestClient(app)

    response = client.options(
        "/api/admin/config",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "PUT",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "PUT" in response.headers["access-control-allow-methods"]
