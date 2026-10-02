# Step 27 rev 10 — attaching / mounting hardware

**Producer:** Claude Opus 5.5 mesh worker, task 136191 (project 924515 Step 27 rev 10).
**Scope (operator, 2026-09-30, Studio insight 75785):** design the topper's attaching/mounting
hardware and a detailed BOM (part numbers, quantity, material, supplier, cost), building on
`agents/claude/r1t-opus-pass@57634ea0` → `df01d411`. Nothing purchased, quoted or fabricated;
no fitment, structural or sealing claim; no Nate approval claimed.

Sources of truth: geometry `cad/mounts.py` (stack derived from `blender/params.json` → `mount`),
engineering inputs `hardware.json` → `port_adapter`, `foot_pad`, `fasteners`, `consumables`,
`mounting`; joint schedule `cad/fasteners.py`; checks `cad/checks_step27.py::check_mounting`,
`check_fastener_schedule`; numbers `out/mounting_analysis.json`.

---

## 1. What attaches the topper to the truck

The R1T gives an upfitter exactly one sanctioned structural interface on the bed: **four bed
accessory ports**, two per rail cap, rated by Rivian at **2,500 N each** (Upfitting Guide
2025-09-24 p.59). Rivian forbids modifying them and does not publish their geometry. Drilling
the rail caps or clamping under them (the conventional cap method) is therefore rejected.

The topper anchors at those four ports through a **purchased, non-modifying adapter** that
latches into the OEM port and presents an M10 thread:

* **Weistec Engineering (Direct Current Engineering) 09-111-00078-7** "Accessory Port Adapter
  for Rivian" — billet 6061, clear anodise, 5-axis CNC, "R1T needs 4 for the bed", accessories
  bolt on "using M10 bolts", "no permanent modification to accessory ports". **$100.00 each**
  (weistec.com, retrieved 2026-10-02). Second source: Mars Adventure Gear port adapter, two M8
  points 25 mm apart, $59 per pair (would need a second station drawing).

### 1.1 The port station (×4) — `SEC-27-008`, `SEC-27-008D`, `DWG-27-010/012/013`

Top down; every height is derived in `mounts.py`, not typed:

| Item | Part | z (mm, rail-cap top = 0) |
|---|---|---|
| Nut | M10 ISO 4032 A4-80, 16 AF, **30 Nm**, Tef-Gel | 42.4 – 50.8 |
| Lock | Nord-Lock NL10ss wedge pair (art. 1575) | 39.0 – 42.4 |
| Slot washer | 316, 40 × 36 × 4, ground — covers the rail obround | 35.0 – 39.0 |
| Base rail | 6061-T6 75 × 25, bonded on the foot; **12 mm wrench pocket**, open to the inboard edge; obround 22.5 × 16 (±6 x / ±2.75 y float) | 22 – 47 (13 under the pocket) |
| **Port spacer = the stop** | 6061, Ø36 × 9.00 ±0.02, in a through-pocket in the carbon foot | 13 – 22 |
| Shims | 316 Ø36, 2 × 0.5 nominal (fit-up kit 0 – 2 mm) | 12 – 13 |
| Port adapter | Weistec 09-111-00078-7, latched in the OEM port, M10 female | ≤ 12 (PROVISIONAL) |
| Stud | M10 × 60 A4-70, cut from DIN 975 rod, Loctite 243 into the adapter, 17.6 engaged, 3.6 past the nut | −5.6 – 54.4 |

Design intent, each a check:

* **Metal-to-metal clamp; the carbon is not in the bolt's clamp path** (`port_stack_metal_to_metal`):
  composite under a bolt creeps and loses preload. The foot is captured indirectly: the rail is
  bonded to it and the pad reacts it.
* **Preload/compression stop** (`pad_compression_set_by_stop`): the EPDM pad under the foot is
  6.0 mm free; when the spacer bottoms on the shims it is exactly 4.0 mm (33 %). Torque cannot
  over-crush the pad or load the paint; ±1.0 mm of foot/rail-cap profile keeps it in 17–50 %
  (`pad_strain_band_15_55pct`). The pad needs < half the minimum preload to seat
  (`pad_seats_within_preload`), so every station reaches its stop.
* **Slip-critical joint** (`port_joint_slip_resistant`): 30 Nm → 15–20 kN preload (K 0.20–0.15);
  μ 0.20 per slip plane gives 3.0 kN at the low preload, ≥ 1.25 × the worst limit shear. The stud
  never bears in its slot under limit loads.
* **Tolerance absorbed, not machined away** (`port_slot_float_covers_tolerance`): ±6 mm along the
  rail, ±2.75 mm across, ±1 mm in height (shims) — truck-to-truck port position and moulding
  variation are dialled out at fit-up.
* **Serviceable with the topper fully built** (`port_nuts_tool_accessible`): the first layout (a
  socket-head screw from above) FAILED its own access check — the socket frames' return lips sit
  ~15 mm above the heads. Fix: stud + nut dropped into a 12 mm pocket milled in the rail top and
  open to the inboard edge, so a 16 mm ratcheting box wrench swings in horizontally from the bed.
  Checked against the closed assembly with all four modules fitted.
* **The studs stay in the truck.** Lift-off = 4 nuts; re-fit = lower the topper over the studs —
  the rail obrounds are the lead-in, so the topper self-locates on its four studs.

### 1.2 Foot pad and foot

ASTM D1056 **2B2** closed-cell EPDM, 1/4 in, PSA one side, 100 mm wide strip under each foot
(Pres-On P9200 is a spec match; any certified 2B2 is interchangeable). The shell foot underside is
relieved by the 4 mm compressed pad height, so the A-surface does not move. Foot widened
115 → 125 mm so the measured rear port (y 710) keeps a full pocket wall.

### 1.3 Loads (stated design cases — not a standard, not FEA)

Mass and CG come from the manifest (mass × centroid per part). Per-port reactions: elastic
bolt-group distribution about the port-pattern centroid. Table regenerated by the check suite
into `out/mounting_analysis.json`; values at this commit:

Topper system mass **88.67 kg**, CG (706.1, 0.7, 206.7) mm (x from the bed front wall, z above
the rail cap). Worst port per case:

| Case | Accel (g) x / y / z | Extra | Compression N | Tension N | Shear N | **Resultant N** | Class |
|---|---|---|---|---|---|---|---|
| LC1 vertical bump | 0 / 0 / −3 | — | 690 | 0 | 0 | **690** | limit |
| LC2 rebound + highway lift | 0 / 0 / +1 | 600 N aero lift | 0 | 380 | 0 | **380** | limit |
| LC3 braking | −1 / 0 / −1 | — | 336 | 0 | 217 | **400** | limit |
| LC4 cornering | 0 / 1 / −1 | — | 293 | 0 | 217 | **365** | limit |
| LC5 off-road combined | −0.5 / 0.7 / −2 | — | 558 | 0 | 187 | **588** | limit |
| LC6 forward crash pulse | −10 / 0 / −1 | — | 1,291 | 856 | 2,174 | **2,528** | ultimate (info) |

Joint: preload 15,000–20,000 N at 30 Nm; slip capacity 3,000 N per plane (μ 0.20, low preload)
vs 217 N worst limit shear.

* All limit cases sit far inside Rivian's 2,500 N per port (`port_loads_within_rivian_rating`).
* **LC6 (10 g forward crash pulse) is reported, not passed:** it lands at 2,528 N per port, 1 % over the 2,500 N rating (friction slip capacity 3.0 kN still holds).
  No regulation covers a cap and Rivian rates the port, not a crash case. Remedy if Step 25 wants
  crash retention: two forward tethers from the shell's front hardpoints to the bed's front
  corner tie-downs (Owner's Guide p.297), after P-CAL-04 locates them. Not designed here.
* **Benchmark** (`mass_within_rivian_4_port_benchmark`): Rivian allows 113 kg dynamic on a
  crossbar pair on 4 roof ports. The topper system is ~89 kg on 4 bed ports, so **roof load on the
  topper's own hardpoints is limited to ~24 kg dynamic** until FEA.

## 2. Every other attachment — the joint schedule

`cad/fasteners.py` lists all 17 joints in the product once each (J01 – J17): count from the
geometry, fastener per joint, torque and treatment (Upfitting Guide p.57 torque table), grip
arithmetic. BOM27 §3 prints it. 204 fasteners of 14 specifications, all A4/316, plus 26 potted
M4 inserts (`DWG-27-018`). `every_joint_found_in_geometry`, `joint_counts_match_product_structure`
and `every_fastener_is_specified` check it.

## 3. Installation (driveway, two people, no drilling)

1. Wash and dry the rail caps; apply clear PPF over the pad footprint if desired.
2. Latch the four Weistec adapters into the bed ports (vendor instruction). **P-CAL-01 on first
   fit:** measure adapter top height, thread depth and centre; set `mount.adapter_*` and re-run.
3. Thread the four M10 studs (Loctite 243) into the adapters; hand-tight + 10 Nm.
4. Shims: nominal 2 × 0.5 on each stud (from P-CAL-01: total = 22 − 9.00 − adapter height).
5. Spacers onto the studs (they sit in the foot pockets once the shell is down).
6. Two people lower the topper (pad already bonded to the foot) over the studs; the rail
   obrounds are the lead-in.
7. Slot washer, Nord-Lock pair, nut on each stud. Torque all four to 30 Nm in a cross pattern,
   two passes. The pad is now at its 4 mm stop everywhere.
8. Check: the four OEM rail-cap buttons press freely through the control wells
   (`oem_buttons_not_covered`); modules latch in all four sockets.

## 4. Service

* **Remove topper:** open the hatch, reach in, four nuts with a 16 mm ratcheting box wrench,
  lift off. Studs, shims and spacers stay; re-fit is steps 6–7.
* **Re-torque:** at 500 km after first fit, then every 6 months: 30 Nm; Nord-Lock pairs
  are reusable unless the cam faces are damaged.
* **Corrosion:** A4 into anodised 6061 is isolated by Tef-Gel on every thread and anodise on every
  face except the bond faces (masked, bonded, sealed by the bondline).

## 5. Measurements this design depends on — researched vs physically verified

None of these has been measured on a truck. Every one is a **calibration need**, in the order it
should be done:

| ID | Dimension | Value used | Source (researched) | Physically verified? |
|---|---|---|---|---|
| P-CAL-01 | Weistec adapter above-cap envelope, thread depth, centre | 60 × 36 × 12, ≥ 18 deep (PROVISIONAL) | none published (vendor page states M10 only) | **No** — measure the received part latched on the truck |
| P-CAL-02 | Bed accessory port centres | (307, ±724), (1154, ±710) mm from the bed's inside front wall | Upfit p.59 plan view, port symbols, `rivian_reference.py` (scale by 5,514 mm length; bed width/length cross-checks 0.6 / 1.2 %) | **No** — tape all four before the rail slots are cut |
| P-CAL-03 | Rail-cap flatness/profile under the 100 mm pad band | flat, ±1.0 assumed | Upfit p.59 line clusters (0.644 / 0.783 / 0.828 m) | **No** — straightedge + feelers along both caps |
| P-CAL-04 | Bed front corner tie-down positions (optional crash tethers) | — | Owner's Guide p.297 (location only) | **No** |
| T1–T3 | OEM rail-cap button positions (control wells) | x 60 / 1300 | TAILGATE_CONTROL.md | **No** |
| — | Port rating | 2,500 N per port | Upfit p.59 | Rivian's published value; not tested |
| — | Torque window M10 8.8 hard joint | 27–54 Nm | Upfit p.57 | standard table |

## 6. Open, named

`port_adapter_envelope_P-CAL-01`, `bed_port_positions_P-CAL-02`, `port_crash_pulse_vs_rating`
(OPEN in the suite); plus the Step 27 items carried from `df01d411` (rear-sill seal, tape session,
latch sustained rating, GN 7233 coupler curve, T-handle grip, control wells, release cable
SERIES_ONLY). FEA of the rail/foot bond, adapter strength beyond Rivian's rating, fatigue, water
ingress at the pad, real-truck fit, fabrication release and Nate-only approval are later gates.
