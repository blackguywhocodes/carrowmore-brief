"""Print every distinct logbook phrasing with what the skill rules make of it.

The clean extract has about 10,600 entries but only about 620 distinct phrasings once digits
and case are normalised. Listing all of them lets a person check the rules completely,
including what they miss, instead of sampling.

    python -m carrowmore.audit [path/to/carrowmore-data-pack]
"""

from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from .load import load_entries
from .skills import classify


def normalise(text: str) -> str:
    return re.sub(r"\d+", "#", text.lower())


def main(pack: Path, out: Path) -> None:
    entries = [e for es in load_entries(pack).values() for e in es]
    counts: Counter[str] = Counter()
    example: dict[str, tuple[str, str]] = {}  # phrasing -> (entry_id, original text)
    for e in entries:
        key = normalise(e.text)
        counts[key] += 1
        example.setdefault(key, (e.entry_id, e.text))

    rows: dict[str, list[str]] = defaultdict(list)
    for phrasing, n in counts.most_common():
        entry_id, text = example[phrasing]
        result = classify(text)  # the rules see real text, digits included
        if result is None:
            rows["excluded"].append(f"| {n} | {phrasing} | {entry_id} | excluded: about another person |")
            continue
        role, skills = result
        if not skills:
            rows["unmatched"].append(f"| {n} | {phrasing} | {entry_id} | |")
            continue
        tags = ", ".join(f"{k} ({d.value})" for k, d in sorted(skills.items()))
        rows["matched"].append(f"| {n} | {phrasing} | {entry_id} | {role.value}: {tags} |")

    matched_entries = sum(int(r.split("|")[1]) for r in rows["matched"])
    lines = [
        "# Rule audit",
        "",
        f"{len(entries)} entries, {len(counts)} distinct phrasings (digits and case normalised).",
        f"Matched: {len(rows['matched'])} phrasings covering {matched_entries} entries. "
        f"Unmatched: {len(rows['unmatched'])}. Excluded: {len(rows['excluded'])}.",
        "",
        "Read the unmatched list for misses and the matched list for false positives.",
        "",
    ]
    for section in ("matched", "unmatched", "excluded"):
        lines += [f"## {section.title()}", "", "| n | phrasing | example | result |", "|---|---|---|---|"]
        lines += rows[section] + [""]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out}: {len(rows['matched'])} matched, {len(rows['unmatched'])} unmatched phrasings")


if __name__ == "__main__":
    pack = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("carrowmore-data-pack")
    main(pack, Path("out/rule_audit.md"))
