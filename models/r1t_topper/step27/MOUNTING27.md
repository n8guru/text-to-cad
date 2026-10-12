# Step 27 rev 11 — attaching the topper to the truck: the Port Latch Foot

> **Step30 supersession:** read [STEP30_MOUNTING.md](STEP30_MOUNTING.md) first.
> The current CAD uses C-jaws around one provisional continuous bridge, not the
> isolated-pin/flat-tooth concept described below. Historical screening values,
> including the 24 kg roof-load arithmetic, are NOT ratings or operating limits
> for the revised topper. This retained document is the Step29 rationale/history.

**Task 139737, project r1t-topper Step 29, repo n8guru/text-to-cad.** Replaces the rev-10 design (task
136191: a purchased Weistec adapter with an M10 stud / nut / Nord-Lock stack at each of four ports).
Design package only: nothing purchased, quoted or fabricated; no fitment, structural or sealing result is
claimed; no Nate approval is claimed.

Sources of truth: geometry `cad/mounts.py` (dimensions in `blender/params.json` → `mount`), inputs
`hardware.json` → `port_latch_foot`, `plf_lock`, `plf_detent`, `crossbar_reference`, `mounting`; joint
J01 in `cad/fasteners.py`; checks `cad/checks_step27.py::check_mounting` (+ `check_plf_kinematics_exported`);
numbers `out/mounting_analysis.json`; sweep `out/kinematics.json` → `port_latch`; sources
`research/PORT_MECHANISM_SOURCES.md`.

---

## 1. Why it was redone (operator card 2081357)

Nate: *"it appears you do not understand the rivian custom attach points that the topper needs to connect to.
the topper is meant to connect to the truck bed the same way that the rivian crossbars attach. there is a
clever hardware gizmo."*

Correct. Rev 10 assumed a stud-and-nut interface (a bolt-on port adapter). That is **not** how the Rivian
crossbars attach. The accepted design emulates the crossbar-end mechanism.

## 2. The mechanism being emulated (researched — not verified on hardware)

Each Rivian crossbar END is a foot with a hinged **paddle** latch (Owner's Guide 2022-10-17 p.152-154):

1. **Lift the paddle**, set the foot into the accessory port — **click 1**: the foot is caught on the port's
   cleat / latch pin. Centre it, **push the paddle down** — **click 2**: clamped. "If you don't hear two clicks
   the crossbar may not be latched."
2. A **key lock cylinder** sits under the paddle; the closed paddle covers it. Lock with the key (clockwise).
3. Remove: push the paddle up halfway to reach the lock, unlock, lift the paddle while raising the bar.
4. The latch can be **tuned** ("Crossbar latch tuning", p.154).

The port is a rounded-rectangular recess in the rail cap with a cleat / **dual-barrel latch-pin pair** (two
anchor points per port; Mars Adventure Gear: two M8 points 25 mm apart). Rating **2,500 N per port**; Rivian
forbids modifying the ports (Upfit Guide 2025-09-24 p.59). URLs and fetch dates:
`research/PORT_MECHANISM_SOURCES.md`.

## 3. Researched vs physically verified

| Item | Researched? | Verified on hardware? |
|---|---|---|
| Foot + hinged paddle, two clicks, lock under paddle, tuning | yes (Owner's Guide p.152-154, trailrivian.com) | **no** |
| Port = recess + dual-barrel pin pair, 2 anchors 25 mm apart | yes (Team 1EV, Mars Adventure Gear, Upfit p.59) | **no** |
| 2,500 N per port; do not modify | yes (Upfit p.59) | Rivian's value, not tested |
| Port recess size / depth, pin dia / position, Rivian foot hook / paddle / lock geometry | **not published** | **no — PROVISIONAL** |
| Paddle, hook, lock, detent geometry of OUR foot | designed here (assumption-level) | **no** |
| CompX C8053 lock dimensions | listing only (compx.com 403) | **no — ESTIMATED** |

Every dimension at the port or in the Rivian foot is flagged: OPEN check `plf_port_internals_P-CAL-01b`.

## 4. The Port Latch Foot (PLF), ×4 — one part, passenger side rotated 180°

Station frame: x along the rail, u OUTBOARD, z up from the rail-cap top. Parts (exact manifest names):

| Part | Material / process | What it does |
|---|---|---|
| `PLF_BODY_6061` | 6061-T6, 5-axis CNC, hard anodise III (DWG-27-012) | **stem** 62 × 26 drops through the foot pocket into the port recess; **seat flange** (z 0–4) bears on the rail cap and is the pad's compression STOP; **head** sits in a notch of the base rail; two hinge ears; hook-slider cross-slot, two pin channels, lock bore, rail-screw and tuning-screw holes |
| `PLF_HOOK_SLIDER_17_4PH` | 17-4 PH H1025, wire-EDM + ground (DWG-27-013) | comb slider, **two hook teeth 25 mm apart** that slide under the port's two latch pins; dwell while the paddle goes closed → stage 1, retracts 6.5 mm between stage 1 and open |
| `PLF_PADDLE_6061` | 6061-T6 CNC (DWG-27-013) | hinged **drop-down paddle on the INBOARD face**, axis ∥ rail; closed it covers the lock and the tuning screw |
| `PLF_LOCK_CYLINDER_COMPX` | purchased CompX National **C8053-C346A-14A** | key cam lock under the paddle; keyed alike, one key for four feet |
| `PLF_HINGE_PIN_5x76_A4` | ISO 2338 d5 m6, cut to 76 | paddle hinge |
| `PLF_DETENT_PLUNGER_M8` | purchased M8 ball plunger (McMaster 85015A51) | two detents: stage 1 (68°, click 1) and closed (0°, click 2) |
| `PLF_TUNE_SCREW_M6x20_A4` | ISO 4026 set screw | latch tuning: closed-stop screw under the paddle |
| `PLF_RAIL_SCREW_M6x30_A4` ×2 | ISO 4762 A4-70 | fasten the base rail strip to the body **at the shop** |
| `PLF_SHIM_316_1p0` ×2 | 316, 1.0 mm | across-rail fit-up pack (0–4 mm with the kit) |

Also changed: `BASE_RAIL_6061_L/R` (U-notch per foot + tapped strip), `FOOT_PAD_EPDM_L/R` (cut around the
flange), shell foot pockets (`mounts.foot_cuts()`). **Removed from the primary design:** Weistec adapter,
M10 stud / nut, Nord-Lock, slot washer, port spacer, shims (kept only as the documented fallback,
`hardware.json` → `port_adapter`, BOM section 2c).

### 4.1 States and the sweep (`out/kinematics.json` → `port_latch`)

| State | Paddle | Hooks (cam law, PROVISIONAL) | Lock |
|---|---|---|---|
| Open | 82° inboard (lies out over the bed side) | retracted 6.5 mm: 2.8 mm clear of the pins; the foot can be dropped in / lifted out | face exposed |
| **Stage 1 — "caught"** | 68° (detent, click 1) | teeth under the pins, tip 0.55 mm past the pin centre | key reaches the face (check `plf_key_reaches_lock_at_stage1`) |
| **Stage 2 — closed** | 0° (detent, click 2) | teeth on the pins, tip 1.0 mm past centre | covered by the paddle |

The sweep is computed for 0–80° in 5° steps + stage 1 + open at all four stations against the whole closed
assembly and the cab / body / tailgate keep-outs (`plf_paddle_sweep_clear`). **Difference from Rivian,
stated:** our paddle must reach 68° (not "halfway") for a straight key shank to clear it, because the lock face
is covered by a full-height plate.

### 4.2 Load path at stage 2 (closed) — all metal (`plf_stage2_load_path_metal_to_metal`)

port pin → hook tooth → slider bar → slot floor → body → 2 × M6 (shear) + shim pack → 6061 rail strip →
bond line → carbon foot. The EPDM pad (33 % compressed) is **not** in the clamp path; the seat flange sets
the height (`plf_seat_flange_is_the_pad_stop`).

### 4.3 Fit-up (`plf_fit_up_float_covers_tolerance`)

±3 mm along the rail (notch clearance), 0–4 mm across (shim pack, nominal 2), ±3 mm in height (slotted screw
holes) against ±3 / ±2 / ±1 required for port-position and moulding variation. The rail taps are match-drilled
from the body at shop fit-up; the foot pockets are cut after the port centres are taped (P-CAL-02).

## 5. Loads (stated cases, not a standard, not FEA)

Topper system **89.26 kg**, CG (706.8, 0.7, 205.5) mm. Worst port per case (`out/mounting_analysis.json`):

| Case | g (x/y/z) | Compression N | Tension N | Shear N | **Resultant N** | Class |
|---|---|---|---|---|---|---|
| LC1 vertical bump | 0/0/−3 | 694 | 0 | 0 | **694** | limit |
| LC2 rebound + 600 N lift | 0/0/+1 | 0 | 381 | 0 | **381** | limit |
| LC3 braking | −1/0/−1 | 338 | 0 | 219 | **402** | limit |
| LC4 cornering | 0/1/−1 | 295 | 0 | 219 | **367** | limit |
| LC5 off-road | −0.5/0.7/−2 | 560 | 0 | 188 | **591** | limit |
| LC6 forward crash pulse | −10/0/−1 | 1,293 | 856 | 2,188 | **2,542** | ultimate (info) |

* All limit cases are far inside Rivian's 2,500 N per port (`port_loads_within_rivian_rating`).
* **LC6 is reported, not passed:** 2,542 N per port is 1.7 % over the rating (OPEN `port_crash_pulse_vs_rating`).
  No regulation covers a cap and Rivian rates the port, not a crash case. Remedy if Step 25 wants crash
  retention: forward tethers to the bed's front tie-downs (Owner's Guide p.297), after P-CAL-04. Not designed.
* Hand check at the port rating (ESTIMATED material values, **not FEA**): each station at 2,500 N → hook tooth
  bending 258 MPa vs 600 allowable (0.6 × Rp0.2 of 17-4 PH H1025), tooth shear 31 MPa, rail-screw shear
  62 MPa vs 270, thread strip-out 19.5 kN, slot-floor bearing 8.5 MPa.
* **A real finding, open (`plf_drive_link_and_lock_interlock`):** the 2B2 foot pad, compressed to the flange stop
  (33 %), reacts up to ~2.8 kN per station (0.255 m² of pad, upper-bound CFD) against 219 N of dead weight per
  station. Rev 10 had 15–20 kN of bolt preload to do that; a paddle latch will not. Before release either
  reduce the pad (short pads at the stations, softer grade, or a thinner free height) or show the paddle
  clamp can pull the foot down without loading the port beyond its rating. The hook force, over-centre
  preload and detent force are **not computed**.
* Benchmark: Rivian allows 113 kg dynamic on a crossbar pair on 4 roof ports; the topper is ~89 kg on 4 bed
  ports, so roof load on the topper's own hardpoints stays limited to ~24 kg dynamic until FEA.

## 6. Installation and service

**Shop (factory step, topper OFF the truck, ordinary fasteners):** fit the four PLF bodies to the base rails
(2 × M6 + shim pack each, Loctite 243 once set), bond the rails to the shell foot, fit slider, paddle, pin,
detent, lock and tuning screw. Set the tuning screw at P-CAL-01b / prototype.

**Field install (two people, no tools):** paddles open (82°) → lower the topper so the four stems drop into the
ports → paddles to stage 1 (click 1: caught) → paddles closed (click 2: clamped) → lock with the key. Check the
four OEM rail-cap buttons press through the control wells; modules latch in all four sockets.

**Field removal (same user experience as removing Rivian crossbars):** stand in the bed with the hatch open;
the paddles and lock faces are INBOARD, in reach (`plf_serviceable_from_bed_no_tools`: lock face normal
toward the bed centre, hand corridor clear, socket-frame ceiling z 66 vs paddle top 61.5). Raise each paddle
to stage 1, unlock with the key, lift the paddle fully and the topper off. **Tool required: the key only.**

## 7. Calibration list — every item is a physical measurement not yet made

| ID | What | Value used | Status |
|---|---|---|---|
| **P-CAL-01b** | Buy ONE **Rivian Cargo Crossbars** set (gearshop.rivian.com/products/cargo-crossbars, Bright $700 / Dark $800, read 2026-10-06) as the reference article. Photograph + measure the foot (hook / tang, paddle, lock position, tuning screw) and, on a real truck, the port (recess L × W × depth, cleat / pin positions, pin diameter and pitch). Set `mount.port_*`, `pin_*`, `hook_*` and re-run | recess 70 × 34 × 30, pins Ø8 at 25 pitch, z −14 | **not done** — PROVISIONAL |
| P-CAL-01c | Received CompX C8053 cylinder: body Ø, flange, cam, key code | Ø19 / 28.7 / flange Ø23 | **not done** — ESTIMATED |
| P-CAL-02 | Tape all four bed-port centres before the foot pockets are cut | (307, ±724), (1154, ±710) | **not done** |
| P-CAL-03 | Rail-cap flatness / profile under the 100 mm pad band | flat, ±1.0 | **not done** |
| P-CAL-04 | Bed front corner tie-downs (optional crash tethers) | — | **not done** |
| T1–T3 | OEM rail-cap button positions (control wells) | x 60 / 1300 | **not done** |

(P-CAL-01 of rev 10, the Weistec adapter envelope, applies only if the fallback is ever taken.)

## 8. Open, named

`plf_port_internals_P-CAL-01b`, `plf_drive_link_and_lock_interlock` (link paddle-cam → slider and lock-cam
keeper not drawn; hook force / preload / detent not computed; pad-set force vs rating), `bed_port_positions_P-CAL-02`,
`port_crash_pulse_vs_rating` (OPEN in the suite); plus the Step 27 items carried from `df01d411` (rear-sill seal,
tape session, latch sustained rating, GN 7233 coupler curve, T-handle grip, control wells, release cable
SERIES_ONLY). FEA, fatigue, water ingress at the pad, real-truck fit, fabrication release and Nate-only
approval are later gates.

## 9. Every other attachment — the joint schedule

`cad/fasteners.py` lists the 17 joints once each (J01 – J17), counts from the geometry. J01 is now the PLF
(4 stations; 8 rail screws, 4 tuning screws, 4 hinge pins as fasteners; 4 locks and 4 plungers as purchased
parts). BOM27 §3 prints it. `every_joint_found_in_geometry`, `joint_counts_match_product_structure` and
`every_fastener_is_specified` check it.
