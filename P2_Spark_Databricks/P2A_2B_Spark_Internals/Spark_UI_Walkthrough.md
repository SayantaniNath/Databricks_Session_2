# Spark UI — Walkthrough  
  
How to read the Spark UI for debugging slow jobs & interview answers. Companion to the Spark architecture doc.

**Contents**

  1. How to access the Spark UI
  2. The six tabs — overview
  3. Jobs tab
  4. Stages tab — the most important
  5. SQL / DataFrame tab
  6. Executors tab
  7. Storage & Environment tabs
  8. Diagnosing 4 common problems
  9. Worked example — slow job walkthrough
  10. Interview cheat-sheet



## 1. How to access the Spark UI

  * **Databricks:** open the cluster → click the **Spark UI** tab. Or from a notebook, click the job-progress widget and follow the "View" link.
  * **Local Spark (laptop):** while a job is running, open `http://localhost:4040`. Multiple SparkSessions = ports 4041, 4042...
  * **spark-submit on a cluster:** the driver logs the UI URL on startup. After the job finishes, the live UI dies — use the **Spark History Server** if enabled.
  * **EMR / Dataproc:** Spark UI is accessible via the cluster's "Application Master" link in YARN ResourceManager.



**The live UI dies when the job ends.** If you need to debug after-the-fact, enable the Spark History Server (`spark.eventLog.enabled = true`). Databricks keeps event logs by default for ~30 days. 

## 2. The six tabs — overview

Tab| Use it for  
---|---  
**Jobs**|  List of all Jobs, their actions, status, duration. Top-down entry point.  
**Stages**|  Per-stage timing, task metrics, shuffle bytes, skew analysis. most important  
**SQL / DataFrame**|  Physical plan + DAG with operator-level metrics. Where to spot bad join strategies.  
**Executors**|  Per-executor memory, GC time, cores, dead executors.  
**Storage**|  Cached/persisted DataFrames — what's in memory, how big.  
**Environment**|  Every Spark config value. Useful for "what did I actually set?"  
  
## 3. Jobs tab

The landing page. Lists every Job (= one action you called) with:

  * **Job ID** — sequential number.
  * **Description** — the action that triggered it (e.g., `count at <notebook>:7`).
  * **Submitted** — when it started.
  * **Duration** — how long it ran.
  * **Stages: Succeeded/Total** — e.g., `4/4` means 4 stages all succeeded.
  * **Tasks: Succeeded/Total** — same idea at task granularity.



Click a Job → drills into its **DAG visualization** (a graph of stages, with shuffle edges between them).

**How to use:** sort by Duration. The longest Job is what to investigate first. 

## 4. Stages tab most important

The single most useful page in Spark UI. Lists every Stage with:

  * **Stage ID**
  * **Description** — the operations in the stage
  * **Duration**
  * **Tasks: Succeeded/Total**
  * **Input** — bytes read from source
  * **Output** — bytes written to sink
  * **Shuffle Read** — bytes pulled from the previous shuffle
  * **Shuffle Write** — bytes written for the next shuffle



### Click into a stage — what to look at

The stage detail page is where 80% of debugging happens. Key sections:

### (a) Summary Metrics table — the skew detector

Shows task-level metrics as a distribution: **Min / 25th / Median / 75th / Max** for each metric.

Metric| What it means| What "bad" looks like  
---|---|---  
Duration| Time per task| Max ≫ Median → **skew**  
GC Time| Time spent in garbage collection| >10% of duration → memory pressure  
Shuffle Read Size| Bytes pulled from previous stage| Max ≫ Median → skewed partition  
Shuffle Spill (Memory)| Data spilled because memory was full| Any non-zero = memory pressure  
Shuffle Spill (Disk)| Data spilled to disk (slow!)| Any non-zero = serious memory pressure  
  
**Skew rule of thumb:** if Max duration is > 3× Median, you have skew. One partition is doing way more work than the others, holding up the whole stage. 

### (b) DAG visualization (top of page)

Shows the operators in this stage and how they connect. Each box is an operator like `Scan parquet`, `Filter`, `HashAggregate`, `SortMergeJoin`, `Exchange`.

  * `Exchange` = a shuffle. Every `Exchange` is a stage boundary.
  * `BroadcastExchange` = the broadcast prep step (good — means broadcast join is being used).
  * `SortMergeJoin` = expensive join. Ask: could this be broadcast?
  * `BroadcastHashJoin` = cheap join (small side broadcast). What you want for big-small joins.



### (c) Tasks table — the per-task drill-down

Lists every task with duration, GC, shuffle read/write, status, host. Sort by Duration to find the slowest task. If one task is much slower than the others and processed much more data — that's your skew suspect.

## 5. SQL / DataFrame tab

Every action shows up here as a "query" with:

  * **Description** — short summary
  * **Duration**
  * **Details** — link to the **physical plan** + a visual DAG of operators with row counts and time per operator



### What to look for in the physical plan
    
    
    == Physical Plan ==
    *(3) HashAggregate(keys=[symbol#10], functions=[avg(price_usd_k#15)])
    +- Exchange hashpartitioning(symbol#10, 200)
       +- *(2) HashAggregate(keys=[symbol#10], functions=[partial_avg(price_usd_k#15)])
          +- *(2) Project [symbol#10, price#11 / 1000 AS price_usd_k#15]
             +- *(2) BroadcastHashJoin [symbol#10], [symbol#20], Inner, BuildRight
                :- *(2) Filter isnotnull(symbol#10)
                :  +- *(2) FileScan json [symbol#10,price#11]
                +- BroadcastExchange HashedRelationBroadcastMode
                   +- *(1) Filter isnotnull(symbol#20)
                      +- *(1) FileScan csv [symbol#20,market_cap_tier#21]

Reading bottom-up:

  * `FileScan` — reading source files.
  * `Filter` — predicate.
  * `BroadcastExchange` — small side being broadcast. **Good sign.**
  * `BroadcastHashJoin` — the actual join (efficient). If you see `SortMergeJoin` instead, both sides shuffled.
  * `HashAggregate` appears twice — **partial** aggregation before the shuffle, **final** aggregation after. This is Spark's two-phase aggregation pattern.
  * `Exchange hashpartitioning` — the shuffle for groupBy.
  * `*(N)` prefix = stage number. Whole-stage codegen groups operators in the same stage.



**Interview gold:** "How do you tell which join strategy Spark used?" → "Read the physical plan in the SQL tab. `BroadcastHashJoin` = good for big-small. `SortMergeJoin` = both sides shuffled. `ShuffleHashJoin` = rare, falls between." 

## 6. Executors tab

Per-executor view. Each row shows one executor (or the driver) with:

  * **Cores** — how many tasks can run in parallel on this executor.
  * **Memory Used / Total** — RAM consumed vs allocated.
  * **Disk Used** — spill bytes.
  * **Active Tasks / Total Tasks** — current and lifetime workload.
  * **Task Time (GC Time)** — total CPU time and time spent in GC.
  * **Input / Shuffle Read / Shuffle Write** — totals.
  * **Status** — Active or Dead.



**Red flags:** any "Dead" executor (probably OOM'd — check logs). GC time > 10% of task time (memory pressure). One executor doing 5× the work of others (skew at the executor level). 

## 7. Storage & Environment tabs

**Storage:** lists every cached/persisted DataFrame and how much memory + disk it's using. Useful when you call `df.cache()` or `df.persist()` — verify what's actually in memory.

**Environment:** dumps every Spark config value (executor memory, shuffle partitions, broadcast threshold, etc.). When debugging "did my setting actually apply?" — this is where you confirm.

## 8. Diagnosing 4 common problems

### Problem 1 — "My job is slow. Where do I start?"

  1. **Jobs tab** → sort by Duration → identify the slow Job.
  2. Click into it → see the DAG with stage durations.
  3. **Find the slow stage** (usually 80%+ of total time in one stage).
  4. Click that stage → look at **Summary Metrics** for skew, GC, spill.



### Problem 2 — Skew

**Symptom:** stage takes forever, but most tasks finished in seconds. One straggler task runs for minutes.

**Spot it:**

  * Stage's **Summary Metrics** : Max Duration ≫ Median Duration.
  * **Tasks table** : sort by Duration, see one task with huge Shuffle Read Size or Input Size.



**Fix:** salt the join key, enable AQE skew-join handling (`spark.sql.adaptive.skewJoin.enabled = true` in Spark 3+), or pre-aggregate skewed keys.

### Problem 3 — Memory pressure (OOM / spill)

**Symptom:** tasks failing with OOM, or stages super slow with non-zero Shuffle Spill (Disk).

**Spot it:**

  * Stage Summary Metrics: **Shuffle Spill (Memory)** and **Shuffle Spill (Disk)** non-zero.
  * Executors tab: **GC Time / Task Time** > 10%.
  * Dead executors in Executors tab.



**Fix:** increase `spark.executor.memory`, increase `spark.sql.shuffle.partitions` (smaller per-partition data), reduce skew, or partition input differently.

### Problem 4 — Bad join strategy (the broadcast miss)

**Symptom:** a stage shuffling huge amounts of data for a join where one side is small.

**Spot it:**

  * SQL tab → physical plan shows `SortMergeJoin` instead of `BroadcastHashJoin`.
  * Stage's Shuffle Write/Read is in GB+ for a join.



**Fix:** wrap the small side in `broadcast(df)`, or raise `spark.sql.autoBroadcastJoinThreshold`.

## 9. Worked example — slow job walkthrough

Imagine a FinFlow report job takes 45 minutes. Walking through the UI:

Step 1: Jobs tab ───────────────── Job ID Description Duration Stages 0 schema-infer (read.json) 3s 1/1 1 write parquet at report.py 45m 4/4 ← THE SLOW ONE Step 2: Click Job 1 → DAG view ────────────────────────────── Stage 0 (read transactions) 2m ← OK Stage 1 (read users_meta) 5s ← OK Stage 2 (join + filter + agg) 42m ← BOTTLENECK Stage 3 (write parquet) 1m ← OK Step 3: Click Stage 2 → Summary Metrics ────────────────────────────────────── Metric Min 25% Median 75% Max Duration 5s 12s 18s 25s 38min ← SKEW! Shuffle Read 50MB 80MB 120MB 180MB 18GB ← ONE TASK READS 18 GB! GC Time 0s 1s 2s 3s 5s ← OK Step 4: Stage 2 → Tasks table → sort by Duration desc ───────────────────────────────────────────────────── Task ID Duration Shuffle Read Host 157 38min 18 GB executor-9 104 25s 180 MB executor-3 ... → Task 157 processing one mega-partition. Check the join key distribution — likely a "hot" user_id (system user, anonymous, null, etc.) with most of the rows. Diagnosis: skew on join key. Fix: AQE skew-join, or salt the key, or filter the hot value separately.

That's the full debug path — Jobs → Stage → Summary Metrics → Tasks. Three clicks from "the job is slow" to "this one partition is the problem."

## 10. Interview cheat-sheet

Question| Answer-shape  
---|---  
"How do you debug a slow Spark job?"| "Open Spark UI, Jobs tab → find slow job → click into stages → identify slowest stage → look at Summary Metrics for skew, GC, spill → drill into Tasks table to find the straggler."  
"How do you spot skew?"| "Stage Summary Metrics. If Max Duration is > 3× Median, you have skew. Confirm with Tasks table — one task has much larger Shuffle Read."  
"How do you know which join strategy Spark used?"| "SQL tab → physical plan. `BroadcastHashJoin` = small side broadcasted (good). `SortMergeJoin` = both sides shuffled (expensive)."  
"What does Shuffle Spill (Disk) mean?"| "Memory wasn't enough to hold shuffle data, so Spark spilled to disk. Slow. Fix: more executor memory, more shuffle partitions, or fix skew."  
"How do you verify a config actually took effect?"| "Environment tab in Spark UI lists every active config value."  
"What's the difference between Jobs and Stages?"| "One action = one Job. One Job = many Stages, split at shuffle boundaries. One Stage = many Tasks, one per partition."  
  
### Three killer phrases to use in interviews

  1. "I'd start by looking at the Spark UI — Jobs tab, then drill into the slow stage."
  2. "In the Summary Metrics, if Max ≫ Median for task duration, that's skew."
  3. "The physical plan in the SQL tab shows me whether Spark chose BroadcastHashJoin or SortMergeJoin."



* * *

Generated 2026-05-28 — companion to `Spark_Architecture_Walkthrough.html`. Read this once, then refer back when working in Databricks notebooks.
