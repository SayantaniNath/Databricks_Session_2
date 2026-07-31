# Spark — Master Learning Checklist

Scope: FAANG + Databricks + Top-tier DE interviews  |  Starting from scratch  |  Updated: 2026-06-07

✅ Done Taught in detail + exercises 🟡 Partial In doc but not fully taught ⏳ Pending Not yet covered ⭐ Critical Highest interview weight

## Module 1 — Spark Architecture & Mental Model

Core Architecture ✅ Done

  * Why Spark exists — scale-out vs scale-up
  * Driver, Executors, Cluster Manager — roles and communication
  * SparkSession as entry point
  * Distributed + lazy mental model



Lazy Evaluation ✅ Done

  * Transformations vs Actions
  * Why lazy eval exists — optimization window
  * Narrow vs Wide transformations
  * When execution actually triggers



DAG, Jobs, Stages, Tasks ✅ Done

  * Job → Stage → Task hierarchy
  * Stage boundary = shuffle boundary
  * Stage counting recipe
  * Partitions are per-stage, not summed



Catalyst Optimizer 🟡 Partial

  * 4 phases: Parse → Analyze → Optimize → Physical plan
  * Predicate pushdown
  * Column pruning / projection pushdown
  * Constant folding
  * Cost-based join selection
  * **Missing:** ANALYZE TABLE, statistics collection, explain() deep-dive



Tungsten Execution Engine 🟡 Partial

  * Off-heap memory management
  * Cache-aware columnar processing
  * Whole-stage code generation (WSCG)
  * **Missing:** Reading WSCG in explain() output, * notation



## Module 2 — Partitioning & Shuffles

Partitions ✅ Done

  * Partition = unit of parallelism, one task per partition
  * How partitions are set at read time (maxPartitionBytes = 128MB)
  * spark.sql.shuffle.partitions (default 200)
  * Checking partition count: df.rdd.getNumPartitions()



repartition vs coalesce ✅ Done

  * repartition — full shuffle, can increase or decrease, even distribution
  * coalesce — no shuffle, decrease only, merge locally
  * repartition(n, col) — partition by column key
  * When to use each



Shuffles ✅ Done

  * Map side (shuffle write) → network transfer → reduce side (shuffle read)
  * Why expensive: disk I/O + network I/O + stage barrier
  * What triggers shuffles: groupBy, join, orderBy, distinct
  * How to reduce shuffle cost



Bucketing ⏳ Pending ⭐ Critical

  * Pre-partitioning tables by a join key at write time
  * Eliminates shuffle on joins when both tables bucketed on same key
  * saveAsTable with bucketBy + sortBy
  * When to use bucketing vs repartition
  * Limitations: only works with Hive-style tables



Dynamic Partition Pruning (DPP) ⏳ Pending

  * Runtime pruning of partitions based on join filter
  * Broadcasts filter from one join side to prune the other
  * Transparent — no code changes needed
  * Works on partitioned tables only



## Module 3 — Join Strategies

Broadcast Hash Join (BHJ) ✅ Done

  * Small table broadcast to every executor — no shuffle
  * Default threshold: 10MB (autoBroadcastJoinThreshold)
  * Why no shuffle — match is always local
  * Force with F.broadcast() hint
  * 1 stage only



Sort-Merge Join (SMJ) ✅ Done

  * Both sides shuffled + sorted on join key
  * 3+ stages (2 pre-shuffle + 1 merge)
  * Default for large-large joins



Shuffle Hash Join (SHJ) ✅ Done

  * One side shuffled into hash map, other side streams through
  * Middle ground between BHJ and SMJ



Join Hints & Cost-Based Selection 🟡 Partial

  * F.broadcast() hint covered
  * **Missing:** SQL hint syntax /*+ BROADCAST(t) */, MERGE hint, SHUFFLE_HASH hint
  * **Missing:** How Spark selects join strategy from statistics
  * **Missing:** Storage Partition Join (SPJ) for bucketed tables



## Module 4 — Performance Tuning

AQE (Adaptive Query Execution) ✅ Done

  * Runtime re-optimization after each shuffle
  * Coalescing small shuffle partitions
  * Switching join strategy at runtime
  * Skew join handling (split fat partitions)
  * On by default in Spark 3+



Caching ✅ Done

  * cache() = persist(MEMORY_AND_DISK)
  * Lazy — data cached on first action
  * Storage levels: MEMORY_ONLY, MEMORY_AND_DISK, DISK_ONLY, MEMORY_ONLY_SER
  * When to cache vs not
  * Always unpersist when done



Salting — Data Skew Fix ✅ Done

  * Detect skew: Spark UI Max vs Median partition size
  * Join salting: salt large table + explode small table
  * groupBy salting: salt + two-pass aggregation
  * Bucket sizing: Max / 200MB or Max / Median ratio
  * Salting vs AQE skew handling



Memory Management ⏳ Pending ⭐ Critical

  * Executor memory: heap vs off-heap
  * Storage memory vs execution memory (unified memory model)
  * Memory spill to disk — when it happens, how to fix
  * GC overhead — when JVM GC hurts Spark jobs
  * PySpark overhead: Python worker memory on top of JVM
  * OOM errors — diagnosis and fix



UDFs & Performance ⏳ Pending

  * Python UDF vs Spark SQL built-in functions — why UDFs are slow
  * Pandas UDFs (vectorized UDFs) — Arrow serialization
  * When to use UDFs vs rewriting in native Spark functions



## Module 5 — Spark UI

Spark UI — Reading Execution Plans 🟡 Partial

  * Jobs / Stages / Tasks tabs — covered conceptually
  * BroadcastHashJoin confirmed live (2026-05-29 session)
  * **Missing:** Reading Summary Metrics table (Min/Median/Max/P75) hands-on
  * **Missing:** Shuffle read/write bytes diagnosis
  * **Missing:** GC time, task duration distribution
  * **Missing:** Identifying spill in Spark UI
  * **Missing:** SQL tab — DAG visualization, reading explain() output fully



## Module 6 — Delta Lake ⭐

Delta Lake Fundamentals ⏳ Pending ⭐ Critical

  * What Delta Lake is — ACID on top of Parquet files
  * Transaction log (_delta_log) — single source of truth
  * How every write is recorded as a JSON commit entry
  * Optimistic concurrency control
  * Append-only architecture — files never modified



Time Travel ⏳ Pending ⭐ Critical

  * Query by version: VERSION AS OF n
  * Query by timestamp: TIMESTAMP AS OF '2024-01-01'
  * RESTORE TABLE to previous version
  * How the transaction log enables time travel
  * Retention period and VACUUM interaction



MERGE (Upsert) ⏳ Pending ⭐ Critical

  * MERGE INTO syntax — matched/not matched clauses
  * Upsert pattern (update if exists, insert if not)
  * Delete within MERGE
  * Idempotent MERGE for exactly-once writes
  * Performance considerations of MERGE



OPTIMIZE + Z-ORDER ⏳ Pending ⭐ Critical

  * OPTIMIZE — compacts small files into larger ones (bin packing)
  * Why small files accumulate (streaming, frequent writes)
  * Z-ORDER — co-locates related data using space-filling curves
  * Z-ORDER BY multiple columns — trade-offs
  * Data skipping enabled by Z-ORDER
  * OPTIMIZE vs VACUUM — different purposes



VACUUM ⏳ Pending

  * Removes old files no longer in transaction log
  * Default retention: 7 days
  * Trade-off: VACUUM removes time travel history
  * Safety checks before running VACUUM



Schema Evolution ⏳ Pending

  * mergeSchema — additive column changes
  * Type widening (int → long, float → double)
  * What's NOT supported (narrowing, removing columns)
  * Schema enforcement (rejects mismatched writes by default)



## Module 7 — Structured Streaming ⭐

Streaming Fundamentals ⏳ Pending ⭐ Critical

  * Micro-batch model — how Spark processes streams in small batches
  * Trigger modes: default, fixed interval, once, continuous
  * readStream vs read — streaming vs batch DataFrames
  * Output modes: Append, Update, Complete
  * Sources: Kafka, file sources, Delta
  * Sinks: Kafka, Delta Lake, foreach/foreachBatch



Watermarks ⏳ Pending ⭐ Critical

  * What a watermark is — late data threshold
  * withWatermark(eventTime, "10 minutes")
  * How watermarks determine when windows finalize
  * State cleanup — watermark controls how long state is kept
  * Multi-stream watermarks (minimum used as global)



Exactly-Once Semantics ⏳ Pending ⭐ Critical

  * At-most-once vs at-least-once vs exactly-once
  * Replayable sources (Kafka offset tracking)
  * Idempotent sinks (Delta Lake transaction IDs)
  * Checkpointing for fault tolerance
  * Write-ahead logs (WALs)



Checkpoints ⏳ Pending

  * What checkpoints store (offsets + state)
  * Unique checkpoint per query — never share
  * Recovery from checkpoint on restart
  * Checkpoint location on cloud storage



Stateful Operations ⏳ Pending

  * Stateful aggregations (groupBy + window)
  * Deduplication using state stores
  * State size management and cleanup
  * mapGroupsWithState / flatMapGroupsWithState (advanced)



## Module 8 — Delta Live Tables (DLT) ⭐

DLT Fundamentals 🟡 Partial

  * Lakeflow Designer intro done (2026-05-21)
  * **Missing:** @dlt.table and @dlt.view decorators in Python
  * **Missing:** Materialized views vs Streaming tables vs Views
  * **Missing:** Automatic dependency resolution and DAG
  * **Missing:** Incremental vs full refresh



Expectations (Data Quality) ⏳ Pending ⭐ Critical

  * @dlt.expect — log failures, continue pipeline
  * @dlt.expect_or_drop — drop bad rows
  * @dlt.expect_or_fail — halt pipeline on violation
  * Metrics tracking (passed/failed/dropped counts)
  * Data quality dashboards



Pipeline Management ⏳ Pending

  * Development vs Production mode
  * Auto-scaling clusters in DLT
  * Error handling and retries
  * Monitoring lineage visualization in UI



## Module 9 — Unity Catalog ⭐

Unity Catalog Architecture ⏳ Pending ⭐ Critical

  * Three-level namespace: catalog.schema.table
  * Metastore as top-level governance unit
  * Workspace-level vs metastore-level scopes
  * Securable objects: tables, views, volumes, UDFs, models



Access Control & Grants ⏳ Pending

  * GRANT / REVOKE syntax
  * Catalog → Schema → Table permission hierarchy
  * Role-based access control (RBAC)
  * Row-level and column-level security



Lineage & Governance ⏳ Pending

  * Automatic data lineage tracking
  * Column-level lineage
  * Tags and classifications (PII, PHI)
  * Audit logging



## Module 10 — Data Modeling for Spark

Star Schema & Dimensional Modeling ⏳ Pending ⭐ Critical

  * Fact tables — transactional data, foreign keys, grain definition
  * Dimension tables — context, attributes, SCD handling
  * Star vs snowflake schema — when to use each
  * Conformed dimensions for reusability
  * Degenerate dimensions



Slowly Changing Dimensions (SCDs) ⏳ Pending ⭐ Critical

  * Type 1 — Overwrite (no history)
  * Type 2 — Add new row with effective_from / effective_to dates
  * Type 3 — Add historical column (current + previous value)
  * Implementing SCD Type 2 with Delta MERGE
  * Grain definition — what one row represents



Medallion Architecture ⏳ Pending ⭐ Critical

  * Bronze → Silver → Gold layers
  * Bronze: raw ingestion, no transformation
  * Silver: cleaned, deduplicated, typed
  * Gold: aggregated, business-ready, star schema
  * When to use Delta tables at each layer



## Module 11 — DataFrame API Deep-Dive

Core DataFrame Operations ✅ Done

  * select, filter, withColumn, groupBy, agg, join, orderBy
  * createOrReplaceTempView + spark.sql()
  * show() vs display()
  * explain(True) — reading physical plans



Window Functions 🟡 Partial

  * NTILE, PERCENT_RANK covered (2026-05-27 dailysql.com session)
  * **Missing (PySpark):** Window.partitionBy().orderBy(), F.row_number(), F.rank(), F.dense_rank()
  * **Missing:** LAG / LEAD in PySpark
  * **Missing:** Running totals, moving averages
  * **Missing:** Frame specification (ROWS BETWEEN ...)



Complex Types 🟡 Partial

  * explode() covered in salting context
  * **Missing:** array(), struct(), map() column types
  * **Missing:** F.from_json() / F.to_json() for nested data
  * **Missing:** flatten(), array_contains(), array_distinct()



Schema Management ⏳ Pending

  * StructType / StructField for explicit schema definition
  * Schema inference vs explicit schema (performance implications)
  * printSchema() reading
  * Schema evolution with mergeSchema



## Module 12 — Databricks-Specific

Auto Loader ⏳ Pending ⭐ Critical

  * Incremental file ingestion from cloud storage
  * Automatic schema inference and evolution
  * File notification vs directory listing mode
  * checkpoint location for tracking processed files
  * Use case: Bronze layer ingestion pattern



Photon Engine ⏳ Pending

  * Native C++ vectorized query engine
  * Replaces JVM-based execution for eligible operators
  * 2–8× speedups on average, 12× on benchmarks
  * When Photon helps vs when it doesn't
  * Cost implications (Photon DBU pricing)



Databricks Workflows / Jobs ⏳ Pending

  * Multi-task job orchestration
  * Task dependencies and DAG
  * Job clusters vs all-purpose clusters
  * Retries, alerts, notifications



## Module 13 — Open Lakehouse Formats

Delta vs Iceberg vs Hudi 🟡 Partial

  * Overview + comparison table saved in PySpark_QA_Log.html ✅
  * **Missing deep-dive:** Iceberg hidden partitioning internals
  * **Missing deep-dive:** Hudi COW vs MOR storage types
  * **Missing:** When to choose each at a real company
  * **Missing:** Apache Iceberg with Spark — table API



## Summary — What's Left

Module| Status| Priority  
---|---|---  
1. Architecture & Mental Model| 🟡 Mostly done, Catalyst/Tungsten partial| Medium  
2. Partitioning & Shuffles| ✅ Done — Bucketing + DPP missing| High  
3. Join Strategies| ✅ Done — SQL hints missing| Low  
4. Performance Tuning| 🟡 AQE/Caching/Salting done — Memory mgmt missing| High  
5. Spark UI| 🟡 Conceptual only — hands-on missing| High  
6. Delta Lake| ⏳ Not started| ⭐ Critical  
7. Structured Streaming| ⏳ Not started| ⭐ Critical  
8. Delta Live Tables| 🟡 Lakeflow intro only| ⭐ Critical  
9. Unity Catalog| ⏳ Not started| ⭐ Critical  
10. Data Modeling| ⏳ Not started| ⭐ Critical  
11. DataFrame API| 🟡 Core done — Window fns + complex types missing| Medium  
12. Databricks-Specific| ⏳ Auto Loader / Photon / Workflows missing| High  
13. Lakehouse Formats| 🟡 Overview done — deep-dive missing| Medium
