# FinFlow Financial Data Platform — Interview Prep

Sayantani Nath  ·  Built: 2026  ·  Status: In Progress  ·  Language: Python, SQL (dbt)

## One-Liner

A financial data engineering platform that ingests real-time cryptocurrency and stock prices from public APIs, stores them in date-partitioned JSONL format, and transforms them through dbt models — demonstrating the full data engineering lifecycle (ingest → store → transform → analyze) on real market data.

## Full Pipeline — End to End

CoinGecko REST API (free, no key required) ↓ HTTP GET every 60 seconds ↓ nested JSON: {"bitcoin": {"usd": 67432, "usd_market_cap": 1.3T, ...}} ↓ crypto_producer.py ↓ normalize() — flattens nested JSON → flat record per coin ↓ adds: coin_id, price_usd, market_cap_usd, change_24h_pct, volume_24h_usd ↓ adds: fetched_at (UTC ISO timestamp), source="coingecko" ↓ appends to date-partitioned JSONL: data/raw/crypto/YYYY-MM-DD.jsonl ↓ optional: publishes same records to Kafka topic (USE_KAFKA=true) ↓ JSONL files (partitioned by date) ↓ Pandas analysis (practice_pandas_*.py — written from scratch) ↓ groupby, agg, sort, boolean filter, map, apply ↓ answers: highest price, most volatile coin, volume by date ↓ dbt models (/dbt/models/) ↓ stg_crypto_prices.sql — staging: type cast, rename, filter bad rows ↓ fact_price_movements.sql — fact table: price + volume per coin per timestamp ↓ agg_daily_summary.sql — mart: avg price, max price, total volume per day ↓ schema.yml — column docs + dbt tests (not_null, unique)

## What's Fully Built

**✅ Fully working:**

  * crypto_producer.py — ingests from CoinGecko, normalizes, writes JSONL with date partitioning and retry logic
  * stock_producer.py — same pattern, different API source
  * Pandas analysis — 4 lessons practiced on real FinFlow JSONL data, all written from blank
  * dbt models — staging, fact, and mart layers with schema.yml tests
  * redis_manager.py — caching layer structure built
  * Airflow DAG skeleton — finflow_dag.py exists



**🟡 In Progress:**

  * PySpark processing of JSONL files (practice_pyspark_lesson1.py started)
  * Kafka consumer wiring — producer has Kafka publish built in, local broker setup pending



## File-by-File: What Each Does

### crypto_producer.py

  * Hits `/simple/price` endpoint with 6 coin IDs and fields: usd, usd_market_cap, usd_24h_change, usd_24h_vol
  * `normalize(response)`: iterates `response.items()`, unpacks `(coin_id, metrics)` tuple, builds flat dict per coin
  * Uses `datetime.now(timezone.utc).isoformat()` — always UTC, never local time
  * JSONL append-mode write: `open(path, "a")` — one JSON object per line
  * Date-partitioned path: `data/raw/crypto/{date}.jsonl` — new file per day
  * Retry logic: catches `requests.exceptions.HTTPError` (429 rate limit), `requests.exceptions.Timeout`, logs and sleeps before retry
  * Kafka toggle: checks `os.environ.get("USE_KAFKA")` — if true, publishes same records to topic



### dbt Models

  * **stg_crypto_prices.sql:** Selects from raw source, casts price_usd as FLOAT, timestamp as TIMESTAMP, renames coingecko field names to clean standard names, filters where coin_id IS NOT NULL
  * **fact_price_movements.sql:** References stg_crypto_prices, contains one row per coin per timestamp with all price/volume metrics
  * **agg_daily_summary.sql:** GROUP BY coin_id, DATE(fetched_at) — AVG(price_usd), MAX(price_usd), SUM(volume_24h_usd), COUNT(*)
  * **schema.yml:** Documents every column, adds tests: `not_null` on coin_id + fetched_at, `unique` on surrogate key, `accepted_values` for source field



### Pandas Analysis (What You Wrote From Scratch)

  * Load: `df = pd.read_json("data/raw/crypto/2026-05-26.jsonl", lines=True)`
  * Highest price coin: `df.loc[df["price_usd"].idxmax(), "coin_id"]`
  * Positive movers: `df[df["change_24h_pct"] > 0]`
  * Average per coin: `df.groupby("coin_id")["price_usd"].mean()`
  * Sort by market cap: `df.sort_values("market_cap_usd", ascending=False)`
  * Label up/down: `df["label"] = df["change_24h_pct"].map(lambda x: "up" if x > 0 else "down")`
  * Multi-agg: `df.groupby("coin_id").agg({"price_usd": ["mean","max"], "volume_24h_usd": "sum"})`



## Why You Built It

To learn data engineering concepts on real data, not synthetic toy datasets. Financial market data was deliberate — it's high-frequency, has a clear schema, generates meaningful business questions (which coin is most volatile, what's the volume pattern by hour), and naturally demonstrates why streaming and batch ingestion patterns exist. The date-partitioned JSONL storage mirrors how production data lakes work — Parquet on S3 is the production version of the same pattern, just at scale.

## Design Decisions to Defend

  * **JSONL over CSV:** Append-friendly — one record per line, no need to load the whole file. Standard output format for streaming systems. Also handles nested data naturally
  * **Date partitioning:** Same concept as Hive/Spark date partitioning — you never scan all history to answer "what happened today". Each day's data is isolated
  * **UTC timestamps:** Financial markets operate globally. Local time is ambiguous across timezones. UTC + ISO 8601 is unambiguous and sort-safe
  * **dbt 3-layer model:** Staging layer is the only layer that touches raw data. Fact layer is business logic. Mart layer is the serving layer. This separation means raw data issues are fixed in one place only
  * **CoinGecko API:** Free, no key required for basic usage, returns rich data (price + market cap + 24h change + volume) in one call
  * **Why not a database for local storage:** Flat files are faster to iterate on locally. The dbt transformation logic works identically whether the underlying store is files or a warehouse



## How to Productionize It

  1. Swap JSONL files for S3 with Parquet — same date-partitioned concept, production storage
  2. Run Kafka as the streaming layer — producer publishes to topic, consumers process in real time
  3. Airflow DAG for scheduling — the dag skeleton already exists in `airflow/dags/finflow_dag.py`
  4. Point dbt at Snowflake or Databricks — model logic stays identical, warehouse does the compute



## Interview Q&A

Q: Walk me through FinFlow end to end.

FinFlow is a financial data platform I built to practice DE concepts on real data. The ingestion layer is a Python producer that hits CoinGecko's API every 60 seconds, normalizes the nested JSON response into flat records, and writes them in JSONL to date-partitioned files — one file per day, which mirrors how production data lakes partition by date. On top of the raw files I have dbt models: a staging layer that cleans and standardizes, a fact table for price movements, and a daily aggregate mart. I've also been doing Pandas analysis on the FinFlow data — groupby, aggregation, boolean filtering, written from scratch.

Q: Why JSONL and not a database?

JSONL is append-friendly — one record per line, no file lock or full load needed. It's the native output format of streaming systems, so it maps directly to what a Kafka consumer would write in production. The date partitioning is the same concept as Parquet partitioning on S3 — just smaller scale. The dbt transformation logic works the same regardless of whether the underlying storage is flat files or a warehouse.

Q: What does your dbt model structure look like?

Three layers. Staging — stg_crypto_prices is the only model that touches raw data. It casts types, renames columns to standard names, filters null rows. The fact model — fact_price_movements — contains one row per coin per timestamp with price, volume, and change metrics, built from staging. The mart — agg_daily_summary — groups by coin and date to give daily averages, max, and total volume. Schema.yml adds column documentation and dbt tests: not_null on coin_id and timestamp, unique on the surrogate key.

Q: How would you productionize this?

Four changes. JSONL on disk becomes Parquet on S3 — same date-partitioned concept. The Kafka publish path that's already in the producer gets wired to a real broker. The Airflow DAG skeleton that already exists in the project gets fleshed out to schedule ingestion and dbt runs. And dbt points at Snowflake or Databricks instead of local files — the model logic stays identical, the warehouse provides the compute at scale.

Q: Why UTC timestamps and why does it matter?

Financial markets run globally — crypto trades 24/7 across every timezone. If I store timestamps in local time, records from different days when my system clock changes become ambiguous and sort incorrectly. UTC is unambiguous and ISO 8601 format is both human-readable and lexicographically sortable. I learned this the hard way — early builds used datetime.now() without timezone, which caused groupby-date operations to produce wrong results when the local clock rolled over midnight.
