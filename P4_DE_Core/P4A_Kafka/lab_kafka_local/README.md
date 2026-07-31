# P4A Kafka - local hands-on lab

## 0. Setup
    python3 -m venv .venv && source .venv/bin/activate
    pip install kafka-python
    docker compose up -d
Console UI: http://localhost:8080

## 1. Create a topic with 3 partitions
    docker exec -it redpanda rpk topic create transactions -p 3
    docker exec -it redpanda rpk topic list

## 2. Produce keyed events
    python producer.py
Observe: the SAME card always prints the SAME partition. That is
`murmur2(key) % 3` being deterministic - the ordering guarantee in action.

## 3. Consumer group + live rebalance  <- the important one
Terminal 1:  python consumer.py A      # A gets all 3 partitions
Terminal 2:  python consumer.py B      # REBALANCE - now A gets 2, B gets 1
Terminal 3:  python consumer.py C      # one partition each
Terminal 4:  python consumer.py D      # D sits IDLE - 4 consumers, 3 partitions

Now Ctrl-C consumer C and watch its partition get reassigned within seconds.

Re-run producer.py while consumers are live to see events stream in.

## 4. Inspect offsets like a DE
    docker exec -it redpanda rpk group describe fraud-detector
Columns: CURRENT-OFFSET, LOG-END-OFFSET, LAG.
LAG is the single most important number you will ever monitor in production.

## 5. Prove replay (the thing queues cannot do)
    docker exec -it redpanda rpk group seek fraud-detector --to start
Restart a consumer - it reads everything again. Reading never deleted the data.

## 6. Teardown
    docker compose down -v
