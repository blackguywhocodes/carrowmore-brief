# Working notes

## Time log

| Date | Start | End | What |
|---|---|---|---|
| 2026-10-15 | [11:00] | [11:38] | Step 1: read brief and data pack, questions, assumptions |  
| 2026-10-18 | [9:00] | [11:30] | Created and implemented app 
|   2026-10-18 | [02:00] | 02:49] | Testing + Write-up |  

## Step 1: intake

- Received the brief (`brief-PE-carrowmore.docx`) and the data pack (`carrowmore-data-pack/`).
- Read the brief end to end, then the pack README and `clean/README.md`.

## Assumptions (From brief)

- **Primary user: the redeployment team.** Section 5 frames the question as theirs: who among the 340 could plausibly work on the Array, and what would each need first.
- **Secondary audience: the keeper.** Whatever the output says about a person, it should be fit for that person to read (section 3).
- **No integrations, no UI.** The brief says there is no expected architecture and no credit for an interface. Output is JSON plus a readable markdown report.
- **Target role: Carrowmore Array O&M technician** (about 40 hires). The other five postings are out of scope unless something interesting falls out.
- **Language: Python, stdlib only**, unless a library clearly earns its place.

## Questions sent to Greg

1. Are the Authority's internal HV authorisations recorded anywhere, or are they only inferable from logbooks? (The HVAP scheme accepts a lapsed internal authorisation in lieu of experience, but only with documents.)
2. “Is offshore medical fitness recorded anywhere? I can’t find it in the pack.”
3. “How was the certifications block in clean/keepers.json derived? clean/README.md says certification status wasn't resolved, but the block is there, and K0147 shows HVAP awarded 2024 with no training record dated 2024.”

Sent: 10:21. Answered by Greg: 12:33.

### Greg's answers

1. **HV authorisations:** assumption confirmed. Inferable from logbooks only, so treat as "possible, needs paperwork", never as held.
2. **Offshore medical:** assumption confirmed. Unknown for everyone, so it is a "needs first" item for every keeper.
3. **Certifications block:** a real flaw in the data pack. The data team built it as a per-scheme summary of the training records:
   - `modules_held`: modules with a completed record.
   - `complete`: every module in the scheme has one.
   - `awarded_year`: the latest completion year, **rolled forward by the scheme's renewal period wherever the team assumed a keeper had renewed**.
   - `valid_2026`: complete and not past `expires_year`.

   The assumed renewals aren't backed by any record in the extract. K0147: last HVAP completion 2021, HVAP renews every 3 years, so the block shows an award in 2024 and expiry in 2027. Nothing proves or disproves those renewals. Greg: recomputing and treating the block as unverified is reasonable; **say which I used**.

### Decision: certifications

- Recompute certification status from `training_records` only. Ignore `awarded_year`, `expires_year` and `valid_2026` in the block.
- Applies to all 40 keepers, not just K0147.
- Output separates an evidenced completion from an assumed renewal. Example for K0147: "HVAP: last completed module 2021; renewal was due 2024; no record of renewal; scheme incomplete (HVAP-01, HVAP-03 missing)." Add "confirm renewal or re-sit" to their "needs first".
- Unasked finding for the write-up: the pack's own certification summary assumed renewals no record supports; my output never states a certification is current without a dated completion behind it.

## Process decisions
1. What turns an entry into evidence that someone “has done” a skill: one entry, three, or a span of years?
2. Does recency matter? Is switching work in 1988 worth the same as in 2022?
3. What does “needs first” mean: mobilisation blockers (OSSC, medical) before skill gaps?
4. Which sources am I deliberately ignoring, and why? Appraisals and notes are the obvious ones.
5. How will I check it’s right? Hand-check five keepers against their source entries.
6. What question is this data answering that nobody asked?

## Decision: which data

- [x] `clean/` (40 keepers, identities resolved, each entry has a `source_record` pointer back to raw)
- [ ] raw pack (340 keepers, OCR, CP1252, three logbook eras, unreconciled identities)

Decision and why: I used `clean/`. Before deciding, I sampled the raw pack against the clean schema. Parsing is manageable; the real cost is identity. Era 2 uses keeper codes, era 3 switches from names (2014–17) to payroll refs (2018–26) with no mapping back to keeper codes, and era 1 often names nobody, so ownership would have to be inferred from station postings. The clean set is the only place a payroll-to-keeper link exists, and only for its 40. Four hours there would go to ingestion, not to the question the brief cares about: how the system handles uncertainty. If this graduated, identity resolution across the three eras is the first thing I'd build, starting with era 2, whose keeper codes are reliable. Trade-off: these 40 aren't a random sample and routine watch lines were removed, so nothing here generalises to all 340.