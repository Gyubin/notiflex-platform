import pytest
from fastapi.testclient import TestClient
from redis.exceptions import ConnectionError

import main

client = TestClient(main.app)


class FakeValkey:
    def __init__(self) -> None:
        self.value = 0

    def incr(self, _: str) -> int:
        self.value += 1
        return self.value


@pytest.fixture
def valkey_client(monkeypatch):
    fake = FakeValkey()
    monkeypatch.setattr(main, "_valkey_client", fake)
    return fake


def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version_returns_app_version():
    response = client.get("/version")
    assert response.status_code == 200
    body = response.json()
    assert body["version"] == main.APP_VERSION
    assert body["runtime"].startswith("python ")
    assert "pod" in body


def test_version_returns_pod_name_from_env(monkeypatch):
    monkeypatch.setenv("POD_NAME", "notiflex-xyz789")
    response = client.get("/version")
    assert response.json()["pod"] == "notiflex-xyz789"


def test_id_increments_between_calls(valkey_client):
    first = client.get("/id").json()["id"]
    second = client.get("/id").json()["id"]
    assert second == first + 1


def test_id_returns_pod_field_default_local(monkeypatch, valkey_client):
    monkeypatch.delenv("POD_NAME", raising=False)
    response = client.get("/id")
    assert response.status_code == 200
    assert response.json()["pod"] == "local"


def test_id_returns_pod_name_from_env(monkeypatch, valkey_client):
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


def test_connect_to_valkey_retries_until_ping_succeeds(monkeypatch):
    attempts = 0
    sleeps = []
    connection_args = {}

    class FlakyValkey:
        def ping(self):
            nonlocal attempts
            attempts += 1
            if attempts < 4:
                raise ConnectionError("not ready")

        def close(self):
            pass

    def create_client(**kwargs):
        connection_args.update(kwargs)
        return FlakyValkey()

    monkeypatch.setenv("VALKEY_ADDR", "valkey-primary.notiflex.svc.cluster.local:6379")
    monkeypatch.setenv("VALKEY_PASSWORD", "test-password")
    monkeypatch.setattr(main.redis, "Redis", create_client)
    monkeypatch.setattr(main.time, "sleep", sleeps.append)

    client_instance = main.connect_to_valkey()

    assert isinstance(client_instance, FlakyValkey)
    assert attempts == 4
    assert sleeps == [3, 3, 3]
    assert connection_args["host"] == "valkey-primary.notiflex.svc.cluster.local"
    assert connection_args["port"] == 6379
    assert connection_args["password"] == "test-password"
