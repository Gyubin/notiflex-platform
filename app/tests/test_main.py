from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version_returns_app_version():
    from main import APP_VERSION

    response = client.get("/version")
    assert response.status_code == 200
    assert response.json() == {"version": APP_VERSION}


def test_id_increments_between_calls():
    first = client.get("/id").json()["id"]
    second = client.get("/id").json()["id"]
    assert second == first + 1


def test_id_returns_pod_field_default_local(monkeypatch):
    monkeypatch.delenv("POD_NAME", raising=False)
    response = client.get("/id")
    assert response.status_code == 200
    assert response.json()["pod"] == "local"


def test_id_returns_pod_name_from_env(monkeypatch):
    monkeypatch.setenv("POD_NAME", "notiflex-abc123")
    response = client.get("/id")
    assert response.json()["pod"] == "notiflex-abc123"
