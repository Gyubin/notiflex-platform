import logging
import os
import platform
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import redis
from fastapi import FastAPI, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel

logger = logging.getLogger(__name__)

VALKEY_CONNECT_ATTEMPTS = 10
VALKEY_CONNECT_RETRY_SECONDS = 3
_valkey_client: redis.Redis | None = None


def get_valkey_password() -> str:
    """CSI가 마운트한 파일을 우선 사용하고, 로컬 개발은 환경변수를 사용한다."""
    password_file = os.environ.get("VALKEY_PASSWORD_FILE")
    if password_file:
        return Path(password_file).read_text()
    return os.environ["VALKEY_PASSWORD"]


def connect_to_valkey() -> redis.Redis:
    """Valkey가 준비될 때까지 연결을 확인해 시작 순서 경합을 흡수한다."""
    address = os.environ["VALKEY_ADDR"]
    password = get_valkey_password()
    host, port = address.rsplit(":", maxsplit=1)

    for attempt in range(1, VALKEY_CONNECT_ATTEMPTS + 1):
        client = redis.Redis(
            host=host,
            port=int(port),
            password=password,
            decode_responses=True,
            socket_connect_timeout=2,
        )
        try:
            client.ping()
            logger.info("Valkey 연결 성공: %s", address)
            return client
        except redis.RedisError as error:
            client.close()
            if attempt == VALKEY_CONNECT_ATTEMPTS:
                raise RuntimeError("Valkey 연결 재시도 횟수를 초과했습니다") from error
            logger.warning(
                "Valkey 연결 재시도 %d/%d: %s",
                attempt,
                VALKEY_CONNECT_ATTEMPTS,
                error,
            )
            time.sleep(VALKEY_CONNECT_RETRY_SECONDS)

    raise AssertionError("Valkey 연결 시도 횟수 계산 오류")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    global _valkey_client
    _valkey_client = connect_to_valkey()
    try:
        yield
    finally:
        _valkey_client.close()
        _valkey_client = None


app = FastAPI(lifespan=lifespan)

# Prometheus 계측: /metrics 엔드포인트로 HTTP 요청 수·지연 등을 노출한다.
# 단일 uvicorn 워커 + 인메모리 레지스트리라 readOnlyRootFilesystem와 충돌하지 않는다.
# (다중 워커로 전환하면 multiprocess 모드 + 쓰기 가능 디렉터리가 필요하다.)
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

# 버전은 빌드 시 --build-arg APP_VERSION=<git tag>로 주입되어 이미지 ENV에 구워진다.
# 로컬 실행 등 미주입 시 "dev".
APP_VERSION = os.environ.get("APP_VERSION", "dev")

class HealthResponse(BaseModel):
    status: str


class VersionResponse(BaseModel):
    version: str
    runtime: str
    pod: str


class IdResponse(BaseModel):
    id: int
    pod: str


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/version", response_model=VersionResponse)
def version() -> VersionResponse:
    pod_name = os.environ.get("POD_NAME", "local")
    return VersionResponse(
        version=APP_VERSION,
        runtime=f"python {platform.python_version()}",
        pod=pod_name,
    )


@app.get("/id", response_model=IdResponse)
def get_id() -> IdResponse:
    if _valkey_client is None:
        raise HTTPException(status_code=503, detail="Valkey 연결이 준비되지 않았습니다")
    current_id = _valkey_client.incr("notiflex:id")
    pod_name = os.environ.get("POD_NAME", "local")
    return IdResponse(id=current_id, pod=pod_name)
