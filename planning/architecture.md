# Carrowmore: deliverable architecture (v2)

v2 changes the product. v1 found skills and listed gaps for one posting, which is close to the
"search engine over a skills taxonomy" the brief warns about (section 3). v2 answers the keeper's
own three questions in section 2, for every posting, and turns gaps into a route: an ordered
plan, with the paperwork to fetch and the course to book next.

## The product in one paragraph

For each keeper and each of the six postings, the system says one of three things:
**qualified now**, **nearly** (with the evidenced, closeable gaps named), or **not on these
records**. For anyone who is "nearly", it gives **the shortest honest route**: the steps in
the order the scheme prerequisites force, separated into things to *fetch* (paperwork that
probably exists, pointed to by the logbook entries), things to *ask* (questions only the keeper
can answer) and things to *book* (courses). It produces two views of the same claims: one for
the redeployment team (who to interview for which job, and what training to buy) and a short
page addressed to the keeper.

## Why this goes beyond taxonomy search

The numbers in this table are illustrative, not from the data.

| A taxonomy search gives you | This gives you |
|---|---|
| "Has skill: HV switching" | "Has repeatedly done HV switching (14 entries, 2006–2019). Not authorised on these records. The HVAP scheme accepts a lapsed internal authorisation as evidence, so the first step is to find the original paperwork. Entries C004512 and C004530 name the stations and years to search." |
| A list of missing certificates | An ordered route: medical → OSSC → WAHS-2, WAHS-4, because the scheme rules force that order |
| A per-keeper list | A team-level decision: "One OSSC course cohort makes N keepers eligible for two employers" |
| One job | Six jobs, including the one where a keeper who is weak for the Array is the strongest candidate (Coastguard) |

## What this optimises for

1. **Accuracy:** no claim without evidence, and no inference outside the whitelist.
2. **Usefulness:** each answer ends in an action someone can take next week.
3. **The 4-hour window:** stdlib Python, `clean/` only, a cut order written down in advance (below).
4. **Simple, with room to expand:** each expansion slots into one pipeline stage.

## Method selection: known techniques for known problems

Principle: use established techniques for well-understood problems, and keep novel methods
for hard problems with no established solution. Start from the problem, never from a
preselected solution.

| Sub-problem | Established? | Method chosen |
|---|---|---|
| Load structured JSON | Yes | stdlib `json` + dataclasses |
| Recompute certification status | Yes | Rule evaluation over training records |
| Eligibility against a posting | Yes | A requirements table per posting (six, hand-mapped) |
| **Order the route** | **Yes: dependency resolution** | **Topological sort over the scheme prerequisites** (medical → OSSC → OSSC-SS → WAHS, SMOC; MECS-3 → HVAP; LOSC-S, LOSC-A → LOSC-P) |
| Find a fixed set of skills in short free text | Yes, for a small vocabulary | Regex per skill, measured by hand-checks |
| Pick the training that unlocks the most people | Yes: counting | For each missing module, count keepers for whom it is the last gap per posting |
| Express uncertainty to a human | A design problem | Typed claims + fixed, committed wording rules |
| **Resolve identities across three eras** | **No: hard** | Not attempted; `clean/` resolves it for 40 (deferred, stage 1 slot) |
| **Map logbook shorthand to the 2,514-statement NOSF** | **No: hard** | Not attempted; scoped to ~14 skills (deferred, stage 2 slot) |

The route planner is the step that makes this a product rather than a search, and it is
still an established technique. Sophistication goes where the value is, not where the
method is novel.

## Where AI fits

AI is a build tool here. The rule: AI may produce anything a human then checks against the
data, and nothing in the output relies on AI judgement that wasn't checked.

| Use AI for | Check it by |
|---|---|
| Drafting skill regexes from real entries | Hand-check sample per skill |
| Turning six postings into requirement tables | Line-by-line against each posting |
| Encoding scheme prerequisites (they are prose in the JSON) | Read each against `certification_schemes.json` |
| Scaffolding code, renderer, tests | Running it; reading the diff |
| Recall check on 50 *unmatched* entries (optional) | Read each flagged entry |

The brief says a model inside the product is fine if "a handful of cases you checked by hand"
shows it works. Regex is still the choice because ~14 skills over short log lines is an
established problem. That's the defence, not a lack of rigour budget. Log every AI correction in
notes.md; that's the "where was the AI wrong" answer.

## Design principles

1. **Accuracy beats coverage.** "A confident unsourced claim is worse than no claim."
2. **Commit where the evidence is strong; hedge only where it's weak.** The brief's own example
   is "has almost certainly done high-voltage switching". If every line has a caveat, the
   answer tells a keeper nothing (section 3: "lean too cautious").
3. **Inference has a whitelist.** Inferred: has done, trained. Never inferred: authorisation,
   current certification, medical fitness, personal fit, interest.
4. **Every gap becomes an action.** fetch, ask or book. A gap with no action isn't output.
5. **The wording carries the uncertainty.** Fixed phrasing per claim kind and strength.
6. **Durable core, disposable edges.** Claim model, wording rules, route ordering: durable.
   Loaders, regexes, requirement tables, renderer: disposable.

## Pipeline

```
clean/*.json ─────────────────────────┐
employers/*.md (6 requirement tables) ─┼─> 1 load ─> 2 match ─> 3 claims ─> 4 assess ─> 5 route ─> 6 render
certification_schemes.json (+ prereq graph) ┘
```

| Stage | Does | Output |
|---|---|---|
| 1. Load | Read clean JSON into dataclasses | `Keeper`, `Entry` |
| 2. Match | Per-skill regex over entry text; keep entry_id, date, source_record, matched phrase | `Evidence` |
| 3. Claims | Evidence + training records → typed claims with strength and reason; recompute schemes | `Claim` |
| 4. Assess | Each keeper × each posting: qualified / nearly / not on these records, with typed gaps | `Fit` |
| 5. Route | For each "nearly" fit, order the gaps by the prerequisite graph and tag each fetch / ask / book | `Route` |
| 6. Render | `answers.json`; `team.md` (per posting interview list + training buy); `keepers/K0xxx.md` | files |

## Data model (durable)

```python
class ClaimKind(Enum):
    HAS_DONE = "has_done"; TRAINED = "trained"; SCHEME_STATUS = "scheme"
    NO_RECORD = "no_record"; UNKNOWN = "unknown"

class Strength(Enum):
    STRONG = "strong"; MODERATE = "moderate"; LIMITED = "limited"

class Action(Enum):
    FETCH = "fetch"   # paperwork that probably exists; evidence says where to look
    ASK = "ask"       # only the keeper can answer (interest, medical history, comfort at height)
    BOOK = "book"     # a course or assessment

@dataclass(frozen=True)
class Evidence:
    entry_id: str; date: str; source_record: str; text: str; matched: str

@dataclass
class Claim:
    keeper: str; skill: str; kind: ClaimKind
    strength: Strength | None; reason: str
    evidence: list[Evidence]; caveat: str | None

@dataclass
class Gap:
    requirement: str            # "OSSC-HL", "hv_switching_2yrs_documented"
    kind: str                   # module_missing / renewal_due / skill_limited / paperwork / unknown
    action: Action; because: list[Claim]

@dataclass
class Fit:
    keeper: str; posting: str
    status: str                 # qualified / nearly / not_on_these_records
    met: list[Claim]; gaps: list[Gap]

@dataclass
class Route:
    keeper: str; posting: str; steps: list[Gap]   # topologically ordered
```

Invariants, enforced in code (these are the tests worth submitting):
1. A HAS_DONE or TRAINED claim with no evidence raises.
2. A Gap with no Action raises.
3. No route step appears before a step it depends on.

## Stage 2: skills (disposable)

About 14 skills, the union of what the six postings ask for. Patterns are starting points;
check them on real entries and log changes.

| Skill | Postings | Example patterns | Watch for |
|---|---|---|---|
| Generator / diesel plant | Array, Port, Meridian | `generator`, `diesel`, `alternator`, `injector` | routine "generator run" vs repair |
| LV electrical | Array, Port, Deepline | `fuse`, `breaker`, `wiring`, `distribution`, `fault` | |
| HV switching / earthing | HV AP | `switch(ed\|ing)`, `earth(ed\|ing)`, `\bkV\b`, `isolat` | non-electrical "earthed" |
| Permits / isolation | Array, HV AP | `permit`, `lock[- ]?out` | |
| Working at height | Array | `tower`, `gallery`, `harness`, `abseil`, `rope` | routine gallery cleaning |
| Confined space | Array, Port | `tank`, `void`, `confined`, `chamber` | |
| Boat handling | Array, Meridian | `boat`, `landing`, `tender`, `transfer` | relief as passenger vs handling |
| Hydraulics / mechanical | Array | `hydraulic`, `pump`, `bearing`, `gearbox` | |
| Fault-finding (electronic) | Deepline | `fault`, `telemetry`, `multimeter`, `diagnos` | |
| Radio (VHF/MF/DSC) | Coastguard | `VHF`, `MF`, `DSC`, `radio`, `distress`, `mayday` | routine radio checks count here |
| Met observing | Coastguard | `barometer`, `visibility`, `wind \w+ force`, `met obs` | |
| Nav lights / ATON | Port, Meridian | `lens`, `lamp`, `character`, `flasher`, `optic` | |
| First aid / casualty | Array | `first aid`, `casualty`, `evacuat` | skill only; never the health detail |
| Training others | Array, HV AP | `trained`, `instructed`, `supernumerary` | |

Watchkeeping tenure comes from postings, not regex: years in post at a rock station.

## Stage 3: strength rules and committed wording

| Strength | Rule (HAS_DONE) | Wording |
|---|---|---|
| Strong | ≥5 entries across ≥3 years, latest within 10 years | "Has repeatedly done {skill}: {n} entries, {first}–{last}." |
| Moderate | ≥2 entries, or strong but latest >10 years ago | "Has done {skill}: {n} entries, {first}–{last}." |
| Limited | 1 entry | "One logbook entry mentions {skill} ({year})." |

Hedges are reserved for what is actually uncertain:

| Question | Wording | Action |
|---|---|---|
| Certification current | "{scheme}: last completed {year}; renewal was due {year}; no record of renewal." | book (or fetch, if renewed elsewhere) |
| HV authorisation | "Not authorised on these records. Logbook entries {ids} show switching at {stations}, {years}: the places to look for the original authorisation." | fetch |
| Offshore medical | "Not recorded for anyone." (stated once per page, not per claim) | ask, then book |
| Personal fit (height, swell, rota) | "Related work: {skills}. Comfort offshore is the keeper's to say." | ask |
| Interest | "Not recorded." | ask (first) |
| Missing history | "No record of {x}. Records before 1997 are incomplete." / RCOM: "The 1985–1998 radio register was never digitised." | ask or fetch |

**Never used:** appraisals, manager notes, date of birth, age, grade. One line each in the write-up.

## Stage 4: fit rules (durable)

For each posting, the requirement table marks each line `cert`, `skill`, `paperwork` or
`unknown`. Then:

- **Qualified now:** every cert and paperwork line met on the records, every essential skill at
  least moderate. Universal unknowns (medical, interest) don't block this status but appear as "to confirm".
- **Nearly:** every essential skill at least moderate, and every unmet line is closeable
  (module missing, renewal due, paperwork to fetch, one limited skill).
- **Not on these records:** an essential skill with no evidence. The wording is "not shown in
  these records", never "unsuitable".

Expected reality: almost nobody will be "qualified now" for offshore roles (OSSC, medical).
Say so in the team view: the honest headline is "nearly", and the route is the product.

## Stage 5: route (durable logic, small)

1. Collect the fit's gaps.
2. Add implied prerequisites from the graph (WAHS needs OSSC-SS in date; OSSC needs medical).
3. Topologically sort. Order ties by action: ask → fetch → book (cheapest first; a "no" to
   interest ends the route).
4. Render as numbered steps, each with its reason and evidence ids.

Example (shape, not real data): K0147 for HV Authorised Person:
1. Ask: interested in the HV role? 2. Ask: offshore medical. 3. Fetch: original internal HV
authorisation (search 2006–2019 records for {stations}; entries …). 4. Book: OSSC (all five).
5. Book: HVAP-01, HVAP-03; re-sit HVAP-02, HVAP-04 (last completed 2021, renewal lapsed 2024).

## Stage 6: outputs

- `out/answers.json`: keepers → claims, fits per posting, routes.
- `out/team.md`, for the redeployment team:
  - Per posting: qualified / nearly (ordered by route length, then evidence strength, reason shown) / count not on these records.
  - **Training buy:** the modules that, if one cohort were booked, move the most keepers from
    nearly to qualified, per posting. Counting, not optimisation.
  - **Paperwork hunt:** keepers worth reconstructing HV authorisation for (unasked finding).
  - **Opposite fit:** keepers "not on these records" for the Array who are nearly or qualified for Coastguard.
- `out/keepers/K0xxx.md`, for the keeper: their three questions answered in plain words.
  "What you're qualified for", "What you're nearly qualified for, and the steps", "What we
  couldn't tell from the records". 15 lines max. No group labels, no internal codes except entry ids.

## How you'll know it works

1. Hand-check 5 keepers end to end, including one route each. Open every cited entry.
2. 20 matched entries per high-stakes skill (HV, height, boat): count false positives, name one miss.
3. Check every route against the prerequisite graph by hand for 3 keepers.
4. Invariant tests (above).
5. Optional: recall check on 50 unmatched entries.

## Repo layout

```
README.md             run commands, thresholds, cut order, what was cut
WRITEUP.md            the one page
notes.md              working notes, time log, AI log
carrowmore/
  model.py            dataclasses + wording templates (durable)
  schemes.py          prereq graph + recompute (durable)
  route.py            topo sort + action tagging (durable)
  rules.py            skill regexes + 6 requirement tables (disposable)
  pipeline.py         load → … → render (disposable)
tests/test_invariants.py
out/answers.json, out/team.md, out/keepers/
```

Run with `python -m carrowmore.pipeline`. Stdlib only.



## Proposed solutions we passed on

| Proposed | Why passed |
|---|---|
| Ingest the raw pack (340) | Identity resolution across three eras would consume the budget |
| Numeric confidence score | No ground truth to calibrate; reads as a label, not honesty in the language |
| LLM classifier for entries | Allowed by the brief; regex is the established method for ~14 skills, and every match is explainable |
| Embedding match to NOSF | Policy language vs logbook shorthand; not the question |
| Trust the `certifications` block | Assumes renewals no record supports (confirmed by Greg) |
| Optimiser for training spend | Simple counting answers "which course first"; costs and dates aren't in the data |
| Mine appraisals and manager notes | Unreliable and private |
| Age or DOB as a fitness proxy | Wrong and discriminatory |
| UI or web app | No credit; Markdown pages carry the wording, which is what's judged |
| Database or vector store | 40 keepers, ~10k entries fit in memory |

## Expansion paths

| Expansion | Stage | What changes |
|---|---|---|
| Era 2 KEEPERLOG for all 340 | 1 | New loader; keeper codes are reliable |
| Identity resolution eras 1 and 3 | 1 | Its own reviewable step with match confidence |
| LLM-assisted matching / NOSF mapping | 2 | Second matcher behind the same `Evidence` |
| Costs and course dates | 5–6 | Training buy becomes a real plan |
| Keeper answers the "ask" items | 4–5 | Routes update; the page becomes a form |
| Team confirms or rejects claims | 3 | Ground truth that could later justify a calibrated score |
