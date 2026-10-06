# Step 29 — revision pass on Nate's change request (card 2081357)

**Producer:** claude-sonnet-5-5 mesh worker, task 139737 (project 924515 Step 29), 2026-10-06, with one
`default`-role subagent for the attachment redesign (its branch merged here). Builds on Step 27 rev 10
(`0996915`, verified, **not edited**: this is a new branch off that pin). Design package only: no fitment,
structural, sealing or fabrication claim; no Nate approval claimed; nothing purchased.

Nate, verbatim: *"1) back hatch. a topper is meant to allow the truck tail-gate to open, and the hatch of the
topper to open, and then have a large access to truck bed. your version has a crossbar where there should be
none. 2) it appears you do not understand the rivian custom attach points that the topper needs to connect to.
the topper is meant to connect to the truck bed the same way that the rivian crossbars attach. there is a
clever hardware gizmo."*

## 1. Rear hatch / tailgate access (acceptance 1)

**What was wrong.** Rev 10's hatch was a 1000 × 226 slot starting 100 mm above the rail with a fixed band
(shell wall + surround bottom run, z 0…97) under it: a bar across the lower rear.

**What changed** (`cad/hatch.py`, `blender/params.json` hatch block, `cad/shell.py`):
* aperture 1000 × **292**, lower edge 34 mm up the raked face (was 100): the carbon leaf now starts 1 mm above
  the rail-cap plane (z) and runs up to the roof roll-off. Leaf 1052 × 344, 3.75 kg (was 3.28).
* the surround's bottom run (land, recess wall, bond flange, return lip) and its seal are **removed between two
  corner stubs** (`HA.STUB_X` = 390 mm) and everything is clipped to z >= 0. The stubs carry only the two latch
  carriers; nothing fixed crosses the opening below the roof header. The 2 skin-exit drain tubes are deleted:
  the wet channel is open at the stub ends.
* struts re-solved by `hatch.solve_struts`: 6462II no longer solves; **Stabilus 6467IK** (50 N, 150 stroke,
  375.5) selected; hold-open ratio 1.70, close force 1.9 N; price EUR 67.18 read 2026-10-06
  (USD 75.90 derived at the store's own display rate, labelled so in `research/pricing_2026-10.json`).

**Evidence (all CAD-solid checks, `cad/checks_step27.py::check_rear_access`):**
`rear_doorway_free_hatch_open` (208 parts vs a 778 × 324 mm doorway from the rail-cap plane to the aperture top,
hatch at 95°: zero volume), `no_fixed_crossbar_across_rear_opening` (16 horizontal slices, none crossed by a fixed
part), `hatch_open_clear_of_lowered_tailgate` (tailgate folded flat at the bed floor, `truck.tailgate_lowered_keepout`),
`rear_opening_larger_than_rev10`, plus the existing 0…95° sweep, interference, flange and strut checks.
**Renders** (`evidence/r29/`, Blender/Cycles on the traced R1T proxy, run `r1t-step29-final`, script
`blender/s17_access.py`): hatch up + tailgate folded down + a 0.70 × 0.60 × 0.55 m cargo proxy half-way in
(`S17_access_access_rear3q.jpg`, `_rear.jpg`, `_side.jpg`, `_top_rear.jpg`); 10/10 rays from the cargo back
through the doorway hit no topper part; closed view `S13_hero_hero_rear3q.jpg`.
**Open (named):** the leaf's lower-edge seal onto the tailgate cap is not designed
(`rear_leaf_bottom_seal_on_tailgate`, after the tape session); the leaf is held shut by the two corner latches
only, so leaf stiffness along its free lower edge is an FEA item. Renders are not photoreal and not Nate's truck.

## 2. Mounting interface (acceptance 2)

Researched 2026-10-06 (`research/PORT_MECHANISM_SOURCES.md`): the Rivian crossbar end is a foot with a hinged
**two-stage paddle latch** (click 1 = caught on the port cleat/latch pins, click 2 = paddle down = clamped), a
**key lock under the paddle**, release = lift paddle + unlock, and a latch-tuning adjustment (R1T Owner's Guide
2022-10-17 pp.152-154); the port is a rounded-rect recess in the bed-rail cap with a dual-barrel pin pair, 2,500 N
per port (Upfitting Guide p.59). Rev 10's Weistec M10 stud/nut adapter was an assumed bolt interface, not this.

Replaced by a **Port Latch Foot** x4 emulating that mechanism (`cad/mounts.py`; parts `PLF_BODY_6061`,
`PLF_HOOK_SLIDER_17_4PH`, `PLF_PADDLE_6061`, `PLF_LOCK_CYLINDER_COMPX`, ...): two hook teeth 25 mm apart, inboard
drop-down paddle (closed 0°, stage 1 at 68°, open 82°), key lock covered by the closed paddle. Removal =
four keys + four paddles + lift, same as the Rivian crossbars. Full description, loads, install/service and the
researched-vs-verified table: `MOUNTING27.md`; mounting-interface provenance recorded in the BOM: `BOM27.md` §7
(reference article, fallback, sources). **Everything at the port / foot is PROVISIONAL**: Rivian publishes
neither the port internals nor the crossbar-foot drawing (OPEN `plf_port_internals_P-CAL-01b`; calibration =
buy one Rivian R1 Cargo Crossbars set and measure it). Open design items from the producer's own checks: paddle
cam-to-slider link and lock keeper not drawn (`plf_drive_link_and_lock_interlock`); **the 33 %-compressed EPDM
pad may need up to ~2.8 kN per station to reach its stop vs 219 N of dead weight, which a paddle clamp may not
supply — shrink/soften the pad or prove the clamp** (MOUNTING27 §5); LC6 crash pulse 2.5 kN vs the 2.5 kN port
rating reported OPEN; lock dimensions estimated and its price from a third-party listing.

## 3. Checks, regeneration

`checks_step27.py`: 97 PASS, 0 FAIL, 11 OPEN (`out/checks.json`). Order unchanged from RESULT27 §1
(`assembly_step27.py` now also writes `out/parts_access`), then `cad/provenance.py`. Blender lane from
`models/r1t_topper/blender/` (CPU Cycles, `R1T_HDRI` optional): S11, S12, S13, S16_mount, S17_access.
