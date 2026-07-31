# Data Vault 2.0 — Live Session Script

Built 2026-07-29. Parked — not yet delivered. Closes the last untouched 2J topic.

**Delivery rule:** one block → ask the check question → wait → confirm → next block. Never read two blocks in a row. `EXPECTED:` lines are not read aloud.

**Prerequisite finding:** the Synthea CSVs are **no longer on disk** — only `~/Downloads/clinicalflow/synthea.jar` survives; `~/output/csv/` is gone. Part 8 Step 0 regenerates or re-downloads them.

---

## PART 1 — The problem DV2 solves that Kimball doesn't

### 1.1 What Kimball optimizes for

Kimball's star schema is a **query-time** optimization. Conformed dimensions, denormalized attributes, one grain per fact — all of it exists to make a business user's aggregate query fast and understandable. To get there, Kimball forces you to **conform on the way in**: you decide what "customer" means, you resolve the conflict between Salesforce's customer and NetSuite's customer, and you write that decision into `dim_customer` before a single row lands. You pay integration cost up front and get clean, fast, decision-ready tables out.

**CHECK:** In one sentence — in a Kimball star, at what point in the pipeline do you resolve conflicting definitions of the same entity from two source systems?
**EXPECTED:** Before/during the load into the dimension — up front, in ETL, before the data lands. (Anything close to "before it hits the star" is correct.)

### 1.2 Where that deal breaks

Three things break it. **(a) Source-system churn** — Salesforce is replaced by HubSpot, or a source adds a field, and conform-first ETL has to be rewritten because the dimension's structure encoded a business decision. **(b) Auditability** — a Type 1 overwrite or a late-arriving correction destroys the ability to answer "what did this warehouse say on March 3rd, and where did each field come from?" Regulated environments (HIPAA, SOX, GxP, finance) need that answer. **(c) Parallel loading** — surrogate sequence keys mean the dimension must load before the fact, serializing the pipeline and putting a lookup on the critical path.

**CHECK:** Of those three — churn, auditability, parallel loading — which does a HIPAA/PHI environment like Oura care about most?
**EXPECTED:** Auditability / lineage. Good follow-up: "and specifically, being able to prove *where* a value came from and that nothing was silently overwritten."

### 1.3 The DV2 inversion: "load first, conform later"

DV2 inverts the order. The **raw vault** ingests source data as-is with zero business rules — no dedup logic, no "fix the bad ZIP codes", no conforming two customer definitions into one. Insert-only, fully audited, historized. Business rules are applied *downstream*, in the business vault and information marts. Consequence: when a business rule changes, you **replay** it against retained raw history instead of re-extracting from a source that may no longer exist.

**CHECK:** If a business rule changes in year 3 — say "active patient" gets redefined — what does DV2 let you do that a conform-first Kimball pipeline doesn't?
**EXPECTED:** Recompute/replay the new rule over the full retained raw history, rather than only applying it going forward or begging the source for history it no longer has.

### 1.4 Direct contrast against her Kimball instincts

State this explicitly — it will fight her training:

| Instinct from Kimball | What DV2 does instead |
|---|---|
| Denormalize for query speed | **Hyper-normalize** for load speed and auditability |
| Dimensions hold descriptive attributes | Hubs hold **only** the business key |
| Surrogate sequence key from a lookup | **Hash** of the business key, computed independently |
| Type 1 overwrite is fine for corrections | **Nothing** is ever updated or deleted |
| One conformed truth in the warehouse | Multiple source truths retained side by side, conformed later |
| The star schema is the deliverable | The star schema is the **last layer**, built on top of the vault |

**CHECK:** Which single row is the biggest reversal of what she'd do by reflex?
**EXPECTED:** No wrong answer — likely denormalize→normalize or "dimensions hold attributes → hubs hold none." Use her answer as the lead-in to Part 2.

---

## PART 2 — Hubs

### 2.1 What a hub is

A table of **distinct business keys** for one business concept, and essentially nothing else. `HUB_PATIENT` is every patient identifier the enterprise has ever seen. Four columns: the **hash key** (PK, derived from the business key), the **business key**, `load_date` (when the vault first saw this key), `record_source` (which system it first arrived from). A hub row is written **once, ever** — first sighting wins, never updated.

**CHECK:** Name the four columns of a hub.
**EXPECTED:** hash key, business key, load_date, record_source. If she gets 3 of 4, prompt for the missing one rather than telling her.

### 2.2 Why the hub holds no descriptive attributes

This is the design's whole point. Descriptive attributes **change**; business keys don't. Put `patient_name` in the hub and a name change forces either an update (destroying auditability) or a new hub row (destroying the "distinct key" guarantee). Evicting all descriptors into satellites makes the hub an **immutable, append-only registry** — loadable from ten source systems in parallel, in any order, with identical results.

**CHECK:** If `patient_name` lived in `HUB_PATIENT` and a patient married and changed her surname, what specifically breaks?
**EXPECTED:** You'd update the hub row (losing the old value / auditability) or insert a second row for the same business key (breaking key uniqueness and every FK pointing at it).

### 2.3 What counts as a business key

The identifier the **business** uses, not the one the database generated. Order number, MRN, NPI, SKU, email — things a human would quote on a phone call. An auto-increment `id` from one application's Postgres is a *bad* business key: meaningless elsewhere, and two sources will collide on it. With no natural key, use a **composite** (`source_system + local_id`) and document it, because that choice permanently defines the hub's grain.

**CHECK:** Synthea's `patients.Id` is a UUID generated by the simulator. Real business key, or surrogate you're stuck with?
**EXPECTED:** A surrogate we're treating as the business key because it's the only stable identifier available — honest answer is "in a real hospital this would be the MRN." Reward her if she flags the discomfort; that instinct is the architect-level read.

### 2.4 ARCHITECT LAYER — hubs

> **Trade-off / ownership:** The hub list *is* the enterprise's master entity list, so **choosing the hubs is a governance act, not a modeling act** — the same argument as a Kimball bus matrix, and worth saying so in an interview. Hub proliferation is the classic failure: 300 hubs means the business had 300 "concepts," i.e. nobody agreed on anything. A healthy enterprise vault is 15–40 hubs. **At scale:** hubs stay tiny (millions of rows, not billions) and are cheap — the storage and compute problem is never the hubs, it's the satellites. **Where you push back:** a proposed hub with exactly one satellite from exactly one source and no links isn't a business concept, it's a table someone copied.

**CHECK:** Given "15–40 hubs" — what does it *mean* organizationally if a team proposes 300?
**EXPECTED:** No shared business definitions; mirroring source tables 1:1 instead of modeling concepts. A governance smell, not a technical one.

---

## PART 3 — Links

### 3.1 What a link is

A table of **relationships between hubs** — always modeled many-to-many, regardless of current cardinality. `LINK_PATIENT_ENCOUNTER` says "this patient key and this encounter key occurred together." Columns: **link hash key** (PK), one **hub hash key per participating hub**, `load_date`, `record_source`. No descriptive attributes — if the relationship has attributes (a rate, a status, a date range), those go in a **satellite hanging off the link**.

**CHECK:** A patient has many encounters; an encounter has exactly one patient. Why is the link still many-to-many?
**EXPECTED:** Cardinality is a *business rule* and business rules change (data-sharing, merged records, a source allowing co-patients). Modeling 1:M bakes today's rule into the structure; M:M makes a cardinality change a data change, not a migration.

### 3.2 The link hash key

Hash of the **concatenated business keys of every participating hub**, in a fixed documented order with a fixed separator. Not a hash of the hub hash keys, not a sequence. Consequence: two independent pipelines, on two clusters, loading two different source files, compute the **same** link hash key for the same relationship — idempotent and parallel with zero coordination.

**CHECK:** Why hash the *business keys* rather than the *hub hash keys*?
**EXPECTED:** So the link can be computed from the raw source record alone, without joining to the hubs first — that's what removes the lookup dependency and lets hub and link load in parallel.

### 3.3 Why links are insert-only, and how deletes are handled

You never update or delete a link row. "This relationship ended" is represented by an **effectivity satellite** on the link (carrying the relationship's status/date range, with a *driving key* determining which side is tracked), or a **status-tracking satellite** fed by CDC recording `I/U/D` flags. The link row stays forever — a permanent statement that this relationship *was once true*, which is exactly what an auditor wants.

**CHECK:** A patient is reassigned from Provider A to Provider B. What happens to the `LINK_PATIENT_PROVIDER` row for A?
**EXPECTED:** Nothing — it stays. A new link row is inserted for B, and an effectivity satellite records that A's relationship ended and B's began.

### 3.4 ARCHITECT LAYER — links

> **Trade-off / ownership:** Links are where DV2 gets expensive — a link between 4 hubs means a 5-table join to reconstruct one business row before touching a single attribute. **Unit of work matters:** if three hubs are only meaningful together (patient + encounter + provider for one visit), model **one 3-way link**, not three 2-way links — splitting destroys the transaction's atomicity and forces the marts to re-derive it. **At scale:** links are the biggest tables after satellites (one row per relationship instance), and the anti-join dedup on load is the hot spot — cluster/Z-ORDER on the link hash key. **Where you push back:** "same-as" links and hierarchical links are legitimate but are where teams over-engineer; if you can't name the query they serve, don't build them.

**CHECK:** Is `LINK_PATIENT_ENCOUNTER_PROVIDER` (one link) better than three pairwise links for a clinical visit? Why?
**EXPECTED:** One link — the three keys are atomic for a visit; splitting them means you can never prove *which* provider was on *which* encounter for *which* patient without re-joining and guessing.

---

## PART 4 — Satellites (THE BRIDGE CONCEPT)

### 4.0 Cold-recall drill — run BEFORE teaching 4.1

Do not skip, do not hint. Ask exactly this:

> "Before I explain satellites — from memory, no looking: in Kimball, what's the technique for tracking the full history of a changing dimension attribute, what's it called, and what columns does it use?"

**EXPECTED:** Slowly Changing Dimension **Type 2**, using `effective_from` / `effective_to` (or `valid_from`/`valid_to`) plus an `is_current` flag, with a new surrogate key row per version.

**IF SHE MISSES IT:** Don't supply the answer. Narrow the prompt: "You'd insert a new row rather than overwrite — what do you need on that row so a query can pick the version that was true on a given date?" Let her rebuild `effective_from`/`effective_to`/`is_current` herself, then name it "Type 2" only after she's described the mechanism. Record the result — this is the recall being repaired.

### 4.1 What a satellite is

Holds all the **descriptive attributes** hubs and links refuse to carry. Hangs off exactly one parent — one hub or one link. Primary key is `(parent_hash_key, load_date)`. When an attribute changes, you **insert a new row** with the same parent hash key and a later `load_date`. The old row stays untouched, forever.

**CHECK:** What is the primary key of a satellite, and why are there two columns in it?
**EXPECTED:** `(parent_hash_key, load_date)` — the parent identifies *which* entity, the load_date identifies *which version* of it.

### 4.2 The punchline: a satellite IS an SCD Type 2

Land this hard — it's the hook for the whole session:

- Type 2's `effective_from` → the satellite's **`load_date`**
- Type 2's `effective_to` → the satellite's **`load_end_date`** (or derived by `LEAD()` over `load_date`)
- Type 2's `is_current` → the row where `load_end_date IS NULL` / `= '9999-12-31'`
- Type 2's "did anything actually change?" comparison → the satellite's **`hashdiff`**

The only real difference is *mechanical*: Kimball's SCD2 typically **updates** the prior row to close it out; strict DV2 **never updates**, so end-dating is done in a view or accepted as a pragmatic exception. **She already knows this pattern — under a different name.**

**CHECK:** Map it back: satellite `load_date` corresponds to which SCD Type 2 column?
**EXPECTED:** `effective_from` / `valid_from` / `start_date`. Then the reverse: "and `is_current`?" → `load_end_date IS NULL`.

### 4.3 Hashdiff — the change detector

A hash of **all descriptive columns concatenated** (never including `load_date` or `record_source`). Each load compares the incoming record's hashdiff against that entity's *current* satellite row: same → skip, different → insert a new version. Replaces column-by-column `col1 <> col1 OR col2 <> col2 OR ...`, which is unreadable at 40 columns and lethally wrong with NULLs.

**CHECK:** Why is comparing a single hashdiff safer than a 40-column `OR` chain?
**EXPECTED:** NULL handling — `NULL <> NULL` is unknown, so the OR chain silently misses changes into or out of NULL. Hashdiff forces you to coalesce NULLs to a fixed token once, consistently.

### 4.4 Satellite splitting

One hub can have **many** satellites, and usually should. Split by **source system** (each source gets its own — that's how the vault holds two conflicting truths side by side without conforming) and by **rate of change** (volatile attributes separate from static). Splitting by rate of change is a direct storage optimization: if a patient's address changes yearly but their risk score changes hourly, one satellite means rewriting the address 8,760 times a year.

**CHECK:** Patient demographics (rarely change) and wearable telemetry (constantly). One satellite or two, and what's the cost of getting it wrong?
**EXPECTED:** Two. One satellite means every telemetry tick duplicates the entire demographic payload — storage explosion, and the single most common DV2 cost blowup.

### 4.5 ARCHITECT LAYER — satellites

> **Trade-off / ownership:** Satellites hold 90%+ of a vault's storage and compute, and are where DV2 projects fail financially. **Storage explosion** is the headline risk: insert-only × wide rows × high-frequency change = monotonic growth with no natural pruning. Mitigations to name: split by rate of change, split by source, satellite-level retention/archival tiers, and *not vaulting high-frequency telemetry at all*. **Ownership:** each satellite has exactly one source system, making data ownership and PHI classification per-satellite — a governance win worth naming in a HIPAA conversation, because you can drop or encrypt a PHI satellite without touching the hub or links. **Where you push back:** if a satellite would receive more than a handful of versions per entity per day, ask whether that data belongs in the vault or in an event/telemetry table the vault merely *references*.

**CHECK:** Oura ingests wearable readings at high frequency. Do those go in a satellite? Argue either way in one sentence.
**EXPECTED:** No — model *device* and *user* as hubs with a link, keep telemetry as a partitioned Iceberg/Delta event table referenced by business key. Vaulting it produces billions of near-identical versions with no auditability benefit, because raw sensor readings are immutable facts, not changing descriptions. Strong answer: "DV2 historizes *state*; telemetry is already *events*, and events don't need SCD2."

---

## PART 5 — Hash keys

### 5.1 Why hash instead of a sequence

A surrogate sequence key requires a **lookup**: to load a fact you must join to the dimension first, so the dimension must finish loading first. Hash keys are computed **from the data itself** — `md5(upper(trim(business_key)))` — so every table loads simultaneously, on separate clusters, in any order, and the keys still line up. The single biggest architectural argument for DV2 at scale, and the one to lead with in an interview.

**CHECK:** What dependency does a hash key remove from the load pipeline?
**EXPECTED:** The key-lookup / load-order dependency between parent and child tables — no more "dimension must load before fact."

### 5.2 The cross-system argument

The hash is deterministic and depends only on the business key, so **two separate systems compute the same key without ever talking to each other.** A Kafka streaming ingest in one region and a nightly batch in another both produce hash key `a3f5...` for MRN `12345`. Merging two vaults is a `UNION` and a dedup — not a key-remapping project. A sequence-based warehouse cannot do this at all.

**CHECK:** Two regional vaults must be merged after an acquisition. Difference in effort between hash keys and sequence keys?
**EXPECTED:** Hash: union + dedup, keys already agree. Sequence: every key collides and means something different — a full remap of every fact table, i.e. a migration project.

### 5.3 Normalization before hashing — the part everyone gets wrong

The hash is only deterministic if the *input* is. Standardize before hashing and write the standard down: **trim**, **upper-case**, **coalesce NULLs to a fixed token** (`'^^'` or `'-1'`), **fixed separator** for composites (`'||'`). If one pipeline hashes `'12345'` and another hashes `' 12345 '`, you have two hubs for one patient and won't find out for months.

**CHECK:** Composite business key `('SYNTHEA', 'abc-123')` — why does the separator matter?
**EXPECTED:** Without it, `('AB','C')` and `('A','BC')` hash identically — a real collision from concatenation ambiguity, not from the hash function.

### 5.4 Syntax — all the spellings

**Spark / Delta SQL**
```sql
md5(concat_ws('||', upper(trim(patient_id))))                        -- 32-char hex
sha2(concat_ws('||', upper(trim(patient_id))), 256)                  -- 64-char hex, collision-safe
```

**PySpark (batch)**
```python
from pyspark.sql import functions as F

bk = F.upper(F.trim(F.col("Id")))
df = df.withColumn("patient_hk", F.md5(F.concat_ws("||", bk)))
# or: F.sha2(F.concat_ws("||", bk), 256)
```

**PySpark (streaming — identical, that's the point)**
```python
# Structured Streaming / Auto Loader: the exact same expression works,
# because the hash depends only on the row, not on any table state.
stream_df = (spark.readStream.format("cloudFiles")
    .option("cloudFiles.format", "csv").load(path)
    .withColumn("patient_hk", F.md5(F.concat_ws("||", F.upper(F.trim(F.col("Id")))))))
```

**Snowflake**
```sql
MD5(CONCAT_WS('||', UPPER(TRIM(patient_id))))          -- VARCHAR(32)
MD5_BINARY(CONCAT_WS('||', UPPER(TRIM(patient_id))))   -- BINARY(16), half the storage
SHA2(CONCAT_WS('||', UPPER(TRIM(patient_id))), 256)    -- VARCHAR(64)
-- Avoid HASH(): fast but non-cryptographic AND not portable across platforms.
```

**Hashdiff — same idea, all descriptors, NULLs coalesced**
```sql
-- Delta
md5(concat_ws('||',
  coalesce(upper(trim(first_name)), '^^'),
  coalesce(upper(trim(last_name)),  '^^'),
  coalesce(cast(birthdate as string), '^^')
)) AS hashdiff
```
```python
# PySpark
cols = ["FIRST", "LAST", "BIRTHDATE"]
hd = F.md5(F.concat_ws("||", *[F.coalesce(F.upper(F.trim(F.col(c).cast("string"))), F.lit("^^")) for c in cols]))
```

**CHECK:** Why is Snowflake's `HASH()` wrong for a vault key, even though it's fastest?
**EXPECTED:** Non-cryptographic and Snowflake-specific — a Spark job or future platform can't reproduce it, killing the "any system computes the same key" property.

### 5.5 ARCHITECT LAYER — hash keys

> **Trade-off / ownership:** **MD5 collisions are real at petabyte scale.** MD5 is 128-bit; birthday-bound collision probability becomes non-negligible in the 10^18 range, and MD5 is cryptographically broken (deliberate collisions are trivial) — which matters if any source is adversarial. SHA-256 is the safe default; the cost is 64 bytes vs 32 per key across every satellite row and join column, a genuine storage and join-CPU tax. **The modern counter-position:** on Snowflake/Databricks with cheap columnar compression, a growing camp skips hashing and joins on the **natural business key** directly — no collision risk, human-readable, debuggable, and the parallel-load property is preserved (the key still comes from the data). Hash keys mainly win for fixed-width joins and multi-column composites. **HIPAA landmine worth raising unprompted at Oura:** hashing an MRN is **not** de-identification — a hash of PHI is still PHI, because the identifier space is small enough to brute-force. Hash keys are a *join* mechanism, never a *privacy* mechanism; de-identification needs a separate salted-token or Safe Harbor treatment.

**CHECK:** An interviewer says "we hash the MRN, so the vault is de-identified." Response?
**EXPECTED:** It isn't. A deterministic hash of a small, enumerable identifier space is trivially brute-forceable and still PHI. De-identification requires a salted/keyed token with the salt held separately, or Safe Harbor removal — a different concern from key generation.

---

## PART 6 — load_date, record_source, immutability

### 6.1 The two audit columns

**`load_date`** is when *the vault* saw the record — system time, not business time. **`record_source`** is where it came from, at useful granularity: not `'oracle'` but `'ORACLE.EHR.PATIENTS'`. Together, every row answers "when did we learn this, and who told us." That's the audit lineage argument, and the entire reason regulated industries adopt DV2.

**CHECK:** A record's business effective date is 2024-01-05 but it arrived 2024-03-01. Which is `load_date`?
**EXPECTED:** 2024-03-01 — arrival/processing time. The business date is a separate column (`applied_date` / `effective_date`), and keeping both is what makes bi-temporal queries possible.

### 6.2 Bi-temporality

Because `load_date` and the business effective date are separate, you can ask two genuinely different questions: *"what was true on March 3rd?"* (business time) and *"what did the warehouse believe on March 3rd?"* (load time). Kimball SCD2 typically collapses these into one date and loses the distinction — exactly what a regulator asks about after a restatement.

**CHECK:** A late-arriving correction restates January's numbers in March. Which question's answer changes?
**EXPECTED:** Business time — "what was true in January" now reads differently. Load time is unchanged: "what we believed in January" is preserved, which proves the restatement was a restatement and not a cover-up.

### 6.3 Why DV2 never updates or deletes

An `UPDATE` destroys evidence; a `DELETE` destroys evidence. In a vault a "change" is a new satellite row, and a "delete" is a status-tracking satellite row recording the deletion event — the original survives. Engineering consequence she already knows from Delta: **append-only writes have no write conflicts**, so concurrent loaders don't fight and the Delta transaction log stays small compared to a MERGE-heavy table.

**CHECK:** Connect to Delta — why is an append-only vault cheaper to write than a MERGE-based dimension?
**EXPECTED:** Appends don't rewrite existing files; MERGE rewrites every file containing a matched row (or uses deletion vectors + rewrite later), causing write amplification, longer transactions, and concurrency conflicts on the Delta log.

### 6.4 ARCHITECT LAYER — immutability

> **Trade-off / ownership:** Insert-only collides head-on with **GDPR/CCPA right-to-erasure** and HIPAA retention limits, and you will be asked. Real answers in order of preference: (1) **crypto-shredding** — store PHI satellites encrypted with a per-subject key and destroy the key, leaving the row structurally intact but unreadable; (2) isolate PII/PHI into dedicated satellites so a targeted physical `DELETE` touches one table, not the whole vault; (3) tokenize at ingest so the vault never holds the identifier. **Ownership:** somebody must own the retention policy *per satellite*, not per warehouse — that's the operational cost of the design. **Where you push back:** "we never delete" is a statement about the *model*, not the *law*; if a mandate says the vault is untouchable, that's a legal-exposure conversation, not a modeling one.

**CHECK:** Which erasure strategy keeps insert-only fully intact?
**EXPECTED:** Crypto-shredding — nothing is deleted or updated, the key just ceases to exist, so the audit chain is unbroken.

---

## PART 7 — When DV2 wins, and when it does not

### 7.1 The three layers

DV2 is three layers, and conflating them is why people think it's unusable:

1. **Raw Vault** — hubs, links, satellites, *zero* business rules. Source data, historized, as-is.
2. **Business Vault** — same three structures, holding *computed* results: derived satellites, standardized values, plus **PIT (point-in-time)** and **bridge** tables built purely as query accelerators.
3. **Information Marts** — the consumption layer, and where **the star schema lives**. Views or materialized tables, in Kimball form, on top of the vault.

Key sentence: **DV2 does not replace Kimball — it sits underneath it.** Nobody queries the raw vault. Analysts query the star.

**CHECK:** Which layer do BI tools and analysts connect to?
**EXPECTED:** The information mart — the star schema. Follow up: "so did she lose any Kimball knowledge in this session?" → No. It's the top layer.

### 7.2 PIT and bridge tables

Reconstructing one business entity from a vault means joining a hub + N satellites, each needing a "pick the version current as of date X" window — expensive, and the same query every time. A **PIT table** precomputes, per entity per snapshot date, the `load_date` to use in each satellite, turning N window functions into N equi-joins. A **bridge table** precomputes hub-to-hub paths across links, collapsing multi-link traversals. Both are pure denormalization for speed, both disposable and rebuildable, both in the business vault.

**CHECK:** PIT and bridge tables are denormalizations for query speed. What does their existence admit about the raw vault?
**EXPECTED:** That it's genuinely too join-heavy to query directly — the model optimizes for load and audit, and you buy query performance back separately. Great interview line: "DV2 doesn't avoid denormalization, it defers it to a layer where it's disposable."

### 7.3 When DV2 wins

Many source systems (5+), high source churn, regulatory audit requirements, M&A that keeps adding systems, multiple teams loading in parallel, and a real need to replay history under changed rules. Healthcare, insurance, banking, pharma. **Also: it needs automation** — a hand-written vault is unmaintainable, so it presupposes dbt (`datavault4dbt`, `AutomateDV`) or a generator like WhereScape/VaultSpeed.

**CHECK:** Oura: Snowflake, dbt, Kafka, data mesh, HIPAA. Which "when DV2 wins" conditions does that hit?
**EXPECTED:** Regulatory audit (HIPAA/PHI), many sources + data mesh (domain teams loading in parallel — the parallel-load property is exactly the data-mesh fit), and dbt automation already in the stack.

### 7.4 When DV2 loses — be blunt

DV2 is **heavy and badly over-applied.** Don't use it for: a single stable source; a small team without automation tooling; a startup where the model changes weekly; pure analytics/ML feature workloads; high-frequency event/telemetry data. The costs are real — roughly 3–5× the table count of an equivalent star, a steep learning curve for every new engineer, join depth that punishes ad-hoc querying, monotonic storage growth. **A well-run Kimball warehouse with disciplined SCD2 solves most companies' problems.** Saying that out loud in an interview reads as senior, not ignorant.

**CHECK:** A team with one Postgres source and three data engineers proposes DV2. Pushback, in one sentence?
**EXPECTED:** One stable source means no integration or conflicting-truth problem to solve, so you'd pay 3–5× the modeling and maintenance cost for the audit benefit alone — which SCD2 dimensions plus an immutable raw landing zone already give you at a fraction of the effort.

### 7.5 ARCHITECT LAYER — the decision itself

> **Trade-off / ownership:** The architect move is to **name the alternatives and the decision criterion**, not to advocate. The spectrum: **Kimball + SCD2 + immutable raw zone** (most companies, most of the time), **DV2** (many sources, regulated, parallel teams), **Anchor Modeling** (even more normalized, near-zero adoption — mention only to show range), **Activity Schema / One Big Table** (event-centric, ELT-native, popular in modern stacks). The criterion: *how many independently-governed sources must be integrated, and is the audit trail a legal requirement or a nice-to-have?* **Where you push back on a DV2 mandate:** ask what the automation strategy is (no generator = no vault), who owns hub definitions (no governance = 300 hubs), and what the information-mart layer looks like (no marts = a vault nobody can query, the classic dead project). If any answer is "we'll figure it out," the honest recommendation is a hybrid: DV2 for the integration-heavy regulated core, plain Kimball for everything else.

**CHECK:** Three questions to ask before agreeing to build a Data Vault?
**EXPECTED:** (1) automation/codegen strategy? (2) who governs hub/business-key definitions? (3) what does the consumption layer look like? Accept the substance in her own words.

---

## PART 8 — HANDS-ON: Synthea → Data Vault

**Framing to read aloud:** "This part you run. I'll give you the steps and the code, and I'll debug with you, but you're driving — every command below is yours to execute."

### Step 0 — Locate or regenerate the data (REQUIRED, do first)

Her `patients.csv` / `encounters.csv` are **no longer on disk**. Only the generator survives. Three options — she picks one:

```bash
# Option A — regenerate locally (she already has the jar)
cd ~/Downloads/clinicalflow
java -jar synthea.jar -p 5000 -s 42 --exporter.csv.export true
ls -la output/csv/          # expect patients.csv, encounters.csv, conditions.csv, ...

# Option B — pull the ClinicalFlow copy back down from S3, if still there
aws s3 ls s3://<her-clinicalflow-bucket>/raw/ --recursive | head
aws s3 cp s3://<her-clinicalflow-bucket>/raw/patients.csv   ~/clinicalflow_dv/
aws s3 cp s3://<her-clinicalflow-bucket>/raw/encounters.csv ~/clinicalflow_dv/

# Option C — public Synthea sample (no generation wait)
# https://synthetichealth.github.io/synthea-sample-data/downloads/synthea_sample_data_csv_latest.zip
```

5,000 patients is plenty; the original 64,338 only matters for runtime realism.

**Columns she'll work with** (Synthea standard):
- `patients.csv`: `Id, BIRTHDATE, DEATHDATE, SSN, DRIVERS, PASSPORT, PREFIX, FIRST, LAST, SUFFIX, MAIDEN, MARITAL, RACE, ETHNICITY, GENDER, BIRTHPLACE, ADDRESS, CITY, STATE, COUNTY, ZIP, LAT, LON, HEALTHCARE_EXPENSES, HEALTHCARE_COVERAGE, INCOME`
- `encounters.csv`: `Id, START, STOP, PATIENT, ORGANIZATION, PROVIDER, PAYER, ENCOUNTERCLASS, CODE, DESCRIPTION, BASE_ENCOUNTER_COST, TOTAL_CLAIM_COST, PAYER_COVERAGE, REASONCODE, REASONDESCRIPTION`

**CHECK before she writes any code:** Which Synthea column is the business key for `HUB_PATIENT`, and which connects `encounters` to it?
**EXPECTED:** `patients.Id` is the patient business key; `encounters.PATIENT` carries that same value — which is exactly why the link hash key can be computed from `encounters.csv` alone, without ever reading `patients.csv`. Make sure she sees that second half; it's Part 3.2 landing in practice.

### Step 1 — Target model

```
HUB_PATIENT ──< SAT_PATIENT_DETAILS
     │
     └──< LINK_PATIENT_ENCOUNTER >── HUB_ENCOUNTER
```

Four tables. Optional stretch: `SAT_ENCOUNTER_DETAILS` off the encounter hub, and `SAT_LINK_PATIENT_ENCOUNTER_STATUS` off the link.

**CHECK:** Where do `TOTAL_CLAIM_COST` and `ENCOUNTERCLASS` belong?
**EXPECTED:** A satellite on `HUB_ENCOUNTER` — they describe the encounter, so they can't live in the hub or the link.

### Step 2 — DDL (Delta SQL, Snowflake deltas noted)

```sql
-- ============ HUB_PATIENT ============
CREATE TABLE IF NOT EXISTS dv_raw.hub_patient (
    patient_hk        STRING    NOT NULL,   -- md5 of the business key
    patient_bk        STRING    NOT NULL,   -- Synthea patients.Id
    load_date         TIMESTAMP NOT NULL,
    record_source     STRING    NOT NULL
) USING DELTA;

-- ============ HUB_ENCOUNTER ============
CREATE TABLE IF NOT EXISTS dv_raw.hub_encounter (
    encounter_hk      STRING    NOT NULL,
    encounter_bk      STRING    NOT NULL,   -- Synthea encounters.Id
    load_date         TIMESTAMP NOT NULL,
    record_source     STRING    NOT NULL
) USING DELTA;

-- ============ LINK_PATIENT_ENCOUNTER ============
CREATE TABLE IF NOT EXISTS dv_raw.link_patient_encounter (
    patient_encounter_hk  STRING    NOT NULL,  -- md5(patient_bk || encounter_bk)
    patient_hk            STRING    NOT NULL,
    encounter_hk          STRING    NOT NULL,
    load_date             TIMESTAMP NOT NULL,
    record_source         STRING    NOT NULL
) USING DELTA;

-- ============ SAT_PATIENT_DETAILS ============
CREATE TABLE IF NOT EXISTS dv_raw.sat_patient_details (
    patient_hk        STRING    NOT NULL,   -- PK part 1
    load_date         TIMESTAMP NOT NULL,   -- PK part 2  == SCD2 effective_from
    load_end_date     TIMESTAMP,            --            == SCD2 effective_to (NULL = current)
    hashdiff          STRING    NOT NULL,
    record_source     STRING    NOT NULL,
    birthdate         DATE,
    deathdate         DATE,
    first_name        STRING,
    last_name         STRING,
    maiden_name       STRING,
    marital_status    STRING,
    race              STRING,
    ethnicity         STRING,
    gender            STRING,
    birthplace        STRING,
    address           STRING,
    city              STRING,
    state             STRING,
    county            STRING,
    zip               STRING
) USING DELTA;
```

**Optimize for the join pattern she already knows:**
```sql
OPTIMIZE dv_raw.sat_patient_details ZORDER BY (patient_hk);
OPTIMIZE dv_raw.link_patient_encounter ZORDER BY (patient_hk, encounter_hk);
-- Or declarative, on newer DBR:
ALTER TABLE dv_raw.sat_patient_details CLUSTER BY (patient_hk);
```

**Snowflake equivalents — the differences that matter:**
```sql
-- Types
STRING              -> VARCHAR(32)          (MD5 hex) or BINARY(16) (MD5_BINARY, half the bytes)
TIMESTAMP           -> TIMESTAMP_NTZ(9)
USING DELTA         -> (omit entirely)

-- Snowflake ACCEPTS declared constraints but does NOT enforce PK/FK — metadata only,
-- used by the optimizer for join elimination. Declare them anyway:
CREATE TABLE dv_raw.hub_patient (
    patient_hk      VARCHAR(32)   NOT NULL,
    patient_bk      VARCHAR       NOT NULL,
    load_date       TIMESTAMP_NTZ NOT NULL,
    record_source   VARCHAR       NOT NULL,
    CONSTRAINT pk_hub_patient PRIMARY KEY (patient_hk) RELY
);
-- RELY tells the optimizer to trust it — enabling join elimination on unreferenced
-- hubs, a real query win in a vault. Worth naming at Oura.

-- No OPTIMIZE/ZORDER. The equivalent is:
ALTER TABLE dv_raw.sat_patient_details CLUSTER BY (patient_hk);
-- and Snowflake's automatic clustering service maintains it (and bills for it).
```

**CHECK:** In Snowflake the PK isn't enforced. Why declare it?
**EXPECTED:** With `RELY`, the optimizer trusts it and can perform **join elimination** — dropping joins to hubs whose columns aren't selected. In a vault with 8-table joins that's substantial. Optimizer metadata, not a data-quality guarantee.

### Step 3 — Staging (compute the keys once, reuse everywhere)

**PySpark — batch**
```python
from pyspark.sql import functions as F

RS  = F.lit("SYNTHEA.CSV.PATIENTS")
NOW = F.current_timestamp()

def bk(c):                       # normalize before hashing — ALWAYS
    return F.coalesce(F.upper(F.trim(F.col(c).cast("string"))), F.lit("^^"))

pat_raw = (spark.read.option("header", True)
           .csv("file:///Users/sayantaninath/Downloads/clinicalflow/output/csv/patients.csv"))

DESC = ["BIRTHDATE","DEATHDATE","FIRST","LAST","MAIDEN","MARITAL","RACE",
        "ETHNICITY","GENDER","BIRTHPLACE","ADDRESS","CITY","STATE","COUNTY","ZIP"]

stg_patient = (pat_raw
    .withColumn("patient_bk", F.col("Id"))
    .withColumn("patient_hk", F.md5(F.concat_ws("||", bk("Id"))))
    .withColumn("hashdiff",   F.md5(F.concat_ws("||", *[bk(c) for c in DESC])))
    .withColumn("load_date",  NOW)
    .withColumn("record_source", RS))

stg_patient.createOrReplaceTempView("stg_patient")
```

**Same thing in pure SQL — the alternative spelling**
```sql
CREATE OR REPLACE TEMP VIEW stg_patient AS
SELECT
    Id                                               AS patient_bk,
    md5(concat_ws('||', upper(trim(Id))))            AS patient_hk,
    md5(concat_ws('||',
        coalesce(upper(trim(BIRTHDATE)), '^^'),
        coalesce(upper(trim(DEATHDATE)), '^^'),
        coalesce(upper(trim(FIRST)),     '^^'),
        coalesce(upper(trim(LAST)),      '^^'),
        coalesce(upper(trim(MAIDEN)),    '^^'),
        coalesce(upper(trim(MARITAL)),   '^^'),
        coalesce(upper(trim(RACE)),      '^^'),
        coalesce(upper(trim(ETHNICITY)), '^^'),
        coalesce(upper(trim(GENDER)),    '^^'),
        coalesce(upper(trim(BIRTHPLACE)),'^^'),
        coalesce(upper(trim(ADDRESS)),   '^^'),
        coalesce(upper(trim(CITY)),      '^^'),
        coalesce(upper(trim(STATE)),     '^^'),
        coalesce(upper(trim(COUNTY)),    '^^'),
        coalesce(upper(trim(ZIP)),       '^^')
    ))                                               AS hashdiff,
    current_timestamp()                              AS load_date,
    'SYNTHEA.CSV.PATIENTS'                           AS record_source,
    *
FROM read_files('/path/to/patients.csv', format => 'csv', header => true);
-- Snowflake: same SELECT, source is a staged file or an external/Iceberg table.
```

**Streaming variant (Auto Loader) — note what changes and what doesn't**
```python
stg_stream = (spark.readStream.format("cloudFiles")
    .option("cloudFiles.format", "csv").option("header", True)
    .option("cloudFiles.schemaLocation", "/tmp/dv/_schema/patients")
    .load("/mnt/landing/patients/")
    .withColumn("patient_hk", F.md5(F.concat_ws("||", bk("Id"))))
    .withColumn("hashdiff",   F.md5(F.concat_ws("||", *[bk(c) for c in DESC])))
    .withColumn("load_date",  F.current_timestamp())
    .withColumn("record_source", F.lit("SYNTHEA.STREAM.PATIENTS")))
# The hashing logic is character-for-character identical to batch.
# That is the parallel-load property paying off, not a coincidence.
```

**CHECK:** The hash expressions are identical in batch and streaming. Why possible here, impossible with a surrogate sequence key?
**EXPECTED:** The hash is a pure function of the row; a sequence requires reading and incrementing shared table state, which a streaming micro-batch and a batch job cannot do concurrently without a lock and a lookup.

### Step 4 — Incremental load, table by table

**HUB — insert only keys never seen before (anti-join)**
```sql
INSERT INTO dv_raw.hub_patient
SELECT s.patient_hk, s.patient_bk, min(s.load_date), min(s.record_source)
FROM   stg_patient s
LEFT ANTI JOIN dv_raw.hub_patient h ON h.patient_hk = s.patient_hk
GROUP BY s.patient_hk, s.patient_bk;
```
```sql
-- Alternative spelling #1 — MERGE (works in Delta AND Snowflake; no LEFT ANTI JOIN in Snowflake)
MERGE INTO dv_raw.hub_patient AS h
USING (SELECT patient_hk, patient_bk,
              min(load_date) AS load_date, min(record_source) AS record_source
       FROM stg_patient GROUP BY patient_hk, patient_bk) AS s
   ON h.patient_hk = s.patient_hk
WHEN NOT MATCHED THEN INSERT (patient_hk, patient_bk, load_date, record_source)
                      VALUES (s.patient_hk, s.patient_bk, s.load_date, s.record_source);
-- Note: NO "WHEN MATCHED THEN UPDATE". Ever. That absence is the design.

-- Alternative spelling #2 — portable ANSI, if the engine lacks LEFT ANTI JOIN
INSERT INTO dv_raw.hub_patient
SELECT patient_hk, patient_bk, min(load_date), min(record_source)
FROM   stg_patient s
WHERE  NOT EXISTS (SELECT 1 FROM dv_raw.hub_patient h WHERE h.patient_hk = s.patient_hk)
GROUP BY patient_hk, patient_bk;
```

**HUB_ENCOUNTER** — same shape, sourced from `encounters.csv`, `Id` → `encounter_bk`.

**LINK — note it reads only `encounters.csv`**
```sql
CREATE OR REPLACE TEMP VIEW stg_enc AS
SELECT
    Id      AS encounter_bk,
    PATIENT AS patient_bk,
    md5(concat_ws('||', upper(trim(Id))))                                  AS encounter_hk,
    md5(concat_ws('||', upper(trim(PATIENT))))                             AS patient_hk,
    md5(concat_ws('||', upper(trim(PATIENT)), upper(trim(Id))))            AS patient_encounter_hk,
    current_timestamp()                                                    AS load_date,
    'SYNTHEA.CSV.ENCOUNTERS'                                               AS record_source
FROM read_files('/path/to/encounters.csv', format => 'csv', header => true);

INSERT INTO dv_raw.link_patient_encounter
SELECT DISTINCT s.patient_encounter_hk, s.patient_hk, s.encounter_hk, s.load_date, s.record_source
FROM   stg_enc s
LEFT ANTI JOIN dv_raw.link_patient_encounter l
       ON l.patient_encounter_hk = s.patient_encounter_hk;
```

**PySpark equivalent for the hub/link anti-join**
```python
new_hubs = (stg_patient.select("patient_hk","patient_bk","load_date","record_source")
            .dropDuplicates(["patient_hk"])
            .join(spark.table("dv_raw.hub_patient").select("patient_hk"), "patient_hk", "left_anti"))
new_hubs.write.format("delta").mode("append").saveAsTable("dv_raw.hub_patient")
# mode("append"), never mode("overwrite") — insert-only is enforced by the write mode.
```

**SATELLITE — the SCD2 step. Insert only when hashdiff differs from the current row.**
```sql
INSERT INTO dv_raw.sat_patient_details
SELECT s.patient_hk, s.load_date, CAST(NULL AS TIMESTAMP), s.hashdiff, s.record_source,
       CAST(s.BIRTHDATE AS DATE), CAST(s.DEATHDATE AS DATE),
       s.FIRST, s.LAST, s.MAIDEN, s.MARITAL, s.RACE, s.ETHNICITY, s.GENDER,
       s.BIRTHPLACE, s.ADDRESS, s.CITY, s.STATE, s.COUNTY, s.ZIP
FROM stg_patient s
LEFT JOIN (
    SELECT patient_hk, hashdiff
    FROM (SELECT patient_hk, hashdiff,
                 row_number() OVER (PARTITION BY patient_hk ORDER BY load_date DESC) rn
          FROM dv_raw.sat_patient_details)
    WHERE rn = 1
) cur ON cur.patient_hk = s.patient_hk
WHERE cur.patient_hk IS NULL          -- brand new entity
   OR cur.hashdiff <> s.hashdiff;     -- something actually changed
```
```sql
-- Snowflake alternative spelling — QUALIFY removes the subquery entirely
WITH cur AS (
  SELECT patient_hk, hashdiff
  FROM dv_raw.sat_patient_details
  QUALIFY row_number() OVER (PARTITION BY patient_hk ORDER BY load_date DESC) = 1
)
INSERT INTO dv_raw.sat_patient_details (...)
SELECT ... FROM stg_patient s
LEFT JOIN cur ON cur.patient_hk = s.patient_hk
WHERE cur.patient_hk IS NULL OR cur.hashdiff <> s.hashdiff;
-- Databricks Runtime 12.2+ supports QUALIFY too — same syntax works there.
```

**End-dating — give her BOTH options and make her choose:**
```sql
-- Option A (PURIST): never write load_end_date. Derive it in a view.
CREATE OR REPLACE VIEW dv_raw.v_sat_patient_details_scd2 AS
SELECT *,
       lead(load_date) OVER (PARTITION BY patient_hk ORDER BY load_date) AS load_end_date,
       CASE WHEN lead(load_date) OVER (PARTITION BY patient_hk ORDER BY load_date) IS NULL
            THEN TRUE ELSE FALSE END                                     AS is_current
FROM dv_raw.sat_patient_details;
-- Insert-only preserved. Cost: a window function on every single read.

-- Option B (PRAGMATIC): physically close the prior row on load.
MERGE INTO dv_raw.sat_patient_details t
USING (SELECT patient_hk, min(load_date) AS new_load_date
       FROM stg_new_versions GROUP BY patient_hk) s
   ON t.patient_hk = s.patient_hk AND t.load_end_date IS NULL
WHEN MATCHED AND t.load_date < s.new_load_date
     THEN UPDATE SET t.load_end_date = s.new_load_date;
-- Fast reads. Cost: this is an UPDATE, which technically violates insert-only.
-- Most real vaults do this anyway and document the exception.
```

**CHECK:** Option A vs B — which is *actually* Data Vault, and which would she ship?
**EXPECTED:** A is doctrinally correct (insert-only intact); B is what most production vaults do because A's read cost is paid on every query forever. Senior answer: **B, generated by the framework and documented as a deliberate deviation** — or better, skip both and let a **PIT table** carry the end-dating, giving B's read speed while keeping the satellite pure. If she reaches the PIT answer unprompted, that's a strong signal.

### Step 5 — Validate what she built

```sql
-- 1. Hub grain: must return 0
SELECT patient_hk, count(*) FROM dv_raw.hub_patient GROUP BY 1 HAVING count(*) > 1;

-- 2. Idempotency: re-run the ENTIRE Step 4 load. Counts must not move.
SELECT 'hub' t, count(*) FROM dv_raw.hub_patient
UNION ALL SELECT 'link', count(*) FROM dv_raw.link_patient_encounter
UNION ALL SELECT 'sat',  count(*) FROM dv_raw.sat_patient_details;

-- 3. Orphan links: must return 0
SELECT count(*) FROM dv_raw.link_patient_encounter l
LEFT ANTI JOIN dv_raw.hub_patient h ON h.patient_hk = l.patient_hk;

-- 4. THE SCD2 PROOF — force a change, then watch a second version appear.
--    Edit ONE patient's CITY in the source CSV, re-run staging + the satellite insert:
SELECT patient_hk, load_date, city, hashdiff
FROM   dv_raw.sat_patient_details
WHERE  patient_hk = '<the-one-she-edited>'
ORDER  BY load_date;
-- Two rows. Different hashdiff. Old city preserved. That is SCD Type 2, in a satellite.

-- 5. Rebuild her Kimball star ON TOP of the vault (the information mart)
CREATE OR REPLACE VIEW marts.dim_patient AS
SELECT h.patient_bk       AS patient_id,
       s.first_name, s.last_name, s.gender, s.birthdate, s.city, s.state,
       s.load_date        AS effective_from,          -- <- her SCD2 columns, by their Kimball names
       s.load_end_date    AS effective_to,
       s.load_end_date IS NULL AS is_current
FROM   dv_raw.hub_patient h
JOIN   dv_raw.v_sat_patient_details_scd2 s ON s.patient_hk = h.patient_hk;
```

**FINAL CHECK for the exercise:** Point at query #5. What just happened to the vocabulary?
**EXPECTED:** `load_date`/`load_end_date` got renamed to `effective_from`/`effective_to`/`is_current` — the information mart is a Type 2 dimension, and the satellite was storing it in that shape the whole time. **This is the retention hook. If she says it back in her own words, the SCD2 gap is closed.**

**Idempotency note to give her:** re-running Step 4 twice must not change any count. If it does, the anti-join/hashdiff logic is wrong — the same bug that shows up in every real vault.

---

## PART 9 — Architect interview questions with model answers

Deliver one at a time. **Let her answer first, then read the model answer.**

### Q1. "Why would you choose Data Vault over a star schema?"

"I wouldn't choose one over the other — Data Vault sits underneath a star schema, it doesn't replace it. The consumption layer is still Kimball. What I'd be choosing is whether to put a vault *between* the sources and the marts, and I'd do that for three specific reasons. First, auditability: insert-only satellites with `load_date` and `record_source` on every row mean I can prove what the warehouse believed on any past date and which system told it — in a HIPAA or SOX environment that's a requirement, not a preference. Second, source churn: raw vault applies zero business rules, so a source system being replaced or a business definition changing means I replay rules over retained history instead of re-extracting from a system that may be decommissioned. Third, parallel loading: hash keys are computed from business keys, so there's no key-lookup dependency and every hub, link, and satellite loads concurrently — which is what makes it work for a data-mesh org where domain teams load independently.

The cost is real and I'd name it: roughly 3–5× the table count, significant join depth at query time, and monotonic storage growth. So my actual criterion is: how many independently-governed sources am I integrating, and is the audit trail a legal requirement or a nice-to-have? One stable source and a nice-to-have audit trail — that's Kimball with SCD2 over an immutable raw zone, and I'd say so."

### Q2. "How does a satellite handle a changed attribute?"

"It inserts a new row — it never updates. The satellite's primary key is `(parent_hash_key, load_date)`, and change detection uses a `hashdiff`: a hash of all the descriptive columns concatenated with NULLs coalesced to a fixed token. On load I compare the incoming record's hashdiff to the hashdiff of that entity's most recent satellite row. Identical, I skip it — that's what makes the load idempotent. Different, I insert a new version with a later `load_date`, and the previous row is untouched.

Structurally this is exactly an SCD Type 2. `load_date` is `effective_from`, `load_end_date` is `effective_to`, and `load_end_date IS NULL` is `is_current`. The only difference from textbook Kimball is that strict DV2 won't `UPDATE` the prior row to close it out, so you either derive the end date with a `LEAD()` window in a view, or accept a physical end-date update as a documented deviation, or — the option I'd actually pick at scale — let a PIT table carry the end-dating so reads are fast and the satellite stays pure insert-only.

I'd also flag the design decision that comes with it: you split satellites by rate of change and by source system. If a patient's demographics change yearly but a derived risk score changes hourly, they must not share a satellite, or every score update rewrites the full demographic payload."

### Q3. "What breaks at petabyte scale?"

"Four things, in the order they bite.

**Satellite storage growth.** Insert-only plus wide rows plus high-frequency change is unbounded growth with no natural pruning. The fixes are architectural: split satellites by rate of change, split by source, and — most importantly — don't vault high-frequency telemetry at all. DV2 historizes *state*; sensor readings are already immutable *events*, so they belong in a partitioned Iceberg or Delta table the vault references by business key. Putting wearable telemetry in a satellite is the single most expensive mistake I see.

**Join depth at query time.** Reconstructing one business entity means a hub plus N satellites, each with a 'pick the version current as of date X' window function, plus the links. That's 8–15 joins for what was one star-schema query. This is what PIT and bridge tables are for — a PIT precomputes which `load_date` to use per satellite per snapshot, turning N window functions into N equi-joins; a bridge precomputes multi-link traversals. Both are disposable and rebuildable, which is the point.

**Load-time dedup cost.** Every hub, link, and satellite load is an anti-join or MERGE against a table that only grows. At petabyte scale that's the hot spot. Mitigations: cluster/Z-ORDER on the hash key, partition satellites by `load_date` so the current-row lookup prunes, and restrict the anti-join to a recent partition window rather than the whole table.

**Hash collisions and hash cost.** MD5 is 128-bit and cryptographically broken; birthday-bound collision risk becomes non-negligible in the 10^18 key range, and if any source is adversarial, deliberate collisions are trivial. SHA-256 is the safe default, but 64 bytes per key across every satellite row and join column is a genuine tax. The modern alternative on Snowflake or Databricks is to skip hashing and join on the natural business key directly — columnar compression makes it cheap, it's debuggable, and it eliminates collision risk while preserving the parallel-load property.

The one I'd raise unprompted in a HIPAA context: hashing an MRN is not de-identification. A deterministic hash of a small identifier space is brute-forceable and is still PHI. Hash keys are a join mechanism, not a privacy control."

### Q4. "We're mandating Data Vault across the platform. Thoughts?"

**(The pushback question — what separates Staff from Senior. Deliver as the closer.)**

"I'd want to agree, and there are three questions I'd need answered before I could.

**What's the automation strategy?** A hand-written vault is unmaintainable — the table count and the boilerplate are the whole reason codegen exists. On dbt that's `datavault4dbt` or `AutomateDV`; otherwise VaultSpeed or WhereScape. No generator means no vault, just a lot of copy-pasted SQL that drifts.

**Who governs business-key definitions?** Hub selection is a governance act, not a modeling act — the same conversation as a Kimball bus matrix. A healthy enterprise vault is 15–40 hubs. If we end up with 300, that tells me the business never agreed on what its concepts are and we're mirroring source tables one-to-one, which gets us all of DV2's cost and none of its integration benefit.

**What does the consumption layer look like?** Nobody queries a raw vault. If we don't have funded, owned information marts on top, we'll ship a technically correct vault no analyst can use, and it'll be abandoned in eighteen months. That's the most common way these projects die.

And I'd argue for scoping rather than a blanket mandate. DV2 earns its cost where we're integrating many independently-governed sources under a regulatory audit requirement — that's the core. For a domain with one stable source, or ML feature workloads, or event and telemetry data, it's 3–5× the cost for benefits an immutable raw zone plus SCD2 dimensions already deliver. So my recommendation would be a hybrid: vault the integration-heavy regulated core, plain Kimball everywhere else, and one set of conformed marts on top of both so consumers can't tell the difference."

---

## Session close — 60-second recall drill

Rapid-fire, no hints, record misses:

1. Four columns of a hub? → hash key, business key, load_date, record_source
2. Why no descriptors in a hub? → they change; hubs must be immutable and parallel-loadable
3. Link hash key is derived from what? → the concatenated **business keys** of the participating hubs, fixed order, fixed separator
4. **A satellite is which Kimball pattern?** → **SCD Type 2** (`load_date`=`effective_from`, `load_end_date`=`effective_to`, `load_end_date IS NULL`=`is_current`)
5. Which layer does the star schema live in? → the **information mart**, on top of the vault

**Question 4 is the one that matters.** If she misses it, re-ask at the start of the next session before anything else — that's the regression being tracked.

---

## Report after delivery

Record: whether she got the 4.0 cold-recall drill unassisted, whether Q4 in the close was clean, and whether she reached the PIT-table answer on Step 4's end-dating question without prompting.
