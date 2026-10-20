"""Order a keeper's steps: scheme prerequisites first, then ask -> fetch -> book. Durable.

The prerequisites come from certification_schemes.json, where they are prose; they are
encoded here by hand:
  OSSC  needs a current offshore medical declaration
  WAHS  needs OSSC-SS within its validity
  SMOC  needs OSSC-SS within its validity
  HVAP  needs MECS at stage 3, and documented switching experience or a documented authorisation
  MECS  is cumulative: stage n needs stage n-1
  LOSC-P needs LOSC-S and LOSC-A
Assumption: the medical applies to each OSSC module, not only to the full certificate.
"""

from __future__ import annotations

from graphlib import TopologicalSorter

from .model import Step


class RouteError(ValueError):
    pass


def depends_on(key: str, present: set[str]) -> set[str]:
    """Which of the steps in `present` must come before `key`."""
    scheme = key.split("-")[0]
    deps: set[str] = set()
    if key != "interest":
        deps.add("interest")
    if scheme == "OSSC":
        deps.add("medical")
    if scheme in ("WAHS", "SMOC"):
        deps.add("OSSC-SS")
    if scheme == "HVAP":
        deps |= {"MECS-1", "MECS-2", "MECS-3", "HV-paperwork"}
    if scheme == "MECS" and key[-1].isdigit():
        deps |= {f"MECS-{i}" for i in range(1, int(key[-1]))}
    if key == "LOSC-P":
        deps |= {"LOSC-S", "LOSC-A"}
    return deps & present


def order(steps: list[Step]) -> list[Step]:
    """Topological order (Kahn's algorithm). Among steps free to go next: ask before fetch
    before book, so the cheap questions that could end a route come first; then the step
    that unblocks the most others."""
    pending = {s.key: s for s in steps}
    if len(pending) != len(steps):
        raise RouteError("duplicate step keys")
    present = set(pending)
    TopologicalSorter({k: depends_on(k, present) for k in present}).prepare()  # raises on a cycle
    unblocks = {k: sum(k in depends_on(other, present) for other in present) for k in present}
    done: set[str] = set()
    out: list[Step] = []
    while pending:
        ready = [k for k in pending if depends_on(k, present) <= done]
        k = min(ready, key=lambda k: (pending[k].action.rank, -unblocks[k], k))
        out.append(pending.pop(k))
        done.add(k)
    return out


def check(route: list[Step]) -> None:
    """Invariant: no step appears before a step it depends on."""
    seen: set[str] = set()
    keys = {s.key for s in route}
    for s in route:
        missing = depends_on(s.key, keys) - seen
        if missing:
            raise RouteError(f"{s.key} comes before {sorted(missing)}")
        seen.add(s.key)
