# Real-Time Fraud Detection Pipeline

Sayantani Nath  ·  Stage 3 Project  ·  Target: Jul 2026

⚠️ NOT STARTED YET — This is a build blueprint + pre-interview prep document.  
Update this document as you build each component. Only put this on your resume once Stage 3 is complete. 

## One-Liner (Learn This Now)

An end-to-end real-time streaming pipeline that ingests financial transaction events through Kafka, scores them for fraud using IsolationForest anomaly detection, routes alerts to a dedicated Kafka topic, sinks all records to Delta Lake, and orchestrates the full flow with Airflow — built on Databricks.

## Why This Project (The Interview Story)

I wanted a capstone project that used every layer of a real DE stack in one coherent flow: event streaming, real-time scoring, Delta Lake storage with ACID guarantees, and orchestration. Fraud detection was a deliberate choice — it has real business stakes (financial loss, customer trust), a natural latency requirement (must detect in near real-time, not batch daily), and a clear definition of success (flagged transactions reach the alert topic before the next window closes). It's also rare in tutorial portfolios, which usually clone Reddit feeds or weather APIs.

## Full Architecture — End to End

Data Source Kaggle "Credit Card Fraud Detection" dataset OR PaySim simulated mobile money transactions ↓ transaction_producer.py (Python) Reads dataset rows, publishes to Kafka topic: "transactions" Message format: JSON {transaction_id, amount, merchant, timestamp, features...} ↓ Kafka Topic: "transactions" ↓ PySpark Structured Streaming (Databricks) readStream from Kafka ↓ parse JSON payload ↓ feature engineering (amount_log, hour_of_day, merchant_category) ↓ IsolationForest scoring (scikit-learn model, broadcast to workers) ↓ tag each record: is_fraud = True/False, anomaly_score ↓ Fork: ├─ All records → Delta Lake sink (transactions table, Bronze layer) └─ Flagged records (is_fraud=True) → Kafka topic: "fraud_alerts" ↓ Delta Lake (Databricks) Bronze: raw transactions Silver: cleaned + scored transactions Gold: daily fraud summary mart (count, amount_sum, by merchant_category) ↓ Airflow DAG Schedules: producer start, dbt runs on Delta, daily alert report ↓ Optional: Grafana or Databricks dashboard for live fraud rate

## Technology Choices — Why Each One

Component| Choice| Why  
---|---|---  
Event streaming| Apache Kafka| Industry standard for financial event streams. Decouples producer from consumer. Replay capability for debugging. Separate topics for transactions vs alerts is a clean architectural pattern  
Stream processing| PySpark Structured Streaming| Handles exactly-once semantics with checkpoints. Integrates natively with Delta Lake. Runs on Databricks without setup overhead  
Anomaly detection| IsolationForest (scikit-learn)| Doesn't require labeled training data — unsupervised. Works well on tabular financial features. Fast inference. Can be broadcast to Spark workers as a broadcast variable so the model doesn't re-serialize for every partition  
Storage| Delta Lake| ACID transactions on a data lake. Time travel for debugging (what was the fraud rate on a specific day?). MERGE for upserts. OPTIMIZE + Z-ORDER for query performance. Native to Databricks  
Orchestration| Apache Airflow| Schedules the producer, dbt runs, and daily reports. Retry on failure. Observable via Airflow UI  
Platform| Databricks| PySpark + Delta Lake + Unity Catalog in one platform. Matches where the industry is going for lakehouse workloads  
  
## Build Order (Follow This Sequence)

  1. **Step 1:** Download Kaggle Credit Card Fraud dataset. Write transaction_producer.py to read CSV rows and print them — don't touch Kafka yet
  2. **Step 2:** Add Kafka. Run a local Kafka broker (Docker). Publish transactions to "transactions" topic. Verify with kafka-console-consumer
  3. **Step 3:** Write PySpark consumer that reads from Kafka topic and prints records — no ML yet, just confirm the stream works
  4. **Step 4:** Add IsolationForest. Train it on the Kaggle features offline. Broadcast the model to Spark workers. Score each record
  5. **Step 5:** Fork the output — write all records to Delta Lake, write flagged records to "fraud_alerts" Kafka topic
  6. **Step 6:** Add dbt models on top of Delta Lake — Bronze/Silver/Gold layers
  7. **Step 7:** Add Airflow DAG to orchestrate the full flow
  8. **Step 8:** Update this document with what you actually built, then add to resume



## Key Concepts to Understand Before Building

  * **Kafka topic:** A named stream of records. Producers write to it, consumers read from it. "transactions" and "fraud_alerts" are two separate topics
  * **Consumer group:** Multiple consumers can read from the same topic in parallel — Kafka tracks the offset (position) per group
  * **Exactly-once semantics:** PySpark + Kafka can guarantee each record is processed exactly once — not zero times (lost), not twice (duplicate). Requires checkpointing
  * **Checkpoint:** PySpark saves its progress to a checkpoint location. If it crashes and restarts, it picks up from the last checkpoint instead of reprocessing everything
  * **Watermark:** Tells Spark how long to wait for late-arriving records before closing a time window. Important for windowed aggregations
  * **IsolationForest:** Anomaly detection algorithm. Builds random decision trees, isolates outliers faster (fewer splits needed). contamination parameter = expected % of fraud
  * **Broadcast variable:** In Spark, if you have a large model or lookup table, broadcasting it sends one copy to each worker node instead of serializing it with every task
  * **Delta Lake MERGE:** Upsert pattern — update if exists, insert if not. Used for deduplication and SCD patterns on streaming data



## Interview Q&A (Prepare These Now — Build First, Then Practice)

Q: Walk me through this pipeline end to end.

[Fill this in once you've built it. Use the pipeline diagram above as your guide — walk through each component, what it does, and why you made that choice.]

Q: Why Kafka and not just batch processing?

Fraud detection has a latency requirement — if you batch daily, a fraudulent transaction completes before you detect it. Kafka gives you an event stream where each transaction is available for scoring within milliseconds of occurring. The separate alert topic means downstream systems (risk team notification, card freeze trigger) can react immediately without polling a database.

Q: Why IsolationForest over a supervised model?

Two reasons. First, fraud labels are rare and often delayed — real fraud datasets have 99%+ legitimate transactions, and you often don't know a transaction was fraudulent until days later when a chargeback happens. IsolationForest is unsupervised so it doesn't need labels. Second, it's interpretable — the anomaly score tells you how far a transaction deviates from normal patterns, which you can threshold and tune. A deep learning model would give you better accuracy but worse interpretability for a compliance conversation.

Q: How does Delta Lake help here specifically?

Three things. ACID transactions mean the streaming write and the batch dbt read never see partial data — no dirty reads. Time travel means I can query the transaction table as it was at any point in time, which is critical for regulatory audit ("show me the fraud rate on this specific date"). And MERGE lets me upsert records cleanly — if a transaction arrives late or needs correction, I merge it rather than appending a duplicate.

Q: What would you monitor in production?

Four things: consumer lag (is the Spark consumer keeping up with Kafka or falling behind?), fraud rate over time (sudden spike = either real fraud wave or model drift), pipeline latency (time from transaction event to alert), and checkpoint health (are checkpoints completing before the next micro-batch starts?).

* * *

Last updated: May 2026. Update this document after each build step. Do not put on resume until Step 7 is complete.
