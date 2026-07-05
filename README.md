# notiflex-platform

B2B 알림 SaaS 플랫폼을 가정한 Kubernetes 운영환경 구축 실습 프로젝트입니다. FastAPI 백엔드를 GKE에 배포하고, 이미지 빌드부터 배포·외부 노출·CI/CD까지 단계적으로 구성합니다.

## 현재 상태

- [x] FastAPI 앱 (`/health`, `/id`) + pytest 테스트
- [x] Dockerfile (multi-stage, non-root) — Cloud Build로 `notiflex-api:v0.1.1` 빌드/push 완료
- [x] K8s 매니페스트 (Namespace/Deployment/Service/PDB) — GKE `notiflex-cluster`에 배포 완료 (replicas 2, 노드 분산, Running)
- [ ] Gateway API 외부 노출 (HTTPRoute)
- [ ] CI/CD (GitHub Actions + ArgoCD)

## 구성

| 항목 | 값 |
|---|---|
| 클러스터 | GKE Standard (Zonal) `notiflex-cluster`, `asia-northeast3-a`, e2-medium x 2 (Spot) |
| 네임스페이스 | `notiflex` |
| 이미지 저장소 | `asia-northeast3-docker.pkg.dev/project-b3c5c78c-8a5c-4e47-9fe/notiflex-platform/<이미지명>:<태그>` |
| kubectl context | `notiflex-gke` |

## 디렉토리 구조

```
app/                  # FastAPI 소스, 테스트, Dockerfile
k8s/smb/              # K8s 매니페스트 (namespace, deployment, service, pdb)
.github/workflows/    # CI 파이프라인 (예정)
docs/superpowers/     # 설계 스펙 및 구현 플랜 문서
```

## API

| 엔드포인트 | 설명 |
|---|---|
| `GET /health` | 상태 확인 (K8s readiness/liveness probe에서 사용) |
| `GET /id` | in-memory 카운터 ID + Pod 이름 반환. Pod별 카운터라 전역 유일하지 않음 (`pod` + `id` 조합으로 식별) |

## 로컬 개발

```bash
cd app
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

pytest                              # 테스트
uvicorn main:app --port 8080        # 로컬 실행
```

## 이미지 빌드 (Cloud Build)

로컬 Mac(arm64)과 GKE 노드(amd64)의 아키텍처가 달라 로컬 빌드 대신 Cloud Build를 사용합니다. 태그는 릴리스마다 새 버전으로 올리며, 한 번 배포에 쓴 태그는 재사용하지 않습니다.

```bash
gcloud builds submit app/ \
  --tag=asia-northeast3-docker.pkg.dev/project-b3c5c78c-8a5c-4e47-9fe/notiflex-platform/notiflex-api:<버전> \
  --service-account=projects/project-b3c5c78c-8a5c-4e47-9fe/serviceAccounts/notiflex-cloudbuild@project-b3c5c78c-8a5c-4e47-9fe.iam.gserviceaccount.com \
  --default-buckets-behavior=REGIONAL_USER_OWNED_BUCKET
```

## 배포

```bash
kubectl --context notiflex-gke apply -f k8s/smb/

# 확인
kubectl --context notiflex-gke get pods -n notiflex
kubectl --context notiflex-gke port-forward -n notiflex svc/notiflex-api 8080:8080
curl localhost:8080/health
```

외부 노출은 클러스터에 활성화된 Gateway API(HTTPRoute)로 연결할 예정이며, 아직 미구성입니다. 현재는 `port-forward`로만 접근 가능합니다.

자세한 GCP/클러스터 설정과 작업 규칙은 [CLAUDE.md](CLAUDE.md), 설계 배경은 [docs/superpowers/](docs/superpowers/)를 참고하세요.
