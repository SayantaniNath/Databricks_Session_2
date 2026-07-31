# AI Job Application Agent — Interview Prep

Sayantani Nath  ·  Built: 2026  ·  Status: Live  ·  Language: Python

## One-Liner

A Python automation pipeline that scrapes live job postings from LinkedIn and Indeed, scores them against a resume using keyword matching, filters visa-restricted roles, and auto-fills ATS application forms using browser automation — saving ~2 hours/week of repetitive form-filling.

## Full Pipeline — End to End

LinkedIn / Indeed (scraped via jobspy) ↓ job_matcher.py ↓ score each job against 35 resume keywords ↓ filter: SF Bay Area + US Remote only ↓ filter: remove green card / clearance / citizenship required roles ↓ flag: EAD-friendly jobs (explicitly mention L2, EAD, work auth) ↓ Ranked CSV → job_matches_YYYYMMDD.csv ↓ (you review top matches, pick a role) ↓ agent_apply.py <apply_url> ↓ opens real Chrome via Playwright ↓ scans all visible form fields ↓ matches field labels → profile.yaml values ↓ fills: name, email, phone, LinkedIn, GitHub, portfolio, location, work auth ↓ uploads resume PDF automatically ↓ STOPS — you review and submit manually

## File-by-File Breakdown

### job_matcher.py

  * Uses `jobspy` library to scrape LinkedIn + Indeed simultaneously — 20+ job titles searched in one run
  * **Scoring:** `score_job(title, description)` matches text against ~35 resume keywords. Score = (matched / total) × 250, capped at 100
  * **Location filter:** Two modes — `remote_only` (must say "remote" in location string) and `sf_relocated` (SF Bay Area + major US cities + remote). remote_only is stricter because LinkedIn often tags hybrid jobs as is_remote=True
  * **Visa filter:** `is_visa_restricted()` scans for ~25 phrases: "US citizens only", "green card only", "security clearance", "FedRAMP", "requires citizenship" — removes these before scoring
  * **EAD signal:** Flags jobs that explicitly mention EAD, L2, work authorization, no sponsorship required
  * **Output:** Sorted CSV with score, title, company, salary, apply URL, matched keywords, EAD status



### agent_apply.py

  * Takes a single ATS URL as input, opens it in Chrome (headless=False — visible window)
  * **field_signal():** For each form field, collects label, placeholder, aria-label, field name, nearby heading text → concatenates into one lowercase string
  * **matches_keyword():** Word-boundary regex — `\bstate\b` matches "state" field but NOT "United States"
  * **Combobox handling:** React ATS platforms (Greenhouse, Lever) render dropdowns as comboboxes — the script clicks, types, waits for dropdown, clicks matching option
  * **File upload:** Detects `input[type=file]`, uploads resume PDF automatically
  * **Never submits:** Stops after filling, prints summary of filled/skipped fields, waits for you to review and submit



## Why You Built It

Each job application repeats the same 20-40 form fields — name, email, phone, LinkedIn, work authorization. Manually filling these 30-50 times a month is pure repetitive work. The visa filter was added after wasting time on roles requiring US citizenship or clearance, which an L2 EAD holder cannot have. The agent catches these before they reach the shortlist.

## Design Decisions to Defend

  * **jobspy over LinkedIn API:** LinkedIn's official API blocks individual developer access for job search. jobspy scrapes structured data from both LinkedIn and Indeed in one call
  * **Playwright over Selenium:** Modern ATS platforms are React SPAs. Playwright handles client-side rendering, async loading, and shadow DOM better than Selenium
  * **Word-boundary regex:** Simple substring matching caused "state" to match inside "United States", filling the wrong field. Word boundaries prevent this
  * **headless=False:** You need to see the form in real time to catch captchas, load failures, or unexpected UI
  * **Never auto-submit:** A wrong submission (wrong salary, wrong answer) can't be undone. Human stays in the loop for final review
  * **Two location modes:** LinkedIn tags hybrid roles as is_remote=True. remote_only mode requires "remote" explicitly in the location string to catch these false positives



## What It Can't Do Yet

  * Dropdown/select fields (ethnicity, gender, job type) — need separate handling
  * LinkedIn Easy Apply — different mechanism, separate build needed
  * Free-text "why do you want to work here" questions — needs LLM integration



## Interview Q&A

Q: Walk me through this pipeline end to end.

I run job_matcher.py which scrapes LinkedIn and Indeed for 20+ data engineering job titles. Each job gets scored against my resume keywords — things like dimensional modeling, Kafka, Snowflake. It filters out visa-restricted roles and flags EAD-friendly ones. Output is a ranked CSV. I pick a role, pass its URL to agent_apply.py, which opens Chrome, reads all form fields, matches them to my profile using keyword rules, fills everything it can, uploads my resume — then stops. I review the filled form and click Submit myself.

Q: Why didn't you use the LinkedIn API?

LinkedIn's API is not available to individual developers for job search. jobspy scrapes structured job data from both LinkedIn and Indeed in one call — title, company, salary, location, description, is_remote flag. The trade-off is it can break if the sites change their HTML, but for a personal tool that's acceptable.

Q: How does field matching work?

For each form field I collect every clue about what it's asking — label, placeholder, aria-label, field name, nearby heading — and concatenate into one lowercase string. Then I match that against keyword rules using word-boundary regex. Word boundaries were important: plain substring matching caused "state" to match inside "United States", filling the wrong field with a Yes/No work auth answer.

Q: What would you build next?

Three things: LLM-powered answers for open-ended questions like "why do you want this role", LinkedIn Easy Apply support since most quick applications go through that, and a proper tracking dashboard instead of a CSV — callback rate by company type, visa filter effectiveness, salary range distribution.

Q: What's the hardest bug you fixed?

The combobox problem. Some ATS platforms render Yes/No and dropdown fields as React comboboxes — they look like plain text inputs but reject direct fill() because React controls the state. Plain el.fill("Yes") would appear filled, then silently reset when React re-rendered. The fix was to detect comboboxes via role="combobox" or aria-autocomplete attributes, then click, type, wait for the dropdown, and click the matching option — mimicking real human interaction so React accepted the value.
