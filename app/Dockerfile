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
