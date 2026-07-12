# ---- builder ----
FROM python:3.13-slim AS builder
# uv 바이너리 주입 (로컬과 동일 버전으로 핀)
COPY --from=ghcr.io/astral-sh/uv:0.9.18 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy
WORKDIR /app
# uv.lock 기준으로 정확히 동일한 의존성 설치 (로컬 uv sync와 바이트 단위 일치)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# ---- runtime ----
FROM python:3.13-slim
RUN useradd --create-home --uid 1000 appuser
WORKDIR /app
# 의존성(venv)/코드는 root 소유로 두어 appuser가 변조할 수 없게 한다 (읽기만 가능)
COPY --from=builder /app/.venv /app/.venv
COPY main.py .
ENV PATH="/app/.venv/bin:$PATH"
USER appuser
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
