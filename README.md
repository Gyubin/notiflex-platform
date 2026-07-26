# notiflex-platform

B2B 알림 SaaS 플랫폼을 가정한 Kubernetes 운영환경 구축 실습 프로젝트입니다. FastAPI 백엔드를 GKE에 배포하고, 이미지 빌드부터 GitOps 배포·관측 가능성·공유 캐시·외부 시크릿·점진 배포·멀티테넌시·이벤트 드리븐 처리까지 단계적으로 구성합니다.

처음 보신다면 [ONBOARDING.md](ONBOARDING.md)부터 읽으세요.

## 현재 상태

- [x] FastAPI 앱 (`/health`, `/version`, `/id`, `/notifications`, `/metrics`) + pytest 테스트
- [x] Dockerfile (multi-stage, non-root, `uv sync --frozen`) — CI가 빌드/push
- [x] GitOps 배포 (ArgoCD **App of Apps** — `root-app` + Application 4개)
- [x] CI/CD (GitHub Actions 릴리스 태그 트리거 + WIF 키리스 인증 → ArgoCD 자동 배포)
- [x] 관측 가능성 — 메트릭(Prometheus+Grafana), 로그(Loki+Fluent Bit), 알림(PrometheusRule+Alertmanager), **트레이스(Tempo+OpenTelemetry)**
- [x] Gateway API 외부 노출 (`Gateway` + `HTTPRoute` + `HealthCheckPolicy`)
- [x] 공유 상태 — Valkey 9.1.0 standalone + 1Gi PVC, `/id` 전역 원자 카운터
- [x] 시크릿 관리 — Workload Identity + GKE Secret Manager CSI 읽기 전용 파일 마운트
- [x] 점진 배포 — Argo Rollouts Canary 20% → 50% → 80% → 100%, 각 30초 pause
- [x] **역할별 노드풀** — api / worker / ops 분리 (전부 Spot)
- [x] **멀티테넌시** — SMB(`notiflex`) + Enterprise(`enterprise`) 네임스페이스 분리
- [x] **이벤트 드리븐** — Strimzi Kafka(KRaft 단일 브로커), `/id`가 `notifications` 토픽에 발행
- [x] **주기 작업** — `notiflex-healthcheck` CronJob이 5분마다 `/health` 확인

> 배포 이미지: `notiflex-api:v0.4.0` · 앱 버전은 git 태그가 단일 소스(`/version`으로 확인).
> **비용 절감을 위해 평소에는 노드풀 0, ArgoCD auto-sync 비활성, CronJob suspend 상태입니다.**
> 중단·재개 절차는 [AGENTS.md](AGENTS.md)의 "Paused Cluster"를 그대로 따르세요.

## 구성

| 항목 | 값 |
|---|---|
| 클러스터 | GKE Standard (Zonal) `notiflex-cluster`, `asia-northeast3-a`, Kubernetes 1.35.5-gke.1241004 |
| 노드풀 | `default-pool` e2-medium ×2 / `api-pool` e2-medium ×1 / `worker-pool` e2-standard-2 ×1 / `ops-pool` e2-small ×1 — 전부 Spot |
| 네임스페이스 | `notiflex`(SMB), `enterprise`, `kafka`, `monitoring`, `argocd`, `argo-rollouts` |
| 이미지 저장소 | `asia-northeast3-docker.pkg.dev/project-b3c5c78c-8a5c-4e47-9fe/notiflex-platform/<이미지명>:<태그>` |
| kubectl context | `notiflex-gke` (**모든 명령에 `--context notiflex-gke` 필수**) |
| 외부 IP | `35.216.8.57` (Regional external Gateway) |
| GitOps | ArgoCD v3.4.5, App of Apps — `root-app`이 `argocd/apps/`를 감시 |
| 배포 전략 | Argo Rollouts v1.9.1 Canary, 20/50/80%와 각 30초 pause |
| 데이터 | Valkey 9.1.0 standalone(1Gi PVC), Kafka 4.3.0(Strimzi 1.1.0, 5Gi PVC) |
| 시크릿 | GKE Secret Manager CSI + Workload Identity, `/mnt/secrets/valkey-password` |

## 디렉토리 구조

```
app/                   # FastAPI 소스, 테스트, Dockerfile, pyproject.toml + uv.lock
k8s/
  smb/                 # SMB 테넌트 — Rollout, Service(stable/preview), Gateway, HTTPRoute,
                       #   PDB, ServiceMonitor, SecretProviderClass, 헬스체크 CronJob
  enterprise/          # Enterprise 테넌트 — Rollout, Service, ServiceAccount, SecretProviderClass
  monitoring/          # Grafana 데이터소스·대시보드 ConfigMap, PrometheusRule
  kafka/               # Strimzi Kafka / KafkaNodePool / KafkaTopic CR
helm-values/           # Helm values (kube-prometheus-stack, Loki, Fluent Bit, Valkey, Strimzi, Tempo)
argocd/
  root-app.yaml        # App of Apps 루트 — 유일하게 손으로 apply하는 파일
  apps/                # Application 4개. 여기에 YAML을 넣으면 새 앱이 등록된다
.github/workflows/     # CI 파이프라인 (ci.yaml)
command-guardrails/    # 되돌리기 어려운 작업의 절차서 (Kafka 토픽 삭제, CronJob 수동 실행, 테넌트 삭제)
claude-context/        # 지금의 아키텍처 스냅샷
docs/                  # ADR 16건, 에이전트 공통 작업 절차
AGENTS.md              # 모든 코딩 에이전트의 정본 규칙
CLAUDE.md              # Claude Code 호환 진입점 (AGENTS.md로 연결)
ONBOARDING.md          # 신규 합류자용 안내
JOURNEY.md             # 진행 기록 + 도구 선택 이유 + 트러블슈팅 이력
```

## API

| 엔드포인트 | 설명 |
|---|---|
| `GET /health` | 상태 확인 (readiness/liveness probe, CronJob, Gateway HealthCheckPolicy에서 사용) |
| `GET /version` | 앱 버전(git 태그) + 런타임(python 버전) + Pod 이름 |
| `GET /id` | Valkey `INCR`로 만든 전역 ID + Pod 이름 + 테넌트 + Kafka 발행 여부 |
| `GET /notifications` | 이 Pod의 Kafka Consumer가 받은 메시지 |
| `GET /metrics` | Prometheus 메트릭 (`http_requests_total` 등). ServiceMonitor가 스크레이프 |

`/health`와 `/metrics`는 트레이싱에서 제외합니다 — 프로브 트래픽이 Tempo 검색 결과를 뒤덮습니다.

## 로컬 개발 (uv)

로컬 의존성/가상환경은 **uv**로 관리합니다 (`app/pyproject.toml` + `app/uv.lock`, Python 3.13 고정 — 이미지 베이스와 정합).

```bash
cd app
uv sync                             # 의존성 설치 (가상환경 자동 생성)
uv run pytest                       # 테스트
uv run uvicorn main:app --port 8080 # 로컬 실행
```

`KAFKA_BROKER`와 `VALKEY_ADDR`가 없으면 메시징·캐시 없이 뜹니다. 테스트와 로컬 실행이 이 경로입니다.

## 이미지 빌드

평상시 빌드는 **CI(GitHub Actions)가 담당**합니다. 아래 Cloud Build는 로컬 일회성/디버그용 fallback입니다.

로컬 Mac(arm64)과 GKE 노드(amd64)의 아키텍처가 달라 로컬 docker build 대신 Cloud Build(GCP 서버, amd64)를 사용합니다. 한 번 배포에 쓴 태그는 재사용하지 않고 릴리스마다 새 버전으로 올립니다.

```bash
gcloud builds submit app/ \
  --tag=asia-northeast3-docker.pkg.dev/project-b3c5c78c-8a5c-4e47-9fe/notiflex-platform/notiflex-api:<버전> \
  --service-account=projects/project-b3c5c78c-8a5c-4e47-9fe/serviceAccounts/notiflex-cloudbuild@project-b3c5c78c-8a5c-4e47-9fe.iam.gserviceaccount.com \
  --default-buckets-behavior=REGIONAL_USER_OWNED_BUCKET
```

## CI/CD (릴리스 주도)

릴리스 태그를 밀면 CI가 빌드·태그 갱신까지 하고, ArgoCD가 이를 감지해 자동 배포합니다. **main에 코드만 push하면 배포되지 않습니다.**

```bash
git tag vX.Y.Z && git push origin vX.Y.Z
```

- **CI** (`.github/workflows/ci.yaml`): uv 테스트 → `docker build`(amd64) → Artifact Registry push → `k8s/smb/rollout.yaml`과 `k8s/enterprise/rollout.yaml`의 이미지 태그 갱신 → main commit/push
- **CD**: ArgoCD가 변경을 감지하면 Argo Rollouts가 Canary 단계(20/50/80/100%)를 진행
- **인증**: Workload Identity Federation(키리스). 조직 정책으로 SA 키 생성이 금지되어 GitHub OIDC로 `notiflex-ci` SA를 impersonate — 저장 키 없음
- git 태그가 곧 이미지 태그이자 `APP_VERSION`(`/version` 값)의 단일 소스

> 태그를 민 뒤 문서를 push하면 CI 커밋 때문에 non-fast-forward로 거절됩니다.
> `git fetch && git rebase --autostash origin/main`으로 재배치하세요. force push는 쓰지 않습니다.

### ArgoCD 애플리케이션 (App of Apps)

```
root-app  (수동 apply, argocd/apps/ 를 recurse 감시)
├── notiflex-monitoring   wave 1  → k8s/monitoring/   → monitoring
├── notiflex-kafka        wave 1  → k8s/kafka/        → kafka
├── notiflex-smb          wave 2  → k8s/smb/          → notiflex
└── notiflex-enterprise   wave 2  → k8s/enterprise/   → enterprise
```

`argocd/` 최상위에는 `root-app.yaml` 말고 다른 Application을 두지 않습니다 (루트가 자기 자신을 sync하게 됩니다).

Helm이 소유해 GitOps 밖에 있는 것: kube-prometheus-stack, Loki, Fluent Bit, Valkey, Strimzi operator, Tempo. values는 `helm-values/`에 커밋돼 있지만 릴리스 자체는 Helm이 관리합니다.

## 배포 확인

```bash
kubectl argo rollouts get rollout notiflex-api -n notiflex --context notiflex-gke --watch
kubectl --context notiflex-gke get pods -n notiflex
kubectl --context notiflex-gke get app -n argocd
```

> `kubectl` 플러그인은 플래그를 **플러그인 이름 뒤에만** 받습니다.
> `kubectl --context notiflex-gke argo rollouts ...`는 실패합니다.

정상 릴리스는 수동 `kubectl apply`가 아니라 릴리스 태그와 GitOps 경로를 사용합니다. Gateway가 준비된 동안에는 외부 IP `35.216.8.57`에서 API를 호출할 수 있습니다.

## 멀티테넌시

`notiflex`(SMB)와 `enterprise` 두 테넌트가 각자 네임스페이스·Rollout·Service·ServiceAccount를 갖고, 각각 별도 ArgoCD Application으로 배포됩니다. 두 테넌트는 같은 이미지를 쓰고 CI가 두 매니페스트를 함께 갱신합니다.

**네임스페이스가 가른 것은 컴퓨트뿐입니다.** 두 테넌트가 같은 Valkey 카운터를 쓰고, 같은 `notifications` 토픽을 Consumer Group만 나눠 읽습니다. 그룹을 나눈 건 "각자 전량을 독립적으로 읽는다"는 뜻이라 enterprise가 smb의 메시지까지 전부 받습니다(측정으로 확인). 진짜 격리는 테넌트별 토픽이나 Kafka ACL, 테넌트별 키 접두사나 별도 Valkey 인스턴스가 필요합니다.

테넌트를 추가할 때는 GCP 쪽 Workload Identity 바인딩(`...svc.id.goog[<namespace>/notiflex-api]`)도 함께 추가해야 합니다. 빠뜨리면 Pod은 뜨는데 Secret Manager만 못 읽습니다.

## 공유 상태와 시크릿

- `helm-values/valkey.yaml`로 Valkey standalone을 운영하며, 1Gi PVC와 비밀번호 인증을 사용합니다.
- API는 `valkey-primary.notiflex.svc.cluster.local:6379`에 연결하고 `/id`에서 `notiflex:id`를 원자적으로 증가시킵니다.
- Valkey 비밀번호의 원본은 GCP Secret Manager에 있으며 Git이나 환경변수에 복제하지 않습니다.
- Kubernetes ServiceAccount `notiflex-api`가 Workload Identity로 전용 GCP Service Account를 사용합니다.
- GKE 관리형 CSI Driver가 Secret을 `/mnt/secrets/valkey-password`에 읽기 전용으로 마운트합니다.

## 메시징

Strimzi operator(Helm)가 관리하는 KRaft 단일 브로커가 `kafka` 네임스페이스에 있습니다. 브로커가 controller를 겸하고, `notifications` 토픽은 3파티션입니다.

`/id`가 Valkey `INCR` 후 이벤트를 발행하고, 같은 Pod의 백그라운드 Consumer가 이를 받습니다. `KAFKA_BROKER`가 없으면 메시징이 꺼진 채 기동합니다.

> Kafka 버전을 바꾸기 전에 operator가 지원하는 목록을 먼저 확인하세요.
> `helm template ... | grep STRIMZI_KAFKA_IMAGES` — 지원하지 않는 값은 경고 없이 클러스터를 죽입니다.

## 관측 가능성

`monitoring` 네임스페이스에 Helm으로 구축했습니다 (values는 `helm-values/`, 매니페스트는 `k8s/monitoring/`이며 ch7.3부터 ArgoCD가 관리).

| 도구 | 답하는 질문 | 사용 |
|---|---|---|
| Prometheus | 얼마나 · 몇 번 · 언제부터 느려졌나 | `/metrics` 스크레이프 (ServiceMonitor, `release: kube-prometheus`) |
| Loki + Fluent Bit | 그때 무슨 일이 있었나 | Grafana LogQL `{namespace="notiflex"}` |
| Tempo | 요청 하나가 어디에 시간을 썼나 | OTLP gRPC 4317 수집 / HTTP 3200 조회, `uid: tempo` |
| Alertmanager | 문제가 났을 때 알려주기 | `pod-restart-alert` PrometheusRule. **외부 채널 미설정** |

```bash
# Grafana 접속
kubectl --context notiflex-gke -n monitoring port-forward svc/kube-prometheus-grafana 3000:80
# http://localhost:3000 (admin, 비밀번호는 kube-prometheus-grafana Secret)
```

> 기본 데이터소스(`isDefault: true`)는 Prometheus 하나뿐이어야 합니다 — 둘 이상이면 Grafana가 기동에 실패합니다.
> 데이터소스 `uid`는 반드시 고정하세요. 비워두면 Grafana가 임의 값을 만들고 대시보드가 재프로비저닝 때 깨집니다.

## 알려진 한계

- 테넌트 격리가 컴퓨트에만 적용됩니다 (위 "멀티테넌시" 참조)
- 메시지 키가 테넌트 이름이라 한 테넌트의 메시지는 항상 같은 파티션 → 같은 Consumer로 갑니다. 순서는 보장되지만 테넌트 안에서 replica를 늘려도 처리량이 늘지 않습니다
- replica 2개라 Canary 가중치가 파드 단위로 뭉개집니다
- `api-pool`이 노드 1대이고 PDB가 `minAvailable: 1`이라 그 노드를 드레인하려면 PDB를 잠깐 낮춰야 합니다
- Kafka 브로커 1대, Zonal 클러스터 — HA 없음
- Alertmanager가 null receiver라 알림이 아무에게도 가지 않습니다

---

자세한 GCP/클러스터 설정·중단/재개 절차·작업 규칙은 [AGENTS.md](AGENTS.md)에 있습니다.
[CLAUDE.md](CLAUDE.md)는 Claude Code 호환 진입점이고, 신규 합류자 안내는 [ONBOARDING.md](ONBOARDING.md),
진행 기록과 트러블슈팅 이력은 [JOURNEY.md](JOURNEY.md), 결정 기록은
[docs/architecture-decisions.md](docs/architecture-decisions.md)에 있습니다.
