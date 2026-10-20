"""load -> match -> claims -> assess + route -> render.

python -m carrowmore.pipeline [path/to/carrowmore-data-pack] [--out out]
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from .assess import assess
from .claims import skill_claims
from .load import Keeper, load_entries, load_keepers, load_schemes
from .model import Claim, Evidence, Fit
from .postings import POSTINGS
from .render import render_all
from .route import check
from .schemes import SchemeStatus, pack_block_disagreements, recompute
from .skills import match


@dataclass
class KeeperResult:
    keeper: Keeper
    evidence: dict[str, list[Evidence]]
    claims: list[Claim]
    schemes: dict[str, SchemeStatus]
    fits: dict[str, Fit]


def run(pack: Path) -> tuple[list[KeeperResult], list[Keeper], dict]:
    keepers = load_keepers(pack)
    entries = load_entries(pack)
    scheme_defs = load_schemes(pack)

    results, leavers = [], []
    for k in keepers.values():
        if not k.current:
            leavers.append(k)  # not among the 340 being redeployed
            continue
        evidence = match(entries.get(k.code, []))
        schemes = recompute(k, scheme_defs)
        fits = {p.key: assess(k, p, evidence, schemes) for p in POSTINGS}
        for f in fits.values():
            check(f.route)
        results.append(KeeperResult(k, evidence, skill_claims(k.code, evidence), schemes, fits))

    raw = json.loads((pack / "clean" / "keepers.json").read_text(encoding="utf-8"))
    facts = {
        "entries": sum(len(v) for v in entries.values()),
        "pack_block_disagreements": pack_block_disagreements(raw, {r.keeper.code: r.schemes for r in results}),
    }
    return results, leavers, facts


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pack", nargs="?", default="carrowmore-data-pack", type=Path)
    ap.add_argument("--out", default="out", type=Path)
    args = ap.parse_args()
    results, leavers, facts = run(args.pack)
    written = render_all(results, leavers, facts, args.out)
    for path in written:
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
