# Step 27 continuation — producer result

**Model: `claude-opus-5-5`.** Verified, not assumed: the session runs `opus[1m]` from
`~/.claude/settings.json`, and every recent transcript in `~/.claude/projects/-home-n8/*.jsonl`
on this host records `"model":"claude-opus-5-5"`.

**Scope.** This run answers the 2026-09-27 operator continuation appended to Step 27. It does
**not** claim Step 27 complete, does not advance to Step 21, answers no card, buys nothing, and
claims no Nate sign-off.

---

## 0. What was rejected, and what this run did about it

| Nate's rejection | What changed |
|---|---|
| "the latch is only meaningless white square chunks" | Every latch is now a **Southco R4-30-41-501-20** two-stage rotary latch modelled to its published 77 x 19.4 x 34.8 envelope, 38.1 mm hole pattern and Ø7.8 panel prep, with a **R4-90-321-20** striker bolt (Ø12.7 shoulder). Blender no longer models any latch — it **imports the CAD**. |
| "rear window/hatch opening is not engineered" | Authoritative surround, seal datum stack, glazing rebate + mechanical retainer, JW Winco GN 7233 hinges, solved Stabilus 6541IS strut anchors, gutter and two C-pillar drains, interior closeouts, and solid interference checks shut and at 95°. |
| "actual R1T tailgate switch/control details are missing" | Researched from Rivian's own PDFs. The answer is a **negative result that changes the design**: the Gen-1 tailgate has no switch on it, and the one that matters faces **up** on the driver-side bed-rail cap — exactly where our base rail lands. See `TAILGATE_CONTROL.md`. |
| "styling still does not blend / match the R1S profile" | **Not addressed this run.** Named as the largest open gap in §6. |
| "authoritative CAD and drawings are missing" | `out/R1T_TOPPER_STEP27.step` (+ open state), 153 per-part STLs with a material/process/finish manifest, 5 section views, 8 dimensioned drawing sheets, 59 machine checks. |

---

## 1. Commands, in order, all re-runnable

```bash
cd ~/text-to-cad-worktrees/r1t-opus-pass/models/r1t_topper/step27
PY=/home/n8/text-to-cad/.venv/bin/python

$PY cad/checks_step27.py        # -> STEP27_CHECKS_PASS, 59/59
$PY cad/assembly_step27.py      # -> STEP27_EXPORT_OK; STEP, 153 STLs, 5 sections
$PY cad/make_drawings.py        # -> 8 drawing sheets
$PY cad/make_bom.py             # -> BOM27.md

cd ../blender
blender-loop init r1t-step27 --intent "..."
blender-loop step r1t-step27 --label S1_truck  --script $PWD/s1_truck.py --fresh
blender-loop step r1t-step27 --label S2_shell  --script $PWD/s2_shell.py
blender-loop step r1t-step27 --label S3_sockets --script $PWD/s3_sockets.py
blender-loop step r1t-step27 --label S4_modules --script $PWD/s4_modules.py
blender-loop step r1t-step27 --label S5_hatch_roof_base --script $PWD/s5_hatch_roof_base.py
blender-loop step r1t-step27 --label S7_hardware_closed  --script $PWD/s7_hardware.py
MECH_SUBSET=one                blender-loop step r1t-step27 --label S10_station_closed \
    --script $PWD/s8_mechanism.py --fresh
MECH_SUBSET=one STEP27_STATE=open blender-loop step r1t-step27 --label S10_station_open \
    --script $PWD/s8_mechanism.py --fresh
```

Evidence: `~/evidence/blender-loop/r1t-step27/{ledger.json,stills/,scene.blend}`.

---

## 2. Architecture: two files are the truth, everything else derives

* `blender/params.json` — vehicle and shell dimensions (unchanged from the previous pass).
* `step27/hardware.json` — **every** latch/seal/strut/locator/control part: manufacturer,
  orderable PN, per-dimension provenance (`DATASHEET` / `DATASHEET_ARCHIVED` / `ESTIMATED` /
  `CUSTOM`), source URL, and what is still unresolved.

`cad/hw.py` reads the catalogue and builds solids. `cad/side_socket.py` and `cad/hatch.py` place
them. `cad/assembly_step27.py` exports STEP + per-part STL. **The Blender lane imports those
STLs.** A still therefore cannot show geometry the authoritative CAD does not contain — which was
the structural cause of the "white square chunks", not an oversight.

---

## 3. Acceptance item by item

### 3.1 Latch hardware (item 1) — done, with two named open questions

| Function | Part | Status |
|---|---|---|
| Rotary latch, two-stage, stainless | Southco **R4-30-41-501-20** (10 off) | ORDERABLE |
| Striker bolt, Ø12.7 shoulder, M10x1.5 | Southco **R4-90-321-20** (10 off) | ORDERABLE |
| FMVSS-206 support plate | Southco **R4-38-101-10** | ORDERABLE |
| Release cable | Southco **AC-C**-scheme, type 9, jacketed | SERIES_ONLY |
| Release handle + splitter | Southco **AC-75-101-11** + **AC-05-301-11** | ORDERABLE |
| Locating pins, round + diamond | MISUMI **FPBPA6** / **FPBPD6** | SERIES_ONLY |
| Bushing | MISUMI **JBHC10-15** | SERIES_ONLY |
| Bulb seal | Trim-Lok **DD6139** (2nd source Fairchild TS1014) | ORDERABLE |
| Compression limiter | CUSTOM, UHMW, DWG-27-006 | CUSTOM |
| Anti-rattle plunger | McMaster **85015A51** | ORDERABLE |
| Keyed T-handle | Southco **E3-18-15** / **E3-108-015**, CH751 key-alike | ORDERABLE |
| Striker bracket | CUSTOM, 316 SS, DWG-27-004 | CUSTOM |

Things the research corrected that would otherwise have shipped wrong:

* **There is no Southco R4-40 family.** The previous pass's "R4 series, dash # TBD" pointed at a
  family that does not exist.
* **The custom release lever is deleted.** It existed only to pull two cables with equal travel;
  Southco's **AC-05-301-11** splitter already does that. One fewer custom part and drawing.
* **10 mm H7 bushings do not exist at MISUMI** — at d = 10 every JBH variant is **G6**. The whole
  pin/bushing fit is re-specified to 10 G6.
* **The seal is a push-on channel, not a groove seal**, so the frames carry a 3.0 mm retention
  **rib** sized into Trim-Lok's published .060–.125 in grip range.

Kinematics are proven by solid intersection, not asserted: 0° is the **receiving** position
(mouth faces the entry slot), the bar drives the fork to **58°** where the outer horn blocks the
escape corridor by 357 mm³, with a secondary catch at **30°** still blocking 56 mm³ — that is the
car-door "click-click". Released, the corridor measures **0 mm³**. A shut latch has **zero**
interference with its own striker; capture is a blocked escape path, and the check now says so.

Tolerance stack, service access, weather and anti-rattle all have their own checks (§4).

### 3.2 Rear window / hatch opening (item 2) — engineered

* Authoritative surround with the seal **datum stack** derived, not guessed: the surround face
  sits exactly one leaf thickness plus one compressed-seal height inboard of flush, so the bulb is
  at its designed 33 % deflection with nothing shimmed at assembly.
* Glazing: 5 mm hard-coat PC in a 9 mm rebate, retained by a **bonded retainer strip** as well as
  urethane — a bond-line failure cannot release a pane. Rebate leaves a controlled 4 mm bead.
* Hinges: **JW Winco GN 7233-NI-50-L/R-MT**, 120° rated, 750 N radial per pair against a ~5 kg leaf.
* Struts: **Stabilus 6541IS** (150 N, 150 mm stroke, 375.5 mm extended). Anchors were **solved**,
  not placed: installed length runs 237.7 → 369.5 mm, inside 225.5–375.5 with margin at both ends,
  monotonic through the swing, minimum moment arm 70.2 mm. Hold-open ratio 1.8×; close force 50 N.
* Gutter above the aperture with outboard fall, and two C-pillar drains discharging **below and
  outboard of the seal line**.
* Interior closeouts on quarter-turns, checked clear of the strut path.
* Solid interference, shut: clean. This check found and forced three real fixes — the latch flange
  fouling the leaf's inner skin, the hinge bosses buried in the leaf, and the drains stopping
  3 mm short of the seal bottom.

### 3.3 R1T tailgate control (item 3) — researched, and it changed the design

Full write-up in `TAILGATE_CONTROL.md`, raw log with page citations in
`research/tailgate_switch_research.md`. Headlines, all Rivian-primary:

* The Gen-1 tailgate is **manual** — electric latch release, gravity drop, damped, closed by hand.
  Stated three ways on Owner's Guide p.283.
* **There is no switch on the tailgate.** Nothing to relocate, because it does not exist.
* The tailgate release is **flush in the TOP face of the driver-side bed-rail cap, at the rear** —
  and it is **also the only in-bed bed-light toggle**. Our base rail covers it, plus the tonneau
  button and both Gear Tunnel releases.
* Solution: **sealed access wells** through the base rail. No splice, no relocation, no added
  switch — Rivian publishes no connector or pinout for that button, so wiring into it would be
  inventing a switch, which is exactly what the acceptance forbids.
* The **entrapment button** (passenger inner wall, under the lip) survives a topper install and is
  the one in-bed physical release that still works.
* Topper power is the sanctioned **J019** Gear-Tunnel port: 13.5 V (14.1 LVM), 15 A cont / 20 A
  max, **Aptiv 13897598** connector with **12034047** terminals, 14 AWG PVC min, grounded at
  Module Zone Controller South.
* A topper **blocks the CHMSL**, and Upfitting Guide p.65 makes the upfitter responsible for
  FMVSS 108 secondary lighting. Our hatch CHMSL is now a cited requirement with a real part:
  **Maxxima M63319R** (SAE J1957 / **U3**), 394 x 32 x 19, 370 mm hole centres.

### 3.4 Styling (item 4) — NOT DONE

No styling work happened this run. See §6.

### 3.5 Authoritative CAD (item 5) — done for the Step 27 subsystems

`out/R1T_TOPPER_STEP27.step`, `out/R1T_TOPPER_STEP27_open.step`, 153 per-part STLs,
`out/parts_manifest.json` (material / process / finish / mass / PN per part), 5 section views
(`drawings/SEC-27-*.svg`), 8 dimensioned drawing sheets (`drawings/DWG-27-*.svg`) with tolerances
and notes. The **carbon shell itself is still Blender-authored** and is not in the STEP — that is
open item G3 below.

### 3.6 BOM (item 6) — 9 ORDERABLE, 5 SERIES_ONLY, 0 OPEN

`BOM27.md`, generated from `hardware.json` + the parts manifest. Every purchased row carries a
manufacturer, a part number and a source URL. Every fabricated row carries material, process,
finish, drawing and critical tolerances. **Five items are SERIES_ONLY** — series and scheme
resolved, final dash number needs a vendor configurator input we do not have. Those five are
named, not hidden, and they are why this step is not complete.

### 3.7 Evidence (item 7) — partial

Done: CAD-imported mechanism stills shut and released, section views, drawing sheets, the check
suite with its own "not checked" list. **Not done:** real-R1T-context photoreal multiviews and
the animation showing the new hardware. See §6.

---

## 4. The check suite — `cad/checks_step27.py`, 59/59

Groups: socket identity across all four; one module interface mating all four; fork/striker
capture by solid intersection in three states; latch static margin; weight path; closing sequence;
seal deflection and grip; limiter setting the gap; tolerance stack and shut line; cable bend
radius; release travel; service access; anti-theft; strut stroke and monotonicity; hatch mass,
hold-open and close force; leaf clearances; shut-state interference; glazing retention; drainage;
closeout clearance; control-well access; CHMSL requirement; harness tap; hinge envelope; BOM
completeness.

**Defects the suite found and forced fixed this run** (all of these were silent before):

1. `export_stl` does not compose nested Compound locations — most parts exported at the origin.
2. The de-duplicating exporter collapsed 8 latches into 1.
3. The material classifier matched on `startswith` and fell through to steel density, inflating
   the mass rollup 3×.
4. The strut moment arm used an unprojected 3-D cross product, over-reporting by ~80 %.
5. The latch flange, hinge bosses and drains all fouled or fell short.
6. The striker bracket offset put the bolt's **thread** in the fork and the shoulder 40 mm clear.
7. The fork kinematics were inverted — 0° was being treated as shut when it is the receiving position.

Explicitly **not** checked, and printed as such by the suite: FEA, sealing performance, real-truck
fit, vendor endurance/salt-spray/UV data, solid interference of the leaf against the carbon shell,
and every later gate.

**One open engineering question, stated rather than buried:** Southco publishes a 10 675 N average
ultimate static load for the R4-30 **and** a 222 N max **dynamic** working load. Our computed
service pull is 383 N per latch. We read the 222 N as a door-slam rating that does not govern a
sustained aerodynamic/cornering pull — **that reading is ours, not Southco's.** Confirm with
Southco before fabrication release. If it does govern, the fix is a third latch per socket, and
the flange already has room.

---

## 5. Where the files are

```
models/r1t_topper/step27/
  hardware.json          vendor + provenance truth for every fitting
  TAILGATE_CONTROL.md    Gen-1 control research + the preservation design
  research/tailgate_switch_research.md   raw log, page-cited
  BOM27.md               generated BOM
  cad/  hw.py geom.py side_socket.py hatch.py checks_step27.py
        assembly_step27.py make_drawings.py make_bom.py
  out/  R1T_TOPPER_STEP27.step, _open.step, parts/, parts_open/, parts_manifest.json, checks.json
  drawings/ SEC-27-001..005, DWG-27-001..009
models/r1t_topper/blender/
  s7_hardware.py         imports the CAD into the topper scene
  s8_mechanism.py        hardware-only mechanism close-ups
```

---

## 6. Open gaps — nothing here is hidden

| # | Gap | Why it is open |
|---|---|---|
| G1 | **Styling / R1S profile match** | Untouched this run. The shell is unchanged from the previous pass. This is the largest remaining item and needs its own pass. |
| G2 | **Real-R1T-context photoreal renders + mechanism animation** | The mechanism stills are CAD-accurate but the vehicle is still the dimensioned proxy, and no animation was rebuilt against the new hardware. |
| G3 | **The carbon shell is not authoritative CAD** | Sockets, hatch and hardware are STEP. The shell is still Blender-authored; the build123d shell has not been regenerated from this geometry. |
| G4 | **5 SERIES_ONLY BOM rows** | Cable dash number, both MISUMI pin dash numbers, the bushing, and the Stabilus column choice each need one vendor-configurator input. |
| G5 | **GN 7233 is a linkage, not a fixed pivot** | Every clearance and strut number assumes a pure rotation about the design axis. Re-run against JW Winco's CAD coupler curve. |
| G6 | **R4-30 internals are a representation** | Southco does not dimension the claw throat and renders the hole table as raster art. Envelope and mounting are datasheet; the mechanism is ours. |
| G7 | **Tape measurements T1–T8** | Rivian publishes no dimensioned button position, no J019 pinout. The control wells are parameterised but provisional. |
| G8 | **Mass not optimised** | 71.6 kg of Step 27 hardware. Frames are lightened but not properly pocketed. |
| G9 | **Southco dynamic-vs-static rating** | §4. |

Later gates, unchanged and unclaimed: FEA, prototype fit, real-truck calibration, fabrication
release, purchasing, and **Nate-only design approval**.

---

## 7. Continuation plan, in order

1. **Styling pass (G1).** Gather R1T and R1S reference photography, rebuild the shell section
   profiles against the cab-to-topper transition, shoulder line, rear-corner wrap and glazing
   proportion. Keep the socket and hatch interfaces fixed — they are now parametric off
   `params.json`, so the skin can move without re-cutting the hardware.
2. **Regenerate the shell as build123d (G3)** from the styled sections, then re-run
   `checks_step27.py` with the leaf-against-shell interference check switched from
   bounding-box to solid.
3. **Animation + photoreal (G2)** off the new shell, driven by the CAD states already exported
   (`out/parts` and `out/parts_open`).
4. **Close the 5 SERIES_ONLY rows (G4)** with Southco's cable configurator, MISUMI's live pages
   and one Stabilus question about the two Ref.-No. columns.
5. **Vendor CAD for GN 7233 and R4-30 (G5, G6)**, then re-run the strut solve and the clearance
   checks against the real motion path.
6. **Tape session (G7)** — the 8 measurements listed in `TAILGATE_CONTROL.md` §5.
7. Only then: FEA, prototype, Nate review.

## 8. Commit

Branch `agents/claude/r1t-opus-pass`, parent `ee390669`. Local only, not pushed.
Commit **`d570ccfb74fe69e29f0414ed20c7b6c485dc319e`** (also in `out/COMMIT.txt`).
