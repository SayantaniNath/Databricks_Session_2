# Data Modelling Practice — Method + Worked Models

Built 2026-07-28. Companion to `Meta_Data_Modeling_Prep.md/html` (Kimball theory + the six mock rounds). This document holds the **repeatable procedure** and two full worked designs.

Why it exists: the framework steps (processes → grain → dimensions → facts) were already known, but the *decision rules inside each step* weren't. These are those rules, written to be mechanical enough to run under interview pressure.

---

## Part 1 — The Method

### Step 0 — Don't draw anything yet

The most common failure in a modelling round is sketching tables before asking questions. Three questions first:

- Who consumes this, and what decisions do they make with it? (finance ≠ merchandising ≠ ops)
- What time resolution do they need — sub-day, or is daily fine?
- Roughly what scale, and batch or near-real-time?

Those three answers determine the grain, and the grain determines everything downstream.

### Step 1 — Business processes, not tables

List **verbs**. What actually *happens*? Each real business event is a candidate fact table.

> **Naming rule.** A fact table is named after *an event that happens* — never after a number you compute (`FactRevenue`, `FactCustomerValue`) and never after a thing that merely exists (`FactShowtime`, `FactProduct`).

> **The timestamp test — process vs dimension.** Does it have a timestamp of its own? An order is *placed* at 14:32. A payment is *captured* at 14:33. A customer doesn't happen at a time — a customer just *is*. Date is never a process; it's the spine every fact hangs off.

> **The "same entity, later" test — process vs milestone.** If a candidate can be phrased as *"the same order, later"*, it's a milestone and belongs as a date column on an existing fact. A genuinely new process has a **different grain**: different actor, different cardinality, or it can happen zero-to-many times independently.

**Worked contrast — why returns is a fact and packing is a column:**

| | Customer returns an item | Order is packed at warehouse |
|---|---|---|
| Times per order line | 0, 1, or many | Exactly once |
| Timing | Independent — days/weeks later | Fixed position in a sequence |
| Own measures? | Yes — refund amount, reason code | No |
| **Verdict** | **Its own fact table** | **A date column** |

> **Carry this one sentence:** a new fact table needs a *different grain*, not a *later timestamp*.

### Step 2 — Declaring the grain

Three things decide it:

1. **What is the atomic event?** Go to the lowest level the process naturally occurs at. Kimball's rule: declare the grain at the lowest atomic level available. You can always aggregate up; you can never recover detail you didn't store.
2. **What must you slice by?** Every dimension you need to filter or group by must be identifiable at the grain. If it isn't, that question becomes permanently unanswerable.
3. **The unique key test.** Name the combination of columns that makes a row unique. That combination *is* the grain. If you can't name it, you haven't declared one.

> **The asymmetry that makes the call easy.** Too coarse destroys information permanently. Too fine only costs storage. *When unsure, go finer.*

Say these three sentences out loud for every fact table:

```
"The atomic event here is ______."
"One row is uniquely identified by ______."
"That means one row per ______."
```

If sentence 2 gives you trouble, that's the signal to ask a clarifying question — not to guess.

### The three fact table types

> **The distinguishing test.** Does the thing being measured go through a *fixed, ordered set of stages, each happening at most once*? → **accumulating snapshot**. Does it happen *repeatedly and unboundedly* with no fixed sequence? → **transaction**. Does *nothing happen at all* — are you just taking a measurement on a schedule? → **periodic snapshot**.

| | Transaction | Accumulating snapshot | Periodic snapshot |
|---|---|---|---|
| **One row =** | One event, when it happens | One entity moving through a pipeline | One measurement of a state at a point in time |
| **Row lifecycle** | Insert once, never update | **Inserted then UPDATED repeatedly** as milestones land | Insert once per period, never update |
| **Grows by** | Volume of events | Number of entities (bounded) | Entities × periods (predictable) |
| **Date columns** | One | **Many** — one per milestone | One — the snapshot date |
| **Answers** | "How many / how much?" | "How long between stages? Where do things stall?" | "What was the level on that day?" |
| **Density** | Sparse — rows only when something happens | Sparse — one row per entity | **Dense** — a row even when nothing changed |

**Examples**

| Type | Examples |
|---|---|
| **Transaction** | `FactOrderLine` (item sold) · `FactReturn` · `FactRating` · `FactReelsEngagement` (like/comment/share) · `FactTicketSale` (seat booked) · ATM withdrawal · web page view |
| **Accumulating snapshot** | `FactOrderFulfillment` (cart→checkout→paid→packed→shipped→delivered) · `FactTrip` (requested→matched→arrived→started→ended) · `FactNotification` (created→sent→delivered→opened) · mortgage application (submitted→underwriting→approved→funded) · recruiting pipeline (applied→screen→onsite→offer) |
| **Periodic snapshot** | `FactInventorySnapshot` (stock per product per warehouse per day) · `FactDriverAvailability` (drivers online per zone per 5 min) · monthly account balance · daily unread-notification backlog · headcount per department per month |

> **The trap that keeps recurring:** defaulting to *transaction* because the previous question was a transaction. Re-derive from the entity's actual behaviour every time. Ask: *can this happen to the same entity twice?* If yes → transaction. If each stage happens at most once in fixed order → accumulating snapshot.

**Same domain, all three at once — e-commerce:** a sale is a *transaction* (repeats unboundedly). The order's journey to the door is an *accumulating snapshot* (fixed stages, once each). Stock on hand is a *periodic snapshot* (nothing happens — you just measure it nightly). That's why this domain is the standard prompt.

### Steps 3 & 4 — The sentence test

Write the business event as plain English with a verb:

> Who did what to what, when, where, how — and how much?

| Part of the sentence | Becomes |
|---|---|
| The **verb** | The fact table name |
| **Who / what / when / where / how** | Dimensions |
| **How much / how many** | Facts (measures) |

#### Deciding facts — two tests

**Test 1 — would you add it up?**

- SUM or AVG across rows → **fact** (`quantity`, `fare_amount`, `duration_min`)
- Filter or GROUP BY → **dimension attribute** (`shoe_size`, `age_band`, `vehicle_capacity`) — numbers, but they describe rather than measure

**Test 2 — is it true at the grain?** ← the one people fail

Put `order_total` on a line-grain fact and every 3-line order counts its total three times. Silent double-counting, and the single most common modelling bug in production. `line_revenue` belongs at line grain; `order_total` is derived by summing lines.

#### Additivity — the three kinds of measure

> **The test:** pick a dimension, and ask whether SUM across it produces a number a business person would accept. Do it for *every* dimension, and **always test time separately and last** — time is the discriminator.

- Yes for **all** dimensions including time → fully additive
- Yes for some, **No for time** → semi-additive
- No essentially everywhere → non-additive

**How to predict the answer without running the test.** Ask: is this number *NEW* at this row, *RESTATED* at this row, or *DERIVED by division*?

| | Meaning | Result |
|---|---|---|
| **New** | The event generated this quantity; it didn't exist before | Fully additive |
| **Restated** | The row reports what the total already *was* at that moment | Semi-additive |
| **Derived** | A rate, ratio, or per-unit value — a denominator is baked in | Non-additive |

**The test, run out loud**

| Measure | New / restated / derived? | Across entities | Across time | Verdict |
|---|---|---|---|---|
| `line_revenue` | **New** — this line generated ₹3,000 that didn't exist before | ✓ | ✓ | Additive |
| `duration_min` | **New** — this trip consumed 23 min no other trip consumed | ✓ | ✓ | Additive |
| `quantity_on_hand` | **Restated** — Monday says 100, Tuesday says 100; the *same* 100 units | ✓ different stock | ✗ same stock twice | Semi-additive |
| `drivers_online` | **Restated** — 40 at 18:00 and 40 at 18:05 are largely the same people | ✓ across zones | ✗ | Semi-additive |
| `unit_price` | **Derived** — revenue ÷ quantity | ✗ | ✗ | Non-additive |
| `surge_multiplier` | **Derived** — total_fare ÷ base_fare | ✗ | ✗ | Non-additive |
| `rating_value` | **Derived** — a 1–5 score, not a quantity of anything | ✗ | ✗ | Non-additive |

`quantity_on_hand` is the instructive row: it's the only one where the answer *changes* depending on which dimension you test — which is exactly what "semi" means.

**Three shortcuts that get you there in seconds**

1. **If the fact table is a periodic snapshot, its main measure is almost certainly semi-additive.** Snapshots restate a level by definition — spotting the fact type gives you the additivity for free.
2. **Name-sniffing.** Contains *rate, ratio, percent, price, score, per, avg* → non-additive. Contains *balance, on_hand, headcount, backlog, currently* → semi-additive. A count of events or money generated → additive.
3. **"Could this row's value have been true yesterday too?"** If yes, it's a level → semi-additive. Revenue of ₹3,000 belongs to *this* order and no other day. Stock of 100 units was probably also true yesterday.

**What you do about each**

- **Additive** — SUM, no thought required.
- **Semi-additive** — SUM across non-time dimensions, **LAST or AVG across time**. Define that rule explicitly in the semantic layer, because the default SUM will silently be wrong.
- **Non-additive** — ideally don't store it; store the components and compute after aggregation.

> **The standard Kimball resolution for `unit_price`:** keep it for reference, but *also* store `extended_price = unit_price × quantity`, which **is** additive. The fact table then has something summable and nobody accidentally sums the price. Same trick everywhere — alongside any non-additive measure, store the additive quantity it was derived from.

| | Fully additive | Semi-additive | Non-additive |
|---|---|---|---|
| **Rule** | SUM across *every* dimension | SUM across some dims, **never across time** | SUM is *always* meaningless |
| **Why** | Each row is an independent quantity | Each row is a *level*, and levels don't accumulate over time | It's a rate, ratio, or per-unit value |
| **Aggregate with** | SUM | SUM across non-time dims; **AVG or LAST** across time | AVG, or recompute from components |

| Kind | Examples | What breaks if you get it wrong |
|---|---|---|
| **Fully additive** | `quantity`, `line_revenue`, `refund_amount`, `fare_amount`, `tip_amount`, `trips_completed`, `online_minutes`, `watch_duration_seconds`, `engagement_count` | Nothing — these are the easy ones |
| **Semi-additive** | `quantity_on_hand` · bank `account_balance` · `drivers_online` · `headcount` · `unread_notification_count` · any "backlog" or "level" | 100 units Monday + 100 Tuesday reported as **200 units** — you own 100, twice. Sums across *products* are fine; across *days* they're nonsense |
| **Non-additive** | `unit_price` · `surge_multiplier` · `rating_value` · `conversion_rate` · `refund_rate` · `margin_pct` · temperature · heart rate | Averaging daily rates to get a monthly rate is **wrong** unless every day had identical volume |

> **The rule that saves you every time:** never store a ratio — store its numerator and denominator. Store `refunds` and `orders`, not `refund_rate`. Then the ratio is computed *after* aggregation, at whatever level is asked for, and it's correct at all of them.

**Why semi-additive is the one they probe.** It's the only kind where the *same measure* is valid on one dimension and invalid on another, so it tests whether you actually reason about the measure or just pattern-match. Periodic snapshot facts are almost always semi-additive — the two concepts travel together.

Say it this way in a round: *"`quantity_on_hand` is semi-additive — I can sum it across products and warehouses, but across time I'd take the closing value or an average, because summing daily balances would double-count stock that never moved."*

#### Deciding dimensions — four questions each

1. **Does it have attributes I'd slice by?** Yes → dimension table. No, bare identifier → **degenerate dimension**, keep as a column on the fact (`order_id`, `trip_id`).
2. **Do its attributes change, and do I care about history?** No → SCD Type 1 (overwrite). Yes → **SCD Type 2**: new row per change with `effective_from` / `effective_to` / `is_current`. Old fact rows keep pointing at the old row, so March revenue is computed against March's price.
3. **Is it shared across fact tables?** Yes → **conformed dimension**, build once. That's the bus matrix, and it's what makes "returns as % of sales" one join instead of a reconciliation project.
4. **Does it play more than one role?** `order_date` and `ship_date` both point at `DimDate` → **role-playing dimension**: one table, multiple views.

> **Shortcut for finding dimensions fast:** listen for the word *"by"*. "Revenue *by* category *by* region *by* month" — every "by" is a dimension, and it must exist at or above your grain.

### The whole recipe

1. Write the event as a sentence with a verb
2. Verb → fact table name
3. Nouns / when / where / how → dimensions
4. Numbers → candidate facts; **drop any not true at the grain**
5. Classify additivity; replace ratios with their components
6. Per dimension: attributes? → table or degenerate · history? → SCD type · shared? → conformed · multiple roles? → role-playing

Six steps, any domain, every time.

---

## Part 2 — Worked Model: E-commerce

**Step 0 assumptions:** analytics for merchandising, finance, ops. Daily reporting sufficient but order-level detail preserved. ~10M orders/year.

### Step 1 — processes → facts

| Business process | Fact table | Type |
|---|---|---|
| A customer buys an item | `FactOrderLine` | Transaction |
| An order moves cart → delivered | `FactOrderFulfillment` | Accumulating snapshot |
| A customer returns an item | `FactReturn` | Transaction |
| Stock level at a point in time | `FactInventorySnapshot` | Periodic snapshot |

`cart`, `checkout`, `payment`, `processed`, `shipped`, `delivered` all collapse into row 2 — milestones *inside* fulfillment, not four processes. All three Kimball fact types appear in one domain.

### Step 2 — grain

| Fact | Grain | Unique key |
|---|---|---|
| `FactOrderLine` | One row per product per order | `(order_id, product_id)` |
| `FactOrderFulfillment` | One row per order, updated in place | `(order_id)` |
| `FactReturn` | One row per returned item per return event | `(return_id, order_line_id)` |
| `FactInventorySnapshot` | One row per product per warehouse per day | `(product_id, warehouse_id, date_key)` |

- **Why not one row per order on `FactOrderLine`?** "Which product category drives the most revenue?" becomes permanently unanswerable — you cannot split $180 back into the shirt and the shoes.
- **Why not one row per unit?** Nothing you'd slice by differs between unit 1 and unit 2 — triple storage, zero gain. *Exception:* serialized goods (IMEIs, per-unit warranties) — units are distinguishable, per-unit is correct.
- **Why `return_id` in the key?** Someone can return 1 of 3 shirts in March and another in April. Drop it and the second overwrites the first.
- **Clarifying question worth asking:** can an order ship in multiple parcels? If yes, fulfillment grain drops to *one row per shipment* — two parcels have two `shipped_ts` values. Split shipments are the norm at scale and interviewers plant this.

### Step 3 — dimensions

`DimCustomer` (SCD2) · `DimProduct` (SCD2) · `DimDate` · `DimWarehouse` · `DimShipMethod` · `DimPromotion` · `DimReturnReason`

- **Degenerate:** `order_id`, `order_line_id`
- **Conformed:** `DimProduct`, `DimCustomer`, `DimDate` across all four facts — the bus matrix
- **SCD2 on `DimProduct`** because price and category change, and March revenue must use March's price

### Step 4 — measures

| Fact | Measures | Additivity |
|---|---|---|
| `FactOrderLine` | `quantity`, `unit_price`, `discount_amount`, `line_revenue`, `cost_of_goods` | Additive (except `unit_price` — non-additive) |
| `FactOrderFulfillment` | `cart_created_ts`, `checkout_started_ts`, `payment_captured_ts`, `order_placed_ts`, `packed_ts`, `shipped_ts`, `delivered_ts`, `hours_to_ship`, `hours_to_deliver` | Lags additive via AVG |
| `FactReturn` | `quantity_returned`, `refund_amount` | Fully additive |
| `FactInventorySnapshot` | `quantity_on_hand` | **Semi-additive** — sum across products, never across days |

The fulfillment table answers "where do customers abandon?" and "is our delivery SLA slipping?"

### The Staff layer

- Partition `FactOrderLine` by order date, cluster on product — dominant query pattern
- `FactOrderFulfillment` is **mutable** → MERGE upserts + defined late-arrival window. Others append-only
- DQ gates: every order line joins to a valid product; refund never exceeds original line revenue
- Retention: raw cart events are huge and low-value after ~90 days — raise with the team, don't decide silently

---

## Part 3 — Worked Model: Ride-sharing

**Step 0 assumptions:** ops (supply/demand), finance (revenue + driver payouts), product (funnel, cancellations). **Sub-day resolution required** — surge and dispatch analysis are meaningless at daily grain. ~100M trips/year.

### Step 1 — the sentence

> *"Driver D picked up Rider R in Zone Z on Jan 14 at 18:40 in an UberXL, drove 8.2 km for 23 minutes, fare ₹420."*

Verb → `FactTrip`. Nouns → `DimDriver`, `DimRider`, `DimZone`, `DimDate`, `DimTime`, `DimVehicleType`. Numbers → `distance_km`, `duration_min`, `fare_amount`.

| Business process | Fact table | Type |
|---|---|---|
| A rider requests a ride, run to completion or cancellation | `FactTrip` | Accumulating snapshot |
| A driver's device emits a GPS ping | `FactDriverLocation` | Event stream |
| A driver goes online and works a session | `FactDriverShift` | Accumulating snapshot |
| A rating is submitted after a trip | `FactRating` | Transaction |
| Driver availability per zone per interval | `FactDriverAvailability` | Periodic snapshot |

**The split that earns the round:** `FactDriverLocation` must be *separate* from `FactTrip` — a frequency mismatch, not a preference. GPS pings arrive per-second per-driver whether or not a trip exists; trips arrive per-trip. Forcing them together means either exploding trip rows or losing location resolution. Most candidates miss this.

### Step 2 — grain

| Fact | Grain | Unique key |
|---|---|---|
| `FactTrip` | One row per trip request — *including ones that never became trips* | `(trip_request_id)` |
| `FactDriverLocation` | One row per driver per GPS ping | `(driver_id, ping_ts)` |
| `FactDriverShift` | One row per driver per online session | `(driver_id, shift_start_ts)` |
| `FactRating` | One row per trip **per direction** | `(trip_id, rating_direction)` |
| `FactDriverAvailability` | One row per zone per 5-minute interval | `(zone_id, interval_ts)` |

- **Why `FactTrip` is grained on the *request*, not the completed trip:** cancellations are the business question. Grain on completed trips and you permanently lose "what % of requests never find a driver, and in which zones?" — the key supply/demand metric. Cancelled requests carry null milestones and a `trip_status`.
- **Why `rating_direction` is in the key:** riders rate drivers and drivers rate riders. Same trip, two ratings. Leave it out and one silently overwrites the other.

### Step 3 — dimensions

`DimDriver` (SCD2) · `DimRider` (SCD2) · `DimVehicle` (SCD2) · `DimVehicleType` · `DimDate` · `DimTime` · `DimZone` · `DimCancellationReason` · `DimPaymentMethod`

- **`DimTime` separate from `DimDate`** — time-of-day is the primary surge dimension. Rush hour vs 3am *is* the analysis
- **Role-playing:** `DimZone` plays `pickup_zone` and `dropoff_zone`; `DimDate` plays request/start/end
- **Degenerate:** `trip_id`, `trip_request_id`
- **Conformed:** `DimDriver`, `DimZone`, `DimDate` across trips, shifts, ratings, availability — lets you ask "driver earnings per online hour by zone" in one join
- **SCD2 on `DimDriver`** — vehicle changes, tier changes, city transfers

### Step 4 — measures

| Fact | Measures | Notes |
|---|---|---|
| `FactTrip` | Milestones: `requested_ts`, `matched_ts`, `driver_arrived_ts`, `started_ts`, `ended_ts`, `cancelled_ts`. Measures: `distance_km`, `duration_min`, `wait_time_sec`, `base_fare`, `surge_multiplier`, `total_fare`, `driver_payout`, `platform_commission`, `tip_amount` | Fares additive; **`surge_multiplier` non-additive** — store `base_fare` and `total_fare`, derive it |
| `FactDriverLocation` | `lat`, `lon`, `speed_kmh`, `heading` | Coordinates not additive — positional |
| `FactDriverShift` | `online_minutes`, `idle_minutes`, `trips_completed`, `gross_earnings` | Fully additive. Powers driver utilisation |
| `FactRating` | `rating_value` (1–5) | Non-additive — average, never sum |
| `FactDriverAvailability` | `drivers_online`, `drivers_on_trip`, `open_requests` | **Semi-additive** — sum across zones, never across intervals |

### The Staff layer

- **Partition `FactTrip` by request date, cluster by pickup zone** — date is the dominant filter, zone the dominant group-by; zone also bounds hotspot size
- **`FactDriverLocation` does not belong in the warehouse.** Per-second pings across hundreds of thousands of drivers is a time-series problem. Raw pings → object storage, short retention (7–30 days); land *zone-minute rollups* in the warehouse
- **`FactTrip` and `FactDriverShift` are mutable** → MERGE upserts, late-arrival window, idempotent reprocessing. `FactRating` and `FactDriverLocation` append-only
- **DQ gates:** completed trips need non-null fare and end timestamp; `driver_payout + platform_commission` reconciles to `total_fare`; `ended_ts > started_ts`
- **SLA:** ops dashboards need trip data within ~15 min → streaming ingestion; finance aggregates daily batch. Different SLAs on one table is a legitimate design conversation

---

## Part 4 — Self-check before any modelling round

- [ ] Did I ask the three Step 0 questions before drawing anything?
- [ ] Is every fact table named after a **verb / event**?
- [ ] Can I state each grain as one sentence, and name its unique key?
- [ ] Did I check every candidate process against *"same entity, later?"* before giving it its own table?
- [ ] Is every measure **true at the grain** — no order totals on line-grain facts?
- [ ] Did I classify each measure additive / semi-additive / non-additive, and replace ratios with components?
- [ ] Did I name the conformed dimensions and the SCD type on anything that changes?
- [ ] Did I add the Staff layer — partitioning, mutability, data quality, SLA, retention?

---

## Part 5 — Concept Q&A (2026-07-29)

Questions asked during the session, with the answers as delivered. These are the *why* behind the method in Part 1.

### Q1. Why is normalization required for OLTP data models?

Because OLTP is optimized for **writes**, and redundancy is what makes writes go wrong.

In a transactional system the dominant operation is a small, concurrent, single-entity change — one customer updates an address, one order is placed. If a customer's address is copied into 400 order rows, that one logical change becomes 400 physical writes, and any row you miss is now a contradiction the database cannot detect. Normalization stores each fact **in exactly one place**, so a change is one write and correctness is structural rather than dependent on application code doing it right.

Two supporting reasons that matter operationally:

- **Concurrency.** Narrower tables mean narrower row locks and less contention. A wide denormalized row makes unrelated transactions fight over the same page.
- **Enforcement.** Foreign keys, unique constraints and NOT NULL only work when a fact has one home. Denormalize and enforcement moves into application code, where it silently rots.

> **The architect layer.** Normalization is a **write-time optimization, paid for at read time in joins.** That's a reasonable trade for OLTP, where reads are point lookups by key, not aggregations across millions of rows. OLAP inverts every assumption — data is historical and effectively immutable, so update anomalies cannot occur, and reads are wide scans where joins are the dominant cost. Same data, opposite optimization target, because the workload is opposite.

Practical stopping point: **3NF**. BCNF and beyond buy diminishing correctness for real complexity. In high-scale OLTP teams *do* selectively denormalize back — a cached counter, a materialized read model — but as a deliberate, owned exception with a defined refresh path, not as the default.

### Q2. The three anomalies, worked

One badly designed table — everything crammed into orders:

| order_id | customer_id | cust_name | cust_email | product_id | product_name | price |
|---|---|---|---|---|---|---|
| 1001 | C-1 | Priya | priya@x.com | P-9 | Keyboard | 2500 |
| 1002 | C-1 | Priya | priya@x.com | P-7 | Mouse | 800 |
| 1003 | C-2 | Arjun | arjun@x.com | P-9 | Keyboard | 2500 |

Priya's email appears twice; the keyboard's name and price appear twice. Neither fact is *about an order* — they're about a customer and a product. That's the design error, and all three anomalies fall out of it.

| Anomaly | What happens here | Normalized fix |
|---|---|---|
| **Update** | Priya changes her email. It lives in rows 1001 and 1002. Update only 1001 and the table now says Priya has two different emails — with no way for the DB to flag it, since those are just two rows that happen to disagree. | Email lives once, in `customers`. One update, no possible disagreement. |
| **Insert** | You want to add product P-12 (a monitor) before anyone buys it. The only table is orders, so you'd invent a fake order or insert a row with `order_id` NULL. The product exists in the real world but the schema has nowhere to put it. Same for a registered customer who hasn't ordered. | `products` and `customers` are their own tables. A product exists independently of whether it ever sold. |
| **Delete** | Arjun cancels order 1003, his only order. Delete the row and Arjun is gone entirely — name, email, the fact he's a customer. If that had been the last P-9 order, the keyboard's price goes with it. | Deleting from `orders` touches only the order. Arjun stays in `customers`. |

> **The pattern under all three:** each happens because a fact about *entity A* is stored inside a row about *entity B*. Normalization is the discipline of giving every fact exactly one home, so its lifecycle is independent of anything else's.

### Q3. In what case does denormalization help in OLAP?

Start with the bridge case — `price` on an order row. It looks like redundancy but it's **defensible, arguably required**: it's the price *at the time of sale*. Normalize it away and read the current price from `products`, and a price change silently rewrites the revenue of every historical order. The value is a snapshot of a moment, not a live copy, so it genuinely belongs to the order.

That's the whole principle in one column: **duplicating immutable, historical values is safe, because every anomaly requires the value to change.**

**The worked example.** Normalized OLTP side:

```
orders → order_lines → products → categories → departments
                    ↘ customers → cities → states → countries
```

Analyst question: *"total revenue by product category by state, last 3 years."* Normalized, that's a 7-table join over hundreds of millions of order lines. Every join is a shuffle, and none carry business value — they exist only because normalization scattered the attributes.

Denormalized into a star:

```
FactSales (500M rows)
  date_key, product_key, customer_key, store_key,
  quantity, revenue, discount

DimProduct (50K rows)
  product_key, product_name, category, department, brand, supplier
       ↑ category and department REPEATED on every product row

DimCustomer (2M rows)
  customer_key, name, city, state, country, segment
       ↑ state and country REPEATED on every customer row
```

Same query is now a 3-table join, and the dimensions are small enough to broadcast — the difference between a broadcast hash join and a series of shuffles.

**Why the anomalies don't apply:**

- **Update?** `category = 'Peripherals'` is duplicated across thousands of rows, but nobody UPDATEs a dimension in place — a category change is a Type 2 insert or a controlled full reload. One write path, owned by ETL, not thousands of concurrent application writes.
- **Insert?** Doesn't arise. Dimensions load independently of facts — a product can have zero sales.
- **Delete?** Warehouses don't delete. That's the point of the historical record.

> **The architect layer.** Denormalize the *dimensions*, never the *grain*. Flattening product hierarchy into DimProduct is free. Pre-aggregating FactSales to daily totals to "make it faster" destroys everything below that grain — that's a mistake, not a trade-off.

### Q4. Should you snowflake `state`/`country` out of a 2M-row DimCustomer?

**No — not for storage.** Size is the right axis but the threshold matters: `state` and `country` are ~20 bytes per row, so 2M × 20 ≈ 40 MB before columnar compression crushes repeated strings like 'California' to almost nothing. Against a 500M-row fact table that's a rounding error, and you've added a join to every geography query forever.

The real test is the **ratio** — dimension size relative to the fact table — and the **width of what's actually repeated**. Two short strings on 2M rows never justifies it. Fifty columns of address, demographic and firmographic text on 200M rows might.

**What would actually justify a DimGeography** — none of which is row count:

1. **It's conformed.** DimCustomer, DimStore and DimSupplier all carry geography, so you're maintaining the same hierarchy three times and they will drift. One shared table is a *governance* win. Strongest argument by far.
2. **The hierarchy has its own attributes and lifecycle** — population, timezone, sales region, tax jurisdiction — with its own owner and refresh cadence.
3. **The repeated block is genuinely wide**, not two columns.

> **The reusable rule:** snowflake for *governance and conformance*, essentially never for *storage*. Storage is the argument everyone reaches for and it's almost always the weakest one.

### Q5. What is an outrigger dimension?

A dimension table that joins to **another dimension**, not directly to the fact.

```
FactSales → DimCustomer → DimGeography
                 ↑              ↑
          joins to fact    joins to DimCustomer, not the fact
```

`DimCustomer` carries a `geography_key`; `DimGeography` holds the full hierarchy — city, state, country, region, timezone, tax jurisdiction.

**Outrigger vs snowflake.** Snowflaking is systematic: normalize the whole hierarchy out and *remove* the attributes from the primary dimension. An outrigger is targeted and additive — you **keep** the common attributes denormalized on `DimCustomer` (`state`, `country` stay right there for the 90% query) *and* add the key for cases needing the full hierarchy. Fast path preserved, shared reference data available. It's the answer that refuses the star-vs-snowflake binary.

**When it earns its place:**

- The hierarchy is **shared across several dimensions** and would otherwise be maintained multiple times.
- The secondary table has its own **attributes and refresh cadence**, owned by someone else.
- A **date attribute inside a dimension** needs real date semantics — `DimProduct.introduction_date_key → DimDate` lets you ask "products introduced in Q3 of a fiscal year" without reimplementing the fiscal calendar.

> **Kimball's position, worth quoting:** outriggers are permitted but should be used *sparingly*. Every one adds a join and makes the model harder for BI tools and analysts to navigate. Five outriggers means you've snowflaked by accident.

---

## Part 6 — The conceptual-model formula (2026-07-29)

### The sentence parse

> **"A `<who>` `<does what>` to a `<what>` at a `<where>`, on a `<when>`, via a `<how>`, because of `<why>` — for `<how much>`."**

Every part of speech maps to exactly one structure:

| Question | Grammatical role | Becomes |
|---|---|---|
| **Does what** | the **verb** | the **fact table name** |
| **Who** | actor noun | dimension (`DimCustomer`, `DimDriver`) |
| **What** | object noun | dimension (`DimProduct`, `DimAccount`) |
| **Where** | location noun | dimension (`DimStore`, `DimZone`) |
| **When** | time | `DimDate` + `DimTime` — never a process, always the spine |
| **How** | method/channel noun | dimension (`DimPaymentMethod`, `DimDevice`) |
| **To whom** | second actor | second dimension role, or role-playing dimension |
| **Why** | reason noun | dimension (`DimCancellationReason`) |
| **How much / how many** | the **numbers** | **measures** on the fact |

Worked: *"A **customer** **purchases** a **product** at a **store** on **2026-07-29** via **credit card** for ₹2,500."* → `FactSale`; dimensions Customer, Product, Store, Date, PaymentMethod; measure `sale_amount`.

**Four rules that make it mechanical:**

1. **The verb is the fact table name — always.** If the name isn't verb-derived, it's a measure (`FactRevenue`) or a noun (`FactShowtime`). Reread the sentence, take the verb.
2. **The grain is the sentence made singular and precise.** Not "customers buy products" but *"one row per product per order."* If you can't say it with the word "one" in it, you don't have a grain.
3. **A noun becomes a dimension only if it has attributes you'd filter or group by.** A bare identifier with nothing hanging off it is a **degenerate dimension** — stays on the fact, gets no table.
4. **A number is a measure only if it's true at the grain.** Order total on a line-grain fact double-counts on every aggregation. Ratios: store numerator and denominator, because ratios don't sum.

**Three questions the sentence can't answer** — the shape comes from the parse, the correctness from these:

- **Does this repeat, or happen once?** Repeatable → transaction fact. Fixed ordered stages, once each → **accumulating snapshot** (milestones become columns, not tables). Measured at intervals → **periodic snapshot**.
- **Does any dimension attribute change over time, and does history matter?** → SCD type.
- **Is this the same entity later, or a genuinely different grain?** → *a new fact table needs a different grain, not a later timestamp.*

### Layer boundaries — where most people lose the round

A conceptual model has **no attributes, no keys, no datatypes, no fact/dimension labels.** Entities and relationships in business language, readable by a stakeholder. The moment you write `customer_key BIGINT` you've left the conceptual layer.

| Layer | Contains | Audience |
|---|---|---|
| **Conceptual** | Entities, relationships, cardinality. Business nouns and verbs. | Business stakeholders |
| **Logical** | Attributes, keys, normalization or star structure. Platform-agnostic. | Data teams |
| **Physical** | Datatypes, partitioning, clustering, indexes, file format. | The engine |

Interviewers ask for conceptual specifically to see whether you can *stay* there.

### The six-step procedure

1. **Capture decisions, not data.** Who consumes this, and what decision do they make? Finance, merchandising and ops want three different models of the same business.
2. **List the verbs.** Every real business event. Filter with the timestamp test.
3. **List the nouns.** Things the business talks about across *multiple* processes. A noun in one process only is usually not a core entity.
4. **Draw relationships, name every one with a verb.** `Customer ——places——< Order` tells you something; an unnamed line tells you nothing. Naming forces you to know what the relationship is.
5. **Constrain the size — 10–20 boxes.** At 60 you're modeling tables, not concepts.
6. **Validate by narration.** Trace each Step-1 business question as a path through the diagram, out loud. No path → something's missing. A box on no path → it doesn't belong.

### The artifact differs by target

**OLTP** → an **ER diagram**: entities, named relationships, crow's-foot cardinality. Normalization comes later, at the logical layer.

**Analytics** → a **bus matrix**, and this is the point most candidates miss: *the conceptual model of a warehouse **is** the bus matrix.* Rows are the verbs, columns are the nouns, checkmarks are the relationships. Shared columns are the conformed dimensions, visible at a glance — the artifact that makes a data-mesh conversation possible, since it shows which domains must agree on what.

### Where the formula breaks

- **Graph domains** (social networks, fraud rings, supply-chain traversal) — the *relationship* is the primary object. ER modeling inverts badly; use a property graph.
- **Document/hierarchical** (clinical notes, nested catalogs, event payloads) — the shape is a tree. Forcing it into boxes destroys the nesting that carries meaning.
- **Continuous time-series** (sensor telemetry, wearable readings) — no meaningful entity; the grain is a continuous measurement stream. Lives outside the dimensional model, referenced by business key.

> Saying "this domain doesn't fit the formula, and here's why" is a stronger signal than forcing every domain into a star.

---

## Part 7 — Worked Model: Ride-sharing, conceptual → logical → physical (2026-07-29)

Supersedes the thinner Part 3 treatment. Same facts and dimensions where those were right; adds the layer progression and the physical design.

### CONCEPTUAL

**Step 1 — consumers and decisions**

| Consumer | Decisions | Implication |
|---|---|---|
| Marketplace ops | Where to incentivize drivers, why requests go unfilled | Needs *unfilled* requests, not just completed trips |
| Finance | Revenue, commission, payouts, tax by jurisdiction | Money at legal-entity and city grain |
| Pricing | Surge multipliers by zone and time | Zone-interval supply/demand |
| Driver ops | Utilization, earnings, churn | Online time, not just trip time |
| Trust & safety | Rating patterns, incident follow-up | Both rating directions |

The first row shapes everything: **ops needs failed requests**, which forces the trip grain onto the *request*, not the completed ride.

**Step 2 — the verbs**

*Genuine processes:* rider requests a ride · driver goes online/offline · payment is charged · driver is paid out · rating is submitted · surge is priced for a zone-interval

*Not processes — milestones on the trip:* driver matched · driver arrived · trip started · trip ended · trip cancelled

> "Driver arrived" is the same trip, later — a timestamp column, not a fact table. The carry rule doing its work.

**Step 3 — the nouns:** Rider · Driver · Vehicle · Zone · City/Market · Payment Method · Promotion · Cancellation Reason · Vehicle Class · Date · Time

**Step 4 — relationships, every line named**

```
Rider ──requests──< Trip >──fulfilled by── Driver ──operates──< Vehicle
                      │                        │
              originates in                 works
                      │                        │
                    Zone ──belongs to── City   └──< Shift

Trip ──settled by──< Payment ──uses── Payment Method
Trip ──receives──< Rating
Zone ──priced by──< Surge Interval
```

**Step 5 — the bus matrix**

| Process ↓ / Dimension → | Date | Time | Rider | Driver | Vehicle | Zone | City | Pay Method | Reason |
|---|---|---|---|---|---|---|---|---|---|
| **Ride requested** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Payment charged** | ✓ | ✓ | ✓ | | | | ✓ | ✓ | |
| **Driver paid out** | ✓ | | | ✓ | | | ✓ | | |
| **Rating submitted** | ✓ | | ✓ | ✓ | | | | | |
| **Driver shift** | ✓ | ✓ | | ✓ | ✓ | ✓ | ✓ | | |
| **Zone priced** | ✓ | ✓ | | | | ✓ | ✓ | | |

Conformed dimensions fall out visually: **Date, Driver, Zone, City** span nearly everything — the four needing central governance, and in a data-mesh org the cross-domain contract.

### LOGICAL

| Fact | Grain (one row per…) | Type | Why |
|---|---|---|---|
| `FactTripRequest` | **request** — filled or not | Accumulating snapshot | Grain on completed trips permanently loses "% of requests unfilled, by zone" — ops' primary metric |
| `FactPayment` | payment **event** per trip | Transaction | Zero-to-many per trip: charge, refund, tip, promo credit, split fare |
| `FactDriverPayout` | payout **line** per driver per period | Transaction | Weekly settlement, different actor, different timing |
| `FactRating` | trip **per direction** | Transaction | Rider rates driver *and* driver rates rider — leave direction out of the key and one silently overwrites the other |
| `FactDriverShift` | driver **online session** | Accumulating snapshot | Utilization denominator; cannot be computed from trips |
| `FactZoneInterval` | zone **per 5-min interval** | Periodic snapshot | Supply/demand state for pricing |

> **Why `FactPayment` is separate but "driver arrived" is not** — the test both times is *cardinality*, not chronology. A payment happens 0/1/many times per trip and carries its own measures. An arrival happens exactly once, in a fixed position, with no measures. Different grain → different table; later timestamp → column.

**`FactTripRequest` detail**

```
Keys        request_id (DD), rider_key, driver_key, vehicle_key,
            pickup_zone_key, dropoff_zone_key, city_key,
            request_date_key, request_time_key, cancellation_reason_key,
            promotion_key, vehicle_class_key
Milestones  requested_ts, matched_ts, driver_arrived_ts,
            started_ts, ended_ts, cancelled_ts
Measures    wait_time_sec, time_to_match_sec, distance_km, duration_min,
            base_fare, surge_multiplier, total_fare,
            driver_payout, platform_commission, tip_amount, promo_discount
Status      trip_status, cancelled_by
```

- **`surge_multiplier` is non-additive.** Store `base_fare` and `total_fare`, derive it. The average of ratios is not the ratio of averages.
- **Unmatched requests carry NULL driver_key** → point at a "Not Assigned" dimension row, not NULL, so joins don't silently drop your most important rows.

**Dimensions**

| Dimension | SCD | Note |
|---|---|---|
| `DimDriver` | **Type 2** | Tier, city, status, vehicle change over time |
| `DimRider` | **Type 2** | Segment and city change; loyalty tier at trip time matters |
| `DimVehicle` | **Type 2** | Ownership and class change |
| `DimZone` | **Type 2** | Zone boundaries get redrawn — under-modeled real problem; silently breaks YoY comparison unless versioned |
| `DimCity` | Type 1 | Effectively static |
| `DimVehicleClass` | Type 1 | UberX / XL / Black |
| `DimPaymentMethod` | Type 1 | |
| `DimCancellationReason` | Type 1 | |
| `DimPromotion` | **Type 2** | Terms change |
| `DimDate` / `DimTime` | static | |

**Role-playing:** `DimZone` plays pickup/dropoff; `DimDate` plays request/start/end. **Degenerate:** `request_id`, `trip_id`, `payment_id`. **`DimTime` separate from `DimDate`** because time-of-day *is* the analysis — rush hour vs 3am is the entire surge question.

### PHYSICAL

**First decision: what does not go in the warehouse.**

Driver GPS pings — hundreds of thousands of drivers at 1-second resolution — do not belong in the dimensional model. Billions of rows/day of positional data nobody aggregates.

```
Raw pings → Kafka → object storage, Iceberg/Delta
            partitioned by (event_date, hour), 7–30 day retention
Rollups   → zone-minute aggregates → FactZoneInterval in the warehouse
```

Naming this unprompted is the strongest signal in a ride-share design round — same reasoning as wearable telemetry at Ōura.

**Databricks / Delta**

```sql
CREATE TABLE gold.fact_trip_request (
  request_id            STRING    NOT NULL,
  rider_key             BIGINT    NOT NULL,
  driver_key            BIGINT,
  pickup_zone_key       BIGINT    NOT NULL,
  dropoff_zone_key      BIGINT,
  request_date_key      INT       NOT NULL,
  requested_ts          TIMESTAMP NOT NULL,   -- UTC
  requested_ts_local    TIMESTAMP,            -- city-local
  matched_ts            TIMESTAMP,
  driver_arrived_ts     TIMESTAMP,
  started_ts            TIMESTAMP,
  ended_ts              TIMESTAMP,
  cancelled_ts          TIMESTAMP,
  trip_status           STRING    NOT NULL,
  distance_km           DECIMAL(8,3),
  base_fare             DECIMAL(12,2),        -- never FLOAT
  surge_multiplier      DECIMAL(4,2),
  total_fare            DECIMAL(12,2),
  driver_payout         DECIMAL(12,2),
  platform_commission   DECIMAL(12,2),
  currency_code         STRING    NOT NULL
)
USING DELTA
PARTITIONED BY (request_date_key)
CLUSTER BY (pickup_zone_key, city_key);
```

- **`DECIMAL`, never `FLOAT`, for money.** Floating-point money fails reconciliation — payouts and commission won't sum to fare. Caught in audits; interviewers ask.
- **UTC plus city-local timestamps.** A 2am local trip three timezones away lands on the wrong date in UTC and quietly corrupts every daily metric. Store both, derive `date_key` from local.
- **Partition on date, cluster on zone** — date is the dominant filter, zone the dominant group-by, and zone bounds hotspot size.
- **`FactTripRequest` is mutable** — a request lands, then milestones fill in over minutes → `MERGE` upserts, late-arrival window, idempotent reprocessing. `FactRating` and `FactPayment` are append-only.

**Snowflake equivalent**

```sql
CREATE TABLE gold.fact_trip_request (
  request_id          VARCHAR       NOT NULL,
  rider_key           NUMBER(38,0)  NOT NULL,
  base_fare           NUMBER(12,2),
  requested_ts        TIMESTAMP_NTZ NOT NULL,
  CONSTRAINT pk_ftr PRIMARY KEY (request_id) RELY
)
CLUSTER BY (request_date_key, pickup_zone_key);
```

No explicit partitioning — micro-partitions are automatic and `CLUSTER BY` is a maintained background service you pay for. Constraints aren't enforced, but `RELY` enables optimizer join elimination. CDC is `Streams + Tasks` rather than Delta CDF.

**Ingestion and SLA** — different consumers, different freshness, one table:

| Consumer | Freshness | Path |
|---|---|---|
| Ops dashboards | ~2–15 min | Kafka → Structured Streaming → Delta MERGE |
| Pricing | ~1–5 min | Zone-interval rollups from the stream |
| Finance | Daily, reconciled | Batch T+1, after settlement closes |

**Data quality gates**

- Completed trips must have non-null `ended_ts` and `total_fare`
- `driver_payout + platform_commission + promo_discount` reconciles to `total_fare`
- `ended_ts > started_ts > matched_ts > requested_ts` — monotonic milestones
- Every `pickup_zone_key` resolves to a live `DimZone` version
- Cancelled trips must carry a `cancellation_reason_key`

> **The 30-second summary:** grain on the *request* so unfilled demand survives · milestones as columns not tables · payments split out on cardinality · GPS telemetry outside the warehouse entirely · money in DECIMAL with dual-timezone timestamps.

---

*Directly reusable for the Ōura Senior Data Architect loop — a data-mesh shop will ask you to model a domain.*
