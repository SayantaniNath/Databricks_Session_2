# HIPAA for Data Engineers — Healthmap Solutions Prep

**Created:** 2026-05-27

**Purpose:** Practical HIPAA reference for a Senior Data Engineer interview at Healthmap Solutions (kidney population health). Not a compliance officer's manual — focused on what a DE actually needs to discuss, claim honestly, and map to the JD's Databricks/Unity Catalog/AWS requirements.

**Companion docs:** `~/Downloads/Recruiter_Call_Prep_Databricks_SDE_20260527.html`

* * *

## HIPAA in 3 sentences

A 1996 US federal law that protects patient health information. It governs how PHI (Protected Health Information) is collected, stored, transmitted, and accessed by healthcare organizations and the companies that work with them. **For a data engineer, HIPAA isn't a vague compliance vibe — it's a concrete list of technical and process requirements that shape how every pipeline, table, and access grant gets built.**

* * *

## What counts as PHI — the 18 identifiers

Anything that ties health info to a specific person. Memorize the categories — interviewers test this:

#| Identifier  
---|---  
1| Names  
2| Geographic info smaller than a state (street, city, ZIP — except first 3 digits of ZIP for areas >20K population)  
3| Dates more granular than year (birth, admission, discharge, death) — anything tied to an individual  
4| Phone numbers  
5| Fax numbers  
6| Email addresses  
7| Social Security Numbers  
8| Medical record numbers  
9| Health plan beneficiary numbers  
10| Account numbers  
11| Certificate / license numbers  
12| Vehicle identifiers (VIN, plates)  
13| Device identifiers / serial numbers  
14| URLs  
15| IP addresses  
16| Biometric identifiers (fingerprints, voice)  
17| Full-face photos / comparable images  
18| Any other unique identifying number, characteristic, or code  
  
**Critical insight:** PHI = health info **+** any identifier. A lab result alone is not PHI. A lab result + a name (or a record number, or an address) **is** PHI. This matters because it shapes how you de-identify data for analytics. 

* * *

## Covered Entity vs Business Associate — where Healthmap sits

Role| Who| HIPAA obligation  
---|---|---  
**Covered Entity (CE)**|  Health plans (insurers), healthcare providers (hospitals, clinics), healthcare clearinghouses| Full HIPAA compliance  
**Business Associate (BA)**|  Anyone who handles PHI on behalf of a CE — analytics vendors, IT providers, billing services, **population health managers**|  Full HIPAA compliance via a contract (BAA) with the CE  
**Subcontractor**|  A BA's vendor that also touches PHI| BAA chains downstream too  
  
**Healthmap = Business Associate.** They contract with payers (CEs) under a **Business Associate Agreement (BAA)** to manage kidney patient populations. That BAA legally binds them to HIPAA's full ruleset — same obligations as the payer themselves.   
  
**IQVIA was also typically a Business Associate** when working with pharma + payer data. That's where your exposure comes from. 

* * *

## The 3 rules — what a DE actually needs to know

### Privacy Rule

Governs **who can see PHI and for what purpose**.

  * **Minimum Necessary principle** — only access the smallest amount of PHI needed for your task. This is why you'll see row-level / column-level access controls in healthcare lakehouses.
  * **Patient rights** — patients can request access to their data, request corrections, request an audit of who accessed their record.



### Security Rule

Governs **how PHI is technically protected**. This is the rule DEs touch every day. Three categories:

Safeguard| Examples DEs touch  
---|---  
**Administrative**|  Access policies, role-based access, workforce training, incident response plans  
**Physical**|  Data center security, workstation security, media disposal (mostly infra team, not DE)  
**Technical**| **Encryption at rest, encryption in transit, access controls, audit logs, integrity controls, transmission security** ← this is your zone  
  
### Breach Notification Rule

If PHI is exposed, must notify affected individuals + HHS within 60 days. If >500 individuals, also notify media. This is why every healthcare org has **audit logs you can't disable** — when a breach is investigated, regulators ask "who accessed what, when?" and you must have the answer.

* * *

## How HIPAA shapes the Healthmap JD (concrete mapping)

Now the JD reads completely differently. Every Databricks/AWS requirement is a HIPAA control in disguise:

JD item| HIPAA control it implements  
---|---  
**Unity Catalog** (three-level namespace, grants, lineage)| Privacy Rule's minimum necessary + Security Rule's access controls + audit trail  
**Delta Lake** (transaction log, time travel)| Security Rule integrity controls + Breach Notification audit requirement  
**S3 + IAM**|  Access controls (IAM roles, S3 bucket policies, server-side encryption with KMS)  
**Secrets Manager**|  Security Rule — no plaintext credentials in code/configs  
**CI/CD across Dev/Staging/Prod workspaces**|  Workforce access separation; PHI typically doesn't exist in Dev — synthetic or de-identified data only  
**Healthcare experience preferred**|  They want someone who already understands all of the above without 6 months of ramp-up  
  
* * *

## De-identification — the analytics escape hatch

PHI can be transformed into non-PHI through formal **de-identification** , after which HIPAA stops applying. Two methods:

  1. **Safe Harbor** — strip all 18 identifiers AND have no actual knowledge that the result could re-identify someone. Mechanical, easy to verify, but lossy (you lose granular dates, ZIPs, etc.).
  2. **Expert Determination** — a qualified statistician certifies that re-identification risk is "very small." More flexible (can keep some identifiers if risk analysis supports it), but requires expert sign-off.



**Why DEs care:** ML/analytics teams often work on de-identified copies. As a DE, you may build **de-identification pipelines** (hashing IDs, generalizing dates to year-only, suppressing rare ZIPs) — _Safe Harbor implementation_ is real DE work and worth mentioning if it comes up. 

**Related concept — Limited Data Set:** PHI with most identifiers stripped but dates and ZIPs retained. Used for research under a Data Use Agreement (DUA). Common in population health / claims analytics, including what Healthmap does.

* * *

## What you can honestly say in interviews

**✅ Safe to say:**

  * _"At IQVIA I worked with patient-level and pharma trial data under HIPAA-aware data handling practices. PHI was handled under documented access controls, encrypted at rest and in transit, with audit trails on sensitive data access."_
  * _"I'm familiar with the distinction between Covered Entities and Business Associates, and the BAA framework that binds vendors like IQVIA — and Healthmap — to the same compliance posture as the payers and providers they serve."_
  * _"I understand the role of de-identification and Limited Data Sets in enabling analytics, including the Safe Harbor 18-identifier rule."_



**❌ Don't claim:**

  * That you were a compliance officer, HIPAA auditor, or BAA lead.
  * That you "owned" HIPAA at IQVIA — you operated _within_ it.
  * Specific incidents or audit findings (confidentiality).
  * Deep familiarity with HHS Office for Civil Rights enforcement details — that's not DE territory.



* * *

## What to be ready to discuss if pressed

Topic| What to say  
---|---  
Encryption| "AES-256 at rest is standard; TLS 1.2+ in transit. On Databricks that maps to storage-level encryption + UC grants for column-level controls."  
Access controls| "Least privilege via role-based access. Unity Catalog's three-level namespace lets you grant at catalog, schema, or table — plus row/column filters for sensitive columns like SSN or DOB."  
Audit| "Every PHI access event needs to be logged immutably. Delta's transaction log + cluster audit logs + UC access logs form that chain."  
De-identification| "Safe Harbor is mechanical — strip the 18 identifiers. Expert determination is statistical and allows richer data but needs sign-off."  
Breach response| "Detection + 60-day notification window. As a DE, my role is making sure the audit logs exist and are queryable so the investigation can actually happen."  
  
* * *

## Quick reading (15–30 min total if going deeper before the call)

  * **HHS HIPAA summary** — `hhs.gov/hipaa` — official, plain language. Read the "Summary of the Privacy Rule" and "Summary of the Security Rule" pages.
  * **De-identification guidance** — `hhs.gov/hipaa/for-professionals/privacy/special-topics/de-identification/` — the canonical reference for Safe Harbor.
  * **Databricks HIPAA compliance page** — search "Databricks HIPAA" — shows how the platform supports compliance (relevant for "have you used Databricks for PHI?" follow-ups).



* * *

## Cheat sheet — one-line version for last-minute review

  * HIPAA protects PHI. PHI = health info + any of 18 identifiers.
  * Covered Entity = payer/provider. Business Associate = vendor handling PHI under a BAA. Healthmap is a BA. IQVIA was a BA.
  * Three rules: Privacy (who can see), Security (how it's protected — admin/physical/technical safeguards), Breach Notification (60-day window).
  * DE = Technical safeguards: encryption (AES-256 rest, TLS in transit), access control (UC grants, IAM), audit logs (immutable), integrity (Delta transaction log).
  * De-identification: Safe Harbor (strip 18 identifiers) or Expert Determination (statistical sign-off). Limited Data Set keeps dates/ZIPs under DUA.
  * Minimum Necessary — only the smallest slice of PHI needed for the task.
  * Healthmap's JD = HIPAA controls expressed in Databricks vocabulary. UC = access. Delta = audit. IAM/Secrets = credential protection. CI/CD = no PHI in Dev.


