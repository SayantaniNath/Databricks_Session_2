# DE Interview Prep — Full Learning Path

**Sayantani Nath | Updated: 2026-08-04**
**Goal:** Job-ready for FAANG / Databricks DE roles by Oct 1, 2026
**Base:** Strong SQL, Python, Snowflake/Redshift production, AWS CCP in progress

---

## ⚡⚡ CURRENT PLAN — rebuilt 2026-08-04 (supersedes the Jul 28 plan below)

**Meta interview CONFIRMED: Friday 2026-09-04 — and the role changed to `Data Scientist, Product Analytics` (IC5).**
This is a different loop from the DE one prepped in June–July: four 45-min rounds — **Technical Skills · Analytical Execution · Analytical Reasoning · Behavioral**. There is **no data modeling round**, and no DSA/LeetCode round. Stats/probability, A/B testing and product sense — none of which were in this plan — are now the bulk of the grade.

➡️ **Full round-by-round breakdown, gap analysis, frameworks, question bank, and the day-by-day Aug 4 → Sep 3 schedule live in [`P9_Meta_DS_Product_Analytics/P9_Meta_DS_Product_Analytics_Prep.html`](P9_Meta_DS_Product_Analytics/P9_Meta_DS_Product_Analytics_Prep.html).**

**Calendar changes made 2026-08-04:**

| Item | Was | Now |
|---|---|---|
| Aug 4 → Sep 3 | Aug 1–21 P4+P7 push | **Meta DS Product Analytics prep** (primary track) |
| P7 project hands-on + Kafka hands-on | Aug 1–21, spread | **Aug 25–29** (one shared week; Meta drills continue daily) |
| AWS CCP exam | Sep 1–6 | **Sep 8–21** |
| Databricks DEA exam | Sep 1–6 | **Sep 8–21** |
| SnowPro Core exam | Sep 2026, TBD | **Sep 8–21** |
| Snowflake 4C · dbt 4D · Airflow 4B | Aug 1–21 | **Unscheduled** — Oura material, and Oura has no date yet |

**Weekly shape Aug 4 → Sep 3:** Tue–Fri 1 hr Meta track (stats → A/B testing → product sense → behavioral, in that order), Sat ~3 hr mock rounds, Sun rest. Week of Aug 25–29 shares the hour with P7/Kafka builds.

**Standing rule for the whole window:** every SQL rep is a **complete, runnable query typed from blank on a clock**. Meta's own candidate guide states pseudo-code is not acceptable — fragment mode is a scored failure.

---

## ⚡ PREVIOUS PLAN — rebuilt 2026-07-28 (kept for the Oura track)

**Two live interview loops:**
- **Ōura — Senior Data Architect (SF).** Recruiter reached out Jul 28 to move ahead. JD stack: Snowflake, dbt, Iceberg, Databricks/BigQuery, Kafka/Kinesis, Airflow/Dagster, Fivetran, data mesh + federated governance, MDM, HIPAA/PHI, vector/RAG architecture. 8+ yrs, $172.5–203K, in-office SF.
- **Meta — DE Product Analytics (E5).** HR screen done Jul 24; likely rerouted req; technical screen expected ~Aug 24, ball on recruiter's side.

**Exams moved again: AWS CCP + Databricks DEA now sit Sep 1–6** (were Aug 10–16, then Aug 24–31). Aug 22–31 becomes dedicated prep runway rather than a cram week, and the Aug 24 Meta-screen collision is cleared.

### AUG 1–21 PUSH — Pillar 4 + Pillar 7 compressed for interview readiness

The Oura JD maps almost 1:1 onto the untouched P4/P7 backlog, so those stopped being "resume breadth" and became direct prep.

**Design principle: P4 and P7 are the SAME sessions, not competing tracks.** Fraud Detection = the Kafka capstone. CDC Pipeline = Kafka + the SCD2-MERGE hands-on still owed from 2J. Airflow gets wired into both. Built serially these were ~40 hrs against ~14 hrs of slots; merged, they fit.

| Week | Mon/Wed/Fri (1 hr) | Tue/Thu (1 hr) | Sat (~3 hr) |
|---|---|---|---|
| **Aug 1–7** | 8/3 Kafka: exactly-once, idempotent producer, transactional API, partitioning · 8/5 Kafka Connect + Debezium + kafka-python · 8/7 ClinicalFlow Ph2 deploy to MWAA + tear down | 8/4 Snowflake 4C pt.1 — warehouses, micro-partitions, time travel/fail-safe, zero-copy clone · 8/6 4C pt.2 — Snowpipe, Streams, Tasks, VARIANT/FLATTEN, RBAC | 8/1 ClinicalFlow **Phase 2** — MWAA DAG, local dev first |
| **Aug 8–14** | 8/10 Fraud Detection pt.1 — Kafka producer + Structured Streaming → Delta · 8/12 pt.2 — IsolationForest + alert topic + first Airflow DAG · 8/14 **CDC Pipeline** — Debezium → Kafka → Delta CDF + SCD2 MERGE | 8/11 4C pt.3 — Snowpipe auto-ingest + Streams/Tasks CDC on Synthea · 8/13 4C wrap — vs-Databricks articulation, warehouse sizing | 8/8 ClinicalFlow **Phase 3** — Kinesis → Lambda → Firehose → S3 |
| **Aug 15–21** | 8/17 Airflow — wire both project DAGs + vs-Databricks-Workflows articulation · 8/21 **Portfolio** — READMEs, architecture diagrams, push, resume bullets | 8/18 dbt 4D pt.1 — structure, ref/source, materializations, incremental · 8/19 pt.2 — tests, dbt-expectations, snapshots (SCD2), profiles.yml → Snowflake · 8/20 pt.3 — Elementary, Jinja/macros, docs lineage, staging→mart | 8/15 Airflow 4B concentrated — operators, retries, SLAs, TaskGroup, XCom, sensors |

**Targets:** Snowflake 4C ✅ and all remaining P7 projects ✅ by **Aug 14**. Pillar 4 fully ✅ by **Aug 21**.

**Open call (not yet confirmed):** cut **Databricks Lakehouse + AI Monitor** (P7 capstone, ~12 hrs) from August → September. Its content is already taught and retained (DLT ✅, UC ✅, medallion ✅) and its old Aug 18–29 slot is now cert-prep window. The table above assumes this cut.

**Meta sprint daily items** — timed 5-SQL+5-Python CoderPad drills, behavioral story building, data modeling mocks — continue on top of the above, unchanged.

---

## STATUS KEY
- ✅ Complete
- 🟡 In Progress
- ⏳ Not Started
- ⏹️ Skipped / Replaced

---

# PHASE 1 — DE-Focused (Jun 8 → Oct 1, 2026)

Structured by interview round order — the thing tested first is built first.

---

## PILLAR 1: SQL + Python Coding
*Interview round: CodeSignal (Round 1) + Algorithm Onsite (Round 2)*

### SQL — Ongoing throughout Phase 1

| Topic | Status | Notes |
|---|---|---|
| Window functions: RANK, DENSE_RANK, ROW_NUMBER, LAG, LEAD, NTILE, PERCENT_RANK | ✅ | Done — dailysql.com 2026-05-27 |
| Complex GROUP BY, HAVING, CTEs, set operations | ✅ | |
| JOIN types, NULL handling, conversion math | ✅ | |
| SCD Type 2 with Delta MERGE INTO syntax | ⏳ | Covered in Pillar 2C |
| DataLemur — 2 problems/week (Tue/Thu 20 min) | 🟡 | Ongoing through Oct; from Jul 2026 filter to Meta-tagged questions |
| **StrataScratch — Meta-tagged SQL (added 2026-07-17 for Meta loop)** | 🟡 | Daily during Meta prep. Session 1 (2026-07-17), 4 hard: consecutive-days streaks (gaps-and-islands — redo from blank), best-seller/month (top-1 per group), rank improvement Dec→Jan (DENSE_RANK + self-join — **passed, own assembly**), MoM % change (LAG — finish Tue) |
| Meta screen patterns to drill: retention cohorts, funnels, gaps-and-islands, top-N per group, LAG/MoM, DENSE_RANK vocabulary | 🟡 | Dialect note: StrataScratch = Postgres (`date - rn::int`, subquery alias required); Meta CoderPad = Presto (`date_add('day', -rn, d)`) |

### Python DE Foundations ← Jun 27–30 (rescheduled from Aug)
*Topics 1–3: Jun 27 (Sat, ~1.5 hr) | Topics 4–5: Jun 30 (Mon, first 45 min of regular slot)*

| Topic | Session | Status |
|---|---|---|
| Generators & iterators: yield, next(), iter(), generator expressions, lazy pipelines | Jun 27 (Sat) | ⏳ |
| Memory-efficient patterns: chunked CSV reads, dtype downcasting, Parquet vs CSV trade-offs | Jun 27 (Sat) | ⏳ |
| Pandas for DE: read_csv(chunksize=), memory_usage(), dtype optimization, groupby/agg/merge, apply vs vectorize | Jun 27 (Sat) | ⏳ |
| Exception handling: try/except/finally/raise, custom exceptions, context managers (with statement) | Jun 30 (Mon) | ⏳ |
| Functions deep-dive: *args/**kwargs, decorators (basic), lambda, map/filter | Jun 30 (Mon) | ⏳ |

### Python Algorithms — NeetCode 150 (expanded scope for Databricks)
*PUSHED 2026-07-03: starts week of Sep 1 (was Aug 1); Mon/Wed slot paused until then. Windows compressed.*
*Cadence: Mon/Wed, 25 min. Log: ~/Downloads/interview_prep/python_log.md*

| Pattern | ~Problems | Est. Window | Status |
|---|---|---|---|
| Arrays & Hashing | Two Sum ✅ + Group Anagrams ✅ + Top K Frequent, Contains Duplicate, Valid Anagram, Product Except Self, Encode/Decode, Longest Consecutive (~8 total) | Sep 1 → Sep 8 | 🟡 |
| Two Pointers | Valid Palindrome, Two Sum II, 3Sum, Container With Most Water, Trapping Rain Water (~5) | Sep 8 → Sep 15 | ⏳ |
| Sliding Window | Best Time to Buy/Sell, Longest Substring Without Repeating, Longest Repeating Char, Permutation in String (~4) | Sep 15 → Sep 19 | ⏳ |
| Trees BFS/DFS ← Databricks CodeSignal | Level Order Traversal, Max Depth, Same Tree, Invert Tree, Validate BST, Right Side View (~6) | Sep 19 → Sep 26 | ⏳ |
| **Python OOP Basics** ← prerequisite for LRU Cache + Concurrency | 1 session (~45 min): `class`, `__init__`, instance vs class methods, `@property`, dunder methods (`__len__`, `__repr__`), inheritance basics — write a `Node` class and a `LinkedList` class from blank | Sep 26 (Fri) | ⏳ |
| Linked Lists ← Databricks CodeSignal | Reverse LL, Merge Two Sorted, Palindrome LL, LRU Cache (~4) | Sep 26 → Oct 3 | ⏳ |
| Binary Search ← Databricks CodeSignal | Capacity to Ship Packages, Find Min in Rotated, Search in Rotated (~3) | Oct 3 → Oct 10 | ⏳ |

---

## PILLAR 2: Spark + Databricks Technical Depth
*Interview round: Spark/Databricks Tech Fit (Round 4) — biggest differentiator*
*Slot: Mon/Wed/Fri 1 hr. Est. window: Jun 8 → Jul 18*

### 2A: Spark Architecture
*Started: 2026-05-28 | Completed: 2026-06-03*

| Topic | Status |
|---|---|
| Driver / Executor / Cluster Manager / SparkSession | ✅ |
| Partitions as unit of parallelism | ✅ |
| Transformations vs actions, lazy evaluation | ✅ |
| Narrow vs wide dependencies, shuffles, stage boundaries | ✅ |
| Job / Stage / Task hierarchy, DAG | ✅ |
| Broadcast joins: auto (<10MB), explicit hint, 50MB boundary | ✅ |
| Spark UI: live session, BroadcastHashJoin confirmed hands-on | ✅ |
| DataFrame API Lessons 1+2: select/filter/join/withColumn/groupBy/agg/orderBy | ✅ |
| PySpark SQL Lesson 3: createOrReplaceTempView, spark.sql, Catalyst plan reading | ✅ |
| Databricks CE live session: serverless compute, display(), Unity Catalog volume upload | ✅ |

### 2B: Spark Internals — Deep Dive
*Started: 2026-06-07 | Completed: 2026-06-09*

| Topic | Status |
|---|---|
| Catalyst optimizer: 4 phases (Analysis → Logical Opt → Physical Planning → Code Gen) | ✅ |
| Tungsten: off-heap memory, whole-stage code generation, WSCG `*(1)` in explain output | ✅ |
| AQE: partition coalescing, dynamic join strategy switching, skew join optimization (Spark 3.0+) | ✅ |
| Shuffles: map-side write → network → reduce side, stage barrier | ✅ |
| spark.sql.shuffle.partitions: why 200 is wrong, how to tune | ✅ |
| Join strategies: BHJ / SMJ / SHJ — when each fires, stage count, speed | ✅ |
| Caching: storage levels, lazy gotcha, when to cache vs not, unpersist | ✅ |
| repartition vs coalesce: shuffle vs no-shuffle, when to use each | ✅ |
| Salting — conceptual + full walkthrough doc (join salting, groupBy salting, Spark UI detection) | ✅ |
| Spark UI hands-on + salting from-blank exercises | ✅ 2026-06-08 |
| Photon engine: C++ vectorized columnar execution, when it activates vs JVM Spark | ✅ 2026-06-09 |

> **2B fully complete. Next: 2C Delta Lake.**

### 2C: Delta Lake Mechanics ⭐ (most-asked topic in Databricks DE interviews)
*Actual start: 2026-06-12 | Est. completion: 2026-06-27*

| Topic | Status |
|---|---|
| _delta_log structure: JSON commit files + Parquet checkpoints at every 10th commit | ✅ 2026-06-12 |
| ACID via optimistic concurrency control (writer conflict resolution) | ✅ 2026-06-12 |
| Time travel: how Delta reconstructs snapshot at version N using the log | ✅ 2026-06-12 (incl. RESTORE) |
| Schema enforcement vs evolution (mergeSchema option), risks of each | ✅ 2026-06-12 |
| OPTIMIZE + Z-ORDER: when it helps, when it doesn't, column selection strategy | ✅ 2026-06-12 (incl. liquid clustering) |
| VACUUM: default 7-day retention, time travel impact, why to never drop below retention period | ✅ 2026-06-12 |
| MERGE INTO: isolation level, under-the-hood mechanics, upsert patterns | ✅ re-taught + retention verified 2026-07-03 |
| Change Data Feed (CDF): pre-image/post-image for UPDATE, how to enable and consume | ✅ re-taught + retention verified 2026-07-03 |
| Small files problem: API call math, how OPTIMIZE consolidates | ✅ 2026-06-12 |
| Dynamic file pruning + data skipping (min/max column statistics) | ✅ 2026-06-12 |
| Delta Sharing: what problem it solves, how it differs from copying data | ✅ re-taught + retention verified 2026-07-03 |
| Delta vs Iceberg vs Hudi: transaction log architecture differences, ecosystem split (Databricks/Apple/Uber) | ✅ re-taught + retention verified 2026-07-03 |
| Hands-on lab: build Delta table in CE, inspect _delta_log, watch checkpoint at v10 (walkthrough doc §23) | ✅ 2026-06-15 |

*2026-07-03: §26/§27 re-teach pulled forward from Monday and completed same day. Retention check: MERGE (write-amp math ✓, corrected "OPTIMIZE = bigger files" → right-sized), CDF pre/post-image ✓, Delta Sharing (pre-signed URLs, no-Databricks recipient) ✓. Format comparison log structures recalled correctly on retry (incl. _last_checkpoint pointer) → ✅. 2C fully complete and retained. Mon 2026-07-06 freed.*

### 2D: Structured Streaming ⭐
*Taught 2026-07-03 in small-steps mode (one concept → one check → next). Reference: walkthrough doc §28–§33.*

| Topic | Status |
|---|---|
| Micro-batch mental model (stream = unbounded table) | ✅ taught + verified 2026-07-03 |
| Checkpoint: what it stores (offsets/commits/state), crash recovery, consequence of deleting it | ✅ taught + verified 2026-07-03 |
| Output modes: append / update / complete — when each applies, constraints | ✅ taught + recapped 2026-07-03 |
| Watermarking: late-arriving data, how window state is evicted after watermark passes | ✅ taught + verified 2026-07-03 |
| Exactly-once with Kafka: source vs sink, Kafka sink = at-least-once | ✅ taught + recapped 2026-07-03 |
| Atomic micro-batch commits to Delta Lake (txn metadata batch-skip) | ✅ taught + recapped 2026-07-03 |
| Trigger modes: default (micro-batch), once, processingTime, availableNow | ✅ taught + recapped 2026-07-03 |
| Exercises Ex1–4 | ✅ closed 2026-07-03 (model answers reviewed together) |
| Ex-5 hands-on checkpoint lab (Free Edition) | ✅ done 2026-07-06 — availableNow batches (serverless-only trigger), offsets/commits inspected, continuation verified, checkpoint delete → duplicates observed; as-run scripts in interview_prep/databricks_exercises.py §5 |

**2D COMPLETE ✅ 2026-07-03** (marked at her request; Ex-5 lab completed 2026-07-06).

### 2E: Delta Live Tables (DLT) ⭐ — ✅ COMPLETE 2026-07-07
*Actual completion: 2026-07-07 (all concepts + retention checks; hands-on lab deferred by her choice to move to DEA prep)*

| Topic | Status |
|---|---|
| Lakeflow Designer intro (Andreas Kretz repo, done 2026-05-21) | ✅ |
| DLT vs manually writing Spark pipelines — what problem it solves | ✅ intro level |
| Expectations: warn / drop / fail modes, when to use each | ✅ taught + checks passed 2026-07-06 (§35) |
| Streaming live table vs materialized view | ✅ taught + checks passed 2026-07-06 (§36) |
| Schema drift prevention: StructType + Expectations pattern | ✅ recapped + check passed 2026-07-07 (§37; schema = shape guard, Expectations = content guard) |
| Pipeline update modes: complete vs append | ✅ taught + check passed 2026-07-06 (§38) |
| **Hands-on lab** (added 2026-07-03): build a mini Lakeflow pipeline in Free Edition — bronze→silver with expectations (warn/drop/fail), watch a violation get dropped | ⏹️ deferred 2026-07-07 — optional during DEA hands-on |

### 2F: Unity Catalog ⭐
*Est. start: 2026-07-11 | Est. completion: 2026-07-14*

| Topic | Status |
|---|---|
| Three-level namespace: catalog.schema.table | ⏳ |
| RBAC: grants, roles, privilege inheritance | ⏳ |
| Row-level security + column masking for PII | ⏳ |
| Data lineage tracking — how it captures table-level and column-level lineage | ⏳ |
| Metastore vs legacy Hive metastore: what changes, what migrates | ⏳ |
| **Hands-on lab** (added 2026-07-03): in Free Edition — create catalog/schema, GRANT to a group, add a row filter + column mask on a PII column, view lineage graph | ⏳ |

### 2G: Auto Loader
*Est. start: 2026-07-14 | Est. completion: 2026-07-16*

| Topic | Status |
|---|---|
| Auto Loader vs COPY INTO: when to use which | ⏳ |
| Two file discovery modes: directory listing vs file notification (Event Grid/SNS) | ⏳ |
| Schema inference, evolution, and schema hints | ⏳ |
| cloudFiles format in PySpark Structured Streaming | ⏳ |
| **Hands-on lab** (added 2026-07-03): Auto Loader ingest from a UC volume — drop files in, watch incremental pickup, then add a new column to test schema evolution | ⏳ |

### 2H: MLflow Basics (appears in Databricks DE rounds)
*Est. start: 2026-07-16 | Est. completion: 2026-07-18*

| Topic | Status |
|---|---|
| Experiment tracking: runs, params, metrics, artifacts | ⏳ |
| Model registry: stages (Staging / Production / Archived) | ⏳ |
| Log model from PySpark/sklearn, load and serve a registered model | ⏳ |
| MLflow UI navigation — what interviewers expect you to know | ⏳ |
| **Hands-on lab** (added 2026-07-03): train a tiny sklearn model, log params/metrics/artifacts, register it, load it back and score a batch | ⏳ |

### 2I: Databricks Platform + Ecosystem
*Fold into above sessions throughout Jun–Jul*

| Topic | Status |
|---|---|
| All-Purpose Cluster vs Job Cluster: cost, startup time, use cases | ⏳ |
| DBUs and cluster sizing for cost estimation | ⏳ |
| Databricks Workflows vs Airflow: when to choose which | ⏳ |
| Secret scopes: Databricks-backed vs Azure Key Vault-backed | ⏳ |
| CI/CD: Databricks Repos + Git integration + databricks-cli | ⏳ |
| **Databricks Asset Bundles (DABs)** ⭐ (added 2026-07-07 — DEA exam #1 miss cluster): `databricks.yml` structure (bundle / targets / resources / include); target env config (`host` + `root_path` nested under `workspace:`); deploy-time vs runtime variables (`--var` baked at `bundle deploy`; `bundle run --var` cannot override); `bundle deploy --auto-approve` for non-interactive CI/CD (`--force` = Git-branch override only). **Hands-on:** init a bundle, define dev/prod targets, deploy a job in Free Edition | ⏳ |
| ai_query() / Mosaic AI functions: inline LLM calls in SQL/PySpark | ⏳ |
| Photon-enabled vs standard Databricks Runtime | ⏳ |
| **Databricks vs Snowflake vs BigQuery** — architecture-level articulation for interviews | ⏳ |

*Snowflake architecture comparison topics are covered as a full crash course — see **4C: Snowflake Crash Course** (Tue/Thu Aug 1–14, pulled forward 2026-07-03).*

### 2J: Data Modeling — EXPANDED 2026-07-03 (OLTP + enterprise + OLAP)
*Est. start: 2026-07-14 | Est. completion: 2026-07-21 (extra sessions for expanded scope)*

| Topic | Status |
|---|---|
| **OLTP modeling:** normalization 1NF→3NF (+BCNF awareness), ER diagrams, keys/constraints, when to denormalize | ⏳ |
| **Enterprise modeling:** Kimball vs Inmon, conformed dimensions, bus matrix | ⏳ |
| **Data Vault 2.0 + practical** (added 2026-07-03): hubs/links/satellites, hash keys, load_date/record_source, when DV beats Kimball; **hands-on: model Synthea patients/encounters into HUB_PATIENT + LINK_ENCOUNTER + SAT_PATIENT_DETAILS in Delta SQL with an incremental load** | ⏳ |
| **OLAP modeling:** star vs snowflake schema, fact vs dimension tables, grain definition, additive/semi-additive/non-additive facts | ⏳ |
| SCD Type 1 (overwrite), Type 2 (history rows with effective dates), Type 3 (prev-value column) | ⏳ |
| Implementing SCD Type 2 with Delta MERGE INTO — full from-scratch exercise | ⏳ |

---

## PILLAR 3: Concurrency Round
*Interview round: Dedicated Concurrency Round at Databricks (Round 3) — most candidates unprepared*
*Est. start: 2026-08-11 | Est. completion: 2026-08-18 | ~8 targeted problems, 1 week intensive*

| Topic | Status |
|---|---|
| Python threading primitives: Lock, RLock, Semaphore, Condition, Event | ⏳ |
| Thread-safe LRU cache with TTL eviction | ⏳ |
| Thread-safe logger with concurrent queue (deque + locking) | ⏳ |
| Sliding window rate limiter (deque + Python time module, 300-sec window) | ⏳ |
| Distributed rate limiter design: Redis + token bucket (conceptual + code skeleton) | ⏳ |
| Write-ahead logging + crash recovery on single-machine key-value store | ⏳ |
| ConcurrentHashMap internal locking — asked as follow-up in Java/conceptual form | ⏳ |

---

## PILLAR 4: Data Engineering Core
*Interview round: Tech Fit + System Design rounds*

### 4A: Kafka
*Est. start: 2026-07-21 | Est. completion: 2026-08-01 | Slot: Mon/Wed/Fri*

| Topic | Status |
|---|---|
| Core concepts: topics, partitions, producers, consumers, consumer groups, offsets | ⏳ |
| Exactly-once semantics: idempotent producer + transactional API | ⏳ |
| Partitioning strategy: key-based vs round-robin, when each matters | ⏳ |
| Replication factor and fault tolerance | ⏳ |
| Kafka Connect + Debezium basics (for CDC pipeline project) | ⏳ |
| Python kafka-python library — producers and consumers | ⏳ |
| Local dev: Redpanda via Docker (Kafka-API-compatible, lighter than Kafka) | ⏳ |

### 4B: Airflow
*Est. start: 2026-08-01 | Est. completion: 2026-08-11 | Slot: Mon/Wed/Fri + Tue/Thu*

| Topic | Status |
|---|---|
| DAGs, operators: BashOperator, PythonOperator, SparkSubmitOperator | ⏳ |
| Scheduling (cron), retries, SLAs | ⏳ |
| TaskGroup, XComs for inter-task data passing, sensors | ⏳ |
| Airflow vs Databricks Workflows trade-off articulation | ⏳ |
| Wire Airflow DAG into Fraud Detection Pipeline as orchestration layer | ⏳ |

### 4C: Snowflake Crash Course ⭐ (Tom Bailey Udemy)
*PULLED FORWARD 2026-07-03 | Slot: Tue/Thu 1 hr (shares slot with DEA prep; DEA wins on exam-crunch weeks) | Est. start: 2026-08-01 | Est. completion: 2026-08-14*
*Why: production background exists; crash course to solidify architecture vocabulary for "Databricks vs Snowflake" interview Q, and prerequisite for dbt (4D)*

| Topic | Status |
|---|---|
| Virtual Warehouses: compute/storage separation, auto-suspend/resume, multi-cluster | ⏳ |
| Micro-partitions: automatic clustering vs Delta Z-ORDER | ⏳ |
| Time Travel + Fail-Safe: retention periods, mechanics, how they differ from Delta | ⏳ |
| Zero-copy cloning vs Delta SHALLOW CLONE | ⏳ |
| Snowpipe (continuous ingestion) vs Auto Loader — trigger model comparison | ⏳ |
| Streams (CDC) vs Delta Change Data Feed | ⏳ |
| Tasks (scheduling) vs Airflow / Databricks Workflows | ⏳ |
| Data Sharing vs Delta Sharing | ⏳ |
| VARIANT, FLATTEN, PARSE_JSON — semi-structured data handling | ⏳ |
| RBAC: roles, users, privilege model | ⏳ |
| Result cache + query pruning: how Snowflake avoids recompute | ⏳ |
| Snowflake vs Databricks: when each wins (governance-heavy warehouse vs open lakehouse) | ⏳ |
| **Mini-project:** Snowpipe auto-ingest from S3 → staging table (hands-on, ~1 hr) | ⏳ |
| **Mini-project:** Streams + Tasks incremental processing (staging → curated, ~1 hr) | ⏳ |
| **Mini-project:** BI views + virtual warehouse sizing + query profile exercise (~1 hr) | ⏳ |

### 4D: dbt Crash Course
*PULLED FORWARD 2026-07-03 | Slot: Tue/Thu 1 hr | Est. start: 2026-08-15 | Est. completion: 2026-08-31*
*Prerequisite: Snowflake (4C). Practice project connects dbt Core to Snowflake.*

| Topic | Status |
|---|---|
| Project structure: models/, seeds/, tests/, macros/, snapshots/ | ⏳ |
| Models: ref(), source(), materialization types (table, view, incremental, ephemeral) | ⏳ |
| Incremental models: is_incremental() macro, unique_key, merge vs append strategy | ⏳ |
| Schema tests: not_null, unique, accepted_values, relationships | ⏳ |
| Custom singular data tests | ⏳ |
| **dbt-expectations** package: GE-style checks in dbt (`expect_column_values_to_not_be_null`, value ranges, regex) — install via packages.yml, run with `dbt test` | ⏳ |
| **Elementary** package: data observability on dbt — anomaly detection (row counts, null %, freshness), schema change alerts, Elementary UI dashboard | ⏳ |
| Snapshots: SCD Type 2 with dbt (timestamp strategy + check strategy) | ⏳ |
| Seeds: loading CSV reference data | ⏳ |
| Macros + Jinja templating | ⏳ |
| dbt docs generate + serve — lineage graph | ⏳ |
| CLI commands: dbt run, dbt test, dbt debug, dbt deps, dbt compile | ⏳ |
| profiles.yml: connecting dbt Core to Snowflake | ⏳ |
| dbt Cloud vs dbt Core trade-offs | ⏳ |
| Practice project: 3-layer model (staging → intermediate → mart) on Snowflake | ⏳ |

---

## PILLAR 5: System Design (FAANG-grade, all 4 phases)
*Interview round: System Design (Round 5)*

### Phase A — DDIA Reading (1 chapter/weekend)
*PUSHED 2026-07-03: Ch 4–9 resume week of Sep 1. Ch 1–3 done.*

| Chapter | Status | Date |
|---|---|---|
| Ch 1 — Reliable, Scalable, Maintainable | ✅ | by 2026-05-29 |
| Ch 2 — Data Models and Query Languages | ✅ | by 2026-05-29 |
| Ch 3 — Storage and Retrieval | ✅ | 2026-06-01 |
| Ch 4 — Encoding and Evolution | ⏳ | Week of Sep 1 |
| Ch 5 — Replication | ⏳ | Week of Sep 7 |
| Ch 6 — Partitioning | ⏳ | Week of Sep 14 |
| Ch 7 — Transactions | ⏳ | Week of Sep 21 |
| Ch 8 — Trouble with Distributed Systems | ⏳ | Week of Sep 28 |
| Ch 9 — Consistency and Consensus | ⏳ | Week of Oct 5 |

### Phase B — Case Studies (1/weekend, Jun 14 → Aug 31, ~10 total)
*6-step framework: requirements → estimation → API → schema → HLD → deep-dive*

| Case | Type | Status |
|---|---|---|
| Prepaid Credits / billing ledger (Chargebee-style) | DE/billing | ✅ 2026-06-01 |
| Design LeetCode (submission pipeline + SLA) | Classic | ✅ 2026-06-03 |
| Real-time fraud detection (Kafka → Structured Streaming → MLflow → Delta) | DE/streaming | ⏳ |
| Lakehouse medallion architecture with governance (Unity Catalog, lineage, RBAC) | DE/lakehouse | ⏳ |
| CDC pipeline at scale (Debezium → Kafka → Delta CDF, SCD Type 2) | DE/CDC | ⏳ |
| Streaming pipeline: late-data handling, watermarks, backpressure | DE/streaming | ⏳ |
| Multi-tenant feature store (offline + online, 50K QPS, sub-50ms p99) | ML/DE | ⏳ |
| Design the Delta Lake transaction protocol (the system itself) | Databricks-specific | ⏳ |
| Unity Catalog (multi-tenant metastore design) | Databricks-specific | ⏳ |
| RAG architecture (architectural only — no LangChain coding) | AI/DE | ⏳ |

### Phase C — Out-Loud Mocks (Sep 1 → Oct 15)
*2 mocks/week, Excalidraw + verbal walkthrough. Redo weak Phase B cases. Build behavioral stories in parallel.*

- ⏳ Mock 1–2 (Sep 1–5)
- ⏳ Mock 3–4 (Sep 7–12)
- ⏳ Mock 5–6 (Sep 14–19)
- ⏳ Mock 7–8 (Sep 21–26)

### Resources
- Designing Data-Intensive Applications — Kleppmann (Phase A–B)
- Alex Xu System Design Interview Vol 2 — Phase B (data-heavy systems)
- Alex Xu Machine Learning System Design Vol 3 — feature store, RAG, recommender chapters
- Hello Interview (hellointerview.com) ⭐ — FAANG-grade SD, Stefan Mai videos
- Exponent (tryexponent.com) — DE-specific mock interviews, Phase C
- excalidraw.com — whiteboarding

---

## PILLAR 6: Certifications

### AWS Cloud Practitioner (CLF-C02)
*Slot: Tue/Thu 1 hr | **Exam: 2nd week of Aug 2026 (Aug 10–16)** — set 2026-07-03; prep wraps mid-Jul, light mock maintenance until exam week*

| Phase | Detail | Status |
|---|---|---|
| Skilljar Modules 1–5 | Modules 1-4 done; Module 5 Networking done 2026-05-19 | ✅ |
| Skilljar Module 6 | Skipped 2026-05-29 — Maarek covers same content faster | ⏹️ |
| Maarek Udemy course | Intensive week Jun 15-19 (1 hr Mon + 3 hrs/day Tue-Fri) — completing Mon Jun 23 | 🟡 |
| Tutorials Dojo Round 1 | Full timed exam, review every wrong answer (~3 hrs) — starts Jul 7 (Tue/Thu) | ⏳ |
| Patch weak topics | Re-watch Maarek sections exposed by TD | ⏳ |
| Tutorials Dojo Round 2 | Score 80%+ consistently → book real exam | ⏳ |

### Databricks Data Engineer Associate (DEA)
*Slot: Tue/Thu, prep starts Jul 18 | **Exam: 2nd week of Aug 2026 (Aug 10–16)** — set 2026-07-03; both certs sit the same week*

| Resource | Status |
|---|---|
| Databricks Academy — "Data Engineering with Databricks" learning path | ⏳ |
| Derar Alhussein Udemy course (~6 hrs condensed) | ⏳ |
| Official Databricks practice exam | ⏳ |
| Skillcertpro / Udemy mocks | ⏳ |

### SnowPro Core Certification
*Slot: Tue/Thu, after Snowflake crash course (4C) wraps Aug 14 (pulled forward 2026-07-03) | Target: Sep 2026*

| Resource | Status |
|---|---|
| Snowflake crash course 4C (Tom Bailey Udemy) — prerequisite | ⏳ |
| SnowPro Core practice exams (COF-C02) | ⏳ |
| Book + sit SnowPro Core exam | ⏳ |

---

## PILLAR 7: Projects (4 DE Portfolio Projects)
*Interview round: Project Walkthrough + demonstrates skills in every other round*

| Project | Stack | Est. Build Window | Status |
|---|---|---|---|
| **AWS ClinicalFlow — Healthcare Data Lakehouse** ⭐ NEW | Synthea EHR (10yr, 64K patients) + S3 + Glue + EMR + Redshift + Lambda + Kinesis + MWAA + Iceberg + KMS + HIPAA/GDPR + **Anomaly Detection (IsolationForest on EMR)** | Phase 1: Jun 23–26 ✅ · Phase 2: Aug 1–11 · Phase 3: Aug 11–18 | 🟡 Phase 1 completing 2026-06-26 |
| **Fraud Detection Pipeline** ⭐ | Kafka → Structured Streaming → IsolationForest → alert Kafka topic → Delta Lake → Airflow | Aug 1–11 | ⏳ |
| **CDC Pipeline** | Debezium → Kafka → Delta (CDF enabled) + SCD Type 2 MERGE INTO | Aug 11–18 | ⏳ |
| **Databricks Lakehouse + AI Monitor** ⭐ | Bronze/Silver/Gold + DLT + Unity Catalog + Airflow + Claude API anomaly detection | Aug 18–29 | ⏳ |

**Portfolio polish window:** Sep 15 → Oct 1 — GitHub READMEs, architecture diagrams, measurable outcomes, deploy instructions.

---

### AWS ClinicalFlow — Healthcare Data Lakehouse: Architecture Spec
*Dataset: **Synthea** synthetic EHR — 100K patients × 10 years → ~50–100M records across patients, encounters, conditions, medications, observations. FHIR R4 JSON format. No credentialing needed; code can be pushed to GitHub.*
*Why healthcare: HIPAA/GDPR/PHI/PII compliance is a top differentiator for healthcare DE roles and appears in senior architect JDs across all verticals.*

**Services demonstrated:** S3 + KMS, Glue (Crawler + ETL + Data Catalog), EMR Serverless, Redshift Serverless, Lambda, Kinesis Data Streams, Kinesis Firehose, MWAA, Apache Iceberg, CloudTrail, CloudWatch

**Compliance layer demonstrated:** HIPAA Safe Harbor de-identification, PHI encryption at rest + in transit, GDPR right to erasure (Iceberg DELETE + VACUUM), consent tracking, audit logging, column-level + row-level access control

#### Data Flow

**Batch path:**
```
Synthea generator → FHIR R4 JSON bundles (PHI: names, DOBs, SSNs, diagnoses, medications)
  → S3 raw zone (KMS encrypted at rest, bucket policy: deny non-SSL)
  → ydata-profiling: HTML profile report (null rates, distributions, record counts per year) — informs ETL design
  → Glue Crawler → Data Catalog (FHIR resource types as tables: Patient, Encounter, Condition, MedicationRequest, Observation)
  → Glue ETL — de-identification step (HIPAA Safe Harbor: mask 18 identifiers):
       patient_name → SHA-256 token | DOB → age bucket (0-17, 18-64, 65+) | zip → 3-digit prefix | SSN → NULL
  → Great Expectations: validate silver (no SSN regex match, no exact DOB, null % on token fields < 1%) — fails job if PHI leaks
  → S3 silver (de-identified, Apache Iceberg format)  ← covers Hudi/Iceberg/Delta tri-fecta
  → dim_patient_consent table: consent given/withdrawn per data use category + effective dates (GDPR)
  → Redshift COPY → fact_encounters, fact_conditions, dim_patient (token only), dim_medication (gold layer)
  → Redshift column privileges: analysts see patient_token only; PHI role sees full dim (restricted)
  → EMR Serverless: 10-year readmission risk aggregation (heavy join across 50M+ rows, terminates after)
```

**Streaming path:**
```
Python producer (replays Synthea encounter events at ~1K events/sec as FHIR JSON)
  → Kinesis Data Streams
  → Lambda (validate schema, check required FHIR fields, add risk_flag via threshold rule)
  → Kinesis Firehose → S3 (streaming prefix, hourly partitions, KMS encrypted)
  → Glue ETL incremental job picks up new S3 partitions → appends to Iceberg silver
```

**Orchestration:**
```
MWAA DAG:
  S3KeySensor (new raw file) → trigger Glue Crawler → GlueJobOperator (ETL)
  → RedshiftDataOperator (COPY) → data quality check (row count, null %) → CloudWatch alarm on SLA breach
```
*Develop + test on local Airflow (same DAG). Deploy to MWAA for 1–2 demo sessions, then delete environment to avoid $0.49/hr cost.*

#### Build Phases

**Phase 1 — Batch (Jun 23 – Jul 4, Tue/Thu slot freed from Maarek + Fri slot):**
- Run Synthea: `./run_synthea -p 100000 --years 10` → FHIR R4 JSON + CSV exports (~10GB raw, ~50–100M records)
- S3 bucket: raw/ (KMS encrypted, deny non-SSL policy), silver/ (de-identified), gold/, audit/ prefixes
- **ydata-profiling** (Session 1, ~30 min): profile Synthea CSVs → null rates, age distributions, encounter counts per year → HTML report to S3 → informs de-identification design
- Glue Crawler on FHIR JSON → Data Catalog (Patient, Encounter, Condition, MedicationRequest, Observation tables)
- Glue ETL — **HIPAA Safe Harbor de-identification step** (Session 2, ~1.5 hr): SHA-256 token for patient_id/name, DOB → age bucket (0-17 / 18-64 / 65+), zip → 3-digit prefix, SSN → NULL, free-text notes → scrubbed
- **Great Expectations** (Session 3, ~1 hr): silver suite — no SSN regex match, no exact DOB column, null % on patient_token < 1%, encounter row count within ±5% of expected → Data Docs HTML to S3; fails Glue job on breach
- `dim_patient_consent`: GDPR consent tracking (consent_category, given_at, withdrawn_at, legal_basis)
- Redshift Serverless: COPY → fact_encounters, fact_conditions, dim_patient (token + age_bucket only), dim_medication
- Redshift column-level privileges: `analyst` role sees patient_token only; `phi_authorized` role sees full dim_patient
- CloudTrail enabled: all S3 GET + Redshift query audit → stored in separate audit/ S3 bucket (immutable)
- EMR Serverless: 10-year readmission risk aggregation across 50M+ rows (1 job, terminate after)

**Phase 2 — Orchestration (Aug 1–11, parallel to Airflow 4B):**
- Build DAG locally first (Airflow), then deploy same DAG to MWAA
- Add CloudWatch alarm: if Redshift row count < expected, fire SNS alert
- Tear down MWAA environment after demo to stop hourly billing

**Phase 3 — Streaming (Aug 11–18, parallel to CDC Pipeline):**
- Python Kinesis producer: stream Synthea encounter events as FHIR JSON
- Lambda handler: schema validation + fraud_flag enrichment + Firehose delivery
- End-to-end test: event → S3 within 60 seconds, Glue picks up within next hourly window

#### Failure Scenarios (built into Phase 1 and 2 — deliberately break and recover each)

| Service | Failure to inject | How to detect | How to recover (prod pattern) |
|---|---|---|---|
| **Glue ETL** | Schema mismatch: add new column to raw S3 file without updating script | Job fails with `AnalysisException` | Enable `mergeSchema` in Glue or add schema evolution handling; use `enableUpdateCatalog` flag |
| **Glue ETL** | Job bookmark drift: reprocess already-seen files | Duplicate rows in silver layer | Reset job bookmark via console; add dedup step on unique key in ETL |
| **Glue Crawler** | Partition not detected after new S3 prefix added | Athena/Redshift Spectrum returns no data | Run `MSCK REPAIR TABLE` or re-trigger crawler; automate with S3 event → Lambda → trigger crawler |
| **Redshift COPY** | S3 IAM role missing `s3:GetObject` on new prefix | `COPY` hangs then fails with `S3ServiceException` | Check `STL_LOAD_ERRORS` table; fix IAM policy or bucket policy; re-run COPY with `MAXERROR` to surface all bad rows |
| **Redshift COPY** | Data type mismatch (varchar too short) | Row-level error in `STL_LOAD_ERRORS` | Inspect error table: `SELECT * FROM STL_LOAD_ERRORS ORDER BY starttime DESC LIMIT 10`; widen column, COPY again |
| **EMR Serverless** | Executor OOM on large shuffle (no salting) | Stage fails, Driver log: `GC overhead limit exceeded` | Increase executor memory config; add repartition before wide transformation; or salt the join key |
| **EMR Serverless** | Spot interruption mid-job | Job fails unexpectedly | Enable checkpointing for Spark jobs; use On-Demand fallback in instance fleet config |
| **Lambda** | Timeout on large Kinesis batch | CloudWatch shows `Task timed out` after 3s | Increase timeout + memory; reduce batch size in Kinesis event source mapping; add DLQ for failed batches |
| **Lambda** | At-least-once delivery causes duplicates in S3 | Duplicate files in Firehose prefix | Make Lambda idempotent: hash event + check S3 object exists before writing; use Firehose deduplication window |
| **Kinesis** | Shard iterator expired (consumer fell behind) | `ExpiredIteratorException` in Lambda logs | Scale shards (`UpdateShardCount`); tune Lambda batch size + parallelization factor; check `GetRecords.IteratorAgeMilliseconds` CloudWatch metric |
| **MWAA / Airflow** | Glue job fails mid-DAG, downstream tasks run anyway | Wrong data in Redshift | Set `trigger_rule=TriggerRule.ALL_SUCCESS` on downstream tasks; add `GlueJobSensor` with failure callback |
| **MWAA / Airflow** | Zombie task (task stuck in `running` state) | Scheduler heartbeat loss, task never completes | Kill via `airflow tasks clear`; set `task_instance_mutation_hook` timeout; configure `scheduler.zombie_task_threshold` |
| **S3** | Object deleted mid-Glue ETL run | Glue fails with `NoSuchKey` | Enable S3 Versioning; add retry logic in ETL script; use Glue job bookmarks to reprocess from last checkpoint |
| **Iceberg** | Concurrent write conflict (two Glue jobs writing same table) | `CommitFailedException` | Iceberg uses optimistic concurrency — conflicting writer retries automatically (up to `write.upsert.enabled`); avoid concurrent writes to same partition by serializing via MWAA task dependency |
| **Great Expectations** | Expectation suite fails on new upstream data (schema drift adds new category) | GE raises `ValidationError`, Glue job exits non-zero | Update expectation suite: add new value to `expect_column_values_to_be_in_set`; add `expect_column_to_exist` checks to catch schema drift early; version suites in S3 alongside data |

#### Cost Controls
| Service | Cost estimate | Action |
|---|---|---|
| S3 | Free (<5 GB) | — |
| Glue ETL (2 DPU, ~5 min/run) | ~$0.07/run | Run sparingly during dev |
| EMR Serverless (1 job) | ~$0.10–0.20 | Terminate immediately after job |
| Redshift Serverless | ~$0.36/RPU-hr | Auto-pause enabled; query only during active work |
| Lambda + Kinesis | Free tier for test volumes | — |
| MWAA | $0.49/hr × ~72 hrs | Spin up Phase 2 week only, delete after (~$35 total) |
| **Total estimate** | **~$50–70** | Acceptable for full AWS DE portfolio project |

#### Interview story
*"Built a HIPAA-compliant clinical data lakehouse on AWS: Synthea synthetic EHR data (100K patients, 10 years, ~50M records). Raw FHIR JSON lands encrypted in S3 (KMS). Glue ETL applies HIPAA Safe Harbor de-identification — token, age bucket, zip prefix — before writing Iceberg silver. Great Expectations validates no PHI leaks downstream. Redshift gold layer with column-level privileges: analysts see tokens only, PHI-authorized roles see full records. CloudTrail audit log on all S3 and Redshift access. GDPR right to erasure handled via Iceberg DELETE + VACUUM. MWAA orchestrates the full batch DAG; Kinesis + Lambda handles real-time encounter event streaming."*

---

### Snowflake Mini-Project (embedded in 4C slot, Aug 1–14 — pulled forward 2026-07-03)
*Same Synthea healthcare data (de-identified). 3 sessions (Tue/Thu), no schedule extension needed.*

| Topic | Status |
|---|---|
| Snowpipe: auto-ingest from S3 event notification → Snowflake staging table | ⏳ |
| Streams + Tasks: CDC-style incremental processing (staging → curated table) | ⏳ |
| BI layer: analytical views + virtual warehouse sizing + query profile exercise | ⏳ |

*Interview story: "Set up Snowpipe to auto-ingest from S3, used Streams + Tasks for CDC-style incremental processing — direct comparison to Kinesis+Lambda (push) vs Snowpipe (poll/event) patterns."*

---

## PILLAR 8: Behavioral
*Interview round: Behavioral (Round 6) | Start: Aug 2026 — do NOT start early, stories get stale*

| Story | Status |
|---|---|
| Most complex data project — end-to-end ownership, trade-offs, measurable outcomes | ⏳ |
| Major optimization — latency / cost / reliability improvement with numbers | ⏳ |
| Conflict with a coworker + resolution | ⏳ |
| Decision made with incomplete information | ⏳ |
| Raised quality bar on a project | ⏳ |
| Why Databricks — must include real product opinion (Delta vs Iceberg, Photon, Unity Catalog model) | ⏳ |
| Databricks vs Snowflake vs BigQuery — architecture-level differentiation | ⏳ |
| Mistake owned + what changed afterward | ⏳ |

---

## PHASE 1 TIMELINE OVERVIEW

| Window | Primary Focus | Slot |
|---|---|---|
| Jun 8 → Jul 18 | Spark Internals (2B) → Delta Lake (2C) → Streaming (2D) → DLT (2E) → Unity Catalog (2F) → Auto Loader (2G) → MLflow (2H) → Data Modeling (2J) + Tom Bailey Snowflake (2I) + AWS CCP | Mon/Wed/Fri + Tue/Thu |
| Jun 23 → Jul 4 | **AWS ClinicalFlow Phase 1** (S3+Glue+EMR+Redshift+Iceberg + failure scenarios) — Tue/Thu freed from Maarek + Fri | Tue/Thu + Fri |
| Jul 7 → Jul 18 | Tutorials Dojo Round 1 + patch weak topics + Round 2 → book AWS CCP exam (Tue/Thu) | Tue/Thu |
| Jul 18 → Aug 1 | Kafka (4A) + Databricks DEA cert starts | Mon/Wed/Fri |
| Aug 1 → Aug 14 | Airflow (4B) + Fraud Detection DAG + **AWS ClinicalFlow Phase 2** (MWAA) + **Snowflake 4C (Tue/Thu, shares slot with DEA)** | Mon/Wed/Fri + Tue/Thu |
| Aug 11 → Aug 18 | Concurrency prep (P3) + CDC Pipeline + **AWS ClinicalFlow Phase 3** (Kinesis+Lambda streaming) | Mon–Fri intensive |
| Aug 15 → Aug 31 | Databricks Lakehouse + AI Monitor capstone build + DEA cert push + **dbt 4D (Tue/Thu)** | Mon/Wed/Fri + Tue/Thu |
| Aug 29 → Sep 15 | SD out-loud mocks Phase C (2/week) + Behavioral stories | Flexible |
| Sep 1 → Oct 15 | **NeetCode resumes (Mon/Wed) + DDIA Ch 4–9 resume (Thu/weekend)** — pushed here 2026-07-03 | Mon/Wed/Thu |
| Sep 1 → Sep 28 | SnowPro Core practice exams → sit exam Sep 2026 | Tue/Thu |
| Sep 15 → Oct 1 | Portfolio polish + GitHub + Apply | Flexible |

**Ongoing every week:**
- Mon/Wed: NeetCode Python (25 min, within session) — **PAUSED until Sep 1** (2026-07-03)
- Tue/Thu: DataLemur SQL (20 min); DDIA chapter (Thu) — **PAUSED until Sep 1** (2026-07-03)
- Weekend: SD Phase B case study (1/weekend, Jun 14 → Aug 31) + Databricks blog post (15 min)

---

# PHASE 2 — AI/LLM Engineering (post-October 2026)

Start after applying is underway. Not needed for DE interview rounds.

| Stage | Content | Status |
|---|---|---|
| Stage 5 — GraphQL | Queries, mutations, schema, playground | ⏳ Phase 2 |
| Stage 6 — DeepLearning.AI LLM Foundations | LangChain, LangGraph, ChatGPT Prompt Engineering, Building Systems with ChatGPT API | ⏳ Phase 2 |
| Stage 6 — Responsible / Ethical AI | Bias mitigation, risk assessment, quality reviews | ⏳ Phase 2 |
| Stage 7 — RAG Pipelines (hands-on) | LangChain RAG, Chroma vector DB, Resume Q&A Bot | ⏳ Phase 2 |
| Stage 8 — Agentic Workflows | LangGraph, CrewAI, Vertex Agent Builder, AI Job Application Agent project | ⏳ Phase 2 |
| GCP / Vertex AI full track | Vertex AI Workbench, Model Garden, Vector Search, Agent Builder, Pipelines | ⏳ Phase 2 |

**Note:** RAG *architecture* (for SD rounds) is covered in Phase 1 via a Phase B case study — no hands-on coding needed for interview purposes. LLM coding courses are deferred; architectural understanding is sufficient.

---

## Reference Files
- Spark walkthrough: `~/Downloads/My Learning Journey on DE/Spark_Architecture_Walkthrough.html`
- Databricks DEA resources: `~/Downloads/My Learning Journey on DE/Databricks_DEA_Learning_Resources.html`
- Databricks Lakehouse blueprint: `~/Downloads/My Learning Journey on DE/Project_Databricks_Lakehouse_Blueprint.html`
- Fraud Detection blueprint: `~/Downloads/My Learning Journey on DE/Project_Fraud_Detection_Blueprint.html`
- System Design Prepaid Credits: `~/Downloads/sysdesign/SystemDesign_Prepaid_Credits_Walkthrough.html`
- Python NeetCode log: `~/Downloads/My Learning Journey on DE/interview_prep/python_log.md`
- SD Q&A log: `~/Downloads/My Learning Journey on DE/interview_prep/sd_qa_log.md`
