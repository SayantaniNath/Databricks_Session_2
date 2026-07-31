# System Design Q&A Log

---

## 2026-06-03

**Q: How do you identify functional vs non-functional requirements in system design?**

**Functional** = what the system does. Ask: *"What are the core user actions?"*
- Derive directly from the problem statement
- Examples: user can post, read, search, upload, pay, consume credits

**Non-functional** = how well it does it. Ask these explicitly:
- **Scale** — how many users/requests per second?
- **Latency** — how fast must reads/writes be? (real-time vs eventual)
- **Availability** — can it go down? (99.9% vs 99.999%)
- **Consistency** — does every user see the same data immediately?
- **Durability** — can we lose data? (usually no for payments/billing)

From Prepaid Credits mock:
- Functional: subscribe, consume credits, renew, expire, upgrade/downgrade
- Non-functional: idempotency (no double-charge), consistency (FIFO consumption), durability (never lose a grant record)

In interviews: spend first 3-4 minutes asking these questions before drawing anything. Interviewers want to see you clarify before you build.

---

**Q: What is an API and how important is it in DE interviews?**

API = a contract defining how two systems talk. In system design: what endpoints does your system expose, what goes in, what comes out.

Example from Prepaid Credits:
```
POST /grants          → create a new credit grant
POST /consume         → deduct credits for usage
GET  /balance/{user}  → return current balance
```

Importance in DE interviews:
- At Databricks/Google/Stripe — yes, Step 3 of the 6-step framework, expected. Define API before drawing architecture.
- At most DE roles — lighter. They care more about schema, data flow, pipeline design than REST endpoints.

Rule of thumb: define it briefly (2-3 endpoints) to show you think about interfaces, don't spend more than 2-3 minutes on it. Interviewer will redirect if they want more or less.

---

**Q: Synchronous vs asynchronous — what's the difference?**

**Synchronous** — caller waits for the response before moving on.
- Example: REST API call. You call `/get-balance`, wait, get `{balance: 100}`, then code continues.
- Simple, predictable, but caller is blocked.

**Asynchronous** — caller fires the request and moves on. Response comes later (via callback, event, or polling).
- Example: Kafka. Producer writes a message to a topic and continues. Consumer processes it whenever ready.
- More complex, but decouples systems and handles load spikes better.

In DE context:
- Batch pipelines = async (Airflow triggers a job, doesn't wait inline)
- Streaming = async (Kafka producer doesn't wait for Spark to process)
- REST APIs for lookups = sync (check balance, get config)
- Webhooks = async (payment processor calls you back when payment completes)

Interview tip: when designing a pipeline, explicitly state *why* you chose async — usually because producer and consumer have different speeds or the work is long-running.

**Q: Why choose async over sync?**

Choose async when:
1. **Producer and consumer run at different speeds** — Kafka lets a fast producer not overwhelm a slow consumer
2. **Work is long-running** — don't block the caller for a 10-min Spark job; fire and forget
3. **You need to decouple systems** — if the consumer is down, producer keeps working; messages queue up
4. **You need to handle traffic spikes** — async buffers absorb bursts instead of crashing the downstream system

Choose sync when the caller **needs the result immediately** to continue — balance checks, auth, real-time pricing lookups.

---

**Q: What is polling?**

Polling = the client repeatedly asks "are you done yet?" on a fixed interval until it gets a result.

```
Client → GET /status/abc123  → "pending"   (t=0)
Client → GET /status/abc123  → "pending"   (t=1s)
Client → GET /status/abc123  → "completed" (t=2s)  ✓
```

Async because the client didn't block on the original request — but noisy since you make repeated calls even when nothing changed.

Alternatives:
- **Webhooks** — server calls you back when done (you don't ask, it tells you)
- **WebSockets** — persistent connection, server pushes updates in real time

In DE interviews: polling is acceptable for low-frequency checks (job status, batch completion). For high-frequency or latency-sensitive cases, prefer webhook or event-driven callback to avoid polling overhead.

---

**Q: What does O(1), O(log n), O(n), O(n log n) mean? And what does "Redis sorted set uses a skip list, O(log n) insert, O(log n + k) fetch" mean?**

**Big O — what each means:**

| Notation | Meaning | Example |
|---|---|---|
| O(1) | Instant, regardless of size | Dict lookup `seen[key]` |
| O(log n) | Grows slowly — double input, add 1 step | Binary search, Redis sorted set insert |
| O(n) | Grows linearly with input | Loop through a list once |
| O(n log n) | Sorting cost | `sort()`, merge sort |
| O(n²) | Nested loops | Two Sum brute force |

O(log n) intuition: 1 million items → log₂(1M) ≈ 20 steps. You halve the search space each time, so it stays fast at scale.

**Redis sorted set:**
Automatically keeps scores in order as you insert — no separate sort step. Fetching top 50 = "give me first 50 from an already-sorted structure."
- Insert/update a score = O(log n) — ~20 steps even for 1M entries
- Fetch top 50 = O(log n + 50) — find position + read 50 items
- vs. sorting the whole list every time = O(n log n) — massive difference at scale

---

**Q: Does Redis have persistent storage?**

Yes — two options:

- **RDB (snapshot)** — saves point-in-time snapshot to disk every N seconds or N writes. Fast, compact, but can lose last few minutes of data if it crashes between snapshots.
- **AOF (Append Only File)** — logs every write command to disk. More durable (flush every second or every write), but larger files and slower recovery.

Can run both together — AOF for durability, RDB for fast restarts.

Redis is primarily an **in-memory store** — persistence is a safety net, not the main use case. If you need guaranteed durability as the primary requirement (e.g. financial transactions), use a proper DB (Postgres, CockroachDB) and Redis as a cache/leaderboard layer on top.

Interview tip: if you use Redis, expect "what happens if Redis goes down?" — answer: AOF/RDB + source of truth lives in the primary DB, Redis is just the fast read layer.

---

**Q: How does LSM Tree work and what are SSTables?**

**LSM Tree (Log-Structured Merge Tree) — write path:**
1. Write comes in → goes to **memtable** (in-memory sorted structure, usually a red-black tree)
2. Memtable fills up → flushed to disk as an **SSTable**
3. Over time, multiple SSTables pile up → background **compaction** merges them

```
Write → [Memtable] → flush → [SSTable 1]
                             [SSTable 2]  → compaction → [Merged SSTable]
                             [SSTable 3]
```

**SSTable (Sorted String Table):**
- Immutable file on disk
- Keys stored in sorted order
- Has a sparse index + bloom filter so you don't scan the whole file for a lookup
- Once written, never modified — updates/deletes are new entries, old ones removed at compaction

**Read path:**
Check memtable first → then SSTables newest to oldest → return first match found. Reads can be slow if data is spread across many SSTables — bloom filters help by ruling out files that definitely don't contain the key.

**Used in:** Cassandra, HBase, RocksDB, LevelDB — write-heavy workloads where sequential disk writes are faster than random.

**vs B-Tree** (Postgres, MySQL): B-trees update in place → better for reads. LSM writes sequentially → better for high write throughput.

(Covered in DDIA Ch 3)

---

**Q: Why is B-tree not good for writes? What is high write throughput?**

**Why B-trees are slower for writes:**
B-trees store data in pages on disk and updates happen **in place** — finds the exact page on disk and modifies it:
- Random disk I/O (jumping around the disk to find the right page)
- If a page is full, it splits → cascading updates up the tree
- Write-ahead log (WAL) also written for crash recovery = data written twice

LSM writes sequentially — always append to memtable, then flush in one sequential disk write. Sequential writes are much faster than random writes on both spinning disks and SSDs.

**High write throughput** = system can handle a large number of writes per second without slowing down.
- Low: 1,000 writes/sec before slowing down
- High: 500,000 writes/sec (Cassandra, Kafka)

Use cases: IoT sensors, Kafka event ingestion, fraud detection logging every transaction.

Interview rule of thumb:
- Write-heavy → LSM (Cassandra, RocksDB)
- Read-heavy → B-tree (Postgres, MySQL)

---

**Q: Redis sorted sets only take one score — how do you encode points + time as a single number? And why does the decimal offset method break at scale?**

**Decimal Offset Method (works for small scoreboards):**
```
redis_score = points + 1/(1 + time_in_seconds)

User A (5pts, 120s): 5 + 1/121 = 5.008264
User B (5pts, 90s):  5 + 1/91  = 5.010989  ← beats A on tie-breaker ✓
User C (6pts, 500s): 6 + 1/501 = 6.001996  ← beats both ✓
```

**Why it breaks at scale — floating point precision:**
64-bit float has ~15-17 significant digits total across the entire number (integer + decimal combined).

```
1000000000.1736112029  ← needs 20 significant digits
What Redis stores: 1000000000.17361  ← last digits rounded off
```

Two users with different times can round to the same stored value → tie-breaker destroyed.

**The fix — integer bit-shifting:**
Keep everything as integers, subtract time (lower time = higher score):
```
redis_score = points * 10^10 - time_in_seconds

User A (5pts, 120s):  5 * 10^10 - 120  = 49,999,999,880
User B (5pts, 90s):   5 * 10^10 - 90   = 49,999,999,910  ← higher ✓
User C (6pts, 500s):  6 * 10^10 - 500  = 59,999,999,500  ← highest ✓
```

No decimals, no precision loss. 64-bit float handles integers exactly up to 2^53 ≈ 9×10^15.

Rule: decimals break at scale because float precision is shared between both sides of the decimal point. Use integers whenever encoding composite scores in Redis.

---

## SLA Definition and Performance Trade-offs (Staff-level)

Context: LeetCode platform, 10k concurrent users during contests. Product wants "results within 5 seconds."

---

**Q: What is P50, P95, P99? (revisited 2026-06-05)**

Imagine 100 users, sort their response times fastest to slowest:
```
User 1:   0.5s  (fastest)
User 2:   0.6s
...
User 50:  1.2s  ← P50
...
User 95:  3.8s  ← P95
...
User 99:  8.5s  ← P99
User 100: 45s   (slowest)
```
P50 = middle user. Half faster, half slower.
P95 = 95 out of 100 got response by this time.
P99 = 99 out of 100 got response by this time. Only 1 user was slower.
Higher percentile = slower number (you're including more of the tail).

---

**Q: What is P50, P95, P99? (original)**

Percentiles — describe how fast your system is for different slices of users. Imagine 100 requests sorted fastest to slowest:
- P50 = 50th request → half your users are faster than this
- P95 = 95th request → 95% of users are faster than this
- P99 = 99th request → 99% of users are faster than this

Don't use averages — they hide outliers. 99 users at 1s + 1 user at 100s = average ~2s, but that 1 user had a terrible experience. P99 catches them.

**Why P95 for the "5 second" marketing promise:**
- P100 (every request) < 5s → impossible at scale
- P50 < 5s → too easy, wastes the guarantee
- P95 < 5s → 95% of users get the promise kept, only 5% exceed it

Realistic SLA commitment:
- P50 < 2s — most users feel it's instant
- P95 < 5s — aligns with marketing promise
- P99 < 10s — bounds the tail

**Percentile rules of thumb:**
- P50 → capacity planning ("what does a typical request cost us?")
- P95 → user-facing SLA / marketing promise ("95% of users get results in Xs")
- P99 → premium tier SLA or internal engineering target (costs more, used for high-value customers)
- Engineering health check → watch all three together

---

**Q: How do you measure and track SLA compliance?**

Per submission, record: `user_id, submission_id, submitted_at, result_at, latency_ms, status, user_tier`

`latency_ms = result_at - submitted_at`

- Execution service emits `execution.latency_ms` metric to a time-series DB (Prometheus/Datadog)
- Grafana dashboard computes P50/P95/P99 in real time
- Alerts fire if P95 crosses 5s for more than 60 seconds

**Contest vs normal — separate dashboards:**

| | Normal | Contest |
|---|---|---|
| Concurrent users | ~500 | ~10,000 |
| Burst pattern | Steady | Everyone submits at once |
| SLA target | P95 < 5s | P95 < 8s (relaxed, pre-announced) |

Pre-announce relaxed SLA during contests — sets user expectations correctly instead of silently missing the normal SLA. Keep separate dashboards so contest spikes don't pollute normal metrics.

---

**Q: What happens when you can't meet the SLA during traffic spikes?**

System response (in order):
1. **Queue submissions** — don't drop them, buffer in Kafka/SQS. User sees "your submission is queued."
2. **Auto-scale** — spin up more execution workers (1-2 min lag on cloud)
3. **Shed load if queue grows too large** — reject free-tier submissions, let premium through

User communication by severity:

| Severity | Response |
|---|---|
| Minor (P95 = 6s) | Status page yellow — "elevated latency" |
| Moderate (queue backing up) | In-app banner — "high traffic, result may be delayed" |
| Severe | Pause contest submissions temporarily, communicate ETA |

Key principle: users tolerate slow better than unknown. "Estimated wait: 45 seconds" beats a silent spinner.

---

**Q: What is hill-climbing and adaptive resource allocation?**

**Basic auto-scaling** — reactive. Crosses threshold → scale up. Blunt instrument.

**Hill-climbing** — continuously experiments to find optimal allocation:
```
Current: 20 workers, P95 = 4.2s
Try: +5 workers → P95 = 3.1s, cost +20% → worth it?
Try: -3 workers → P95 = 4.8s, cost -15% → acceptable?
```
Keeps nudging up or down, measuring result each time.

**Adaptive strategy:**
```
if P95 > 4.5s → pre-emptively add workers before SLA breach
if queue depth > 500 → prioritize premium, slow-queue free tier
if P95 < 2s for 5 min → scale down, over-provisioned
```

Key insight: watch **leading indicators** (queue depth, P95 trend), not just **lagging indicators** (SLA already breached). Act before the breach, not after.

---

**Q: Trade-offs between strict SLA guarantees and infrastructure costs?**

```
Stricter SLA → more workers always running → higher cost
Looser SLA  → fewer workers → cheaper → worse experience
```

Capacity estimation example:
- Average execution time = 2s per submission
- 5% of 10k users submit simultaneously = 500 submissions/sec
- Each worker handles 0.5 submissions/sec (1 job ÷ 2s)
- 500 ÷ 0.5 = 1,000 workers to handle average load
- P99 buffer (+50%) = 1,500 workers total
- Extra 500 "standby" workers = cost of P99 guarantee

Relaxing P99 → P95 can save 30-60% infrastructure cost.

**When to deliberately degrade service:**
1. **Tiered degradation** — free users queued, premium protected
2. **Cost ceiling hit** — cap workers, let P95 slip, pre-announce as "best effort"
3. **Cascading failure risk** — better to slow the queue than crash everything

Staff-level answer: "Design for P95 as baseline with burst capacity, and a tiered degradation policy that protects premium users when capacity is exhausted."

---

**Q: How do you design SLAs differently for free vs premium users?**

| | Free | Premium |
|---|---|---|
| SLA target | P95 < 10s (best effort) | P99 < 5s (guaranteed) |
| During spike | Queued first | Protected, processed first |
| Queue position | Back | Front |
| Communication | Generic status page | In-app notification with ETA |

Two separate Kafka queues:
```
premium_submissions_queue → dedicated worker pool (never shared)
free_submissions_queue    → shared pool (shrinks during spikes)
```

When capacity is constrained, free queue workers reassigned to premium. Free users slow down, premium don't notice.

"Best effort" for free = no legal commitment. "Guaranteed P99 < 5s" for premium = you owe credits/refunds if missed. SLA tiers are also a sales tool — "upgrade for guaranteed results during contests."

---

**Q: What organizational processes ensure SLAs are realistic?**

1. **SLA review before any public commitment** — engineering signs off with load test results, current P95/P99 numbers, cost estimate
2. **Error budget** — agree upfront how much you're allowed to miss:
   - 99.9% uptime = 8.7 hours downtime/year allowed
   - 99.99% = 52 minutes/year allowed
   - If budget burns too fast → freeze new features until reliability improves
3. **Runbook for breaches** — who gets paged, what they do first, how users get communicated to. No scrambling during incidents.
4. **Post-mortems after every breach** — root cause + fix + what changes in SLA or infrastructure going forward

Staff-level answer: "SLAs shouldn't be set by product or engineering alone. Product defines the user experience goal, engineering defines what's achievable at what cost, operations defines monitoring and response. All three align before anything is committed publicly."

---

## 2026-06-07

**Q: TiDB vs AlloyDB vs CockroachDB — when to use which?**

All three are distributed SQL databases but built for different problems.

| | TiDB | AlloyDB | CockroachDB |
|---|---|---|---|
| Made by | PingCAP | Google | Cockroach Labs |
| Compatible with | MySQL | PostgreSQL | PostgreSQL |
| Type | HTAP (OLTP + OLAP) | HTAP-ish | Pure OLTP |
| Where it runs | Self-hosted / TiDB Cloud | GCP only | Multi-cloud / self-hosted |
| Multi-region? | Yes | No (single region) | ⭐ Yes — core strength |
| Analytics built-in? | ✅ TiFlash columnar | ✅ Columnar engine | ❌ No |

**TiDB** — MySQL-compatible, HTAP: one DB for transactions + analytics on same data. No ETL needed. Popular in fintech/Asia.

**AlloyDB** — Managed Postgres on GCP. 4× faster OLTP, 100× faster analytics vs standard Postgres. Fully managed, no ops. GCP-only.

**CockroachDB** — Globally distributed Postgres-compatible OLTP. Survives region failures, active-active multi-region, serializable consistency. No analytics engine — pure OLTP.

**Interview one-liner:** Pick CockroachDB for geo-distribution + resilience, TiDB for HTAP (MySQL), AlloyDB for managed GCP Postgres with analytics acceleration.

**Follow-up Q: Aren't there other DBs with always-on / multi-region? Why CockroachDB specifically?**

Yes — many options exist:

| Database | Cloud | Multi-region HA | Notes |
|---|---|---|---|
| Amazon Aurora Global | AWS | ✅ Cross-region read replicas | Postgres/MySQL, managed, most popular on AWS |
| Azure Cosmos DB | Azure | ✅ Active-active multi-region | Multi-model APIs |
| Google Spanner | GCP | ✅ Global, strongest consistency | Best-in-class for consistency |
| CockroachDB | Any | ✅ Active-active | Open source, cloud-agnostic |
| YugabyteDB | Any | ✅ Active-active | Open source, Postgres compat, similar to CockroachDB |

**Pick CockroachDB when:** multi-cloud, cloud-agnostic, open source control, or avoiding vendor lock-in.
**Pick Aurora Global** when: already on AWS, want managed, simpler ops.
**Pick Spanner** when: on GCP, need the strongest global consistency guarantees.
**Pick Cosmos** when: on Azure, need multi-model APIs.

Interview answer: "If on AWS → Aurora Global. On GCP → Spanner. CockroachDB for cloud-agnostic/open-source/multi-cloud scenarios."

---

**Q: Database segregation based on CAP theorem**

CAP = Consistency + Availability + Partition Tolerance. Only 2 of 3 guaranteed. P is mandatory for distributed systems → real trade-off is C vs A.

**CP (Consistency + Partition Tolerance):** HBase, MongoDB, CockroachDB, Google Spanner, TiDB, ZooKeeper, etcd, Redis cluster
**AP (Availability + Partition Tolerance):** Cassandra, DynamoDB, CouchDB, Riak
**CA (single node only):** MySQL, PostgreSQL, Oracle, SQLite — become CP or AP once replicated

Where discussed DBs land:
- CockroachDB → CP (serializable, rejects writes during partition)
- Spanner → CP (TrueTime API)
- Cosmos DB → Tunable (5 levels from strong CP to eventual AP)
- Cassandra → AP (tune per query)
- AlloyDB → CP

When to pick: CP = banking/payments (stale data = wrong balance). AP = social feeds, DNS, shopping carts (slightly stale is fine).

Interview one-liner: "P is non-negotiable, so it's really CP vs AP. CP sacrifices availability during partition. AP sacrifices consistency. Modern DBs like Cosmos let you tune per operation."
