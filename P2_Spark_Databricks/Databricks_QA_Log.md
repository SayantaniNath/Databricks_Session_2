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

---

## Auto Loader — 2G lab (2026-07-17): why did schema evolution fail on the WRITE side, not the read side?

**There are TWO independent schema guards** in a `cloudFiles → Delta` pipeline, and evolving one does nothing for the other:

| Guard | Controlled by | State lives in |
|---|---|---|
| Read side | `cloudFiles.schemaEvolutionMode` | `schemaLocation` |
| Write side | `mergeSchema` | the table's `_delta_log` |

Observed: landing a file with a new `region` column threw `DELTA_METADATA_MISMATCH`, **not** `UnknownFieldException`. `DeltaSink.updateMetadata` in the stack = the failure is on the **sink**. Table schema had 4 cols, data schema had 5 → Auto Loader had *already* evolved its read schema (the file was in the dir at stream start), and Delta's **schema enforcement** (2C) then rejected the wider DataFrame.

Normal fix = `.option("mergeSchema","true")` on `writeStream`. **On UC standard access mode** Table ACLs block automatic schema migration → must widen explicitly:

```sql
ALTER TABLE workspace.autoloader_lab.orders_bronze ADD COLUMN region STRING;
```

Result: 4 rows, `region='us-west'` on the new row, **NULL** on the older three. Delta backfills nothing — rows that landed before the column existed have no value for it.

## Why does `addNewColumns` FAIL on a new column instead of silently adding it?

**Mechanical reason:** a stream's schema is fixed when the query starts. `.load()` resolves a schema and Spark builds the query plan around it; that plan is what executors run. A DataFrame's schema **cannot change mid-flight**. So on an unknown column Auto Loader writes the wider schema to `schemaLocation` and stops. The next start reads it, plans around it, and the column flows.

The "fail" is a **handoff, not a rejection** — fail → update → restart.

In production it isn't disruptive: a job with retries (or a Lakeflow pipeline) restarts automatically and resumes from the checkpoint — nothing lost, nothing reprocessed. It only looks harsh when you're the one clicking Run.

Alternatives: `"rescue"` never fails but new columns land in `_rescued_data` as JSON; `"none"` ignores them. `addNewColumns` is the default because a brief restart is a good trade for the column actually existing in the table.

## How do you PROVE the checkpoint made ingestion incremental? (the "1, not 3" test)

`DESCRIBE HISTORY <table>` — one commit per run. Observed: v0 `CREATE TABLE` (implicit, from `toTable`), v1 `numOutputRows=2`, v2 `numOutputRows=1`.

**The inference:** on run 2 both files were still in the directory — nothing moved or deleted. With no memory it would have reprocessed both → 3 rows written and rows 1–2 duplicated. It wrote **1** → it skipped file 1 → the checkpoint (RocksDB) remembered. Swap `cloudFiles` for `spark.read.json` and that run writes 3 *every time*.

Also in the history:

  * Same `queryId` across both runs with `epochId` 0→1 — **stream identity lives in the checkpoint, not the session** (same lesson as the 2D lab, where a notebook restart wiped the vars but the stream resumed).
  * `isBlindAppend=true` — the write read no existing data, which is what makes an append stream cheap and conflict-free under OCC.

File-level proof instead: `.load(base).selectExpr("*", "_metadata.file_name as source_file")` — but add it **before** the first run; earlier rows won't have it.

**Gotchas:** `numFilesInputted` is *not* a real key. `lastProgress` has `numInputRows` at top level; Auto Loader adds `numFilesOutstanding`/`numBytesOutstanding` under `sources[0].metrics`. And keep the query handle — chaining `.awaitTermination()` onto `.toTable()` throws it away.

## What are the alternatives to Auto Loader for ingesting JSON — and what do the commands look like?

  * **Batch PySpark:** `spark.read.json(path)` · `spark.read.format("json").load(path)` · `spark.read.schema(s).json(path)` (explicit schema skips inference).
  * **Batch SQL:** ``SELECT * FROM json.`/path` `` · `SELECT * FROM read_files('/path', format => 'json')` · `CREATE TABLE t USING JSON LOCATION '/path'`.
  * **Incremental SQL:** `COPY INTO t FROM '/path' FILEFORMAT = JSON` — idempotent, tracks loaded files, good for thousands of files on a schedule.
  * **Legacy file streaming source:** `spark.readStream.format("json").schema(s).load(path)` — streams, but re-lists the whole directory every batch and needs an explicit schema: no inference, no evolution, no RocksDB registry. **Auto Loader is its replacement.**

**Dividing line:** only **Auto Loader and COPY INTO remember what they already ingested**; only Auto Loader scales to millions of files with schema evolution. The rest reprocess.

Lakeflow Declarative Pipelines (2E) still use Auto Loader underneath — the pipeline just manages the stream and expectations for you.

## Auto Loader path/setup details worth remembering

  * **Two `format` calls:** `.format("cloudFiles")` = the source is Auto Loader; `.option("cloudFiles.format","json")` = the underlying file type.
  * `cloudFiles.inferColumnTypes=true` matters — without it every inferred column comes back as a **string** (`amount` would be `"100"`, not a bigint).
  * `_schema` and `_ckpt` can live **inside** the scanned directory: Spark's file source skips paths starting with `_` or `.`. Drop the underscore and Auto Loader would try to ingest its own checkpoint.
  * Schema versions are inspectable: `dbutils.fs.ls(f"{schema_loc}/_schemas")` → `0`, `1`, ... Two versions = the fail→update→restart cycle ran.
  * Volume path = the 2F three-level namespace on the file side: `/Volumes/<catalog>/<schema>/<volume>`. UI: **Catalog → workspace → autoloader_lab → Volumes → landing**.
  * `dbutils.fs.put` only **lands** a file (like a source system dropping into S3) — it touches no table. Ingestion happens on the next stream run. Alternatives: `open()`/`pathlib` (volumes behave like a real filesystem), `%sh echo >`, `spark.createDataFrame(...).write.json()` (writes a *directory* of part-files), or Catalog UI → Upload to this volume.
  * `display()` is read-only — it renders `SELECT *`, it never inserts.
