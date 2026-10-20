# Write-up

**Time spent:** [X hours, fill in from the time log in notes.md].

## Why `clean/`

I used `clean/`: 40 keepers, of whom 38 are still employed. Before deciding, I sampled the raw pack against the clean schema. Parsing it is manageable. Identity is the real cost:
- Era 2 uses keeper codes.
- Era 3 identifies people by name from 2014 to 2017, then by payroll reference from 2018 to 2026, with no mapping back to keeper codes.
- Era 1 often names nobody, so whose entry it is would have to be inferred from station postings.

The only place a payroll reference links to a keeper is `clean/`, and only for its 40. Four hours on the raw pack would have gone on identity resolution, and the brief puts the weight on how the system handles uncertainty about a person, so I spent the time there.

The cost is that these 40 aren't a random sample and routine watch lines were removed, so no count here generalises to the 340. What does carry over is the rules: what counts as evidence, how strong it is, what a certificate needs, and what order the steps go in. They don't care which ingestion fed them. If this graduated, identity resolution across the three eras is the first thing I'd build, starting with era 2, whose keeper codes are reliable.

## The question I answered

I widened it from "who could work on the Array" to all six postings. Only 2 of the 38 hold a current offshore safety certificate, and nobody's medical is recorded, so "who is ready for the Array" is 0. The answer the team can act on is the order of the nearly list and what each person needs first, in the order the certification rules force. The other five employers then take people the Array can't use soon. Each keeper gets ready, nearly or not shown for each posting, plus a route of steps marked *ask*, *fetch* or *book*. Every claim cites logbook entry ids, and `answers.json` traces each one to its `source_record`.

## How this differs from a search over a taxonomy

A taxonomy search tags each logbook entry with a skill and returns the keepers whose tags match a posting. I kept that step as the base layer and built four things on top:

1. **Claims, not tags.** Each match records the keeper's role. Doing the work and leading it count. Standing by while someone else did it is shown separately and never counts. Strength comes from fixed rules on entry count, years covered and recency, and every claim cites its entries.
2. **Certificates are worked out, not looked up.** Schemes are recomputed from dated training records against each scheme's modules and renewal period.
3. **Three answers instead of match or no match.** Each keeper is ready, nearly or not shown for each posting. "Not shown" means not in these records, which isn't the same as never having done the work.
4. **A route, not a list.** For anyone nearly, the gaps become ask, fetch or book steps, ordered by a topological sort over the scheme prerequisites. The answer to "what would each of them need first" is the first step of that route.

Matching is a well-understood problem, so it gets a well-understood technique. The work went into what a match is allowed to say about a person and what they should do next.

## What I chose not to build

- **A mapping onto the 2,400-statement skills framework.** None of the six postings refers to it. They ask for certificates and kinds of work, so I mapped the postings by hand into requirement tables (`postings.py`) and matched entries to 26 kinds of work.
- **A model in the loop.** 10,627 entries collapse to 620 distinct phrasings once digits and case are normalised. That is small enough to check every one, so the skill rules are regexes and `out/rule_audit.md` lists every phrasing with what the rules made of it. A model would have needed its own evaluation to earn the same trust.
- **A score.** Strength is ordinal and rule-based: strong, moderate or limited, from entry count, years covered and recency. A number would have looked more precise than the evidence is.
- **Reading numbers from entry text.** Units are swapped across the same template (v and ohm, bar and psi), so a voltage in the text means "mentioned", never "measured".
- **Appraisals, manager notes, date of birth and grade.** None of them is evidence of what someone can do. Entries about disciplining a colleague are excluded, and casualty-care entries count as evidence but their text is never shown, because it describes someone else's injury.
- **An interface.** The team page and the 38 keeper pages are markdown generated from the same claims.

## Where the AI was wrong

- **It counted locking a door as high-voltage switching.** "HV room locked and keys signed back in" fed K0147's HV claim. It is access control. I only found it by hand-checking one keeper against the source entries. HV is the claim the insurer cares about, so after that I read the matches for every authority pattern myself.
- **The audit was broken before the rules were.** The first audit ran the rules over digit-normalised text, so every rule containing `\d` silently matched nothing and the audit looked cleaner than it was. Now it classifies a real example of each phrasing.
- **Plausible regexes, wrong matches.** "refused" matched the fuse rule. "Fault only showed when…" counted as training someone and as being in charge. "permit bk.3 no.41" was missed as permit work. Each fix has a regression test.
- **It wrote a sentence the data didn't support** ("The Coastguard isn't on anyone's redeployment list today"). After that I took the wording back. Every sentence about a person is built from fixed templates in `claims.py`, whose strength rules I set, and standing by while someone else did the work is shown separately and never counts.
- **It would have trusted the pack's certificate summary.** K0147 showed HVAP awarded in 2024 with no training record from 2024. I asked Greg, who confirmed the block assumes renewals no record supports. The system recomputes from training records, and that turns up 4 certificates the pack calls valid that the records don't support (K1374 HVAP and MECS, K1418 OSSC, K1483 LOSC).





Hand checked K0184, 303, 354, 394, and 478, They all passed rules hand check.

## What I'd throw away, and what I'd keep

**Throw away first:**
- `skills.py`, the regexes. They work for 620 phrasings in one clean extract and won't survive OCR.
- `load.py`. It reads `clean/` and would be replaced by identity resolution across the three logbook eras, starting with era 2, whose keeper codes are reliable.
- `postings.py`, hand-mapped and only right for these six.
- `render.py`.

**Keep:**
- **The evidence invariant** (`model.py`). No has-done claim can exist without cited entries. It is enforced in the constructor, not by convention.
- **The claim rules** (`claims.py`): ordinal strength and the line between doing work and standing by while it was done.
- **The certificate recompute** (`schemes.py`), with pre-2011 attendance records turned into "find the certificate" steps because that vendor didn't separate attending from completing.
- **The route ordering** (`route.py`): a topological sort over scheme prerequisites.
- **The audit**, kept as the evaluation set for whatever replaces the regexes.

The 15 tests cover only these invariants and the rule regressions, not the disposable code.

## Things not aske for

- **Whose HV paperwork is worth reconstructing.** The HV posting accepts a lapsed internal authorisation, but only with documents. Ten keepers' logbooks show them issuing switching documents or holding the HV keys, led by K0566 (22 entries) and K1231 (21). Each comes with the stations whose records to search first.
- **The job that wants the opposite.** 15 keepers need 6 or more courses before the Array could use them, but already show everything the Coastguard can check from records (radio work) plus at least two of its desirables: incident handling, weather observing or long-kept logs.
- **Training to buy.** For the Array, WAHS-2 is needed by 36 of the 37 nearly keepers. Counting only, because costs and dates aren't in the data.
