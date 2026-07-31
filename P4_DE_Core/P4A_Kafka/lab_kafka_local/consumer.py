"""
Lab 2 - consumer group member.
Run this in 2 or 3 terminals AT THE SAME TIME and watch partitions
get split across them, then watch a rebalance when you kill one.

    python consumer.py A
    python consumer.py B
"""
import json, sys
from kafka import KafkaConsumer

name = sys.argv[1] if len(sys.argv) > 1 else "A"

consumer = KafkaConsumer(
    "transactions",
    bootstrap_servers="localhost:9092",
    group_id="fraud-detector",        # SAME group -> partitions are SPLIT between members
    auto_offset_reset="earliest",     # no committed offset? start from the beginning
    enable_auto_commit=True,
    key_deserializer=lambda k: k.decode("utf-8") if k else None,
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
)

print(f"[{name}] waiting for assignment...")
for msg in consumer:
    print(f"[{name}] p{msg.partition} off={msg.offset:3d}  {msg.key:8s}  "
          f"{msg.value['city']:10s} {msg.value['amount']}")
