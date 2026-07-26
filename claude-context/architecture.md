# Notiflex 아키텍처 스냅샷

> **기준 시점: 9장 완료 (2026-07-27)** · 이미지 `v0.4.0`
> 9장은 회고·문서 챕터라 인프라 구조는 8장 완료 시점과 같다. 재개 후 실측으로 확인했다.
> 이 문서는 "지금 어떻게 동작하는가"만 담는다. 구조가 바뀌면 이 파일을 갱신한다.

## 문서의 역할

이 저장소는 참조 문서를 층으로 나눈다. 섞이면 어느 것도 믿을 수 없게 된다.

| 문서 | 담는 것 | 성격 |
|------|---------|------|
| `AGENTS.md` | 프로젝트 규칙·제약·작업 계약 (`CLAUDE.md`는 이 파일을 가리키는 얇은 어댑터) | 매 대화 자동 로드 |
| `claude-context/architecture.md` | **지금의** 아키텍처 스냅샷 — 이 문서 | 현재 상태 한눈 보기 |
| `docs/architecture-decisions.md` | 결정과 그 이유의 누적 기록 (ADR-001~016) | 과거, 덧붙이기만 함 |
| `JOURNEY.md` | 진행 이력과 트러블슈팅 | 겪은 일, 덧붙이기만 함 |
| `README.md` · `ONBOARDING.md` | 사람이 읽는 입구 | 위 넷을 요약해 가리킴 |

`AGENTS.md`는 "이렇게 해라", 이 문서는 "지금 이렇게 되어 있다", ADR은 "그때 왜 그렇게 정했나",
`JOURNEY.md`는 "오는 길에 무슨 일이 있었나"다. 결정의 **이유**는 ADR에만 쓰고 여기 옮기지 않는다.

마지막 두 문서는 고유한 내용을 갖지 않고 나머지를 요약할 뿐이지만, 그래서 갱신에서 빠지기 쉽다.
실제로 `README.md`가 6장 상태로 두 챕터를 방치됐다. 문서 갱신 때 명시적으로 확인한다.

---

## 클러스터 토폴로지

| 항목 | 값 |
|------|-----|
| 클러스터 | `notiflex-cluster` (GKE Standard, Zonal) |
| 버전 | 1.35.5-gke.1241004 |
| 리전 / 존 | `asia-northeast3` / `asia-northeast3-a` |
| 프로젝트 | `project-b3c5c78c-8a5c-4e47-9fe` |
| kubectl 컨텍스트 | `notiflex-gke` (모든 명령에 `--context notiflex-gke` 필수) |
| Workload Identity 풀 | `project-b3c5c78c-8a5c-4e47-9fe.svc.id.goog` |
| 외부 IP | `35.216.8.57` (Regional external Gateway) |

### 노드풀 (전부 Spot, 총 5노드)

| 노드풀 | 머신 타입 | 수 | 디스크 | 올라가는 것 |
|--------|----------|----|--------|-----------|
| `default-pool` | e2-medium | 2 | pd-balanced 30GB | ArgoCD, 관측 스택, Argo Rollouts, kube-system |
| `api-pool` | e2-medium | 1 | pd-standard 50GB | notiflex ×2, enterprise ×1, Valkey |
| `worker-pool` | e2-standard-2 | 1 | pd-standard 50GB | Strimzi operator, Kafka 브로커, entity-operator |
| `ops-pool` | e2-small | 1 | pd-standard 50GB | Tempo, 헬스체크 CronJob |

배치는 `nodeSelector: cloud.google.com/gke-nodepool: <풀 이름>`으로 한다. GKE가 자동으로 붙이는
라벨이며, **커스텀 라벨은 만들지 않는다.** Strimzi처럼 `nodeSelector` 필드가 없는 CRD는 같은 라벨 키에
`nodeAffinity`를 쓴다.

> `ops-pool`은 여유가 거의 없다. allocatable이 940m CPU / 1391Mi인데 시스템 DaemonSet만으로
> CPU 56% · 메모리 75%가 예약된 상태다. 여기에 뭔가 더 올리기 전에 반드시 실제 requests를 확인한다.

### 활성화된 GKE 기능

- Workload Identity (모든 노드풀 `--workload-metadata=GKE_METADATA`)
- 관리형 Secret Manager CSI Driver (`secrets-store-gke.csi.k8s.io`)
- Gateway API (standard 채널)
- `default` 네트워크의 `proxy-only-subnet` (`172.16.0.0/23`) — Regional external Gateway 전제 조건

---

## 컴포넌트 흐름

```text
 인터넷
   │
   ▼
[Gateway  notiflex-gateway]  35.216.8.57  (gke-l7-regional-external-managed)
   │  HTTPRoute notiflex-route  "/" → notiflex-api:8080
   ▼
[Service  notiflex-api]  ClusterIP :8080          [Service notiflex-api-preview]
   │        (stable)                                        (canary)
   ▼                                                            │
[Rollout  notiflex-api]  replicas 2, api-pool  ◄────────────────┘
   │        Canary 20% → 50% → 80% → 100% (각 30초 pause)
   │
   ├──► [Valkey]  valkey-primary.notiflex:6379
   │       /id 의 INCR. 비밀번호는 CSI 파일 마운트로 읽는다.
   │
   ├──► [Secret Manager CSI]  /mnt/secrets/valkey-password  (읽기 전용)
   │       ServiceAccount notiflex-api → GCP SA notiflex-secrets (Workload Identity)
   │
   ├──► [Kafka]  notiflex-kafka-kafka-bootstrap.kafka:9092
   │       Producer: /id 가 notifications 토픽에 발행
   │       Consumer: 같은 파드의 백그라운드 태스크가 구독 (Group: notiflex-<tenant>)
   │
   └──► [Tempo]  tempo.monitoring:4317 (OTLP gRPC)
           요청마다 서버 span + valkey.incr / kafka.publish 자식 span

[CronJob  notiflex-healthcheck]  ops-pool, */5 * * * *
   └──► Service DNS 경유로 /health 호출 (파드 안이 아니라 밖에서 확인)
```

**핵심 데이터 흐름**: `/id` 요청 → Valkey `INCR` → Kafka `notifications` 발행 → Consumer 로그

---

## 배포 파이프라인

```text
git tag vX.Y.Z && git push origin vX.Y.Z
   │
   ▼
[GitHub Actions]  .github/workflows/ci.yaml   (태그 v* 에만 트리거)
   │  1. uv sync --frozen && pytest
   │  2. docker build (APP_VERSION=태그 주입) → Artifact Registry push
   │  3. k8s/smb/rollout.yaml + k8s/enterprise/rollout.yaml 의 image 태그 갱신
   │  4. main 에 "ci: deploy notiflex-api vX.Y.Z" 커밋 & push
   │     인증: Workload Identity Federation (저장된 SA 키 없음)
   ▼
[ArgoCD]  auto-sync (prune + selfHeal), 기본 폴링 3분
   │       급하면 argocd.argoproj.io/refresh=hard 어노테이션
   ▼
[Argo Rollouts]  Canary 단계 진행 → 승격
```

주의할 점 둘:

- CI가 `main`에 먼저 커밋하므로, 태그를 민 뒤 문서를 푸시하려면 `git fetch` → `git rebase --autostash origin/main`이 필요하다. 그냥 push 하면 non-fast-forward로 거절된다.
- 두 테넌트가 같은 이미지를 쓰므로 CI가 두 매니페스트를 함께 갱신한다. 테넌트마다 다른 버전을 배포하려면 이 단계를 먼저 갈라야 한다.

### ArgoCD 애플리케이션 (App of Apps)

```text
root-app  (수동 apply, argocd/apps/ 를 recurse 감시)
├── notiflex-monitoring   wave 1  → k8s/monitoring/   → monitoring
├── notiflex-kafka        wave 1  → k8s/kafka/        → kafka
├── notiflex-smb          wave 2  → k8s/smb/          → notiflex
└── notiflex-enterprise   wave 2  → k8s/enterprise/   → enterprise
```

`argocd/apps/`에 Application YAML을 넣으면 새 앱이 등록된다. sync-wave는 1이 플랫폼, 2가 애플리케이션이다.
`argocd/` 최상위에는 `root-app.yaml` 외에 다른 Application을 두지 않는다 (루트가 자기 자신을 sync하게 된다).

Helm이 소유해 GitOps 밖에 있는 것: kube-prometheus-stack, Loki, Fluent Bit, Valkey, Strimzi operator, Tempo.
values 파일은 `helm-values/`에 커밋되어 있지만 릴리스 자체는 Helm이 관리한다.

---

## 관측 가능성

네 층이 각각 다른 질문에 답한다.

| 도구 | 답하는 질문 | 접근 |
|------|-----------|------|
| **Prometheus** | 얼마나 · 몇 번 · 언제부터 느려졌나 | `/metrics` 스크레이프 (ServiceMonitor, `release: kube-prometheus`) |
| **Loki + Fluent Bit** | 그때 무슨 일이 있었나 | Grafana LogQL `{namespace="notiflex"}` |
| **Tempo** | 요청 하나가 어디에 시간을 썼나 | OTLP gRPC 4317 수집 / HTTP 3200 조회 |
| **Alertmanager** | 문제가 났을 때 알려주기 | `pod-restart-alert` PrometheusRule (외부 채널 미연결) |

Grafana 접속:

```bash
kubectl --context notiflex-gke -n monitoring port-forward svc/kube-prometheus-grafana 3000:80
```

주의할 점:

- 기본 데이터소스(`isDefault: true`)는 **Prometheus 하나뿐이어야 한다.** 둘 이상이면 Grafana가 기동에 실패한다.
- 데이터소스 `uid`는 고정한다 (`prometheus`, `tempo`). 비워두면 Grafana가 임의로 만들고, 그걸 참조하던 대시보드가 재프로비저닝 때 깨진다.
- 트레이싱은 `/health`와 `/metrics`를 제외한다. 프로브가 `/id`의 246배를 두드려서, 넣어두면 검색 결과가 헬스체크로 뒤덮인다.
- 앱은 `logging.basicConfig`로 root 로거를 직접 설정한다. 이게 없으면 uvicorn 액세스 로그만 나오고 앱이 남기는 로그는 전부 사라진다.

---

## 네임스페이스별 워크로드

| 네임스페이스 | 주요 워크로드 | 비고 |
|-------------|-------------|------|
| `notiflex` | Rollout `notiflex-api` ×2, `valkey-primary`, Gateway/HTTPRoute, CronJob `notiflex-healthcheck` | SMB 테넌트. Valkey가 여기에만 있다 |
| `enterprise` | Rollout `notiflex-api` ×1 | Enterprise 테넌트. Valkey는 `notiflex`의 것을 FQDN으로 쓴다 |
| `kafka` | `strimzi-cluster-operator`, `notiflex-kafka-dual-role-0`, `notiflex-kafka-entity-operator` | KRaft 단일 브로커가 controller 겸용 |
| `monitoring` | Prometheus, Grafana, Alertmanager, Loki, Fluent Bit, Tempo, kube-state-metrics | Helm 소유, 매니페스트는 ArgoCD |
| `argocd` | ArgoCD v3.4.5 (server, controller, repo, redis, dex, applicationset, notifications) | |
| `argo-rollouts` | Argo Rollouts v1.9.1 컨트롤러 | |

### 테넌트 구조와 그 한계

네임스페이스가 가른 것은 **컴퓨트뿐이다.** 데이터는 아직 공유한다.

- **Valkey**: 두 테넌트가 같은 `notiflex:id` 카운터를 쓴다. `/id`가 테넌트를 넘나들며 증가한다.
- **Kafka**: 같은 `notifications` 토픽을 Consumer Group만 나눠 쓴다. 그룹을 나눈다는 건 "각자 전량을
  독립적으로 읽는다"는 뜻이라, enterprise가 smb의 메시지까지 전부 읽는다 (측정으로 확인).
  메시지 키의 테넌트 이름은 파티션 배분을 정할 뿐 구독 범위와 무관하다.
- 키를 테넌트로 고정한 탓에 한 테넌트의 메시지는 항상 한 파티션 → 한 Consumer로 간다. 순서는
  보장되지만 테넌트 안에서 replica를 늘려도 처리량이 늘지 않는다.

진짜 격리는 테넌트별 키 접두사 / 별도 Valkey 인스턴스, 그리고 테넌트별 토픽이나 Kafka ACL이 필요하다.
둘 다 미해결 과제다.

테넌트를 추가할 때 잊기 쉬운 것: GCP 쪽 Workload Identity 바인딩은 네임스페이스 단위라
`...svc.id.goog[<namespace>/notiflex-api]`를 `roles/iam.workloadIdentityUser`로 따로 추가해야 한다.
빠뜨리면 파드는 뜨는데 Secret Manager만 못 읽는다.
