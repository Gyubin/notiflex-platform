# /health, /id API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement `GET /health` and `GET /id` on a FastAPI app in `app/`, per [docs/superpowers/specs/2026-07-05-health-id-api-design.md](../specs/2026-07-05-health-id-api-design.md).

**Architecture:** A single-file FastAPI app (`app/main.py`) exposes two routes. `/health` returns a static OK payload for Kubernetes probes. `/id` increments a process-local, lock-protected counter and returns it together with the pod name (from the `POD_NAME` env var, Kubernetes Downward API).

**Tech Stack:** Python, FastAPI, uvicorn, pytest, httpx (for FastAPI's `TestClient`).

## Global Constraints

- Framework: FastAPI + uvicorn only — do not introduce another web framework.
- File structure: keep everything in `app/main.py` — do not split into routers/services for these 2 endpoints (YAGNI; revisit only when endpoint count grows).
- Tests: pytest + FastAPI `TestClient`.
- Do not commit build artifacts or virtualenvs (`app/.venv/` is already covered by the repo's `.gitignore`).
- No hardcoded credentials (not applicable to this plan's scope, but a standing project rule).

---

### Task 1: FastAPI app scaffold + GET /health

**Files:**
- Create: `app/requirements.txt`
- Create: `app/requirements-dev.txt`
- Create: `app/conftest.py`
- Create: `app/main.py`
- Create: `app/tests/test_main.py`
- Delete: `app/.gitkeep` (no longer needed once `app/` has real files)

**Interfaces:**
- Produces: `app.main:app` — a `FastAPI()` instance that Task 2 will add a route to. `HealthResponse` Pydantic model (`status: str`), defined in `app/main.py`, importable as `from main import HealthResponse`.

- [ ] **Step 1: Create `app/requirements.txt`**

```
fastapi
uvicorn
```

- [ ] **Step 2: Create `app/requirements-dev.txt`**

```
-r requirements.txt
pytest
httpx
```

- [ ] **Step 3: Create a venv and install dependencies**

Run:
```bash
cd app
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements-dev.txt
```
Expected: install completes with no errors, ending in something like `Successfully installed fastapi-... uvicorn-... pytest-... httpx-...`.

- [ ] **Step 4: Create `app/conftest.py`**

```python
# Empty on purpose: its presence makes pytest add app/ (this file's
# directory) to sys.path, so tests can do `from main import app`
# without installing the app as a package.
```

- [ ] **Step 5: Write the failing test for `/health`**

Create `app/tests/test_main.py`:

```python
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 6: Run the test to verify it fails**

Run (from `app/`, with the venv active): `python -m pytest tests/ -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'main'` (since `app/main.py` doesn't exist yet).

- [ ] **Step 7: Write the minimal implementation**

Create `app/main.py`:

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class HealthResponse(BaseModel):
    status: str


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")
```

- [ ] **Step 8: Run the test to verify it passes**

Run: `python -m pytest tests/ -v`
Expected: PASS — `test_main.py::test_health_returns_ok PASSED`.

- [ ] **Step 9: Remove the placeholder file**

```bash
rm app/.gitkeep
```

- [ ] **Step 10: Commit**

```bash
git add app/requirements.txt app/requirements-dev.txt app/conftest.py app/main.py app/tests/test_main.py
git rm app/.gitkeep
git commit -m "Add FastAPI scaffold with GET /health"
```

---

### Task 2: GET /id (in-memory counter + pod name)

**Files:**
- Modify: `app/main.py` (add imports, counter state, `IdResponse` model, `/id` route)
- Modify: `app/tests/test_main.py` (append tests for `/id`)

**Interfaces:**
- Consumes: `app.main:app` and `HealthResponse` from Task 1 (unchanged).
- Produces: `IdResponse` Pydantic model (`id: int`, `pod: str`), `GET /id` route on `app`.

- [ ] **Step 1: Write the failing tests for `/id`**

Append to `app/tests/test_main.py`:

```python
def test_id_increments_between_calls():
    first = client.get("/id").json()["id"]
    second = client.get("/id").json()["id"]
    assert second == first + 1


def test_id_returns_pod_field_default_local():
    response = client.get("/id")
    assert response.status_code == 200
    assert response.json()["pod"] == "local"


def test_id_returns_pod_name_from_env(monkeypatch):
    monkeypatch.setenv("POD_NAME", "notiflex-abc123")
    response = client.get("/id")
    assert response.json()["pod"] == "notiflex-abc123"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run (from `app/`, venv active): `python -m pytest tests/ -v`
Expected: FAIL — the three new tests fail with 404 (`assert 404 == 200` / `KeyError: 'id'`), since `/id` doesn't exist yet. `test_health_returns_ok` still passes.

- [ ] **Step 3: Implement `/id`**

Replace the full contents of `app/main.py` with:

```python
import os
import threading

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

_counter_lock = threading.Lock()
_counter = 0


class HealthResponse(BaseModel):
    status: str


class IdResponse(BaseModel):
    id: int
    pod: str


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/id", response_model=IdResponse)
def get_id() -> IdResponse:
    global _counter
    with _counter_lock:
        _counter += 1
        current_id = _counter
    pod_name = os.environ.get("POD_NAME", "local")
    return IdResponse(id=current_id, pod=pod_name)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/ -v`
Expected: PASS — all 4 tests pass (`test_health_returns_ok`, `test_id_increments_between_calls`, `test_id_returns_pod_field_default_local`, `test_id_returns_pod_name_from_env`).

- [ ] **Step 5: Manual smoke test**

Run (from `app/`, venv active, in one terminal):
```bash
uvicorn main:app --host 0.0.0.0 --port 8080
```
In another terminal:
```bash
curl -s localhost:8080/health
curl -s localhost:8080/id
curl -s localhost:8080/id
POD_NAME=notiflex-test-pod uvicorn main:app --port 8081 &
curl -s localhost:8081/id
```
Expected: `/health` returns `{"status":"ok"}`; the two `/id` calls on port 8080 return `{"id":1,"pod":"local"}` then `{"id":2,"pod":"local"}`; the call to port 8081 returns `{"id":1,"pod":"notiflex-test-pod"}` (separate process = separate counter). Stop both servers (Ctrl+C / `kill %1`) when done.

- [ ] **Step 6: Commit**

```bash
git add app/main.py app/tests/test_main.py
git commit -m "Add GET /id with in-memory counter and pod name"
```
