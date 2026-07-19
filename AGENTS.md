# notiflex-platform Agent Guide

This is the canonical instruction file for every coding agent working in this repository.
`CLAUDE.md` is a Claude Code compatibility entry point and must defer to this file.
Keep textbook discussions and completion reports in Korean.

## Project and Textbook Context

- notiflex-platform is a Python B2B notification SaaS platform used to practice Kubernetes operations.
- The backend is deployed to Kubernetes; container images are stored in GCP Artifact Registry.
- The textbook uses Go. Translate its code and configuration to the Python implementation here; do not copy Go artifacts unchanged.
- When the sibling workspace layout is available, read `../reference/Book_GitAIOps/AGENTS.md` for the active agent's adapter and `../reference/Book_GitAIOps/CLAUDE.md` for chapter routing, guardrails, and result templates.
- Read `JOURNEY.md` before entering a subchapter. For every chapter task, read the matching guardrail, check prerequisites, implement the requested work, verify against its result template, then update `JOURNEY.md`.
- This file overrides the workspace router and textbook when they conflict. `reference/` is read-only; all work products belong in this repository. A standalone clone can be developed normally, but cannot run the textbook workflow without the sibling harness.
- Bare textbook examples never override this guide: use Python adaptations, the current GCP values, and `--context notiflex-gke` on every `kubectl` command.

## Infrastructure

- **Orchestration**: GKE Standard (Zonal)
- **CI/CD**: GitHub Actions + ArgoCD
- **Project ID**: `project-b3c5c78c-8a5c-4e47-9fe`
- **Project name**: `gyubin-gitaiops-project`
- **Region / zone**: `asia-northeast3` / `asia-northeast3-a`
- **Artifact Registry**: `asia-northeast3-docker.pkg.dev/project-b3c5c78c-8a5c-4e47-9fe/notiflex-platform`
- **Cluster**: `notiflex-cluster`, default-pool e2-medium Spot nodes with 30 GB disks; currently scaled to zero, resume with 3 nodes until ch7 adds capacity
- **kubectl context**: `notiflex-gke`
- **Application namespace**: `notiflex`
- **Gateway API**: enabled on the standard channel

The GKE kubeconfig is separated from the company EKS configuration: personal GKE data lives in
`~/.kube/config-personal`, while `~/.zshrc` merges it with `~/.kube/config` through `KUBECONFIG`.
On another computer, recreate the personal file from the original GKE context before using this
repository.

## Repository Layout

- `app/`: Python source, tests, Dockerfile, `pyproject.toml`, and `uv.lock`
- `k8s/smb/`: ArgoCD-managed Rollout, traffic, monitoring-discovery, and secret-mount manifests
- `k8s/monitoring/`: monitoring manifests applied directly with `kubectl apply`
- `helm-values/`: Helm values for kube-prometheus-stack, Loki, Fluent Bit, and Valkey
- `.github/workflows/`: CI pipeline
- `argocd/`: ArgoCD Application definition

## Paused Cluster: Resume Only for Requested Work

The default node pool is intentionally scaled to zero to save cost, and the `notiflex-smb`
ArgoCD application's automated sync is disabled. Documentation-only work must not resume the
cluster. Before a requested chapter needs a live cluster, explain the impact and perform the
following recovery sequence:

```bash
gcloud container clusters resize notiflex-cluster --node-pool default-pool \
  --num-nodes 3 --zone asia-northeast3-a \
  --project project-b3c5c78c-8a5c-4e47-9fe --quiet

kubectl --context notiflex-gke patch application notiflex-smb -n argocd --type merge \
  -p '{"spec":{"syncPolicy":{"automated":{"prune":true,"selfHeal":true}}}}'

kubectl --context notiflex-gke annotate application notiflex-smb -n argocd \
  argocd.argoproj.io/refresh=hard --overwrite
```

To pause it again, first disable automated sync, then scale the `notiflex-api` Rollout to zero, then resize
the node pool to zero. Do not reverse that order: ArgoCD self-heal and the PDB can otherwise block
node draining.

```bash
kubectl --context notiflex-gke patch application notiflex-smb -n argocd --type merge \
  -p '{"spec":{"syncPolicy":{"automated":null}}}'

kubectl --context notiflex-gke scale rollout.argoproj.io/notiflex-api -n notiflex --replicas=0

gcloud container clusters resize notiflex-cluster --node-pool default-pool \
  --num-nodes 0 --zone asia-northeast3-a \
  --project project-b3c5c78c-8a5c-4e47-9fe --quiet
```

## Development, Build, and Delivery

- Use `uv` for local dependencies: `cd app && uv sync && uv run pytest`.
- Python is fixed to 3.13 to match `python:3.13-slim`; `requirements*.txt` is retired.
- `app/Dockerfile` is a multistage, non-root (`appuser`) image built with `uv sync --frozen`.
  It receives `APP_VERSION` as a build argument so `/version` can report the release tag.
- Normal builds run in GitHub Actions. For local one-off or debugging builds, use Cloud Build because
  the local Mac is arm64 while GKE nodes are amd64:

  ```bash
  gcloud builds submit app/ \
    --tag=asia-northeast3-docker.pkg.dev/project-b3c5c78c-8a5c-4e47-9fe/notiflex-platform/notiflex-api:<version> \
    --service-account=projects/project-b3c5c78c-8a5c-4e47-9fe/serviceAccounts/notiflex-cloudbuild@project-b3c5c78c-8a5c-4e47-9fe.iam.gserviceaccount.com \
    --default-buckets-behavior=REGIONAL_USER_OWNED_BUCKET
  ```

- Release delivery starts with `git tag vX.Y.Z && git push origin vX.Y.Z`. CI tests, builds, pushes,
  updates `k8s/smb/rollout.yaml`, and pushes to `main`; when automated sync is enabled, ArgoCD then
  deploys the change.
- Workload Identity Federation is required for CI. Do not create or store service-account keys.
- Git tags are the single source for image tags and the `APP_VERSION` reported by `/version`.
- `app/.gcloudignore` excludes virtual environments and Python cache directories from Cloud Build uploads.

## Application Data and Secrets

- Valkey 9.1.0 runs in standalone mode from the Bitnami chart with a 1Gi PVC and password
  authentication. Its tracked inputs live in `helm-values/valkey.yaml`; Helm owns the generated
  Kubernetes Secret and it must not be committed.
- The API uses Valkey `INCR` for the shared `/id` counter. `VALKEY_ADDR` points to
  `valkey-primary.notiflex.svc.cluster.local:6379`.
- GCP Secret Manager is the source of truth for the Valkey password. The GKE managed Secret Manager
  CSI Driver mounts it read-only at `/mnt/secrets/valkey-password` through
  `k8s/smb/secretproviderclass.yaml`.
- The `notiflex-api` Kubernetes ServiceAccount uses Workload Identity to impersonate the dedicated
  `notiflex-secrets` GCP Service Account. Do not replace this with a service-account key or copy the
  password into Git.

## Progressive Delivery

- `notiflex-api` is an Argo Rollouts `Rollout`, not a Deployment. CI updates
  `k8s/smb/rollout.yaml` after building each immutable release tag.
- The current strategy is Canary with stable Service `notiflex-api`, canary Service
  `notiflex-api-preview`, weights 20/50/80, and a 30-second pause after each weight.
- Preserve `notiflex-api-preview`; deleting it makes the Rollout specification invalid.
- With the current single desired replica, intermediate pod-based weights are coarse. Production
  traffic percentages require more replicas or an integrated traffic router and metric analysis.

## Observability

- The `monitoring` namespace contains Helm-installed kube-prometheus-stack, Loki, and Fluent Bit;
  it is not ArgoCD-managed.
- Prometheus scrapes the FastAPI instrumentator's `/metrics` endpoint through
  `k8s/smb/servicemonitor.yaml` (`release: kube-prometheus`). Loki runs as SingleBinary and Fluent Bit
  runs as a DaemonSet; Grafana has a non-default Loki datasource and LogQL uses `{namespace="notiflex"}`.
  The `pod-restart-alert` PrometheusRule routes only to the default null Alertmanager receiver.
- Access Grafana with:

  ```bash
  kubectl --context notiflex-gke -n monitoring port-forward svc/kube-prometheus-grafana 3000:80
  ```

- Prometheus, Grafana, Alertmanager, operator, and Loki CPU requests were reduced to 5m before the
  ch6 CSI DaemonSet was enabled. Even after that reduction, two e2-medium nodes were CPU-saturated;
  use three default-pool nodes until ch7 adds capacity and validate actual usage with `kubectl top`.

## Operating Rules

1. At the start of every session, run `kubectl config current-context`. If it is not
   `notiflex-gke`, run `kubectl config use-context notiflex-gke` and confirm the result
   before any Kubernetes command. This is a safeguard against the company AWS context;
   every Kubernetes command must still include `--context notiflex-gke`.
2. Inspect current state before running commands.
3. Read existing files before editing them.
4. Diagnose errors and present the resolution before proceeding.
5. Declare the `notiflex` namespace in application manifests.
6. Every `kubectl` command must include `--context notiflex-gke`.
7. Explain the impact before creating or deleting resources.
8. Never use `latest` or reuse a deployed image tag; every release needs a new explicit version.
9. Never hardcode credentials, keys, tokens, or passwords; use environment variables, GitHub Secrets,
   or Secret Manager.
10. Do not commit build output, binaries, `dist/`, or `bin/`.
11. Reference Secret Manager or Kubernetes Secret resources instead of embedding actual secret values in manifests.
12. Write blog drafts only in the workspace-sibling `../for-blog/` directory, outside this repository; blog content must never be added to a commit or retained in this repository's Git history.

## Documentation Updates

Treat `/update-docs`, `update docs`, `문서 갱신`, and a chapter-completion documentation request as
the procedure in `docs/agent-workflows/update-docs.md`. The legacy `claude-context/` name, when
introduced by the textbook, is a required compatibility artifact rather than an agent runtime
dependency.

## Codex and Claude-Specific Behavior

From the workspace root, start an infrastructure-capable Codex session with:

```bash
codex -C notiflex-platform -s danger-full-access -a on-request
```

When already in the repository, omit `-C notiflex-platform`. For read-only investigation, use
`-s read-only`. Codex must use its own sandbox and approval model;
do not create `.claude/settings.local.json` as a substitute. The textbook's statusline and
`.claude/settings.local.json` exercises should be explained as Claude-only, with a non-destructive
Codex configuration check in their place.
