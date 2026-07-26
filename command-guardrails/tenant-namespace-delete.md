# 테넌트 Namespace 삭제

가장 위험한 작업이다. Namespace를 지우면 그 안의 모든 것이 함께 사라지고,
`kubectl delete namespace`는 확인 절차 없이 바로 시작된다. 순서를 거꾸로 하면
ArgoCD selfHeal이 지운 것을 계속 되살려 작업이 끝나지 않는다.

## 사전 확인

1. 그 namespace에 뭐가 들어 있는지 전부 본다. `get all`은 PVC·Secret·ConfigMap을
   빠뜨리므로 따로 봐야 한다.

   ```bash
   kubectl --context notiflex-gke get all -n <namespace>
   kubectl --context notiflex-gke get pvc,secret,configmap,secretproviderclass -n <namespace>
   ```

2. 지우면 안 되는 데이터가 있는지 판단한다. PVC는 지금 설정상 namespace와 함께
   사라진다.

3. **다른 namespace에서 이 namespace를 참조하는지 확인한다.** 지금 구조에서는
   `enterprise`가 `notiflex`의 Valkey를 FQDN으로 쓰고 있다. `notiflex`를 지우면
   `enterprise`의 `/id`가 같이 죽는다. 반대 방향은 영향이 없다.

   ```bash
   grep -rn "svc.cluster.local" k8s/
   ```

4. 어느 ArgoCD Application이 이 namespace를 관리하는지 확인한다.

   ```bash
   kubectl --context notiflex-gke get applications -n argocd \
     -o custom-columns='NAME:.metadata.name,NS:.spec.destination.namespace'
   ```

5. GCP 쪽에 이 namespace 앞으로 걸린 Workload Identity 바인딩이 있는지 본다.
   테넌트를 추가할 때 `...svc.id.goog[<namespace>/notiflex-api]`를 넣었으므로,
   지울 때도 같이 정리해야 남지 않는다.

## 실행

1. **ArgoCD Application을 먼저 없앤다.** 이 단계를 건너뛰고 리소스부터 지우면
   selfHeal이 곧바로 되살린다.

   ```bash
   git rm argocd/apps/notiflex-<tenant>.yaml
   git commit -m "..." && git push
   ```

2. root-app이 변경을 반영할 때까지 기다린다. 급하면 hard refresh를 건다.

   ```bash
   kubectl --context notiflex-gke annotate application root-app -n argocd \
     argocd.argoproj.io/refresh=hard --overwrite
   ```

3. Application에 `resources-finalizer.argocd.argoproj.io`가 붙어 있으므로 ArgoCD가
   관리하던 리소스를 알아서 정리한다. 사라지는지 지켜본다.

   ```bash
   kubectl --context notiflex-gke get applications -n argocd
   kubectl --context notiflex-gke get all -n <namespace>
   ```

4. 매니페스트 디렉터리도 지운다.

   ```bash
   git rm -r k8s/<tenant>/
   ```

5. 리소스가 다 빠진 뒤에야 namespace 자체를 지운다.

   ```bash
   kubectl --context notiflex-gke delete namespace <namespace>
   ```

6. GCP IAM 바인딩을 제거한다. (이 명령은 승인 분류기에 막히므로 사용자가 직접 실행)

## 사후 검증

1. Application과 namespace가 모두 사라졌는지 확인한다.

   ```bash
   kubectl --context notiflex-gke get applications -n argocd
   kubectl --context notiflex-gke get ns
   ```

2. namespace가 `Terminating`에서 멈춰 있으면 finalizer가 남은 리소스를 붙잡고 있는
   것이다. 무엇이 남았는지부터 확인한다.

   ```bash
   kubectl --context notiflex-gke get namespace <namespace> -o jsonpath='{.status.conditions}'
   ```

3. 남은 테넌트가 멀쩡한지 본다. 크로스 네임스페이스 참조가 끊겼다면 여기서 나온다.

   ```bash
   kubectl --context notiflex-gke logs -l app=notiflex-api -n <남은-namespace> --tail=50
   curl -s http://35.216.8.57/id
   ```

4. Kafka Consumer Group에 사라진 테넌트 그룹(`notiflex-<tenant>`)이 남아 있으면
   정리한다. 브로커 쪽 상태라 namespace를 지워도 자동으로 없어지지 않는다.
