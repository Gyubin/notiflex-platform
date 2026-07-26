# Notiflex 여정 기록

이 파일은 독자가 실제로 진행한 내용을 기록한다. AI가 각 챕터 완료 시 자동으로 업데이트한다.

> 이 저장소는 교재(Go 기준)와 달리 Python(FastAPI) 기반으로 진행한다. ch2 구간은 JOURNEY.md 도입(2026-07-07) 이전에 완료되어 소급 기록했다.

## 진행 현황

| 챕터 | 서브챕터 | 상태 | 완료일 | 비고 |
|------|---------|------|--------|------|
| ch2 | 2.2 설치 확인 | ✅ | 2026-07-07 | 소급 기록 |
| ch2 | 2.3 gcloud 설정 | ✅ | 2026-07-07 | 소급 기록. 프로젝트 `gyubin-gitaiops-project`, 서울 리전 |
| ch2 | 2.4 GitHub 저장소 | ✅ | 2026-07-07 | 소급 기록. `Gyubin/notiflex-platform` |
| ch2 | 2.5 GKE 클러스터 | ✅ | 2026-07-07 | 소급 기록. `notiflex-cluster`, e2-medium ×2 (Spot) |
| ch2 | 2.6 빌드/배포 | ✅ | 2026-07-07 | 소급 기록. FastAPI 앱, Cloud Build로 v0.1.0 빌드/배포 |
| ch2 | 2.7 첫 커밋 | ✅ | 2026-07-07 | 소급 기록. Deployment/Service/PDB 매니페스트 포함 |
| ch3 | 3.2 GitOps 도구 | ✅ | 2026-07-12 | ArgoCD v3.4.5 설치. Application `notiflex-smb`(k8s/smb, automated/prune/selfHeal). 노드 풀 0→2 재개 후 selfHeal이 파드 자동 복구 |
| ch3 | 3.3 기능 추가 | ✅ | 2026-07-12 | `/version`(앱 버전+런타임+Pod명) 추가, 로컬 uv 전환+Dockerfile uv 통일하며 v0.1.4까지. git push→ArgoCD 롤링 배포, git revert 롤백/롤포워드까지 검증 |
| ch3 | 3.4 CI | ✅ | 2026-07-12 | GitHub Actions, 릴리스 태그(v*) 트리거, WIF 키리스 인증. uv 테스트→docker build→push. v0.1.5 빌드/푸시 (배포는 3.5) |
| ch3 | 3.5 CI-CD 연결 | ✅ | 2026-07-12 | CI가 빌드 후 deployment.yaml 태그 갱신→main push→ArgoCD 자동 배포. `git tag v0.1.6` 한 번으로 v0.1.4→v0.1.6 E2E 검증 |
| ch4 | 4.2 메트릭 모니터링 | ✅ | 2026-07-12 | kube-prometheus-stack 87.15.1(Helm) 설치, 파드 7개 Running. 앱에 prometheus-fastapi-instrumentator 계측(/metrics, http_requests_total) 추가→v0.1.7 릴리스. ServiceMonitor(notiflex)로 스크레이프(타깃 2/2 UP). Grafana 대시보드 ConfigMap(CPU/메모리/HTTP요청/재시작) 사이드카 자동 임포트 완료 |
| ch4 | 4.3 로그 수집 | ✅ | 2026-07-12 | Loki(SingleBinary, 2Gi PVC) + Fluent Bit(DaemonSet 2/2) 설치. Grafana Loki 데이터소스 자동 등록(isDefault:false). `{namespace="notiflex"}`로 앱 로그 조회 확인. 캐시/게이트웨이/셀프모니터링 비활성으로 리소스 최소화 |
| ch4 | 4.4 알림 | ✅ | 2026-07-12 | PrometheusRule(pod-restart-alert, release:kube-prometheus 라벨) 생성. crashloop 테스트 파드로 재시작 3회 유발 → Prometheus firing + Alertmanager active(severity:warning) E2E 검증. 외부 채널(Slack 등)은 미설정 |
| ch5 | 5.2 트래픽 관리 | ✅ | 2026-07-18 | GKE Gateway API(Regional external)로 외부 IP `35.216.8.57` 할당. HTTPRoute `/` → active Service `notiflex-api:8080`, HealthCheckPolicy `/health:8080` 검증 |
| ch5 | 5.3 무중단 배포 | ✅ | 2026-07-18 | Argo Rollouts v1.9.1 Blue/Green 전환. `notiflex-api-preview` 추가, v0.2.0 preview 생성 후 30초 자동 승격·active 전환 검증 |
| ch6 | 6.1 캐시 | ✅ | 2026-07-20 | Bitnami Valkey 9.1.0 standalone(1Gi PVC) 설치. FastAPI `/id`를 Valkey `INCR`로 전환하고 v0.2.1 배포 후 Gateway에서 1→2→3 순차 증가 검증 |
| ch6 | 6.2 시크릿 관리 | ✅ | 2026-07-20 | Workload Identity와 GKE 관리형 Secret Manager CSI Driver 구성. Valkey 비밀번호를 Secret Manager에 이관하고 v0.2.2에서 읽기 전용 파일 마운트(`/mnt/secrets/valkey-password`) 검증 |
| ch6 | 6.3 Canary 전환 | ✅ | 2026-07-20 | Argo Rollouts Canary(20%→50%→80%→100%, 각 30초) 전환. v0.2.3 실배포 후 자동 진행·승격 검증 |
| ch7 | 7.2 멀티 노드풀 | ✅ | 2026-07-27 | 역할별 Spot 노드풀 api-pool(e2-medium)·worker-pool(e2-standard-2)·ops-pool(e2-small) 생성. Rollout에 `cloud.google.com/gke-nodepool: api-pool` nodeSelector 적용해 API Pod 2개가 api-pool에 배치됨을 확인. 전용 노드 확보로 replicas 1→2, PDB `minAvailable` 0→1 복원 |
| ch7 | 7.3 App of Apps | ✅ | 2026-07-27 | `argocd/root-app.yaml`이 `argocd/apps/`를 감시(`directory.recurse`)하는 App of Apps 구성. 기존 `notiflex-smb`를 `argocd/apps/`로 이동하고, 수동 `kubectl apply`로 관리하던 `k8s/monitoring/`을 `notiflex-monitoring` Application으로 편입. sync-wave 1(플랫폼)→2(앱) |
| ch7 | 7.4 멀티테넌시 | ✅ | 2026-07-27 | `enterprise` 네임스페이스에 별도 Rollout/Service/SA 배포. `argocd/apps/notiflex-enterprise.yaml`을 root-app이 자동 감지해 Application 생성(`CreateNamespace=true`). 교재의 커밋된 Valkey Secret 대신 테넌트 전용 SecretProviderClass로 Secret Manager를 마운트하고, `/id`가 notiflex의 Valkey에 크로스 네임스페이스로 붙는 것까지 검증 |
| ch7 | 💡 settings.local.json 권한 분리 | ✅ | 2026-07-27 | `.claude/settings.local.json`으로 deny/ask 체험. 교재 규칙 `Bash(kubectl delete *)`가 이 저장소에서는 매칭되지 않아 삭제가 실제로 실행됨(ArgoCD selfHeal로 복구). 실제 명령 형태에 맞춘 규칙으로 차단 확인 후 파일 삭제해 원상 복구. `ask` 시연은 worker-pool 실삭제 위험이 있어 생략 |
| ch8 | 8.1 메시징 | ⬜ | | |
| ch8 | 8.2 트레이싱 | ⬜ | | |
| ch8 | 8.3 CronJob | ⬜ | | |
| ch9 | 9.1 저장소 분석 | ⬜ | | |
| ch9 | 9.2 회고 | ⬜ | | |
| ch9 | 9.3 온보딩 문서 | ⬜ | | |
| ch9 | 9.4 GitAIOps 분석 | ⬜ | | |
| ch9 | 9.5 마무리 | ⬜ | | |

## 도구 선택 기록

독자가 3-프롬프트 패턴(탐색→비교→실행)에서 실제로 선택한 도구와 이유를 기록한다.

| 영역 | 선택 | 검토한 대안 | 선택 이유 |
|------|------|-----------|----------|
| 앱 언어 | Python (FastAPI + uvicorn) | Go (교재 기준) | Python 학습 목적으로 교재의 Go 스택을 대체 |
| 이미지 빌드 | Cloud Build | 로컬 docker build | M-시리즈 맥(arm64)과 GKE 노드(amd64) 아키텍처 불일치 회피 |
| GitOps 도구 | ArgoCD | Flux | UI/App of Apps 등 교재 진행 흐름과 정합, 선언적 Application으로 selfHeal 복구 |
| 로컬 의존성 관리 | uv (pyproject.toml + uv.lock) | pip + requirements.txt, .venv(3.14) | dev/운영 Python·의존성 정합(둘 다 3.13, uv.lock으로 하위 의존성까지 잠금), Dockerfile도 uv 통일 |
| CI 도구 | GitHub Actions | Cloud Build, Jenkins, GitLab CI | GitHub 네이티브, YAML 한 파일. 릴리스 태그(v*) 트리거 + git 태그를 이미지 태그/APP_VERSION으로 주입 |
| CI 인증 | Workload Identity Federation (키리스) | SA 키 + GitHub Secrets | 조직 정책(iam.disableServiceAccountKeyCreation)으로 SA 키 금지 → OIDC 교환, 저장 키 없음 |
| 메트릭 모니터링 | Prometheus + Grafana (kube-prometheus-stack) | Datadog, CloudWatch, GCP Monitoring | 오픈소스 K8s 표준(CNCF), 무료 자체 호스팅, Helm 번들로 6개 컴포넌트 일괄 설치, 이후 Loki/Tempo와 Grafana로 통합 |
| 로그 수집 | Loki + Fluent Bit | ELK Stack, CloudWatch, GCP Logging | 경량(Loki 128Mi vs ELK 2Gi+, e2-medium에 ELK 불가), Grafana 네이티브 통합, 라벨 인덱싱으로 저장 비용 낮음 |
| 알림 | PrometheusRule + Alertmanager | Grafana Alerting, PagerDuty/Opsgenie, Cloud Monitoring | 4.2 스택에 이미 포함(추가 설치 불필요), CRD를 YAML로 관리해 GitOps 호환(git blame/PR 리뷰), Alertmanager 라우팅/그루핑이 강력, 실무 표준 |
| 외부 트래픽 | GKE Gateway API | GKE Ingress, NGINX Ingress | GKE 네이티브라 별도 Controller가 없고, HTTPRoute로 표준적인 라우팅을 선언하며, 기존 active Service를 유지해 Blue/Green 전환과 자연스럽게 연동 |
| 무중단 배포 | Argo Rollouts Blue/Green | Deployment Rolling Update, Canary | preview 리비전을 active 트래픽과 분리해 검증한 뒤 30초 후 전환 가능. 2 replica 규모에서는 이중 Pod 비용이 감당 가능하고, Canary 자동 판정을 위한 메트릭 기준은 아직 미구축 |
| 배포 전략 전환 (ch6.3) | Argo Rollouts Canary | Blue/Green 유지, Rolling Update | 같은 Rollout CRD와 stable/preview Service를 재사용하면서 20%→50%→80% 단계별 관찰 구간을 두어 새 버전 노출 위험을 줄인다. 별도 배포 도구는 추가하지 않는다 |
| 캐시 (ch6.1) | Valkey standalone | Redis, Memcached, DragonflyDB | Redis 호환 `INCR`로 Pod 간 원자적 ID 생성을 보장하고 BSD 라이선스를 유지한다. 2노드 학습 환경에는 50m/64Mi 요청과 1Gi PVC의 단일 인스턴스가 적합 |
| 노드 배치 (ch7.2) | nodeSelector + 역할별 노드풀 | taint/toleration, nodeAffinity, topologySpreadConstraints | GKE가 노드풀 이름을 `cloud.google.com/gke-nodepool` 라벨로 자동 부여하므로 매니페스트에 한 줄만 추가하면 된다. 단일 존 학습 클러스터에서 taint/affinity는 과도하다. 대신 nodeSelector는 다른 Pod의 진입을 막지 못한다는 한계를 감수한다 |
| 다수 앱 관리 (ch7.3) | App of Apps (root-app) | ApplicationSet, Application 수동 관리 | `argocd/apps/`에 YAML을 넣으면 앱이 생긴다는 개념이 직관적이고 순수 YAML만 쓴다. 관리 대상이 5~7개 수준이라 ApplicationSet의 템플릿 이점이 크지 않다 |
| 멀티테넌시 (ch7.4) | Namespace 분리 + per-tenant Rollout | 단일 namespace + 라벨 격리, vCluster | 강한 격리, ArgoCD App of Apps와 자연 결합, 테넌트별 독립 배포 |
| 시크릿 관리 (ch6.2) | GKE Secret Manager CSI + Workload Identity | K8s Secret, Sealed Secrets, External Secrets Operator | GKE 네이티브 Workload Identity로 키 파일 없이 Secret Manager를 읽고, CSI 파일 마운트로 앱 환경변수·Git에 비밀번호를 복제하지 않는다 |

## 현재 버전

| 컴포넌트 | 버전 | 변경 이력 |
|---------|------|----------|
| Python | 3.13 | 2026-07-12 로컬 uv 전환하며 이미지(python:3.13-slim)에 맞춰 3.14→3.13 정합 |
| FastAPI | 0.139.0 | |
| uvicorn | 0.50.0 | |
| Notiflex 이미지 | v0.2.3 | 2026-07-20 v0.2.3: Canary 실배포 검증용 불변 태그. 20%→50%→80% 각 30초 pause 후 자동 승격, Gateway `/version`과 `/id` 정상 확인 |
| ArgoCD | v3.4.5 | 2026-07-12 설치 (stable manifest) |
| Argo Rollouts | v1.9.1 | 2026-07-20 Blue/Green에서 Canary로 전환. stable Service `notiflex-api`, canary Service `notiflex-api-preview`, setWeight 20/50/80과 각 30초 pause |
| kube-prometheus-stack | 87.15.1 (Helm) | 2026-07-12 설치. Prometheus v3.13.1, Grafana 13.1.0, operator v0.92.1 |
| Loki | 3.6.7 (grafana/loki Helm) | 2026-07-12 설치. SingleBinary, 2Gi PVC |
| Fluent Bit | grafana/fluent-bit (plugin-loki 2.1.0) | 2026-07-12 설치. DaemonSet, deprecated 차트지만 정상 동작 |
| Valkey | 9.1.0 (Bitnami chart 6.2.0) | 2026-07-20 설치. standalone, 비밀번호 인증, 1Gi PVC. Helm이 `valkey` Secret의 `valkey-password`를 생성 |
| Secret Manager CSI | GKE 관리형 addon | 2026-07-20 활성화. `secrets-store-gke.csi.k8s.io` Driver + provider `gke`, Workload Identity pool `project-b3c5c78c-8a5c-4e47-9fe.svc.id.goog` |
| Kafka | (미설치) | |
| OTel SDK | (미설치) | |

## 현재 리소스

| 노드풀 | 머신 타입 | 노드 수 | 주요 워크로드 |
|--------|----------|---------|-------------|
| default-pool | e2-medium (Spot), pd-balanced 30GB | 2 | 관측 스택(Prometheus/Grafana/Loki/Fluent Bit), ArgoCD, Argo Rollouts, kube-system |
| api-pool (ch7.2) | e2-medium (Spot), pd-standard 50GB | 1 | notiflex 테넌트 Rollout ×2 + enterprise 테넌트 Rollout ×1 (모두 nodeSelector). 여유 용량 때문에 valkey-primary도 현재 이 노드에 배치됨 |
| worker-pool (ch7.2) | e2-standard-2 (Spot), pd-standard 50GB | 1 | ch8 Kafka 배치 예정 |
| ops-pool (ch7.2) | e2-small (Spot), pd-standard 50GB | 1 | ch8 CronJob 배치 예정 |

모든 노드풀에 `--workload-metadata=GKE_METADATA`를 지정해 ch6.2의 Workload Identity(Secret Manager 접근)가 새 노드에서도 동작한다. 신규 풀은 `pd-standard`(HDD) 50GB로 만들어 리전 SSD 쿼터(300GB)를 소비하지 않는다.

> **운영 주의**: 현재 5노드로 가동 중이며 `notiflex-smb` auto-sync가 켜져 있다. 중단할 때는 auto-sync 비활성화 → Rollout replica 0 → 노드 풀 0 순서를 지킨다 (AGENTS.md "Paused Cluster" 참조). 재개 시에는 노드 풀 복구 후 auto-sync 재활성화와 hard refresh가 필요하다. api-pool은 노드가 1개이므로 그 노드를 드레인해야 할 때는 `notiflex-api` PDB의 `minAvailable`을 임시로 0으로 낮춘다.

## 트러블슈팅 이력

독자가 겪은 문제와 해결 방법을 기록한다. 같은 문제를 다시 겪지 않도록 한다.

| 챕터 | 문제 | 해결 |
|------|------|------|
| ch2 | 로컬(M-시리즈 맥, arm64) 빌드 이미지가 GKE 노드(amd64)와 아키텍처 불일치 | Cloud Build(GCP 서버, amd64)로 빌드 전환 |
| ch2 | Cloud Build에서 Compute Engine 기본 서비스 계정 권한 부족으로 빌드 실패 | 전용 SA `notiflex-cloudbuild` 생성 + `--default-buckets-behavior=REGIONAL_USER_OWNED_BUCKET` 지정 |
| ch2 | POD_NAME 기본값 테스트가 환경에 따라 간헐적 실패 | 테스트에서 환경변수를 명시적으로 unset (conftest.py) |
| ch2 | 노드 풀 0으로 중단 시 PDB가 노드 드레인을 차단 | 리사이즈 전에 Deployment replicas를 먼저 0으로 축소 |
| ch4~ | (2026-07-13) 노드 0 중단 시 `kubectl scale --replicas=0`이 안 먹힘 → ArgoCD selfHeal이 replicas=2로 되돌리고 되살아난 파드의 PDB가 마지막 노드 드레인을 1시간+ 차단 (PDB도 ArgoCD 관리라 delete해도 복원) | 중단 전에 `notiflex-smb` 앱의 auto-sync(`spec.syncPolicy.automated`)를 먼저 끄고 scale 0 → resize 0. 재개 시 auto-sync 재활성화(필요 시 `refresh=hard`). CLAUDE.md 중단 절차에 반영 |
| ch3 | 재개 후 auto-sync 재활성화해도 selfHeal이 바로 안 돎 | Application에 `argocd.argoproj.io/refresh=hard` 어노테이션으로 즉시 sync 트리거 |
| ch3 | CI용 SA 키 생성이 조직 정책(개인 org의 secure-by-default)으로 차단 | SA 키 대신 WIF(키리스)로 전환 |
| ch4 | helm이 미설치 상태 | `brew install helm` (v4.2.3) |
| ch4 | helm install이 auto 모드 분류기에 차단(node-exporter가 전클러스터 DaemonSet 생성) | 개인 학습 클러스터임을 확인하고 전체 스택 설치로 진행(사용자 승인) |
| ch4 | 설치 후 node1 CPU requests 93%(e2-medium allocatable ~940m/노드) | 정상 기동. 예산표대로 ch6 진입 전 관측 스택 requests를 5m으로 선제 축소 필요 |
| ch4 | Loki `persistence.enabled:false`로 두니 `mkdir /var/loki: read-only file system` CrashLoop | 루트 FS가 읽기 전용이라 /var/loki 쓰기 볼륨 필요. `singleBinary.persistence.enabled:true`(2Gi PVC)로 해결 |
| ch4 | Loki 차트 기본 memcached 캐시가 수백 Mi 요구 → e2-medium 부족 위험 | `chunksCache.enabled:false`, `resultsCache.enabled:false`로 비활성 |
| ch4 | grafana/fluent-bit 기본 `servicePath:/api/prom/push`(구버전)라 Loki 3.x 미수신 우려, PSP는 k8s 1.25+ 제거 | `loki.servicePath:/loki/api/v1/push`, `loki.serviceName:loki`, `rbac.pspEnabled:false` |
| ch4 | Fluent Bit DaemonSet도 클러스터 전체 워크로드라 auto 분류기 승인 대상 | node-exporter와 동일 성격, 로그 수집 목적상 필수 → 진행 |
| ch5 | Regional external Gateway 생성 전 서울 리전에 proxy-only 서브넷이 없음 | `default` 네트워크에 `REGIONAL_MANAGED_PROXY` 용도의 `proxy-only-subnet`(`172.16.0.0/23`)을 생성한 뒤 Gateway가 외부 IP를 할당받음 |
| ch5 | `kubectl argo rollouts` 플러그인 조회에서 컨텍스트를 생략해 기본 회사 AWS 컨텍스트의 OIDC 인증이 시도됨 | 세션 시작 시 기본 컨텍스트를 `notiflex-gke`로 확인·전환하고, 플러그인 명령에도 `--context notiflex-gke`를 반드시 붙인다. 일반 `kubectl`도 계속 `--context notiflex-gke`를 사용 |
| ch7 | `kubectl --context notiflex-gke argo rollouts status ...`가 `flags cannot be placed before plugin name`으로 실패 | kubectl 플러그인은 플래그를 플러그인 이름 뒤에만 받는다. `kubectl argo rollouts status notiflex-api -n notiflex --context notiflex-gke` 순서로 쓴다 (ch5 기록의 명령 형식을 이에 맞춰 정정) |
| ch7 | 교재의 `Bash(kubectl delete *)` deny 규칙이 동작하지 않아 enterprise Rollout이 실제로 삭제됨 | 이 저장소는 AGENTS.md 규칙 6에 따라 모든 명령이 `kubectl --context notiflex-gke delete ...` 형태라 `kubectl delete`로 시작하지 않는다. 규칙은 명령의 실제 접두사와 일치해야 한다. `Bash(kubectl --context notiflex-gke delete *)`를 추가하니 차단됨. 삭제된 Rollout은 ArgoCD selfHeal이 복구 |
| ch7 | enterprise 테넌트 Pod이 GCP Secret Manager를 못 읽어 기동 실패할 뻔함 | Workload Identity 바인딩은 `namespace/serviceaccount` 단위라 네임스페이스를 추가하면 GCP 쪽에도 `...svc.id.goog[enterprise/notiflex-api]`를 `roles/iam.workloadIdentityUser`로 추가해야 한다. IAM 정책 변경은 Claude Code 자동 승인 분류기에 차단되어 사용자가 직접 실행 |
| ch7 | nodeSelector를 api-pool로 지정한 뒤 `valkey-primary`도 같은 api-pool 노드에 배치됨 | nodeSelector는 "이 노드로 가라"만 지시하고 다른 Pod의 진입을 막지 못한다(거부하려면 taint/toleration 필요). 학습 범위에서는 그대로 두고, ch8에서 워크로드가 늘면 데이터·워커 계열 배치를 재검토한다 |
| ch5 | v0.2.0 CI가 `rollout.yaml`을 main에 먼저 커밋해 문서 푸시가 non-fast-forward로 거절됨 | 원격의 CI 커밋 범위를 확인한 뒤 `git rebase --autostash origin/main`으로 사용자 작업을 보존하며 문서 커밋을 재배치. force push는 사용하지 않음 |
| ch6 | Bitnami Valkey chart 6.2.0이 `bitnami/valkey:latest` 롤링 태그 경고를 표시 | 학습 환경에서는 chart 6.2.0을 고정해 사용. 운영 전환 시에는 이미지 digest 또는 지원되는 고정 이미지 태그로 검토 필요 |
| ch6 | Workload Identity 노드 교체가 단일 API replica의 PDB(`minAvailable: 1`) 때문에 드레인에서 정체 | GitOps PDB를 `minAvailable: 0`으로 임시 완화해 새 노드로 재배치. ch7에서 replicas와 함께 `minAvailable: 1` 복원 필요 |
| ch6 | CSI DaemonSet 추가 뒤 2개 e2-medium 노드의 CPU 예약이 96% 이상으로 포화되어 API·Valkey가 Pending | Loki·Fluent Bit만 중지해도 50m Pod를 수용할 여유가 부족해 default-pool을 Spot 노드 3개로 임시 확장. ch7 역할별 노드풀 설계에서 재평가 |
| ch6 | CSI Rollout이 이전 이미지(v0.2.1)를 그대로 사용해 `VALKEY_PASSWORD` 누락으로 CrashLoop | 코드 변경 후 새 불변 태그 `v0.2.2`를 릴리스해 `VALKEY_PASSWORD_FILE` 지원 이미지를 배포 |
