# Step 27 — Gen-1 R1T tailgate / bed control arrangement, and how the topper preserves it

Acceptance item 3. **Nothing here is an invented switch.** Every arrangement claim below is
traced to a Rivian-published PDF; every gap is named as a gap. Raw research log with page
citations: `research/tailgate_switch_research.md` in this directory.

---

## 1. What the truck actually has (Rivian primary sources)

Sources, both fetched and text-extracted during this pass:

* **R1T Owner's Guide, MY22–24 (June 2025 revision)** — the correct Gen-1 document. Rivian forked
  the guide line at MY25, so `r1t-my22-24-og-*` is the Gen-1 maintained branch.
  <https://assets.ctfassets.net/2md5qhoeajym/530xs9hu11xOKefT2JrvA5/9806f4c37762c217a108b1a07ea3c37f/r1t-my22-24-og-en-us-20250630.pdf>
  The tailgate section is textually identical to the May-2022 launch guide, so this holds across
  the whole Gen-1 run.
* **R1T Upfitting Guide, Sept 2025.**
  <https://assets.ctfassets.net/2md5qhoeajym/5ysf6K5UtGtHedY1fMeClC/3ab05048ce5c4f7e3195607919f3def3/r1t-upfitting-guide-en-us-20250924.pdf>

### 1.1 The tailgate is MANUAL, electrically released

Owner's Guide p.283 states it three separate ways:

> "The only way to close the tailgate is to manually close it."
> "Since the tailgate uses gravity to open, it won't open if the car points downhill."
> "Press the tailgate button on the exterior bed rail to open the tailgate. The tailgate
> unlatches and slowly opens."

So: **electric latch release only**, gravity drop, damped descent, 100 % manual close. There is no
tailgate motor on Gen 1. Two latch actuators, one per side (forum-level, medium confidence).
Max load on the open tailgate is **1,000 lb (453 kg)** (Tier A).

### 1.2 There is NO switch on the tailgate itself

Owner's Guide p.16 "Truck Bed Exterior View" lists six bed items; none is on the tailgate. There
is no exterior handle, no recess, no release in the tailgate skin. **This is the single most
important negative result in this document:** the prior design had nothing to relocate because
the thing it was imagining does not exist. Do not budget a tailgate-mounted switch.

### 1.3 The controls that DO exist, and where

Owner's Guide p.283 gives the exhaustive open list: key fob (double-press button 2), button on the
exterior bed rail, centre display (Access and Security), Rivian app, entrapment button in the bed.
Plus voice ("Alexa, open the tailgate"). **There is no driver-door-panel tailgate control.**

Physical switch inventory, from the p.16 callout diagram:

| # | Rivian's label | Side | Fore/aft | Surface |
|---|---|---|---|---|
| 1 | Gear Tunnel release buttons (×2) | **both** | forward end of rail | **rail TOP face** |
| 2 | Tonneau cover button (if equipped) | driver | rear end of rail | **rail TOP face** |
| 3 | **Tailgate release button** | **driver** | rear end of rail | **rail TOP face** |
| 4 | Air compressor + Gear Guard cable latches | driver | rear, high | inside bed, inner wall |
| 5 | Spare tire compartment lever | driver | rear, floor level | inside bed |
| 6 | Power outlets (120 V) | passenger | rear, high | inside bed, inner wall |
| — | **Entrapment button** (p.284) | **passenger** | rear, under the rail lip | inside bed, inner wall |

Two button variants exist for #3, both flush in a moulded recess in the stippled rail-cap top
face: a **squared two-icon button** on power-tonneau trucks (p.283) and a **plain rounded blank**
without (p.284). The entrapment button is an amber, glow-in-the-dark oval carrying the standard
running-person egress icon.

### 1.4 The bed lights have no switch of their own

Owner's Guide / Upfitting Guide pp.56–57: bed lights come on automatically with the tailgate or
tonneau, and manually either from the centre display or by **pressing the same rail-top tailgate
button while the tailgate is open and unlocked**. Auto-on times out at 2 min, manual at 10 min.

**Therefore the driver-side rail-top button is dual-function.** Covering it costs the owner both
the tailgate release and the only in-bed bed-light control.

### 1.5 Constraints the Upfitting Guide puts on us

* p.65: *"Do not cut, splice, or modify in any way the high-voltage wires and outlet in the truck
  bed. Relocation may be permitted if the wires and outlet itself are not modified."*
* p.65: blocking required lighting such as the **CHMSL** makes the upfitter responsible for
  secondary lighting meeting **FMVSS 108**. A topper blocks the CHMSL, so our hatch CHMSL is a
  *named Rivian requirement*, not a styling choice.
* p.59: accessory ports along the top of the truck bed are rated **2,500 N / 551 lb each**. They
  are the sanctioned mount; we already land on them.
* pp.100–102: the sanctioned upfitter power tap is **J019, the 12 V auxiliary port in the Gear
  Tunnel** — see §4.

---

## 2. The problem this creates for the topper

Our base rails run along `y = ±0.79 m`, 90 mm wide, from `x0` to `x1` — directly over the bed-rail
cap top face. **They cover, on the driver side, the tailgate release (#3) and the tonneau button
(#2) at the rear, and on both sides the Gear Tunnel release buttons (#1) at the front.**

That is four OEM buttons enclosed by our own structure. Losing #3 alone costs tailgate release
plus bed lights.

## 3. The chosen solution: mechanical preservation, not electrical relocation

**Decision: cut sealed access wells through the base rail over each OEM button. Do not touch
Rivian wiring.**

Rationale, in order:

1. Rivian does not publish the rail-button connector, pin count, circuit type (discrete vs
   LIN/CAN), or current. Splicing an undocumented body-control input is unqualifiable and would be
   inventing a switch — exactly what the acceptance criterion forbids.
2. An access well needs zero electrical work, so it cannot affect warranty, cannot fail
   electrically, and needs no re-qualification when Rivian revises the rail module.
3. The OEM button keeps its OEM feel, OEM sealing and OEM lock-state behaviour (forum reports the
   rail button is disabled when the vehicle is locked; the entrapment button is not).

### 3.1 The access well — `OEM_CONTROL_WELL` (custom part, DWG-27-009)

One per covered button, four total:

| Well | Location | Buttons served |
|---|---|---|
| `WELL_TG` | driver rail, rear | tailgate release + tonneau button (one shared well) |
| `WELL_GT_L` | driver rail, forward | Gear Tunnel release, driver |
| `WELL_GT_R` | passenger rail, forward | Gear Tunnel release, passenger |

Construction:

* A through-pocket in the 6061 base rail, `120 × 70 mm` clear, with a `6 mm` raised perimeter land.
* A **flush hinged lid** in the same carbon as the shell, on a concealed leaf spring, with a
  detent that holds it open so the button can be pressed one-handed.
* An **EPDM bulb seal** on the land, same section as every other seal in the design (one seal PN
  for the whole product).
* A **drain slot** at the lowest corner of the pocket, outboard, discharging onto the OEM rail
  cap outside our seal line — water that gets past the lid never reaches the bed.
* Clear depth under the lid: `28 mm`, enough for a gloved fingertip; verified by
  `checks_step27.py::check_control_well_access`.

### 3.2 Ergonomics

The well lid sits `≈ 40 mm` above the OEM button plane (base-rail height). Reach is from outside
the truck, standing at the rear quarter — the same posture as pressing the button today. The lid
opens **outboard** so the user's hand is not over the topper body. Actuation is: flip lid, press
OEM button, release lid; the lid self-closes under its spring.

### 3.3 Service

The well lid is removable with two M4 captive screws from inside the topper. The base rail is
bolted, not bonded, at the well stations, so the whole rail section over a button can be dropped
for OEM service access without disturbing the shell bond line.

### 3.4 Functions preserved, and residual losses

| Function | Preserved? | How |
|---|---|---|
| Tailgate release (rail button) | **yes** | `WELL_TG` |
| Bed lights (same button) | **yes** | `WELL_TG` |
| Tonneau button | **yes** | `WELL_TG` (shared) |
| Gear Tunnel release ×2 | **yes** | `WELL_GT_L`, `WELL_GT_R` |
| Entrapment button (passenger inner wall) | **yes** | never covered — it is inside the bed volume, which the topper encloses rather than blocks |
| 120 V bed outlets (passenger inner wall) | **yes** | inside the enclosed volume |
| Air compressor / Gear Guard latches | **yes** | inside the enclosed volume |
| Spare-tyre lever | **yes** | inside the enclosed volume |
| **CHMSL** | **NO — blocked** | topper-mounted secondary CHMSL on the hatch leaf, per FMVSS 108, as Rivian's guide requires |

**Net: no OEM control is lost.** The only blocked OEM item is the CHMSL, which Rivian's own
upfitting guide tells us to replace.

---

## 4. Topper electrical — the sanctioned tap

Upfitting Guide pp.100–102, verbatim-sourced:

| Attribute | Value |
|---|---|
| Port | **J019, 12 V auxiliary port, in the Gear Tunnel** |
| Voltage | **13.5 V nominal, 14.1 V in Low Voltage Maintenance** |
| Current | **15 A continuous, 20 A maximum** |
| Mating connector | **Aptiv 13897598** |
| Terminals | **Aptiv 12034047** |
| Wire | **14 AWG (2.5 mm²) PVC** or **16 AWG (1.5 mm²) XLPE** minimum |
| Ground | Module Zone Controller South (Service Manual LC 782246010) |
| Vehicle-off | available via **Camp Mode** |
| Service ref | Labor Code 781013010 |

Topper loads on this feed: secondary CHMSL, interior lighting, optional cage fan. Our estimated
draw is well inside 15 A; the exact figure is set once the CHMSL PN is resolved.

Routing: J019 sits in the Gear Tunnel, **forward of the bed**, so the topper harness enters at the
front bulkhead, under the shell's forward cantilever, and runs inside the shell above the seal
line to the hatch. That is the same interior channel the release cables use.

**Not published, must not be guessed:** the J019 **pin count and pinout**. Rivian gives the
connector and terminal PNs but no pinout. Resolve from the Aptiv catalogue for 13897598 or from
the Service Manual before the harness drawing is released.

---

## 5. Open gaps — measure, do not estimate

Rivian publishes no dimensioned position for any of these buttons. The access wells are therefore
parameterised, and their `x` positions in `params.json` are **provisional** until taped:

| # | What to measure | Feeds |
|---|---|---|
| T1 | Tailgate button centre: X from bed rear face, Y from outboard rail edge | `WELL_TG` position |
| T2 | Tonneau button centre, same datums | `WELL_TG` size |
| T3 | Gear Tunnel button centres, both sides | `WELL_GT_*` positions |
| T4 | Button footprint + recess depth, both variants | well clear opening |
| T5 | Rail cap cross-section (width, crown, edge radii) | seal land + well land |
| T6 | Entrapment button position (to confirm our interior closeout clears it) | hatch interior closeout |
| T7 | J019 pin count / pinout | harness drawing |
| T8 | Whether the forum-reported L/R manual latch release strings behind the inner bed-wall trim are real | emergency egress procedure |

Derived, not cited: the bed-rail top face is **≈465 mm above the bed floor**, from the Upfitting
Guide's cited "bed height, tonneau open = 18.3 in (465 mm)". That is a bed-height figure, not
explicitly a rail-cap plane, so treat it as **medium** confidence and confirm with T5.

---

## 6. What this section does NOT claim

No physical verification on Nate's truck has happened. No OEM part number for the rail button,
its connector, or the latch actuators was found — Rivian does not publish them and this design
does not need them, because it touches none of them. The manual-latch-release-string report is a
single forum thread and is recorded as unverified, not designed against.
