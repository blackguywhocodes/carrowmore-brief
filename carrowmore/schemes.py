"""Recompute certification status from training records. Durable.

The clean pack's `certifications` block is ignored: its awarded years assume renewals that
no record supports (confirmed by the data team via Greg Davis). Rules used here:

- A module is held if it has a `completed` record.
- A scheme is complete when every module is held. It is awarded in the year its last
  module was completed, and is current while AS_OF_YEAR <= award + renewal period.
  Lifetime schemes (no renewal period) stay current.
- MECS stage is the highest consecutive module completed (the scheme's own rule).
- Before 2011 the training system did not separate attendance from completion, so an
  `attended` record from then may be a completion that was never recorded as one.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .load import Keeper
from .model import AS_OF_YEAR

ATTENDANCE_UNRELIABLE_BEFORE = 2011
NOT_DIGITISED_BEFORE = 1994
MIGRATION_YEAR = 1997
RCOM_REGISTER_GAP = (1985, 1998)


@dataclass
class ModuleStatus:
    code: str
    name: str
    completed: list[int] = field(default_factory=list)
    attended: list[int] = field(default_factory=list)
    failed: list[int] = field(default_factory=list)

    @property
    def held(self) -> bool:
        return bool(self.completed)

    @property
    def last_completed(self) -> int | None:
        return max(self.completed) if self.completed else None


@dataclass
class SchemeStatus:
    code: str
    name: str
    renewal_years: int | None
    modules: dict[str, ModuleStatus]

    @property
    def missing(self) -> list[ModuleStatus]:
        return [m for m in self.modules.values() if not m.held]

    @property
    def complete(self) -> bool:
        return not self.missing

    @property
    def awarded(self) -> int | None:
        return max(m.last_completed for m in self.modules.values()) if self.complete else None

    @property
    def expires(self) -> int | None:
        if self.awarded is None or self.renewal_years is None:
            return None
        return self.awarded + self.renewal_years

    @property
    def current(self) -> bool:
        return self.complete and (self.expires is None or AS_OF_YEAR <= self.expires)

    @property
    def any_record(self) -> bool:
        return any(m.completed or m.attended or m.failed for m in self.modules.values())

    def module_current(self, code: str) -> bool:
        """A single module completed within the scheme's renewal period (used for OSSC-SS)."""
        m = self.modules[code]
        if not m.held:
            return False
        return self.renewal_years is None or AS_OF_YEAR <= m.last_completed + self.renewal_years

    def mecs_stage(self) -> int:
        stage = 0
        for i in range(1, len(self.modules) + 1):
            if not self.modules[f"{self.code}-{i}"].held:
                break
            stage = i
        return stage

    def describe(self) -> str:
        """One plain sentence: what the training records say about this scheme."""
        held = [m.code for m in self.modules.values() if m.held]
        if not self.any_record:
            return f"{self.code}: no training record."
        if self.current:
            until = "lifetime award" if self.expires is None else f"current to {self.expires}"
            return f"{self.code}: all modules completed, last in {self.awarded}; {until}."
        if self.complete:
            return (
                f"{self.code}: all modules completed, last in {self.awarded}; renewal was due "
                f"{self.expires} and no renewal is on record."
            )
        parts = [f"{self.code}: {len(held)} of {len(self.modules)} modules completed"]
        if held:
            parts[0] += f" ({', '.join(held)})"
        for m in self.missing:
            if m.attended:
                parts.append(f"{m.code} attended {max(m.attended)}, no completion recorded")
            elif m.failed:
                parts.append(f"{m.code} failed {max(m.failed)}")
        if self.code == "MECS":
            parts.append(f"stage {self.mecs_stage()}")
        return "; ".join(parts) + "."


def recompute(keeper: Keeper, schemes: dict[str, dict]) -> dict[str, SchemeStatus]:
    out = {}
    for code, s in schemes.items():
        modules = {m["code"]: ModuleStatus(m["code"], m["name"]) for m in s["modules"]}
        for r in keeper.training:
            m = modules.get(r["module"]) if r["scheme"] == code else None
            if m is None:
                continue
            {"completed": m.completed, "attended": m.attended, "failed": m.failed}[r["outcome"]].append(r["year"])
        out[code] = SchemeStatus(code, s["name"], s["renewal_years"], modules)
    return out


def record_gaps(keeper: Keeper, scheme: str | None = None) -> list[str]:
    """Why a missing training record is not proof of absence, for this keeper."""
    notes = []
    if keeper.joined < NOT_DIGITISED_BEFORE:
        notes.append(f"Training before {NOT_DIGITISED_BEFORE} was never digitised.")
    if keeper.joined <= MIGRATION_YEAR:
        notes.append(
            f"In service during the {MIGRATION_YEAR} records migration, which lost about a "
            "quarter of the workforce's training records."
        )
    if scheme == "RCOM" and keeper.joined <= RCOM_REGISTER_GAP[1]:
        notes.append("The 1985–1998 radio certificate register was never digitised.")
    return notes


def pack_block_disagreements(raw_keepers: list[dict], recomputed: dict[str, dict[str, SchemeStatus]]) -> list[dict]:
    """Where the pack's precomputed certifications block says valid and the records don't."""
    rows = []
    for r in raw_keepers:
        mine = recomputed.get(r["keeper_code"], {})
        for c in r.get("certifications", []):
            status = mine.get(c["scheme"])
            if c.get("valid_2026") and status and not status.current:
                rows.append(
                    {
                        "keeper": r["keeper_code"],
                        "scheme": c["scheme"],
                        "pack_says": f"awarded {c['awarded_year']}, expires {c['expires_year']}",
                        "records_say": status.describe(),
                    }
                )
    return rows
