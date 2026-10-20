"""Render the same claims three ways: answers.json, team.md, keepers/<code>.md. Disposable."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING

from .model import ClaimKind, Fit, FitStatus, Line, Step, Strength
from .postings import BY_KEY, POSTINGS
from .schemes import record_gaps

if TYPE_CHECKING:
    from .load import Keeper
    from .pipeline import KeeperResult

OPPOSITE_MIN_COURSES = 6

STATUS_WORDS = {FitStatus.READY: "ready", FitStatus.NEARLY: "nearly", FitStatus.NOT_SHOWN: "not shown in these records"}


def cite(ids: tuple[str, ...] | list[str], limit: int = 3) -> str:
    ids = list(ids)
    if not ids:
        return ""
    shown = ", ".join(ids[:limit])
    more = f" and {len(ids) - limit} more" if len(ids) > limit else ""
    return f" ({shown}{more})"


def line(ln: Line) -> str:
    return ln.text + cite(ln.evidence_ids)


def step_md(s: Step, keeper_facing: bool = False) -> str:
    """Every step text starts with its verb (Ask, Find, Look, Book, Renew, Complete, Re-sit)."""
    text = s.text
    if keeper_facing:
        for a, b in (
            ("Ask: ", "Tell us: "),
            ("Ask about ", "Tell us about "),
            ("they issued", "you issued"),
            ("If they renewed", "If you renewed"),
            ("they held", "you held"),
        ):
            text = text.replace(a, b)
    return f"{text}{cite(s.evidence_ids)}"


def you(text: str) -> str:
    """Third-person claim wording -> addressed to the keeper."""
    for a, b in (
        ("Has repeatedly done", "You have repeatedly done"),
        ("Has done", "You have done"),
        ("Was present while", "You were present while"),
        ("One logbook entry mentions", "One entry mentions"),
    ):
        if text.startswith(a):
            return b + text[len(a) :]
    return text


def requirement_lines(lines: list[Line]) -> str:
    return " ".join(f"{ln.requirement}: {line(ln)}" for ln in lines)


def rank_key(f: Fit) -> tuple:
    """Order within a status: fewest bookings, then most essential evidence, then most desirables."""
    evidence = sum(len(ln.evidence_ids) for ln in f.met)
    return (len(f.bookings), -evidence, -len(f.desirable), f.keeper)


# ---------------------------------------------------------------- answers.json


def to_json(results: list[KeeperResult], leavers: list[Keeper], facts: dict) -> dict:
    keepers = []
    for r in results:
        keepers.append(
            {
                "keeper": r.keeper.code,
                "claims": [
                    {
                        "subject": c.subject,
                        "kind": c.kind.value,
                        "strength": c.strength.value if c.strength else None,
                        "text": c.text,
                        "evidence": [
                            {
                                "entry_id": e.entry_id,
                                "date": e.date,
                                "source_record": e.source_record,
                                "role": e.role.value,
                                "depth": e.depth.value,
                                "text": None if e.withhold_text else e.text,
                            }
                            for e in c.evidence
                        ],
                    }
                    for c in r.claims
                ],
                "training": {code: s.describe() for code, s in r.schemes.items() if s.any_record},
                "fits": {
                    key: {
                        "status": f.status.value,
                        "met": [ln.__dict__ for ln in f.met],
                        "missing": [ln.__dict__ for ln in f.missing],
                        "desirable": [ln.__dict__ for ln in f.desirable],
                        "route": [
                            {
                                "key": s.key,
                                "action": s.action.value,
                                "text": s.text,
                                "because": s.because,
                                "evidence_ids": list(s.evidence_ids),
                            }
                            for s in f.route
                        ],
                        "to_confirm": [ln.__dict__ for ln in f.to_confirm],
                    }
                    for key, f in r.fits.items()
                },
            }
        )
    return {
        "as_of": 2026,
        "source": "clean/ (40 keepers); certification status recomputed from training_records",
        "excluded_keepers": [{"keeper": k.code, "reason": f"left the Authority in {k.left}"} for k in leavers],
        "pack_certifications_block_disagreements": facts["pack_block_disagreements"],
        "keepers": keepers,
    }


# ---------------------------------------------------------------- team.md


def team_md(results: list[KeeperResult], leavers: list[Keeper], facts: dict) -> str:
    by_code = {r.keeper.code: r for r in results}
    out = [
        "# Redeployment: who could do which job, and what comes first",
        "",
        f"{len(results)} keepers from `clean/` (the 40, less {len(leavers)} who have left). Six postings. "
        "Every line cites logbook entry ids; `answers.json` has the full evidence with source records.",
        "",
        "- **ready**: every requirement these records can show is met. What's left is for the keeper "
        "or the employer to confirm (interest, medical, comfort offshore).",
        "- **nearly**: the essential work is in the logbooks; the gaps are courses, renewals or paperwork.",
        "- **not shown**: an essential kind of work doesn't appear in these records. That is not the "
        "same as not having done it.",
        "",
        "| Posting | Posts | Ready | Nearly | Not shown |",
        "|---|---|---|---|---|",
    ]
    for p in POSTINGS:
        c = Counter(r.fits[p.key].status for r in results)
        out.append(
            f"| {p.title}, {p.employer} | {p.posts} | {c[FitStatus.READY]} | {c[FitStatus.NEARLY]} | "
            f"{c[FitStatus.NOT_SHOWN]} |"
        )
    ossc = [r.keeper.code for r in results if r.schemes["OSSC"].current]
    out += [
        "",
        f"Only {len(ossc)} of {len(results)} hold a current offshore safety certificate ({', '.join(ossc) or 'none'}), "
        "and medical fitness isn't recorded for anyone. So for the offshore roles the useful answer is the "
        "order of the nearly list and the route each person needs, not a list of who is ready.",
        "",
    ]

    for p in POSTINGS:
        fits = [r.fits[p.key] for r in results]
        out += [f"## {p.title}, {p.employer}", ""]
        for status in (FitStatus.READY, FitStatus.NEARLY):
            group = sorted((f for f in fits if f.status is status), key=rank_key)
            if not group:
                continue
            out += [
                f"### {STATUS_WORDS[status].capitalize()} ({len(group)})",
                "",
                "| # | Keeper | Bookings | Essential evidence | Desirable shown |",
                "|---|---|---|---|---|",
            ]
            for i, f in enumerate(group, 1):
                evidence = " ".join(line(ln) for ln in f.met) or "none needed"
                out.append(
                    f"| {i} | [{f.keeper}](keepers/{f.keeper}.md) | {len(f.bookings)} | {evidence} | "
                    f"{len(f.desirable)} |"
                )
            out.append("")
        not_shown = [f for f in fits if f.status is FitStatus.NOT_SHOWN]
        if not_shown:
            by_req: dict[str, list[str]] = {}
            for f in not_shown:
                by_req.setdefault(f.missing[0].requirement, []).append(f.keeper)
            out.append(f"**Not shown in these records ({len(not_shown)}):**")
            out += [f"- {req}: {', '.join(codes)}" for req, codes in by_req.items()]
            out.append("")
    out += training_buy(results)
    out += hv_hunt(results)
    out += opposite_fit(results, by_code)
    out += pack_block(facts)
    out += [
        "## Left out on purpose",
        "",
        *[f"- {k.code}: left the Authority in {k.left}, so not among the 340." for k in leavers],
        "- Appraisals and station manager notes: not read. They hold private matters and say nothing a "
        "logbook entry doesn't say better.",
        "- Date of birth, age and grade: not loaded. Age isn't evidence of fitness; grade follows length of service.",
        "- Entries about disciplining another person are excluded from every claim.",
        "- Casualty-care entries count as evidence, but their text is never shown because it describes "
        "someone else's injury. Only the entry ids appear.",
        "",
    ]
    return "\n".join(out)


def training_buy(results: list[KeeperResult]) -> list[str]:
    out = [
        "## Training to buy",
        "",
        "For each posting: which booking the most nearly keepers need, and how many keepers it would "
        "leave with no bookings at all. Counting only; costs and dates aren't in the data.",
        "",
    ]
    for p in POSTINGS:
        nearly = [r.fits[p.key] for r in results if r.fits[p.key].status is FitStatus.NEARLY]
        if not nearly:
            continue
        need = Counter(s.key for f in nearly for s in f.bookings)
        last = Counter(f.bookings[0].key for f in nearly if len(f.bookings) == 1)
        if not need:
            continue
        top = ", ".join(f"{k} ({n})" for k, n in need.most_common(6))
        out.append(f"- **{p.title}**: {top}.")
        if last:
            out.append("  - One booking from ready: " + ", ".join(f"{k} for {n}" for k, n in last.most_common()) + ".")
    out.append("")
    return out


def hv_hunt(results: list[KeeperResult]) -> list[str]:
    rows = []
    for r in results:
        step = next((s for s in r.fits["hv_ap"].route if s.key == "HV-paperwork"), None)
        if step:
            authority = step.text.startswith("Find the original")
            rows.append((not authority, -len(step.evidence_ids), r.keeper.code, step))
    if not rows:
        return []
    out = [
        "## Unasked: whose HV paperwork is worth reconstructing",
        "",
        "The HV Authorised Person posting fails most applicants on documented switching experience. "
        "The Board accepts a lapsed internal authorisation instead, but only with documents, and the "
        "Array says it has had some success reconstructing them. These keepers' logbooks show them doing "
        "the switching (not standing by while someone else did). Those listed first issued switching "
        "documents or held the HV keys, which suggests they held an authorisation at the time.",
        "",
    ]
    for *_, code, step in sorted(rows, key=lambda row: row[:3]):
        out.append(f"- [{code}](keepers/{code}.md): {step.text}{cite(step.evidence_ids)}")
    out.append("")
    return out


def opposite_fit(results: list[KeeperResult], by_code: dict) -> list[str]:
    rows = []
    for r in results:
        cg, om = r.fits["coastguard"], r.fits["array_om"]
        if cg.status is FitStatus.READY and len(cg.desirable) >= 2 and len(om.bookings) >= OPPOSITE_MIN_COURSES:
            rows.append((-len(cg.desirable), r.keeper.code, cg, om))
    if not rows:
        return []
    out = [
        "## Unasked: the job that wants the opposite",
        "",
        "The Array wants offshore tickets and physical capability. The Coastguard calls both irrelevant "
        "and wants the watchkeeping, radio and record-keeping keepers did every day. These keepers need "
        f"{OPPOSITE_MIN_COURSES} or more courses before the Array can mobilise them, but the records "
        "already show everything the Coastguard can check, plus at least two of its desirables.",
        "",
    ]
    for _, code, cg, om in sorted(rows):
        out.append(
            f"- [{code}](keepers/{code}.md): the Array needs {len(om.bookings)} courses first. For the "
            "Coastguard: " + " ".join(line(ln) for ln in cg.desirable)
        )
    out.append("")
    return out


def pack_block(facts: dict) -> list[str]:
    rows = facts["pack_block_disagreements"]
    if not rows:
        return []
    out = [
        "## Unasked: the pack's certificate summary is optimistic",
        "",
        "`clean/keepers.json` has a precomputed `certifications` block. Its award years assume renewals "
        "that no training record supports (the data team confirmed this). This system ignores it and "
        f"recomputes from the records. Where the block says a certificate is valid in 2026 and the records "
        f"don't support it ({len(rows)}):",
        "",
        "| Keeper | Scheme | Block says | Records say |",
        "|---|---|---|---|",
    ]
    out += [f"| {r['keeper']} | {r['scheme']} | {r['pack_says']} | {r['records_say']} |" for r in rows]
    out.append("")
    return out


# ---------------------------------------------------------------- keepers/<code>.md


def keeper_md(r: KeeperResult) -> str:
    k = r.keeper
    done = [c for c in r.claims if c.kind is ClaimKind.HAS_DONE and c.strength is not Strength.LIMITED]
    done.sort(key=lambda c: (-c.strength.rank, -len(c.evidence)))
    out = [
        f"# {k.name} ({k.code})",
        "",
        "This page is built only from your station logbooks and training records. "
        "Each line names the logbook entries it comes from, so you can check it and tell us where it's wrong.",
        "",
    ]
    out += ["## What your logbooks show", ""]
    out += [f"- {you(c.text)}{cite([e.entry_id for e in c.evidence])}" for c in done[:8]] or [
        "- Nothing we could match."
    ]
    out.append("")

    ready = [f for f in r.fits.values() if f.status is FitStatus.READY]
    nearly = sorted((f for f in r.fits.values() if f.status is FitStatus.NEARLY), key=lambda f: len(f.bookings))
    out += ["## Jobs you could apply for now", ""]
    if ready:
        for f in ready:
            p = BY_KEY[f.posting]
            out.append(
                f"- **{p.title}, {p.employer}.** Your records show what they ask for. "
                "They will want to check for themselves:"
            )
            out += [f"  - {ln.requirement}" for ln in f.to_confirm]
    else:
        out.append("- None on these records alone. That usually means a certificate, not a lack of experience.")
    out.append("")

    out += ["## Jobs you're close to, and the steps in order", ""]
    if not nearly:
        out.append("- None on these records.")
    for f in nearly:
        p = BY_KEY[f.posting]
        steps = [s for s in f.route if s.key != "interest"]
        n = len(f.bookings)
        count = "no courses needed" if n == 0 else "1 course or renewal" if n == 1 else f"{n} courses or renewals"
        out.append(f"**{p.title}, {p.employer}**: {count}.")
        out += [f"{i}. {step_md(s, keeper_facing=True)}" for i, s in enumerate(steps, 1)]
        out.append("")

    trained = [s.describe() for s in r.schemes.values() if s.any_record]
    out += ["## Your training record", ""] + [f"- {t}" for t in trained] + [""]
    out += [
        "## What we couldn't tell from the records",
        "",
        "- Whether you want any of these jobs.",
        "- Your medical fitness, and how you feel about heights, enclosed spaces and small boats offshore.",
        "- Anything you did that nobody wrote down, or that went into a record we don't have.",
    ]
    out += [f"- {n}" for n in record_gaps(k)]
    out.append("")
    return "\n".join(out)


def render_all(results: list[KeeperResult], leavers: list[Keeper], facts: dict, out: Path) -> list[Path]:
    (out / "keepers").mkdir(parents=True, exist_ok=True)
    written = []
    p = out / "answers.json"
    p.write_text(json.dumps(to_json(results, leavers, facts), indent=1, ensure_ascii=False), encoding="utf-8")
    written.append(p)
    p = out / "team.md"
    p.write_text(team_md(results, leavers, facts), encoding="utf-8")
    written.append(p)
    for r in results:
        p = out / "keepers" / f"{r.keeper.code}.md"
        p.write_text(keeper_md(r), encoding="utf-8")
    written.append(out / "keepers" / f"({len(results)} pages)")
    return written
