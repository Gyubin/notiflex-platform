# notiflex-platform

이 파일은 이 저장소에서 작업하는 AI 어시스턴트를 위한 컨텍스트입니다.

## 프로젝트 개요

- notiflex-platform: Go로 작성되는 백엔드 서비스
- Kubernetes(K8s)에 배포되며, Docker 이미지는 GCP Artifact Registry에 저장

## 디렉토리 구조

- `app/` — Go 소스 코드
- `k8s/smb/` — K8s 매니페스트 (배포, 서비스 등)
- `.github/workflows/` — CI 파이프라인

## GCP 설정

- Project ID: `project-b3c5c78c-8a5c-4e47-9fe`
- Project Name: `gyubin-gitaiops-project`
- Region: `asia-northeast3` (Seoul)
- Zone: `asia-northeast3-a`
- Artifact Registry: `asia-northeast3-docker.pkg.dev/project-b3c5c78c-8a5c-4e47-9fe/notiflex-platform`

## 행동 규칙

- 자격 증명(서비스 계정 키, API 키, 토큰 등)은 코드나 커밋에 절대 포함하지 않는다.
- 빌드 산출물(바이너리, `dist/`, `bin/` 등)은 저장소에 커밋하지 않는다.
- K8s 매니페스트에 실제 시크릿 값을 직접 넣지 않고, Secret 리소스 참조로 분리한다.
