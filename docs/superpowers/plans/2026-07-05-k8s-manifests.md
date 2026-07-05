# Namespace/Deployment/Service Manifests Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy `notiflex-api:v0.1.0` to the `notiflex-cluster` GKE cluster via declarative Namespace, Deployment, and Service manifests in `k8s/smb/`, per [docs/superpowers/specs/2026-07-05-k8s-manifests-design.md](../specs/2026-07-05-k8s-manifests-design.md).

**Architecture:** Three separate YAML files, one resource each. The Deployment runs 2 replicas of the existing container image with a readiness/liveness probe on `/health`, `POD_NAME` injected via the Downward API, and a hardened `securityContext`. The Service is a `ClusterIP` selecting the Deployment's pods.

**Tech Stack:** Kubernetes (GKE Standard), `kubectl`.

## Global Constraints

- Every `kubectl` command must include `--context notiflex-gke` (CLAUDE.md behavior rule 5 — this kubeconfig also has company AWS EKS contexts).
- `KUBECONFIG` must be exported explicitly in every shell command that runs `kubectl`: `export KUBECONFIG="$HOME/.kube/config:$HOME/.kube/config-personal"`. Shell profile files (`~/.zshrc`) are not sourced by non-interactive tool shells, so this cannot be assumed to already be set — always include it.
- Namespace: `notiflex` for every namespaced resource.
- Image: `asia-northeast3-docker.pkg.dev/project-b3c5c78c-8a5c-4e47-9fe/notiflex-platform/notiflex-api:v0.1.0` — this exact tag, do not change it (CLAUDE.md rule against reusing/changing tags outside a real release).
- Deployment `securityContext` must be exactly: `runAsNonRoot: true`, `runAsUser: 1000`, `readOnlyRootFilesystem: true` — no additional securityContext fields.
- File layout: one resource per file in `k8s/smb/` — `namespace.yaml`, `deployment.yaml`, `service.yaml`.

---

### Task 1: Namespace manifest

**Files:**
- Create: `k8s/smb/namespace.yaml`
- Delete: `k8s/smb/.gitkeep` (no longer needed once `k8s/smb/` has real files)

**Interfaces:**
- Produces: namespace `notiflex` (already exists imperatively; this makes it declarative/idempotent).

- [ ] **Step 1: Create `k8s/smb/namespace.yaml`**

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: notiflex
```

- [ ] **Step 2: Apply it**

Run:
```bash
export KUBECONFIG="$HOME/.kube/config:$HOME/.kube/config-personal"
kubectl --context notiflex-gke apply -f k8s/smb/namespace.yaml
```
Expected: `namespace/notiflex configured`, possibly preceded by a one-time warning like `Warning: resource namespaces/notiflex is missing the kubectl.kubernetes.io/last-applied-configuration annotation...`. This is expected — the namespace already exists from earlier manual (non-apply) creation, so kubectl patches in the annotation it needs to track this resource declaratively going forward. Not an error.

- [ ] **Step 3: Verify**

Run: `kubectl --context notiflex-gke get namespace notiflex`
Expected: `STATUS` column shows `Active`.

- [ ] **Step 4: Commit**

```bash
git add k8s/smb/namespace.yaml
git rm k8s/smb/.gitkeep
git commit -m "Add Namespace manifest for notiflex"
```

---

### Task 2: Deployment manifest

**Files:**
- Create: `k8s/smb/deployment.yaml`

**Interfaces:**
- Consumes: namespace `notiflex` (Task 1), image `asia-northeast3-docker.pkg.dev/project-b3c5c78c-8a5c-4e47-9fe/notiflex-platform/notiflex-api:v0.1.0`.
- Produces: Deployment `notiflex-api` in namespace `notiflex`, pods labeled `app: notiflex-api` (Task 3's Service selector matches this label).

- [ ] **Step 1: Create `k8s/smb/deployment.yaml`**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: notiflex-api
  namespace: notiflex
spec:
  replicas: 2
  selector:
    matchLabels:
      app: notiflex-api
  template:
    metadata:
      labels:
        app: notiflex-api
    spec:
      containers:
        - name: notiflex-api
          image: asia-northeast3-docker.pkg.dev/project-b3c5c78c-8a5c-4e47-9fe/notiflex-platform/notiflex-api:v0.1.0
          ports:
            - containerPort: 8080
          env:
            - name: POD_NAME
              valueFrom:
                fieldRef:
                  fieldPath: metadata.name
          readinessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 3
            periodSeconds: 5
          livenessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 10
          resources:
            requests:
              cpu: 50m
              memory: 64Mi
            limits:
              cpu: 200m
              memory: 128Mi
          securityContext:
            runAsNonRoot: true
            runAsUser: 1000
            readOnlyRootFilesystem: true
```

- [ ] **Step 2: Apply it**

Run:
```bash
export KUBECONFIG="$HOME/.kube/config:$HOME/.kube/config-personal"
kubectl --context notiflex-gke apply -f k8s/smb/deployment.yaml
```
Expected: `deployment.apps/notiflex-api created`.

- [ ] **Step 3: Wait for rollout to complete**

Run: `kubectl --context notiflex-gke -n notiflex rollout status deployment/notiflex-api --timeout=120s`
Expected: `deployment "notiflex-api" successfully rolled out`. If this times out, run `kubectl --context notiflex-gke -n notiflex describe pods -l app=notiflex-api` and `kubectl --context notiflex-gke -n notiflex logs -l app=notiflex-api --all-containers` to diagnose — a likely cause is `readOnlyRootFilesystem` blocking a write the app needs; report BLOCKED with what you find rather than removing `securityContext` fields on your own judgment.

- [ ] **Step 4: Verify pods are running and ready**

Run: `kubectl --context notiflex-gke -n notiflex get pods -l app=notiflex-api`
Expected: 2 pods, `STATUS` = `Running`, `READY` = `1/1` each.

- [ ] **Step 5: Verify no crashes/permission errors in logs**

Run: `kubectl --context notiflex-gke -n notiflex logs -l app=notiflex-api --tail=50`
Expected: uvicorn startup log lines (e.g. `Uvicorn running on http://0.0.0.0:8080`), no `PermissionError` or traceback output.

- [ ] **Step 6: Verify `POD_NAME` is injected correctly (not falling back to `"local"`)**

Run: `kubectl --context notiflex-gke -n notiflex exec deploy/notiflex-api -- python -c "import os; print(os.environ.get('POD_NAME'))"`
Expected: prints an actual pod name like `notiflex-api-<hash>-<hash>` — NOT `None` and not `local`.

- [ ] **Step 7: Commit**

```bash
git add k8s/smb/deployment.yaml
git commit -m "Add Deployment manifest for notiflex-api"
```

---

### Task 3: Service manifest

**Files:**
- Create: `k8s/smb/service.yaml`

**Interfaces:**
- Consumes: Deployment's pod label `app: notiflex-api` (Task 2).

- [ ] **Step 1: Create `k8s/smb/service.yaml`**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: notiflex-api
  namespace: notiflex
spec:
  type: ClusterIP
  selector:
    app: notiflex-api
  ports:
    - port: 8080
      targetPort: 8080
```

- [ ] **Step 2: Apply it**

Run:
```bash
export KUBECONFIG="$HOME/.kube/config:$HOME/.kube/config-personal"
kubectl --context notiflex-gke apply -f k8s/smb/service.yaml
```
Expected: `service/notiflex-api created`.

- [ ] **Step 3: Verify the Service found the pods**

Run: `kubectl --context notiflex-gke -n notiflex get endpoints notiflex-api`
Expected: `ENDPOINTS` column lists 2 IP:8080 pairs (one per pod). If it shows `<none>`, the Service's `selector` doesn't match the Deployment's pod labels — report BLOCKED with the output of `kubectl --context notiflex-gke -n notiflex get pods --show-labels` rather than guessing at a fix.

- [ ] **Step 4: Verify end-to-end connectivity via port-forward**

Run:
```bash
export KUBECONFIG="$HOME/.kube/config:$HOME/.kube/config-personal"
kubectl --context notiflex-gke -n notiflex port-forward svc/notiflex-api 8080:8080 &
PF_PID=$!
sleep 2
curl -s localhost:8080/health
curl -s localhost:8080/id
kill $PF_PID
```
Expected: `/health` returns `{"status":"ok"}`; `/id` returns `{"id":1,"pod":"notiflex-api-<hash>-<hash>"}` — a real pod name in the `pod` field, not `"local"` (confirms the Downward API wiring from Task 2 works end-to-end through the Service).

- [ ] **Step 5: Commit**

```bash
git add k8s/smb/service.yaml
git commit -m "Add Service manifest for notiflex-api"
```
