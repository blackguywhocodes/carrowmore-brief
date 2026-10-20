# Carrowmore: the opportunities, structured

Source: `carrowmore-data-pack/employers/` (six postings) and `certification_schemes.json`.
Here they're normalised into one shape: what's **mandatory** (a certificate, checkable against
training records), what's **essential evidence** (inferable from logbooks), what's **not knowable
from the data** (ask the keeper), and what's **desirable**.

## Summary

| # | Role | Employer | Posts | Pattern | Mandatory certs / checks | Fit for keepers (from the posting) |
|---|---|---|---|---|---|---|
| 1 | Wind Turbine Technician (O&M) | Carrowmore Array | ~40, two waves | 14 on / 14 off, offshore vessel | OSSC (all modules), offshore medical | Explicitly wants people who kept plant running remotely; no wind experience needed |
| 2 | HV Authorised Person | Carrowmore Array Asset Ops | 6 (4 offshore, 2 onshore) | 2 on / 3 off; or 4-on 4-off onshore | HVAP (all 4, current), OSSC, offshore medical, 2 yrs documented switching ≥11kV **or** a documented lapsed internal HV authorisation | Narrow: only keepers with paperwork-backed HV history |
| 3 | Watch Officer | Northern Isles Coastguard | 5 | Rotating 12h watches incl. nights | None stated; hearing test, security vetting, timed written test | Strong: continuous watchkeeping, radio, met observing, formal records are a keeper's daily work. Physical fitness and offshore certs "irrelevant" |
| 4 | Offshore Survey Technician | Deepline Offshore | not stated | 4 on / 4 off, worldwide | OSSC (all, in date), offshore medical, valid passport | Says lighthouse people have done well; bench fault-finding test |
| 5 | Hydrographic Technician | Meridian Survey | 1–2 | Apr–Oct on a 16m launch, winter in office | SMOC current, or obtained in the first season (paid) | Small boat all day, careful logging, generator fixing, ATON verification work |
| 6 | Marine Electrician | Port of Cnoc Harbour Trust | 1 | Mon–Fri, 1-in-4 standby | None stated; no switching without an existing authorisation | Distribution, motors, standby generation, navigation lights; values "what you have actually done" |

## Per role: requirements mapped to evidence

### 1. Wind Turbine Technician (the primary question)

| Requirement | Type | How to check | Scheme / skill |
|---|---|---|---|
| Offshore safety and survival cert | Mandatory | Recompute from training records | OSSC (SS, FF, FA, HL, CS) |
| Offshore medical | Mandatory | **Not in data** | needs first for everyone |
| Hands-on mechanical or electrical maintenance on plant | Essential | Logbook HAS_DONE | generator/diesel, electrical, hydraulics/pumps |
| Comfortable at height, enclosed spaces, small boat in a swell | Essential | **Not in data**: show related HAS_DONE, then ask the keeper | height, confined space, boat |
| Maintained generating plant remotely | Desirable | Logbook + station class (`rock`) | generator/diesel |
| Electrical fault-finding | Desirable | Logbook | electrical |
| Permit system | Desirable | Logbook | isolation/permits |
| Trained younger colleagues | Desirable | Logbook | training others |
| Tower climbing and rescue (from duties) | Implied | Training records | WAHS-2, WAHS-4 |

⚠ **Inconsistency to note:** the posting says the offshore certificate covers "sea survival,
fire, first aid **and working at height**", but OSSC in `certification_schemes.json` has no
height module. Height is a separate scheme (WAHS). Assume WAHS is also needed before
mobilisation and say so. This is a good candidate for another short question to Greg.

### 2. HV Authorised Person

| Requirement | Type | How to check | Scheme / skill |
|---|---|---|---|
| HVAP, all 4 modules, current | Mandatory | Recompute; renewal 3 yrs | HVAP-01…04 |
| HVAP prerequisite | Mandatory | Training records | MECS at Stage 3+ |
| OSSC + offshore medical | Mandatory | Recompute / **not in data** | OSSC |
| 2 yrs documented switching ≥11kV, or a documented lapsed internal authorisation | Mandatory | **Not provable from data**; logbooks show who is worth reconstructing paperwork for | HV switching |
| Permits, supervising contractors, mentoring | Desirable | Logbook | permits, training others |

### 3. Coastguard Watch Officer

| Requirement | Type | How to check | Scheme / skill |
|---|---|---|---|
| Sustained concentration, composure, situational judgement | Essential | **Not in data**: assessed by the employer | n/a |
| Written accuracy under pressure | Essential | **Not in data** (a timed test); logbook authorship is weak supporting evidence | n/a |
| Radiotelephone: VHF, DSC, distress traffic | Essential | Training records + logbook | RCOM-GEN, RCOM-DSC; radio entries |
| Meteorological observing | Desirable | Training + logbook (routine weather lines) | RCOM-MET |
| Long-term formal operational record | Desirable | Years of logbook entries | tenure |
| Continuous watchkeeping background | Desirable | Postings history | tenure |

### 4. Offshore Survey Technician

| Requirement | Type | How to check |
|---|---|---|
| OSSC (all, in date), offshore medical, passport | Mandatory | Recompute / **not in data** / **not in data** |
| Electrical/electronic fault-finding | Mandatory (bench test) | Logbook: electrical, telemetry |
| Winch/A-frame, cable terminations, corrosion control | Duties | Logbook; LOSC is relevant |

### 5. Hydrographic Technician

| Requirement | Type | How to check |
|---|---|---|
| SMOC current, or within the first season | Mandatory (can be gained) | Recompute SMOC (BH, NV, MO, SR) |
| Small boat all day; careful logging; clear writing | Essential | Logbook boat entries; the rest **not in data** |
| Generator fixing, ATON verification | Duties | Logbook; ANSM is relevant |

### 6. Marine Electrician

| Requirement | Type | How to check |
|---|---|---|
| Electrical distribution, motors, standby generation, navigation lights | Essential (by duties) | Logbook electrical/generator; ANSM, MECS |
| Mechanical handiness; boat occasionally; drained chambers and tunnels | Essential | Logbook; confined space |
| Works unsupervised | Essential | **Not in data** |

## How to use this in the build

- **Encode all six as requirement tables** (superseded the earlier "role 1 only" advice; see
  architecture v2). If short on time, keep roles 1, 2 and 3 per the v2 cut order.
- **Commit this file as `opportunities.md` (or a JSON version) anyway.** It costs nothing extra
  and shows you read all six.
- **Possible "better question" angle:** roles 1 and 3 want nearly opposite things. The Array
  wants physical offshore capability; the Coastguard calls that "irrelevant" and wants the
  watchkeeping, radio and record-keeping that every keeper did for decades. A keeper who
  looks weak for the Array may be one of the strongest Coastguard candidates. One paragraph
  on this in the write-up, plus a short list if time allows, is a strong unasked finding.
