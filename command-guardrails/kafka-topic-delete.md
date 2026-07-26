# Kafka Topic 삭제

토픽을 지우면 아직 아무도 안 읽은 메시지가 같이 사라진다. 되돌릴 수 없으므로
아래 순서를 지킨다.

## 사전 확인

1. 토픽에 남아 있는 메시지와 Consumer가 어디까지 읽었는지 본다. `LAG`가 0이 아니면
   아직 처리되지 않은 메시지가 있다는 뜻이다.

   ```bash
   kubectl --context notiflex-gke exec -n kafka notiflex-kafka-dual-role-0 -- \
     bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --all-groups
   ```

2. 이 토픽에 메시지를 보내는 쪽을 전부 찾는다. 지금은 두 테넌트의 `notiflex-api`가
   Producer이고, 둘 다 `KAFKA_BROKER` 환경변수로 붙는다.

   ```bash
   grep -rn "KAFKA_BROKER" k8s/
   ```

3. 이 토픽이 ArgoCD 관리 대상인지 확인한다. 관리 대상이면 `kubectl delete`로 지워도
   selfHeal이 곧바로 되살린다.

   ```bash
   kubectl --context notiflex-gke get kafkatopic notifications -n kafka \
     -o jsonpath='{.metadata.annotations.argocd\.argoproj\.io/tracking-id}'
   ```

## 실행

1. 메시지 유입을 먼저 끊는다. Rollout에서 `KAFKA_BROKER`를 빼고 배포하거나,
   급하면 replica를 0으로 내린다.
2. 위 `--describe`로 `LAG`가 0이 될 때까지 기다린다. Consumer가 잔여 메시지를 다
   가져갔다는 뜻이다.
3. ArgoCD가 관리하므로 매니페스트에서 지우고 push한다. `kubectl delete`를 직접
   쓰지 않는다.

   ```bash
   git rm k8s/kafka/kafka-topic.yaml
   git commit -m "..." && git push
   ```

## 사후 검증

1. 토픽이 실제로 사라졌는지 본다.

   ```bash
   kubectl --context notiflex-gke get kafkatopic -n kafka
   ```

2. Producer·Consumer 로그에 `UnknownTopicOrPartition` 같은 에러가 반복되는지 본다.
   토픽을 지웠는데 앱이 계속 붙으려 하면 여기서 드러난다.

   ```bash
   kubectl --context notiflex-gke logs -l app=notiflex-api -n notiflex --tail=50 | grep -i kafka
   ```

3. ArgoCD Application이 Synced 상태로 돌아왔는지 확인한다.
