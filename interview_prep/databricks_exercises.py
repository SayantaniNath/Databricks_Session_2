# =============================================================================
# DATABRICKS / SPARK EXERCISES — consolidated from Spark_Architecture_Walkthrough.html
# One place for all practice exercises. Full teaching content + answers stay in
# the walkthrough doc (the .html is canonical) — section refs (§) point there.
# =============================================================================


# =============================================================================
# 1. FROM-BLANK EXERCISES — Job/Stage/Shuffle counting (walkthrough §11)
# For each snippet: how many jobs? how many stages? where are the shuffles?
# =============================================================================

# --- Exercise 1 — groupBy + orderBy + write ---
"""
df = spark.read.json("~/Downloads/finflow/crypto/*.jsonl")
result = (df.filter(col("symbol").isin(["BTC", "ETH"]))
            .withColumn("price_usd_k", col("price") / 1000)
            .groupBy("symbol")
            .agg(avg("price_usd_k").alias("avg_price_k"),
                 count("*").alias("tick_count"))
            .orderBy("symbol"))
result.write.parquet("~/Downloads/finflow/output/")
"""
# ANSWER: 1 job (write.parquet is the action), 3 stages, 2 shuffles:
#   Stage 1: read → filter → withColumn → groupBy partial agg → SHUFFLE
#   Stage 2: post-shuffle agg → orderBy partial → SHUFFLE
#   Stage 3: post-shuffle sort → write parquet
# Traps: count("*") inside agg is lazy (not the action); orderBy IS a shuffle.

# --- Exercise 2 — with a join ---
"""
crypto = spark.read.json("~/Downloads/finflow/crypto/*.jsonl")
coin_meta = spark.read.csv("~/Downloads/finflow/coin_metadata.csv", header=True)

result = (crypto.join(coin_meta, on="symbol", how="inner")
                .filter(col("market_cap_tier") == "large")
                .withColumn("price_usd_k", col("price") / 1000)
                .groupBy("symbol")
                .agg(avg("price_usd_k").alias("avg_price_k"),
                     count("*").alias("tick_count")))
total = result.count()
"""
# ANSWER (SortMergeJoin case): 1 job (result.count()), 4 stages:
#   Stage 0: read crypto + shuffle-write for join          (~200 tasks)
#   Stage 1: read coin_meta + shuffle-write for join       (1 task, parallel w/ 0)
#   Stage 2: join + filter + withColumn + groupBy partial + shuffle (200 tasks)
#   Stage 3: final agg + count                             (1 task)
# ~2-3 stages if Spark auto-broadcasts coin_meta (likely — it's tiny).
# Partitions are PER-STAGE, not summed across stages.

# --- Self-check ---
"""
df.filter(...).groupBy("a").count().orderBy("a").show()
"""
# ANSWER: 3 stages. .count() on GroupedData is lazy (= agg(count(*)));
# the action is .show(). Two shuffles: groupBy and orderBy.


# =============================================================================
# 2. SALTING HANDS-ON LAB — skew detection + fix (walkthrough §21, done 2026-06-08)
# Setup: shuffle.partitions=10, AQE off, autoBroadcastJoinThreshold=-1
# (BHJ masks skew — must force SMJ to see the straggler)
# =============================================================================

# --- Ex 1 — detect skew programmatically (row count per partition) ---
# (spark_partition_id detect — done ✅)
"""
spark_partition_counts = (
    txns.repartition(10, "merchant_id")
        .withColumn("partition_id", F.spark_partition_id())
        .groupBy("partition_id")
        .count()
        .orderBy(F.desc("count"))
)
# Result: one partition ~40,000 rows (MEGACORP), others ~2,500 or less
"""

# --- Ex 2 — join salting (done ✅) ---
"""
SALT_BUCKETS = 10

# Step 1 — salt the large (skewed) table
txns_salted = (
    txns
    .withColumn("salt", (F.rand() * SALT_BUCKETS).cast("int"))
    .withColumn("salted_key", F.concat_ws("_", F.col("merchant_id"), F.col("salt")))
)

# Step 2 — explode the small (lookup) table to match all salt values
merchants_salted = (
    merchants
    .withColumn("salt_array", F.array([F.lit(i) for i in range(SALT_BUCKETS)]))
    .withColumn("salted_key", F.explode(F.col("salt_array")))
    .withColumn("salted_key", F.concat_ws("_", F.col("merchant_id"), F.col("salted_key")))
)

# Step 3 — join, dropping duplicate merchant_id from small table
salted_result = (
    txns_salted
    .join(merchants_salted.drop("merchant_id"), on="salted_key", how="inner")
    .groupBy("merchant_id", "category")
    .agg(F.count("*").alias("txn_count"),
         F.sum("amount").alias("total_amount"),
         F.avg("amount").alias("avg_amount"))
    .orderBy(F.desc("txn_count"))
)
"""
# Result: max partition dropped 41,468 → 12,632 rows (~3.3x better), no empty partitions.
# RULE: use 2-3x more salt buckets than shuffle partitions (hash collisions
# otherwise land 2-3 hot keys in the same partition).

# --- Ex 3 — groupBy two-pass salting (partially done 🟡 — finish from blank) ---
# Task: aggregate txn counts per merchant WITHOUT a join, using two-pass
# aggregation: groupBy(salted_key) partial agg → strip salt → final groupBy(merchant_id).

# --- Ex 4 — bucket sizing (done ✅) ---
# SALT_BUCKETS = ceiling(max_partition_rows / target_rows_per_partition)
#              = ceiling(41,468 / 5,000) = 9
# Skew ratio = Max / non-zero Median = 41,468 / 2,596 = 16x


# =============================================================================
# 3. DELTA LAKE FROM-BLANK CHECKS — 2C session 1 (walkthrough §23)
# Answer out loud before checking the doc.
# =============================================================================
# Q1. You run DELETE FROM tx WHERE tx_id < 100. Describe exactly what appears
#     in the next commit JSON, and what happens to the old Parquet file.
# Q2. A reader starts at version 12 while a writer commits version 13 mid-read.
#     What does the reader see and why?
# Q3. Two jobs both MERGE into the same table at the same time. Walk through
#     the OCC steps that decide who wins.
# Q4. Why does Delta write checkpoints as Parquet instead of JSON?


# =============================================================================
# 4. DELTA LAKE FROM-BLANK CHECKS — 2C sessions 2+ (walkthrough §24-27)
# =============================================================================
# Q1. VACUUM ran with default retention this morning. A teammate asks for the
#     table as of 10 days ago. Possible? Why?
# Q2. A MERGE updates 1 row that lives in a 1-GB file. How much data gets
#     rewritten, and what two log actions appear?
# Q3. You filter on customer_id (10M distinct values). Partition, Z-ORDER,
#     or both? Justify.
# Q4. Streaming job commits every 20 seconds. Name the problem that develops
#     and two fixes.
# Q5. Why does CDF store pre-images for UPDATE but nothing extra for INSERT?
# Q6. Iceberg query: WHERE event_ts > '2026-06-01' prunes partitions even
#     though no partition column is referenced. What feature is this and how
#     does Delta differ?
# Q7. "Why did Databricks build Delta Sharing instead of just granting
#     cross-account S3 read access?" — answer like an interview.


# =============================================================================
# 5. STRUCTURED STREAMING — 2D Ex-5 CHECKPOINT LAB (run 2026-07-06, Free Edition)
# Final version as actually run. Two serverless realities shaped it:
#   1. Serverless does NOT allow long-running triggers (no default/processingTime/
#      continuous) — only trigger(availableNow=True): catch up, commit, stop.
#      So each manual re-run of the write cell = one visible micro-batch.
#   2. Serverless sessions auto-terminate when idle → all Python variables
#      (ckpt, df, query) vanish. Re-run the full cell; the checkpoint itself
#      survives — it lives on the VOLUME (durable storage), not in the session.
# rate + availableNow gotcha: the rate source re-anchors its clock each query
# start and rows are computed (never stored) → no real backlog; "available now"
# only covers the ~1s startup window. Bump rowsPerSecond for visible batches.
# =============================================================================

# --- Step 1 — rate source → Delta with checkpoint (one availableNow batch) ---
"""
ckpt = "/Volumes/workspace/default/mydatadbex5/ex5_ckpt"

df = spark.readStream.format("rate").option("rowsPerSecond", 100).load()

query = (df.writeStream
    .format("delta")
    .option("checkpointLocation", ckpt)
    .outputMode("append")
    .trigger(availableNow=True)          # serverless: only allowed trigger
    .toTable("workspace.default.ex5_rate_sink"))

query.awaitTermination()   # toTable/start is async — block until batch commits
                           # (without this, the checks below read stale data)

spark.sql("SELECT count(*), max(value) FROM workspace.default.ex5_rate_sink").show()
"""

# --- Step 2 — re-run Step 1 (no kill needed — availableNow stops itself) ---
# PREDICT: will max(value) continue, or restart at 0 and duplicate?
# OBSERVED 2026-07-06: count 1877, max 1876 → values 0..1876 exactly once.
# Continuation survived a session restart AND a rowsPerSecond change —
# the checkpoint pins WHERE to resume; source options may change between runs.
# (What must never change per query: the checkpointLocation itself.)

# --- Step 3 — inspect the checkpoint (PREDICT what's in each folder first) ---
"""
display(dbutils.fs.ls(ckpt))
display(dbutils.fs.ls(f"{ckpt}/offsets"))
display(dbutils.fs.ls(f"{ckpt}/commits"))
print(dbutils.fs.head(f"{ckpt}/offsets/2"))   # open any batch number you see
"""
# Expect matching numbered files in offsets/ and commits/ — one pair per run.

# --- Step 4 — delete the checkpoint ---
"""
dbutils.fs.rm(ckpt, recurse=True)   # must print True
"""

# --- Step 5 — re-run Step 1 unchanged, observe the damage ---
# PREDICT: offsets/ is gone — where does the next run start reading, and what
# lands in the sink? Why is this dangerous in production?
"""
spark.sql('''SELECT value, count(*) FROM workspace.default.ex5_rate_sink
             GROUP BY value HAVING count(*) > 1 LIMIT 10''').show()
"""
# Expected: rate source re-anchors → values restart at 0 → duplicates appear.
# Production translation: stateless stream = reprocessing/duplicates;
# stateful stream = state/ (window sums, watermark, dedup history) is gone
# → silently WRONG answers, not just duplicates.

# NOTE: 2D Ex1-4 (from-blank streaming exercises) were reviewed together in
# the 2026-07-03 session as model answers in chat — they were never written
# into the walkthrough doc. Reconstruct here if wanted for redo practice.


# =============================================================================
# 6. LAKEFLOW / DLT — 2E EXPECTATIONS LAB (prepped 2026-07-07, Free Edition)
# Goal: mini bronze->silver Lakeflow pipeline; watch expectations WARN vs DROP.
# Runs as a PIPELINE (not cell-by-cell): Step 2 is the pipeline source notebook;
# create an ETL pipeline pointing at it and Start.
# =============================================================================

# --- Step 1 — sample data (run once in a NORMAL notebook) ---
# 5 rows, 2 intentionally bad (row 3 no name, row 4 zip too short).
"""
data = [
    (1, "Alice", "12345"),   # good
    (2, "Bob",   "67890"),   # good
    (3, None,    "11111"),   # bad: no name   -> dropped by expect_or_drop
    (4, "Dana",  "1"),       # bad: short zip -> only warned by expect
    (5, "Eve",   "54321"),   # good
]
df = spark.createDataFrame(data, ["patient_id", "name", "zip_code"])
df.write.mode("overwrite").saveAsTable("workspace.default.patients_raw")
display(spark.table("workspace.default.patients_raw"))
"""

# --- Step 2 — pipeline source notebook (DO NOT run directly; point a pipeline at it) ---
"""
import dlt
from pyspark.sql import functions as F

@dlt.table(name="patients_bronze")
def patients_bronze():
    return spark.readStream.table("workspace.default.patients_raw")

@dlt.table(name="patients_silver")
@dlt.expect("warn_zip", "length(zip_code) = 5")          # WARN: keep row, count violations
@dlt.expect_or_drop("drop_no_name", "name IS NOT NULL")  # DROP: throw the row out
def patients_silver():
    return dlt.read_stream("patients_bronze")
"""

# --- Step 3 — create & run ---
# Pipelines -> Create pipeline -> ETL -> Source = Step 2 notebook ->
# target catalog=workspace, schema=default -> Start.

# EXPECT / observe:
#   - patients_silver = 4 rows (row 3 dropped by expect_or_drop for null name).
#   - row 4 (short zip) STAYS IN — expect() only warns, doesn't remove.
#   - silver node -> Data quality panel shows per-expectation pass/fail counts.
# OPTIONAL: switch warn_zip to @dlt.expect_or_fail -> whole pipeline FAILS on
#   row 4 (the "system's broken" mode). Then switch back.
#
# heuristic: fail = system's broken (missing key); drop = row's bad (garbage zip);
#            warn = still learning what normal looks like.
#
# -----------------------------------------------------------------------------
# AS-RUN 2026-07-16 (Free Edition, new Lakeflow Pipelines editor)
# -----------------------------------------------------------------------------
# NOTE on tooling: the new "ETL pipeline" flow does NOT use a separate source
# notebook. Create pipeline -> it scaffolds a project folder with a .py file
# under transformations/. That .py file IS the source code — replaced the
# scaffold with the block below. target catalog=workspace, schema=lakeflow_lab.
# `import dlt` + @dlt.table decorators run fine inside the new editor.
#
# Ran an ORDERS variant (not the patients template above) — same lesson:
"""
import dlt
from pyspark.sql import functions as F

@dlt.table(comment="Raw orders — includes intentionally bad rows")
def orders_bronze():
    data = [
        (1, "C001", 250.0),
        (2, "C002", 100.0),
        (3, None,    75.0),   # null customer_id  -> DROP
        (4, "C003", -20.0),   # negative amount    -> WARN only (kept)
        (5, "C004", 500.0),
        (6, None,   None),    # null customer_id   -> DROP
    ]
    return spark.createDataFrame(data, ["order_id", "customer_id", "amount"])

@dlt.table(comment="Cleaned orders")
@dlt.expect("amount_positive", "amount > 0")                        # WARN
@dlt.expect_or_drop("customer_not_null", "customer_id IS NOT NULL") # DROP
def orders_silver():
    return dlt.read("orders_bronze")
"""
# OBSERVED:
#   DROP: orders_bronze=6 -> orders_silver=4. SELECT * confirmed ids 1,2,4,5
#         (orders 3 & 6 with null customer_id removed).
#   WARN: order 4 (amount -20) STAYED IN silver; amount_positive shows 1 failing
#         record but 0 dropped. Proved expect() counts-but-keeps.
#   FAIL: swapped customer_not_null -> @dlt.expect_or_fail, rerun -> whole update
#         went RED. Error: EXPECTATION_VIOLATION.VERBOSITY_ALL, named
#         'customer_not_null', halted on order_id=3 (null). Then reverted to
#         expect_or_drop -> green again.
#   => all three modes (warn / drop / fail) demonstrated end-to-end. 2E lab DONE.

# -----------------------------------------------------------------------------
# 6b. FOLLOW-ON — streaming table vs materialized view IDEMPOTENCY (run 2026-07-16)
# -----------------------------------------------------------------------------
# Q she asked: "is it idempotent — can I change expectations and rerun freely?"
# Answer proven hands-on. Added a SECOND source file (streaming_demo.py) with
# NEW table names so the MV lab above stayed intact (new names => no MV->ST
# type conflict, normal Run works, no full refresh needed on first build).
#
# Setup (normal notebook, batch): built a Delta source table first, because a
# streaming table needs a real streaming source, not an inline list.
"""
data = [(1,"C001",250.0),(2,"C002",100.0),(3,None,75.0),
        (4,"C003",-20.0),(5,"C004",500.0),(6,None,None)]
spark.createDataFrame(data,["order_id","customer_id","amount"]) \
    .write.mode("overwrite").saveAsTable("workspace.lakeflow_lab.orders_raw")
"""
# Pipeline source (streaming_demo.py) — streaming tables (readStream / read_stream):
"""
import dlt
@dlt.table
def orders_bronze_stream():
    return spark.readStream.table("workspace.lakeflow_lab.orders_raw")

@dlt.table
@dlt.expect("amount_positive", "amount > 0")
@dlt.expect_or_drop("customer_not_null", "customer_id IS NOT NULL")
def orders_silver_stream():
    return dlt.read_stream("orders_bronze_stream")
"""
# Append 2 new rows (batch notebook) then rerun pipeline NORMALLY:
"""
new = [(7,"C005",300.0),(8,None,40.0)]
spark.createDataFrame(new,["order_id","customer_id","amount"]) \
    .write.mode("append").saveAsTable("workspace.lakeflow_lab.orders_raw")
"""
# OBSERVED:
#   First build: orders_silver_stream = 4 (all 6 read, 2 null-customer dropped).
#   After appending 2 + NORMAL rerun: silver_stream = 5 (added only order 7;
#     order 8 dropped). It processed ONLY the 2 new rows — checkpoint remembered
#     where it left off. An MV would have re-read all 8.
#
# TAKEAWAY (answer to the idempotency Q):
#   MATERIALIZED VIEW  -> full recompute each run  -> idempotent; a changed rule
#                         re-judges ALL rows automatically.
#   STREAMING TABLE    -> incremental (new data only) -> old rows stay as-written;
#                         a tightened rule only affects FUTURE rows unless you
#                         run FULL REFRESH to replay history.

# =============================================================================
# 7. UNITY CATALOG — 2F GOVERNANCE LAB (run 2026-07-16, Free Edition, SQL)
# Concepts: 3-level namespace, USE-vs-SELECT grants, row filter, column mask,
#           lineage, metastore. All 5 taught + checks passed same day.
# Key grant rule proven: to read a table need USE CATALOG + USE SCHEMA (the
#   "key to the door") AND SELECT (the "contents"). No DENY; deny-by-default.
# is_account_group_member('g') -> TRUE/FALSE per querying user, evaluated at
#   query time. Not in the group => ELSE / filtered branch (perfect solo test).
# =============================================================================

# --- Step 1 — schema + PII table ---
"""
CREATE SCHEMA IF NOT EXISTS workspace.uc_lab;
CREATE OR REPLACE TABLE workspace.uc_lab.patients (
  patient_id INT, name STRING, ssn STRING, state STRING, diagnosis STRING);
INSERT INTO workspace.uc_lab.patients VALUES
  (1,'Alice','111-22-3333','CA','Diabetes'),
  (2,'Bob',  '222-33-4444','NY','Hypertension'),
  (3,'Cara', '333-44-5555','CA','Asthma'),
  (4,'Dan',  '444-55-6666','TX','Flu');
"""

# --- Step 2 — COLUMN MASK on ssn (PII) ---
"""
CREATE OR REPLACE FUNCTION workspace.uc_lab.mask_ssn(ssn STRING)
RETURN CASE WHEN is_account_group_member('hr') THEN ssn
            ELSE 'XXX-XX-' || right(ssn, 4) END;
ALTER TABLE workspace.uc_lab.patients
  ALTER COLUMN ssn SET MASK workspace.uc_lab.mask_ssn;
"""
# OBSERVED: not in 'hr' => SSNs displayed as XXX-XX-#### (base data untouched). ✅

# --- Step 3 — ROW FILTER (only CA rows unless auditor) ---
"""
CREATE OR REPLACE FUNCTION workspace.uc_lab.filter_ca(state STRING)
RETURN is_account_group_member('auditors') OR state = 'CA';
ALTER TABLE workspace.uc_lab.patients
  SET ROW FILTER workspace.uc_lab.filter_ca ON (state);
"""
# OBSERVED: not in 'auditors' => table dropped to 2 rows (Alice, Cara / CA). ✅

# --- Step 4 — real GRANT (built-in 'account users' = everyone) ---
"""
GRANT USE CATALOG ON CATALOG workspace           TO `account users`;
GRANT USE SCHEMA  ON SCHEMA  workspace.uc_lab     TO `account users`;
GRANT SELECT      ON TABLE   workspace.uc_lab.patients TO `account users`;
"""

# --- Step 5 — LINEAGE ---
# Catalog Explorer -> workspace.lakeflow_lab.orders_silver_stream -> Lineage tab
# -> auto-captured graph orders_raw -> orders_bronze_stream -> orders_silver_stream.
#
# cleanup (optional): ALTER TABLE ... DROP ROW FILTER;
#                     ALTER TABLE workspace.uc_lab.patients ALTER COLUMN ssn DROP MASK;
#
# => 2F Unity Catalog COMPLETE (concepts + lab). Next Pillar 2 stage: 2G Auto Loader.
