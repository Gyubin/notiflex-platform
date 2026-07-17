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
| ch6 | 6.1 캐시 | ⬜ | | |
| ch6 | 6.2 시크릿 관리 | ⬜ | | |
| ch6 | 6.3 Canary 전환 | ⬜ | | |
| ch7 | 7.2 멀티 노드풀 | ⬜ | | |
| ch7 | 7.3 App of Apps | ⬜ | | |
| ch7 | 7.4 멀티테넌시 | ⬜ | | |
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

## 현재 버전

| 컴포넌트 | 버전 | 변경 이력 |
|---------|------|----------|
| Python | 3.13 | 2026-07-12 로컬 uv 전환하며 이미지(python:3.13-slim)에 맞춰 3.14→3.13 정합 |
| FastAPI | 0.139.0 | |
| uvicorn | 0.50.0 | |
| Notiflex 이미지 | v0.2.0 | 2026-07-18 v0.2.0: Argo Rollouts Blue/Green preview 생성 → 30초 auto-promotion → active Service 전환 검증 |
| ArgoCD | v3.4.5 | 2026-07-12 설치 (stable manifest) |
| Argo Rollouts | v1.9.1 | 2026-07-18 설치. active Service `notiflex-api`, preview Service `notiflex-api-preview`, autoPromotionSeconds=30 |
| kube-prometheus-stack | 87.15.1 (Helm) | 2026-07-12 설치. Prometheus v3.13.1, Grafana 13.1.0, operator v0.92.1 |
| Loki | 3.6.7 (grafana/loki Helm) | 2026-07-12 설치. SingleBinary, 2Gi PVC |
| Fluent Bit | grafana/fluent-bit (plugin-loki 2.1.0) | 2026-07-12 설치. DaemonSet, deprecated 차트지만 정상 동작 |
| Kafka | (미설치) | |
| OTel SDK | (미설치) | |

## 현재 리소스

| 노드풀 | 머신 타입 | 노드 수 | 주요 워크로드 |
|--------|----------|---------|-------------|
| default-pool | e2-medium (Spot) | **2 (2026-07-18 ch5 실습 재개)** | notiflex-api Rollout ×2, 관측 스택(Prometheus/Grafana/Alertmanager/Loki + node-exporter·Fluent Bit DaemonSet), ArgoCD, Argo Rollouts. CPU requests가 빠듯하므로 ch6 전 관측 스택 축소 필요 |

> **운영 주의**: ch5 실습을 위해 노드 풀을 2개로 재개하고 `notiflex-smb` auto-sync를 다시 켰다. 다시 중단할 때는 auto-sync 비활성화 → Rollout replica 0 → 노드 풀 0 순서를 지킨다. 그렇지 않으면 self-heal과 PDB가 드레인을 막을 수 있다 (AGENTS.md "Paused Cluster" 참조).

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
