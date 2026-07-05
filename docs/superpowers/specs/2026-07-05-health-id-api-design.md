# notiflex-platform: /health, /id API 설계

## 배경

`notiflex-platform`의 첫 애플리케이션 코드로, Kubernetes readiness/liveness probe에 쓰일 상태 확인 API와, Pod별로 고유 ID를 발급하는 API 2개를 구현한다. 원본 교재는 Go(표준 라이브러리만 사용, 외부 프레임워크 없음)를 기준으로 하지만, 이 프로젝트는 Python으로 대체해서 진행 중이다 ([CLAUDE.md](../../../CLAUDE.md) 참고).

## 요구사항

- `GET /health`: Kubernetes readiness/liveness probe용 상태 확인
- `GET /id`: 고유 ID 생성 (in-memory 카운터 + Pod 이름 반환)

## 결정 사항

- **프레임워크**: FastAPI (+ uvicorn). Python 웹 API의 사실상 표준이며 타입힌트 기반 자동 문서화를 제공한다.
- **파일 구조**: 단일 파일(`app/main.py`)에 앱과 두 라우트를 모두 작성한다. 엔드포인트가 2개뿐인 지금 규모에서 라우터/서비스 계층 분리는 과한 추상화(YAGNI 위반)이므로 보류하고, 이후 엔드포인트가 늘어나면 그때 분리한다.
- **테스트**: pytest + FastAPI `TestClient`로 기본 동작을 검증하는 테스트를 함께 작성한다.
- **의존성 관리**: `requirements.txt`에 `fastapi`, `uvicorn` 명시.

## API 명세

### GET /health

- 응답: `200 OK`, `{"status": "ok"}`
- 별도 상태나 외부 의존성 체크는 하지 않는다 (현재 이 서비스에 DB 등 외부 의존성이 없음).

### GET /id

- 응답: `200 OK`, `{"id": <int>, "pod": <string>}`
- `id`: 프로세스 시작 이후 요청마다 1씩 증가하는 in-memory 카운터 값 (1부터 시작).
- `pod`: 환경변수 `POD_NAME` 값. Kubernetes Downward API(`fieldRef: metadata.name`)로 주입될 예정이며, 값이 없는 로컬 개발 환경에서는 `"local"`로 대체한다.

## 동시성

카운터 증가는 `threading.Lock`으로 보호해 동시 요청 시 경쟁 상태(race condition)를 방지한다.

Pod가 여러 개 떠 있는 경우 각 Pod는 독립적인 in-memory 카운터를 가지므로, `id` 값만으로는 전역적으로 유일하지 않다. 전역 유일성이 필요하면 `pod`와 `id`를 함께 사용해 식별해야 한다. 이번 스코프에서는 별도의 분산 카운터나 외부 저장소를 두지 않는다.

## 에러 처리

두 엔드포인트 모두 실패 가능성이 낮은 단순 로직이므로 별도의 에러 핸들링을 두지 않고, FastAPI 기본 예외 처리(500 응답)에 맡긴다.

## 파일 구성

```
app/
├── main.py           # FastAPI 앱 + /health, /id
├── requirements.txt
└── tests/
    └── test_main.py  # pytest + FastAPI TestClient
```

## 테스트 계획

- `GET /health` 호출 시 `200`과 `{"status": "ok"}`를 반환하는지 확인
- `GET /id`를 여러 번 호출했을 때 `id`가 1씩 증가하는지 확인
- `GET /id` 응답에 `pod` 필드가 존재하는지 확인 (환경변수 미설정 시 `"local"`인지 포함)

## 스코프 외

- 인증/인가
- `/health`의 외부 의존성 체크 (현재 의존성 없음)
- 분산 환경에서의 전역 유일 ID 보장
- 라우터/서비스 계층 분리 (엔드포인트 증가 시 재검토)
