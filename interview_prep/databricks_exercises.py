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
# AS-RUN RESULTS (fill after running): _______________________________________
