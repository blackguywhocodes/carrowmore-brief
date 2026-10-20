"""The six postings as requirement tables, hand-mapped from employers/*.md. Disposable.

Each line is one of:
  cert      a scheme (or some of its modules) that must be held and current
  skill     work the logbooks must show, at a minimum strength
  paperwork something only a document can prove; the logbooks show whether it is worth looking
  ask       something only the keeper or the employer can tell
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .model import Depth, Strength


@dataclass(frozen=True)
class Req:
    kind: str  # cert | skill | paperwork | ask
    text: str
    essential: bool = True
    scheme: str | None = None
    modules: tuple[str, ...] = ()  # empty means the whole scheme
    skills: tuple[str, ...] = ()  # any of these
    min_strength: Strength = Strength.MODERATE
    depth: Depth | None = None  # Depth.SKILLED: routine checks don't count
    related: tuple[str, ...] = ()  # for ask lines: work worth showing alongside the question
    note: str = ""


@dataclass(frozen=True)
class Posting:
    key: str
    title: str
    employer: str
    posts: str
    offshore: bool
    reqs: tuple[Req, ...] = field(default_factory=tuple)


MAINTENANCE = ("mechanical", "generating_plant", "electrical", "hydraulics")

POSTINGS = (
    Posting(
        "array_om",
        "Wind Turbine Technician (O&M)",
        "Carrowmore Array",
        "about 40",
        offshore=True,
        reqs=(
            Req("cert", "Offshore safety and survival certificate", scheme="OSSC"),
            Req(
                "cert",
                "Tower climbing and rescue",
                scheme="WAHS",
                modules=("WAHS-1", "WAHS-2", "WAHS-4"),
                note=(
                    "The posting says the offshore certificate covers working at height; OSSC has no "
                    "height module, so WAHS is assumed. Confirm with the Array."
                ),
            ),
            Req(
                "skill",
                "Hands-on mechanical or electrical maintenance on plant",
                skills=MAINTENANCE,
                depth=Depth.SKILLED,
            ),
            Req(
                "ask",
                "Comfortable at height, in enclosed spaces and on a small boat in a swell",
                related=("height", "confined_space", "boat"),
            ),
            Req(
                "skill",
                "Maintained generating plant",
                essential=False,
                skills=("generating_plant",),
                depth=Depth.SKILLED,
            ),
            Req("skill", "Electrical fault-finding", essential=False, skills=("fault_finding",), depth=Depth.SKILLED),
            Req("skill", "Worked to a permit system", essential=False, skills=("permits",)),
            Req("skill", "Trained and looked after younger colleagues", essential=False, skills=("training_others",)),
        ),
    ),
    Posting(
        "hv_ap",
        "High Voltage Authorised Person",
        "Carrowmore Array Asset Operations",
        "6",
        offshore=True,
        reqs=(
            Req("cert", "HVAP, all four modules, current", scheme="HVAP"),
            Req("cert", "Offshore safety and survival certificate", scheme="OSSC"),
            Req(
                "paperwork",
                "Two years' documented switching at 11kV or above, or a documented lapsed internal authorisation",
                skills=("hv_switching",),
                depth=Depth.SKILLED,
            ),
            Req("skill", "Issued safety documents under a permit regime", essential=False, skills=("permits",)),
            Req("skill", "Supervised contractors", essential=False, skills=("contractors",)),
            Req("skill", "Mentored others", essential=False, skills=("training_others",)),
        ),
    ),
    Posting(
        "coastguard",
        "Watch Officer",
        "Northern Isles Coastguard",
        "5",
        offshore=False,
        reqs=(
            Req("skill", "Radiotelephone discipline: VHF, DSC, distress traffic", skills=("radio",)),
            Req(
                "ask",
                "Sustained concentration over 12-hour night watches",
                related=("radio",),
                note="Assessed by the Coastguard.",
            ),
            Req(
                "ask",
                "Written accuracy under pressure (timed test)",
                related=("records",),
                note="Assessed by the Coastguard.",
            ),
            Req(
                "ask", "Situational judgement and composure", related=("incident",), note="Assessed by the Coastguard."
            ),
            Req("ask", "Hearing test and security vetting", note="Done by the Coastguard."),
            Req(
                "skill",
                "On-scene coordination or a reporting point in a live incident",
                essential=False,
                skills=("incident",),
                depth=Depth.SKILLED,
            ),
            Req("skill", "Meteorological observing", essential=False, skills=("met_obs",)),
            Req("skill", "A formal operational record kept over a long period", essential=False, skills=("records",)),
        ),
    ),
    Posting(
        "deepline",
        "Offshore Survey Technician",
        "Deepline Offshore",
        "not stated",
        offshore=True,
        reqs=(
            Req("cert", "Offshore survival and safety certificate, all modules, in date", scheme="OSSC"),
            Req(
                "skill",
                "Electrical and electronic fault-finding (bench test at interview)",
                skills=("fault_finding",),
                depth=Depth.SKILLED,
            ),
            Req("ask", "Valid passport and travel at 48 hours' notice"),
            Req("skill", "Winch and lifting operations", essential=False, skills=("lifting",)),
            Req("skill", "Telemetry and electronics", essential=False, skills=("electronics",)),
            Req("skill", "Corrosion control and terminations", essential=False, skills=("fabric",)),
            Req("skill", "Helideck duties", essential=False, skills=("helideck",)),
        ),
    ),
    Posting(
        "meridian",
        "Hydrographic Technician",
        "Meridian Survey",
        "1–2",
        offshore=False,
        reqs=(
            Req(
                "cert",
                "Small craft and marine operations certificate (can be gained in the first season, paid)",
                scheme="SMOC",
                essential=False,
            ),
            Req("skill", "On a small boat all day; handles the boat", skills=("boat",), depth=Depth.SKILLED),
            Req("skill", "Keeps a careful log", skills=("records",)),
            Req("ask", "Writes a clear sentence", note="Meridian asks for a letter."),
            Req("skill", "Fixes the generator", essential=False, skills=("generating_plant",)),
            Req("skill", "Aid-to-navigation checks", essential=False, skills=("aton",)),
        ),
    ),
    Posting(
        "port_electrician",
        "Marine Electrician",
        "Port of Cnoc Harbour Trust",
        "1",
        offshore=False,
        reqs=(
            Req("skill", "Distribution, motors and standby generation", skills=("electrical",), depth=Depth.SKILLED),
            Req(
                "skill", "Handy on the mechanical side", skills=("mechanical", "generating_plant"), depth=Depth.SKILLED
            ),
            Req(
                "ask",
                "Works alone without supervision; boat work and drained chambers",
                related=("supervising", "boat", "confined_space"),
            ),
            Req("skill", "Navigation lights", essential=False, skills=("aton",)),
            Req(
                "skill",
                "HV switching experience (no switching here without an existing authorisation)",
                essential=False,
                skills=("hv_switching",),
                depth=Depth.SKILLED,
            ),
        ),
    ),
)

BY_KEY = {p.key: p for p in POSTINGS}
