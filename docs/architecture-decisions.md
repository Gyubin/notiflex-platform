# Architecture Decision Records

## ADR-001: 배포 자동화는 ArgoCD (3장)
**시점**: 2026-07 / **결정**: GitOps 배포 도구로 ArgoCD를 사용한다. Flux는 도입하지 않는다.
**이유**:
- Git 저장소의 선언형 매니페스트를 클러스터 상태와 지속적으로 동기화한다.
- Application UI와 App of Apps 확장 경로가 이후 실습 흐름에 맞는다.
- 자동 동기화, prune, self-heal로 수동 변경 이후의 원하는 상태를 복원한다.
- Kubernetes 환경에서 널리 쓰이는 GitOps 도구이며 학습 자료가 충분하다.

## ADR-002: CI 도구는 GitHub Actions (3장)
**시점**: 2026-07 / **결정**: 릴리스 CI로 GitHub Actions를 사용한다. Cloud Build, Jenkins, GitLab CI는 사용하지 않는다.
**이유**:
- 소스 저장소와 같은 GitHub에서 워크플로우를 관리한다.
- 릴리스 태그를 이미지 태그와 `APP_VERSION`의 단일 소스로 유지한다.
- 테스트, 이미지 빌드·푸시, GitOps 매니페스트 갱신을 한 워크플로우로 연결한다.
- Workload Identity Federation으로 저장형 서비스 계정 키 없이 GCP에 인증한다.

## ADR-003: 메트릭은 Prometheus와 Grafana (4장)
**시점**: 2026-07 / **결정**: 메트릭 수집·시각화에 kube-prometheus-stack을 사용한다. Datadog, CloudWatch, GCP Monitoring은 사용하지 않는다.
**이유**:
- Kubernetes 생태계의 표준적인 오픈소스 조합이다.
- 자체 호스팅으로 추가 SaaS 비용 없이 운영할 수 있다.
- Helm 설치로 Prometheus, Grafana, Alertmanager를 일관되게 구성한다.
- 이후 Loki와 Tempo까지 Grafana에서 통합 조회할 수 있다.

## ADR-004: 로그는 Loki와 Fluent Bit (4장)
**시점**: 2026-07 / **결정**: 로그 수집·조회에 Loki와 Fluent Bit를 사용한다. ELK Stack, CloudWatch, GCP Logging은 사용하지 않는다.
**이유**:
- e2-medium 2노드 환경에서 ELK보다 훨씬 적은 리소스를 사용한다.
- Grafana와 네이티브로 연동되어 메트릭과 로그를 함께 분석할 수 있다.
- 전체 로그가 아니라 라벨을 인덱싱해 저장 비용과 운영 복잡도를 낮춘다.
- DaemonSet Fluent Bit가 모든 노드의 컨테이너 로그를 일관되게 수집한다.

## ADR-005: 알림은 PrometheusRule과 Alertmanager (4장)
**시점**: 2026-07 / **결정**: Kubernetes 알림 규칙과 라우팅에 PrometheusRule과 Alertmanager를 사용한다. Grafana Alerting, PagerDuty/Opsgenie, Cloud Monitoring은 사용하지 않는다.
**이유**:
- 기존 kube-prometheus-stack에 포함되어 추가 설치가 필요 없다.
- CRD를 Git으로 선언적으로 관리해 리뷰와 변경 이력을 남긴다.
- Alertmanager의 라우팅과 그루핑 기능을 사용할 수 있다.
- Prometheus 기반 운영 환경에서 널리 검증된 표준 조합이다.

## ADR-006: 외부 진입점은 Gateway API (5장)
**시점**: 2026-07 / **결정**: GKE Gateway API로 외부 진입점을 제공한다. Ingress Controller는 도입하지 않는다.
**이유**:
- GKE가 `gke-l7-regional-external-managed` GatewayClass를 네이티브로 제공한다.
- 별도 NGINX Ingress Controller의 운영 리소스와 관리 부담이 없다.
- HTTPRoute와 Service 참조가 표준 Kubernetes Gateway API 모델을 따른다.
- active Service를 유지해 Argo Rollouts Blue/Green 전환과 자연스럽게 연동된다.

## ADR-007: 무중단 배포는 Blue/Green (5장)
**상태**: ADR-010으로 대체됨
**시점**: 2026-07 / **결정**: Argo Rollouts의 Blue/Green 전략을 사용한다. 기본 Deployment Rolling Update와 Canary는 사용하지 않는다.
**이유**:
- preview 리비전을 active 트래픽과 분리해 검증한 뒤 전환한다.
- `autoPromotionSeconds: 30`으로 검증 시간과 자동 전환을 명시한다.
- 2 replica 규모에서는 일시적인 이중 Pod 리소스 비용을 감당할 수 있다.
- Canary 자동 판정을 위한 메트릭 임계값과 분석 정책은 아직 준비되지 않았다.

## ADR-008: 공유 카운터는 Valkey (6장)
**시점**: 2026-07 / **결정**: Pod 간 공유 상태와 원자적 ID 생성에 Valkey standalone을 사용한다. Redis, Memcached, DragonflyDB는 도입하지 않는다.
**이유**:
- Redis 호환 `INCR` 연산으로 여러 API Pod가 하나의 ID 순서를 안전하게 공유한다.
- BSD 라이선스의 오픈소스 구현이라 Redis 라이선스 변화와 공급자 종속을 피한다.
- 2~3개 e2-medium 노드의 학습 환경에 50m CPU, 64Mi 메모리 요청의 standalone 구성이 적합하다.
- 1Gi PVC로 Pod 재시작 뒤에도 카운터 상태를 유지한다.

## ADR-009: 시크릿 원본은 GCP Secret Manager (6장)
**시점**: 2026-07 / **결정**: Valkey 비밀번호는 GCP Secret Manager에 저장하고 GKE 관리형 CSI Driver와 Workload Identity로 전달한다. 평문 Kubernetes Secret, Sealed Secrets, External Secrets Operator는 사용하지 않는다.
**이유**:
- Workload Identity로 저장형 서비스 계정 키 없이 최소 권한의 GCP Service Account를 사용한다.
- CSI 읽기 전용 파일 마운트로 비밀번호를 Git, 이미지, Pod 환경변수에 복제하지 않는다.
- GKE 관리형 Driver를 사용해 별도 시크릿 동기화 Operator의 설치와 운영 부담을 피한다.
- Secret Manager의 버전 관리와 IAM 감사 경계를 시크릿 원본에 그대로 적용한다.

## ADR-010: 점진 배포는 Argo Rollouts Canary (6장)
**시점**: 2026-07 / **결정**: 5장의 Blue/Green 전략을 Argo Rollouts Canary로 전환한다. Blue/Green 유지와 기본 Rolling Update는 선택하지 않는다.
**이유**:
- 새 버전의 목표 노출을 20%, 50%, 80% 순서로 늘려 한 번의 전체 전환보다 영향 범위를 줄인다.
- 각 단계에 30초 관찰 구간을 두고 문제 발생 시 안정 버전으로 중단할 수 있다.
- 기존 Rollout CRD와 stable/preview Service를 재사용하므로 별도 배포 도구가 필요 없다.
- Blue/Green의 상시 이중 환경보다 점진적으로 리소스를 늘리는 확장 경로를 제공한다.

## ADR-011: 워크로드 배치는 nodeSelector와 역할별 노드풀 (7장)
**시점**: 2026-07 / **결정**: 역할별 Spot 노드풀(api-pool, worker-pool, ops-pool)을 만들고 `cloud.google.com/gke-nodepool` 라벨을 nodeSelector로 지정한다. taint/toleration, nodeAffinity, topologySpreadConstraints 기반 배치는 사용하지 않는다.
**이유**:
- GKE가 노드풀 이름을 라벨로 자동 부여하므로 매니페스트에 nodeSelector 한 줄만 추가하면 된다.
- 단일 존 클러스터에서는 taint/affinity의 표현력이 필요하지 않고 설정 실수 위험만 늘어난다.
- API 워크로드를 전용 노드로 옮겨 ch6에서 발생한 CPU 예약 포화를 해소한다.
- nodeSelector는 배치만 지시하고 다른 Pod의 진입을 막지 못한다는 한계는 감수한다.

## ADR-012: 다수 Application 관리는 App of Apps (7장)
**시점**: 2026-07 / **결정**: `argocd/root-app.yaml`이 `argocd/apps/`를 재귀 감시하는 App of Apps 구조를 사용한다. ApplicationSet과 Application 수동 관리는 사용하지 않는다.
**이유**:
- 디렉터리에 YAML을 추가하면 앱이 등록되는 흐름이라 템플릿 문법 없이 순수 YAML만 쓴다.
- 관리 대상이 5~7개 수준이므로 ApplicationSet의 대량 생성 이점이 크지 않다.
- sync-wave로 플랫폼(1)과 애플리케이션(2)의 설치 순서를 선언적으로 고정한다.
- 이 전환에서 `k8s/monitoring/`을 수동 `kubectl apply` 대상에서 ArgoCD 관리로 편입한다.

## ADR-013: 테넌트 격리는 Namespace 분리와 테넌트별 Rollout (7장)
**시점**: 2026-07 / **결정**: 테넌트를 Namespace로 분리하고 테넌트마다 독립된 Rollout, Service, ServiceAccount, SecretProviderClass를 둔다. 단일 namespace 라벨 격리와 vCluster는 사용하지 않는다.
**이유**:
- Namespace 경계로 RBAC, 리소스 쿼터, 네트워크 정책을 테넌트 단위로 적용할 수 있다.
- App of Apps와 자연스럽게 결합되어 테넌트 추가가 Application YAML 한 개로 끝난다.
- 테넌트별로 배포 시점과 버전을 독립적으로 가져갈 수 있다.
- 격리 대상은 컴퓨트이며 Valkey는 여전히 공유한다. 데이터 격리는 이후 과제로 남긴다.

## ADR-014: 비동기 처리는 Kafka와 Strimzi (8장)
**시점**: 2026-07 / **결정**: 알림 이벤트를 Kafka `notifications` 토픽으로 넘기고, Strimzi Operator가 KRaft 모드 단일 브로커를 관리한다. RabbitMQ, NATS, Valkey Streams는 사용하지 않는다. 앱 쪽 클라이언트는 aiokafka를 쓴다.
**이유**:
- 요청 수신과 실제 처리를 분리해, 처리가 늦어져도 API 응답 시간이 끌려가지 않는다.
- Strimzi가 클러스터와 토픽을 CRD로 노출하므로 매니페스트 그대로 ArgoCD가 관리한다.
- KRaft 모드는 ZooKeeper가 없어 단일 브로커가 e2-standard-2 한 대에 들어간다.
- FastAPI가 asyncio 기반이라 aiokafka의 Consumer를 lifespan 백그라운드 태스크로 그대로 띄울 수 있다.
- 토픽은 테넌트가 공유한다. Consumer Group만 나눈 상태라 서로의 메시지가 보이며, 격리는 이후 과제로 남긴다.

## ADR-015: 분산 트레이싱은 Tempo와 OpenTelemetry (8장)
**시점**: 2026-07 / **결정**: 트레이스를 OTLP gRPC로 Grafana Tempo에 보낸다. Jaeger, Zipkin은 사용하지 않는다.
**이유**:
- 이미 쓰는 Grafana에서 메트릭·로그와 같은 화면으로 트레이스까지 조회한다.
- 인덱스를 따로 두지 않아 Jaeger의 Elasticsearch 백엔드보다 훨씬 가볍고 e2-small 노드에 들어간다.
- OpenTelemetry SDK를 쓰므로 나중에 백엔드를 바꿔도 앱 계측 코드는 그대로 둔다.
- 자동 계측 위에 Valkey·Kafka 구간 span을 얹어 요청 안에서 어디가 느린지 나눠 본다.
- 트레이스 ID 조회 위주라 복잡한 속성 검색은 Jaeger보다 약하다는 점은 감수한다.

## ADR-016: 주기 작업은 Kubernetes CronJob (8장)
**시점**: 2026-07 / **결정**: 헬스체크 같은 주기 작업을 Kubernetes CronJob으로 실행한다. 클러스터 외부 cron과 Argo Workflows는 사용하지 않는다.
**이유**:
- 추가 설치 없이 쓸 수 있고, 매니페스트 한 장이라 ArgoCD가 다른 리소스와 똑같이 관리한다.
- 스케줄 변경이 코드 리뷰와 git 히스토리에 그대로 남는다.
- ops-pool에 배치해 API 노드의 리소스를 건드리지 않는다.
- Argo Workflows는 의존성 있는 다단계 파이프라인용이라 단일 헬스체크에는 과하다.
