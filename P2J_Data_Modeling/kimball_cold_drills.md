# Kimball Cold-Retrieval Drill Set

Built 2026-07-29. Parked — not yet run. Targets two specific gaps:

- **Gap 1 — SCD Type 2 cold recall.** Regressed 2026-07-28: placed a loyalty-tier change on the dimension correctly (the harder half) but could not name "Type 2" or the effective_from / effective_to / is_current mechanism. Re-taught same day; needs a fresh cold redo.
- **Gap 2 — Fact-table naming.** Missed 3x in one round on 2026-07-23 (FactRevenue → FactShowtime → FactPrice before landing on FactTicketSale; earlier FactCustomerValue). One clean rep since (factOrders, 2026-07-28) — these drills confirm or refute the improvement.

Carry rule she was given: **"A new fact table needs a different grain, not a later timestamp."**

## Delivery rules

- **READ ALOUD** is verbatim. **EYES ONLY** never gets spoken.
- No lead-in. Do not name the topic — the whole value is that it's cold.
- One nudge maximum per item. If the nudge doesn't land, give the answer cleanly, say "carry that one," move on. No third attempt.
- **Hard stop:** two "not sure" responses in the same block → stop the battery, close on something she got right, end the session.

## Run order & checkpoints

| Block | Items | Status | Purpose |
|---|---|---|---|
| 0 — Warm-up | D-1, D-2, D-3 | MUST-RUN | Warmest material (unfinished from 7/28). Gets her talking before the cold gaps. |
| ⛳ CHECKPOINT 1 | — | — | See below |
| 1 — Gap 1 core | SCD-1, SCD-3 | MUST-RUN | The pass/fail on SCD2 cold recall |
| ⛳ CHECKPOINT 2 | — | — | See below |
| 2 — Gap 2 core | FN-1, FN-2, FN-3 | MUST-RUN | The pass/fail on fact naming |
| ⛳ CHECKPOINT 3 | — | — | See below |
| 3 — Consolidation | SCD-2, SCD-4, C-1…C-5 | Optional if going well | Confirms retention, not a lucky hit |
| 4 — Depth | SCD-5, FN-4, FN-5, FN-6 | Optional, only if Block 3 was fluent | Breaks the "always Type 2" reflex; hardest naming traps |
| 5 — Stretch | SCD-6 | Only if she asks for more | Architect-level, Oura-relevant |

**⛳ CHECKPOINT 1** — Did she classify at least 2 of 3 correctly *and* justify with the timestamp test unprompted? If yes → Block 1. If she got D-2 wrong (called delivery a process), that's the known failure repeating; correct it, still proceed to Block 1, but expect a shorter session.

**⛳ CHECKPOINT 2 — the one that matters.** Gap 1 is CLEARED only if, on SCD-1, she said **"Type 2"** *and* described row versioning **without a nudge**:

- Named Type 2 + mechanism cold → **cleared**. Go to Block 2.
- Named the mechanism but not "Type 2" (or vice versa) → **partial**. Run SCD-3, then Block 2. Re-drill in 3–4 days.
- "Not sure" again → **regression confirmed**. Give the answer, run SCD-3 as an open-book walkthrough, then **stop the session**. Do not run Block 2 the same day.

**⛳ CHECKPOINT 3** — Gap 2 is trending clear if she named the *event* on FN-1 and FN-3 without cycling through derived measures. If she proposed 2+ wrong names before landing on any one, stop after Block 2.

---

# A) SCD drills

### SCD-1 — Name the type (must-run, first)

> **READ ALOUD:** "A sales rep, Priya, covers the Northeast region. In March she transfers to the West region. Comp analytics needs every deal she closed before March to still roll up under Northeast, and every deal after March to roll up under West. Same rep, same employee ID. How do you handle that in the warehouse?"

**EYES ONLY**

- **Expected:** SCD **Type 2** on DimSalesRep. Close out the existing row (`effective_to` = change date, `is_current = false`), insert a **new row with a new surrogate key**, `effective_from` = change date, `effective_to` = 9999-12-31, `is_current = true`. Natural key (employee ID) stays the same across both rows. The fact carries the surrogate key current at deal-close time, so history stays intact with no special query logic.
- **Bar to clear:** the words **"Type 2"** AND the row-versioning mechanism, both unprompted.
- **Likely wrong answers:** (a) "not sure" — the exact 7/28 failure; (b) a `region` column on the fact table; (c) a separate rep-history side table joined by date range; (d) versioning described correctly but can't produce the name "Type 2" — that's the *specific* half she lost, so a good description does not substitute for the name.
- **Nudge (one only):** "You've put the change on the dimension, not the fact — that's right. Now: what's this pattern called, and if I `SELECT * FROM DimSalesRep WHERE employee_id = 'Priya'`, how many rows come back and what tells them apart?"

### SCD-2 — Name the type, Type-1 bait (Block 3)

> **READ ALOUD:** "A hospital's provider dimension has a `specialty` attribute. Dr. Rao is credentialed as a cardiologist, then in June gets recredentialed as an electrophysiologist. Quality reporting has to attribute every past procedure to the specialty Dr. Rao held on the date that procedure was performed. What's your design?"

**EYES ONLY**

- **Expected:** Type 2, same mechanism. Key reasoning she must voice: the old value **was not wrong** — it was correct as of its time. That's the Type 1 vs Type 2 discriminator.
- **Likely wrong answers:** (a) Type 1 overwrite, reasoning "recredentialing is a correction"; (b) snapshotting `specialty` onto the procedure fact (defensible in some designs, but dodges the question — push back with "and if you have 400 provider attributes?"); (c) "same as the last one" without re-deriving — she pattern-matches under pressure, so make her state *why*.
- **Nudge:** "Is the old specialty **wrong**, or was it **right at the time**?"

### SCD-3 — Write the mechanism (must-run)

> **READ ALOUD:** "Customer C-1001 is a Silver loyalty member. On 15 March 2026 they hit Gold. Give me the column list for DimCustomer such that this change does not rewrite history — just the columns, name them yourself. Then tell me literally what rows exist for C-1001 the day before the change and the day after, and what the ETL did on the 15th."

**EYES ONLY**

- **Expected columns:** `customer_key` (surrogate, PK), `customer_id` (natural/business key), `loyalty_tier`, `effective_from`, `effective_to`, `is_current` (+ optional `version_number`, `row_hash`, audit timestamps).
- **Expected rows:**
  - Before: one row — key 501, C-1001, Silver, effective_from 2024-01-01, effective_to 9999-12-31, is_current = TRUE.
  - After: two rows — key 501, C-1001, Silver, effective_from 2024-01-01, **effective_to 2026-03-14** (or 03-15 exclusive — accept either if she states the convention), is_current = **FALSE**; and key 502, C-1001, **Gold**, effective_from 2026-03-15, effective_to 9999-12-31, is_current = TRUE.
  - ETL: detect change (hash/column compare vs current row) → UPDATE old row's `effective_to` + `is_current` → INSERT new row with a **new surrogate key**. Update-then-insert, never update-in-place of the attribute.
- **Likely wrong answers:** (a) single row with `previous_tier` + `current_tier` — that's Type 3, the collapse she's at risk of; (b) new row inserted but old row left `is_current = TRUE`; (c) reusing the same surrogate key for both rows — silently destroys the design, call it out hard; (d) no natural key column, so nothing ties the two rows to one customer.
- **Nudge:** "You have two rows for the same person now. What in the table tells me which one an order from January should point at — and what stops a query from double-counting them?"

### SCD-4 — The fact-side half (Block 3)

> **READ ALOUD:** "The orders fact already has two years of history. Customer C-1001 now has three rows in DimCustomer. Tonight's load brings in a new order for C-1001. How does the ETL decide which of the three rows that order points at? And separately — when finance re-runs last year's revenue-by-loyalty-tier report next week, what makes the numbers come out identical to what they saw last year?"

**EYES ONLY**

- **Part 1:** ETL looks up DimCustomer on the **natural key** where `is_current = TRUE`, takes the surrogate key; the fact stores **only that surrogate key**. For a late-arriving fact, the lookup instead uses `order_date BETWEEN effective_from AND effective_to` — bonus if she raises this unprompted, strong Meta-loop signal.
- **Part 2:** The report just joins fact → dim on the surrogate key. The fact froze the correct version at load time, so the historical tier comes back automatically. **The report needs no date logic and must not filter `is_current`.** That's the payoff, and the sentence to listen for.
- **Likely wrong answers:** (a) fact stores `customer_id` and the report joins on it — classic break, 3x fan-out or requires `is_current = 1` which silently rewrites history; (b) report does a BETWEEN range join — works, but pays at query time for something ETL already solved; push on cost; (c) confusion about which side the surrogate key lives on.
- **Nudge:** "If that report has to filter on `is_current` to get the right answer, something upstream is already broken. What?"

### SCD-5 — Type 2 is the WRONG answer (Block 4)

> **READ ALOUD:** "DimProduct has a `product_description` field. Marketing edits it constantly — typo fixes, SEO rewording, seasonal copy. Nobody ever filters or groups by it; it's tooltip text on a dashboard. But marketing does want to see the previous wording next to the new wording for one release cycle so they can compare. What do you do with that attribute?"

**EYES ONLY**

- **Expected:** **Type 1** (overwrite) for routine edits — no analytic value, nobody slices by it, versioning spawns dimension rows on cosmetic text changes. The "previous alongside current, one cycle" requirement is textbook **Type 3**: add `prior_product_description` + `description_changed_date` on the same row. Full credit = "Type 1, with a Type 3 column pair for the side-by-side." Partial = "Type 1" plus a clear statement of why Type 2 is wrong.
- **Why Type 2 is wrong — at least one of:** explodes row counts on an attribute nobody analyzes; fragments the dimension so every other attribute inherits spurious versions; Type 3 gives exactly the one prior value that was asked for, no more.
- **Likely wrong answer:** "Type 2 — always preserve history." The reflex this drill exists to break. If she says it, don't correct — ask "how many product rows do you have after a year of SEO edits?" and let her find it.
- **Nudge:** "Does anyone ever `GROUP BY` this column? And how many versions back do they actually need?"

### SCD-6 — Architect trade-off (Block 5, stretch only)

> **READ ALOUD:** "You own DimSubscriber — 40 million rows. Product wants Type 2 on six attributes. Two of them are `plan_tier` and `device_firmware_version`, and a large chunk of the base changes those every month. Marketing wants five years of point-in-time reporting. Talk me through what you'd actually build, and what you'd push back on."

**EYES ONLY** — expected coverage (3–4 is strong):

- **Row growth math, out loud.** 40M rows, two fast-churning attributes, monthly churn on a meaningful share, 60 months → hundreds of millions of rows. Type 2 on a fast-changing attribute versions the *entire row*, including the 200 attributes that didn't change.
- **The fix: mini-dimension.** Pull the rapidly-changing, low-cardinality attributes into a mini-dimension of distinct combinations; the fact carries **both** FKs — base dim key and mini-dim key. Dimension row count stops growing with churn; the "as of event time" value is captured on the fact. Bonus: naming it Type 4, or hybrid **Type 6** if they also need "report by *current* tier" alongside "tier at event time."
- **Point-in-time query cost.** Consumers range-joining `event_ts BETWEEN effective_from AND effective_to` is a non-sargable inequality join at scale. Architect answer: resolve once in ETL, store the surrogate key on the fact, consumers never range-join. Range joins are for late-arriving-fact backfill and repair only.
- **Retention decision.** Five years at full fidelity is rarely the real requirement. Interrogate it: "as of any second" or "as of month-end"? If month-end, a **monthly dimension snapshot** beyond 12–18 months is dramatically cheaper, with full-fidelity versions archived to cold storage.
- **When she'd refuse Type 2 outright:** (1) attribute changes faster than facts arrive; (2) nobody analyzes by it (Type 1); (3) source can't emit reliable change detection — no CDC, no change timestamps, no dependable deletes, so version boundaries are fiction; (4) the true requirement is "current only" and someone confused *audit trail* with *analytic history* — audit belongs in a change log, not the dimension.
- **Likely wrong answers:** re-explaining the Type 2 mechanism instead of trading off; "storage is cheap, Type 2 everything" — push with "what's the query cost, not the storage cost?"
- **Nudge:** "Of those six attributes, which one would you be embarrassed to have versioned — and if the churn doesn't go into DimSubscriber, where does it go?"

---

# B) Fact-table-naming drills

Ask each the same way so the format never leaks: **"Name the fact table and give me the grain in one sentence."** All domains new to her (avoiding Reels, ride-sharing, e-commerce, Instagram, notifications, movie theater).

### FN-1 — Utility smart meters (must-run, easiest)

> **READ ALOUD:** "A utility company runs three million smart meters. Each meter reports consumption every fifteen minutes. Both customer billing and leak detection are built on this data. Name the fact table and give me the grain in one sentence."

**EYES ONLY**
- **Correct:** `FactMeterReading` — one row per meter per 15-minute interval. Periodic measurement. `FactCustomerBill` (one row per bill line per customer per billing period) is a **legitimate second fact** — raising it is a plus, not a trap.
- **Trap:** `FactConsumption` / `FactUsage` (naming the measure in the row), `FactBilling` (jumping to the downstream rollup), `FactMeter` (dimension-shaped).
- **Diagnostic:** "Consumption is the *number in* the row. The reading is the *event that produced* the row."

### FN-2 — Hotel occupancy (must-run; derived-measure bait #1)

> **READ ALOUD:** "A hotel group's executives want occupancy rate by property, by room type, by night — plus revenue per available room. Name the fact table and give me the grain in one sentence."

**EYES ONLY**
- **Correct:** `FactRoomNight` — one row per room, per property, per night, occupied or vacant, with an occupied flag and the rate charged. Occupancy rate = occupied rows ÷ total rows. RevPAR = revenue ÷ available room-nights. **Both requested metrics are calculations over this grain, not tables.** `FactReservation` (one row per booking event) is a legitimate second fact.
- **Trap:** `FactOccupancy`, `FactOccupancyRate`, `FactRevPAR` — naming the table after the KPI on the exec's slide. The `FactRevenue` / `FactCustomerValue` failure in a new costume.
- **Diagnostic:** "A rate is a numerator over a denominator. You can't store a ratio at a grain — you store the countable thing that produces both halves."

### FN-3 — Airline on-time performance (must-run; scheduling-entity bait #1)

> **READ ALOUD:** "An airline needs to analyze on-time performance and delay causes across its whole network. Name the fact table and give me the grain in one sentence."

**EYES ONLY**
- **Correct:** `FactFlightLeg` — one row per flight leg per scheduled departure date (flight number + date + origin/destination), with scheduled and actual departure/arrival timestamps, delay minutes, and a delay-cause dimension. Accumulating-snapshot-flavored: gate departure, wheels up, wheels down, gate arrival are **columns on one row**, not four tables.
- **Traps — three available here:** (a) `FactFlightSchedule` — scheduling-entity trap, direct analogue of her `FactShowtime` miss; (b) `FactOnTimePerformance` / `FactDelay` — derived-measure trap; (c) separate `FactDeparture` + `FactArrival` — later-timestamp trap.
- **Diagnostic:** "The schedule is the *plan*; the flight operating is the *event*. And departure and arrival are two clocks on one leg, not two tables."

### FN-4 — Boutique fitness classes (Block 4; scheduling-entity bait #2)

> **READ ALOUD:** "A boutique fitness chain wants to know which classes fill up, which members no-show, and whether no-show rates justify overbooking. Name the fact table and give me the grain in one sentence."

**EYES ONLY**
- **Correct:** `FactClassBooking` — one row per member per class session, with status columns: booked / attended / no-showed / cancelled, plus booking and cancellation timestamps. Near-factless, counts only. Capacity lives on a `FactClassSession` row or a class-offering dimension — raising this is a plus.
- **Traps:** `FactClassSchedule` (scheduling entity); `FactNoShowRate` / `FactAttendanceRate` (derived measure); `FactAttendance` as a *second* table alongside `FactBooking` (later-timestamp — attended is an outcome on the booking row).
- **Diagnostic:** "Booked, attended, no-showed and cancelled are four outcomes of one booking. Same grain, so same table — as columns."

### FN-5 — Health insurance claims (Block 4; grain-below-header)

> **READ ALOUD:** "A health insurer needs to analyze cost drivers — which procedures, which providers, which members drive spend. Name the fact table and give me the grain in one sentence."

**EYES ONLY**
- **Correct:** `FactClaimLine` — one row per claim line, i.e. one procedure or service on one claim (claim ID + line number), with billed / allowed / paid / member-responsibility amounts. **Claim ID is a degenerate dimension** — she's verified on DDs, listen for it. The adjudication lifecycle (submitted → adjudicated → paid → appealed) is an accumulating snapshot of milestones, not separate facts.
- **Traps:** `FactClaimAmount` / `FactMemberCost` / `FactSpend` (derived); `FactClaim` at *header* grain — subtly wrong, can't answer "which procedures"; `FactClaimSubmitted` + `FactClaimPaid` as two tables (later-timestamp).
- **Diagnostic:** "The words 'which procedures' set the grain. That phrase put you below the claim header before you started designing."
- **Note:** header-grain is the *interesting* wrong answer. If she gives it, don't call it wrong — ask "can that table answer the first thing they asked for?" and let her drop a level herself. Oura-relevant domain, worth the extra beat.

### FN-6 — Card payments (Block 4, hardest; the carry-rule test)

> **READ ALOUD:** "A payments platform sees a card authorization at 9am. The settlement of that authorization lands at 2am the next day. And sometimes, three weeks later, a chargeback. Design the fact layer — name your tables and give me the grain of each."

**EYES ONLY**
- **Correct:** `FactPayment` as an **accumulating snapshot** — one row per payment attempt, with `auth_ts`, `capture_ts`, `settle_ts` as columns, plus status and lag measures, **updated in place** as it progresses. `FactChargeback` is defensibly a **separate transaction fact** — zero-to-many per payment, arrives weeks later, own amounts and reason codes. **That is a genuine grain difference and she must justify it that way, not by "it happens later."**
- **Trap:** three tables — `FactAuthorization` + `FactSettlement` + `FactChargeback`. The exact "later timestamp means new fact table" error, which is why this is last.
- **Diagnostic:** "Auth and settle are the same money moving through stages — one row, updated. A chargeback is a new event with its own measures and its own cardinality — its own row. **A new fact table needs a different grain, not a later timestamp.**"
- Best single item for confirming the carry rule stuck. If Block 4 gets cut for time, consider running FN-6 alone.

---

# C) Process vs dimension vs milestone — rapid fire

> **READ ALOUD (once):** "Five items. For each one tell me: business process, dimension, or a milestone inside a process — and one sentence on why. Fast, don't overthink."

| # | READ ALOUD | EYES ONLY — expected |
|---|---|---|
| C-1 | "Sales territory." | **Dimension.** Timestamp test: a territory doesn't *happen*, it *is*. Bonus: Type 2 candidate, since reps get reassigned and you need historical attribution. |
| C-2 | "A shipment clears customs." | **Milestone**, inside the shipment-fulfillment accumulating snapshot. A `customs_cleared_ts` column, not `FactCustomsClearance`. Same shape as her 7/28 "packed at warehouse" miss. |
| C-3 | "A refund is issued." | **Business process** — its own transaction fact. Different grain (zero-to-many per order, partial amounts), own measures and reason codes. Cannot collapse to a column. Contrast with C-2 out loud. |
| C-4 | "An insurance policy." | **Dimension.** Bait: it has effective and expiry dates, so it *looks* like an event. But the policy is a noun that exists over time; the policy being *issued* or *renewed* is the process. Noun vs verb. |
| C-5 | "A student enrolls in a course." | **Business process** → `FactEnrollment`, one row per student per course-section per term. "Course" and "course section offering" are the dimensions. |

**Scoring:** the mix is deliberate — 2 dimensions, 2 processes, 1 milestone — so she can't pattern-match a rhythm. If she gets C-2 right after C-1, that's real signal; C-2 is the item that failed on 7/28.

---

# D) Unfinished 7/28 items — warm-up block (run first)

> **READ ALOUD (once):** "Three quick ones. For each: is this a business process that earns its own fact table, or is it something else? And if it earns one, name it and give me the grain."

### D-1 — "A customer writes a product review."

- **Expected:** **Genuine business process.** `FactProductReview` — one row per review (customer + product + submission timestamp). Measures: star rating, helpful-vote count. Review text is a degenerate/wide attribute or lives outside the fact. Bonus: helpful-votes accumulate after the fact, so it's mildly accumulating-snapshot-shaped.
- **Trap:** `FactRating` / `FactAverageRating` (derived-measure trap in miniature); or classifying "review" as a dimension.
- **Nudge:** "Did something happen at a moment in time?"

### D-2 — "An order is delivered." ← the trap item; watch closely

- **Expected:** **Not a separate process.** A **milestone** in the order-fulfillment accumulating snapshot — a `delivered_ts` column on `FactOrderFulfillment`, alongside ordered / packed / shipped. Same grain as the order, so same row.
- **Trap:** `FactDelivery`. The 7/28 failure mode verbatim — "later timestamp" mistaken for "new fact table," plus failure to connect back to accumulating snapshots she's already passed three times.
- **Nudge:** "Same order or a different one? And if it's the same order, what's changed about the grain?"
- If she gets this right and names "accumulating snapshot" unprompted, say so explicitly — that connection is exactly what was missing on 7/28 and she should hear that it landed.

### D-3 — "A supplier restocks inventory."

- **Expected:** **Genuine business process.** `FactInventoryReceipt` — one row per receipt line, per SKU, per warehouse, per delivery. Transaction fact. Strong answer also names the sibling: `FactInventorySnapshot`, one row per SKU per warehouse per day, semi-additive on-hand quantity — a **legitimately different grain, therefore a legitimately different table.** She's verified on semi-additive facts, so this is a fair reach.
- **Trap:** `FactInventory` (ambiguous — ask "at what grain? the event or the level?"); or `FactStockLevel` as the name for the receipt event, conflating snapshot with transaction.
- **Nudge:** "Is 'how much arrived today' the same question as 'how much is on the shelf right now'?"

---

## Closing note

The single most important data point is **Checkpoint 2**: did she say "Type 2" cold, yes or no. Everything else is secondary. If the answer is no for a second time, the retention approach needs to change — spaced re-test every 2–3 days rather than one re-teach — and that's worth flagging rather than running more drills the same day.
