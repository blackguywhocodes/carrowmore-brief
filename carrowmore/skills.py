"""Skill rules: logbook text -> evidence. Disposable; audited by `python -m carrowmore.audit`.

Every pattern was written against the 620 distinct phrasings in clean/ (digits and case
normalised) and the audit lists every phrasing with what it matched, so a reviewer can check
the whole rule set rather than a sample.
"""

from __future__ import annotations

import re

from .load import Entry
from .model import Depth, Evidence, Role

S, R = Depth.SKILLED, Depth.ROUTINE

# key: (label, [(depth, pattern), ...]). Patterns run on lower-cased entry text.
SKILLS: dict[str, tuple[str, list[tuple[Depth, str]]]] = {
    "generating_plant": (
        "diesel generating plant",
        [
            (S, r"decoke on no"),
            (S, r"injectors off no"),
            (S, r"big-end"),
            (S, r"set the timing on no"),
            (S, r"governor hunting"),
            (S, r"overhauled the raw water side"),
            (S, r"\bavr on no"),
            (S, r"synchronised no"),
            (S, r"auto-start sequence"),
            (S, r"engine room fire in the no"),
            (S, r"load chart worked out for the new generator"),
            (R, r"bled the fuel system"),
            (R, r"changed oil and filters on no"),
            (R, r"topped coolant"),
            (R, r"\bran no\.? ?\d+ set\b"),
            (R, r"started no\.? ?\d+ set"),
            (R, r"auto start tested"),
            (R, r"reset the overspeed"),
            (R, r"weekly changeover, no"),
            (R, r"defect reported on the no"),
            (R, r"checked panel gauges"),
            (R, r"to the day tank"),
        ],
    ),
    "mechanical": (
        "mechanical and pumped plant maintenance",
        [
            (S, r"decoke on no"),
            (S, r"injectors off no"),
            (S, r"big-end"),
            (S, r"set the timing on no"),
            (S, r"overhauled the raw water side"),
            (S, r"rings worn"),
            (S, r"mechanical seal gone"),
            (S, r"rebuilt the no\.? ?\d+ pump"),
            (S, r"repacked the gland"),
            (S, r"foot valve"),
            (S, r"gearbox stripped"),
            (S, r"brake band relined"),
            (S, r"luffing gear"),
            (S, r"clockwork drive"),
            (S, r"stripped and cleaned the mercury bath"),
            (S, r"diaphone piston"),
            (S, r"dismantled the ratchet"),
            (S, r"emitter horn"),
            (S, r"overhauled the foam installation"),
            (S, r"renewed the winch wire"),
            (S, r"duty/standby arrangement on the two sump pumps"),
            (R, r"bled the fuel system"),
            (R, r"changed oil and filters"),
            (R, r"topped coolant"),
            (R, r"primed the no"),
            (R, r"suction strainer"),
            (R, r"greased the (compressor|winch|derrick)"),
            (R, r"compressor run up"),
            (R, r"winch brake adjusted"),
            (R, r"ran the sump pump"),
            (R, r"engine run up and flushed"),
        ],
    ),
    "hydraulics": (
        "hydraulic systems",
        [
            (S, r"reseal on the no"),
            (S, r"relief valve passing"),
            (S, r"flushed the whole system after water ingress"),
            (S, r"new hose to length"),
            (R, r"hydraulic reservoir"),
            (R, r"weeps on the rams"),
            (R, r"filter changed on the power pack"),
        ],
    ),
    "electrical": (
        "LV electrical work",
        [
            (S, r"chafed core"),
            (S, r"clamp meter"),
            (S, r"earth fault"),
            (S, r"halving the circuit"),
            (S, r"loose wire"),
            (S, r"wrong terminal"),
            (S, r"protection relay settings"),
            (S, r"discrimination not right"),
            (S, r"changeover contactor"),
            (S, r"reconfigured distribution"),
            (S, r"changeover logic"),
            (S, r"re-terminated"),
            (S, r"megger"),
            (S, r"balanced loads"),
            (S, r"\bavr on no"),
            (S, r"synchronised no"),
            (S, r"auto-start sequence"),
            (S, r"charger float voltage"),
            (S, r"soft cell"),
            (S, r"rebalanced the bank"),
            (S, r"load-tested the standby bank"),
            (S, r"full capacity discharge"),
            (S, r"drive motor brushes"),
            (S, r"duty/standby arrangement"),
            (S, r"fitted suppression"),
            (S, r"power supply dropping"),
            (R, r"\bfuse"),  # not "refused"
            (R, r"reset tripped breaker"),
            (R, r"checked continuity"),
            (R, r"checked board readings"),
            (R, r"tightened glands"),
            (R, r"contacts in the changeover relay"),
            (R, r"changed over main board"),
            (R, r"lamp circuit off at the board"),
            (R, r"cleaned terminals"),
            (R, r"topped up cells"),
            (R, r"charger on boost"),
            (R, r"battery checked on the beacon"),
            (R, r"checked the feeder run"),
            (R, r"sgs taken across the bank"),
            (R, r"battery room vented"),
            (R, r"intermittent fault on the gallery lights"),
        ],
    ),
    "fault_finding": (
        "electrical and electronic fault-finding",
        [
            (S, r"\btraced\b"),
            (S, r"clamp meter"),
            (S, r"to catch the earth fault"),
            (S, r"halving the circuit"),
            (S, r"contractor could not find it"),
            (S, r"two were found wrong"),
            (S, r"discrimination not right"),
            (S, r"receiver desensitised"),
            (S, r"not triggering"),
            (S, r"antenna feeder found waterlogged"),
            (S, r"megger"),
            (R, r"lamp not lit, found the fuse"),
            (R, r"intermittent fault on the gallery lights"),
        ],
    ),
    "hv_switching": (
        "high-voltage switching and earthing",
        [
            (S, r"carried out switching"),
            (S, r"switched the ring"),
            (S, r"restored the hv"),
            (S, r"\d+kv board off"),
            (S, r"earthed off both ends"),
            (S, r"isolated no\.? ?\d+ transformer"),
            (S, r"racked out no"),
            (S, r"authorised the switching programme"),
            (S, r"held the keys for the hv work"),
            (S, r"stood by while .* switched"),
            (S, r"witnessed earths applied"),
            # "HV room locked and keys signed back in" is access control, not switching: left out.
        ],
    ),
    "permits": (
        "permit-to-work",
        [
            (S, r"issued (ptw|permit)"),
            (S, r"(ptw|permit)\S*( bk\.\d+ no\.\d+)?( \S+)? issued to the contractor"),
            (S, r"acted as issuing authority"),
            (S, r"refused to sign"),
            (S, r"authorised the switching programme"),
            (S, r"wrote the safe system"),
            (S, r"cancelled (ptw|permit)"),
            (R, r"permit returned and cancelled"),
            (R, r"signed on to (ptw|permit)"),
            (R, r"read the permit conditions"),
            (R, r"\b(ptw|permit)\b.* refers"),
        ],
    ),
    "height": (
        "working at height and rope access",
        [
            (S, r"fall arrest"),
            (S, r"rigged staging"),
            (S, r"abseil"),
            (S, r"descended to the mid-course"),
            (S, r"roped access"),
            (S, r"rebelay"),
            (S, r"worked the mast head"),
            (S, r"pick-off rescue on the tower"),
            (R, r"harness and lanyard inspected"),
            (R, r"up the ladder to the gallery"),
            (R, r"anchor points on the gallery"),
            (R, r"from the staging"),
            (R, r"ropes inspected"),
        ],
    ),
    "rescue": (
        "rescue of a casualty from height or a confined space",
        [
            (S, r"pick-off rescue"),
            (S, r"from the cable duct after he was overcome"),
            (S, r"rescue kit rigged at the manhole"),
            (S, r"packaged him for the winch lift"),
        ],
    ),
    "confined_space": (
        "confined-space entry",
        [
            (S, r"confined space"),
            (S, r"tank entry"),
            (S, r"entered the water tank"),
            (S, r"gas tested the fuel tank"),
            (S, r"ventilated the cellar"),
            (S, r"as top man"),
            (S, r"from the cable duct after he was overcome"),
            (S, r"rescue kit rigged at the manhole"),
        ],
    ),
    "boat": (
        "small-boat handling and landings in a sea",
        [
            (S, r"coxed"),
            (S, r"took the boat through the sound"),
            (S, r"ran the boat off the rock"),
            (S, r"broken-down punt under tow"),
            (S, r"landed the relief"),
            (S, r"landing in the dark"),
            (S, r"men and stores ashore"),
            (S, r"fuel transfer by hose in a swell"),
            (S, r"judged the sea wrong"),
            (S, r"mooring dragged"),
            (S, r"ground chain for the boat mooring"),
            (S, r"slewed heavy plant off the boat"),
            (S, r"landing attempted, abandoned"),
            (S, r"reported the landing as unsafe"),
            (S, r"keepers on the boat work"),
            (R, r"took the punt"),
            (R, r"boat away to the landing"),
            (R, r"boat hauled up"),
            (R, r"landing party rigged"),
            (R, r"stood by at the landing"),
            (R, r"shackle on the boat mooring"),
            (R, r"moorings checked"),
            (R, r"mooring chain inspected"),
        ],
    ),
    "lifting": (
        "lifting operations, winches and cranes",
        [
            (S, r"comms for the lift operation"),
            (S, r"load chart"),
            (S, r"ran the lifting operation"),
            (S, r"heavy lift"),
            (S, r"slewed heavy plant"),
            (S, r"condemned \d+ strops"),
            (S, r"load tested the winch"),
            (S, r"strop and thimble"),
            (S, r"renewed the winch wire"),
            (S, r"jackstay"),
            (S, r"luffing gear"),
            (S, r"gearbox stripped on the winch"),
            (S, r"brake band relined"),
            (R, r"derrick used"),
            (R, r"crane hook"),
            (R, r"stores with the winch"),
            (R, r"taken up by the winch"),
            (R, r"shackles and strops"),
            (R, r"wire inspected"),
            (R, r"greased the (winch|derrick)"),
            (R, r"winch brake adjusted"),
            (R, r"buoy recovered"),
        ],
    ),
    "first_aid": (
        "casualty care",
        [
            (S, r"heart case"),
            (S, r"back injury"),
            (S, r"hypothermia"),
            (S, r"crush injury"),
            (S, r"after he was overcome"),
            (R, r"dressed a cut hand"),
            (R, r"first aid box"),
            (R, r"casualty bag"),
        ],
    ),
    "radio": (
        "maritime radio: VHF, MF, DSC and distress traffic",
        [
            (S, r"stations at once during the search"),
            (S, r"ran comms for"),
            (S, r"poor-range casualty"),
            (S, r"heard the mayday"),
            (S, r"coordinated the relay"),
            (S, r"held the distress watch"),
            (S, r"live dsc distress alert"),
            (S, r"copied a distress"),
            (S, r"talked the pilot in on the radio"),
            (S, r"cleared a false dsc alert"),
            (R, r"distress watch kept"),
            (R, r"nothing heard on the distress"),
            (R, r"radio check"),
            (R, r"scheduled call"),
            (R, r"mayday relay heard"),
            (R, r"\bon ch\.\d+ re the relief"),
            (R, r"dsc watch"),
            (R, r"dsc test call"),
            (R, r"mf watch kept"),
            (R, r"mf sched"),
            (R, r"silence periods"),
            (R, r"logged the search traffic"),
            (R, r"passed the weather by vhf"),
        ],
    ),
    "electronics": (
        "radio, AIS and telemetry electronics",
        [
            (S, r"tuned the aerial"),
            (S, r"antenna feeder"),
            (S, r"standby transmitter"),
            (S, r"pa valve"),
            (S, r"receiver desensitised"),
            (S, r"earth mat for the mf aerial"),
            (S, r"aerial mast head"),
            (S, r"reprogrammed the dsc controller"),
            (S, r"racon not triggering"),
            (S, r"wrong mmsi"),
            (S, r"synthetic aton message"),
            (S, r"telemetry link"),
            (S, r"aton reporting intermittently"),
            (S, r"new beacon from the manual"),
            (S, r"false alerts to a fault in the position feed"),
            (R, r"aerial inspected"),
            (R, r"mf set checked"),
            (R, r"racon (reset|checked|coding)"),
            (R, r"ais (unit reporting|reset)"),
            (R, r"mmsi checked"),
            (R, r"ais position"),
            (R, r"changed the battery in the portable set"),
        ],
    ),
    "incident": (
        "search and rescue incident handling",
        [
            (S, r"stations at once during the search"),
            (S, r"poor-range casualty"),
            (S, r"on-scene reporting point"),
            (S, r"search pattern from the drift"),
            (S, r"full timeline of the incident"),
            (S, r"held the search log"),
            (S, r"heard the mayday first"),
            (S, r"live dsc distress alert"),
            (S, r"coordinated the relay"),
            (S, r"copied a distress"),
            (R, r"lookout for the missing boat"),
            (R, r"reported a flare"),
            (R, r"logged the search traffic"),
            (R, r"stood by for evacuation"),
        ],
    ),
    "met_obs": (
        "meteorological observing",
        [
            (S, r"kept hourly obs through the storm"),
            (S, r"queried our own obs"),
            (S, r"instrument screen"),
            (S, r"on the observing code"),
            (S, r"fog detector"),
            (R, r"passed the weather"),
            (R, r"\bob taken"),
            (R, r"missed the \d+ ob"),
            (R, r"sea state and swell recorded"),
            (R, r"^wind \w+ \d+"),
            (R, r"^bar [\d.]+"),
            (R, r"visibility cleared"),
        ],
    ),
    "records": (
        "formal operational records",
        [
            (S, r"reconstructed the log"),
            (S, r"full timeline of the incident"),
            (S, r"held the search log"),
            (S, r"rewrote the station returns"),
            (S, r"running hours schedule"),
            (S, r"rebuilt the stores ledger"),
            (S, r"full condition survey"),
            (S, r"dilapidation schedule"),
            (S, r"traffic log straight"),
            (S, r"manifests kept straight"),
            (S, r"station handbook"),
            (R, r"log written up"),
            (R, r"log made up"),
            (R, r"entries checked and signed"),
            (R, r"annual return"),
            (R, r"returns completed"),
            (R, r"watch bill made out"),
            (R, r"report filed"),
        ],
    ),
    "aton": (
        "navigation lights and aids to navigation",
        [
            (S, r"lamp focus"),
            (S, r"aligned the no"),
            (S, r"character found"),
            (S, r"timing gear on the signal"),
            (S, r"new flasher unit"),
            (S, r"coding wheel"),
            (S, r"lamp changer"),
            (S, r"stripped and cleaned the mercury bath"),
            (S, r"clockwork drive"),
            (S, r"diaphone piston"),
            (S, r"emitter horn"),
            (S, r"fog detector"),
            (S, r"racon not triggering"),
            (S, r"synthetic aton message"),
            (S, r"new beacon from the manual"),
            (S, r"telemetry link so the lamp fault"),
            (R, r"lens panels cleaned"),
            (R, r"lamp changed"),
            (R, r"wick trimmed"),
            (R, r"mercury bath checked"),
            (R, r"rotation checked"),
            (R, r"changer tested"),
            (R, r"diaphone tested"),
            (R, r"fog signal in operation"),
            (R, r"character (checked|confirmed)"),
            (R, r"timed the flashes"),
            (R, r"occulting timing"),
            (R, r"aton message confirmed"),
            (R, r"lantern glass cleaned"),
            (R, r"lamp not lit"),
        ],
    ),
    "fire": (
        "fire response",
        [
            (S, r"engine room fire"),
            (S, r"fire drill as a real scenario"),
            (S, r"overhauled the foam installation"),
            (R, r"fire drill"),
            (R, r"fire alarm tested"),
            (R, r"extinguishers checked"),
            (R, r"hose reels"),
        ],
    ),
    "helideck": (
        "helicopter landing area operations",
        [
            (S, r"marshalled the relief aircraft"),
            (S, r"talked the pilot in"),
            (S, r"ran the deck for"),
            (S, r"off the rock by helicopter"),
            (S, r"pad discipline"),
            (R, r"stood by for the aircraft"),
            (R, r"pad lighting tested"),
            (R, r"helipad swept"),
            (R, r"windsock renewed"),
        ],
    ),
    "survival": (
        "sea survival and station evacuation",
        [
            (S, r"annual survival drill"),
            (S, r"evacuated the station"),
            (S, r"abandon plan"),
            (S, r"evacuation plan"),
            (S, r"survival kit"),
            (R, r"survival drill with"),
            (R, r"immersion suits"),
            (R, r"liferaft"),
            (R, r"lifejackets"),
            (R, r"evacuation route checked"),
            (R, r"muster list"),
        ],
    ),
    "fabric": (
        "structures, coatings and corrosion control",
        [
            (S, r"two-pack"),
            (S, r"needle-gunned"),
            (S, r"\blime\b"),
            (S, r"original mortar"),
            (S, r"original batter"),
            (S, r"glazing bars"),
            (S, r"curved pane"),
            (S, r"lantern panes"),
            (S, r"bimetallic corrosion"),
            (S, r"sacrificial anodes"),
            (S, r"surveyed the whole landing ironwork"),
            (S, r"full condition survey"),
            (S, r"surface prep argued"),
            (S, r"tower repaint"),
            (S, r"roof water system"),
            (S, r"soakaway"),
            (S, r"yard drain to a proper fall"),
            (R, r"pointing"),
            (R, r"rendered"),
            (R, r"red lead"),
            (R, r"painted"),
            (R, r"whitewashed"),
            (R, r"wire brushed"),
            (R, r"putty"),
            (R, r"rust"),
            (R, r"mortar"),
            (R, r"anodes checked"),
            (R, r"exposed threads"),
            (R, r"astragals"),
            (R, r"gutters"),
            (R, r"cracked pane"),
            (R, r"boundary wall"),
        ],
    ),
    "training_others": (
        "training and looking after newer colleagues",
        [
            (S, r"ran the overhaul party"),
            (S, r"paired with an experienced hand"),
            (S, r"briefed the new"),
            (S, r"round the plant"),
            (S, r"through the whole plant"),
            (S, r"\bshowed (?!when)"),  # not "fault only showed when"
            (S, r"on the observing code"),
            (S, r"\bcoached\b"),
            (S, r"with the new man"),
            (S, r"handbook for the new men"),
            (S, r"keepers on the boat work"),
            (S, r"briefed the party"),
        ],
    ),
    "supervising": (
        "running a team or a station",
        [
            (S, r"ran the overhaul party"),
            (S, r"took charge of the station"),
            (S, r"ran the whole tower repaint"),
            (S, r"ran the lifting operation"),
            (S, r"ran the muster"),
            (S, r"ran the deck for"),
            (S, r"coxed for the relief"),
            (R, r"\bdetailed\b"),
            (R, r"work allocated and checked"),
        ],
    ),
    "contractors": (
        "working with and supervising contractors",
        [
            (S, r"to the contractor"),
            (S, r"contractor could not find it"),
            (S, r"after the contractor cleared"),
            (S, r"walked the isolations with him"),
        ],
    ),
}

# The keeper was present while somebody else did the work. These never count as having done it.
OBSERVED = [r"stood by while", r"witnessed earths applied"]

# The keeper authorised, controlled, supervised, trained or assessed.
LED = [
    r"authorised the switching programme",
    r"acted as issuing authority",
    r"held the keys",
    r"issued (ptw|permit)",
    r"issued to the contractor",
    r"refused to sign",
    r"ran the (overhaul party|lifting operation|deck|whole tower repaint|muster|fire drill|annual survival drill)",
    r"coxed",
    r"keepers on the boat work",
    r"took charge",
    r"\b(trained|coached|briefed|detailed)\b",
    r"\bshowed (?!when)",
    r"round the plant|through the whole plant",
    r"with the new man",
    r"work allocated",
    r"wrote the (method|safe system)",
]

# Entries about another person's conduct. Excluded from every claim (see the write-up).
EXCLUDED = [r"stand a man down"]

# Skills whose entries describe someone else's injury or illness: the claim is made,
# the entry text is never shown, only its id.
WITHHOLD_TEXT = {"first_aid"}

_COMPILED = {key: [(depth, re.compile(p)) for depth, p in patterns] for key, (_label, patterns) in SKILLS.items()}
_OBSERVED = [re.compile(p) for p in OBSERVED]
_LED = [re.compile(p) for p in LED]
_EXCLUDED = [re.compile(p) for p in EXCLUDED]


def label(skill: str) -> str:
    return SKILLS[skill][0]


def classify(text: str) -> tuple[Role, dict[str, Depth]] | None:
    """Return (role, {skill: depth}) for one entry's text, or None if it is excluded."""
    t = text.lower()
    if any(p.search(t) for p in _EXCLUDED):
        return None
    if any(p.search(t) for p in _OBSERVED):
        role = Role.OBSERVED
    elif any(p.search(t) for p in _LED):
        role = Role.LED
    else:
        role = Role.PERFORMED
    skills: dict[str, Depth] = {}
    for key, rules in _COMPILED.items():
        for depth, rx in rules:
            if rx.search(t):
                if skills.get(key) != Depth.SKILLED:
                    skills[key] = depth
    return role, skills


def match(entries: list[Entry]) -> dict[str, list[Evidence]]:
    """Evidence per skill for one keeper's entries."""
    out: dict[str, list[Evidence]] = {}
    for e in entries:
        result = classify(e.text)
        if result is None:
            continue
        role, skills = result
        for key, depth in skills.items():
            out.setdefault(key, []).append(
                Evidence(
                    entry_id=e.entry_id,
                    date=e.date,
                    station=e.station,
                    source_record=e.source_record,
                    text=e.text,
                    role=role,
                    depth=depth,
                    withhold_text=key in WITHHOLD_TEXT,
                )
            )
    return out


def kv_levels(evidence: list[Evidence]) -> list[int]:
    """Voltage levels a keeper's HV entries state explicitly (most entries don't)."""
    found = {int(m.group(1)) for ev in evidence for m in re.finditer(r"(\d+)\s?kv", ev.text.lower())}
    return sorted(found)
