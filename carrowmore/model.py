"""The claim model. This is the durable part: everything else feeds it or renders it."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

AS_OF_YEAR = 2026


class ClaimKind(Enum):
    HAS_DONE = "has_done"  # logbook entries show the keeper doing the work
    PRESENT = "present"  # logbook shows the keeper there while someone else did it
    TRAINED = "trained"  # a training record exists for a module
    SCHEME = "scheme"  # recomputed position in a certification scheme
    NO_RECORD = "no_record"  # looked and found nothing; never "didn't do it"
    UNKNOWN = "unknown"  # not answerable from these records at all


class Strength(Enum):
    STRONG = "strong"
    MODERATE = "moderate"
    LIMITED = "limited"

    @property
    def rank(self) -> int:
        return {"limited": 1, "moderate": 2, "strong": 3}[self.value]


class Role(Enum):
    PERFORMED = "performed"  # did the work
    LED = "led"  # authorised, supervised, trained or assessed others doing it
    OBSERVED = "observed"  # stood by, witnessed, acted as top man


class Depth(Enum):
    ROUTINE = "routine"  # a check, a top-up, a reset
    SKILLED = "skilled"  # a repair, a diagnosis, a job that needed the trade


class Action(Enum):
    ASK = "ask"  # only the keeper can answer
    FETCH = "fetch"  # paperwork that probably exists somewhere
    BOOK = "book"  # a course, a renewal or a medical

    @property
    def rank(self) -> int:
        return {"ask": 0, "fetch": 1, "book": 2}[self.value]


class FitStatus(Enum):
    READY = "ready"  # every requirement the records can show is met
    NEARLY = "nearly"  # the essential work is evidenced; every gap is closeable
    NOT_SHOWN = "not_shown"  # an essential kind of work does not appear in these records


@dataclass(frozen=True)
class Evidence:
    entry_id: str
    date: str
    station: str
    source_record: str
    text: str
    role: Role
    depth: Depth
    withhold_text: bool = False  # the entry describes another person's health

    @property
    def year(self) -> int:
        return int(self.date[:4])


class EvidenceError(ValueError):
    """Raised when a claim that must rest on evidence has none."""


@dataclass
class Claim:
    keeper: str
    subject: str  # a skill key or a scheme code
    kind: ClaimKind
    text: str  # the sentence a person reads; built by wording.py
    strength: Strength | None = None
    evidence: list[Evidence] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.kind in (ClaimKind.HAS_DONE, ClaimKind.PRESENT) and not self.evidence:
            raise EvidenceError(f"{self.keeper}: {self.kind.value} claim on {self.subject} with no evidence")


@dataclass(frozen=True)
class Step:
    """One thing that has to happen before the keeper can take a job."""

    key: str  # stable id, used for ordering: "medical", "OSSC-SS", "HV-paperwork"
    action: Action
    text: str
    because: str = ""  # what in the records led to this step
    evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.action, Action):
            raise ValueError(f"step {self.key} has no action")


@dataclass(frozen=True)
class Line:
    """A sentence about a keeper against a posting, with the entries behind it."""

    requirement: str  # the posting's words
    text: str  # what the records say against it
    evidence_ids: tuple[str, ...] = ()


@dataclass
class Fit:
    keeper: str
    posting: str
    status: FitStatus
    met: list[Line]  # essential lines the records show
    missing: list[Line]  # essential work not shown (NOT_SHOWN only)
    desirable: list[Line]  # nice-to-haves the records show
    route: list[Step]  # ordered by prerequisites, then ask -> fetch -> book
    to_confirm: list[Line]  # only the keeper or the employer can tell

    @property
    def bookings(self) -> list[Step]:
        """Courses and renewals. The offshore medical is left out: everyone needs one."""
        return [s for s in self.route if s.action is Action.BOOK and s.key != "medical"]
