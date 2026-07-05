# ---- builder ----
FROM python:3.13-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- runtime ----
FROM python:3.13-slim
RUN useradd --create-home --uid 1000 appuser
WORKDIR /app
# 의존성/코드는 root 소유로 두어 appuser가 변조할 수 없게 한다 (읽기만 가능)
COPY --from=builder /install /usr/local
COPY main.py .
USER appuser
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
