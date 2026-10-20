## The Carrowmore Brief

For each keeper in `clean/` and each of the six postings, this says **ready**, **nearly** or
**not shown in these records**, and for anyone nearly it gives the route: the steps in the
order the certification rules force, each marked as something to ask, fetch or book. Every
claim cites the logbook entries behind it.

### Run it

Python 3.10+, standard library only. Put the data pack at `./carrowmore-data-pack` (it is
git-ignored) or pass its path.

```bash
python -m carrowmore.pipeline              # writes out/answers.json, out/team.md, out/keepers/*.md
python -m carrowmore.audit                 # writes out/rule_audit.md: every distinct logbook phrasing and what the rules made of it
python -m unittest                         # invariants and rule regressions
```

### What to read

- `out/team.md`: for the redeployment team. Per posting, who is ready or nearly and in what
  order; the training that unlocks the most people; and three findings nobody asked for.
- `out/keepers/K0147.md` (and the other 37): for the keeper. What the logbooks show, which jobs
  are open now, which are close and the steps in order, and what the records can't tell.
- `out/answers.json`: everything, with each claim's entries, dates and `source_record` paths.
- `out/rule_audit.md`: how the skill rules were checked (all 620 phrasings, not a sample).

### Rules you'd otherwise have to guess

- **Data:** `clean/` only. The two keepers who have left are excluded. Appraisals, manager notes,
  date of birth and grade are never read.
- **Certificates** are recomputed from `training_records`; the pack's `certifications` block is
  ignored. A scheme is awarded when its last module is completed and is current until award +
  renewal period. An `attended` record before 2011 is treated as "look for the certificate",
  because that system didn't separate attending from completing.
- **Has done** counts entries where the keeper did or led the work. Standing by or witnessing
  is shown separately and never counts. Strength: strong = 5+ entries over 3+ years with one in
  the last 10; moderate = 2+; limited = 1.
- **Ready** = everything the records can show is met. **Nearly** = the essential work is shown
  and every gap is a course, a renewal, paperwork or a question. **Not shown** = an essential kind
  of work isn't in these records. The offshore medical and interest are never in the records, so
  they are steps for everyone and never decide the status.
- **Route order** comes from the scheme prerequisites (medical → OSSC → WAHS/SMOC; MECS stage 3 →
  HVAP; the HV paperwork before HVAP), then ask → fetch → book.
- Assumed and flagged: WAHS for the Array (the posting says OSSC covers height; OSSC has no height
  module), and the medical applying to each OSSC module.

### Layout

```
carrowmore/
  model.py      claim, evidence, step and fit types; the evidence invariant   (keep)
  claims.py     strength rules and wording                                    (keep)
  schemes.py    certification recompute                                       (keep)
  route.py      prerequisite graph and ordering                               (keep)
  assess.py     keeper x posting -> fit and route                             (keep the rules)
  skills.py     regex rules per skill                                         (disposable)
  postings.py   the six postings as requirement tables                        (disposable)
  load.py       reads clean/                                                  (disposable)
  render.py     json and markdown                                             (disposable)
  audit.py      rule audit over every distinct phrasing
tests/test_invariants.py
```
