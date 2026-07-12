import os
import platform
import threading

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# 버전은 빌드 시 --build-arg APP_VERSION=<git tag>로 주입되어 이미지 ENV에 구워진다.
# 로컬 실행 등 미주입 시 "dev".
APP_VERSION = os.environ.get("APP_VERSION", "dev")

_counter_lock = threading.Lock()
_counter = 0


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
    global _counter
    with _counter_lock:
        _counter += 1
        current_id = _counter
    pod_name = os.environ.get("POD_NAME", "local")
    return IdResponse(id=current_id, pod=pod_name)
