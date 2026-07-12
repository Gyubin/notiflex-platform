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
    body = response.json()
    assert body["version"] == APP_VERSION
    assert body["runtime"].startswith("python ")
    assert "pod" in body


def test_version_returns_pod_name_from_env(monkeypatch):
    monkeypatch.setenv("POD_NAME", "notiflex-xyz789")
    response = client.get("/version")
    assert response.json()["pod"] == "notiflex-xyz789"


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


def test_metrics_endpoint_exposes_prometheus_format():
    # 한 번 요청을 발생시켜 카운터가 증가하도록 한 뒤 /metrics를 조회한다.
    client.get("/health")
    response = client.get("/metrics")
    assert response.status_code == 200
    body = response.text
    # prometheus-fastapi-instrumentator 기본 히스토그램 계측 노출 확인
    assert "http_request_duration_seconds" in body
