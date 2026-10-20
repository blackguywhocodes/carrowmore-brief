# Carrowmore: what can and can't be answered

> Superseded in part by architecture.md (v2, 2026-10-19), which covers all six postings and adds routes. Where they differ, v2 wins.

Viability means how likely an option is to work well inside the 4-hour budget, using
`clean/`. Rank 1 is the recommended option. "Reject" means it would hurt the submission.

## Solved: answerable from the data

| # | Aspect | Options, ranked | Viability |
|---|---|---|---|
| S1 | **"Has done" a skill**, from logbook entries | 1. Keyword/regex rules for 8–12 Array-relevant skills, each match keeping its `entry_id` | High |
| | | 2. LLM classifies entries into those skills, then hand-check 20–30 | Medium: more coverage, but costs time and needs checking |
| | | 3. Embedding similarity to NOSF framework statements | Low: the framework uses policy language, and tuning eats the budget |
| S2 | **Training and certification status** | 1. Recompute per scheme from `training_records`: completed vs attended, missing modules, last completion year, renewal due | High (Greg agreed) |
| | | 2. Use the `certifications` block as given | Reject: assumes renewals no record supports |
| S3 | **Gaps against the Array O&M posting ("needs first")** | 1. Hand-map the posting's essentials to `certification_schemes.json` plus the skill list, once, in a small config | High |
| | | 2. Have an LLM parse all six postings into requirements | Low–medium: the scope is only one posting, so it doesn't pay |
| S4 | **Traceability** | 1. Every claim carries its `entry_id`s and `source_record` paths inline | High: comes free with `clean/` |
| | | 2. Separate evidence index file that claims point into | Medium: cleaner, but more to build |
| S5 | **Per-keeper answer** | 1. Three groups (strong / plausible with named gaps / not enough evidence) with thresholds written down | High |
| | | 2. Weighted numeric score and ranking | Low: false precision, which reads as overclaiming |
| S6 | **Recency** | 1. Show first and last year and entry count per skill; don't weight | High |
| | | 2. Time-decay weighting | Medium: defensible, but adds a judgement you'd have to justify |
| S7 | **Unasked question: lapsed HV authorisation candidates** | 1. List keepers with repeated switching or earthing entries as "worth reconstructing paperwork for" (feeds the HV Authorised Person posting) | High |

## Unsolved: not answerable from the data, so handle them honestly

| # | Aspect | Options, ranked | Viability |
|---|---|---|---|
| U1 | **Whether someone is authorised** (HV) | 1. Wording: "has done X (entries…); authorisation unknown; needs documentary evidence" | High (Greg confirmed) |
| | | 2. Treat a `verified_by` field (2022+ logs) as supporting evidence, never as authorisation | Medium: check whether `clean/` even carries it |
| U2 | **Whether a certificate is current** | 1. "Last completed 2021; renewal due 2024; no record of renewal" → needs first: confirm or re-sit | High |
| U3 | **Offshore medical fitness** | 1. A universal "needs first" item for every keeper, stated once | High (Greg confirmed) |
| U4 | **Personal fit** (height, swell, confined spaces, 14/14 rota) | 1. "Ask the keeper" item; related logbook work (boat handling, working at height) is shown as *has done*, never as *fit* | High |
| | | 2. Use age or date of birth as a proxy | Reject: wrong, and discriminatory |
| U5 | **Whether the keeper wants the job** | 1. First action for every shortlisted keeper: confirm interest | High |
| | | 2. Note it as out of scope in the write-up only | Medium |
| U6 | **No record ≠ didn't do it** (pre-1994, the 1997 migration, Vendor A's attended/completed) | 1. Always "no record of…", and flag keepers in service in 1997 as possibly affected | High |
| | | 2. Treat missing records as gaps | Reject: penalises the people the migration failed |
| U7 | **How well they did the work** | 1. State it isn't assessed; exclude appraisals and manager notes | High: also covers the privacy concern |
| | | 2. Mine appraisals through an allowlist of work-only phrases | Low: unreliable and sensitive, for little gain |
| U8 | **Accuracy** (no ground truth) | 1. Hand-check 5 keepers end to end against their source entries | High |
| | | 2. Hand-label about 30 entries to estimate matcher precision | Medium–high: strong if time allows |
| U9 | **Generalising to all 340** | 1. State the limit: 40 keepers, not a random sample, routine lines removed | High |
| | | 2. Extend to era 2 (KEEPERLOG) for all 340 using keeper codes | Low within 4 hours: one to mention, not build |

## What this means for the build

Build S1–S7 using option 1 throughout. Each U row becomes either a fixed wording rule or a
"needs first" / "unknown, how to find out" line on the keeper's answer. Put the rejected
options in the write-up under "what I chose not to build".
