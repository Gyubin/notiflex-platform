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
- `k8s/smb/` — K8s 매니페스트 (배포, 서비스 등)
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

## 행동 규칙

1. 명령 실행 전 현재 상태를 확인한다 (`kubectl get`, `gcloud config list` 등).
2. 파일 변경 전 기존 내용을 먼저 읽는다.
3. 에러 발생 시 원인을 분석하고 해결 방안을 제시한 뒤 진행한다.
4. 매니페스트 작성 시 네임스페이스(`notiflex`)를 명시한다.
5. **모든 `kubectl` 명령에 `--context notiflex-gke`를 반드시 지정한다** (잘못된 클러스터 대상 실행 방지. 이 컴퓨터의 kubeconfig에는 회사 AWS EKS 컨텍스트도 함께 있음).
6. 리소스 생성/삭제 전에는 영향 범위를 먼저 설명한다.
7. 이미지 태그는 `latest`를 쓰지 않고 명시적 버전(`v0.1.0` 등)을 사용한다.
8. 자격 증명(서비스 계정 키, API 키, 토큰, 비밀번호 등)은 코드나 매니페스트에 하드코딩하지 않는다 (환경변수, GitHub Secrets, Secret Manager 사용).
9. 빌드 산출물(바이너리, `dist/`, `bin/` 등)은 저장소에 커밋하지 않는다.
10. K8s 매니페스트에 실제 시크릿 값을 직접 넣지 않고, Secret 리소스 참조로 분리한다.
