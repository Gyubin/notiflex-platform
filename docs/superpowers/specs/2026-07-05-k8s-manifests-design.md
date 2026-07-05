# notiflex-platform: K8s Namespace/Deployment/Service 매니페스트 설계

## 배경

`notiflex-api:v0.1.0` 이미지가 Artifact Registry에 준비됐다. 이를 `notiflex-cluster`(GKE)에 배포하기 위한 Namespace, Deployment, Service 매니페스트를 `k8s/smb/`에 작성한다.

## 요구사항

- `notiflex` 네임스페이스(이미 `kubectl create namespace`로 생성됨)를 선언적으로도 정의한다.
- `notiflex-api:v0.1.0` 이미지를 실행하는 Deployment를 만든다.
- 클러스터 내부에서 접근 가능한 Service를 만든다.

## 결정 사항

### 이미지 참조: 태그(`v0.1.0`), digest 아님

Kubernetes는 Deployment의 pod template에 있는 `image:` 문자열이 바뀔 때만 새 롤아웃을 트리거한다 — 레지스트리에 같은 태그로 새 이미지를 push해도 그 문자열 자체는 안 바뀌므로 감지되지 않는다. 이번 프로젝트에서는 개발 중 `v0.1.0` 태그를 3번 덮어썼는데, 이는 태그 재사용의 위험성을 보여주는 사례였다.

앞으로는 **한 번 배포에 쓴 태그는 절대 재사용하지 않고, 릴리스마다 새 버전 태그로 올린다**는 원칙을 지키기로 했다 (CLAUDE.md 행동규칙에 추가). 이 원칙을 지키면 태그 변경 자체가 Deployment의 `image:` 문자열 변경으로 이어져 정상적으로 롤아웃되고, 향후 CI/CD(GitHub Actions + ArgoCD)의 표준 패턴과도 일치한다. 따라서 digest가 아닌 태그로 참조한다.

### 파일 구성: 리소스별 분리

`k8s/smb/namespace.yaml`, `k8s/smb/deployment.yaml`, `k8s/smb/service.yaml`로 나눈다. 리소스 하나만 바뀔 때 git diff가 명확하고, 향후 ArgoCD 연동 시에도 표준적인 구조다. (단일 파일에 `---`로 합치는 방식과 Kustomize base/overlays 구조도 검토했으나, 전자는 diff 가독성이 떨어지고 후자는 클러스터가 하나뿐인 지금 시점엔 과함.)

## 매니페스트 명세

### Namespace (`namespace.yaml`)

- 이름: `notiflex`
- 이미 `kubectl create namespace`로 존재하는 것과 동일한 리소스를 선언적으로 정의 (idempotent, 재적용해도 안전)

### Deployment (`deployment.yaml`)

- 이름: `notiflex-api`, 네임스페이스: `notiflex`
- `replicas: 2` — 노드가 Spot VM이라 언제든 preempt될 수 있어, 레플리카를 노드 2개에 분산해 가용성을 확보한다
- 이미지: `asia-northeast3-docker.pkg.dev/project-b3c5c78c-8a5c-4e47-9fe/notiflex-platform/notiflex-api:v0.1.0`
- 환경변수 `POD_NAME`을 Downward API(`fieldRef: metadata.name`)로 주입 — `/id` 엔드포인트가 이미 이 값을 읽도록 구현되어 있음
- `readinessProbe`/`livenessProbe`: `GET /health` (포트 8080)
- 리소스: `requests: {cpu: 50m, memory: 64Mi}`, `limits: {cpu: 200m, memory: 128Mi}`
- `securityContext`: `runAsNonRoot: true`, `runAsUser: 1000`, `readOnlyRootFilesystem: true` (Dockerfile 최종 리뷰의 권장사항 반영. 루트 파일시스템을 읽기전용으로 만들어 이전에 지적된 "`/usr/local`이 쓰기 가능" 이슈도 함께 해소)

### Service (`service.yaml`)

- 이름: `notiflex-api`, 네임스페이스: `notiflex`
- `type: ClusterIP`, `port: 8080` → `targetPort: 8080`
- 외부 노출은 이미 클러스터에 활성화된 Gateway API로 이후 별도 작업에서 처리 (이번 스코프 아님)

## 검증 계획

- `kubectl apply -f k8s/smb/`로 세 리소스를 적용
- `kubectl get pods -n notiflex`로 2개 Pod가 `Running`/`Ready` 상태인지 확인
- `readOnlyRootFilesystem: true` 때문에 앱이 예상 못한 쓰기 시도로 크래시하지 않는지 로그로 확인 (실제 리스크이므로 배포 직후 반드시 확인)
- `kubectl port-forward` 또는 클러스터 내부에서 Service를 통해 `/health`, `/id` 호출해 정상 응답 확인

## 스코프 외

- Gateway API를 통한 외부 노출 (HTTPRoute 등, 이후 별도 작업)
- HorizontalPodAutoscaler
- ConfigMap/Secret (현재 앱에 별도 설정값이나 시크릿이 없음)
