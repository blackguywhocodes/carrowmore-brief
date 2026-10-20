"""Evidence -> claims, with strength rules and fixed wording. Durable.

Strength is ordinal and rule-based, never a score:
  strong   >= 5 entries across >= 3 distinct years, the latest within 10 years
  moderate >= 2 entries (or strong, but nothing in the last 10 years)
  limited  1 entry
Entries where the keeper only stood by or witnessed never count; they become a separate
PRESENT claim so the difference is visible.
"""

from __future__ import annotations

from .model import AS_OF_YEAR, Claim, ClaimKind, Depth, Evidence, Role, Strength
from .skills import label

RECENT_YEARS = 10


def done(evidence: list[Evidence], depth: Depth | None = None) -> list[Evidence]:
    """Entries where the keeper did or led the work, optionally only skilled ones."""
    out = [e for e in evidence if e.role in (Role.PERFORMED, Role.LED)]
    if depth is Depth.SKILLED:
        out = [e for e in out if e.depth is Depth.SKILLED]
    return out


def strength(evidence: list[Evidence]) -> Strength | None:
    if not evidence:
        return None
    years = {e.year for e in evidence}
    recent = max(years) >= AS_OF_YEAR - RECENT_YEARS
    if len(evidence) >= 5 and len(years) >= 3 and recent:
        return Strength.STRONG
    if len(evidence) >= 2:
        return Strength.MODERATE
    return Strength.LIMITED


def span(evidence: list[Evidence]) -> str:
    years = sorted({e.year for e in evidence})
    return str(years[0]) if len(years) == 1 else f"{years[0]}–{years[-1]}"


def has_done(keeper: str, skill: str, evidence: list[Evidence], depth: Depth | None = None) -> Claim | None:
    ev = sorted(done(evidence, depth), key=lambda e: e.date)
    s = strength(ev)
    if s is None:
        return None
    what = label(skill)
    led = [e for e in ev if e.role is Role.LED]
    skilled = [e for e in ev if e.depth is Depth.SKILLED]
    details = []
    if led:
        details.append(f"{len(led)} in charge or teaching others")
    if depth is None and skilled and len(skilled) < len(ev):
        details.append(
            f"{len(skilled)} {'was a repair or skilled job' if len(skilled) == 1 else 'were repairs or skilled jobs'}"
        )
    if s is not Strength.LIMITED and ev[-1].year < AS_OF_YEAR - RECENT_YEARS:
        details.append(f"nothing since {ev[-1].year}")
    extra = f" ({'; '.join(details)})" if details else ""
    if s is Strength.STRONG:
        text = f"Has repeatedly done {what}: {len(ev)} entries, {span(ev)}{extra}."
    elif s is Strength.MODERATE:
        text = f"Has done {what}: {len(ev)} entries, {span(ev)}{extra}."
    else:
        text = f"One logbook entry mentions {what} ({ev[0].year}){extra}."
    return Claim(keeper, skill, ClaimKind.HAS_DONE, text, s, ev)


def present(keeper: str, skill: str, evidence: list[Evidence]) -> Claim | None:
    ev = sorted((e for e in evidence if e.role is Role.OBSERVED), key=lambda e: e.date)
    if not ev:
        return None
    text = (
        f"Was present while someone else did {label(skill)}: {len(ev)} entries, {span(ev)}. "
        "This is not counted as doing it."
    )
    return Claim(keeper, skill, ClaimKind.PRESENT, text, None, ev)


def skill_claims(keeper: str, evidence_by_skill: dict[str, list[Evidence]]) -> list[Claim]:
    claims = []
    for skill, ev in sorted(evidence_by_skill.items()):
        for c in (has_done(keeper, skill, ev), present(keeper, skill, ev)):
            if c:
                claims.append(c)
    return claims
