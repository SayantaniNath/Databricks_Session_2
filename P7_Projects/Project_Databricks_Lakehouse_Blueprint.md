# Databricks Lakehouse + AI Data Quality Monitor

Sayantani Nath  ·  Stage 8 Capstone  ·  Target: Aug–Sep 2026

⚠️ NOT STARTED — Build blueprint + interview prep. Update as you build each layer.  
Add to resume only after Bronze → Silver → Gold + AI monitor are all working. 

## One-Liner

A full medallion lakehouse on Databricks using FinFlow financial data — Bronze raw ingestion → Silver cleaned and enriched → Gold analytical mart — with a Claude AI agent that monitors data quality metrics daily and generates plain-English anomaly reports when it detects volume drops, schema drift, or null spikes.

## Why This Project (The Interview Story)

Most portfolio projects either demonstrate data engineering (pipelines, transformations) OR AI (LLM calls, agents) — not both together. This project combines a production-grade lakehouse architecture with an AI layer that adds real business value: instead of a data engineer manually checking dashboards every morning, the AI agent proactively surfaces issues in plain English. That's the direction the industry is moving — AI-augmented data operations — and this project demonstrates I can build both sides. 

I chose Databricks because it's the dominant lakehouse platform in enterprise — Unity Catalog, Delta Lake, and Photon are all things interviewers at Databricks, Google, Stripe, and Snowflake ask about directly. Using my existing FinFlow data as the source means I'm not building with toy data — it's real cryptocurrency and stock market data I've been ingesting since May 2026. 

## Full Architecture — End to End

FinFlow JSONL files (existing, partitioned by date) data/raw/crypto/YYYY-MM-DD.jsonl data/raw/stocks/YYYY-MM-DD.jsonl ↓ Airflow DAG: finflow_lakehouse_dag.py ↓ Task 1: ingest_to_bronze ↓ Task 2: bronze_to_silver ↓ Task 3: silver_to_gold ↓ Task 4: run_dbt_models ↓ Task 5: ai_quality_monitor ↓ BRONZE LAYER (Delta Lake — raw, append-only) catalog.finflow.bronze_crypto_prices catalog.finflow.bronze_stock_prices Schema: raw JSON fields + ingestion_ts + source_file ↓ SILVER LAYER (Delta Lake — cleaned, typed, deduplicated) catalog.finflow.silver_crypto_prices catalog.finflow.silver_stock_prices Transformations: cast types, standardize column names, deduplicate by (coin_id, fetched_at), filter nulls, add derived: price_change_pct, hour_of_day, day_of_week ↓ GOLD LAYER (Delta Lake — aggregated, analytics-ready) catalog.finflow.gold_daily_summary catalog.finflow.gold_coin_volatility catalog.finflow.gold_cross_asset_correlation Grain: coin_id + date ↓ dbt models (on Gold layer) mart_daily_market_report.sql mart_volatility_ranking.sql ↓ Claude AI Data Quality Monitor (Python + Claude API) Reads Gold metrics: row counts, null rates, volume vs 7-day avg Detects: volume drops >30%, null spike >5%, schema drift, new coins Calls Claude API to generate plain-English report Output: daily_quality_report_YYYY-MM-DD.md Example: "Bitcoin volume dropped 42% vs 7-day average on 2026-08-15. Ethereum null rate in market_cap_usd rose from 0.2% to 8.1% — likely CoinGecko API issue. Recommend checking source connection."

## Medallion Architecture — Layer by Layer

🥉 Bronze — Raw Ingestion Layer

  * **What:** Exact copy of source data, no transformations. Append-only. Never deleted
  * **Why:** If a bug in Silver/Gold corrupts data, you can always reprocess from Bronze. It's your source of truth
  * **Schema:** Raw JSON fields + `ingestion_ts` (when it landed) + `source_file` (which JSONL file it came from)
  * **Delta feature used:** `COPY INTO` or `autoloader` for incremental ingestion from JSONL files
  * **Unity Catalog:** Registered in `finflow` catalog under `bronze` schema



🥈 Silver — Cleaned and Enriched Layer

  * **What:** Typed, deduplicated, standardized data. The trusted version
  * **Transformations in PySpark:**
    * Cast `price_usd` to DoubleType, `fetched_at` to TimestampType
    * Deduplicate: `dropDuplicates(["coin_id", "fetched_at"])`
    * Filter: remove rows where `price_usd IS NULL OR price_usd <= 0`
    * Derive: `hour_of_day`, `day_of_week`, `is_weekend`
    * MERGE into Silver table (upsert) — handle late arrivals cleanly
  * **Delta feature used:** `MERGE INTO` for upserts, `OPTIMIZE` \+ `ZORDER BY (coin_id, fetched_at)` for query speed



🥇 Gold — Analytical Mart Layer

  * **What:** Aggregated, business-ready. Grain: coin_id + date
  * **Aggregations:** avg_price, max_price, min_price, total_volume, record_count, avg_change_24h, volatility (stddev of price)
  * **Cross-asset:** Correlation between Bitcoin price and Ethereum price by day
  * **dbt models on Gold:** mart_daily_market_report, mart_volatility_ranking
  * **Delta feature used:** Time travel — `SELECT * FROM gold_daily_summary VERSION AS OF 5` to query historical snapshots



## The AI Layer — Claude Data Quality Monitor

**What it does:** Reads Gold layer metrics, computes anomaly signals, calls Claude API with the metrics + anomaly findings, receives a plain-English report, saves it as a markdown file. Runs as an Airflow task after the Gold layer builds. 

### How It Works (Step by Step)

  1. **Compute metrics:** Query Gold table — today's row count vs 7-day average, null rate per column, new coin_ids not seen before, price range sanity checks
  2. **Detect anomalies:** Flag if volume drops >30%, null rate increases >5%, record count drops >20%, new unexpected coin appears
  3. **Build prompt:** Summarize the metrics and anomalies in structured text, ask Claude to write a plain-English daily data quality report with recommendations
  4. **Call Claude API:** `client.messages.create(model="claude-opus-4-7", messages=[...])`
  5. **Save report:** Write Claude's response to `reports/quality_YYYY-MM-DD.md`



### Example Claude Prompt Structure

You are a data quality analyst reviewing a financial data lakehouse. Today's metrics for the FinFlow crypto pipeline: \- Total records ingested: 8,234 (7-day avg: 14,102) — DROP OF 42% \- Null rate in market_cap_usd: 8.1% (yesterday: 0.3%) — SPIKE \- New coin_ids not seen before: none \- Price range: Bitcoin $67,200–$68,100 (within normal range) Anomalies detected: 1\. Record volume dropped 42% vs 7-day average 2\. market_cap_usd null rate spiked from 0.3% to 8.1% Write a concise data quality report explaining what likely happened, what the business impact is, and what the data engineer should check first.

## Technology Choices — Why Each One

Component| Choice| Why  
---|---|---  
Lakehouse platform| Databricks| Delta Lake, Unity Catalog, PySpark, and Photon all in one platform. Matches enterprise direction. DEA exam tests this directly  
Storage format| Delta Lake| ACID transactions, time travel, MERGE, OPTIMIZE + Z-ORDER. The lakehouse standard — replaces Parquet alone  
Catalog| Unity Catalog| Three-level namespace (catalog.schema.table), lineage tracking, column-level security, data sharing. Most important Databricks governance feature  
Processing| PySpark| Native to Databricks. Handles large-scale transformations across partitions. DataFrame API mirrors Pandas  
Transformation| dbt on Gold| Adds SQL-based transformation discipline, documentation, and tests on top of the Gold layer. dbt + Databricks is a common production pattern  
Orchestration| Airflow| Schedules the full Bronze→Silver→Gold→AI flow. Retries on failure. Observable  
AI layer| Claude API| Best reasoning quality for structured data analysis. Prompt caching reduces cost on repeated metric summaries. You're already familiar with the Anthropic SDK  
Source data| FinFlow JSONL| Real financial data you've been building since May 2026. Not a toy dataset  
  
## Key Concepts to Understand Before Building

**Delta Lake transaction log:** Every write to a Delta table creates a JSON entry in the `_delta_log/` folder. This is how time travel works — Delta replays the log to reconstruct the table at any version. OPTIMIZE compacts small files; VACUUM removes old files beyond the retention period.

**Unity Catalog three-level namespace:** `catalog.schema.table` — e.g. `finflow.bronze.crypto_prices`. The metastore sits above catalogs. Lineage is tracked automatically — Unity Catalog knows that gold_daily_summary was derived from silver_crypto_prices.

**MERGE INTO (upsert):** `MERGE INTO silver USING updates ON silver.coin_id = updates.coin_id AND silver.fetched_at = updates.fetched_at WHEN MATCHED THEN UPDATE SET ... WHEN NOT MATCHED THEN INSERT ...` — handles late-arriving records without duplicates.

**OPTIMIZE + ZORDER:** OPTIMIZE compacts many small files into fewer large files (fixes the "small file problem" in streaming). ZORDER BY (coin_id, fetched_at) co-locates related data on disk so queries filtering by coin_id skip irrelevant files entirely.

**Autoloader (cloudFiles):** Databricks feature that incrementally ingests new files from a directory — only processes new files since last run. Better than a full directory scan for Bronze ingestion.

## Build Order (Follow This Sequence)

  1. **Step 1:** Set up Databricks Community Edition. Create catalog `finflow`. Upload a sample FinFlow JSONL file manually
  2. **Step 2:** Write Bronze ingestion notebook — read JSONL into DataFrame, add ingestion_ts + source_file columns, write to Delta table `finflow.bronze.crypto_prices`
  3. **Step 3:** Write Silver transformation notebook — type casts, deduplication, null filter, derived columns. Write with MERGE INTO
  4. **Step 4:** Write Gold aggregation notebook — groupby coin_id + date, compute all aggregates. Write to Gold Delta table
  5. **Step 5:** Run OPTIMIZE + ZORDER on Silver and Gold. Query with time travel. Verify lineage in Unity Catalog UI
  6. **Step 6:** Add dbt models pointing at Gold layer. Run dbt test
  7. **Step 7:** Write the Claude API quality monitor script. Test with one day's metrics manually
  8. **Step 8:** Wire everything into an Airflow DAG. Test full end-to-end run
  9. **Step 9:** Update this document with what you actually built. Add to resume and portfolio



## Interview Q&A

Q: Walk me through this project end to end.

[Fill in after building. Use the pipeline diagram as your guide. Start with the data source, walk through each layer, explain what transforms at each step, and end with what the AI monitor adds on top.]

Q: Why a three-layer medallion architecture instead of just loading data directly to analytics?

Each layer has a distinct contract. Bronze is immutable raw data — if anything goes wrong in Silver or Gold, I can always reprocess from Bronze without re-ingesting from the source. Silver is the trusted layer — typed, deduplicated, cleaned. Gold is optimized for analytics — aggregated to the grain that consumers need. Keeping these separate means a bug in one layer doesn't corrupt the others, and each layer can be owned and tested independently.

Q: What does Unity Catalog give you that a plain Hive metastore doesn't?

Three things. Automatic lineage — Unity Catalog tracks that gold_daily_summary was derived from silver_crypto_prices, without any manual annotation. Column-level security — I can grant access to specific columns, not just tables. And cross-workspace data sharing — the same catalog is accessible across multiple Databricks workspaces. Hive metastore is workspace-scoped; Unity Catalog is account-scoped.

Q: Why use an LLM for data quality monitoring — couldn't you just write alert rules?

Rule-based alerts are good at catching known issues — "volume dropped more than 30%". But they can't explain WHY, suggest what to check first, or connect multiple signals into a coherent narrative. An LLM looks at all the metrics together — volume drop + null spike in the same column — and can reason that these are probably the same root cause (API outage for that field) rather than two separate issues. It also writes in plain English, which means non-engineers on the team can read the daily report without needing to understand the metrics themselves.

Q: What's Delta Lake time travel and when would you use it?

Every write to a Delta table is logged in the transaction log. You can query any previous version: SELECT * FROM gold_daily_summary VERSION AS OF 5, or SELECT * FROM gold_daily_summary TIMESTAMP AS OF '2026-08-01'. I'd use it for three things: debugging — if the AI monitor flags an anomaly today, I can query yesterday's snapshot to compare. Auditing — regulators can ask "what did your data show on this date?" and I can reproduce it exactly. And recovery — if a bad write corrupts Gold, I can restore from the last known good version with RESTORE TABLE.

Q: What is OPTIMIZE + ZORDER and why does it matter?

Streaming writes create many small files — one per micro-batch — which kills read performance because Spark opens thousands of file handles per query. OPTIMIZE compacts those small files into fewer large files. ZORDER BY (coin_id, fetched_at) then physically co-locates related data — all Bitcoin records are close together on disk. When I query WHERE coin_id = 'bitcoin', Spark can skip irrelevant files entirely using the statistics in the transaction log. Together they can reduce scan time by 10x on large tables.

Q: How would you handle schema evolution — what if CoinGecko adds a new field?

Delta Lake supports schema evolution with mergeSchema option. When Bronze ingests the new field, it automatically adds the column to the Delta table schema. Silver picks it up on the next run. I'd add a check in the AI monitor that alerts when new columns appear — that's what the "schema drift" detection covers — so the data engineer knows to review whether the new field should propagate to Silver and Gold and update the dbt models accordingly.

* * *

Last updated: May 2026. Target build: Aug–Sep 2026 (Stage 8). Update after each step. Do not put on resume until Step 8 is complete.
