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
