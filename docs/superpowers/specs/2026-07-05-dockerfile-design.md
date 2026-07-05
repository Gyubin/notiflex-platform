# notiflex-platform: Dockerfile 설계

## 배경

`app/`의 FastAPI 서비스(`GET /health`, `GET /id`)를 GKE에 배포하기 위한 컨테이너 이미지를 만든다. 원본 교재(Go)는 `scratch` 베이스로 최소 이미지를 추구했지만, Python은 런타임이 필요해 완전히 동일하게는 불가능하다.

## 요구사항

- `app/`의 FastAPI 앱을 컨테이너 이미지로 빌드한다.
- GCP Artifact Registry(`asia-northeast3-docker.pkg.dev/project-b3c5c78c-8a5c-4e47-9fe/notiflex-platform`)에 push할 수 있어야 한다.
- CLAUDE.md 행동규칙 7번(이미지 태그에 `latest` 대신 명시적 버전 사용)을 따른다.

## 결정 사항

### 베이스 이미지: `python:3.13-slim` + 멀티스테이지 빌드

`gcr.io/distroless/python3-debian12`(distroless)와 `python:3.13-alpine`도 검토했으나 다음 이유로 제외했다:

- **distroless**: 내장 파이썬 버전이 고정되어 있어, `pydantic-core`(Rust 컴파일 확장)처럼 컴파일된 의존성은 빌더 이미지와 정확히 같은 파이썬 버전/ABI로 맞춰야 한다. 버전이 어긋나면 컨테이너가 기동 시점에 조용히 죽는데, 쉘이 없어 `kubectl exec`로 들어가 디버깅할 수 없다. 지금 단계에서는 이 리스크가 학습 목표(GKE 운영 실습) 대비 부담이 크다.
- **alpine**: musl libc 기반이라 `pydantic-core` 같은 컴파일된 wheel이 PyPI에 없는 경우가 많아 소스 빌드가 필요해지고, 빌드 도구 때문에 오히려 이미지가 커진다.

`python:3.13-slim`은 쉘이 있어 문제 발생 시 디버깅이 가능하고, 빌더/런타임 스테이지가 동일 베이스라 컴파일된 의존성의 호환성 문제가 없다. 필요해지면 이후 마지막 스테이지만 distroless로 교체할 수 있다.

### 멀티스테이지 빌드

- **builder 스테이지**: `requirements.txt`만 복사해 의존성을 `/install`에 설치 (레이어 캐싱 활용)
- **runtime 스테이지**: builder에서 설치된 패키지와 `main.py`만 복사. `requirements-dev.txt`, `tests/`, `conftest.py`는 이미지에 포함하지 않는다 (필요한 파일만 명시적으로 `COPY`해서, 별도 `.dockerignore` 없이도 깔끔하게 분리).

### 실행 계정

`appuser`(uid 1000)를 생성해 non-root로 실행한다 (`USER appuser`).

### 포트 및 실행 커맨드

포트 8080, `CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]`. 기존 로컬 스모크 테스트(Task 2)와 동일한 포트를 사용해 일관성을 유지한다.

### 의존성 버전 고정

이전 최종 코드 리뷰에서 "Dockerfile 작업 전에 의존성 버전을 고정하라"는 권장이 있었다. 이번 작업 범위에 포함해 `app/requirements.txt`를 현재 설치된 버전으로 고정한다:

```
fastapi==0.139.0
uvicorn==0.50.0
```

`app/requirements-dev.txt`(pytest, httpx)는 이미지 빌드에 쓰이지 않으므로 고정하지 않는다.

## Dockerfile 초안

```dockerfile
# ---- builder ----
FROM python:3.13-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- runtime ----
FROM python:3.13-slim
RUN useradd --create-home --uid 1000 appuser
WORKDIR /app
COPY --from=builder --chown=appuser:appuser /install /usr/local
COPY --chown=appuser:appuser main.py .
USER appuser
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

## 빌드 및 푸시

```bash
docker build -t asia-northeast3-docker.pkg.dev/project-b3c5c78c-8a5c-4e47-9fe/notiflex-platform/notiflex-api:v0.1.0 app/
docker push asia-northeast3-docker.pkg.dev/project-b3c5c78c-8a5c-4e47-9fe/notiflex-platform/notiflex-api:v0.1.0
```

이미지 이름은 `notiflex-api`, 태그는 CLAUDE.md 행동규칙에 따라 `latest`를 쓰지 않고 `v0.1.0`부터 시작한다.

## 검증 계획

- `docker build`로 이미지가 에러 없이 빌드되는지 확인
- `docker run -p 8080:8080 <image>`로 컨테이너를 띄우고 `curl localhost:8080/health`, `curl localhost:8080/id`를 호출해 로컬 개발 환경과 동일하게 동작하는지 확인
- 컨테이너 안에서 non-root로 실행되는지 확인 (`docker exec <container> whoami` → `appuser`)

## 스코프 외

- GitHub Actions를 통한 자동 빌드/푸시 (`.github/workflows/`, 이후 CI 챕터에서 다룸)
- Docker `HEALTHCHECK` 지시어 — Kubernetes가 자체 HTTP probe로 `/health`를 호출할 예정이라 중복이라 추가하지 않는다.
- distroless로의 전환 (필요해지면 마지막 스테이지 베이스만 바꿔서 별도로 진행)
