"""Keeper x posting -> Fit: ready, nearly or not shown, with the route. Durable rules:

- ready      every essential line the records can show is met. Things only the keeper or
             the employer can tell (interest, medical, comfort at height) never block it,
             and are listed under "to confirm".
- nearly     every essential kind of work is shown at the required strength (or is shown
             once and becomes a question), and every certificate gap is closeable.
- not shown  an essential kind of work does not appear in these records. Worded as
             "not shown in these records", never as unsuitable.
"""

from __future__ import annotations

from .claims import done, has_done, present, span
from .load import Keeper
from .model import Action, Claim, Evidence, Fit, FitStatus, Line, Step, Strength
from .postings import Posting, Req
from .route import order
from .schemes import ATTENDANCE_UNRELIABLE_BEFORE, SchemeStatus, record_gaps
from .skills import kv_levels, label

AUTHORITY_PATTERNS = ("authorised the switching programme", "acted as issuing authority", "held the keys")

INTEREST = Step("interest", Action.ASK, "Ask whether they want this job.")
MEDICAL = Step("medical", Action.BOOK, "Book an offshore medical. Medical fitness is not recorded for anyone.")


def ids(evidence: list[Evidence]) -> tuple[str, ...]:
    return tuple(e.entry_id for e in evidence)


# Training modules that count as training in a skill. HV switching is deliberately absent:
# the HVAP course is not the documented experience the posting asks for.
SKILL_TRAINING = {
    "boat": ("SMOC-BH",),
    "radio": ("RCOM-GEN", "RCOM-DSC"),
    "met_obs": ("RCOM-MET",),
    "electrical": ("MECS-1", "MECS-5"),
    "fault_finding": ("MECS-3",),
    "generating_plant": ("MECS-2", "MPMC-A"),
    "mechanical": ("MPMC-A", "MPMC-B", "MPMC-D"),
    "hydraulics": ("MPMC-C",),
    "lifting": ("LOSC-S", "LOSC-A"),
    "aton": ("ANSM-O", "ANSM-C", "ANSM-E"),
}


def training_for(skills: tuple[str, ...], schemes: dict[str, SchemeStatus]) -> str:
    """Completed modules relevant to any of `skills`, as text: "SMOC-BH 2008"."""
    found = []
    for skill in skills:
        for code in SKILL_TRAINING.get(skill, ()):
            m = schemes[code.split("-")[0]].modules[code]
            if m.held:
                found.append(f"{code} {m.last_completed}")
    return ", ".join(sorted(set(found)))


def best_claim(keeper: str, req: Req, evidence: dict[str, list[Evidence]]) -> Claim | None:
    claims = [has_done(keeper, s, evidence.get(s, []), req.depth) for s in req.skills]
    claims = [c for c in claims if c]
    return max(claims, key=lambda c: (c.strength.rank, len(c.evidence)), default=None)


def module_step(scheme: SchemeStatus, code: str) -> Step:
    m = scheme.modules[code]
    if m.held:
        return Step(
            code,
            Action.BOOK,
            f"Renew {code} ({m.name}): last completed {m.last_completed}, now out of date.",
            because=scheme.describe(),
        )
    if m.attended and max(m.attended) < ATTENDANCE_UNRELIABLE_BEFORE:
        return Step(
            code,
            Action.FETCH,
            f"Look for a completion certificate for {code} ({m.name}). The record says attended in "
            f"{max(m.attended)}, and before {ATTENDANCE_UNRELIABLE_BEFORE} the training system did not "
            "separate attending from completing. If there is none, book it.",
            because=scheme.describe(),
        )
    if m.attended:
        return Step(
            code,
            Action.BOOK,
            f"Complete {code} ({m.name}): attended {max(m.attended)}, no completion recorded.",
            because=scheme.describe(),
        )
    if m.failed:
        return Step(code, Action.BOOK, f"Re-sit {code} ({m.name}): failed {max(m.failed)}.", because=scheme.describe())
    return Step(code, Action.BOOK, f"Book {code} ({m.name}).", because=scheme.describe())


def cert_steps(scheme: SchemeStatus, modules: tuple[str, ...]) -> list[Step]:
    """What it takes to hold `modules` (or the whole scheme) and have it current."""
    if not modules:
        if scheme.current:
            return []
        if scheme.complete:
            return [
                Step(
                    f"{scheme.code}-renewal",
                    Action.BOOK,
                    f"Renew {scheme.code}: {scheme.describe().split(': ', 1)[1]} If they renewed "
                    "somewhere we have no record of, the certificate replaces this step.",
                    because=scheme.describe(),
                )
            ]
        # Held modules count toward completing the scheme; validity starts at the award.
        return [module_step(scheme, m.code) for m in scheme.missing]
    # A named subset (e.g. the WAHS modules the Array needs) must itself be in date.
    return [module_step(scheme, c) for c in modules if not scheme.module_current(c)]


def prerequisite_steps(steps: dict[str, Step], schemes: dict[str, SchemeStatus], offshore: bool) -> None:
    """Add the steps the scheme rules imply (see route.py), in place."""
    if offshore:
        steps.setdefault("medical", MEDICAL)
    keys = set(steps)
    needs_ossc_ss = any(k.split("-")[0] in ("WAHS", "SMOC") for k in keys)
    if needs_ossc_ss and "OSSC-SS" not in keys and not schemes["OSSC"].module_current("OSSC-SS"):
        s = module_step(schemes["OSSC"], "OSSC-SS")
        steps["OSSC-SS"] = Step(s.key, s.action, s.text + " WAHS and SMOC both need it in date.", s.because)
    if any(k.startswith("HVAP") for k in keys):
        mecs = schemes["MECS"]
        for i in range(1, 4):
            code = f"MECS-{i}"
            if not mecs.modules[code].held:
                s = module_step(mecs, code)
                steps[code] = Step(s.key, s.action, s.text + " HVAP needs MECS at stage 3.", s.because)
    if any(k.startswith("OSSC") for k in steps) and "medical" not in steps:
        steps["medical"] = Step(
            "medical",
            Action.BOOK,
            "Book an offshore medical: the OSSC course needs a current declaration, even though this "
            "employer doesn't ask for one.",
        )


def hv_paperwork_step(evidence: list[Evidence]) -> Step:
    ev = done(evidence)
    authority = [e for e in ev if any(p in e.text.lower() for p in AUTHORITY_PATTERNS)]
    stations = sorted({e.station for e in ev})
    kv = kv_levels(ev)
    voltage = (
        f" Voltage is stated in some entries ({', '.join(f'{v}kV' for v in kv)})."
        if kv
        else (" No entry states the voltage, and the posting needs 11kV or above.")
    )
    if authority:
        a_stations = sorted({e.station for e in authority})
        n = "1 entry" if len(authority) == 1 else f"{len(authority)} entries"
        text = (
            f"Find the original internal HV authorisation. In {n} ({span(authority)}) they issued "
            "switching documents or held the HV keys, which normally only an authorised person does. "
            "The Board accepts a lapsed authorisation only with documents: start with the records for "
            f"{', '.join(a_stations)}."
        )
        return Step("HV-paperwork", Action.FETCH, text + voltage, evidence_ids=ids(authority))
    text = (
        f"Find documents for the switching work: {len(ev)} logbook entries at {', '.join(stations)}, "
        f"{span(ev)}. The Board needs two years of documented switching; logbook lines "
        "show where to look but are not the documents."
    )
    return Step("HV-paperwork", Action.FETCH, text + voltage, evidence_ids=ids(ev))


def assess(
    keeper: Keeper,
    posting: Posting,
    evidence: dict[str, list[Evidence]],
    schemes: dict[str, SchemeStatus],
) -> Fit:
    met: list[Line] = []
    missing: list[Line] = []
    desirable: list[Line] = []
    to_confirm: list[Line] = []
    steps: dict[str, Step] = {"interest": INTEREST}

    for req in posting.reqs:
        if req.kind == "cert":
            scheme = schemes[req.scheme]
            gaps = cert_steps(scheme, req.modules)
            if gaps:
                for s in gaps:
                    steps[s.key] = s
            else:
                (met if req.essential else desirable).append(Line(req.text, scheme.describe()))
            if req.note:
                to_confirm.append(Line(req.text, req.note))
            if gaps and not scheme.any_record:
                for note in record_gaps(keeper, req.scheme):
                    to_confirm.append(Line(req.text, f"No {req.scheme} record. {note}"))

        elif req.kind == "skill":
            claim = best_claim(keeper.code, req, evidence)
            if claim and claim.strength.rank >= req.min_strength.rank:
                (met if req.essential else desirable).append(Line(req.text, claim.text, ids(claim.evidence)))
            elif req.essential and claim:
                met.append(Line(req.text, claim.text, ids(claim.evidence)))
                steps[f"check-{req.skills[0]}"] = Step(
                    f"check-{req.skills[0]}",
                    Action.ASK,
                    f"Ask about {label(req.skills[0])}: the logbooks show it only once.",
                    evidence_ids=ids(claim.evidence),
                )
            elif req.essential and (trained := training_for(req.skills, schemes)):
                met.append(Line(req.text, f"Trained ({trained}), but the logbooks don't show the work."))
                key = f"check-{req.skills[0]}"
                steps[key] = Step(
                    key, Action.ASK, f"Ask about {label(req.skills[0])}: trained ({trained}), no logbook entries."
                )
            elif req.essential:
                missing.append(Line(req.text, "Not shown in these records."))

        elif req.kind == "paperwork":
            ev = evidence.get(req.skills[0], [])
            claim = has_done(keeper.code, req.skills[0], ev, req.depth)
            if claim and claim.strength.rank >= req.min_strength.rank:
                met.append(Line(req.text, f"{claim.text} Not authorised on these records.", ids(claim.evidence)))
                steps["HV-paperwork"] = hv_paperwork_step(ev)
            else:
                seen = present(keeper.code, req.skills[0], ev)
                why = f" {seen.text}" if seen else ""
                missing.append(Line(req.text, f"Not shown in these records.{why}", ids(seen.evidence) if seen else ()))

        elif req.kind == "ask":
            related = [has_done(keeper.code, s, evidence.get(s, [])) for s in req.related]
            related = [c for c in related if c and c.strength is not Strength.LIMITED]
            text = " ".join(filter(None, [req.note, *(f"Related: {c.text}" for c in related)]))
            to_confirm.append(Line(req.text, text, tuple(i for c in related for i in ids(c.evidence[:3]))))
            if not req.note:  # a note means the employer assesses it, not a question for the keeper
                key = f"ask-{posting.reqs.index(req)}"
                steps[key] = Step(key, Action.ASK, f"Ask: {req.text.lower()}?")

    prerequisite_steps(steps, schemes, posting.offshore)
    route = order(list({s.key: s for s in steps.values()}.values()))

    if missing:
        status = FitStatus.NOT_SHOWN
    elif any(s.action is not Action.ASK and s.key != "medical" for s in route) or any(
        s.key.startswith("check-") for s in route
    ):
        status = FitStatus.NEARLY
    else:
        status = FitStatus.READY
    return Fit(keeper.code, posting.key, status, met, missing, desirable, route, to_confirm)
