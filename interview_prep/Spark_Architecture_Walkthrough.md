# Spark Architecture — Walkthrough

Personal study notes — taught in-chat session, 2026-05-28.

**Contents**

  1. Why Spark exists
  2. The mental model
  3. The cluster — Driver, Executors, Cluster Manager
  4. Partitions
  5. Transformations vs Actions (lazy evaluation)
  6. Narrow vs Wide (shuffles)
  7. Jobs, Stages, Tasks & the DAG
  8. The `count` ambiguity
  9. Broadcast joins — Scenarios A, B, C
  10. Stage-counting recipe
  11. From-blank exercises
  12. Sidebar: byte calculations in Spark configs
  13. Interview takeaways



## 1\. Why Spark exists

Imagine you have **1 TB of CSV files** in S3 and a laptop with 16 GB RAM. Pandas can't load it — your process dies. Two options:

  * **Scale up** — buy a bigger machine. Works up to ~1 TB. Expensive, single point of failure.
  * **Scale out** — split the data across 50 cheaper machines, work in parallel. This is Spark.



Spark = "Pandas, but the data and the compute live across many machines." Everything else is a consequence of that idea.

## 2\. The mental model

Two shifts from Pandas:

  * **Distributed.** Your DataFrame lives as chunks called _partitions_ spread across many workers.
  * **Lazy.** Writing `df.filter(...)` doesn't execute. Spark just records the instruction. Computation only starts on an _action_.



> Pandas = one machine, eager. Spark = many machines, lazy.

## 3\. The cluster — Driver, Executors, Cluster Manager

Role| What it does| Where  
---|---|---  
**Driver**|  Runs your Python code, builds the plan, sends work, collects results.| One machine (or the notebook).  
**Executors**|  Worker processes. Each holds partitions in memory and runs computations.| Many machines, usually one per worker node.  
**Cluster manager**|  Provisions executors, allocates CPU/memory.| YARN / Kubernetes / Databricks-managed.  
  
Entry point — every Spark program starts with a `SparkSession`:
    
    
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.appName("finflow").getOrCreate()

`spark` is your handle to the cluster. In Databricks, it's created for you.

## 4\. Partitions — the unit of parallelism

A Spark DataFrame is a collection of **partitions** — chunks of rows. Each partition lives on one executor; each is processed by one CPU core at a time as a **task**.

Example: reading 200 JSONL files may give 200 partitions. A 50-core cluster runs 50 tasks at a time, finishing in ~4 waves.

  * Too few partitions → executors idle.
  * Too many tiny partitions → scheduling overhead.
  * Sweet spot: 2–4× total core count.


    
    
    df.rdd.getNumPartitions()                     # current count
    spark.conf.get("spark.sql.shuffle.partitions")     # default for post-shuffle
    spark.conf.set("spark.sql.shuffle.partitions", "50")

## 5\. Transformations vs Actions (lazy evaluation)

Category| Behavior| Examples  
---|---|---  
**Transformations**|  Lazy — just record intent| `select`, `filter`, `withColumn`, `groupBy`, `join`, `orderBy`  
**Actions**|  Eager — trigger execution| `show`, `count`, `collect`, `take`, `write.parquet`  
  
You can chain 50 transformations and Spark does nothing until the action. Then it optimizes the whole chain together via Catalyst (the optimizer).

## 6\. Narrow vs Wide (the shuffle thing)

| Narrow| Wide  
---|---|---  
Dependency| Each output partition ← 1 input partition| Each output partition ← many input partitions  
Network| No data movement| Data crosses the network (**shuffle**)  
Cost| Cheap| 10–100× more expensive  
Examples| `filter`, `select`, `withColumn`, `map`| `groupBy`, `join`, `orderBy`, `distinct`, `repartition`  
  
**Performance game:** minimize shuffles. Every Spark interview eventually circles to this.

## 7\. Jobs, Stages, Tasks & the DAG

When you call an action, Spark builds an execution plan:
    
    
    Action  →  1 Job
    Job     →  N Stages     (split at every shuffle boundary)
    Stage   →  M Tasks      (one task per partition, all parallel)

  * **Job** = everything triggered by one action.
  * **Stage** = a run of narrow ops with no shuffles in between.
  * **Task** = smallest unit; one task processes one partition.



The graph of stages = the **DAG** (Directed Acyclic Graph). Each shuffle is a stage boundary. **Spark UI** visualizes all of this — the #1 tool for debugging slow jobs.

## 8\. The `count` ambiguity

Three different `count`s exist in Spark — memorize this:

Expression| Type| Lazy or Action?| Returns  
---|---|---|---  
`df.count()`| DataFrame method| **Action** — triggers a Job| Python int  
`count("*")` from `pyspark.sql.functions`| Column function| **Lazy** — column expression| Column object  
`df.groupBy("k").count()`| Method on GroupedData| **Lazy** — returns DataFrame| DataFrame  
  
**Interview classic:** "Does `df.groupBy('x').count().show()` trigger one Job or two?"  
**Answer:** one. The `.count()` here is the grouped-count shorthand (lazy). The action is `.show()`. 

## 9\. Broadcast joins — Scenarios A, B, C

### Scenario A — small dim, no hint
    
    
    transactions  # 500 GB, ~5000 partitions
    users         # 3 MB
    
    transactions.join(users, on="user_id", how="inner") \
                .filter(col("country") == "US") \
                .count()

Spark **auto-broadcasts** users (3 MB < default 10 MB threshold). Strategy = `BroadcastHashJoin`. No shuffle of the big side.

Stage 0 — Broadcast prep (1 task) read users.parquet → collect → ship to every executor Stage 1 — Main work (~5000 tasks) read transactions partition → join inline with broadcasted users → filter(country == "US") → partial count Stage 2 — Final aggregation (1 task) combine partial counts → single integer

### Scenario B — explicit `broadcast()` hint
    
    
    from pyspark.sql.functions import broadcast
    transactions.join(broadcast(users), on="user_id", how="inner") \
                .filter(col("country") == "US") \
                .count()

Same execution plan as A, but **guaranteed**. Why force it even when auto-broadcast would work?

  1. **Stale statistics** — Spark may think users is 500 MB if old stats say so.
  2. **No statistics at all** — views, CTEs, fresh tables → Spark has no size estimate and defaults to SortMergeJoin.
  3. **Compression mismatch** — on-disk Parquet is small; in-memory is 5–10× larger.
  4. **Push beyond threshold** — 50 MB is still safe to broadcast on a beefy cluster; default 10 MB is conservative.
  5. **Self-documenting code** — reader sees the strategy without checking Spark UI.



### Scenario C — 50 MB dim, no hint
    
    
    users_50mb  # 50 MB (above 10 MB threshold)
    transactions.join(users_50mb, on="user_id", how="inner").count()

Spark **will NOT auto-broadcast** (50 MB > 10 MB). Falls back to `SortMergeJoin`, which shuffles 500 GB of transactions plus 50 MB of users. Wasteful — 50 MB easily fits in every executor's memory.

**Fix:** force `broadcast(users_50mb)** — affects only this query, self-documenting.  
Alternative: `spark.conf.set("spark.sql.autoBroadcastJoinThreshold", 100 * 1024 * 1024)` but this changes every join in the session. 

## 10. Stage-counting recipe

> A stage is a chunk of work that can run end-to-end without data moving between machines. Every shuffle = stage boundary.

### Step-by-step

  1. **Find every wide op** in your code (groupBy, join-SMJ, orderBy, distinct, repartition, window-with-partitionBy).
  2. **Each wide op = one stage boundary.**
  3. **SortMergeJoin:** each input side = its own pre-shuffle stage (because both sides must shuffle-write).
  4. **BroadcastHashJoin:** small side adds a tiny broadcast stage (1 task). Big side does NOT add a boundary.
  5. **Aggregating actions** (`count`, `sum`, `collect`) add a tiny final "combine" stage.



### Worked example — broadcast join
    
    
    transactions.join(users_small, on="user_id").filter(...).count()
    # Stages: broadcast prep (1) + main (~5000) + final combine (1) = 3

### Worked example — SortMergeJoin
    
    
    transactions.join(users_big, on="user_id").filter(...).count()
    # Stages: read transactions+shuffle (1) + read users+shuffle (1)
    #       + join+filter+partial count (1) + final combine (1) = 4

### Mental shortcut

Walk the code top-to-bottom. For each op, ask: _does this need to move data?_

  * **No** → stay in current stage.
  * **Yes (wide)** → close stage, start a new one.
  * **Join** → SMJ adds 2 pre-shuffle stages; BHJ adds 1 tiny broadcast prep.
  * **Aggregating action** at the end → +1 tiny final stage.



## 11. From-blank exercises (with answers)

### Exercise 1 — groupBy + orderBy + write
    
    
    df = spark.read.json("~/Downloads/finflow/crypto/*.jsonl")
    result = (df.filter(col("symbol").isin(["BTC", "ETH"]))
                .withColumn("price_usd_k", col("price") / 1000)
                .groupBy("symbol")
                .agg(avg("price_usd_k").alias("avg_price_k"),
                     count("*").alias("tick_count"))
                .orderBy("symbol"))
    result.write.parquet("~/Downloads/finflow/output/")

**Answer:**

Stage 1: read JSONL → filter → withColumn → groupBy partial agg → SHUFFLE Stage 2: post-shuffle agg → orderBy partial → SHUFFLE Stage 3: post-shuffle sort → write parquet

  * **1 Job** (triggered by `write.parquet`; `read.json` may add a tiny schema-inference job).
  * **3 stages** , 2 shuffles.
  * `count("*")` inside `agg` is the lazy aggregate function — NOT the action.
  * `orderBy` is a shuffle. People forget this.



### Exercise 2 — with a join
    
    
    crypto = spark.read.json("~/Downloads/finflow/crypto/*.jsonl")
    coin_meta = spark.read.csv("~/Downloads/finflow/coin_metadata.csv", header=True)
    
    result = (crypto.join(coin_meta, on="symbol", how="inner")
                    .filter(col("market_cap_tier") == "large")
                    .withColumn("price_usd_k", col("price") / 1000)
                    .groupBy("symbol")
                    .agg(avg("price_usd_k").alias("avg_price_k"),
                         count("*").alias("tick_count")))
    total = result.count()

**Answer (SortMergeJoin case):**

Stage 0: read crypto.jsonl + shuffle-write for join (~200 tasks) Stage 1: read coin_meta.csv + shuffle-write for join (1 task, parallel w/ 0) Stage 2: join + filter + withColumn + groupBy partial + shuffle (200 tasks) Stage 3: final agg + count action (1 task)

  * **1 Job** (the action is `result.count()`).
  * **4 stages** if SortMergeJoin; ~2–3 if Spark auto-broadcasts coin_meta (likely, since it's tiny).
  * Partitions are **per-stage** , not summed across stages.



### Self-check
    
    
    df.filter(...).groupBy("a").count().orderBy("a").show()

**3 stages.** Walkthrough:

Stage 0: read df → filter → groupBy partial agg → SHUFFLE Stage 1: post-shuffle final agg (count) → orderBy partial → SHUFFLE Stage 2: post-shuffle sort → show

The `.count()` on GroupedData is lazy (shorthand for `agg(count(*))`). The action is `.show()`, which doesn't add a final combine stage.

## 12. Sidebar — byte calculations in Spark configs
    
    
    1 KB = 1024 bytes
    1 MB = 1024 × 1024 bytes = 1,048,576 bytes
    100 MB = 100 × 1024 × 1024 = 104,857,600 bytes
    
    spark.conf.set("spark.sql.autoBroadcastJoinThreshold", 100 * 1024 * 1024)

Spark also accepts string forms with units (cleaner):
    
    
    spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "100m")
    spark.conf.set("spark.executor.memory", "4g")
    spark.conf.set("spark.sql.files.maxPartitionBytes", "128m")

## 13. Interview takeaways

  1. **Minimize shuffles** — the whole game.
  2. **Broadcast small joins** — default threshold 10 MB is conservative. Force `broadcast()` when in doubt.
  3. **Know the`count` trap** — three different `count`s; only `df.count()` is an action.
  4. **Stage boundary = shuffle.** SMJ adds 2 pre-shuffle stages; BHJ adds 1 tiny broadcast prep.
  5. **Partitions are per-stage** , not summed.
  6. **Spark UI is your debugger.** First place to look when a job is slow.
  7. **Default`spark.sql.shuffle.partitions` = 200** — almost always wrong. Tune per workload (or rely on AQE in Spark 3+).



* * *

## 14. Partitions — how many, how they're set, how to change them

A **partition** is the unit of parallelism in Spark. Each task processes exactly one partition. More partitions = more tasks = more parallelism (up to the number of cores available).

### How partition count is decided at read time

When you call `spark.read.json("file.jsonl")`, Spark decides partitions based on:

  * **Number of input files** — each file gets at least 1 partition.
  * **`spark.sql.files.maxPartitionBytes`** — default `128 MB`. Files larger than this get split into multiple partitions.
  * **`spark.sql.files.openCostInBytes`** — a small-file coalescing hint (default 4 MB). Spark merges tiny files into the same partition up to this cost.



Practical result: a small local JSONL (a few KB) → **1 partition**.

### Checking partition count
    
    
    df = spark.read.json("data/sample.jsonl")
    print(df.rdd.getNumPartitions())   # prints 1 for a small file

**Caution:** `df.rdd` forces Spark to convert the DataFrame to a low-level RDD, bypassing Catalyst/Tungsten optimizations. Fine for learning and small files. Avoid in production hot paths on large DataFrames — the conversion adds overhead. 

### Changing partition count
    
    
    # repartition — full shuffle, can increase OR decrease, hits exactly N partitions
    df_repartitioned = df.repartition(8)
    
    # coalesce — no shuffle, can only DECREASE, merges existing partitions locally
    df_smaller = df.coalesce(1)   # common before writing to avoid 200-file output
    
    # Check after
    print(df_repartitioned.rdd.getNumPartitions())  # 8
    print(df_smaller.rdd.getNumPartitions())         # 1

Method| Shuffle?| Can increase?| When to use  
---|---|---|---  
`repartition(n)`| Yes| Yes| Need exactly N partitions; rebalancing skewed data  
`coalesce(n)`| No| No| Reducing before a write to avoid tiny output files  
  
### Shuffle partitions vs input partitions

These are two separate settings:

  * **Input partitions** — set at read time by file size / `maxPartitionBytes`.
  * **Shuffle partitions** — how many partitions result from a `groupBy`, `join`, or any wide transformation. Controlled by `spark.sql.shuffle.partitions`, default **200**. Almost always wrong — 200 shuffle partitions on a 10 MB dataset creates 200 tiny tasks; 200 on a 10 TB dataset creates 200 massive ones. AQE (Spark 3+) adjusts this automatically at runtime.



* * *

## 15. Catalyst optimizer + Tungsten execution engine

When you write a DataFrame query or Spark SQL, two engines run before a single byte of your data is touched.

### Catalyst — the query optimizer (logical layer)

Catalyst transforms your query through four phases:

  1. **Parse** — your DataFrame operations or SQL string → an unresolved logical plan (AST).
  2. **Analyze** — resolve column names + types against the catalog → resolved logical plan.
  3. **Optimize** — apply rule-based rewrites to the logical plan: 
     * **Predicate pushdown** — `df.filter(col > 5).join(other)` → filter runs _before_ the join, so fewer rows join.
     * **Column pruning** — `select("a","b")` → Spark never reads column `c` off disk at all.
     * **Constant folding** — `1 + 1` in a query becomes `2` at plan time, not per-row.
  4. **Physical planning** — generate multiple physical plans (e.g. BroadcastHashJoin vs SortMergeJoin), pick cheapest via cost model → physical plan.



This is why `df.explain(True)` shows four plans: _Parsed → Analyzed → Optimized → Physical_.

### Tungsten — the execution engine (physical layer)

Tungsten takes the physical plan from Catalyst and executes it with three key techniques:

  * **Off-heap memory management** — Spark stores data as raw bytes directly in native memory, bypassing the JVM heap and its garbage collector. No GC pauses on large datasets.
  * **Cache-aware computation** — data is stored in columnar binary format, which fits CPU L1/L2 cache lines. Sequential memory access is orders of magnitude faster than random pointer chasing through Java objects.
  * **Whole-stage code generation (WSCG)** — instead of interpreting each operator (filter → project → aggregate) one row at a time, Tungsten compiles the _entire pipeline_ into a single tight Java bytecode loop. One loop, no virtual method dispatch, no per-operator overhead. You can see this in `explain()` output as `*(1) Project` — the `*` means that stage was whole-stage codegen'd.



### Why this matters for you

**Interview one-liner:** Catalyst = smart query planner (rewrites your query before it runs). Tungsten = efficient executor (runs it fast with off-heap memory + compiled bytecode). Together they're why DataFrame/SQL is dramatically faster than raw RDD code — Catalyst optimizes the plan, Tungsten executes without JVM overhead. 

Raw RDD code skips Catalyst entirely. Spark can't push predicates or prune columns through arbitrary Python/Scala lambdas. Always prefer DataFrame API or Spark SQL over RDDs unless you have a very specific reason.

* * *

## 16. Shuffles — what actually happens

A **shuffle** happens whenever Spark needs to regroup data across partitions — after a `groupBy`, `join`, `orderBy`, or `distinct`. It is the most expensive operation in Spark.

### Why shuffles are needed

Imagine you have transactions spread across 4 executors, and you want `groupBy("symbol").sum("amount")`. All BTC rows are on different executors — you can't sum them without first pulling them together onto one machine.

### What happens step by step

  1. **Map side (shuffle write)** — each task hashes its rows by the group/join key and writes them to local disk, sorted by target partition. This is the _shuffle write_.
  2. **Network transfer** — each executor pulls the partitions it's responsible for from other executors' local disks. This is the _shuffle read_.
  3. **Reduce side** — each task now has all rows for its keys co-located, so it can compute the final result (sum, sort, join, etc.).


    
    
    Before shuffle — groupBy("symbol"):
      Executor 1: BTC $50k, ETH $3k
      Executor 2: BTC $51k, SOL $100
    
    After shuffle:
      Executor 1: ALL BTC rows → sum = $101k
      Executor 2: ALL ETH rows → sum = $3k
      Executor 3: ALL SOL rows → sum = $100

### Why shuffles are expensive

  * **Disk I/O** — shuffle writes go to local disk first
  * **Network I/O** — data moves between executors over the network
  * **Stage barrier** — the next stage cannot start until ALL shuffle writes from the current stage are complete



### How to reduce shuffle cost

Problem| Solution  
---|---  
Joining a small table with a large one| Broadcast join — send small table to every executor, no shuffle needed  
Too many tiny partitions post-shuffle| AQE coalesces them automatically (Spark 3+)  
One partition is huge (skew)| AQE skew join handling, or manual salting  
groupBy key already partitioned| Pre-partition by key with `repartition(n, col)` — removes the shuffle entirely  
  
**Interview answer to "why is my Spark job slow?"**  
Open Spark UI → check shuffle read/write bytes. If they're large relative to input size, you have a shuffle-heavy plan. Fix: broadcast joins for small tables, pre-partition by join key, or let AQE handle it. 

* * *

* * *

## 17. Join strategies — BHJ vs SMJ vs SHJ

Spark picks a join strategy automatically based on table sizes. Knowing when each fires is a Databricks interview staple.

### Broadcast Hash Join (BHJ)

**When:** one table is small enough to fit in memory — default threshold **10MB** (`spark.sql.autoBroadcastJoinThreshold`).

**What happens:** the small table is copied in full to every executor. Each executor joins locally — no data moves across the network.
    
    
    # Spark picks BHJ automatically if exchange_rates < 10MB
    df_transactions.join(df_exchange_rates, "currency")
    
    # Force it:
    from pyspark.sql import functions as F
    df_transactions.join(F.broadcast(df_exchange_rates), "currency")
    
    # Raise the threshold:
    spark.conf.set("spark.sql.autoBroadcastJoinThreshold", 50 * 1024 * 1024)  # 50MB

**Stage count:** 1 — no shuffle needed.

**Why no shuffle:** normally a shuffle exists because matching keys are on different machines. BHJ eliminates the problem by putting the entire small table on every machine — matches are always local.

### Sort-Merge Join (SMJ)

**When:** both tables are large (above broadcast threshold).

**What happens:** both sides are shuffled on the join key, sorted within each partition, then merged row by row.
    
    
    Stage 1: shuffle + sort left side by join key
    Stage 2: shuffle + sort right side by join key
    Stage 3: merge join — now co-located and sorted

**Stage count:** 3+ — two pre-shuffle stages (one per side) + merge stage. Most expensive join.

### Shuffle Hash Join (SHJ)

**When:** one side is bigger than broadcast threshold but small enough to build a hash table in memory.

Smaller side is shuffled and built into a hash map; larger side streams through. Less common — Spark prefers SMJ for large data because SMJ handles disk spill better.

### Side by side

| BHJ| SMJ| SHJ  
---|---|---|---  
When| One side < 10MB| Both large| Medium + large  
Shuffle?| ❌ None| ✅ Both sides| ✅ One side  
Stages| 1| 3+| 2  
Speed| Fastest| Slowest| Middle  
  
**Interview answer:** "How do you speed up a slow join?" — Check if one side is small. If yes, force `broadcast()`. Eliminates the shuffle entirely and drops from 3 stages to 1.

* * *

## 18. AQE — Adaptive Query Execution

Before AQE, Spark made all decisions at **plan time** — before seeing real data. Estimates were often wrong. AQE (Spark 3.0+, on by default) re-optimizes **at runtime** , after each shuffle stage completes, using real partition statistics.

### Thing 1 — Coalescing small shuffle partitions
    
    
    spark.sql.shuffle.partitions = 200 (default)
    Data after shuffle = 50MB total
    → 200 × 0.25MB partitions = massive task overhead
    
    AQE fix: merges small partitions automatically
    → 5 × 10MB partitions instead

### Thing 2 — Switching join strategy at runtime
    
    
    Plan time: table B has no stats → Spark assumes large → plans SMJ
    Runtime:   after shuffle, table B = 5MB → AQE switches to BHJ mid-execution

No resubmission needed. Happens transparently.

### Thing 3 — Skew join handling
    
    
    Partition 0–2: 100MB each   ← normal
    Partition 3:   10GB          ← one key dominates (e.g. all "USD" rows)
    → Task 3 takes 100× longer; all other tasks wait
    
    AQE fix: detects skewed partition → splits into sub-tasks → runs in parallel

### Summary table

Problem| AQE fix  
---|---  
Too many tiny partitions post-shuffle| Merges them automatically  
Wrong join strategy at plan time| Switches to better strategy at runtime  
One partition has way more data (skew)| Splits the fat partition, runs sub-tasks in parallel  
      
    
    spark.conf.get("spark.sql.adaptive.enabled")   # "true" in Spark 3+

**Interview one-liner:** AQE re-plans after each shuffle using real data stats instead of estimates — fixes tiny partitions, wrong join type, and data skew automatically. On by default in Spark 3+.

* * *

## 19. Caching

By default Spark recomputes a DataFrame from scratch every time you run an action on it. Caching stores the result so subsequent actions read from memory instead.
    
    
    df.cache()         # shorthand for MEMORY_AND_DISK
    df.persist()       # same thing
    
    df.count()         # first action — data is cached HERE, not at cache()
    df.show()          # reads from cache ✅
    df.filter(...)     # reads from cache ✅
    
    df.unpersist()     # always free memory when done

**Key gotcha:** `cache()` is lazy — nothing is stored until the first action hits it. `df.cache()` alone does nothing.

### Storage levels

Level| Where| Speed| Safe if RAM full?  
---|---|---|---  
MEMORY_ONLY| RAM only| Fastest| ❌ Evicted  
MEMORY_AND_DISK| RAM, spills to disk| Fast| ✅ Spills  
DISK_ONLY| Disk only| Slow| ✅ Always there  
MEMORY_ONLY_SER| RAM, serialized| Medium| ❌ Evicted  
  
### When to cache vs not

Cache ✅| Don't cache ❌  
---|---  
Same DataFrame used in multiple actions| DataFrame used only once  
Iterative ML training loops| DataFrame larger than executor RAM  
Interactive exploration with many filters| Streaming DataFrames  
  
**Interview one-liner:** Cache when the same DataFrame is reused in multiple actions — avoids recomputing from scratch. Always unpersist when done. Remember: cache() is lazy.

* * *

## 20. Salting — manual skew fix

### The problem
    
    
    orders join customers on customer_id
    customer_id = 'AMAZON' has 24M rows — 80% of all data
    
    Executor 1: AMAZON → 10M rows  ← HOT PARTITION
    Executor 2: others → 50K rows
    Executor 3: others → 30K rows
    → job crawls waiting for Executor 1 (straggler problem)

AQE handles this automatically in Spark 3+. But if AQE is off, or you want manual control, **salting** is the fix.

### Case 1 — Join salting (large table + small table)

Two steps: salt the large table, explode the small table to match.
    
    
    SALT_BUCKETS = 10
    
    # Step 1 — salt the LARGE (skewed) table
    orders_salted = orders_df \
        .withColumn("salt", (F.rand() * SALT_BUCKETS).cast("int")) \
        .withColumn("salted_key", F.concat(F.col("customer_id"), F.lit("_"), F.col("salt")))
    # AMAZON → AMAZON_3, AMAZON_7, etc. — randomly spread across 10 partitions
    
    # Step 2 — explode the SMALL (lookup) table to match ALL salt values
    customers_salted = customers_df \
        .withColumn("salt_array", F.array([F.lit(i) for i in range(SALT_BUCKETS)])) \
        .withColumn("salt", F.explode("salt_array")) \
        .withColumn("salted_key", F.concat(F.col("customer_id"), F.lit("_"), F.col("salt")))
    # AMAZON (1 row) → AMAZON_0, AMAZON_1, ... AMAZON_9 (10 rows)
    
    # Step 3 — join on salted key
    result = orders_salted.join(customers_salted, on="salted_key", how="inner") \
                          .drop("salt", "salt_array", "salted_key")

**Why explode the small table?** Orders now have AMAZON_3, AMAZON_7 etc. Customers still only has AMAZON. Without exploding, there's no matching row — join produces nulls. You replicate the small table so every salted key has a match.
    
    
    BEFORE explode:           AFTER explode:
    ─────────────────         ─────────────────────
    AMAZON | [0,1..9]   →    AMAZON_0
                              AMAZON_1
                              ...
                              AMAZON_9

### Case 2 — groupBy salting (aggregation only)
    
    
    # Step 1 — salted groupBy
    df_salted = df.withColumn("salt", (F.rand() * 10).cast("int")) \
                  .withColumn("salted_key", F.concat(F.col("country"), F.lit("_"), F.col("salt")))
    partial = df_salted.groupBy("salted_key").agg(F.sum("amount").alias("partial_sum"))
    
    # Step 2 — strip salt, re-aggregate to get final result
    final = partial.withColumn("country", F.split(F.col("salted_key"), "_")[0]) \
                   .groupBy("country").agg(F.sum("partial_sum").alias("total"))

### How to detect skew — Spark UI

Spark UI → Stages → click slow stage → Summary Metrics:
    
    
    Shuffle Read Size:
      Min:    80 MB
      Median: 100 MB   ← normal partition
      Max:    2.1 GB   ← hot partition
      P75:    110 MB
    
    Skew ratio = Max / Median = 2100 / 100 = 21x → apply salting

Also check programmatically:
    
    
    orders_df.groupBy(F.spark_partition_id()).count().orderBy(F.desc("count")).show(10)

### How to size salt buckets

Signal| Formula  
---|---  
Skew ratio from Spark UI| SALT = Max / Median = 2100MB / 100MB = 21  
Target partition size (~200MB)| SALT = Max / 200MB = 2100 / 200 = 10  
Small table memory budget| If small_table × SALT > executor RAM → reduce SALT  
  
**Rule:** start conservative (SALT=10), check Spark UI, tune up if skew persists. Use Median to detect skew, 200MB target to size the fix.

### Salting vs AQE skew handling

| Salting| AQE skew join  
---|---|---  
Manual or automatic| Manual| Automatic  
Spark version| Any| Spark 3+ only  
Small table explode needed (join)| ✅ Yes| ❌ No  
Use when| AQE off, or fine-grained control| AQE on (default)  
  
**FAANG interview answer:** "Spark UI showed one task taking 48 min with shuffle read of 2GB vs median 100MB — skew ratio ~20x. Hot key was a mega-merchant. Applied join salting with 20 buckets on the fact table, exploded the dimension table. Job time dropped from 50 min to 6 min."  
  
Observation → evidence → decision → result. That's the chain they want. 

* * *

## 21. Salting — Hands-On Lab (2026-06-08)

Full end-to-end exercise: generate skewed data, observe skew in Spark UI, fix with salting, observe improvement.

### Setup — configs and why
    
    
    spark = SparkSession.builder \
        .config("spark.sql.shuffle.partitions", "10")      # low → skew is obvious (not buried across 200 partitions)
        .config("spark.sql.adaptive.enabled", "false")     # AQE OFF → Spark can't auto-fix skew; we must fix it manually
        .config("spark.sql.autoBroadcastJoinThreshold", "-1")  # force SMJ → merchants (5 rows) would normally be
        .getOrCreate()                                         # auto-broadcast (BHJ), masking skew via partial agg;
                                                               # -1 forces shuffle join so all rows move on merchant_id

**BHJ masks skew.** With default settings, Spark broadcasts the 5-row merchants table — each executor gets a full copy and filters locally. No shuffle happens. Skew is invisible in the UI because there are no straggler shuffle tasks. You must disable broadcast to see the problem.  
  
`autoBroadcastJoinThreshold=-1` forces Sort-Merge Join: both tables shuffle on `merchant_id`. MEGACORP's 40K rows all land in one partition → straggler visible. 

### Dataset
    
    
    # transactions_skewed.jsonl — 50,000 rows
    weights = [0.80, 0.05, 0.07, 0.05, 0.03]   # MEGACORP gets 80%
    merchant = random.choices(merchant_ids, weights=weights, k=1)[0]
    
    # merchants.jsonl — 5 rows (small lookup table)
    # MEGACORP, SMALLBIZ, TECHCO, FASTFOOD, LUXESHOP

### Part A — Skewed job (no fix)
    
    
    skewed_result = (
        txns.join(merchants, on="merchant_id", how="inner")
            .groupBy("merchant_id", "category")
            .agg(F.count("*"), F.sum("amount"), F.avg("amount"))
            .orderBy(F.desc("txn_count"))
    )

**Spark UI — Summary Metrics for the shuffle stage:**

Metric| Min| Median| Max  
---|---|---|---  
Shuffle Read Size / Records| ~0 B / 0| ~0 B / 0| **355 KiB / 41,468**  
  
5 out of 10 partitions got zero rows. One partition received 41,468 rows (all MEGACORP). That task ran alone while 9 other tasks were idle.

### Detecting skew programmatically
    
    
    # Ex 1 — show row count per partition after repartition on merchant_id
    spark_partition_counts = (
        txns.repartition(10, "merchant_id")
            .withColumn("partition_id", F.spark_partition_id())
            .groupBy("partition_id")
            .count()
            .orderBy(F.desc("count"))
    )
    # Result: one partition ~40,000 rows, others ~2,500 or less

### Part B — Salted join (fix)
    
    
    SALT_BUCKETS = 10
    
    # Step 1 — salt the large (skewed) table
    txns_salted = (
        txns
        .withColumn("salt", (F.rand() * SALT_BUCKETS).cast("int"))
        .withColumn("salted_key", F.concat_ws("_", F.col("merchant_id"), F.col("salt")))
    )
    # MEGACORP → MEGACORP_0, MEGACORP_3, MEGACORP_7 ... spread randomly
    
    # Step 2 — explode the small (lookup) table to match all salt values
    merchants_salted = (
        merchants
        .withColumn("salt_array", F.array([F.lit(i) for i in range(SALT_BUCKETS)]))
        .withColumn("salted_key", F.explode(F.col("salt_array")))
        .withColumn("salted_key", F.concat_ws("_", F.col("merchant_id"), F.col("salted_key")))
    )
    # MEGACORP (1 row) → MEGACORP_0, MEGACORP_1, ..., MEGACORP_9 (10 rows)
    # merchants_salted.count() = 50 (5 merchants × 10 buckets)
    
    # Step 3 — join, dropping duplicate merchant_id from small table
    salted_result = (
        txns_salted
        .join(merchants_salted.drop("merchant_id"), on="salted_key", how="inner")
        .groupBy("merchant_id", "category")
        .agg(F.count("*").alias("txn_count"), F.sum("amount").alias("total_amount"), F.avg("amount").alias("avg_amount"))
        .orderBy(F.desc("txn_count"))
        .show()
    )

### Part B — Spark UI metrics (shuffle stage)

Metric| Min| Median| Max  
---|---|---|---  
Part A (no salt)| ~0 B / 0| ~0 B / 0| **355 KiB / 41,468**  
Part B (salted)| 6.1 KiB / 579| 50.2 KiB / 4,890| **148.8 KiB / 12,632**  
  
Max dropped from 41,468 rows to 12,632 — ~3.3x improvement. All partitions now have data (min 579 rows vs 0).

### Why max wasn't perfectly even (~4K expected, 12K actual)
    
    
    # With 10 salt buckets and 10 Spark partitions:
    # Spark hashes each salted_key to a partition using murmur3
    # "MEGACORP_0" ... "MEGACORP_9" are 10 keys → don't hash to 10 different partitions
    # Some partitions receive 2-3 MEGACORP keys by hash collision
    # 3 MEGACORP keys × ~4,000 rows each = ~12,000 rows → matches observed max
    
    # Fix: use more buckets than partitions
    SALT_BUCKETS = 20  # or 30
    # Now 20 MEGACORP keys across 10 partitions → ~2 keys/partition on average
    # Variance drops significantly, max closer to ~8K

**Rule:** use 2–3× more salt buckets than shuffle partitions to reduce hash collision probability.

### Bugs found during the exercise

Bug| Wrong| Correct| Why  
---|---|---|---  
cast type | `.cast(int)` | `.cast("int")` | Python's `int` type is not a Spark type string. Spark expects `"int"` or `IntegerType()`.  
F.array misuse | `F.array(F.lit([0,1,...9]))` | `F.array([F.lit(i) for i in range(N)])` | First form passes a Python list as a single literal — creates one ArrayType column containing one element (a list). Second form passes N separate Column objects — creates an ArrayType column with N elements.  
Missing parenthesis | `merchants.withColumn("x", F.array([...]).withColumn(...))` | `merchants.withColumn("x", F.array([...]))  
.withColumn(...)` | Without closing the first `withColumn`, Python calls `.withColumn()` on the Column returned by `F.array()` — Column has no such method → AttributeError at runtime.  
Ambiguous column after join | `txns_salted.join(merchants_salted, ...)`  
then `groupBy("merchant_id")` | `merchants_salted.drop("merchant_id")` before join | Both tables have `merchant_id`. After the join, Spark sees two columns with the same name → `AMBIGUOUS_REFERENCE`. Drop the duplicate from the smaller table before joining.  
  
### Key concepts recap

  * **F.rand()** — returns a random decimal 0.0–1.0 per row; multiply by N then cast to int gives 0 to N-1
  * **F.lit(x)** — wraps a Python scalar as a Spark Column (needed inside `F.array()`)
  * **F.array([F.lit(i) for i in range(N)])** — creates an ArrayType column with N integer elements per row
  * **F.explode()** — turns one row with an array of N elements into N rows
  * **F.concat_ws("_", col1, col2)** — concatenates columns with separator; handles int columns without manual cast
  * **random.choices(population, weights, k)** — weighted sampling with replacement; `k=1` returns a list, `[0]` unpacks it
  * **json.dumps(dict)** — converts Python dict to JSON text string for writing to file (JSONL format)



* * *

## 22. Photon — Databricks Vectorized Execution Engine

### Why Photon exists — JVM limitations

JVM problem| Impact  
---|---  
GC pauses| Stop-the-world collection interrupts execution  
Object overhead| Every Java object has a 16-byte header; 1M integers wastes significant RAM  
JIT warmup| Bytecode compiled to native at runtime; cold starts are slow  
  
Tungsten + WSCG already improves on the JVM baseline (generates bytecode instead of interpreting row-by-row), but it's still JVM.

### What Photon is

Photon is a **C++ vectorized execution engine** built by Databricks. It replaces JVM execution for compatible operations:

  * Same DataFrame / SQL API — **zero code changes**
  * Enabled at cluster level (checkbox in Databricks cluster config)
  * Available on Databricks Runtime 9.1+



### Vectorized execution — the core idea
    
    
    # Row-at-a-time (Spark / Tungsten)
    process row 1 → process row 2 → process row 3 ...
    # one function call per row — overhead adds up at 1M+ rows
    
    # Vectorized (Photon)
    load 1,024 values of column "amount" into CPU registers
    apply operation to ALL 1,024 in ONE CPU instruction (SIMD)
    move to next batch of 1,024

**SIMD** (Single Instruction Multiple Data): modern CPUs can add 4–8 floats in a single CPU cycle. Photon exploits this; JVM cannot.

**Key distinction:** columnar storage is the _format_ that enables vectorized execution (same-type data packed together loads cleanly into CPU registers). Vectorized is the _execution model_ — processing a batch at once with SIMD. The two go together.

### What Photon accelerates vs skips

Operation| Photon?  
---|---  
Parquet / Delta scans| ✅  
Hash joins| ✅  
Aggregations (sum, count, avg)| ✅  
Sorts, shuffle| ✅  
Python UDFs| ❌ — drops back to JVM (Photon fallback)  
Pandas UDFs (Arrow)| ❌  
Some complex window functions| ❌  
  
**Photon fallback:** if a step in your query hits a Python UDF, execution exits Photon for that step and re-enters JVM. The rest of the plan may resume Photon after. Minimize Python UDFs on hot paths to stay in Photon.

### When Photon helps vs when it doesn't

Helps| Doesn't help  
---|---  
CPU-bound: wide aggregations, large hash joins, heavy sorts| I/O-bound: bottleneck is slow disk or network — C++ can't make S3 faster  
Long-running batch queries over large Delta tables| Queries dominated by Python UDFs  
  
### Photon vs Tungsten / WSCG

| Tungsten + WSCG| Photon  
---|---|---  
Language| JVM bytecode (generated)| C++ native  
Execution model| Row-at-a-time (fused)| Vectorized batches (SIMD)  
GC exposure| Yes (JVM)| No  
Available on| Open-source Spark| Databricks Runtime only  
Code changes needed| None| None  
  
**Interview one-liner:** "Photon is Databricks' C++ vectorized execution engine. It replaces JVM/Tungsten for compatible operations, processing columnar batches with SIMD instead of row-at-a-time. No code changes — same API. 2–10x speedup on CPU-bound queries. Falls back to JVM for Python UDFs." 

* * *

## 23. Delta Lake — the transaction log (_delta_log)

_Stage 2C, Session 1 — 2026-06-12. The single most-asked Databricks DE topic._

### What a Delta table physically is

A Delta table is just **two things in a folder** :
    
    
    my_table/
    ├── _delta_log/                          ← the transaction log (the "brain")
    │   ├── 00000000000000000000.json        ← commit 0 (CREATE TABLE)
    │   ├── 00000000000000000001.json        ← commit 1 (first INSERT)
    │   ├── 00000000000000000002.json        ← commit 2 (UPDATE)
    │   ├── ...
    │   ├── 00000000000000000010.checkpoint.parquet  ← checkpoint at commit 10
    │   └── _last_checkpoint                 ← pointer to latest checkpoint
    ├── part-00000-xxxx.parquet              ← data files (immutable!)
    ├── part-00001-xxxx.parquet
    └── ...

The Parquet data files are **immutable — never edited in place**. An UPDATE doesn't modify a file; it writes a _new_ file with the changed rows and records in the log "old file removed, new file added". This immutability is what makes time travel, ACID, and concurrent reads possible.

### What's inside a commit JSON

Each numbered JSON file = one atomic commit = a list of **actions** :

Action| Meaning  
---|---  
`add`| "This Parquet file is now part of the table" — includes path, size, partition values, and **min/max column stats** (used for data skipping)  
`remove`| "This file is no longer part of the table" — a _logical_ delete; the physical file stays on disk until VACUUM  
`metaData`| Schema, partition columns, table properties  
`protocol`| Min reader/writer version required  
`commitInfo`| Audit: operation type (WRITE/MERGE/DELETE), timestamp, user, engine  
  
Example — an UPDATE that touched one file:
    
    
    {"commitInfo": {"operation": "UPDATE", "timestamp": 1718200000000}}
    {"remove": {"path": "part-00000-aaa.parquet", "deletionTimestamp": ...}}
    {"add": {"path": "part-00002-bbb.parquet", "size": 1048576,
             "stats": "{\"minValues\":{\"amount\":10},\"maxValues\":{\"amount\":950}}"}}

### How a read works

  1. Open `_delta_log/`, read commits 0 → N in order
  2. Play the actions forward: every `add` puts a file in the live set, every `remove` takes it out
  3. The result — the set of files alive at version N — is the **snapshot**
  4. Read only those Parquet files (pruned further by min/max stats)



**Key mental model:** the table's current state is not stored anywhere — it is _computed_ by replaying the log. The log is the source of truth; Parquet files are just payload.

### Checkpoints — why replay doesn't get slower forever

Replaying 100,000 JSON files would be brutal. So **every 10th commit** Delta writes a `.checkpoint.parquet` — the _entire table state_ (all live files + metadata) collapsed into one Parquet file. A reader then does:

  1. Read `_last_checkpoint` → "latest checkpoint is at version 30"
  2. Load `00000...030.checkpoint.parquet` (one file = state at v30)
  3. Replay only the JSON commits after 30 (31, 32, ... N)



So a read is never more than ~10 JSON replays + 1 checkpoint load, no matter how old the table.

### ACID via optimistic concurrency control (OCC)

Delta has **no lock server**. Writers don't coordinate up front — they assume conflicts are rare (hence "optimistic") and check at commit time:

  1. Writer reads the latest snapshot, say version **12**
  2. Does all its work — writes new Parquet data files (invisible until committed)
  3. Tries to commit by creating `00000...013.json` — using an atomic **put-if-absent** operation: it succeeds only if no file with that name exists yet
  4. If another writer got 13 first: read commit 13, **check for logical conflict** with what it did, and if compatible, retry as commit 14. If truly conflicting → `ConcurrentModificationException`



Atomicity comes from the fact that **a commit is one file creation** — it either fully appears in the log or doesn't exist at all. Readers never see half a commit, and data files written by an uncommitted writer are invisible because no `add` action references them.

### Which concurrent writes conflict?

Writer A / Writer B| Outcome  
---|---  
Append + Append| ✅ Both succeed — new files don't touch each other; loser just re-commits at the next version  
Append + UPDATE/DELETE (different files)| ✅ Usually fine after retry  
UPDATE + UPDATE on the **same files**|  ❌ Loser gets ConcurrentModificationException — it based its work on files the winner removed  
Anything + schema change| ❌ Conflict — snapshot's metaData changed underneath  
  
**Contrast with a warehouse:** Snowflake/Postgres use locks/MVCC managed by a server. Delta achieves ACID on dumb object storage (S3/ADLS) purely through the log protocol + atomic file creation. That difference — "how do you get ACID without a database server?" — is exactly what interviewers probe.

### Interview one-liners

  * "A Delta table is immutable Parquet files plus a transaction log. The log is the source of truth — current state is computed by replaying add/remove actions, accelerated by Parquet checkpoints every 10 commits."
  * "ACID comes from optimistic concurrency: writers prepare data invisibly, then commit by atomically creating the next numbered log file. Two appends both succeed; two updates to the same files — the loser detects the conflict on retry and throws."
  * "DELETE/UPDATE never modify Parquet in place — they write new files and logically remove old ones, which is also why time travel works."



### Hands-on lab (Databricks CE)
    
    
    # 1. Create a small Delta table at a Volume path (so you can inspect the log)
    path = "/Volumes/<catalog>/<schema>/<volume>/delta_lab/tx"
    spark.range(0, 1000).withColumnRenamed("id", "tx_id").write.format("delta").save(path)
    
    # 2. Look at the folder — count data files vs log files
    display(dbutils.fs.ls(path))
    display(dbutils.fs.ls(path + "/_delta_log"))
    
    # 3. Read commit 0 raw — find the add / metaData / commitInfo actions
    print(dbutils.fs.head(path + "/_delta_log/00000000000000000000.json"))
    
    # 4. Make 11 more commits (append loop) → watch the checkpoint appear at v10
    for i in range(11):
        spark.range(i*10, i*10+10).withColumnRenamed("id", "tx_id") \
            .write.format("delta").mode("append").save(path)
    display(dbutils.fs.ls(path + "/_delta_log"))   # spot 00000...010.checkpoint.parquet
    
    # 5. Audit trail
    display(spark.sql(f"DESCRIBE HISTORY delta.`{path}`"))

### From-blank checks (answer before reading back)

  1. You run `DELETE FROM tx WHERE tx_id < 100`. Describe exactly what appears in the next commit JSON, and what happens to the old Parquet file.
  2. A reader starts at version 12 while a writer commits version 13 mid-read. What does the reader see and why?
  3. Two jobs both MERGE into the same table at the same time. Walk through the OCC steps that decide who wins.
  4. Why does Delta write checkpoints as Parquet instead of JSON?



* * *

## 24. Delta Lake — time travel, RESTORE, schema enforcement & evolution

### Time travel — how it actually works

Because data files are immutable and `remove` is only logical, **every historical version still physically exists** (until VACUUM). Reading version N = replaying the log only up to commit N:

  1. Find the latest checkpoint ≤ N
  2. Load it, replay JSON commits from there up to exactly N
  3. Resulting file set = the table as it was at version N


    
    
    SELECT * FROM tx VERSION AS OF 12;
    SELECT * FROM tx TIMESTAMP AS OF '2026-06-10';          -- resolves to last version committed ≤ that time
    
    df = spark.read.format("delta").option("versionAsOf", 12).load(path)   -- PySpark

**RESTORE** rolls a table back — but it does NOT delete history. It makes a _new_ commit whose actions re-add the old files and remove the current ones:
    
    
    RESTORE TABLE tx TO VERSION AS OF 12;   -- creates version N+1 that "looks like" v12

**Time travel limits:** you can only travel to versions whose data files still exist (VACUUM deletes them past retention, default 7 days) and whose log entries exist (log JSON cleanup after `delta.logRetentionDuration`, default 30 days). "Why can't I time travel to last month?" → VACUUM ate the files.

**Use cases:** debugging ("what did this row look like before yesterday's job?"), audit/compliance, reproducing ML training data, rollback after a bad write, diffing two versions.

### Schema enforcement (on write)

Delta validates every write against the table's `metaData` schema and **rejects** writes whose schema doesn't match — extra columns, missing required types, incompatible type changes → `AnalysisException`. This is the opposite of a plain data lake, where any job can dump any shape of file into a folder and silently poison downstream readers. Enforcement is what makes the lakehouse "schema-on-write" like a warehouse.

### Schema evolution (deliberate change)

Mechanism| What it allows  
---|---  
`.option("mergeSchema", "true")`| Per-write opt-in: **add new columns** (and upcast e.g. int→long). Existing rows get NULL for new columns. Commits a new `metaData` action.  
`spark.databricks.delta.schema.autoMerge.enabled`| Session-wide auto-merge — needed for schema evolution inside **MERGE INTO** (mergeSchema option doesn't apply to MERGE)  
`.option("overwriteSchema", "true")` + mode("overwrite")| Nuclear: replace the schema entirely (drop/rename/retype columns). Rewrites the table.  
`ALTER TABLE ... ADD COLUMN`| Metadata-only — instant, no data rewrite  
  
**Interview one-liner:** "Enforcement is the default — bad writes are rejected at commit time. Evolution is opt-in per write with mergeSchema, which only allows safe additive changes; destructive changes need overwriteSchema and a rewrite. Schema lives in the transaction log's metaData action, so a schema change is itself a versioned commit."

## 25. Delta Lake — OPTIMIZE, Z-ORDER, VACUUM & the small files problem

### The small files problem — why it exists and what it costs

Every commit writes new files. A streaming job committing every 30s, or an over-partitioned write (200 shuffle partitions × tiny data), produces thousands of KB-sized files. Costs:

  * **API/IO overhead:** reading 10 GB as 10,000 × 1 MB files = 10,000 S3 GET requests + 10,000 file-open overheads, vs ~80 × 128 MB files. Each open has fixed latency — it dominates at small sizes.
  * **Driver/planning overhead:** the snapshot tracks every file; more files = bigger log, slower planning, more tasks scheduled.
  * **Poor compression & stats:** Parquet compresses and encodes per file/row-group; tiny files compress badly and min/max stats prune worse.



### OPTIMIZE — bin-packing compaction
    
    
    OPTIMIZE tx;                          -- coalesce small files into ~1 GB files
    OPTIMIZE tx WHERE date = '2026-06-12' -- only a partition (cheaper)

Reads many small files, writes few big ones, commits `remove` (small) + `add` (big). **Data content is identical** — it's a pure file-layout transaction, marked `dataChange=false` so streaming readers don't reprocess it.

**Auto variants (table properties):** `delta.autoOptimize.optimizeWrite` (shuffle before write to emit fewer, bigger files) and `delta.autoOptimize.autoCompact` (post-write mini-OPTIMIZE if too many small files accumulated).

### Z-ORDER — multi-dimensional clustering
    
    
    OPTIMIZE tx ZORDER BY (customer_id, event_date);

During compaction, rows are reordered along a **space-filling curve (Z-curve)** over the chosen columns, so rows with similar values in ALL those columns land in the same files. Result: each file's min/max range for those columns is _narrow_ → data skipping prunes far more files for filters on any of them.

Z-ORDER helps| Z-ORDER doesn't help  
---|---  
High-cardinality columns you filter on (customer_id, device_id)| Low-cardinality columns (country with 5 values) — partition instead  
2–4 columns max — effectiveness drops per added column| Columns never used in WHERE/JOIN predicates  
Point lookups / selective range filters| Full-table scans — nothing to prune  
  
**vs partitioning:** partitioning physically separates directories — perfect pruning but disastrous with high cardinality (one tiny dir per value). Z-ORDER clusters _within_ files — works fine on high-cardinality columns. Rule: partition by low-cardinality (date), Z-ORDER by high-cardinality filter columns.

**Newer alternative — Liquid Clustering** (`CLUSTER BY`): replaces both partitioning and Z-ORDER on recent DBR; incremental, no full rewrite, clustering keys changeable later. Worth name-dropping in interviews.

### VACUUM — physical deletion
    
    
    VACUUM tx;                  -- delete unreferenced files older than 7 days (default)
    VACUUM tx RETAIN 168 HOURS; -- explicit
    VACUUM tx DRY RUN;          -- list what would be deleted

  * Deletes files that are **(a) no longer referenced** by the current version **and (b) older than the retention window**
  * **Time travel beyond the retention window dies** — the files are physically gone
  * Setting retention < 7 days requires disabling `spark.databricks.delta.retentionDurationCheck.enabled` — the guard exists because in-flight jobs reading an old snapshot would break if its files vanish
  * VACUUM does NOT shrink the log; log JSON cleanup is separate (`delta.logRetentionDuration`, 30 days)



### Data skipping + dynamic file pruning (DFP)

**Static data skipping:** every `add` action carries min/max stats for the first 32 columns (`delta.dataSkippingNumIndexedCols`). A query with `WHERE amount > 900` skips any file whose max(amount) ≤ 900 — decided at planning time from the log alone, zero data IO.

**Dynamic file pruning:** same idea but the filter values aren't known until _runtime_ — e.g. `fact JOIN dim ON fact.k = dim.k WHERE dim.region = 'EU'`. There's no literal predicate on fact, so static skipping can't fire. DFP runs the dim side first, collects the surviving join keys, and uses them to prune fact _files_ before scanning (Databricks/Photon feature; pairs with dynamic partition pruning). Classic star-schema accelerator.

## 26. Delta Lake — MERGE INTO mechanics & Change Data Feed

### MERGE INTO — the upsert workhorse
    
    
    MERGE INTO target t
    USING updates s
    ON t.id = s.id
    WHEN MATCHED AND s.deleted = true THEN DELETE
    WHEN MATCHED THEN UPDATE SET t.amount = s.amount, t.updated_at = s.ts
    WHEN NOT MATCHED THEN INSERT (id, amount, updated_at) VALUES (s.id, s.amount, s.ts)
    WHEN NOT MATCHED BY SOURCE THEN DELETE   -- optional third direction (DBR 12.2+)

**Under the hood — two passes:**

  1. **Find touched files:** inner join source ↔ target to identify which target files contain matching rows (file-level, helped by data skipping on the ON keys)
  2. **Rewrite:** full outer join source ↔ _only those files_ , apply matched/not-matched logic, write replacement files; commit `remove` (touched) + `add` (rewritten) atomically



Consequences worth saying out loud in an interview: **one matching row in a 1-GB file rewrites the whole file** (write amplification — keep files right-sized); MERGE cost scales with files _touched_ , so clustering/Z-ORDER on the merge keys directly speeds up MERGE; duplicate matches in the source ("multiple source rows matched the same target row") throw an error — dedupe the source first.

**Isolation:** Delta writes are `WriteSerializable` by default — concurrent MERGEs on the same files conflict via OCC (Section 23) and the loser retries or throws.

### Change Data Feed (CDF)

Problem: a downstream job wants _only what changed_ in a table, not a full re-read + diff. CDF makes Delta record row-level changes:
    
    
    ALTER TABLE tx SET TBLPROPERTIES (delta.enableChangeDataFeed = true);
    
    SELECT * FROM table_changes('tx', 5, 9);            -- changes between versions 5 and 9
    SELECT * FROM table_changes('tx', '2026-06-10');     -- or by timestamp
    
    spark.readStream.format("delta")                     -- streaming consumption
         .option("readChangeFeed", "true")
         .option("startingVersion", 5).table("tx")

Each change row carries `_change_type`, `_commit_version`, `_commit_timestamp`. UPDATE produces **two rows** : `update_preimage` (before) and `update_postimage` (after); plus `insert` and `delete` types.

  * Stored in a `_change_data/` folder next to the data — only for UPDATE/DELETE/MERGE; pure inserts are derived from the add files directly (no extra storage)
  * Retention follows VACUUM like everything else
  * **Use cases:** incremental downstream pipelines (gold tables reading only silver's changes), feeding SCD Type 2, audit, replicating to external systems



**One-liner:** "CDF turns a Delta table into a CDC source: enable a table property and read row-level inserts, deletes, and pre/post-images of updates between any two versions, batch or streaming."

## 27. Delta Sharing & Delta vs Iceberg vs Hudi

### Delta Sharing

**Problem it solves:** sharing live data across organizations historically meant copying (FTP/S3 dumps — stale immediately) or requiring the consumer to be on the same platform (Snowflake-to-Snowflake shares). Delta Sharing is an **open REST protocol** : the provider's sharing server authenticates the recipient and hands out short-lived pre-signed URLs to the underlying Parquet files; the recipient reads them directly with pandas, Spark, Power BI, etc. — **no Databricks account needed, no data copied** , always current, provider keeps governance/audit via Unity Catalog.

### Delta vs Iceberg vs Hudi — transaction log architecture

| Delta Lake| Apache Iceberg| Apache Hudi  
---|---|---|---  
Metadata design| **Linear log** of JSON commits + Parquet checkpoints; state = replay| **Snapshot tree:** table metadata file → manifest lists → manifests → data files; each snapshot is a complete self-describing tree, commit = atomic pointer swap in the catalog| **Timeline** of actions (commits, compactions, cleans) + record-level index; two table types  
Concurrency| OCC via atomic creation of next log file| OCC via atomic catalog pointer swap (catalog is the arbiter)| OCC + MVCC on the timeline  
Signature strengths| Simplicity, Photon/Databricks integration, CDF, liquid clustering| **Hidden partitioning** (partition by `days(ts)` — queries on ts auto-prune, no partition column in queries) + **partition evolution** (change scheme without rewrite); strong engine neutrality| **Copy-on-Write vs Merge-on-Read** choice: MOR writes row-based delta logs merged at read time → fastest upserts/lowest write latency; built for streaming CDC ingest  
Weak spots| Historically Databricks-gravity (open-sourced, but best features land on DBR first)| More moving parts (catalog required); small-file pressure from frequent commits| Most operational complexity (compaction tuning); smaller mindshare outside CDC use cases  
Ecosystem gravity| Databricks| Snowflake, AWS (Athena/Glue), Trino, BigQuery — the "neutral standard"| Uber-born; AWS EMR, streaming-CDC shops  
  
**The convergence story (good closing line):** the formats are converging — Delta's UniForm writes Iceberg-readable metadata alongside Delta, Databricks acquired Tabular (Iceberg's creators) in 2024, and XTable translates between all three. The real moat is shifting from the format to the catalog/governance layer (Unity Catalog vs Polaris vs Glue).

### From-blank checks — Sessions 2+ material

  1. VACUUM ran with default retention this morning. A teammate asks for the table as of 10 days ago. Possible? Why?
  2. A MERGE updates 1 row that lives in a 1-GB file. How much data gets rewritten, and what two log actions appear?
  3. You filter on `customer_id` (10M distinct values). Partition, Z-ORDER, or both? Justify.
  4. Streaming job commits every 20 seconds. Name the problem that develops and two fixes.
  5. Why does CDF store pre-images for UPDATE but nothing extra for INSERT?
  6. Iceberg query: `WHERE event_ts > '2026-06-01'` prunes partitions even though no partition column is referenced. What feature is this and how does Delta differ?
  7. "Why did Databricks build Delta Sharing instead of just granting cross-account S3 read access?" — answer like an interview.



* * *

Updated 2026-06-12 — Stage 2C complete coverage added: Section 23 (transaction log, OCC), 24 (time travel, RESTORE, schema enforcement/evolution), 25 (OPTIMIZE, Z-ORDER, liquid clustering, VACUUM, small files, data skipping + DFP), 26 (MERGE mechanics, CDF), 27 (Delta Sharing, Delta vs Iceberg vs Hudi). All 12 topics from the 2C plan covered.

* * *

## Stage 2D — Structured Streaming

Session: 2026-07-03

### §28 Checkpoint — What it stores and why it matters

A checkpoint is a **directory on durable storage** (S3, ADLS, DBFS) that Spark writes to at the end of every micro-batch so a crashed query can resume exactly where it left off.

#### Checkpoint directory structure
    
    
    checkpoint/
      metadata      ← query ID + config (written once at startup)
      offsets/      ← what was READ each batch (0, 1, 2, ...)
      commits/      ← what was SUCCESSFULLY PROCESSED (0, 1, 2, ...)
      state/        ← aggregation state, watermarks, dedup records

#### How exactly-once works (two-phase commit via checkpoint)

Every micro-batch follows this sequence:

  1. Write `offsets/N` — "I am about to read up to offset N"
  2. Read source data and process
  3. Write output to sink
  4. Write `commits/N` — "batch N is done"



If the job crashes between steps 1 and 4, on restart Spark sees `offsets/N` exists but `commits/N` doesn't → reruns batch N. The sink must be idempotent (Delta handles this automatically via transaction log).

#### Consequence of deleting the checkpoint

What's lost| Effect  
---|---  
`offsets/`| Spark doesn't know where it read to — restarts from beginning or latest depending on source config  
`commits/`| Can't distinguish completed vs in-progress batches → potential duplicates  
`state/`| All aggregation state gone — running counts, window sums, dedup history reset to zero → **wrong answers**  
  
**Rule:** For stateless streams, deleting checkpoint means reprocessing. For stateful streams (aggregations, dedup), it means wrong answers.

### §29 Writing Streaming Queries — Patterns

#### Stateless filter + write (append mode)
    
    
    from pyspark.sql.functions import col
    
    spark.readStream \
        .format("delta") \
        .load("/data/events") \
        .filter(col("event_type") == "purchase") \
        .writeStream \
        .format("delta") \
        .option("checkpointLocation", "/checkpoints/purchases") \
        .outputMode("append") \
        .start("/data/purchases")

**Why append:** simple filter, rows only ever added, never updated → append is the only valid output mode here.

#### Stateful windowed aggregation (update mode)
    
    
    from pyspark.sql.functions import window, col
    
    spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "localhost:9092") \
        .option("subscribe", "payments") \
        .load() \
        .groupBy(
            window(col("timestamp"), "5 minutes"),
            col("merchant_id")
        ) \
        .count() \
        .writeStream \
        .format("delta") \
        .option("checkpointLocation", "/checkpoints/merchant_counts") \
        .outputMode("update") \
        .start("/data/merchant_counts")

**window(col("timestamp"), "5 minutes"):** buckets rows into 5-minute time windows based on event time. Result has a `window` column with `{start, end}` struct. Late arrivals → watermarking (§30).

**Why update:** aggregation rows get updated each batch as new events arrive → use update, not append.

#### Output mode summary

Mode| What gets written each batch| When to use  
---|---|---  
`append`| Only new rows| Stateless (filter, map) — rows never change  
`update`| Only rows that changed this batch| Aggregations writing to Delta/Kafka  
`complete`| Entire result rewritten every batch| Aggregations writing to memory/console only — expensive  
  
#### Import styles — F.col vs col

Both identical, different import style:
    
    
    # Style 1 — module alias (preferred in production, explicit origin)
    import pyspark.sql.functions as F
    F.col("merchant_id"), F.window(...)
    
    # Style 2 — direct import (less typing, risk of name collision)
    from pyspark.sql.functions import col, window
    col("merchant_id"), window(...)

### §30 Watermarking — late-arriving data & state eviction

The problem: in a windowed aggregation, Spark keeps per-window state (e.g. running counts) in memory/state store forever unless told otherwise — because an event with an old timestamp could theoretically still arrive and belong to an old window. Unbounded state growth = eventual OOM.

**A watermark is a moving threshold** that tells Spark: "I won't wait for events older than this anymore — it's safe to finalize and drop state for windows that have closed."
    
    
    from pyspark.sql.functions import window, col
    
    spark.readStream \
        .format("kafka") \
        .option("subscribe", "payments") \
        .load() \
        .withWatermark("event_time", "10 minutes") \
        .groupBy(
            window(col("event_time"), "5 minutes"),
            col("merchant_id")
        ) \
        .count() \
        .writeStream \
        .format("delta") \
        .outputMode("update") \
        .option("checkpointLocation", "/checkpoints/merchant_counts") \
        .start("/data/merchant_counts")

**How the threshold moves:** watermark = `max(event_time seen so far) − lag` (here, 10 minutes). It only moves forward, never backward, and updates after every micro-batch.

**State eviction:** once the watermark passes a window's _end_ boundary, Spark considers that window closed — its state is dropped from the state store and it stops appearing in future updates.

Event arrives...| Watermark says| Result  
---|---|---  
Before window end + lag| Still within tolerance| Included in the aggregation, window state updated  
After watermark has passed the window| Too late| Silently dropped — no error, no output  
  
**Trade-off:** short watermark (e.g. 1 min) → state evicted fast, memory stays small, but real late data gets dropped → wrong aggregates. Long watermark (e.g. 24 hr) → correctness improves, but state store grows large → memory pressure. Tune to the source's realistic max lateness (e.g. mobile clients buffering offline for a few minutes).

**Rule:** watermark only applies to _stateful_ operations (windowed aggregations, stream-stream joins, dedup). A stateless filter/map has no state to evict, so no watermark is needed.

### §31 Exactly-once with Kafka — source vs. sink, the nuance interviewers probe

This is commonly answered wrong as "just turn on `enable.idempotence=true`." The real answer depends on which side of the pipeline Kafka sits on.

#### Kafka as a SOURCE (reading from Kafka)

Exactly-once here is handled entirely by Structured Streaming's checkpoint mechanism (§28) — Spark tracks the exact Kafka offsets consumed in `checkpoint/offsets/`, and on restart resumes from precisely those offsets. No Kafka-side config needed; this is Spark's job, not Kafka's.

#### Kafka as a SINK (writing to Kafka)

This is where it gets tricky. Structured Streaming's built-in Kafka sink is **at-least-once by default** — if a micro-batch is retried after a partial write, some messages can be re-published as duplicates. Why: unlike the Delta sink (§32), Spark's Kafka writer does _not_ participate in Kafka's transactional API, so there's no atomic "commit this whole batch or nothing" guarantee on the write side.

Mechanism| What it actually protects against| Does it give exactly-once in Spark→Kafka?  
---|---|---  
`enable.idempotence=true` (idempotent producer)| Duplicate messages from a single producer's network retries (broker dedups by producer ID + sequence number)| No — protects one write call, not a whole re-executed micro-batch  
Kafka transactional API (`transactional.id`)| Atomic multi-partition/multi-topic writes — used by Kafka Streams for true Kafka→Kafka exactly-once| No — Spark Structured Streaming's Kafka sink doesn't hook into Kafka transactions  
  
**Practical pattern:**

  * **Kafka source → Delta sink:** true exactly-once, for free — Delta's transaction log + checkpoint commits combine into one atomic unit (§32).
  * **Kafka source → Kafka sink:** at-least-once. If you need exactly-once semantics downstream, make the consumer idempotent — write a unique message key/ID and let the downstream store dedup on upsert (same pattern as MERGE INTO dedup in §26).



### §32 Atomic micro-batch commits to Delta — why Delta gets exactly-once and Kafka sink doesn't

Every Structured Streaming micro-batch that writes to Delta becomes exactly one entry in `_delta_log` (§23) — a single atomic transaction. Delta additionally stores the **streaming batch ID** it last committed as transaction metadata (`txnAppId` + `txnVersion`) tied to the query's checkpoint.

Combine this with the checkpoint's offsets/commits protocol (§28):

  1. Spark writes `offsets/N` before processing batch N
  2. Spark processes and writes the Delta commit for batch N, tagging it with batch ID N
  3. Spark writes `commits/N`



If the job crashes after step 2 but before step 3, on restart Spark reruns batch N — but when it tries to commit to Delta again, **Delta checks the txnAppId/txnVersion it already has on file, sees batch N was already applied, and skips it** instead of double-writing. This is what makes Kafka source → Delta sink genuinely exactly-once, not just at-least-once: the sink itself is idempotent per streaming batch, not just per message.

**Interview framing:** "Delta gets exactly-once because the sink is idempotent at the batch level via txn metadata in the log, combined with Spark's own offset tracking. Kafka sink can't do this because Kafka has no equivalent per-batch dedup mechanism exposed to Structured Streaming."

### §33 Trigger modes — controlling when micro-batches run

Trigger| Behavior| Use case  
---|---|---  
Default (none specified)| Runs the next micro-batch immediately after the previous one finishes — back-to-back, as fast as possible| Low-latency continuous ingestion  
`Trigger.ProcessingTime("10 seconds")`| Fixed interval. If a batch finishes early, waits out the rest of the interval. If it overruns, starts the next batch immediately after| Predictable, throttled cadence — avoid hammering the source/sink  
`Trigger.Once()` _(deprecated)_|  Processes all currently available data as a single giant batch, then stops| Superseded by AvailableNow — kept for legacy jobs  
`Trigger.AvailableNow()`| Processes all currently available data too, but splits it into multiple micro-batches (respects `maxOffsetsPerTrigger`) instead of one huge batch, then stops| Scheduled/batch-like runs (e.g. hourly job kicked off by Airflow) — safer than Once() on large backlogs, avoids one massive shuffle  
      
    
    # Continuous, throttled
    .trigger(processingTime="10 seconds")
    
    # Scheduled batch-style run — process backlog, then exit
    .trigger(availableNow=True)

**Why AvailableNow over Once:** Once() reads the whole backlog as one batch — if the backlog is large, that's one enormous shuffle/state update with no incremental checkpointing along the way, and a crash mid-batch means redoing all of it. AvailableNow() chunks the same backlog into normal-sized micro-batches, each checkpointed independently — a crash only loses the current chunk.

### Recap questions for next 2D session

  1. Name the four folders inside a checkpoint directory and what each stores.
  2. A streaming job has been running for 3 days with windowed aggregations. Someone deletes the checkpoint to "free space." What breaks and why?
  3. You have a simple `filter → write to Delta` pipeline. Which output mode? What if you add a `groupBy().count()`?
  4. Write from blank: Kafka source → filter event_type == "click" → write to Delta with append mode and checkpoint.
  5. What does `window(col("ts"), "10 minutes")` produce in the output schema?
  6. Why does a 5-minute watermark on a 5-minute window mean a window doesn't finalize until 10 minutes after it starts?
  7. True or false: Kafka source → Kafka sink is exactly-once if you enable `enable.idempotence=true` on the producer. Explain.
  8. Why does Kafka source → Delta sink get exactly-once "for free" but Kafka source → Kafka sink doesn't?
  9. You have an hourly Airflow-triggered job processing a Kafka backlog. Trigger.Once(), Trigger.AvailableNow(), or default — which, and why?



* * *

Updated 2026-07-03 — Stage 2D taught in full: §28 Checkpoint (structure, exactly-once two-phase commit, consequence of deletion), §29 Streaming query patterns (stateless append, stateful windowed aggregation with Kafka, output mode comparison, F.col vs col import styles), §30 Watermarking (threshold mechanics, state eviction, trade-offs), §31 Exactly-once with Kafka (source vs. sink nuance, idempotent producer vs. transactional API), §32 Atomic micro-batch commits to Delta (txnAppId/txnVersion idempotency), §33 Trigger modes (default, ProcessingTime, Once vs AvailableNow). Next: hands-on lab + from-blank exercises, then Stage 2E (Lakeflow/DLT).
