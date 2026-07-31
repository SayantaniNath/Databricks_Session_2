# Databricks / DEA + AWS CCP Learning Resources

**Purpose:** Depth resources for Stage 2B + Databricks DEA cert + AWS CCP cert + production job readiness. Not surface skim — pick what you need by topic.

**How to use:** This is a menu, not a syllabus. Pin two things at a time. Anchor _Learning Spark 2e_ as your core Databricks reading. For AWS CCP, anchor Stephane Maarek's course + Tutorials Dojo practice exams.

* * *

## Foundational — start here

### Free books

  * **Learning Spark, 2nd Edition** — Jules Damji, Brooke Wenig, Tathagata Das, Denny Lee. Databricks gives the PDF away free — search _"Learning Spark 2nd edition free pdf databricks"_. ~400 pages. Covers DataFrames, Spark SQL, Structured Streaming, Delta Lake. **This + practice ≈ 70% of DEA content.** Read Ch 1–4 first.
  * **Spark: The Definitive Guide** — Bill Chambers & Matei Zaharia. Deeper, longer. Use as reference, not cover-to-cover.
  * **Delta Lake: The Definitive Guide** (O'Reilly, 2024) — Denny Lee et al. Early-release PDF was on databricks.com.



### Free official course

  * **Databricks Academy → "Data Engineering with Databricks"** learning path. DEA-aligned, free, hands-on notebooks. Sign up at `customer-academy.databricks.com`.



* * *

## YouTube — channels worth subscribing to

Rank-ordered by relevance:

**1\. Advancing Analytics** — `youtube.com/@AdvancingAnalytics` (Simon Whiteley). Best Databricks technical channel. Deep playlists on Delta Lake, Unity Catalog, Photon, perf tuning. **Watch Delta Lake series end-to-end.**

**2\. Databricks (official)** — `youtube.com/@Databricks`. Data + AI Summit talks (Delta, UC, Photon, DLT). Also "Databricks Demo Hub". 

**3\. Bryan Cafferky** — `youtube.com/@BryanCafferky`. "Master Databricks and Apache Spark" playlist. Beginner-friendly pace. 

**4\. Derar Alhussein** — `youtube.com/@DerarAlhussein`. Free **DEA crash course** playlist alongside the paid Udemy course. Final-week cert review. 

**5\. Ease With Data** — `youtube.com/@easewithdata`. DEA practice question explanations. 

**6\. Andreas Kretz** — already in flight via his Databricks repo. His YouTube ("Learn Data Engineering") pairs with the repo. 

* * *

## Topic-by-topic depth

### Delta Lake (heaviest JD + heaviest DEA topic)

  * **Docs:** `docs.databricks.com` → "Delta Lake on Databricks". Order: _What is Delta → Tutorial → MERGE → Optimize → Z-Ordering → Vacuum → Time travel → Transaction log internals._
  * **Project site:** `delta.io/learn` (vendor-neutral).
  * **Blog (deep):** Databricks Engineering — _"Diving into Delta Lake: Unpacking the Transaction Log"_ (3-part series). Foundational.
  * **Watch:** Advancing Analytics — Delta Lake playlist (~10 videos).
  * **Book:** _Delta Lake: The Definitive Guide_ (O'Reilly).



### Unity Catalog

  * **Docs:** `docs.databricks.com` → "Data governance" → "Unity Catalog". Order: _What is UC → three-level namespace → managed vs external tables → grants/privileges → lineage → metastore setup._
  * **Watch:** Advancing Analytics — Unity Catalog series. Databricks official "Unity Catalog Demo".
  * **Blog:** Databricks blog `/blog/category/platform/unity-catalog/` — architecture overview + governance posts.



### Spark optimization + Photon

  * **Docs:** `docs.databricks.com` → "Compute" → "Photon"; also "Query optimization" + "Adaptive Query Execution (AQE)".
  * **Book:** _Learning Spark 2e_ , Ch 7 — "Optimizing and Tuning Spark Applications".
  * **⭐ Must-watch:** **Daniel Tomes — _"Apache Spark Core — Deep Dive — Proper Optimization"_** (Spark+AI Summit, on YouTube). ~1 hour. Single best Spark perf talk that exists. Watch twice across your prep arc.
  * **Watch:** Advancing Analytics — Photon + AQE deep-dives.



### Structured Streaming

  * **Book:** _Learning Spark 2e_ , Ch 8.
  * **Docs:** `docs.databricks.com` → "Structured Streaming". Focus: watermarks, output modes, checkpointing, trigger types.
  * **Blog series:** Databricks — _"A Deep Dive into Stateful Stream Processing in Structured Streaming"_ (4-part).



### Delta Live Tables (DLT)

  * **Docs:** `docs.databricks.com` → "Delta Live Tables". Read: _What is DLT → declarative pipelines → expectations → CDC with DLT._
  * **Watch:** Advancing Analytics DLT playlist. Databricks official DLT demos.



### Databricks Workflows / Jobs

  * **Docs:** `docs.databricks.com` → "Jobs". Read: _Create a job → task types → multi-task workflows → triggers → retries → notifications._
  * **Watch:** Databricks official Workflows demo. Bryan Cafferky walkthrough.



### CI/CD — Databricks Asset Bundles (DABs)

  * **Docs:** `docs.databricks.com` → "Databricks Asset Bundles". Modern, Databricks-recommended path. Read in full.
  * **Blog:** Search "Databricks Asset Bundles" announcement post.
  * **Watch:** Databricks official DABs intro. Advancing Analytics CI/CD content.



### AWS integration (S3, IAM, Secrets)

  * **Docs:** `docs.databricks.com` → "Connect to data sources" → "Amazon S3"; "Manage credentials"; "Secret management".
  * Concepts: instance profiles for S3, secret scopes for credentials, mount points (legacy) vs UC external locations (current).



* * *

## AWS Cloud Practitioner (CCP) — fast path

**Honest read on the Skilljar course:** Fine for general audience, but slow for your profile. You've done production cloud-warehouse work — you don't need a primer on what storage or networking is. The Udemy courses below assume that and move ~2× faster. 

### Course — pick one

  1. **Stephane Maarek — _"Ultimate AWS Certified Cloud Practitioner CLF-C02"_ (Udemy)** — ~14–15 hrs. Most popular CCP course by far, exam-focused. Watch at 1.5–1.75×. ~$15 on Udemy sale (almost always running).
  2. **Andrew Brown / ExamPro — free on YouTube / freeCodeCamp** — full ~15 hr CCP course, no cost. Search YouTube for _"AWS Certified Cloud Practitioner Andrew Brown freeCodeCamp"_. Pick this for the zero-spend route. Slightly less polished than Maarek but same ground covered.



### Practice exams (the actual unlock — not optional)

  * **Tutorials Dojo (Jon Bonso) — CLF-C02 practice tests** on `tutorialsdojo.com` (~$15). The single most important resource. Most CCP passers say _"Maarek for content, Bonso for the actual exam."_ Their questions are harder than the real exam, by design — if you can score 75%+ on TD, you'll comfortably pass.



### Concrete plan to pass by ~mid-to-late June

Phase| Time| Action  
---|---|---  
1 — Finish Skilljar Module 6| ~1 hr| Wrap Storage so you're not abandoning mid-module  
2 — Maarek course| ~10 hrs at 1.5×| Watch on AWS slots (Tue/Thu) + 1 weekend session. ~2 weeks  
3 — Tutorials Dojo (round 1)| ~3 hrs| One full timed exam. Review every wrong answer.  
4 — Patch weak topics| ~2 hrs| Re-watch Maarek sections where TD exposed gaps  
5 — Tutorials Dojo (round 2)| ~3 hrs| Score consistently 80%+ → book the exam  
  
Total: ~18 hrs from tomorrow. At Tue/Thu pace + one weekend hour, that's **mid-to-late June for exam-ready**. Original Jun 11 target slips ~1–2 weeks — fine. Better to pass once than rush and re-sit.

### What to skip

  * **AWS Cloud Quest** / gamified learning paths — fun, slow, not exam-prep.
  * **Cloud Academy / A Cloud Guru CCP course** — fine, not differentiated. If you don't already have access, Maarek is better value.
  * **Multiple practice test packs** — Tutorials Dojo alone is enough.



### Free-only alternative

Andrew Brown (free YouTube) + AWS Skill Builder's free official practice exam + 1 paid Tutorials Dojo set ($15). Tutorials Dojo is the only thing I'd not skip — the question style is what trains you for the real exam.

* * *

## DEA cert-specific (when you push for cert, ~Jul–Aug 2026)

  1. **Official exam guide** — `databricks.com/learn/certification/data-engineer-associate`. Read the outline — percentages tell you where to spend time.
  2. **Databricks Academy "Data Engineering with Databricks"** — already in your plan. End-to-end.
  3. **Derar Alhussein's Udemy course** — already in your plan. ~6 hrs condensed.
  4. **Practice exams:**
     * Official Databricks practice exam (1 free).
     * Skillcertpro DEA practice tests (paid, high-quality questions).
  5. **Final-week review:** Derar's free YouTube DEA crash course + re-read weak-topic docs.



* * *

## Suggested sequencing (don't try to consume all of this)

**Next 2 weeks of Stage 2B slots (Mon/Wed/Fri):**

  1. Download _Learning Spark 2e_ — read Ch 1–4 to anchor concepts.
  2. Subscribe to **Advancing Analytics** → pick **Delta Lake playlist** → one video per slot, paired with `docs.databricks.com` skim of the same topic.



Everything else here is the menu. You don't eat the whole menu.
