# notiflex-platform

이 파일은 이 저장소에서 작업하는 AI 어시스턴트를 위한 컨텍스트입니다.

## 프로젝트 개요

- notiflex-platform: B2B 알림 SaaS 플랫폼, Kubernetes 운영환경 구축 실습 프로젝트
- Python으로 작성되는 백엔드 서비스
- Kubernetes(K8s)에 배포되며, Docker 이미지는 GCP Artifact Registry에 저장
- 참고: 원본 교재는 Go 기준으로 작성되어 있음. 이 저장소는 Python으로 대체해서 진행 중이므로, 교재의 Go 코드/설정을 볼 때는 Python으로 옮겨서 구현한다.

## 인프라

- **오케스트레이션**: GKE Standard (Zonal)
- **CI/CD**: GitHub Actions + ArgoCD

## 디렉토리 구조

- `app/` — Python 소스 코드
- `k8s/smb/` — K8s 매니페스트 (배포, 서비스, ServiceMonitor 등, ArgoCD가 동기화)
- `k8s/monitoring/` — 모니터링 관련 매니페스트 (Grafana 대시보드/데이터소스 ConfigMap, PrometheusRule). ArgoCD 대상이 아니라 `kubectl apply`로 적용
- `helm-values/` — Helm 차트 values (kube-prometheus-stack, Loki, Fluent Bit)
- `.github/workflows/` — CI 파이프라인

## GCP 설정

- Project ID: `project-b3c5c78c-8a5c-4e47-9fe`
- Project Name: `gyubin-gitaiops-project`
- Region: `asia-northeast3` (Seoul)
- Zone: `asia-northeast3-a`
- Artifact Registry: `asia-northeast3-docker.pkg.dev/project-b3c5c78c-8a5c-4e47-9fe/notiflex-platform`

## GKE 클러스터

- 클러스터 이름: `notiflex-cluster` (Zonal, `asia-northeast3-a`)
- 노드: e2-medium x 2 (Spot VM), 디스크 30GB
- Gateway API: 활성화 (standard channel)
- kubectl context: `notiflex-gke` (원래 이름 `gke_project-b3c5c78c-8a5c-4e47-9fe_asia-northeast3-a_notiflex-cluster`을 [kubectx](https://github.com/ahmetb/kubectx)로 별칭 지정)
- 네임스페이스: `notiflex` (생성 완료)
- kubeconfig 파일 분리: 회사 AWS EKS 설정은 `~/.kube/config`에 그대로 두고, 이 GKE 클러스터는 `~/.kube/config-personal`로 분리. 쉘 프로필(`~/.zshrc`)에서 `export KUBECONFIG="$HOME/.kube/config:$HOME/.kube/config-personal"`로 두 파일을 병합해서 사용 (물리적으로는 분리, `kubectl`/`kubectx`에서는 하나로 보임). 다른 컴퓨터에서 작업할 경우 동일하게 `kubectl config view --minify --flatten --context=<원래 gcloud 컨텍스트명> > ~/.kube/config-personal` 후 원본에서 `kubectl config delete-context/-cluster/-user`로 제거하고 위 `KUBECONFIG` 설정을 추가할 것

## 임시 중단/재개 (비용 절감)

- 클러스터를 잠시 안 쓸 때는 삭제하지 않고 노드 풀을 0으로 리사이즈한다 (Deployment/Service 등 설정은 컨트롤 플레인에 남아 있으므로 재개 시 그대로 복원됨. Zonal 클러스터 1개는 관리비 무료 티어라 노드가 0이면 비용이 거의 없음).
- **중단** (PDB가 노드 드레인을 막지 않도록 replicas를 먼저 0으로):
  ```bash
  kubectl --context notiflex-gke scale deployment notiflex-api -n notiflex --replicas=0
  gcloud container clusters resize notiflex-cluster --node-pool default-pool \
    --num-nodes 0 --zone asia-northeast3-a \
    --project project-b3c5c78c-8a5c-4e47-9fe --quiet
  ```
- **재개**:
  ```bash
  gcloud container clusters resize notiflex-cluster --node-pool default-pool \
    --num-nodes 2 --zone asia-northeast3-a \
    --project project-b3c5c78c-8a5c-4e47-9fe --quiet
  kubectl --context notiflex-gke scale deployment notiflex-api -n notiflex --replicas=2
  ```

## 로컬 개발 (uv)

- 로컬 의존성/가상환경은 **uv**로 관리한다 (`app/pyproject.toml` + `app/uv.lock`, `app/.python-version=3.13`). `requirements*.txt`는 폐기.
- Python은 이미지 베이스(`python:3.13-slim`)에 맞춰 **3.13**으로 고정한다 (dev/운영 정합, `/version`의 runtime으로 실증됨).
- 설치·테스트: `cd app && uv sync && uv run pytest`.

## 이미지 빌드

- 평상시 빌드는 **CI(GitHub Actions)가 담당**한다 (아래 "CI/CD" 참조). 아래 수동 빌드는 로컬 일회성/디버그용 fallback이다.
- `app/Dockerfile`은 `uv sync --frozen` 기반 멀티스테이지(비루트 `appuser`). 앱 버전은 빌드 시 `--build-arg APP_VERSION=<git tag>`로 주입되어 `/version`이 반환한다.
- 로컬에서 직접 빌드할 땐 로컬 Docker 대신 **Cloud Build**를 쓴다 (M-시리즈 맥은 arm64라 GKE 노드(amd64)와 안 맞음. Cloud Build는 GCP 서버(amd64)에서 빌드). 전용 SA `notiflex-cloudbuild`(`roles/cloudbuild.builds.builder`) 사용:
  ```bash
  gcloud builds submit app/ \
    --tag=asia-northeast3-docker.pkg.dev/project-b3c5c78c-8a5c-4e47-9fe/notiflex-platform/notiflex-api:<버전> \
    --service-account=projects/project-b3c5c78c-8a5c-4e47-9fe/serviceAccounts/notiflex-cloudbuild@project-b3c5c78c-8a5c-4e47-9fe.iam.gserviceaccount.com \
    --default-buckets-behavior=REGIONAL_USER_OWNED_BUCKET
  ```
- `app/.gcloudignore`로 `.venv/`, `__pycache__/` 등을 업로드 대상에서 제외한다.

## CI/CD (릴리스 주도)

- **트리거**: `git tag vX.Y.Z && git push origin vX.Y.Z` → GitHub Actions(`.github/workflows/ci.yaml`) 실행. main에 코드만 push하면 배포되지 않는다(릴리스 태그가 트리거).
- **CI**: uv 테스트 → `docker build`(runner, amd64) → Artifact Registry push → `k8s/smb/deployment.yaml` 이미지 태그를 릴리스 버전으로 갱신 → main에 commit/push.
- **CD**: ArgoCD(Application `notiflex-smb`)가 main의 `k8s/smb` 변경을 감지해 자동 배포(rolling update).
- **GCP 인증**: Workload Identity Federation(키리스). 조직 정책으로 SA 키 생성이 금지되어, CI는 `notiflex-ci` SA(`roles/artifactregistry.writer`)를 GitHub OIDC로 impersonate한다. 저장되는 키 없음.
- git 태그가 곧 이미지 태그이자 `APP_VERSION`(`/version` 값)의 단일 소스다.

## 관측 가능성 (ch4에서 구축)

- **네임스페이스**: `monitoring`. Helm으로 설치했고 ArgoCD 관리 대상이 아니다 (values는 `helm-values/`, 매니페스트는 `k8s/monitoring/`).
- **메트릭**: kube-prometheus-stack (Prometheus + Grafana + Alertmanager + node-exporter + kube-state-metrics). 앱은 `prometheus-fastapi-instrumentator`로 `/metrics`(`http_requests_total` 등)를 노출하고, `k8s/smb/servicemonitor.yaml`(라벨 `release: kube-prometheus`)로 Prometheus가 스크레이프한다.
- **로그**: Loki(SingleBinary) + Fluent Bit(DaemonSet). Grafana Loki 데이터소스 등록됨(`isDefault: false`). LogQL `{namespace="notiflex"}`로 조회.
- **알림**: PrometheusRule `pod-restart-alert`(재시작 과다 → Alertmanager). **외부 채널(Slack/이메일 등)은 미설정** — Alertmanager receiver가 기본 `null`이라 발동은 되지만 외부 전송은 안 된다. 붙이려면 receiver를 설정하고 자격 증명은 Secret으로 분리한다.
- **접속**: `kubectl --context notiflex-gke -n monitoring port-forward svc/kube-prometheus-grafana 3000:80` → `http://localhost:3000` (admin, 비밀번호는 `kube-prometheus-grafana` Secret).
- **⚠️ 리소스**: 관측 스택 설치 후 node CPU requests가 ~95%로 빠듯하다. **ch6(CSI DaemonSet 추가) 진입 전** Prometheus/Grafana/Alertmanager/operator/Loki의 CPU requests를 5m으로 선제 축소해야 한다.

## 행동 규칙

1. 명령 실행 전 현재 상태를 확인한다 (`kubectl get`, `gcloud config list` 등).
2. 파일 변경 전 기존 내용을 먼저 읽는다.
3. 에러 발생 시 원인을 분석하고 해결 방안을 제시한 뒤 진행한다.
4. 매니페스트 작성 시 네임스페이스(`notiflex`)를 명시한다.
5. **모든 `kubectl` 명령에 `--context notiflex-gke`를 반드시 지정한다** (잘못된 클러스터 대상 실행 방지. 이 컴퓨터의 kubeconfig에는 회사 AWS EKS 컨텍스트도 함께 있음).
6. 리소스 생성/삭제 전에는 영향 범위를 먼저 설명한다.
7. 이미지 태그는 `latest`를 쓰지 않고 명시적 버전(`v0.1.0` 등)을 사용한다. **한 번 배포에 쓴 태그는 절대 재사용하지 않고, 릴리스마다 새 버전으로 올린다** (Kubernetes는 `image:` 문자열이 바뀔 때만 롤아웃을 트리거하므로, 같은 태그로 이미지 내용만 바꾸면 재배포가 감지되지 않는다).
8. 자격 증명(서비스 계정 키, API 키, 토큰, 비밀번호 등)은 코드나 매니페스트에 하드코딩하지 않는다 (환경변수, GitHub Secrets, Secret Manager 사용).
9. 빌드 산출물(바이너리, `dist/`, `bin/` 등)은 저장소에 커밋하지 않는다.
10. K8s 매니페스트에 실제 시크릿 값을 직접 넣지 않고, Secret 리소스 참조로 분리한다.
