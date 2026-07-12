# notiflex-platform

B2B 알림 SaaS 플랫폼을 가정한 Kubernetes 운영환경 구축 실습 프로젝트입니다. FastAPI 백엔드를 GKE에 배포하고, 이미지 빌드부터 배포·CI/CD·관측 가능성까지 단계적으로 구성합니다.

## 현재 상태

- [x] FastAPI 앱 (`/health`, `/version`, `/id`, `/metrics`) + pytest 테스트
- [x] Dockerfile (multi-stage, non-root, `uv sync --frozen`) — Cloud Build / CI로 `notiflex-api` 빌드/push
- [x] K8s 매니페스트 (Namespace/Deployment/Service/PDB/ServiceMonitor) — GKE `notiflex-cluster`에 배포 완료 (replicas 2, 노드 분산)
- [x] GitOps 배포 (ArgoCD `notiflex-smb`, automated sync + selfHeal)
- [x] CI/CD (GitHub Actions 릴리스 태그 트리거 + WIF 키리스 인증 → ArgoCD 자동 배포)
- [x] 관측 가능성 — 메트릭(Prometheus+Grafana), 로그(Loki+Fluent Bit), 알림(PrometheusRule+Alertmanager)
- [ ] Gateway API 외부 노출 (HTTPRoute)

> 배포 이미지: `notiflex-api:v0.1.7` · 앱 버전은 git 태그가 단일 소스(`/version`으로 확인).

## 구성

| 항목 | 값 |
|---|---|
| 클러스터 | GKE Standard (Zonal) `notiflex-cluster`, `asia-northeast3-a`, e2-medium x 2 (Spot) |
| 네임스페이스 | 앱 `notiflex`, 관측 스택 `monitoring`, GitOps `argocd` |
| 이미지 저장소 | `asia-northeast3-docker.pkg.dev/project-b3c5c78c-8a5c-4e47-9fe/notiflex-platform/<이미지명>:<태그>` |
| kubectl context | `notiflex-gke` |
| GitOps | ArgoCD (Application `notiflex-smb` → `k8s/smb`, automated/prune/selfHeal) |

## 디렉토리 구조

```
app/                  # FastAPI 소스, 테스트, Dockerfile, pyproject.toml + uv.lock
k8s/smb/              # ArgoCD 동기화 대상 매니페스트 (namespace/deployment/service/pdb/servicemonitor)
k8s/monitoring/       # 관측 매니페스트 (Grafana 대시보드·Loki 데이터소스 ConfigMap, PrometheusRule) — kubectl apply
helm-values/          # Helm values (kube-prometheus-stack, Loki, Fluent Bit)
argocd/               # ArgoCD Application 정의 (notiflex-smb)
.github/workflows/    # CI 파이프라인 (ci.yaml)
docs/superpowers/     # 설계 스펙 및 구현 플랜 문서
```

## API

| 엔드포인트 | 설명 |
|---|---|
| `GET /health` | 상태 확인 (K8s readiness/liveness probe에서 사용) |
| `GET /version` | 앱 버전(git 태그) + 런타임(python 버전) + Pod 이름 반환 |
| `GET /id` | in-memory 카운터 ID + Pod 이름 반환. Pod별 카운터라 전역 유일하지 않음 (`pod` + `id` 조합으로 식별) |
| `GET /metrics` | Prometheus 메트릭 (`http_requests_total` 등). ServiceMonitor가 스크레이프 |

## 로컬 개발 (uv)

로컬 의존성/가상환경은 **uv**로 관리합니다 (`app/pyproject.toml` + `app/uv.lock`, Python 3.13 고정 — 이미지 베이스와 정합).

```bash
cd app
uv sync                             # 의존성 설치 (가상환경 자동 생성)

uv run pytest                       # 테스트
uv run uvicorn main:app --port 8080 # 로컬 실행
```

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

릴리스 태그를 밀면 CI가 빌드·태그 갱신까지 하고, ArgoCD가 이를 감지해 자동 배포합니다. main에 코드만 push하면 배포되지 않습니다.

```bash
git tag vX.Y.Z && git push origin vX.Y.Z
```

- **CI** (`.github/workflows/ci.yaml`): uv 테스트 → `docker build`(amd64) → Artifact Registry push → `k8s/smb/deployment.yaml` 이미지 태그 갱신 → main commit/push
- **CD**: ArgoCD(`notiflex-smb`)가 `k8s/smb` 변경을 감지해 rolling update
- **인증**: Workload Identity Federation(키리스). 조직 정책으로 SA 키 생성이 금지되어 GitHub OIDC로 `notiflex-ci` SA를 impersonate — 저장 키 없음
- git 태그가 곧 이미지 태그이자 `APP_VERSION`(`/version` 값)의 단일 소스

## 배포 (수동 / GitOps 미경유)

```bash
kubectl --context notiflex-gke apply -f k8s/smb/

# 확인
kubectl --context notiflex-gke get pods -n notiflex
kubectl --context notiflex-gke port-forward -n notiflex svc/notiflex-api 8080:8080
curl localhost:8080/health
```

외부 노출은 클러스터에 활성화된 Gateway API(HTTPRoute)로 연결할 예정이며, 아직 미구성입니다. 현재는 `port-forward`로만 접근 가능합니다.

## 관측 가능성

`monitoring` 네임스페이스에 Helm으로 구축했습니다 (ArgoCD 관리 대상 아님 — values는 `helm-values/`, 매니페스트는 `k8s/monitoring/`).

- **메트릭**: kube-prometheus-stack (Prometheus + Grafana + Alertmanager + node-exporter + kube-state-metrics). 앱 `/metrics`를 `k8s/smb/servicemonitor.yaml`로 스크레이프
- **로그**: Loki(SingleBinary) + Fluent Bit(DaemonSet). Grafana에서 LogQL `{namespace="notiflex"}`로 조회
- **알림**: PrometheusRule `pod-restart-alert` → Alertmanager. 외부 채널(Slack/이메일)은 미설정

```bash
# Grafana 접속
kubectl --context notiflex-gke -n monitoring port-forward svc/kube-prometheus-grafana 3000:80
# http://localhost:3000 (admin, 비밀번호는 kube-prometheus-grafana Secret)
```

> ⚠️ 관측 스택 설치 후 노드 CPU requests가 ~95%로 빠듯합니다. 리소스 판단 시 실측(`kubectl top`)을 우선합니다.

---

자세한 GCP/클러스터 설정·비용 절감(중단/재개) 절차·작업 규칙은 [CLAUDE.md](CLAUDE.md), 진행 기록은 [JOURNEY.md](JOURNEY.md), 설계 배경은 [docs/superpowers/](docs/superpowers/)를 참고하세요.
