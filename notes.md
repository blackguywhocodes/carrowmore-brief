# Working notes

## Time log

| Date | Start | End | What |
|---|---|---|---|
| 2026-10-15 | [00:30] | | Step 1: read brief and data pack, questions, assumptions |

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
3. “How was the certifications block in clean/keepers.json derived? K0147 shows HVAP awarded 2024, but no training record is dated 2024.”

Sent: [time]. Answer: [pending]

## Process decisions
1. What turns an entry into evidence that someone “has done” a skill: one entry, three, or a span of years?
2. Does recency matter? Is switching work in 1988 worth the same as in 2022?
3. What does “needs first” mean: mobilisation blockers (OSSC, medical) before skill gaps?
4. Which sources am I deliberately ignoring, and why? Appraisals and notes are the obvious ones.
5. How will I check it’s right? Hand-check five keepers against their source entries.
6. What question is this data answering that nobody asked?

## Open decision: which data

- [ ] `clean/` (40 keepers, identities resolved, each entry has a `source_record` pointer back to raw)
- [ ] raw pack (340 keepers, OCR, CP1252, three logbook eras, unreconciled identities)

Decision and why: [ ]

## Ideas considered

| Idea | Keep / drop | Why |
|---|---|---|
| | | |

## Where the AI was wrong

Log these as they happen: what it said, how I noticed, what I did instead.

-