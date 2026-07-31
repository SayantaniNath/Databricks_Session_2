# Project Interview Prep Guide

Sayantani Nath  ·  Prepared May 2026  ·  For: Senior DE / AI Data Engineer interviews

### Contents

  1. Project 1 — AI Job Application Agent
  2. Project 2 — FinFlow Financial Data Platform
  3. General Interview Tips for Both Projects



## PROJECT 1 — AI Job Application Agent

### What Is It (The One-Liner)

A Python automation pipeline that scrapes live job postings from LinkedIn and Indeed, scores and ranks them against your resume using keyword matching, filters out visa-restricted roles, and auto-fills ATS application forms using browser automation. 

### The Full Pipeline (E2E)

LinkedIn / Indeed APIs    ↓ (via jobspy library — scrapes structured job data)   
job_matcher.py — Score + Filter    ↓ keyword match against resume skills    ↓ location filter (SF Bay Area + US Remote)    ↓ visa restriction filter (removes green card / clearance only roles)    ↓ EAD-friendly signal detected   
Ranked CSV output → job_matches_YYYYMMDD.csv    ↓ (you review top matches)   
agent_apply.py — Auto-fill ATS Forms    ↓ opens real Chrome via Playwright    ↓ scans form fields (input, textarea)    ↓ matches field labels → profile.yaml answers    ↓ fills name, email, phone, LinkedIn, GitHub, work auth, location    ↓ uploads resume PDF automatically    ↓ stops — you review and click Submit yourself 

### The Two Core Files — What Each Does

#### 1\. job_matcher.py

  * **Input:** Scrapes LinkedIn + Indeed via the `jobspy` library
  * **Scoring:** Matches each job description against ~35 resume keywords (SQL, Kafka, Snowflake, dimensional modeling etc.). Score = % of keywords found × multiplier, capped at 100
  * **Location filter:** Two modes — `remote_only` (explicit remote only) and `sf_relocated` (SF Bay Area + major US cities + remote)
  * **Visa filter:** Scans description for ~25 phrases like "US citizens only", "green card only", "security clearance required", "FedRAMP" — removes these jobs entirely
  * **EAD signal:** Flags jobs that explicitly mention "EAD", "work authorization", "L2", "no sponsorship required" as ✅ friendly
  * **Output:** Ranked CSV with match score, title, company, salary, apply URL, matched keywords



#### 2\. agent_apply.py

  * **Input:** A job application URL (ATS page like Greenhouse, Lever, Ashby)
  * **How it works:** Opens a real Chrome window (not headless) using Playwright. Scans all visible form fields. For each field, combines the label, placeholder, aria-label, field name and nearby text into one string ("signal"), then matches against keyword rules
  * **Smart matching:** Uses word-boundary regex matching — so "state" matches "state" field but not inside "United States". Handles combobox dropdowns (React ATSes) separately — clicks, types, waits for dropdown, selects option
  * **What it fills automatically:** First name, last name, email, phone, LinkedIn, GitHub, portfolio, city, state, country, school, degree, current company, current title, years of experience, work authorization (Yes/No), sponsorship required (No)
  * **File uploads:** Detects `input[type=file]` fields and uploads resume PDF automatically
  * **What it does NOT do:** Never clicks Submit — you always review and submit yourself. Intentional design decision for safety



### Why You Built It (The "Why")

Each job application has 20-40 form fields that are identical across companies — name, email, phone, LinkedIn, work authorization, relocation willingness. Filling these manually 30-50 times a month is pure repetitive work with no thinking involved. I built this to eliminate that repetition entirely so I could focus my time on the parts that actually need human judgment: reading the job description, deciding whether to apply, and tailoring my answers to open-ended questions. 

The visa filter was added after wasting time on several roles that turned out to require US citizenship or clearance — things an L2 EAD holder cannot have. The matcher catches these before they even reach the shortlist. 

### Design Decisions You Can Defend

  * **Why jobspy?** It's the only Python library that scrapes LinkedIn + Indeed simultaneously and returns structured data (title, company, location, salary, description, is_remote) without needing API keys for basic usage. Saves 2 separate API integrations.
  * **Why Playwright over Selenium?** Playwright handles modern React ATS pages better — it has proper async support, built-in waiting strategies, and better handling of shadow DOM and dynamic renders. Greenhouse and Lever are both React SPAs.
  * **Why word-boundary regex for field matching?** Simple substring matching caused bugs — "state" matched inside "United States", filling the state field with "Yes" (from the work auth rule). Word boundaries prevent this.
  * **Why not auto-submit?** Safety. A wrong submission can't be undone — wrong salary expectation, wrong answer to a screening question. The human stays in the loop for the final decision.
  * **Why headless=False?** You need to see what's happening in real time. If a form doesn't load or a captcha appears, you need to intervene immediately.
  * **Why two search modes (remote_only vs sf_relocated)?** LinkedIn often tags jobs as is_remote=True when they're actually "remote at HQ city" — hybrid in disguise. remote_only mode requires explicit "remote" in the location string to avoid these false positives.



### What It Can't Do Yet (Be Honest)

  * Dropdown/select fields (job type, gender, ethnicity, race) — these are handled separately or manually
  * LinkedIn Easy Apply (different mechanism, separate build needed)
  * Free-text questions like "Why do you want to work here?" — needs LLM integration (planned)
  * Remote filter is still somewhat imprecise — some hybrid roles slip through



### Interview Q&A

Q: Walk me through how this pipeline works end to end.

I run job_matcher.py which scrapes LinkedIn and Indeed for 20+ data engineering job titles simultaneously. For each job it finds, it scores it against my resume keywords — things like "dimensional modeling", "Kafka", "Snowflake", "data governance". It also filters out any job that requires US citizenship or security clearance, since I'm on an L2 EAD. The output is a ranked CSV. I then pick a job from the list, pass its application URL to agent_apply.py, which opens Chrome, reads all the form fields, matches them to my profile using keyword rules, and auto-fills everything it can. I review the filled form, handle anything it missed, and click Submit myself.

Q: Why didn't you just use the LinkedIn API?

LinkedIn's official API is extremely restrictive — it's not available for individual developers for job search use cases. The jobspy library uses web scraping under the hood, which gives me structured access to job data across both LinkedIn and Indeed from a single call. The trade-off is it can break if the sites change their HTML, but for a personal tool that's an acceptable risk.

Q: How does the form field matching work exactly?

For each visible input field on the page, I collect everything I can about what it's asking — the label text, placeholder, aria-label, field name attribute, and nearby heading text — and concatenate it into one lowercase string I call the "signal". Then I match that signal against a list of keyword rules using word-boundary regex. The first matching rule fills the field with the corresponding value from my profile YAML. Word-boundary matching was important — a plain substring match caused "state" to match inside "United States", which then filled the state field with a Yes/No work auth answer.

Q: What tech stack did you use and why those choices?

Python for the core logic — it's the standard for data automation work. jobspy for scraping because it handles both LinkedIn and Indeed in one call with structured output. Playwright for browser automation because modern ATS platforms like Greenhouse and Lever are React SPAs — they render forms client-side and Playwright handles that much better than Selenium. YAML for the profile config because it's human-readable and easy to update without touching code.

Q: What would you build next if you had more time?

Three things. First, LLM-powered answers for open-ended questions — "why do you want to work here" type fields. Second, LinkedIn Easy Apply support since that's where most quick applications happen. Third, a proper tracking dashboard instead of a CSV — something that shows application status, callback rate by company type, and whether the visa filter is catching the right things.

* * *

## PROJECT 2 — FinFlow Financial Data Platform

**Honesty boundary:** Be clear about what's fully working vs what's in progress. The ingestion layer is working. The Pandas analysis is solid. The dbt models exist. PySpark on the full dataset and Kafka streaming are in progress. 

### What Is It (The One-Liner)

A financial data engineering platform that ingests real-time cryptocurrency and stock prices from public APIs, stores them in a date-partitioned JSONL format, and enables downstream analysis using Pandas and dbt — designed to demonstrate the full data engineering lifecycle on real market data. 

### The Full Pipeline (E2E)

CoinGecko REST API (free, no key required)    ↓ HTTP GET every 60 seconds    ↓ fetches price, market_cap, 24h_change for 6 cryptocurrencies   
crypto_producer.py — Normalize + Store    ↓ flattens nested JSON {"bitcoin": {"usd": ...}} → flat records    ↓ adds UTC timestamp, source field    ↓ appends to date-partitioned JSONL: data/raw/crypto/2026-05-27.jsonl    ↓ optional: publishes to Kafka topic (USE_KAFKA=true)   
JSONL files (partitioned by date)    ↓   
Pandas analysis (practice_pandas_*.py)    ↓ pd.read_json(lines=True) to load JSONL    ↓ groupby, agg, sort, boolean filtering, map/apply    ↓ answered: which coin moved most, which hour had peak volume, etc.   
dbt models (in /dbt/models/)    ↓ stg_crypto_prices.sql — staging layer, type casting, renaming    ↓ fact_price_movements.sql — price movement facts    ↓ agg_daily_summary.sql — daily aggregates mart 

### The Core Files — What Each Does

#### crypto_producer.py (ingestion)

  * Hits CoinGecko's `/simple/price` endpoint with 6 coin IDs and fields: usd, usd_market_cap, usd_24h_change, usd_24h_vol
  * Response is nested: `{"bitcoin": {"usd": 67432, "usd_market_cap": 1.3T, ...}}`
  * `normalize()` function flattens this into a list of flat dicts — one dict per coin
  * Each record gets: coin_id, price_usd, market_cap_usd, change_24h_pct, volume_24h_usd, fetched_at (UTC ISO timestamp), source="coingecko"
  * Records are written in JSONL format (one JSON object per line) using append mode
  * Files are date-partitioned: `data/raw/crypto/YYYY-MM-DD.jsonl` — so each day has its own file
  * Retry logic handles CoinGecko rate limits (429 errors) and network timeouts gracefully
  * Kafka publish is optional — controlled by `USE_KAFKA=true` environment variable



#### Pandas Analysis (practice files)

**What you actually did from scratch (no peeking):**

  * Load JSONL: `pd.read_json("data/raw/crypto/2026-05-26.jsonl", lines=True)`
  * Which coin had the highest price? `df.loc[df["price_usd"].idxmax(), "coin_id"]`
  * Filter only coins with positive 24h change: `df[df["change_24h_pct"] > 0]`
  * Average price per coin across days: `df.groupby("coin_id")["price_usd"].mean()`
  * Sort by market cap descending: `df.sort_values("market_cap_usd", ascending=False)`
  * Map change to label: `df["change_label"] = df["change_24h_pct"].map(lambda x: "up" if x > 0 else "down")`
  * Multi-aggregation: `df.groupby("coin_id").agg({"price_usd": ["mean", "max"], "volume_24h_usd": "sum"})`



#### dbt Models

  * **stg_crypto_prices.sql:** Staging model — selects from raw source, casts types, renames columns to standard names, filters bad rows
  * **fact_price_movements.sql:** Fact table — price and volume metrics per coin per timestamp, references staging model
  * **agg_daily_summary.sql:** Mart layer — daily aggregates: avg price, max price, total volume, count of records per coin per day
  * **schema.yml:** Column-level documentation and tests (not_null, unique, accepted_values)



### Why You Built It (The "Why")

I wanted to learn data engineering concepts — ingestion, normalization, storage patterns, transformation — on real data rather than toy datasets. Financial market data was a deliberate choice: it's high-frequency, has clear schema, has business-meaningful analysis questions (which coin moved most, what's the volume pattern by hour), and naturally demonstrates why streaming/batch ingestion patterns exist. 

The date-partitioned JSONL storage pattern mirrors how production data lakes work — Parquet on S3 is the production version, JSONL on disk is the local prototype of the same concept. The dbt layer adds the transformation discipline that separates raw data from clean analytical models. 

### Design Decisions You Can Defend

  * **Why JSONL over CSV?** JSONL is append-friendly — each line is a complete record. CSV requires loading the whole file to append. JSONL also handles nested data naturally and is the standard format for streaming output.
  * **Why date-partitioned files?** Same reason Hive and Spark partition by date — you never need to scan all history to answer "what happened today". It also makes file management simple: each day's data is isolated.
  * **Why not a database?** For a local prototype, flat files are faster to iterate on than standing up Postgres or SQLite. The dbt layer adds structure on top of the raw files — it models the transformation logic that would apply regardless of the underlying storage.
  * **Why CoinGecko?** Free public API, no key required for basic usage, well-documented, and returns rich financial data (price, market cap, 24h change, volume) in one call.
  * **Why UTC timestamps?** All timestamps are stored in UTC and converted to ISO 8601 format. Financial data comes from global markets — using local time would make cross-timezone analysis ambiguous.



### What's In Progress (Be Transparent)

  * **PySpark processing:** The practice_pyspark_lesson1.py file exists — PySpark analysis of FinFlow data is in progress as I learn Spark
  * **Kafka streaming:** The producer has optional Kafka publish built in — standing up a local Kafka broker and connecting the consumer is next
  * **Stock producer:** stock_producer.py exists and follows the same pattern as crypto_producer.py — different API, same normalization and storage shape



### Interview Q&A

Q: Walk me through FinFlow end to end.

FinFlow is a financial data platform I built to learn data engineering hands-on. The ingestion layer has a Python producer that hits CoinGecko's REST API every 60 seconds, normalizes the nested JSON response into flat records, and writes them in JSONL format to date-partitioned files — so each day's data lives in its own file, which mirrors how production data lakes partition by date. On top of the raw files I have dbt models — a staging layer that cleans and standardizes the data, a fact table for price movements, and a daily aggregate mart. I've been using the FinFlow data to practice Pandas — groupby, aggregation, boolean filtering, map and apply — on real financial data instead of synthetic datasets.

Q: Why JSONL and not a database?

For a local prototype, JSONL is append-friendly — I can write one record per line without loading the whole file. It's also the native output format for streaming systems, so it mirrors what Kafka consumers would write in production. The date partitioning pattern is the same concept as Parquet partitioning on S3 — just smaller scale. The dbt transformation logic works the same regardless of whether the underlying storage is flat files or a warehouse.

Q: What does your dbt model structure look like?

Three layers. Staging — stg_crypto_prices selects from the raw source, casts types, renames columns to clean names, and filters bad rows. This is the only layer that touches raw data. Second layer is a fact table — fact_price_movements contains the price, volume, and 24h change metrics per coin per timestamp, referencing the staging model. Third is the mart layer — agg_daily_summary aggregates to daily grain: average price, max price, total volume, and record count per coin per day. The schema.yml adds column documentation and dbt tests — not_null on coin_id and timestamp, accepted_values for the source field.

Q: How would you productionize this?

Four changes. First, swap local JSONL files for S3 with date-partitioned Parquet — same concept, production storage. Second, run Kafka as the streaming layer so the producer publishes to a topic and consumers can react in real time rather than batch reading files. Third, replace the manual Python script with an Airflow DAG so ingestion is scheduled, retried on failure, and observable. Fourth, point dbt at a warehouse — Snowflake or Databricks — instead of local files, so the models run at scale with proper compute. The transformation logic and dbt model structure would stay exactly the same.

Q: What's the hardest bug you hit building this?

The UTC timestamp issue. Early on I used Python's datetime.now() instead of datetime.now(timezone.utc), which meant timestamps were in my local timezone. When I loaded the JSONL and tried to sort by time or do time-based groupby, the records were out of order because the timezone information was inconsistent across days when my system clock changed. Switching to datetime.now(timezone.utc) and converting to ISO 8601 string fixed it. It was a small bug but it reinforced why financial data should always use UTC — markets operate across timezones and local time is ambiguous.

Q: Why financial data specifically?

A few reasons. It's real — every number I'm working with is an actual market price, not randomly generated. It has natural business questions that make analysis meaningful — which coin is most volatile, what's the volume pattern, how does 24h change correlate with market cap. It's high-frequency enough to make streaming patterns relevant, not just batch. And the domain connects to my Citi background, so I can draw parallels to real production patterns I've seen at scale.

* * *

## GENERAL INTERVIEW TIPS FOR BOTH PROJECTS

### The Golden Rule — Own Your Boundaries

If an interviewer asks about something you haven't built yet — say so directly. "That part is next in my roadmap — right now I have X working, and the plan for Y is Z." Interviewers at top-tier companies respect intellectual honesty. They will catch you if you bluff, and it ends the interview. 

### How to Handle "Show Me the Code"

If asked to walk through code live:

  * **job_matcher.py:** You can walk through `score_job()`, `is_relevant_location()`, `is_visa_restricted()`, and `process_jobs()` — explain what each does and why
  * **agent_apply.py:** You can walk through `field_signal()`, `matches_keyword()`, `fill_field()`, and the main `run()` loop — explain the matching logic
  * **crypto_producer.py:** You can walk through the full file — the API call, `normalize()`, the JSONL write, the retry loop
  * **Pandas practice files:** You can write equivalent operations from scratch — you've done this 4 lessons in a row from blank



### The Story Arc (Use This for "Tell Me About a Project")

  1. **Problem:** What repetitive/painful thing were you solving?
  2. **Architecture decision:** What was the key design choice you made and why?
  3. **One technical challenge:** What broke and how did you fix it?
  4. **Result:** What does it do now, what does it save you?
  5. **What's next:** One concrete next step (shows you think in roadmaps)



### Phrases That Sound Strong

  * "I made that design decision because..." (shows deliberate thinking)
  * "The trade-off I was making was..." (shows systems thinking)
  * "I would productionize this by..." (shows you understand scale)
  * "That's currently in progress — right now I have X working" (honest and structured)


