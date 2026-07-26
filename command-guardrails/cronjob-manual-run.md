# CronJob 수동 실행

정기 실행을 기다리지 않고 지금 한 번 돌리는 절차다. 수동으로 만든 Job은
CronJob의 히스토리 관리 대상이 아니라서 직접 지워야 한다.

## 사전 확인

1. 스케줄과 마지막 실행 시각을 본다. 다음 정기 실행이 코앞이면 굳이 수동으로
   돌릴 필요가 없고, 겹쳐 돌 수도 있다.

   ```bash
   kubectl --context notiflex-gke get cronjob -n notiflex
   ```

2. 지금 돌고 있는 Job이 있는지 본다. `notiflex-healthcheck`는
   `concurrencyPolicy: Forbid`라 정기 실행끼리는 안 겹치지만, 수동 Job은 별개
   리소스라 이 정책이 적용되지 않는다.

   ```bash
   kubectl --context notiflex-gke get jobs -n notiflex
   ```

3. 그 Job이 밖으로 무슨 영향을 주는지 확인한다. 헬스체크는 `/health`를 한 번
   호출할 뿐이라 안전하지만, 데이터를 고치거나 외부에 알림을 보내는 Job이라면
   수동 실행이 그대로 실제 부수효과가 된다.

## 실행

1. CronJob 정의를 그대로 복사해 일회성 Job을 만든다. 이름은 정기 실행과 구분되게
   짓는다.

   ```bash
   kubectl --context notiflex-gke create job healthcheck-manual-$(date +%H%M) \
     --from=cronjob/notiflex-healthcheck -n notiflex
   ```

2. 끝날 때까지 로그를 본다.

   ```bash
   kubectl --context notiflex-gke logs -f job/<job-name> -n notiflex
   ```

## 사후 검증

1. Job이 `Complete`인지 확인한다.

   ```bash
   kubectl --context notiflex-gke get job <job-name> -n notiflex
   ```

2. 로그가 의도한 결과인지 본다. 헬스체크라면 `Health check passed (HTTP 200)`.

3. **만든 Job을 지운다.** CronJob의 `successfulJobsHistoryLimit`은 자기가 만든
   Job만 세므로, 수동 Job은 지우지 않으면 계속 남는다.

   ```bash
   kubectl --context notiflex-gke delete job <job-name> -n notiflex
   ```
