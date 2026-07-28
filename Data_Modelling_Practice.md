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

> **The test:** pick a dimension, and ask whether SUM across it produces a number a business person would accept. Do it for *every* dimension, and **always test time separately** — time is where semi-additive measures break.

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

*Directly reusable for the Ōura Senior Data Architect loop — a data-mesh shop will ask you to model a domain.*
