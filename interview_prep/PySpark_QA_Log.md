# PySpark / Spark — Q&A Log

Running log of questions asked during learning sessions, with answers. Newest date at bottom. Refresh anytime.

2026-06-02 — Stage 2B, PySpark SQL (Lesson 3)

Refresh me on lazy vs wide (transformations).

"Wide vs lazy" are two different axes, not opposites.

**Axis 1 — Lazy vs eager (WHEN work happens)**

  * **Transformations are lazy** — `select`, `filter`, `withColumn`, `groupBy`, `join`, `spark.sql("SELECT…")` just record a recipe (build the DAG). Nothing runs.
  * **Actions are eager** — `show()`, `count()`, `collect()`, `write` — trigger the whole recipe to execute.
  * Payoff: Spark sees the full plan before running, so Catalyst optimizes across steps (push filters down, pick join strategy).



**Axis 2 — Narrow vs wide (HOW MUCH data moves across the network)**

  * **Narrow** — each input partition feeds one output partition. No network movement. `select`, `filter`, `withColumn`. Cheap.
  * **Wide** — output partitions pull from many input partitions → **shuffle** (data sent across executors). `groupBy`, `join` (non-broadcast), `orderBy`, `distinct`. Expensive — the #1 thing you tune.
  * A **stage boundary** is exactly where a shuffle happens. Count shuffles → count stages.



**How they combine in Lesson 3:**

Operation| Lazy/eager| Narrow/wide  
---|---|---  
`SELECT … WHERE`| lazy until `.show()`| narrow  
`GROUP BY`| lazy until `.show()`| **wide** (shuffle)  
`ORDER BY`| lazy until `.show()`| **wide** (shuffle)  
`JOIN`| lazy until `.show()`| **wide** — unless broadcast (tiny `coin_meta` → BroadcastHashJoin, no shuffle)  
  
Full reference: `~/Downloads/Spark_Architecture_Walkthrough.html`

* * *

What does this do? `spark = (SparkSession.builder.appName("…").getOrCreate())`

It creates (or reuses) the SparkSession — the entry point every DataFrame/SQL call goes through.
    
    
    spark = (
        SparkSession.builder              # a configurator to set up a session
        .appName("FinFlow_Lesson3_SQL")   # name shown in Spark UI (localhost:4040)
        .getOrCreate()                    # build it — or hand back the existing one
    )

  * **`SparkSession.builder`** — a configurator you chain settings onto (app name, configs, master URL). Nothing exists yet.
  * **`.appName(...)`** — labels the application; purely for identification in the Spark UI and logs.
  * **`.getOrCreate()`** — the actual build. "Get" the active session if one exists in this process, else "create" one. A JVM allows only one active session, so re-running won't spin up duplicates or error.



**What you get back (`spark`):** the handle that owns `spark.read.json(...)`, `spark.sql("…")`, and launches the Driver + Spark UI on `localhost:4040`. This `spark` object _is_ the Driver's entry point — builds the DAG, hands tasks to executors. Creating it is setup, not an action — nothing computes here.

The outer parentheses are just Python letting you split a chained call across lines for readability — no Spark meaning.

* * *

Why is the path wrapped in `str(...)`? `DATA = str(Path.home() / "Downloads" / … / "sample.jsonl")`

Because `Path.home() / "…"` produces a PosixPath object, and Spark's reader wants a plain **string**.

  * **`Path.home()`** → a `Path` object (`/Users/sayantaninath`).
  * **`/ "Downloads" / …`** → the `/` operator is overloaded on `Path` to join segments. Still a `Path`, not text. (Readable, OS-agnostic joins — the nice part of `pathlib`.)
  * **`str(...)`** → flattens it into the real string `"/Users/sayantaninath/Downloads/…/sample.jsonl"`.



**Why Spark needs the string:** `spark.read.json(path)` hands the path **across to the JVM** (Spark's engine is Scala/Java). The JVM doesn't understand a Python `PosixPath` — it expects a Java string. Pure-Python libs like `pandas.read_json` accept a `Path` directly (they honor `os.PathLike`); the Python→JVM boundary doesn't, so you convert explicitly. Skip the `str()` and you'd likely hit a `py4j` type error.

**Pattern:** use `pathlib` to build the path readably, wrap in `str()` at the moment you hand it to Spark.
    
    
    p = Path.home() / "Downloads"
    print(type(p))        # <class 'pathlib.PosixPath'>
    print(type(str(p)))   # <class 'str'>

* * *

What's the alternative to `show(n)` to show ALL records?

`df.show()` defaults to 20 rows and truncates long columns at 20 chars. To show all:
    
    
    df.show(df.count())                 # pass the exact row count as n
    df.show(df.count(), truncate=False) # + full untruncated column values

Method| Returns| When to use  
---|---|---  
`df.show(df.count())`| prints, nothing returned| quick visual scan of all rows  
`df.collect()`| Python list of Row objects| pull data to driver to loop/process  
`df.toPandas()`| pandas DataFrame| nicer display (notebooks), pandas ops  
  
⚠️ The catch: all three pull every row to the Driver — an **action** that can blow up driver memory or hang on a big table. Fine on 6 rows, dangerous in production. `df.show(20)` exists so you peek cheaply without dragging the whole dataset back.

`truncate=False` is the flag you'll reach for most — keeps timestamps and names from being cut off.

* * *

Difference between using the DataFrame API and Spark SQL?

Two front-ends to the same engine — no performance difference. Both compile through the same Catalyst optimizer to the same physical plan.
    
    
    # DataFrame API
    df.select("coin", "price_usd").filter(F.col("price_usd") > 1000)
    
    # Spark SQL — identical result, identical plan
    spark.sql("SELECT coin, price_usd FROM prices WHERE price_usd > 1000")

Run `.explain()` on both → same physical plan (that's Ex 10 in Lesson 3).

**Why have both? About how you write/read code, not speed:**

| DataFrame API| Spark SQL  
---|---|---  
Looks like| Python method chaining| SQL strings  
Errors caught| compile/build time (bad method name fails immediately)| runtime (bad SQL fails only when query runs)  
Composability| great — build `df` step by step, reuse, pass to functions| weaker — string concatenation gets ugly  
Complex logic readability| nested chains get hard to read| complex joins/aggs often read cleaner  
Who reaches for it| Python engineers, programmatic pipelines| analysts, SQL-first, ad-hoc queries  
IDE support| autocomplete, type hints| just a string — no help  
  
**Guidance:** DataFrame API for dynamically-built logic (loops/conditionals/reusable fns) or compile-time safety; Spark SQL for gnarly multi-join/aggregation queries that read cleaner as SQL or SQL-fluent collaborators. **Mix freely** — `createOrReplaceTempView` flips a DataFrame into SQL and back (common: heavy transforms in the API, final aggregation in SQL).

Interview takeaway: "Same engine, same Catalyst plan, same performance — choice is readability, composability, and compile-time vs runtime error checking." Proving equivalence with `.explain()` is what they're testing.

* * *

What is Iceberg, Hudi, Trino?

Iceberg & Hudi are table formats; Trino is a query engine — different layers of the stack.

**The problem they exist for:** a raw data lake is just Parquet files in object storage (S3). Files alone give no transactions, no time travel, no safe concurrent writes. The lakehouse stack fixes that.

**Table formats — Iceberg & Hudi (and Delta)** — a metadata layer on top of Parquet files that turns a pile of files into a real table with: ACID transactions, time travel (query old snapshots), schema evolution, and MERGE/upserts/deletes.

Format| Born at| Sweet spot| Ecosystem  
---|---|---|---  
Delta| Databricks| tight Databricks/Spark integration| Databricks  
Iceberg| Netflix| huge tables, engine-neutral, hidden partitioning| Apple, Netflix, Snowflake, AWS — momentum winner  
Hudi| Uber| streaming upserts, CDC, incremental pulls| Uber, Robinhood  
  
Same problem; differences are partition handling, how updates are stored, and which engines/vendors back them.

**Trino** — a distributed SQL query engine (formerly PrestoSQL), _not_ a storage format. Doesn't store data; runs fast SQL _across_ data wherever it lives. Superpower: **federation** — one query can join S3 (Iceberg/Hudi/Delta) + PostgreSQL + MySQL. "The SQL brain you point at many sources," vs Spark which is more a general compute/ETL engine.

Interview takeaway: table format (Delta/Iceberg/Hudi) = ACID + time travel on lake files; query engine (Trino, Spark SQL, Athena) = runs SQL over them. "Why Iceberg?" → engine-neutral + scales to massive tables + industry momentum. "Why Delta?" → best if all-in on Databricks.

## show() vs display()

Q: What is the difference between `show()` and `display()` in Spark?

**Both show data from a DataFrame — but they work in different environments.**

`show()` — PySpark, works anywhere
    
    
    df.show()                  # first 20 rows (default)
    df.show(5)                 # first 5 rows
    df.show(truncate=False)    # don't cut off long strings

Output is plain text in the terminal or console.

`display()` — Databricks notebooks only
    
    
    display(df)

Output is a rich interactive table — sortable columns, filter, chart view (bar/line/pie), download as CSV. Not available outside Databricks.

| show()| display()  
---|---|---  
Works in| Anywhere (terminal, script, notebook)| Databricks notebooks only  
Output| Plain text table| Interactive UI table  
Charts| ❌ No| ✅ Yes — built-in  
Truncates long strings| Yes (use truncate=False to disable)| No — shows full content  
Use in production scripts| ✅ Yes| ❌ No  
  
Rule: In Databricks → `display()`. In a local script or terminal → `show()`.

## PySpark vs Flink vs Presto/Trino — when to use which

Q: When do you use PySpark vs Flink vs Presto/Trino?

| PySpark| Flink| Presto/Trino  
---|---|---|---  
Best for| Batch ETL, ML, large-scale transforms| True real-time streaming (sub-second)| Fast ad-hoc SQL on existing data  
Processing model| Micro-batch or batch| Continuous, event-by-event| Query engine only — no pipeline  
Latency| Seconds to minutes| Milliseconds to seconds| Seconds (query time)  
Stores data?| No| No| No — queries data where it lives  
Typical use| DW pipelines, Delta Lake, feature engineering| Fraud detection, real-time alerts, CDC| BI dashboards, cross-source federation  
  
**PySpark** — data is large, you need transformations + joins + aggregations, seconds of latency is fine. 90% of DE work.

**Flink** — true sub-second real-time needed (fraud scoring per transaction as it happens). More operationally complex than Spark Streaming.

**Presto/Trino** — data already exists in S3/Delta/Iceberg/Postgres and you want fast SQL without moving it. Superpower: federation — one query across multiple sources.

Interview one-liner: PySpark = batch/streaming ETL engine. Flink = true real-time streaming engine. Presto/Trino = fast SQL query engine across existing data stores. They solve different problems and often coexist in the same stack.

## Delta Lake — OCC (Optimistic Concurrency Control)

Q: Two writers start at the same time. Writer A commits first. Does Writer B retry automatically or throw ConcurrentModificationException?

**Delta throws — it does NOT retry automatically.**

Delta uses optimistic concurrency: writers don't lock the table upfront. When B tries to commit, Delta checks: _do B's read/write files overlap with what A just modified?_

Scenario| Result  
---|---  
B's files overlap with A's changed files| Delta throws `ConcurrentModificationException` — your code must retry  
B's files don't overlap (e.g. different partitions)| B's commit succeeds — both writers coexist  
  
Key point: Retry is your application's responsibility. Delta only detects and reports the conflict — it does not auto-retry.

Common wrong answer: "B retries automatically." Delta throws; you retry.

## Delta Lake — VACUUM Retention Horizon

Q: A table has commits 0–25. You run VACUUM with default settings. What is the earliest version Delta keeps data files for?

**VACUUM is time-based, not commit-count-based.**

It removes data files (Parquet) that are no longer referenced by any version _within the last 7 days_ (default retention). Commit numbers don't matter — only timestamps do.

  * If all 26 commits happened in the last 3 days → VACUUM removes nothing.
  * If commits 0–10 happened 2 weeks ago → those versions' Parquet files may be removed.



**What VACUUM touches:** Parquet data files only. The `_delta_log` is untouched. Time travel uses the log to reconstruct versions — but if the Parquet files have been vacuumed, the read will fail.

Common wrong answer: "Earliest version is commit 20" — you can't derive a version number from a retention window without knowing timestamps.

## Delta Lake — VACUUM Commands (all variants)

Q: What are the VACUUM command variants in Delta Lake?
    
    
    -- Default (7-day retention)
    VACUUM my_table
    
    -- Custom retention
    VACUUM my_table RETAIN 336 HOURS       -- 14 days
    VACUUM my_table RETAIN 168 HOURS       -- 7 days (explicit)
    
    -- Dry run — shows what WOULD be deleted, deletes nothing
    VACUUM my_table DRY RUN
    
    -- Go below 7 days (disables safety check — breaks time travel)
    SET spark.databricks.delta.retentionDurationCheck.enabled = false;
    VACUUM my_table RETAIN 0 HOURS;

Rule: Always run `DRY RUN` first on production tables. Never go below 7 days unless you explicitly don't need time travel for that table.

## Delta Lake — MERGE Write Amplification

Q: You MERGE 1,000 rows into a Delta table with 500 Parquet files. Only 20 files contain matching rows. How many files are rewritten? Why is this a problem at scale?

**All 20 files are rewritten in full — even if each file had only 1 matching row.**

Parquet files are immutable. Delta cannot update a single row in-place. For every file that contains at least one match, Delta must:

  1. Read the entire file
  2. Apply the change to the matching rows
  3. Write a brand new Parquet file
  4. Mark the old file as deleted in `_delta_log`



The other 480 files are untouched.

**The scale problem:** If those 20 files are 1 GB each → 20 GB of I/O for a 1,000-row change. Actual data changed is tiny; write cost is enormous.

Mitigation| Why it helps  
---|---  
Partition on merge key| Delta prunes to relevant partitions — far fewer files touched  
Z-ORDER on merge key| Co-locates matching rows into fewer files  
OPTIMIZE before large MERGE| Compaction → fewer files → less file-open overhead  
  
Interview one-liner: MERGE rewrites every touched file in full because Parquet is immutable. Partition + Z-ORDER on your merge key to minimize how many files get touched.

## Spark Cluster Sizing & Partitioning — Classic Interview Question

Q: You have a Spark cluster with 5 executors, 4 cores each, 16 GB memory each. You need to process a 300 GB dataset. How would you plan partitioning, parallelism, memory usage, and performance tuning?

#### Step 1 — Establish resources
    
    
    5 executors × 4 cores  = 20 total task slots
    5 executors × 16 GB    = 80 GB total memory
    Dataset                = 300 GB

#### Step 2 — Input partitioning

Target partition size = 128–200 MB (`maxPartitionBytes = 128 MB` default).
    
    
    300 GB / 128 MB = ~2,400 input partitions
    2,400 / 20 cores = 120 waves of tasks   ← healthy
    
    
    spark.conf.set("spark.sql.files.maxPartitionBytes", "134217728")  # 128 MB

#### Step 3 — Shuffle partitions

Default 200 shuffle partitions → 300 GB / 200 = 1.5 GB per partition → too large, will spill.

Fix: target 200 MB per shuffle partition → 300 GB / 200 MB = ~1,500 partitions.
    
    
    # Manual
    spark.conf.set("spark.sql.shuffle.partitions", "1500")
    
    # Or enable AQE (Spark 3+) and let it coalesce dynamically
    spark.conf.set("spark.sql.adaptive.enabled", "true")
    spark.conf.set("spark.sql.shuffle.partitions", "2000")  # set high, AQE coalesces

#### Step 4 — Memory breakdown per executor

Layer| Calculation| Amount  
---|---|---  
Total heap| executor memory| 16 GB  
Reserved (hardcoded)| Spark internal| 300 MB  
Usable heap| 16 GB − 300 MB| ~15.7 GB  
Unified pool (execution + storage)| 60% of usable| ~9.4 GB  
User memory (UDFs, data structures)| 40% of usable| ~6.3 GB  
**Per-task unified memory**|  9.4 GB / 4 cores| **~2.35 GB/task**  
  
2.35 GB per task for 128 MB partitions = ~18× headroom. If you see spill in Spark UI, partitions are too large or joins are blowing up the hash table.
    
    
    spark.conf.set("spark.executor.memoryOverhead", "2g")  # prevent container OOM kills

#### Step 5 — Performance tuning checklist

Lever| When| Config / Action  
---|---|---  
Broadcast join| Small table < 10 MB| `spark.sql.autoBroadcastJoinThreshold = 10485760`  
AQE skew join| Max task >> median in Spark UI| `spark.sql.adaptive.skewJoin.enabled = true`  
Salting| Known skewed key, no AQE| Append random suffix to join key — see salting section below  
Kryo serialization| Always| `spark.serializer = org.apache.spark.serializer.KryoSerializer`  
Caching| Dataset reused 2+ times| Cache derived aggregations only — 300 GB won't fit in 80 GB cluster  
  
Interview answer (say out loud): "With 20 cores I'd target 2,400 input partitions at 128 MB each — 120 task waves. For shuffles I'd set 1,500 partitions to keep each around 200 MB, or enable AQE to tune it dynamically. Each executor gets ~2.35 GB per task for execution memory — enough for these partition sizes without spilling. I'd watch the Spark UI for skew and spill, use broadcast joins for small tables, and enable AQE skew join handling as a safety net."

## Data Skew — Salting Pattern

Q: What is data skew, how do you detect it, and how does salting fix it?

#### What is skew?

Skew happens when one partition holds far more rows than others — usually because a join or groupBy key has a highly unequal value distribution (e.g., a "unknown" customer_id representing 40% of all rows). One task takes 10× longer than all others → the whole stage waits for it.

#### How to detect

  * Spark UI → Stages → Tasks tab: sort by Duration. If max task duration >> median → skew.
  * Shuffle Read Size: Min/Median vs Max. A 16× ratio (e.g. median 2,596 rows, max 41,468 rows) is textbook skew.
  * Many empty partitions (median = 0 B) is also a sign — data is piled into a few partitions.


    
    
    # Detect skew in code — check partition sizes
    from pyspark.sql.functions import spark_partition_id, count
    
    df.groupBy(spark_partition_id().alias("partition_id")) \
      .agg(count("*").alias("row_count")) \
      .orderBy("row_count", ascending=False) \
      .show(20)

#### Salting — fix for join skew

Append a random integer (the "salt") to the skewed key before joining. This spreads one hot partition across N partitions. The other table gets replicated N times to match.
    
    
    from pyspark.sql.functions import col, floor, rand, lit, explode, array
    
    SALT_BUCKETS = 9  # ceil(max_partition_rows / target_rows) = ceil(41468 / 5000)
    
    # Skewed side: append random salt 0..8 to join key
    skewed_df = skewed_df.withColumn(
        "salted_key",
        concat(col("customer_id"), lit("_"), (floor(rand() * SALT_BUCKETS)).cast("int"))
    )
    
    # Other side: explode to replicate each row N times with salt 0..8
    other_df = other_df.withColumn(
        "salted_key",
        explode(array([concat(col("customer_id"), lit(f"_{i}")) for i in range(SALT_BUCKETS)]))
    )
    
    # Join on salted key
    result = skewed_df.join(other_df, "salted_key")

#### Salting for groupBy skew (two-pass aggregation)

When the hot key is in a groupBy (not a join), use a two-pass approach:
    
    
    # Pass 1 — partial aggregation with salt (spreads the hot key)
    partial = df.withColumn("salt", (floor(rand() * SALT_BUCKETS)).cast("int")) \
                .groupBy("customer_id", "salt") \
                .agg(sum("amount").alias("partial_sum"))
    
    # Pass 2 — final aggregation drops salt
    result = partial.groupBy("customer_id").agg(sum("partial_sum").alias("total_amount"))

#### SALT_BUCKETS formula
    
    
    # From Spark UI: max partition rows = 41,468 | target = 5,000 rows/partition
    SALT_BUCKETS = ceil(41468 / 5000) = ceil(8.29) = 9

#### AQE vs manual salting

| AQE Skew Join| Manual Salting  
---|---|---  
Effort| Zero — just enable the config| Code change required  
Works for| Joins only (Spark 3.0+)| Joins + groupBy  
Detectability| Spark detects skew at runtime| You control the logic  
Use when| Spark 3+, standard join skew| Spark 2.x, groupBy skew, or AQE not tuned right  
  
Interview one-liner: "Salting distributes a hot key across N partitions by appending a random integer — the other side is replicated N times to match. For Spark 3+ I'd enable AQE first; salting is the fallback for groupBy skew or older clusters."

## Unity Catalog — What is a Catalog? (asked 2026-07-06, during 2D Ex-5 lab)

Q: What is a catalog in Databricks?

**The top level of Unity Catalog's three-level namespace:** `catalog.schema.table` — a "database of databases."

  * **Catalog** — top-level container; groups schemas
  * **Schema** (= database) — groups tables, views, and volumes
  * **Table / view / volume** — the actual objects



Example from the Ex-5 lab: `workspace.default.ex5_rate_sink` → catalog `workspace` (Free Edition's default) → schema `default` → table `ex5_rate_sink`. The checkpoint path `/Volumes/workspace/default/mydata` is the same namespace — `mydata` is a _volume_ object in that same schema.

**Why catalogs exist:** they're the governance boundary. Teams separate environments (`dev`/`staging`/`prod`) or business units by catalog, and grants cascade down:
    
    
    GRANT SELECT ON CATALOG prod TO analysts;   -- applies to every schema/table inside

Note: Full Unity Catalog coverage (RBAC, row filters, column masks, lineage) is Stage 2F — this entry is just the namespace piece.

Q: What does a volume do? (asked 2026-07-06, during 2D Ex-5 lab)

**A volume is Unity Catalog's container for non-tabular files** — the file-system counterpart to a table.

| Table| Volume  
---|---|---  
Holds| Rows/columns Spark manages| Arbitrary files: CSVs, checkpoints, logs, models, images  
Access| SQL / DataFrame API| Path: `/Volumes/<catalog>/<schema>/<volume>/...`  
Governance| UC grants, lineage, audit| Same — unlike ungoverned DBFS/raw S3 paths  
  
Lives in the same three-level namespace: `workspace.default.mydata` = catalog.schema.**volume**.

Why the Ex-5 lab uses one: a streaming checkpoint needs a durable directory to write `offsets/` and `commits/` into; in Free Edition the sanctioned file-storage location is a volume — hence `ckpt = "/Volumes/workspace/default/mydata/ex5_ckpt"`.

Q: What's the syntax of the writeStream chain? (asked 2026-07-06, during 2D Ex-5 lab)
    
    
    query = (df.writeStream
        .format("delta")                          # sink type: delta | kafka | console | memory | parquet
        .option("checkpointLocation", "/path")    # sink options — checkpoint required for durable sinks
        .outputMode("append")                     # append | update | complete
        .trigger(processingTime="5 seconds")      # optional — default is "next batch ASAP"
        .start("/output/path"))                   # ← THE ACTION — nothing runs until this line

  * Builder methods before the terminal call are lazy config, any order; **`.start()` launches the stream** (streaming twin of `.write.save()`).
  * `.toTable("catalog.schema.table")` is an alternative terminal call — same action, but targets a UC _table name_ instead of a raw path.
  * Returns a `StreamingQuery` handle: `query.stop()`, `query.status`, `query.lastProgress`.



## Photon Recap + Catalyst / Tungsten / Photon Layer Map (asked 2026-07-06, pre-2E recap)

Q: What are Catalyst and Tungsten, and where does Photon fit?

Layer| Job| Analogy  
---|---|---  
**Catalyst**|  The **planner** — takes DataFrame/SQL code, decides _what_ to do and in what order. 4 phases: Analysis → Logical Optimization (filter pushdown, column pruning) → Physical Planning (BHJ vs SMJ) → Code Generation| Architect drawing the blueprint  
**Tungsten**|  The classic **executor** — runs the plan on the JVM. Tricks: off-heap memory (dodges GC), whole-stage code generation (fuses a stage's operators into one function — the `*(1)` in explain output)| Construction crew  
**Photon**|  Replacement executor in **C++** , vectorized + columnar. Same blueprint, faster crew| Better construction crew  
  
Key sentence: Photon replaces **Tungsten (execution)** , not **Catalyst (planning)**. Catalyst still plans every query; Photon executes the plan faster where it can.

Q: What is Photon? (recap — taught in 2B §22)

Databricks' rewrite of Spark's execution engine in **C++**. Code doesn't change — same PySpark/SQL — only execution swaps.

  * **Vectorized** — processes batches of column values with CPU SIMD ("one instruction, many values") instead of row-at-a-time.
  * **Columnar** — operates on columns in memory, matching Parquet/Delta layout and CPU cache behavior.
  * **Activates per-operator** , not all-or-nothing: scans/filters/joins/aggregations on Delta/Parquet → Photon; RDD API, most Python UDFs, exotic functions → fall back to JVM Spark mid-query. `EXPLAIN` shows `Photon`-prefixed operators.
  * **Why:** 2–8x on SQL/DataFrame workloads, zero code change. Higher DBU rate but usually net cheaper (finishes faster).



Q: A pipeline has a heavy groupBy().agg() and a Python UDF in one withColumn — what does Photon do with each?

The `groupBy().agg()` runs **in Photon** (supported). The Python UDF **can't run in C++** — that operator **falls back to JVM Spark**. One query, mixed execution; the seam is visible in `EXPLAIN`.

Practical consequence: replace Python UDFs with built-in functions where possible, or you lose Photon exactly on your most expensive step.

Q: Why does vectorized + columnar beat row-at-a-time on modern CPUs?

Row-at-a-time: the CPU handles one value, checks what to do, moves on — high overhead per value. Vectorized: load a batch of one column's values and apply **one SIMD instruction to many values at once**. Columnar layout puts those batches contiguously in memory → CPU cache stays hot. Less overhead per value + hardware parallelism = the 2–8x.

Q: Stateless vs stateful streams — what's the difference and why does it matter? (asked 2026-07-06 and again 2026-07-07 — retention flag)

**Stateless** — each row processed on its own; Spark remembers nothing between micro-batches. `filter`, `select`, `map`. Batch 7 needs nothing from batches 1–6.

**Stateful** — the answer depends on rows from earlier batches, so Spark carries memory forward in the checkpoint's `state/` folder. `groupBy(window(...)).count()`: batch 7's job is "add these events to the totals so far" — the totals ARE the state.

**Why it matters (checkpoint deletion):**

  * Stateless → worst case reprocessing/duplicates — visible, fixable.
  * Stateful → window counts / watermark / dedup history gone; counts restart from zero mid-window; job reports a plausible-looking **wrong** number with no error — _silently wrong_.



The trap: `dropDuplicates("order_id")` looks stateless but is **stateful** — it must remember every order_id ever seen. Checkpoint gone → old duplicates sail through → double-counted revenue downstream.

Rule of thumb: if this batch requires remembering anything from previous batches — aggregation, window, dedup, stream-stream join — it's stateful.
