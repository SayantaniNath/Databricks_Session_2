"""
Lab 1 - keyed producer.
Sends fake card transactions KEYED BY CARD so all events for one card
land in the same partition (the fraud-detection rule from the lesson).
"""
import json, random, time
from kafka import KafkaProducer

CARDS  = [f"card_{i}" for i in range(1, 6)]
CITIES = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Pune"]

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    key_serializer=lambda k: k.encode("utf-8"),
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    acks="all",                 # durability dial - wait for all in-sync replicas
    enable_idempotence=True,    # dedupe producer retries via PID + sequence number
)

for i in range(30):
    card = random.choice(CARDS)
    event = {
        "txn_id": f"txn_{i:04d}",
        "card":   card,
        "city":   random.choice(CITIES),
        "amount": round(random.uniform(50, 5000), 2),
        "ts":     time.time(),
    }
    # KEY = card  ->  murmur2(card) % num_partitions  ->  same card, same partition
    future = producer.send("transactions", key=card, value=event)
    meta = future.get(timeout=10)
    print(f"{event['txn_id']}  key={card:8s}  -> partition {meta.partition}, offset {meta.offset}")
    time.sleep(0.3)

producer.flush()
print("\ndone - note how each card ALWAYS goes to the same partition")
