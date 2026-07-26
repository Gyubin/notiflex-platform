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
| ch6 | 6.4 아키텍처 스냅샷 | ✅ | 2026-07-27 | 소급 기록. ch6 시점에 건너뛴 것을 ch8 완료 후 작성. `claude-context/architecture.md`에 클러스터 토폴로지·컴포넌트 흐름·배포 파이프라인·관측 스택·네임스페이스를 현재(ch8) 상태로 정리. 규칙(AGENTS.md)·현재 상태(claude-context)·결정 이유(ADR) 3층 분리 |
| ch7 | 7.2 멀티 노드풀 | ✅ | 2026-07-27 | 역할별 Spot 노드풀 api-pool(e2-medium)·worker-pool(e2-standard-2)·ops-pool(e2-small) 생성. Rollout에 `cloud.google.com/gke-nodepool: api-pool` nodeSelector 적용해 API Pod 2개가 api-pool에 배치됨을 확인. 전용 노드 확보로 replicas 1→2, PDB `minAvailable` 0→1 복원 |
| ch7 | 7.3 App of Apps | ✅ | 2026-07-27 | `argocd/root-app.yaml`이 `argocd/apps/`를 감시(`directory.recurse`)하는 App of Apps 구성. 기존 `notiflex-smb`를 `argocd/apps/`로 이동하고, 수동 `kubectl apply`로 관리하던 `k8s/monitoring/`을 `notiflex-monitoring` Application으로 편입. sync-wave 1(플랫폼)→2(앱) |
| ch7 | 7.4 멀티테넌시 | ✅ | 2026-07-27 | `enterprise` 네임스페이스에 별도 Rollout/Service/SA 배포. `argocd/apps/notiflex-enterprise.yaml`을 root-app이 자동 감지해 Application 생성(`CreateNamespace=true`). 교재의 커밋된 Valkey Secret 대신 테넌트 전용 SecretProviderClass로 Secret Manager를 마운트하고, `/id`가 notiflex의 Valkey에 크로스 네임스페이스로 붙는 것까지 검증 |
| ch7 | 💡 settings.local.json 권한 분리 | ✅ | 2026-07-27 | `.claude/settings.local.json`으로 deny/ask 체험. 교재 규칙 `Bash(kubectl delete *)`가 이 저장소에서는 매칭되지 않아 삭제가 실제로 실행됨(ArgoCD selfHeal로 복구). 실제 명령 형태에 맞춘 규칙으로 차단 확인 후 파일 삭제해 원상 복구. `ask` 시연은 worker-pool 실삭제 위험이 있어 생략 |
| ch8 | 8.1 메시징 | ✅ | 2026-07-27 | Strimzi 1.1.0 operator + Kafka 4.3.0 단일 브로커(KRaft, controller/broker 겸용)를 worker-pool에 배치. `notifications` 토픽(3파티션). FastAPI에 aiokafka Producer/Consumer 추가해 `/id`가 Valkey INCR 후 이벤트를 발행하고, 같은 Pod의 백그라운드 Consumer가 수신. v0.3.0 배포 후 앱 로그 누락을 발견해 v0.3.1로 수정. `argocd/apps/notiflex-kafka.yaml`을 root-app이 자동 감지 |
| ch8 | 8.2 트레이싱 | ✅ | 2026-07-27 | Grafana Tempo 2.9.0(SingleBinary)을 ops-pool에 설치하고 OTLP gRPC(4317) 수집. OTel Python SDK 1.39.0 + FastAPI 자동 계측에 `valkey.incr`·`kafka.publish` 수동 span을 더해 v0.4.0 배포. `GET /id` 트레이스에서 전체 6.80ms 중 Valkey 0.80ms·Kafka 2.96ms로 구간이 갈리는 것을 확인. `service.namespace`에 테넌트를 실어 Grafana에서 smb/enterprise를 나눠 조회 |
| ch8 | 8.3 CronJob | ✅ | 2026-07-27 | `notiflex-healthcheck` CronJob(`*/5 * * * *`)을 ops-pool에 배치. Service DNS로 `/health`를 호출해 200이 아니면 실패로 종료한다. `concurrencyPolicy: Forbid`로 앞 실행이 밀렸을 때 중복 실행을 막고, `k8s/smb/`에 두어 ArgoCD가 관리 |
| ch9 | 9.1 저장소 분석 | ✅ | 2026-07-27 | 91커밋·릴리스 태그 10개·추적 파일 61개(첫 커밋 07-05 이래 22일). 코드 475줄 : 매니페스트 1,171줄 : 문서 1,941줄. ch8 종료 직후 중단했던 클러스터를 재개해 Application 5개가 전부 `Synced`+`Healthy`임을 확인(수동 apply 잔재 없음). 외부 IP에서 `/version` v0.4.0, `/id` 28 응답 — 중단 중에도 Valkey PVC의 카운터가 보존됨. 대조 과정에서 README.md가 ch6에서 정지(v0.2.3·단일 노드풀 기준), `app/pyproject.toml`의 `version`이 0.1.4에 멈춘 것을 발견 |
| ch9 | 9.2 회고 | ✅ | 2026-07-27 | CLAUDE.md 28→120줄 성장 후 ch6에서 AGENTS.md로 이관(5줄로 축소), AGENTS.md는 180→273줄. 늘어난 줄의 대부분이 실제 사고 후 추가된 예방 규칙. 반복된 선택 기준 4가지(GKE/managed 우선, Argo 생태계 통일, Grafana 통합 관측, GitOps 호환) 추출. 재선택 검토 항목으로 CSI vs Sealed Secrets, Canary 도입 시점, Valkey Streams vs Kafka, 그리고 Helm 소유 6개 릴리스가 GitOps 밖에 남은 이원화 문제를 기록 |
| ch9 | 9.3 온보딩 문서 | ✅ | 2026-07-27 | `ONBOARDING.md` 생성(약 320줄). 실제 `kubectl` 조회 기반 노드풀·네임스페이스 현황, 접근 방법(ArgoCD·Grafana·API), 배포 플로우, Q&A 7개. 교재 요구사항에 "알고 있어야 할 한계" 절과 증상별 원인 표(트러블슈팅 38건 압축)를 추가 |
| ch9 | 9.4 GitAIOps 분석 | ✅ | 2026-07-27 | Git=결정의 저장소, AI=누적 맥락의 소비자, Ops=Git이 진실임을 재개로 증명. 장별 커밋 수(ch2 31 → ch4 5)로 루프 가속을 확인하고, ch6의 12커밋이 문서 구조 재편 비용이었으며 그 덕에 ch7이 6커밋으로 끝났음을 짚음. 한계로 "기록하는 습관에 전적으로 의존" 명시(ch6.4 소급, README 방치가 사례) |
| ch9 | 9.5 마무리 | ✅ | 2026-07-27 | 다음 단계 5개 영역 제안. 우선순위는 NetworkPolicy(네임스페이스는 갈랐으나 네트워크는 안 갈림)와 Alertmanager 외부 채널 연결(현재 null receiver). KEDA는 메시지 키가 테넌트로 고정된 구조에서는 효과가 없어 키 변경이 선행 작업임을 기록 |

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
| 메시징 (ch8.1) | Kafka (Strimzi Operator) | RabbitMQ, NATS, Valkey Streams | 이벤트 드리븐의 사실상 표준이라 학습 가치가 가장 크고, Strimzi가 Kafka 클러스터·토픽을 CRD로 노출해 ArgoCD로 그대로 관리된다. KRaft 모드라 ZooKeeper 없이 단일 브로커로 e2-standard-2 한 대에 들어간다. 이미 깔린 Valkey의 Streams를 쓰면 추가 설치가 없지만 전용 브로커 대비 기능이 얕다 |
| Kafka 클라이언트 (ch8.1) | aiokafka | confluent-kafka(librdkafka), kafka-python | FastAPI가 asyncio 기반이라 Consumer를 lifespan 안의 백그라운드 태스크로 자연스럽게 띄울 수 있다. confluent-kafka가 더 빠르지만 동기 API라 별도 스레드 관리가 필요하고, kafka-python은 유지보수가 정체됐다. 교재의 Go(sarama)를 대체 |
| 분산 트레이싱 (ch8.2) | Grafana Tempo | Jaeger, Zipkin, Grafana Cloud Traces | 이미 Grafana를 쓰고 있어 메트릭·로그와 같은 화면에서 트레이스까지 본다. 인덱스 없이 오브젝트 스토리지에 그대로 쌓는 구조라 Jaeger의 Elasticsearch 백엔드보다 훨씬 가볍고, e2-small 노드에 22Mi로 들어간다. 대신 트레이스 ID 조회 위주라 복잡한 속성 검색은 Jaeger보다 약하다 |
| 배치 자동화 (ch8.3) | K8s CronJob | 외부 cron + 클러스터 외부 트리거, Argo Workflows | 쿠버네티스 네이티브라 별도 설치가 없고, 매니페스트 한 장이라 ArgoCD가 그대로 관리한다(git blame·PR 리뷰도 그대로 붙는다). ops-pool에 배치해 API 노드를 건드리지 않는다. Argo Workflows는 의존성 있는 다단계 파이프라인용이라 헬스체크 한 건에는 과하다 |
| 시크릿 관리 (ch6.2) | GKE Secret Manager CSI + Workload Identity | K8s Secret, Sealed Secrets, External Secrets Operator | GKE 네이티브 Workload Identity로 키 파일 없이 Secret Manager를 읽고, CSI 파일 마운트로 앱 환경변수·Git에 비밀번호를 복제하지 않는다 |

## 현재 버전

| 컴포넌트 | 버전 | 변경 이력 |
|---------|------|----------|
| Python | 3.13 | 2026-07-12 로컬 uv 전환하며 이미지(python:3.13-slim)에 맞춰 3.14→3.13 정합 |
| FastAPI | 0.139.0 | |
| uvicorn | 0.50.0 | |
| Notiflex 이미지 | v0.4.0 | 2026-07-20 v0.2.3: Canary 실배포 검증용 불변 태그. 2026-07-27 v0.3.0: aiokafka Producer/Consumer 추가, `/id` 응답에 `tenant`·`published` 필드와 `/notifications` 엔드포인트 신설. 2026-07-27 v0.3.1: `logging.basicConfig` 누락으로 앱 자체 로그가 전부 유실되던 문제 수정. 2026-07-27 v0.4.0: OTel 계측 추가(`valkey.incr`·`kafka.publish` span). ch8.1부터 CI가 smb·enterprise 두 Rollout을 함께 갱신 |
| ArgoCD | v3.4.5 | 2026-07-12 설치 (stable manifest) |
| Argo Rollouts | v1.9.1 | 2026-07-20 Blue/Green에서 Canary로 전환. stable Service `notiflex-api`, canary Service `notiflex-api-preview`, setWeight 20/50/80과 각 30초 pause |
| kube-prometheus-stack | 87.15.1 (Helm) | 2026-07-12 설치. Prometheus v3.13.1, Grafana 13.1.0, operator v0.92.1 |
| Loki | 3.6.7 (grafana/loki Helm) | 2026-07-12 설치. SingleBinary, 2Gi PVC |
| Fluent Bit | grafana/fluent-bit (plugin-loki 2.1.0) | 2026-07-12 설치. DaemonSet, deprecated 차트지만 정상 동작 |
| Valkey | 9.1.0 (Bitnami chart 6.2.0) | 2026-07-20 설치. standalone, 비밀번호 인증, 1Gi PVC. Helm이 `valkey` Secret의 `valkey-password`를 생성 |
| Secret Manager CSI | GKE 관리형 addon | 2026-07-20 활성화. `secrets-store-gke.csi.k8s.io` Driver + provider `gke`, Workload Identity pool `project-b3c5c78c-8a5c-4e47-9fe.svc.id.goog` |
| Kafka | 4.3.0 (Strimzi 1.1.0) | 2026-07-27 설치. KRaft 모드, `dual-role` KafkaNodePool 1개가 controller+broker 겸용, 5Gi PVC. Strimzi 1.1.0은 Kafka 4.2.0~4.3.0만 지원 |
| aiokafka | 0.13.0 | 2026-07-27 추가. Producer는 `/id`에서 send_and_wait, Consumer는 lifespan 백그라운드 태스크 |
| Tempo | 2.9.0 (grafana/tempo chart 1.24.4) | 2026-07-27 설치. SingleBinary, OTLP gRPC 4317 수집 / HTTP 3200 조회, emptyDir 저장, retention 24h. deprecated 차트지만 단일 바이너리 모드로 충분 |
| OTel SDK | opentelemetry-sdk 1.39.0 | 2026-07-27 추가. `opentelemetry-exporter-otlp-proto-grpc` 1.39.0, `opentelemetry-instrumentation-fastapi` 0.60b0 |

## 현재 리소스

| 노드풀 | 머신 타입 | 노드 수 | 주요 워크로드 |
|--------|----------|---------|-------------|
| default-pool | e2-medium (Spot), pd-balanced 30GB | 2 | 관측 스택(Prometheus/Grafana/Loki/Fluent Bit), ArgoCD, Argo Rollouts, kube-system |
| api-pool (ch7.2) | e2-medium (Spot), pd-standard 50GB | 1 | notiflex 테넌트 Rollout ×2 + enterprise 테넌트 Rollout ×1 (모두 nodeSelector). 여유 용량 때문에 valkey-primary도 현재 이 노드에 배치됨 |
| worker-pool (ch7.2) | e2-standard-2 (Spot), pd-standard 50GB | 1 | Strimzi operator, Kafka 브로커(dual-role), entity-operator (ch8.1). CPU 10% / 메모리 44% 사용 |
| ops-pool (ch7.2) | e2-small (Spot), pd-standard 50GB | 1 | Tempo (ch8.2), 헬스체크 CronJob (ch8.3). allocatable이 940m/1391Mi뿐이라 DaemonSet만으로 이미 CPU 56%·메모리 75%가 예약된 상태. 여기에 워크로드를 더 얹을 때는 반드시 requests를 먼저 확인한다 |

모든 노드풀에 `--workload-metadata=GKE_METADATA`를 지정해 ch6.2의 Workload Identity(Secret Manager 접근)가 새 노드에서도 동작한다. 신규 풀은 `pd-standard`(HDD) 50GB로 만들어 리전 SSD 쿼터(300GB)를 소비하지 않는다.

ch8 이후 클러스터에는 `kafka` 네임스페이스(Strimzi operator + 브로커 + entity-operator)와 `monitoring`의 Tempo, `notiflex`의 헬스체크 CronJob이 추가됐다. ArgoCD Application은 `root-app`, `notiflex-smb`, `notiflex-enterprise`, `notiflex-monitoring`, `notiflex-kafka` 5개다.

> **운영 주의 (2026-07-27 ch9 종료 시점: 중단됨)**: ch9.1의 클러스터 ↔ Git 일치 확인을 위해 노드풀 4개(총 5노드)를 재개해 Application 5개가 모두 `Synced`+`Healthy`임을 확인하고, 외부 IP에서 `/version` v0.4.0과 `/id` 28을 응답받은 뒤 같은 절차로 다시 중단했다. **재개할 때는 노드 5대가 전부 `Ready`가 된 뒤에 auto-sync를 켠다** — 먼저 켜면 API Pod이 Kafka 브로커보다 앞서 떠서 10분간 CrashLoop을 돈다(트러블슈팅 이력 ch9 항목 참조). 상태는 아래 ch8 종료 시점과 동일하다.
>
> **운영 주의 (2026-07-27 ch8 종료 시점: 중단됨)**: 노드풀 4개 전부 0, Application 5개 auto-sync 비활성, 헬스체크 CronJob suspend 상태다. PVC 3개(Kafka 5Gi·Loki 2Gi·Valkey 1Gi)는 그대로 남아 있어 재개하면 카운터·로그·미수신 메시지가 살아 있다. 중단·재개 절차는 AGENTS.md "Paused Cluster" 참조. **root-app은 끌 때 가장 먼저, 켤 때 가장 마지막**이다. api-pool은 노드가 1개이므로 그 노드를 드레인해야 할 때는 `notiflex-api` PDB의 `minAvailable`을 임시로 0으로 낮춘다.

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
| ch8 | 교재가 지정한 Kafka 4.1.0이 Strimzi 1.1.0에서 기동 실패 | Strimzi 1.1.0이 지원하는 Kafka는 4.2.0·4.2.1·4.3.0뿐이다. `helm template ... \| grep STRIMZI_KAFKA_IMAGES`로 실제 지원 목록을 먼저 확인하고 4.3.0을 지정. Strimzi 버전이 오를 때마다 다시 봐야 하는 값 |
| ch8 | Strimzi PodTemplate에 `nodeSelector` 필드가 없어 worker-pool 고정 방법이 없음 | Strimzi는 `spec.template.pod`에 `affinity`와 `tolerations`만 노출한다. 라벨 키는 다른 매니페스트와 같은 `cloud.google.com/gke-nodepool`을 쓰되 nodeAffinity(`requiredDuringScheduling...`)로 동일한 배치를 만든다 |
| ch8 | 앱이 남기는 `logger.info`가 Pod 로그에 전혀 안 나옴 | uvicorn은 자기 로거만 설정하고 root 로거는 핸들러 없이 둔다. 그래서 INFO 로그가 logging의 last-resort 핸들러(WARNING 이상만 통과)로 떨어져 사라졌다. ch6의 "Valkey 연결 성공"도 그동안 안 보이던 상태. `logging.basicConfig(level=INFO)` 추가(v0.3.1)로 해결 |
| ch8 | CI가 `k8s/smb/rollout.yaml`만 갱신해 enterprise 테넌트가 옛 이미지에 방치됨 | ch7.4에서 테넌트를 추가할 때 CI를 같이 손보지 않아 생긴 빈틈. 두 테넌트가 같은 이미지를 쓰므로 CI의 sed 대상을 두 매니페스트로 확장. 테넌트별로 버전을 다르게 가려면 여기서 다시 갈라야 한다 |
| ch8 | 단일 `notifications` 토픽에서 enterprise Consumer가 smb 메시지까지 전부 수신 (`consumed: 6` = enterprise 2 + smb 4) | Consumer Group을 테넌트별로 나누면 "각자 토픽 전량을 독립적으로 읽는" 것이지 격리가 아니다. 메시지 키에 테넌트를 실어도 파티션 배분이 갈릴 뿐 구독 범위는 그대로다. 진짜 격리는 테넌트별 토픽이나 Kafka ACL이 필요하며, ch7.4의 Valkey `/id` 공유 문제와 같은 성격의 미해결 과제로 ch9에서 함께 다룬다 |
| ch8 | 한 테넌트의 메시지가 Pod 하나에만 몰림 (`consumed: 4` vs `0`) | 메시지 키를 테넌트 이름으로 고정하면 그 테넌트의 메시지가 항상 같은 파티션으로 간다. 파티션 하나는 그룹 내 Consumer 하나만 받으므로 replica를 늘려도 테넌트 내 병렬 처리가 늘지 않는다. 순서 보장과 처리량을 맞바꾼 구조이며, 병렬이 필요하면 키를 알림 ID 등으로 바꿔야 한다 |
| ch8 | Tempo 차트 기본값 `memBallastSizeMbs: 1024`가 e2-small(가용 1391Mi)에 과함 | 볼러스트는 GC를 늦춰 지연을 줄이는 장치라 학습 규모에서는 필요 없다. `0`으로 두고 requests 192Mi/limits 384Mi로 배치. 실사용량은 22Mi에 그쳤다 |
| ch8 | Tempo values에서 `receivers.jaeger: null`로 미사용 수신기를 끄려다 차트 렌더링 실패 | `nil pointer evaluating interface {}.protocols`. Service 템플릿(`_ports.tpl`)이 값의 존재 여부를 확인하지 않고 jaeger 포트를 참조한다. deprecated 차트라 수정될 가능성이 낮아 기본 수신기를 그대로 두기로 결정 |
| ch8 | Grafana 데이터소스 uid가 자동 생성되어 매번 바뀜 | 프로비저닝 YAML에 `uid`를 안 적으면 Grafana가 임의 값(`P214B5B846CF3925F`)을 만든다. 대시보드·링크가 uid로 데이터소스를 참조하므로 재생성 시 깨진다. `uid: tempo`로 고정 |
| ch8 | 중단 절차가 App of Apps 이전 기준이라 그대로 쓰면 auto-sync가 되살아남 | root-app이 자식 Application의 `spec.syncPolicy`까지 관리하므로, 자식만 끄면 root-app selfHeal이 Git의 `automated`를 복원한다. **끌 때는 root-app 먼저, 켤 때는 root-app 마지막.** 대상도 `notiflex-smb` 하나가 아니라 Application 5개 전부다 |
| ch8 | 중단 시 CronJob이 살아 있으면 죽은 API에 계속 요청해 실패 Job이 쌓임 | 노드풀을 내리기 전에 `kubectl patch cronjob ... -p '{"spec":{"suspend":true}}'`로 정지시킨다. ch8에서 새로 생긴 절차 항목 |
| ch8 | 릴리스 태그 push 후 문서 커밋이 non-fast-forward로 거절 (ch5와 동일 재발) | CI가 `ci: deploy ...` 커밋을 main에 먼저 올린다. `git rebase --autostash origin/main`으로 재배치. 태그를 밀기 전에 `git fetch`부터 하는 습관이 필요 |
| ch9 | 재개 직후 `notiflex-api` 2개와 Kafka `entity-operator`가 10분간 CrashLoopBackOff (각 6~7회 재시작) | 기동 순서 경합이다. 노드풀을 순차로 resize하면 노드가 3~5분 간격으로 올라오는데, Pod 객체는 노드가 없는 동안에도 Pending으로 살아 있다가 노드가 붙는 즉시 스케줄된다. 그래서 api-pool의 API Pod이 worker-pool의 Kafka 브로커보다 먼저 뜬다. entity-operator도 브로커보다 먼저 떠서 Exit 0으로 정상 종료를 반복했다. 둘 다 백오프 끝에 자연 복구되므로 조치는 불필요하지만, **재개 절차에 "노드 5대가 모두 Ready가 된 뒤 auto-sync를 켠다"는 순서를 명시**해야 불필요한 CrashLoop을 피한다. API Pod의 Exit 137은 메모리 초과가 아니다(실사용 57Mi / limit 128Mi) — Kafka 접속 실패로 프로세스가 죽은 뒤 liveness probe가 connection refused를 보고 재시작을 건 것 |
| ch9 | 저장소 대조에서 README.md가 ch6 시점(v0.2.3·단일 노드풀·Application 1개)에 멈춰 있는 것을 발견 | ch7·ch8의 `/update-docs`가 에이전트용 문서(AGENTS.md, architecture.md, JOURNEY.md)만 갱신하고 사람이 읽는 README를 대상에서 빠뜨렸다. 문서 갱신 절차의 대상 목록에 README를 명시해야 한다. `app/pyproject.toml`의 `version`도 0.1.4에 멈춰 있으나 실제 버전은 git 태그와 `APP_VERSION`이 결정하므로 동작 영향은 없다 |
