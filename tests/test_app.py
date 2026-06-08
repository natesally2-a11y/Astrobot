from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_healthcheck():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_demo_profile_endpoint():
    response = client.get("/api/webapp/profile")
    assert response.status_code == 200
    payload = response.json()
    assert payload["user"]["first_name"] == "Demo User"
    assert "chart_summary" in payload


def test_demo_chart_svg_endpoint():
    response = client.get("/api/webapp/chart.svg")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")
    assert "<svg" in response.text
