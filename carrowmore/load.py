"""Read clean/ and the scheme file. Disposable: a raw-pack loader would replace this."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

# Fields we read on purpose. Date of birth, grade and grade history are never loaded:
# age is not evidence of fitness, and the pack README says grade follows length of
# service, not assessment.
KEEPER_FIELDS = ("keeper_code", "name", "date_joined", "date_left", "status", "postings", "training_records")


@dataclass
class Keeper:
    code: str
    name: str
    joined: int
    left: int | None
    status: str
    postings: list[dict]
    training: list[dict]

    @property
    def current(self) -> bool:
        return self.status == "current"

    def years_at(self, station_classes: set[str]) -> int:
        return sum(p["to_year"] - p["from_year"] + 1 for p in self.postings if p["station_class"] in station_classes)


@dataclass(frozen=True)
class Entry:
    entry_id: str
    date: str
    keeper: str
    station: str
    station_class: str
    source_record: str
    text: str


def load_keepers(pack: Path) -> dict[str, Keeper]:
    raw = json.loads((pack / "clean" / "keepers.json").read_text(encoding="utf-8"))
    keepers = {}
    for r in raw:
        r = {k: r[k] for k in KEEPER_FIELDS}
        keepers[r["keeper_code"]] = Keeper(
            code=r["keeper_code"],
            name=r["name"],
            joined=int(r["date_joined"][:4]),
            left=int(r["date_left"][:4]) if r["date_left"] else None,
            status=r["status"],
            postings=r["postings"],
            training=r["training_records"],
        )
    return keepers


def load_entries(pack: Path) -> dict[str, list[Entry]]:
    raw = json.loads((pack / "clean" / "logbook_entries.json").read_text(encoding="utf-8"))
    by_keeper: dict[str, list[Entry]] = defaultdict(list)
    for r in raw:
        by_keeper[r["keeper_code"]].append(
            Entry(
                entry_id=r["entry_id"],
                date=r["date"],
                keeper=r["keeper_code"],
                station=r["station"],
                station_class=r["station_class"],
                source_record=r["source_record"],
                text=r["text"],
            )
        )
    return dict(by_keeper)


def load_schemes(pack: Path) -> dict[str, dict]:
    raw = json.loads((pack / "employers" / "certification_schemes.json").read_text(encoding="utf-8"))
    return {s["code"]: s for s in raw["schemes"]}
