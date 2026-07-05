# Dockerfile Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Containerize the `app/` FastAPI service with a multi-stage `python:3.13-slim` Dockerfile, per [docs/superpowers/specs/2026-07-05-dockerfile-design.md](../specs/2026-07-05-dockerfile-design.md), and push a versioned image to Artifact Registry.

**Architecture:** A two-stage Dockerfile: a `builder` stage installs pinned dependencies into `/install`, and a `runtime` stage (same base image) copies only the installed packages and `main.py`, then runs `uvicorn` as a non-root user on port 8080.

**Tech Stack:** Docker, `python:3.13-slim`, uvicorn.

## Global Constraints

- Base image: `python:3.13-slim` for both the builder and runtime stages — no distroless, no alpine.
- Runtime image contains only installed dependencies + `main.py` — never `requirements-dev.txt`, `tests/`, or `conftest.py`.
- Runs as non-root user `appuser` (uid 1000).
- Listens on port 8080; `CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]`.
- Image tag is never `latest` — use explicit versions starting at `v0.1.0` (CLAUDE.md behavior rule 7).
- Artifact Registry path: `asia-northeast3-docker.pkg.dev/project-b3c5c78c-8a5c-4e47-9fe/notiflex-platform`; image name `notiflex-api`.

---

### Task 1: Pin dependency versions

**Files:**
- Modify: `app/requirements.txt`

**Interfaces:** None (dependency manifest only; no code changes).

- [ ] **Step 1: Update `app/requirements.txt` to pinned versions**

Replace its contents with:

```
fastapi==0.139.0
uvicorn==0.50.0
```

- [ ] **Step 2: Rebuild the venv from scratch to verify the pinned versions install cleanly**

Run:
```bash
cd app
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements-dev.txt
```
Expected: install completes with no errors, installing exactly `fastapi==0.139.0` and `uvicorn==0.50.0` (plus their transitive dependencies and the dev-only `pytest`/`httpx`).

- [ ] **Step 3: Run the existing test suite to confirm no regression**

Run (from `app/`, venv active): `python -m pytest tests/ -v`
Expected: PASS — all 4 tests (`test_health_returns_ok`, `test_id_increments_between_calls`, `test_id_returns_pod_field_default_local`, `test_id_returns_pod_name_from_env`).

- [ ] **Step 4: Commit**

```bash
git add app/requirements.txt
git commit -m "Pin fastapi and uvicorn versions for reproducible builds"
```

---

### Task 2: Dockerfile, image build, and Artifact Registry push

**Files:**
- Create: `app/Dockerfile`

**Interfaces:**
- Consumes: `app/requirements.txt` (pinned, from Task 1), `app/main.py` (from the `/health`+`/id` API work).
- Produces: a runnable container image `asia-northeast3-docker.pkg.dev/project-b3c5c78c-8a5c-4e47-9fe/notiflex-platform/notiflex-api:v0.1.0`, pushed to Artifact Registry.

- [ ] **Step 1: Confirm Docker is available**

Run: `docker version`
Expected: prints both a `Client` and `Server` section with no connection errors. If this fails (e.g., Docker Desktop not running), report BLOCKED — do not proceed.

- [ ] **Step 2: Create `app/Dockerfile`**

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

- [ ] **Step 3: Build the image**

Run:
```bash
docker build --platform linux/amd64 -t asia-northeast3-docker.pkg.dev/project-b3c5c78c-8a5c-4e47-9fe/notiflex-platform/notiflex-api:v0.1.0 app/
```
Expected: build completes successfully, ending with `Successfully tagged` (or the equivalent BuildKit "naming to ... done" output) — no errors in either stage.

- [ ] **Step 4: Run the container and smoke-test it**

Run (in one terminal):
```bash
docker run --rm -p 8080:8080 --name notiflex-smoke-test asia-northeast3-docker.pkg.dev/project-b3c5c78c-8a5c-4e47-9fe/notiflex-platform/notiflex-api:v0.1.0
```
In another terminal:
```bash
curl -s localhost:8080/health
curl -s localhost:8080/id
curl -s localhost:8080/id
docker exec notiflex-smoke-test whoami
```
Expected: `/health` returns `{"status":"ok"}`; the two `/id` calls return `{"id":1,"pod":"local"}` then `{"id":2,"pod":"local"}` (no `POD_NAME` set outside Kubernetes); `whoami` prints `appuser` (confirms non-root). Stop the container afterward (Ctrl+C in the first terminal, or `docker stop notiflex-smoke-test`).

- [ ] **Step 5: Push the image to Artifact Registry**

Run:
```bash
docker push asia-northeast3-docker.pkg.dev/project-b3c5c78c-8a5c-4e47-9fe/notiflex-platform/notiflex-api:v0.1.0
```
Expected: push completes successfully, ending with a digest line (e.g., `v0.1.0: digest: sha256:... size: ...`). If this fails with an auth error, re-run `gcloud auth configure-docker asia-northeast3-docker.pkg.dev` (already configured per CLAUDE.md, but re-run if credentials expired) and retry.

- [ ] **Step 6: Commit**

```bash
git add app/Dockerfile
git commit -m "Add Dockerfile for the FastAPI app"
```
