# SQL Advanced — Window Functions, Percentiles, and the Approach Framework

**Created:** 2026-05-27

**Purpose:** Reference for advanced SQL interview problems — built from working through the Razorpay "Churning High-Value Customers" problem and the follow-up discussion on NTILE / RANK / PERCENT_RANK / CUME_DIST / PERCENTILE_CONT.

**Use this when:** Practicing DataLemur weekend slots; stuck on an advanced SQL problem and need to remember the framework; picking between NTILE, RANK, PERCENT_RANK, etc.

* * *

## Part 1 — The 5-step framework for advanced SQL

Apply this to every advanced problem. Once it's muscle memory, 15-min problems become mechanical.

### Step 1. Identify the grain of the answer

Read the expected output. Each row represents what entity? That's your final grain.

In the Razorpay problem: **one row per at-risk high-value customer.** Final grain = `customer_id`.

### Step 2. Identify the grain of each intermediate fact

List the facts you need and what grain each lives at. Every grain change = a new CTE or a window function.

Fact| Grain  
---|---  
total_spend (lifetime)| per customer  
spend per month| per (customer, month)  
is top-25% spender?| per customer  
latest month vs prior months| per (customer, month) → then split  
avg of prior months| per customer (aggregated from monthly)  
  
### Step 3. Apply row filters as early as possible

`status = 'success'` and similar belong in the _first_ CTE so every downstream CTE inherits clean data.

### Step 4. Decompose into CTEs — one logical concept per CTE

If you can't name the CTE in 2–3 words, you don't understand it yet. CTE names map to concepts.

### Step 5. Compute derived columns LAST

Percentages, tiers, formatting belong in the **final SELECT** , not in a CTE. You can't filter on a window-computed column at the same query level anyway.

* * *

## Part 2 — The 5 patterns that show up in 80% of advanced problems

Pattern| Trigger words| Tool  
---|---|---  
Top X% / top N per group| "top 25%", "top 5 per category", quartile, decile| NTILE, ROW_NUMBER, RANK, PERCENTILE_CONT  
Most recent / previous| "latest", "prior", "last", "previous"| ROW_NUMBER ORDER BY date DESC, LAG  
Compare X to its own average| churn, anomaly, drop%, growth%| window AVG vs row, or split with conditional aggregation (CASE inside SUM/AVG)  
Bucket into tiers| risk, severity, segments, labels| CASE WHEN ... THEN  
Only successful / active rows| almost every real problem| Row filter in earliest CTE  
  
* * *

## Part 3 — The Razorpay problem (worked example)

### Problem summary

Identify high-value customers (top 25% spenders) who are at risk of churning (latest month's spend < 50% of their average prior-month spend). Return drop% and a risk tier.

### Grain analysis

  * **Final grain:** per customer
  * **Intermediate grains:** per (customer, month) for monthly aggregation; per customer for total and percentile



### CTE plan (4 CTEs because 4 grain changes)

  1. `monthly_spend` — per (customer, month), success-only
  2. `high_value_customers` — per customer, total + NTILE(4) quartile
  3. `labeled_months` — per (customer, month), with ROW_NUMBER to tag "latest"
  4. `customer_summary` — back to per customer, split latest vs prior with conditional aggregation



### Full query
    
    
    WITH monthly_spend AS (
      SELECT
        customer_id,
        DATE_TRUNC('month', txn_date) AS month,
        SUM(amount) AS month_total
      FROM transactions
      WHERE status = 'success'
      GROUP BY customer_id, DATE_TRUNC('month', txn_date)
    ),
    
    high_value_customers AS (
      SELECT
        customer_id,
        SUM(month_total) AS total_spend,
        NTILE(4) OVER (ORDER BY SUM(month_total) DESC) AS quartile
      FROM monthly_spend
      GROUP BY customer_id
    ),
    
    labeled_months AS (
      SELECT
        customer_id,
        month,
        month_total,
        ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY month DESC) AS rn
      FROM monthly_spend
    ),
    
    customer_summary AS (
      SELECT
        customer_id,
        SUM(CASE WHEN rn = 1 THEN month_total END) AS latest_month_spend,
        AVG(CASE WHEN rn > 1 THEN month_total END) AS avg_monthly_spend
      FROM labeled_months
      GROUP BY customer_id
    )
    
    SELECT
      cs.customer_id,
      bc.customer_name,
      hv.total_spend,
      ROUND(cs.avg_monthly_spend, 2)         AS avg_monthly_spend,
      cs.latest_month_spend,
      ROUND((1 - cs.latest_month_spend / cs.avg_monthly_spend) * 100, 1) AS spend_drop_pct,
      CASE
        WHEN (1 - cs.latest_month_spend / cs.avg_monthly_spend) * 100 > 75 THEN 'Critical'
        WHEN (1 - cs.latest_month_spend / cs.avg_monthly_spend) * 100 BETWEEN 50 AND 75 THEN 'High'
      END AS risk_tier
    FROM customer_summary cs
    JOIN high_value_customers hv ON hv.customer_id = cs.customer_id
    JOIN bank_customers bc       ON bc.customer_id = cs.customer_id
    WHERE hv.quartile = 1                                       -- top 25% (DESC order)
      AND cs.latest_month_spend < 0.5 * cs.avg_monthly_spend    -- at-risk
    ORDER BY spend_drop_pct DESC;

### avg_monthly_spend = all months EXCEPT latest

The problem explicitly excludes the latest month from the average. Otherwise the baseline would be diluted by the very month you're trying to flag.

The split happens in `customer_summary`:
    
    
    SUM(CASE WHEN rn = 1 THEN month_total END) AS latest_month_spend,   -- rn=1: latest
    AVG(CASE WHEN rn > 1 THEN month_total END) AS avg_monthly_spend     -- rn>1: priors

`rn` was assigned by ROW_NUMBER in the previous CTE — `ORDER BY month DESC` so the most recent month gets rn=1.

* * *

## Part 4 — Understanding the drop% formula
    
    
    ROUND((1 - latest_month_spend / avg_monthly_spend) * 100, 1)

**Plain English:** "What percentage of normal spend has disappeared this month."

### Step-by-step (Priya: latest=5000, avg=30000)

Step| Calculation| Result| Meaning  
---|---|---|---  
1| 5000 / 30000| 0.1667| Fraction of normal she's still spending (17%)  
2| 1 - 0.1667| 0.8333| Fraction NOT spending anymore (83%)  
3| × 100| 83.33| Convert decimal to percentage  
4| ROUND(_, 1)| 83.3| Final answer, 1 decimal place  
  
### Equivalent forms (algebraically identical)
    
    
    (1 - latest/avg) * 100        ← the form in the problem
    (avg - latest) / avg * 100    ← "missing amount as % of normal"
    ((avg - latest) * 100) / avg  ← same, parenthesized differently

### Edge-case sanity check

latest| avg| drop%| Reading  
---|---|---|---  
0| 30000| 100.0| Spent nothing → 100% drop  
15000| 30000| 50.0| Spent half → 50% drop  
30000| 30000| 0.0| Spent normal → 0% drop  
45000| 30000| -50.0| Spent 50% more → negative drop (growth)  
5000| 30000| 83.3| Priya's row  
  
**Trick to validate any percentage formula:** plug in `0`, `half`, `equal`, `double`. If all four read correctly, the formula is right. 

### Same shape used in many other problems

  * **Churn / drop:** `1 - new/old`
  * **Growth:** `new/old - 1`
  * **% of total:** `part/whole * 100`
  * **Conversion rate:** `success / attempts * 100`
  * **Discount applied:** `1 - sale_price/list_price`



* * *

## Part 5 — Why ROW_NUMBER, not LAG?

The problem hint mentions LAG, but LAG fits **pairwise** comparisons (this row vs. the row right before it). Razorpay needs **this row vs. an aggregate of many other rows** — that's not pairwise.

Question shape| Right tool  
---|---  
"Latest vs. the one before it"| `LAG()`  
"Latest vs. average of all priors"| `ROW_NUMBER` to tag the latest, then conditional aggregation  
"Each row vs. running average"| window `AVG() OVER (ORDER BY date)`  
  
**LAG-flavored alternative (only useful if the problem was about month-over-month):**
    
    
    SELECT
      customer_id,
      month,
      month_total AS current_spend,
      LAG(month_total) OVER (PARTITION BY customer_id ORDER BY month) AS prev_spend
    FROM monthly_spend;

This gives current + previous side-by-side. But to compare against an **average** of all priors, you'd need to combine with a window AVG anyway — at which point ROW_NUMBER + conditional aggregation is cleaner.

* * *

## Part 6 — Ranking & bucketing functions compared

For data `[80, 90, 90, 100]` ordered ASC:

Function| Output| Use when  
---|---|---  
`ROW_NUMBER()`| 1, 2, 3, 4| Sequential position; ties broken arbitrarily  
`RANK()`| 1, 2, 2, 4| Position; ties same rank; gaps after ties  
`DENSE_RANK()`| 1, 2, 2, 3| Position; ties same rank; no gaps  
`NTILE(2)`| 1, 1, 2, 2| Bucket number (here: top half vs bottom half)  
`PERCENT_RANK()`| 0.00, 0.33, 0.33, 1.00| Relative position 0–1  
`CUME_DIST()`| 0.25, 0.75, 0.75, 1.00| Fraction at-or-below  
  
### Key distinction — PERCENT_RANK vs CUME_DIST

  * `PERCENT_RANK` = `(rank - 1) / (n - 1)` → "fraction strictly ranked below me"
  * `CUME_DIST` = `rank / n` → "fraction at-or-below me" (inclusive)



PERCENT_RANK anchors the smallest at 0; CUME_DIST never gives 0 (smallest gets 1/n).

* * *

## Part 7 — Decision table

Question| Tool  
---|---  
Top X% with evenly-sized buckets, interview-clean code| `NTILE(100/X)`  
Top X% with exact threshold| `PERCENT_RANK` (ASC, `>= 1 - X/100`)  
"Better than X% of others"| `PERCENT_RANK` directly  
"In the bottom X% cumulative"| `CUME_DIST`  
Top N rows (not percent)| `ROW_NUMBER` or `RANK`  
Exact percentile value (the threshold itself, not row filter)| `PERCENTILE_CONT(0.X) WITHIN GROUP (ORDER BY col)`  
  
* * *

## Part 8 — Worked queries for each row of the decision table

Consistent example dataset for all six so you can compare mentally:
    
    
    -- customer_spend(customer_id, customer_name, total_spend)
    -- 10 customers with spends: 1000, 2000, 3000, ... up to 10000

### 8.1 — `NTILE(100/X)` for top X%

**Question:** "Give me the top 25% of customers by spend."
    
    
    WITH ranked AS (
      SELECT
        customer_id,
        customer_name,
        total_spend,
        NTILE(4) OVER (ORDER BY total_spend DESC) AS quartile
      FROM customer_spend
    )
    SELECT customer_id, customer_name, total_spend
    FROM ranked
    WHERE quartile = 1;

Bucket 1 (DESC order) = top 25%. For top 10% → `NTILE(10) = 1`. For top 5% → `NTILE(20) = 1`.

### 8.2 — `PERCENT_RANK` for exact threshold

**Question:** "Give me the top 25% — exactly 25%, not the approximate bucketing NTILE gives."
    
    
    WITH ranked AS (
      SELECT
        customer_id,
        customer_name,
        total_spend,
        PERCENT_RANK() OVER (ORDER BY total_spend) AS pr
      FROM customer_spend
    )
    SELECT customer_id, customer_name, total_spend
    FROM ranked
    WHERE pr >= 0.75;   -- top 25%

`pr >= 0.75` = "above the 75th percentile" → top 25%. For top 10% → `pr >= 0.90`.

### 8.3 — `PERCENT_RANK` directly for "better than X% of others"

**Question:** "For each customer, what percentage of others did they outspend? For UI copy."
    
    
    SELECT
      customer_id,
      customer_name,
      total_spend,
      ROUND(PERCENT_RANK() OVER (ORDER BY total_spend) * 100, 0) AS beat_pct_of_customers
    FROM customer_spend
    ORDER BY total_spend DESC;

**How the calculation works** (Priya, spend = 9000, rank 9 of 10 ASC):

Step| Calc| Result  
---|---|---  
1\. PERCENT_RANK| (9-1) / (10-1) = 8/9| 0.8889  
2\. × 100| convert to percent| 88.89  
3\. ROUND(_, 0)| round to whole number| **89**  
  
Reading: "Priya outspent 89% of other customers." Drop the number into copy: _"You spent more than 89% of our customers this year."_

Edge cases:

  * Lowest customer (rank 1) → (1-1)/9 = 0 → **0** (beat nobody)
  * Highest customer (rank 10) → (10-1)/9 = 1.0 → **100** (beat everyone)



#### How rank is assigned inside PERCENT_RANK

PERCENT_RANK uses the same logic as `RANK()`. With `ORDER BY total_spend ASC` on our 10 customers:

total_spend| rank| PERCENT_RANK| × 100  
---|---|---|---  
1000| 1| 0/9 = 0.000| 0  
2000| 2| 1/9 = 0.111| 11  
3000| 3| 2/9 = 0.222| 22  
4000| 4| 3/9 = 0.333| 33  
5000| 5| 4/9 = 0.444| 44  
6000| 6| 5/9 = 0.556| 56  
7000| 7| 6/9 = 0.667| 67  
8000| 8| 7/9 = 0.778| 78  
9000 ← Priya| 9| 8/9 = 0.889| **89**  
10000| 10| 9/9 = 1.000| 100  
  
**Direction trap:** `ORDER BY ASC` → smallest = rank 1, largest gets PERCENT_RANK = 1. `ORDER BY DESC` flips both. Always read the direction before reading the value. 

#### Ties behave like RANK (gap after)

For `[1000, 2000, 2000, 3000]` ordered ASC:

value| rank| PERCENT_RANK  
---|---|---  
1000| 1| 0/3 = 0.00  
2000| 2| 1/3 = 0.33  
2000| 2| 1/3 = 0.33 (tied — same value)  
3000| **4** (rank jumps past 3)| 3/3 = 1.00  
  
### 8.4 — `CUME_DIST` for "bottom X% cumulative"

**Question:** "Give me the bottom 25% — those whose spend is at-or-below the 25th percentile."
    
    
    WITH ranked AS (
      SELECT
        customer_id,
        customer_name,
        total_spend,
        CUME_DIST() OVER (ORDER BY total_spend) AS cd
      FROM customer_spend
    )
    SELECT customer_id, customer_name, total_spend
    FROM ranked
    WHERE cd <= 0.25;   -- bottom 25%

CUME_DIST is **inclusive** (counts the row itself). For "bottom 10% — likely first to churn" → `WHERE cd <= 0.10`.

### 8.5 — `ROW_NUMBER` or `RANK` for top N rows

#### A. Exactly 5 rows, ties broken arbitrarily
    
    
    WITH ranked AS (
      SELECT
        customer_id,
        customer_name,
        total_spend,
        ROW_NUMBER() OVER (ORDER BY total_spend DESC) AS rn
      FROM customer_spend
    )
    SELECT customer_id, customer_name, total_spend
    FROM ranked
    WHERE rn <= 5;

#### B. Top 5 _positions_ , include all ties
    
    
    WITH ranked AS (
      SELECT
        customer_id,
        customer_name,
        total_spend,
        RANK() OVER (ORDER BY total_spend DESC) AS rk
      FROM customer_spend
    )
    SELECT customer_id, customer_name, total_spend
    FROM ranked
    WHERE rk <= 5;

#### C. Top N per group — top 3 per segment (very common pattern)
    
    
    WITH ranked AS (
      SELECT
        bc.segment,
        cs.customer_id,
        cs.customer_name,
        cs.total_spend,
        ROW_NUMBER() OVER (PARTITION BY bc.segment ORDER BY cs.total_spend DESC) AS rn
      FROM customer_spend cs
      JOIN bank_customers bc USING (customer_id)
    )
    SELECT segment, customer_id, customer_name, total_spend
    FROM ranked
    WHERE rn <= 3;

`PARTITION BY segment` resets the counter within each group. This is _the_ "top N per group" pattern.

### 8.6 — `PERCENTILE_CONT` for the threshold _value_

**Question:** "What's the spend amount at the 75th percentile? The dollar value of the cutoff, not which customers."
    
    
    SELECT
      PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY total_spend) AS p75_threshold
    FROM customer_spend;

Returns a single number, e.g. `7750.00`.

**Common combo — use it inside a filter for "top X%" with exact semantics:**
    
    
    SELECT customer_id, customer_name, total_spend
    FROM customer_spend
    WHERE total_spend >= (
      SELECT PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY total_spend)
      FROM customer_spend
    );

**Variant:** `PERCENTILE_DISC(0.75)` returns an actual value that exists in the data (no interpolation). Use `_DISC` when you need a real row's value (e.g., median order amount in an even-count table).

* * *

## Part 9 — Side-by-side comparison on same data

For 10 customers spending `[1000, 2000, ..., 10000]`, here's what each tool returns for "top 25%":

Method| Filter| Rows returned| Why  
---|---|---|---  
NTILE(4)| `quartile = 1` (DESC)| 3 rows (10000, 9000, 8000)| NTILE distributes 10 rows as 3,3,2,2 — top bucket has 3  
PERCENT_RANK| `pr >= 0.75`| 3 rows (10000, 9000, 8000)| pr=0.778, 0.889, 1.000 qualify  
PERCENTILE_CONT| `>= P75` (where P75=7750)| 3 rows (10000, 9000, 8000)| Three customers exceed threshold  
ROW_NUMBER ≤ 2| top 2 hard cap| 2 rows (10000, 9000)| No percent involved  
  
**On evenly-divisible data they line up. On uneven row counts and ties, they diverge — that's where picking the right tool matters.**

* * *

## Part 10 — Practice protocol

  1. Read the problem **once** , then close the tab.
  2. Sketch grain on paper — final grain + intermediate grains.
  3. **Name your CTEs before writing them.** If you can't name it, you don't understand it.
  4. Write each CTE in isolation. Mentally test on the sample data before composing.
  5. Compose the final query.
  6. **Time-box advanced problems at 20 min.** If stuck, peek at the hint, close it, try again. Read the official solution only after a real attempt.



* * *

## Related references

  * `~/Downloads/Databricks_DEA_Learning_Resources.html` — Databricks-specific resources
  * `~/Downloads/Recruiter_Call_Prep_Databricks_SDE_20260527.html` — Recruiter call prep
  * DataLemur — `datalemur.com` — weekend SQL slot in your learning plan


