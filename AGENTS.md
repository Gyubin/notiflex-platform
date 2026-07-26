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
- **Cluster**: `notiflex-cluster`, four Spot node pools — `default-pool` (e2-medium ×2, pd-balanced 30 GB) for the shared platform, `api-pool` (e2-medium ×1) for `notiflex-api`, `worker-pool` (e2-standard-2 ×1) for Kafka, and `ops-pool` (e2-small ×1) for Tempo and CronJobs. Every pool sets `--workload-metadata=GKE_METADATA`; the ch7 pools use `pd-standard` 50 GB disks to stay off the regional SSD quota
- **kubectl context**: `notiflex-gke`
- **Application namespace**: `notiflex`
- **`ops-pool` is nearly full.** It is an e2-small with 940m CPU and 1391Mi allocatable, and the
  system DaemonSets alone reserve 56% of the CPU and 75% of the memory. Check `kubectl top` and the
  node's `Allocated resources` before scheduling anything else there.
- **Gateway API**: enabled on the standard channel

The GKE kubeconfig is separated from the company EKS configuration: personal GKE data lives in
`~/.kube/config-personal`, while `~/.zshrc` merges it with `~/.kube/config` through `KUBECONFIG`.
On another computer, recreate the personal file from the original GKE context before using this
repository.

## Repository Layout

- `app/`: Python source, tests, Dockerfile, `pyproject.toml`, and `uv.lock`
- `k8s/smb/`: SMB tenant — Rollout, traffic, monitoring-discovery, and secret-mount manifests
- `k8s/enterprise/`: Enterprise tenant — Rollout, Service, ServiceAccount, and SecretProviderClass
- `k8s/kafka/`: Strimzi `Kafka`, `KafkaNodePool`, and `KafkaTopic` custom resources
- `k8s/monitoring/`: Grafana datasource/dashboard ConfigMaps and the PrometheusRule
- `helm-values/`: Helm values for kube-prometheus-stack, Loki, Fluent Bit, Valkey, Strimzi, and Tempo
- `claude-context/architecture.md`: a one-page snapshot of how the system currently works — topology,
  component flow, pipeline, observability, namespaces. Read it to get oriented; update it when the
  shape of the system changes. It holds no reasoning: why a thing was chosen belongs in
  `docs/architecture-decisions.md`, and what happened along the way belongs in `JOURNEY.md`. The
  directory name comes from the textbook and is kept for compatibility.
- `ONBOARDING.md`: the entry point for someone new to the repository — cluster layout, access,
  deployment flow, a Q&A section, and the limits worth knowing before touching anything. It restates
  what the other documents own rather than holding anything of its own, so refresh it whenever the
  architecture snapshot changes.
- `command-guardrails/`: step-by-step procedures for the operations that are hard to undo — deleting
  a Kafka topic, running a CronJob by hand, removing a tenant namespace. Read the matching file
  before performing one of these, and add a file in the same three-part shape when a new hazardous
  operation appears. These are permanent; do not delete them after use.
- `.github/workflows/`: CI pipeline
- `argocd/root-app.yaml`: the App of Apps root; apply it by hand, and it manages everything else
- `argocd/apps/`: one Application per managed path. Adding a file here is how a new app is
  registered — `root-app` watches the directory recursively. Keep `argocd/` itself free of other
  Application manifests so the root does not sync itself.

## Paused Cluster: Resume Only for Requested Work

Between chapters every node pool is scaled to zero to save cost, automated sync is disabled on all
five ArgoCD applications, and the healthcheck CronJob is suspended. Documentation-only work must not
resume the cluster. Check `kubectl --context notiflex-gke get nodes` before assuming either state —
the cluster is sometimes already running.

**`root-app` comes first when disabling sync and last when re-enabling it.** It manages the child
Application resources, `syncPolicy` included, so a child whose automation you switched off gets it
restored from Git while the root is still self-healing.

**Wait until every resized pool's nodes are `Ready` before re-enabling automated sync.** The pools
come back one at a time, three to five minutes apart, while the Pod objects survive the pause as
`Pending` and get scheduled the instant their node appears. Turn sync on early and `notiflex-api`
starts on `api-pool` before the Kafka broker exists on `worker-pool`; both it and Strimzi's
`entity-operator` then crash-loop for about ten minutes before recovering on their own. Nothing
breaks, but the restarts are avoidable.

To resume, explain the impact first, then run this, resizing only the pools the work needs
(`default-pool` 2, `api-pool` 1, `worker-pool` 1, `ops-pool` 1):

```bash
gcloud container clusters resize notiflex-cluster --node-pool default-pool \
  --num-nodes 2 --zone asia-northeast3-a \
  --project project-b3c5c78c-8a5c-4e47-9fe --quiet

# children first, root last
for app in notiflex-smb notiflex-enterprise notiflex-monitoring notiflex-kafka root-app; do
  kubectl --context notiflex-gke patch application "$app" -n argocd --type merge \
    -p '{"spec":{"syncPolicy":{"automated":{"prune":true,"selfHeal":true}}}}'
  kubectl --context notiflex-gke annotate application "$app" -n argocd \
    argocd.argoproj.io/refresh=hard --overwrite
done

kubectl --context notiflex-gke patch cronjob notiflex-healthcheck -n notiflex \
  -p '{"spec":{"suspend":false}}'
```

To pause it again, disable automated sync, then suspend the CronJob and scale both tenants' Rollouts
to zero, then resize the pools. Do not reverse that order: ArgoCD self-heal and the `notiflex-api`
PDB (`minAvailable: 1`) can otherwise block node draining. Leaving the CronJob running would keep
firing failing jobs at an API that is no longer there.

```bash
# root first, then the children
for app in root-app notiflex-smb notiflex-enterprise notiflex-monitoring notiflex-kafka; do
  kubectl --context notiflex-gke patch application "$app" -n argocd --type merge \
    -p '{"spec":{"syncPolicy":{"automated":null}}}'
done

kubectl --context notiflex-gke patch cronjob notiflex-healthcheck -n notiflex \
  -p '{"spec":{"suspend":true}}'

kubectl --context notiflex-gke scale rollout.argoproj.io/notiflex-api -n notiflex --replicas=0
kubectl --context notiflex-gke scale rollout.argoproj.io/notiflex-api -n enterprise --replicas=0

for pool in api-pool worker-pool ops-pool default-pool; do
  gcloud container clusters resize notiflex-cluster --node-pool "$pool" --num-nodes 0 \
    --zone asia-northeast3-a --project project-b3c5c78c-8a5c-4e47-9fe --quiet
done
```

Pausing does not touch the PVCs. Kafka's 5Gi, Loki's 2Gi, and Valkey's 1Gi survive, so the counter,
the logs, and any unread messages are still there on resume. That is a few cents a month and the
reason a paused cluster is not a free one.

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
- The Rollout runs two replicas on `api-pool` through the
  `cloud.google.com/gke-nodepool: api-pool` nodeSelector. Use that label key in every manifest;
  a custom key such as `role` or `workload` leaves pods permanently Pending.
- With only two replicas, intermediate pod-based weights are still coarse. Production traffic
  percentages require more replicas or an integrated traffic router and metric analysis.
- The `notiflex-api` PodDisruptionBudget is back to `minAvailable: 1`. Because `api-pool` has a
  single node, lower it temporarily when that node must be drained.

## Tenants

- `notiflex` is the SMB tenant and `enterprise` is the Enterprise tenant. Each has its own
  namespace, Rollout, Service, and ServiceAccount, and each is a separate ArgoCD Application.
- Both tenants read the Valkey password from the same Secret Manager entry through their own
  `SecretProviderClass`. A tenant's Kubernetes ServiceAccount must be bound to the
  `notiflex-secrets` GCP service account as `PROJECT.svc.id.goog[<namespace>/notiflex-api]` before
  its pods can start. Adding a tenant means adding that binding too.
- Valkey itself lives only in `notiflex`; other tenants reach it at
  `valkey-primary.notiflex.svc.cluster.local:6379`. The namespaces separate compute, not data —
  every tenant currently shares one `/id` counter. Per-tenant key prefixes or separate instances
  are still open work.
- Kafka is shared the same way. Tenants publish to one `notifications` topic under their own consumer
  group, so a tenant reads its own messages *and* everyone else's — measured, not assumed. The tenant
  travels in the message key and payload, which distinguishes senders but isolates nothing. Real
  isolation needs per-tenant topics or Kafka ACLs.
- Keying by tenant name also pins a tenant's messages to one partition, so extra replicas do not add
  parallelism within a tenant. That is the price of per-tenant ordering.
- Both tenants run the same image, and CI bumps both rollout manifests on release. Deploying tenants
  at different versions means splitting that step in `.github/workflows/ci.yaml` first.

## Messaging and Scheduled Work

- Kafka runs in the `kafka` namespace: the Strimzi operator (Helm, `helm-values/strimzi.yaml`) plus a
  single KRaft broker declared in `k8s/kafka/` and synced by the `notiflex-kafka` Application. The
  broker doubles as controller. Reach it at
  `notiflex-kafka-kafka-bootstrap.kafka.svc.cluster.local:9092`.
- Strimzi's pod template has no `nodeSelector` field. Pin its pods with `nodeAffinity` on the same
  `cloud.google.com/gke-nodepool` label the other manifests use.
- Only the Kafka versions listed in the operator's `STRIMZI_KAFKA_IMAGES` will start. Check that list
  before changing `spec.kafka.version`; an unsupported value fails the cluster, it does not warn.
- `/id` publishes an event and a consumer in the same pod reads it back. Both are optional: without
  `KAFKA_BROKER` the app starts with messaging off, which is how the tests and local runs work.
- `notiflex-healthcheck` (`k8s/smb/healthcheck-cronjob.yaml`) curls `/health` through the Service DNS
  name every five minutes from `ops-pool`. The Service listens on 8080, not 80.

## Observability

- The `monitoring` namespace contains Helm-installed kube-prometheus-stack, Loki, and Fluent Bit.
  Helm still owns those releases, but since ch7.3 the manifests in `k8s/monitoring/` are ArgoCD's
  through the `notiflex-monitoring` Application, so edit them in Git rather than with `kubectl`.
- Prometheus scrapes the FastAPI instrumentator's `/metrics` endpoint through
  `k8s/smb/servicemonitor.yaml` (`release: kube-prometheus`). Loki runs as SingleBinary and Fluent Bit
  runs as a DaemonSet; Grafana has a non-default Loki datasource and LogQL uses `{namespace="notiflex"}`.
  The `pod-restart-alert` PrometheusRule routes only to the default null Alertmanager receiver.
- Tempo (Helm, `helm-values/tempo.yaml`) collects traces over OTLP gRPC on 4317 and is queried over
  HTTP on 3200; those two ports are easy to mix up. Its Grafana datasource is
  `k8s/monitoring/tempo-datasource.yaml` with `uid: tempo` pinned, because dashboards reference
  datasources by uid and an unpinned one is regenerated on every reprovision. Exactly one datasource
  may carry `isDefault: true`, and Prometheus already does — a second one crashes Grafana at startup.
- The app traces every request except `/health` and `/metrics`. Probe traffic would otherwise bury
  real requests in Tempo's search results. Traces carry the tenant in `service.namespace`.
- Access Grafana with:

  ```bash
  kubectl --context notiflex-gke -n monitoring port-forward svc/kube-prometheus-grafana 3000:80
  ```

- Prometheus, Grafana, Alertmanager, operator, and Loki CPU requests were reduced to 5m before the
  ch6 CSI DaemonSet was enabled. Two e2-medium nodes were CPU-saturated at that point; ch7.2 moved
  `notiflex-api` onto its own `api-pool`, which freed default-pool for the platform components.
  Validate actual usage with `kubectl top` before adding more workloads.

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
