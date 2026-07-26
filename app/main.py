import asyncio
import json
import logging
import os
import platform
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import redis
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from fastapi import FastAPI, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel

# uvicorn 은 자기 로거만 설정하므로, 이걸 안 하면 root 로거에 핸들러가 없어
# 앱이 직접 남기는 logger.info 가 전부 사라진다 (액세스 로그만 보인다).
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

VALKEY_CONNECT_ATTEMPTS = 10
VALKEY_CONNECT_RETRY_SECONDS = 3
_valkey_client: redis.Redis | None = None

# ch8.1: 이 Pod이 속한 테넌트. 메시지 키와 Consumer Group 이름에 함께 쓴다.
# 네임스페이스마다 다른 값을 Rollout에서 주입한다 (notiflex / enterprise).
TENANT = os.environ.get("TENANT", "local")
NOTIFICATIONS_TOPIC = "notifications"

_kafka_producer: AIOKafkaProducer | None = None
_kafka_consumer_task: asyncio.Task[None] | None = None
# Consumer가 이 Pod에서 실제로 받아간 메시지 수. Gateway에서 바로 확인하려고 노출한다.
_consumed_count = 0
_last_consumed: dict[str, object] | None = None


async def publish_notification(payload: dict[str, object]) -> None:
    """알림 이벤트를 Kafka로 보낸다. 브로커가 없으면 조용히 건너뛴다.

    KAFKA_BROKER가 없으면 Producer 자체를 만들지 않으므로, 로컬 개발과 테스트는
    Kafka 없이도 그대로 돌아간다.
    """
    if _kafka_producer is None:
        return
    await _kafka_producer.send_and_wait(
        NOTIFICATIONS_TOPIC,
        value=json.dumps(payload).encode(),
        # 같은 테넌트의 메시지가 같은 파티션으로 가서 순서가 보장된다.
        # 주의: 이건 "구분"이지 "격리"가 아니다. 같은 토픽을 구독하면 남의 메시지도 보인다.
        key=TENANT.encode(),
    )


async def consume_notifications(broker: str) -> None:
    """notifications 토픽을 구독해 수신 내역을 로그로 남긴다."""
    global _consumed_count, _last_consumed

    consumer = AIOKafkaConsumer(
        NOTIFICATIONS_TOPIC,
        bootstrap_servers=broker,
        # 테넌트별로 그룹을 나눠야 각 테넌트가 토픽 전체를 독립적으로 읽는다.
        # 그룹을 공유하면 두 테넌트가 파티션을 나눠 갖고 서로의 메시지를 절반씩 가져간다.
        group_id=f"notiflex-{TENANT}",
        auto_offset_reset="latest",
        enable_auto_commit=True,
    )
    await consumer.start()
    logger.info("Kafka Consumer 시작: topic=%s group=notiflex-%s", NOTIFICATIONS_TOPIC, TENANT)
    try:
        async for message in consumer:
            event = json.loads(message.value.decode())
            _consumed_count += 1
            _last_consumed = event
            logger.info(
                "Kafka 메시지 수신: partition=%d offset=%d tenant=%s id=%s",
                message.partition,
                message.offset,
                event.get("tenant"),
                event.get("id"),
            )
    except asyncio.CancelledError:
        logger.info("Kafka Consumer 종료 요청 수신")
        raise
    finally:
        await consumer.stop()


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
    global _valkey_client, _kafka_producer, _kafka_consumer_task
    _valkey_client = connect_to_valkey()

    broker = os.environ.get("KAFKA_BROKER")
    if broker:
        _kafka_producer = AIOKafkaProducer(bootstrap_servers=broker)
        await _kafka_producer.start()
        logger.info("Kafka Producer 연결: %s", broker)
        _kafka_consumer_task = asyncio.create_task(consume_notifications(broker))
    else:
        logger.info("KAFKA_BROKER 미설정 — 메시징 비활성화 상태로 기동")

    try:
        yield
    finally:
        if _kafka_consumer_task is not None:
            _kafka_consumer_task.cancel()
            # Consumer가 브로커에서 깔끔히 빠져나가도록 종료를 기다린다.
            await asyncio.gather(_kafka_consumer_task, return_exceptions=True)
            _kafka_consumer_task = None
        if _kafka_producer is not None:
            await _kafka_producer.stop()
            _kafka_producer = None
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
    tenant: str
    published: bool


class NotificationsResponse(BaseModel):
    tenant: str
    pod: str
    consumed: int
    last: dict | None


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
async def get_id() -> IdResponse:
    if _valkey_client is None:
        raise HTTPException(status_code=503, detail="Valkey 연결이 준비되지 않았습니다")
    # redis 클라이언트가 동기라 별도 스레드로 넘긴다. 이벤트 루프에서 직접 호출하면
    # INCR이 끝날 때까지 다른 요청 처리가 멈춘다.
    current_id = await asyncio.to_thread(_valkey_client.incr, "notiflex:id")
    pod_name = os.environ.get("POD_NAME", "local")

    # ch8.1: ID 발급까지만 동기로 끝내고, 실제 알림 처리는 이벤트로 넘긴다.
    event = {"id": current_id, "tenant": TENANT, "pod": pod_name}
    await publish_notification(event)

    return IdResponse(
        id=current_id,
        pod=pod_name,
        tenant=TENANT,
        published=_kafka_producer is not None,
    )


@app.get("/notifications", response_model=NotificationsResponse)
def notifications() -> NotificationsResponse:
    """이 Pod의 Consumer가 받아간 메시지 현황. kubectl 없이 Gateway로 확인하려고 둔다."""
    return NotificationsResponse(
        tenant=TENANT,
        pod=os.environ.get("POD_NAME", "local"),
        consumed=_consumed_count,
        last=_last_consumed,
    )
