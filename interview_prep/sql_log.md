# SQL Practice Log (DataLemur + interview problems)

Format per entry: date · problem · pattern · final solution · what went wrong / coached fixes.

---

## 2026-07-05 — Duplicate Job Listings (DataLemur, Easy) — 20 min session

**Pattern:** Deduplication via `ROW_NUMBER()` (recurring pattern from the SQL framework — extends to "show the duplicate rows" follow-ups).

**Problem:** Count companies that posted duplicate job listings (same title + description within the same company).

**Final solution (window version):**
```sql
WITH cte_joblistings AS (
  SELECT job_id, company_id, title, description,
         ROW_NUMBER() OVER (PARTITION BY company_id, title, description
                            ORDER BY job_id DESC) AS countofjob
  FROM job_listings
)
SELECT COUNT(DISTINCT company_id) AS duplicate_companies
FROM cte_joblistings
WHERE countofjob > 1;
```

**Bugs coached (both self-corrected):**
1. First attempt partitioned by `title, description` only — missed `company_id`, so identical listings at *different* companies were wrongly flagged as duplicates. Rule: the PARTITION BY must include every column that defines "same group" in the problem statement.
2. Second attempt dropped `DISTINCT` from the outer count — a company with 3 identical listings (rn = 2, 3) or duplicates across two different titles would be counted more than once.

**Alternative (aggregate version, no window):**
```sql
SELECT COUNT(*) AS duplicate_companies
FROM (
  SELECT company_id
  FROM job_listings
  GROUP BY company_id, title, description
  HAVING COUNT(*) > 1
  GROUP BY company_id
) AS dup;
```
Same idea: `GROUP BY` the duplicate-defining columns, `HAVING COUNT(*) > 1`, then collapse to distinct companies.

**Takeaway:** window version generalizes better; aggregate version is shorter for pure counts. Watch the two classic traps: incomplete PARTITION BY, and forgetting DISTINCT when multiple duplicate rows map to one entity.
