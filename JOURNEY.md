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
| ch3 | 3.3 기능 추가 | ✅ | 2026-07-12 | `/version` 엔드포인트 추가, v0.1.2 빌드/푸시. git push → ArgoCD 롤링 업데이트로 무중단 교체 확인 |
| ch3 | 3.4 CI | ⬜ | | |
| ch3 | 3.5 CI-CD 연결 | ⬜ | | |
| ch4 | 4.2 메트릭 모니터링 | ⬜ | | |
| ch4 | 4.3 로그 수집 | ⬜ | | |
| ch4 | 4.4 알림 | ⬜ | | |
| ch5 | 5.2 트래픽 관리 | ⬜ | | |
| ch5 | 5.3 무중단 배포 | ⬜ | | |
| ch6 | 6.1 캐시 | ⬜ | | |
| ch6 | 6.2 시크릿 관리 | ⬜ | | |
| ch6 | 6.3 Canary 전환 | ⬜ | | |
| ch7 | 7.2 멀티 노드풀 | ⬜ | | |
| ch7 | 7.3 App of Apps | ⬜ | | |
| ch7 | 7.4 멀티테넌시 | ⬜ | | |
| ch8 | 8.1 메시징 | ⬜ | | |
| ch8 | 8.2 트레이싱 | ⬜ | | |
| ch8 | 8.3 CronJob | ⬜ | | |
| ch9 | 9.1 저장소 분석 | ⬜ | | |
| ch9 | 9.2 회고 | ⬜ | | |
| ch9 | 9.3 온보딩 문서 | ⬜ | | |
| ch9 | 9.4 GitAIOps 분석 | ⬜ | | |
| ch9 | 9.5 마무리 | ⬜ | | |

## 도구 선택 기록

독자가 3-프롬프트 패턴(탐색→비교→실행)에서 실제로 선택한 도구와 이유를 기록한다.

| 영역 | 선택 | 검토한 대안 | 선택 이유 |
|------|------|-----------|----------|
| 앱 언어 | Python (FastAPI + uvicorn) | Go (교재 기준) | Python 학습 목적으로 교재의 Go 스택을 대체 |
| 이미지 빌드 | Cloud Build | 로컬 docker build | M-시리즈 맥(arm64)과 GKE 노드(amd64) 아키텍처 불일치 회피 |
| GitOps 도구 | ArgoCD | Flux | UI/App of Apps 등 교재 진행 흐름과 정합, 선언적 Application으로 selfHeal 복구 |

## 현재 버전

| 컴포넌트 | 버전 | 변경 이력 |
|---------|------|----------|
| Python | 3.14 | |
| FastAPI | 0.139.0 | |
| uvicorn | 0.50.0 | |
| Notiflex 이미지 | v0.1.2 | 2026-07-12 /version 추가 (v0.1.1→v0.1.2) |
| ArgoCD | v3.4.5 | 2026-07-12 설치 (stable manifest) |
| Kafka | (미설치) | |
| OTel SDK | (미설치) | |

## 현재 리소스

| 노드풀 | 머신 타입 | 노드 수 | 주요 워크로드 |
|--------|----------|---------|-------------|
| default-pool | e2-medium (Spot) | 2 | notiflex-api ×2 |

## 트러블슈팅 이력

독자가 겪은 문제와 해결 방법을 기록한다. 같은 문제를 다시 겪지 않도록 한다.

| 챕터 | 문제 | 해결 |
|------|------|------|
| ch2 | 로컬(M-시리즈 맥, arm64) 빌드 이미지가 GKE 노드(amd64)와 아키텍처 불일치 | Cloud Build(GCP 서버, amd64)로 빌드 전환 |
| ch2 | Cloud Build에서 Compute Engine 기본 서비스 계정 권한 부족으로 빌드 실패 | 전용 SA `notiflex-cloudbuild` 생성 + `--default-buckets-behavior=REGIONAL_USER_OWNED_BUCKET` 지정 |
| ch2 | POD_NAME 기본값 테스트가 환경에 따라 간헐적 실패 | 테스트에서 환경변수를 명시적으로 unset (conftest.py) |
| ch2 | 노드 풀 0으로 중단 시 PDB가 노드 드레인을 차단 | 리사이즈 전에 Deployment replicas를 먼저 0으로 축소 |
