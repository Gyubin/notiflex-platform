# Notiflex 온보딩

새로 합류한 엔지니어가 첫 주에 알아야 할 것만 담았습니다. 규칙은 [AGENTS.md](AGENTS.md),
지금의 구조는 [claude-context/architecture.md](claude-context/architecture.md), 결정의 이유는
[docs/architecture-decisions.md](docs/architecture-decisions.md), 여기까지 온 과정은
[JOURNEY.md](JOURNEY.md)에 있습니다. 이 문서는 그 넷으로 가는 입구입니다.

> 기준 시점 2026-07-27 · 이미지 `v0.4.0` · 아래 클러스터 수치는 실제 조회 결과입니다.

---

## 0. 시작하기 전에 — 딱 세 가지

1. **모든 `kubectl`에 `--context notiflex-gke`를 붙입니다.** 이 맥에는 회사 EKS 컨텍스트가
   같이 있고, 개인 GKE 설정은 `~/.kube/config-personal`에 따로 있습니다. 컨텍스트를 빼먹으면
   회사 클러스터를 향해 명령이 나갑니다. 세션 시작할 때 `kubectl config current-context`부터 확인하세요.
2. **클러스터는 평소 꺼져 있습니다.** 비용 때문에 노드풀을 전부 0으로 내려둡니다.
   `kubectl --context notiflex-gke get nodes`가 비어 있으면 중단 상태입니다.
   재개·중단 절차는 AGENTS.md의 "Paused Cluster" 절을 그대로 따르세요. 특히
   **`root-app`은 끌 때 가장 먼저, 켤 때 가장 마지막**입니다.
3. **배포는 `kubectl apply`가 아니라 git 태그로 합니다.** 손으로 고친 건 ArgoCD가 되돌립니다.

---

## 1. 클러스터 현황

`notiflex-cluster` (GKE Standard, Zonal) · `asia-northeast3-a` ·
프로젝트 `project-b3c5c78c-8a5c-4e47-9fe` · Kubernetes 1.35.5-gke.1241004

### 노드풀 — 전부 Spot VM, 5노드

| 노드풀 | 머신 타입 | 수 | 여기 올라가는 것 |
|---|---|---:|---|
| `default-pool` | e2-medium | 2 | ArgoCD, 관측 스택(Prometheus·Grafana·Loki·Fluent Bit), Argo Rollouts |
| `api-pool` | e2-medium | 1 | notiflex API ×2, enterprise API ×1, Valkey |
| `worker-pool` | e2-standard-2 | 1 | Strimzi operator, Kafka 브로커, entity-operator |
| `ops-pool` | e2-small | 1 | Tempo, 헬스체크 CronJob |

배치는 `nodeSelector: cloud.google.com/gke-nodepool: <풀 이름>`으로 합니다. GKE가 자동으로
붙여주는 라벨이라 커스텀 라벨(`role`, `workload` 등)은 만들지 않습니다. 커스텀 키를 쓰면
Pod이 영원히 Pending에 머뭅니다. Strimzi처럼 `nodeSelector` 필드가 없는 CRD는 같은 라벨 키에
`nodeAffinity`를 씁니다.

> **`ops-pool`은 거의 꽉 찼습니다.** allocatable이 940m CPU / 1391Mi인데 시스템 DaemonSet만으로
> CPU 56% · 메모리 75%가 예약돼 있습니다. 여기 뭔가 올리기 전에 반드시 `kubectl top`과 노드의
> `Allocated resources`를 먼저 보세요.

### 네임스페이스별 워크로드

| 네임스페이스 | Pod | 무엇 |
|---|---:|---|
| `kube-system` | 57 | GKE 시스템 (DaemonSet 다수) |
| `monitoring` | 17 | Prometheus, Grafana, Alertmanager, Loki, Fluent Bit ×5, Tempo, node-exporter ×5, kube-state-metrics |
| `argocd` | 7 | server, application-controller, repo-server, redis, dex, applicationset, notifications |
| `gmp-system` | 6 | GKE 관리형 Prometheus (기본 활성, 우리 스택과 별개) |
| `notiflex` | 4 | API ×2 (SMB 테넌트), Valkey, 헬스체크 Job |
| `kafka` | 3 | Strimzi operator, 브로커(dual-role), entity-operator |
| `enterprise` | 1 | API ×1 (Enterprise 테넌트) |
| `argo-rollouts` | 1 | Rollouts 컨트롤러 |

---

## 2. 저장소 구조

```
app/                   FastAPI 소스 + 테스트 + Dockerfile + uv.lock
k8s/
  smb/                 SMB 테넌트 — Rollout, Service(stable/preview), Gateway, HTTPRoute,
                       PDB, ServiceMonitor, SecretProviderClass, 헬스체크 CronJob
  enterprise/          Enterprise 테넌트 — Rollout, Service, ServiceAccount, SecretProviderClass
  monitoring/          Grafana 데이터소스·대시보드 ConfigMap, PrometheusRule
  kafka/               Strimzi Kafka / KafkaNodePool / KafkaTopic CR
helm-values/           Helm values 6개 (kube-prometheus, loki, fluent-bit, valkey, strimzi, tempo)
argocd/
  root-app.yaml        App of Apps 루트 — 유일하게 손으로 apply하는 파일
  apps/                Application 4개. 여기에 YAML을 넣으면 새 앱이 등록된다
.github/workflows/     CI 파이프라인
command-guardrails/    되돌리기 어려운 작업의 절차서 (아래 4번 참조)
claude-context/        지금의 아키텍처 스냅샷
docs/                  ADR 16건, 에이전트 공통 작업 절차
AGENTS.md              모든 코딩 에이전트가 따르는 정본 규칙 (CLAUDE.md는 이걸 가리키는 어댑터)
JOURNEY.md             진행 기록 + 도구 선택 이유 + 트러블슈팅 이력
```

**`argocd/` 최상위에는 `root-app.yaml` 말고 다른 Application을 두지 마세요.** 루트가 자기 자신을
sync 대상으로 잡습니다.

---

## 3. 접근 방법

### API (외부)

```bash
curl http://35.216.8.57/health     # {"status":"ok"}
curl http://35.216.8.57/version    # 앱 버전 + 런타임 + 응답한 Pod 이름
curl http://35.216.8.57/id         # Valkey INCR로 만든 전역 ID + Kafka 발행 여부
curl http://35.216.8.57/notifications  # 이 Pod의 Consumer가 받은 메시지
```

Regional external Gateway가 붙인 IP입니다. Gateway를 다시 만들면 IP가 바뀝니다.

### ArgoCD UI

```bash
kubectl --context notiflex-gke -n argocd port-forward svc/argocd-server 8080:443
# https://localhost:8080  (인증서 경고는 무시)

# 초기 admin 비밀번호
kubectl --context notiflex-gke -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath='{.data.password}' | base64 -d; echo
```

### Grafana — 메트릭·로그·트레이스가 다 여기 있습니다

```bash
kubectl --context notiflex-gke -n monitoring port-forward svc/kube-prometheus-grafana 3000:80
# http://localhost:3000  (admin / kube-prometheus-grafana Secret의 admin-password)
```

| 데이터소스 | 쓰는 법 | 답하는 질문 |
|---|---|---|
| Prometheus (기본) | `rate(http_requests_total[5m])`, `kube_pod_container_status_restarts_total` | 얼마나 · 몇 번 · 언제부터 느려졌나 |
| Loki | `{namespace="notiflex"}`, `{namespace="notiflex"} \|= "ERROR"` | 그때 무슨 일이 있었나 |
| Tempo (`uid: tempo`) | Search 탭에서 서비스·기간으로 조회, 또는 TraceID 직접 입력 | 요청 하나가 어디에 시간을 썼나 |

> 기본 데이터소스(`isDefault: true`)는 **Prometheus 하나뿐이어야 합니다.** 둘 이상이면
> Grafana가 기동에 실패합니다. 데이터소스 `uid`도 반드시 고정하세요 — 비워두면 Grafana가
> 임의 값을 만들고, 그걸 참조하던 대시보드가 재프로비저닝 때 깨집니다.

---

## 4. 배포 플로우

배포의 시작은 코드 push가 아니라 **릴리스 태그**입니다. main에 코드만 밀면 아무 일도 안 일어납니다.

```
git tag v0.4.1 && git push origin v0.4.1
        │
        ▼
[GitHub Actions]  .github/workflows/ci.yaml   (태그 v* 에만 트리거)
   1. uv sync --frozen && pytest
   2. docker build (APP_VERSION=태그 주입) → Artifact Registry push
   3. k8s/smb/rollout.yaml + k8s/enterprise/rollout.yaml 의 image 태그 갱신
   4. main 에 "ci: deploy notiflex-api v0.4.1" 커밋 & push
   인증: Workload Identity Federation — 저장된 SA 키 없음
        │
        ▼
[ArgoCD]  auto-sync (prune + selfHeal), 폴링 3분
        │
        ▼
[Argo Rollouts]  Canary: 20% → (30초) → 50% → (30초) → 80% → (30초) → 100%
```

진행 상황 보기:

```bash
kubectl argo rollouts get rollout notiflex-api -n notiflex --context notiflex-gke --watch
```

> 플러그인 명령은 **플래그를 플러그인 이름 뒤에** 놓아야 합니다.
> `kubectl --context notiflex-gke argo rollouts ...`는
> `flags cannot be placed before plugin name`으로 실패합니다.

### 알아둘 함정 두 개

- **태그를 민 뒤 문서를 push하면 non-fast-forward로 거절됩니다.** CI가 `main`에 먼저 커밋하기
  때문입니다. `git fetch && git rebase --autostash origin/main`으로 재배치하세요. force push는
  쓰지 않습니다. (이 문제는 ch5와 ch8에서 두 번 겪었습니다.)
- **두 테넌트가 같은 이미지를 씁니다.** CI가 매니페스트 두 개를 함께 고칩니다. 테넌트마다 다른
  버전을 배포하려면 `ci.yaml`의 이 단계를 먼저 갈라야 합니다.

### ArgoCD Application (App of Apps)

```
root-app  (수동 apply, argocd/apps/ 를 recurse 감시)
├── notiflex-monitoring   wave 1  → k8s/monitoring/   → monitoring
├── notiflex-kafka        wave 1  → k8s/kafka/        → kafka
├── notiflex-smb          wave 2  → k8s/smb/          → notiflex
└── notiflex-enterprise   wave 2  → k8s/enterprise/   → enterprise
```

Helm이 소유해 GitOps 밖에 있는 것: kube-prometheus-stack, Loki, Fluent Bit, Valkey,
Strimzi operator, Tempo. values는 `helm-values/`에 커밋돼 있지만 릴리스 자체는 Helm이 쥐고 있습니다.

### 되돌리기 어려운 작업

Kafka 토픽 삭제, CronJob 수동 실행, 테넌트 네임스페이스 삭제는 `command-guardrails/`의
해당 파일을 **먼저 읽고** 하세요. 절차서는 지우지 않고 계속 둡니다.

---

## 5. 자주 묻는 것

**Q. Canary가 이상하게 나갑니다. 되돌리려면?**

```bash
kubectl argo rollouts abort notiflex-api -n notiflex --context notiflex-gke
kubectl argo rollouts undo notiflex-api -n notiflex --context notiflex-gke   # 이전 리비전으로
```

`abort`는 stable로 트래픽을 되돌리고 canary를 멈춥니다. 다만 **ArgoCD selfHeal이 Git 상태를
다시 밀어넣습니다.** 진짜 롤백은 Git에서 이전 태그로 되돌린 커밋을 push하는 것입니다.
급하면 해당 Application의 auto-sync를 잠깐 끄고 abort하세요.

**Q. 로그를 어디서 봅니까?**

Grafana → Explore → Loki:

```logql
{namespace="notiflex"}                          # SMB 테넌트 전체
{namespace="notiflex"} |= "ERROR"               # 에러만
{namespace="enterprise"}                        # Enterprise 테넌트
```

앱이 남기는 로그가 안 보이면 `logging.basicConfig`가 빠진 겁니다. uvicorn은 자기 로거만
설정하고 root 로거는 핸들러 없이 둬서, INFO 로그가 조용히 사라집니다 (ch8에서 겪음).

**Q. 특정 요청이 왜 느렸는지 보려면?**

Grafana → Explore → Tempo → Search에서 서비스·기간으로 찾거나, TraceID를 직접 넣습니다.
`GET /id` 트레이스를 열면 `valkey.incr`와 `kafka.publish` 자식 span으로 구간이 갈립니다
(측정 예: 전체 6.80ms 중 Valkey 0.80ms, Kafka 2.96ms).

테넌트는 `service.namespace` 속성에 실려 있어 smb / enterprise를 나눠 볼 수 있습니다.
`/health`와 `/metrics`는 트레이싱에서 제외했습니다 — 프로브가 `/id`의 246배를 두드려서
넣어두면 검색 결과가 헬스체크로 뒤덮입니다.

**Q. Kafka 토픽을 추가하려면?**

`k8s/kafka/`에 `KafkaTopic` CR을 하나 더 만들고 커밋하면 `notiflex-kafka` Application이
동기화합니다. 토픽 **삭제**는 데이터가 사라지므로 `command-guardrails/kafka-topic-delete.md`를
먼저 읽으세요.

토픽 상태 확인:

```bash
kubectl --context notiflex-gke get kafkatopic -n kafka
# notifications  notiflex-kafka  3파티션  RF 1  Ready=True
```

Kafka 버전을 올릴 때는 **먼저 operator가 지원하는 목록을 확인**하세요. 지원하지 않는 값을 쓰면
경고 없이 클러스터가 죽습니다.

```bash
helm template strimzi/strimzi-kafka-operator | grep STRIMZI_KAFKA_IMAGES
```

**Q. 새 테넌트를 추가하려면?**

세 군데를 손대야 합니다. 하나라도 빠지면 조용히 실패합니다.

1. `k8s/<tenant>/`에 Rollout·Service·ServiceAccount·SecretProviderClass
2. `argocd/apps/notiflex-<tenant>.yaml` (`CreateNamespace=true`). root-app이 알아서 감지합니다
3. **GCP 쪽 Workload Identity 바인딩** —
   `...svc.id.goog[<namespace>/notiflex-api]`를 `roles/iam.workloadIdentityUser`로 추가.
   이걸 빠뜨리면 Pod은 뜨는데 Secret Manager만 못 읽어서 기동에 실패합니다 (ch7에서 겪음)

그리고 CI(`ci.yaml`)의 이미지 태그 갱신 대상에 새 매니페스트를 추가하세요. ch7.4에서 이걸
빠뜨려서 enterprise 테넌트가 한동안 옛 이미지로 방치됐습니다.

**Q. 알림은 어디서 확인합니까?**

```bash
kubectl --context notiflex-gke -n monitoring port-forward \
  svc/kube-prometheus-kube-prome-alertmanager 9093:9093
# http://localhost:9093
```

규칙은 `k8s/monitoring/pod-restart-alert.yaml` 하나뿐이고 (Pod 재시작 감지),
**외부 채널(Slack·이메일)은 아직 연결돼 있지 않습니다.** 기본 null receiver로만 갑니다.
PrometheusRule에는 `release: kube-prometheus` 라벨이 반드시 있어야 Prometheus가 집어갑니다.

**Q. 시크릿은 어떻게 다룹니까?**

원본은 GCP Secret Manager에 있고, GKE 관리형 CSI Driver가
`/mnt/secrets/valkey-password`에 읽기 전용 파일로 마운트합니다.
**Git이나 환경변수에 비밀번호를 복제하지 마세요.** SA 키도 만들지 않습니다 (조직 정책으로 막혀
있기도 하고, WIF로 이미 키 없이 됩니다).

---

## 6. 알고 있어야 할 한계

지금 구조가 해결하지 못한 것들입니다. 모르고 있다가 놀라는 게 제일 나쁩니다.

- **테넌트 격리는 컴퓨트에만 적용됩니다.** 네임스페이스는 갈렸지만 데이터는 공유합니다.
  두 테넌트가 같은 Valkey 카운터를 쓰고, 같은 `notifications` 토픽을 읽습니다.
  Consumer Group을 나눈 건 격리가 아니라 "각자 전량을 독립적으로 읽는" 것이라,
  **enterprise가 smb의 메시지까지 전부 받습니다** (측정으로 확인). 진짜 격리는 테넌트별 토픽이나
  Kafka ACL, 그리고 테넌트별 키 접두사나 별도 Valkey 인스턴스가 필요합니다.
- **메시지 키가 테넌트 이름이라** 한 테넌트의 메시지는 항상 같은 파티션 → 같은 Consumer로 갑니다.
  순서는 보장되지만 테넌트 안에서 replica를 늘려도 처리량이 늘지 않습니다.
- **Canary 가중치가 거칩니다.** replica가 2개뿐이라 20%/50%/80%가 파드 단위로 뭉개집니다.
  진짜 트래픽 비율을 원하면 replica를 늘리거나 트래픽 라우터를 붙여야 합니다.
- **`api-pool`이 노드 1대**입니다. `notiflex-api` PDB가 `minAvailable: 1`이라 그 노드를 드레인하려면
  PDB를 잠깐 0으로 낮춰야 합니다.
- **관측 스택 6개가 Helm 소유**라 GitOps 밖에 있습니다. values는 Git에 있지만 릴리스는 아닙니다.
- **Kafka 브로커가 1대**이고 controller를 겸합니다 (KRaft). 학습용 구성이고 HA가 없습니다.

---

## 7. 로컬 개발

```bash
cd app
uv sync                              # 의존성 설치 (Python 3.13 고정)
uv run pytest                        # 테스트
uv run uvicorn main:app --port 8080  # 로컬 실행
```

`KAFKA_BROKER`와 `VALKEY_ADDR`가 없으면 메시징·캐시 없이 뜹니다. 테스트와 로컬 실행은 이 경로입니다.

이미지 빌드는 평소 CI가 합니다. 로컬 일회성 빌드가 필요하면 **Cloud Build를 쓰세요** —
맥은 arm64, GKE 노드는 amd64라 로컬 `docker build` 결과물은 클러스터에서 안 돕니다.

```bash
gcloud builds submit app/ \
  --tag=asia-northeast3-docker.pkg.dev/project-b3c5c78c-8a5c-4e47-9fe/notiflex-platform/notiflex-api:<버전> \
  --service-account=projects/project-b3c5c78c-8a5c-4e47-9fe/serviceAccounts/notiflex-cloudbuild@project-b3c5c78c-8a5c-4e47-9fe.iam.gserviceaccount.com \
  --default-buckets-behavior=REGIONAL_USER_OWNED_BUCKET
```

**배포한 이미지 태그는 절대 재사용하지 않습니다.** `latest`도 쓰지 않습니다.

---

## 8. 막혔을 때

[JOURNEY.md](JOURNEY.md)의 트러블슈팅 이력을 먼저 보세요. 38건이 쌓여 있고, 대부분
"한 번 데인 뒤에 적어둔 것"이라 같은 증상이면 답이 그대로 있습니다. 자주 걸리는 것 몇 개:

| 증상 | 원인 |
|---|---|
| Pod이 계속 Pending | nodeSelector 라벨 키가 `cloud.google.com/gke-nodepool`이 아님 |
| Pod은 뜨는데 Secret Manager만 못 읽음 | 그 네임스페이스의 Workload Identity 바인딩 누락 |
| 앱 로그가 하나도 안 보임 | `logging.basicConfig` 누락 (uvicorn 로그만 나옴) |
| Grafana가 기동 실패 | `isDefault: true` 데이터소스가 둘 이상 |
| 대시보드가 데이터소스를 못 찾음 | 데이터소스 `uid`를 고정하지 않음 |
| 노드 드레인이 안 끝남 | ArgoCD selfHeal이 replicas를 되돌리고 PDB가 드레인을 막음 |
| Kafka 클러스터가 안 뜸 | operator가 지원하지 않는 Kafka 버전 |
| `kubectl argo rollouts` 실패 | 플래그를 플러그인 이름 앞에 둠 |

---

이 문서는 저장소의 코드·매니페스트·커밋 히스토리와 실제 클러스터 조회 결과로 작성했습니다.
구조가 바뀌면 `claude-context/architecture.md`와 함께 갱신하세요.
