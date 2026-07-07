# Databricks — Q&A Log

Running log of Databricks-platform questions (Unity Catalog, Photon, DLT/Lakeflow, platform features) asked during learning sessions, with answers. Newest date at bottom. Spark-core questions live in PySpark_QA_Log.

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
