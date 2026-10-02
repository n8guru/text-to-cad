# Step 27 — styling, authoritative shell CAD, real-R1T evidence (continuation 2)

**Runtime model: `claude-opus-5-5`** (the model ID the harness reports for this session; nothing
inside the session can verify it further).

**Status: Step 27 is NOT complete.** This pass closes the styling-geometry, shell-CAD, evidence,
portability and most BOM gaps the previous result left open. It does not close real-truck fit,
vendor CAD, the hatch's exterior opening, the rear-sill seal or any later gate (§9). Nothing was
pushed, purchased or quoted; Studio was not written to; no operator card was answered; no Nate
approval is claimed.

This file carries no commit hash: a commit cannot contain its own hash, which is why the previous
`out/COMMIT.txt` was always stale (it is deleted). Outputs are tied to their sources by SHA-256 in
`out/PROVENANCE.json`; `cad/provenance.py --check` fails as soon as any input or output changes.

---

## Rev 10 addendum (mesh task 136191, 2026-10-02): attaching hardware + costed BOM

**Runtime model: `claude-opus-5-5`.** Scope per operator 2026-09-30 (Studio 75785): design the
attaching/mounting hardware and a detailed BOM with part numbers, quantity, material, supplier and
cost, on top of `df01d411`. **Still not a Step 27 completion claim for the items in §9 and no
Step 21 input**: nothing purchased, quoted, fabricated or approved.

| Delivered | Where |
|---|---|
| Topper-to-truck attachment at the 4 Rivian bed accessory ports (2,500 N each, Upfit p.59) through a purchased non-modifying adapter (Weistec 09-111-00078-7, $100): metal-to-metal stud/nut clamp stack, machined compression stop setting the EPDM foot pad at 33 %, slot float ±6 / ±2.75 mm + 0–2 mm shims, wrench pocket for service with the topper built | `MOUNTING27.md`, `cad/mounts.py`, `SEC-27-008`, `SEC-27-008D`, `DWG-27-010/012/013` |
| Bed-port positions re-measured from the SHA-pinned Upfit p.59 plan view (rear ports were 21 mm off the carried value) | `style/rivian_reference.py` → `r1t_plan.bed_accessory_ports_x_halfy`; check `bed_ports_match_reference` |
| Load cases LC1–LC6 on the ports, slip, stud preload, pad seating, Rivian 113 kg 4-port benchmark (roof load on topper hardpoints limited to ~24 kg dynamic) | `out/mounting_analysis.json`, `check_mounting` |
| Joint schedule: all 17 joints, 204 fasteners of 14 specs + 26 potted inserts, torques from Upfit p.57 | `cad/fasteners.py`, BOM27 §3 |
| BOM with quantities from the geometry, exact PNs, supplier URLs and **dated (2026-10-02) unit/extended prices** verified against a pinned research file; fabricated parts with material, process, finish, drawing, critical tolerances and a stated ROM cost model | `BOM27.md`, `out/BOM27.csv`, `bom_prices.json`, `research/pricing_2026-10.json` |
| Controlled drawings for every remaining fabricated family | `DWG-27-014` … `DWG-27-020` |
| Playbook phase | `PLAYBOOK-PHASE-27r10.md` (also appended to `forge-agent-os/tools/r1t-opus-pass/PLAYBOOK-NOTES.md`) |

Roll-up (floor, not a price): purchased hardware $2,275.53 priced (5 lines unpriced), fasteners +
consumables $489.13 (1 unpriced), fabricated-part ROM ~$19.1k (class 5, tooling excluded).

Checks: **87 PASS, 0 FAIL, 10 OPEN** (`out/checks.json`). New OPEN: `port_adapter_envelope_P-CAL-01`,
`bed_port_positions_P-CAL-02`, `port_crash_pulse_vs_rating` (10 g pulse = 2,528 N/port vs 2,500).
Unpriced lines: MISUMI pins ×2 and bushing (office-hours API), McMaster plunger (login), Aptiv
13897598 housing (distributors block scripted reads), VHB 5952. EQUIV price proxies (release cable,
DD6139 seal, foot pad, some fasteners) are labelled with the reason; order the specified PN.
Not done in rev 10: new renders/animation of the port station (the CAD-driven evidence lane from
`df01d411` is unchanged), FEA, hatch exterior release (G8), rear-sill seal (G9).

Regenerate: the §1 command list, unchanged in order (`make_bom.py` now also writes `out/BOM27.csv`;
`checks_step27.py` writes `out/mounting_analysis.json`).

---

## 0. The six asks and what happened

| # | Ask | Result |
|---|---|---|
| 1 | Styling pass against sourced R1T/R1S references | **Done, as a drawing-derived pass.** Truck and style targets measured from Rivian's own orthographic line art (three PDFs, SHA-256 pinned, cross-checked against published dimensions). The previous truck model was wrong by 181 mm in rail height and 330 mm at the cab back; the old shell overlapped the real cab and stood ~180 mm above its roof. The shell is rebuilt to cab height. Two deviations from the R1S are stated, not hidden. See `style/STYLE27.md`. |
| 2 | Carbon shell as authoritative build123d CAD in the STEP; solid hatch-sweep / interference checks against it | **Done.** `cad/shell.py`, one valid solid, in both STEPs. The new solid hatch sweep **found a real defect** (the bottom latches' strikers swung through the aperture's bottom land) and the hatch latch stations were redesigned (§3.3). |
| 3 | Real-R1T-context evidence and CAD-driven animation via blender-loop | **Done within stated limits.** Every topper mesh is a CAD STL; the truck is a Blender loft of the same Rivian-measured sections, not a scan or photo plate. 21 final-run images read (stills and clip frames), a 384-frame animation scored at six key poses against the CAD, two MP4 clips (§4). |
| 4 | Resolve SERIES_ONLY rows and vendor-CAD gaps as far as public evidence allows | **4 of 5 SERIES_ONLY rows closed** with exact, vendor-validated part numbers; the release cable stays SERIES_ONLY (needs Southco). Vendor CAD for the R4-30 and GN 7233 was **not** obtained. No dash number was invented (§5). |
| 5 | Portability / provenance | **Done.** Every old Blender script with a hard-coded path is deleted; the new ones resolve from `__file__` and environment variables; a check enforces it. `out/COMMIT.txt` removed; `out/PROVENANCE.json` + `--check` added (§6). |
| 6 | Rerun all checks; add shell/style checks | **79 checks: 72 PASS, 0 FAIL, 7 OPEN** (§7), including 20 new source/style/shell/truck checks. |

---

## 1. Regeneration, in order

From `models/r1t_topper/` with the repository CAD venv (this run: Python 3.12.3, build123d 0.11.1,
pdftoppm 24.02; Blender 5.2.2 LTS for the evidence lane):

```bash
PY=../../.venv/bin/python
$PY step27/style/rivian_reference.py   # RIVIAN_REFERENCE_OK; fetches + SHA-checks the Rivian PDFs
                                       # into ~/.cache/r1t_topper_refs (never into the repo)
$PY step27/cad/assembly_step27.py      # STEP27_EXPORT_OK: 3 STEP files, 180 part STLs (plus open-
                                       # state, payload and truck-reference sets), 7 sections,
                                       # parts_manifest.json, kinematics.json
$PY step27/cad/make_drawings.py        # 9 drawing sheets
$PY step27/cad/make_bom.py             # BOM27.md
$PY step27/cad/checks_step27.py        # STEP27_CHECKS_PASS: 72 PASS, 0 FAIL, 7 OPEN -> out/checks.json
$PY step27/cad/provenance.py           # out/PROVENANCE.json (run last)
$PY step27/cad/provenance.py --check   # PROVENANCE_OK
```

Evidence lane (`blender-loop`, path B), from `models/r1t_topper/blender/`. `R1T_HDRI` is optional
(any equirect `.hdr`; a Nishita sky is used without it); `R1T_CYCLES_DEVICE=CPU` was needed for
S13 because the GPU was occupied by another user's process:

```bash
blender-loop init r1t-step27-final --intent "..."
blender-loop step r1t-step27-final --label S11_truck  --script $PWD/s11_truck.py --fresh --assert '...'
blender-loop step r1t-step27-final --label S12_topper --script $PWD/s12_topper.py --assert '...'
blender-loop step r1t-step27-final --label S13_hero   --script $PWD/s13_hero.py   --assert '...'
blender-loop step r1t-step27-final --label S14_anim   --script $PWD/s14_anim.py   --assert '...'
blender-loop step r1t-step27-final --label S15_clip   --script $PWD/s15_clip.py   --assert '...'
```

The exact assert strings and every score are in `~/evidence/blender-loop/r1t-step27-final/ledger.json`
and summarised in §4.

---

## 2. Styling (ask 1)

Full write-up: `style/STYLE27.md`; numbers: `style/rivian_reference.json`, produced by
`style/rivian_reference.py` from the pages listed in §8.

* **Measured, not assumed.** Each Rivian view is scaled by a published dimension and
  cross-checked against a second one: the wheelbase-scaled side view reproduces the published
  1,834 mm roof height to 0.04 %; the rear view reproduces the 2,014 mm body width to 0.05 %.
  `truck_params_match_reference` now fails if the hand-carried truck numbers in
  `blender/params.json` drift more than 1 mm from the measurement.
* **What the measurement changed.** Rail top 1,366 mm above ground (was 1,185); cab roof 463–469
  mm above the rail (topper roof was 649); cab back at x = −150/−180 mm (was −480) with a roof
  spoiler tip at x = −132. The old shell therefore overlapped the real cab by ~300 mm and stood
  ~180 mm proud of its roof — the structural reason earlier renders "did not blend".
* **The styled shell.** One section: a flat 21° land (R1T C-pillar 21.8°, R1S D-pillar 20.1°),
  an R100 shoulder tangent to a 13 mm crown, roof top at 462 mm (cab roof 463), a 15° raked rear
  face (R1S liftgate 15.2°), a vertical front face tucked 22–33 mm behind the cab and spoiler.
* **Stated deviations.** Rear roll-off 0.16 of the greenhouse vs the R1S 0.21 (the flat raked
  face must carry the hatch frame); dark side band 0.64 of the greenhouse vs the R1S DLO 0.83 (the
  82 mm socket border, not the surface); vertical front face (parallel to the cab back would put
  the roof's leading edge inside the spoiler).
* **Interfaces kept, re-dimensioned to the real envelope:** sockets 470 × 208 aperture (was
  640 × 353), hatch 1,000 × 226 (was 1,280 × 412), strut re-selected (6462II, 50 N).

## 3. Authoritative shell CAD and the checks against it (ask 2)

### 3.1 The shell

`cad/shell.py` builds the carbon shell from the styled section in build123d: section solve
(shoulder circle tangent to land and crown), prism with front R50 and rear R100 loop fillets,
22 mm offset hollow, foot on the rail caps (stopping 5 mm short of the rail's rounded rear end),
socket and hatch through-cuts from the shared border offsets in `geom.py`, drain exits, front
pass-through window, flush roof hardpoints, foot cut-outs for the bed-port adapters and the OEM
control wells. One valid solid; 19.1 kg estimated at 5.8 kg/m² (areal estimate, not a weighed
part). It is `SHELL_CARBON_SANDWICH` in `out/R1T_TOPPER_STEP27.step` and `_open.step`; the truck
keep-outs are exported separately as `out/R1T_REFERENCE_KEEPOUTS.step`. New drawings:
`DWG-27-000_carbon_shell`, `SEC-27-006_shell_styled_section`, `SEC-27-007_cab_to_topper_profile`.

### 3.2 Checks against the shell (all solid booleans / distances, not bounding boxes)

`shell_one_valid_solid`, `shell_wall_22mm`, `bond_flanges_seat_on_flat_skin` (every socket frame
and the hatch surround bond 0.5 mm off the inner skin at every sampled station),
`no_interference_closed_assembly` (every part pair, allow-list of designed contacts only),
`hatch_sweep_clear_of_shell_and_frame` (leaf, glazing, strikers, studs and struts swept 0–95° in
5° steps against the shell and every fixed part), `topper_clear_of_r1t_keepouts` (cab, body below
the rail, tailgate), `cab_gap_ge_20mm` (33.4 mm to the traced cab-back/spoiler keep-out solid;
S12 measures 22.4 mm to the fuller Blender loft of the same trace), `module_removal_path_clear`,
`safety_catch_engages`, `fabricated_parts_are_single_solids` and the style checks in §2.

### 3.3 Defects the new checks found, and the fixes (this pass)

1. **Hatch latches could not open.** The latches hung below the return lip, so the leaf's
   strikers sat ~94 mm inboard of the skin, 251 mm from the top hinge axis. On that arc the bar
   left 22° off the slot and the striker head/bracket swept down through the aperture's bottom
   land (solid clash from 5°). Fixed by geometry, not by allow-listing: each latch now sits up in
   the aperture tube behind the leaf's bottom strip with the closed bar 50 mm below the skin, is
   tilted 10.7° about the bar axis so the slot lies on the chord of the bar's exit arc (arc
   deviation ≈ 0.2 mm inside the 0.4 mm slot clearance), and is carried by a tilted shelf plate
   and a gusset down to the return lip. Stations are now symmetric at x = ±425 with the bracket
   and arm outboard on solid leaf (the bar crosses both slotted side plates, so one PN serves
   both hands). The leaf lost 0.07 kg; the strut solver re-run at 3.28 kg picks the same strut
   and studs.
2. **Cage end bars inside the plug tube's R34 corners** (566 mm³ each): bars now span ±185 mm.
3. **Bed-port adapter flanges cut into the socket frames' lower bond flange** (240 mm³ each):
   flange Ø56 → Ø46, which stays on the 75 mm base rail.
4. Earlier in the pass: the old shell overlapped the cab; the rail/rear-wrap and socket
   frame/foot clashes; the drains exiting below the rail; the TOOLBOX tub fouling the plunger
   bosses; a clash tool that did not compose nested locations; a hatch-sweep filter that could
   not tell the leaf's own sub-parts from fixed parts.

## 4. Evidence (ask 3) — blender-loop run `r1t-step27-final`

Run dir `~/evidence/blender-loop/r1t-step27-final/` (`ledger.json`, `step_*.json`, `stills/`,
`scene.blend`, `clips/`). Outside the repo by design.

| Step | One move | Scores (assert) | Stills read |
|---|---|---|---|
| S11_truck | loft the Rivian-measured R1T | roof 1.835 m (1.82–1.85), rail 1.366 (1.36–1.37), wheelbase 3.450 (3.44–3.46), bed depth 0.465 (0.45–0.48), width 2.014 (2.00–2.03) | `ctx_side`, `ctx_rear3q` |
| S12_topper | import the 180 CAD STLs | roof step −8.6 mm (−15..+10), cab gap 22.4 mm (≥ 20), base seating 0.0–4.0 mm over 31 samples (−3..+5) | `ctx_side_L`, `ctx_rear3q`, `ctx_junction`, `ctx_front3q` |
| S13_hero | switch to Cycles (96 spp, 1600 × 1000, CPU) | mean luminance 0.509–0.654 over 4 views (0.25–0.85: no black or blown frame), roof step −8.6 mm | `hero_rear3q`, `hero_side`, `hero_front3q`, `hero_junction` |
| S14_anim | rig the CAD from `kinematics.json`; 384 frames | L1 release: rotor −26.5° (CAD −26.5), slide 29.0 mm, lift 5.0 mm, withdraw, CAGE → TOOLBOX swap (13 CAGE parts shown before, 2 TOOLBOX parts after, 0 CAGE after), hang 29.0 mm on the fin, home; triangle overlap 0 at released / lifted / hung / locked (designed home-pose contacts excluded and proved by the CAD contact checks instead); hatch 95.0°; strut 204.07 → 308.98 mm vs CAD 204.1 → 309.0 — 22 asserts | `hung_anim_socket`, `released_anim_latch_inside`, `hatch_open_anim_rear3q`, `away_anim_rear3q` |
| S15_clip | render the timeline (EEVEE, 1280 × 720, 24 fps) → `clips/r1t_topper_mechanism_rear3q.mp4` (frames 1–384), `clips/r1t_topper_socket_inside.mp4` (1–250) | frames counted on disk 384 / 250 (asserted ≥ 384 / ≥ 250); ffprobe decodes 384 / 250 H.264 frames; 0.46 MB each | clip frames `f_0130` (payload away), `f_0206` (TOOLBOX hung), `f_0310` (hatch open), inside `f_0064` (lifted); runtime defaults `S15_clip_side`, `_overhead`, `_front` |

What the stills show, and what they do not: the topper roof continues the cab roofline, the
front face sits behind the cab-back spoiler with a visible gap, the L0 WINDOW / L1 CAGE / R0
WINDOW / R1 TOOLBOX kit is in its sockets, and the hatch carries two panes and the CHMSL. The
truck is a lofted proxy with flat panels — right in proportion, not photoreal and not Nate's
truck.

**The stills caught one defect the scores missed:** the first S14 run (earlier run dir
`r1t-step27-style`, stills `S14_anim_hung_anim_socket` / `lifted_anim_*`) showed an empty L1 socket
after the payload swap. The TOOLBOX STLs had never been imported (a glob that did not match the
exporter's names); every overlap score still passed. Fixed, and S14 now scores how many CAGE and
TOOLBOX parts are visible at each pose.

## 5. BOM (ask 4)

`BOM27.md`, generated from `hardware.json` + `out/parts_manifest.json`. Status rollup:
**13 ORDERABLE, 1 SERIES_ONLY, 2 CUSTOM, 1 NO_PART_REQUIRED.**

Closed this pass, each against the vendor's own data:

| Item | Part number | Evidence |
|---|---|---|
| Locating pin, round | MISUMI **CFPBPA6-P10-L10-B8** | MISUMI part-number service returned `completeFlag=1` for the exact string on 2026-09-27 (out-of-range strings rejected); series 110300557320 drawing; 2019 catalogue pp.1544–1545 |
| Locating pin, diamond | MISUMI **CFPBPD6-P10-L10-B8** | same |
| Bushing | MISUMI **JBHC10-15** | same service, series 110302666420; 10 G6 bore (MISUMI offers no 10 H7) |
| Gas strut | Stabilus **6462II** + 4 ball studs **4486MD** (or the column-2 **5025DT**, supplied with the M8 studs) | Standard Program EN p.17 table (SHA-256 recorded) and p.37; the two Ref.-No. columns resolved from the page's own callouts; selected by `hatch.solve_struts` |

Still open, with the reason: **release cable** SERIES_ONLY — fitting letters, TA, type-9
availability at 450/650 mm and conduit OD are only in Southco's configurator (placeholder PN is
marked as such). The BOM also lists unresolved notes on otherwise ORDERABLE rows: the E3-18-15
keyed T-handle's grip (11.4–27.2 mm) cannot reach through the 52.25 mm hatch stack; GN 7233 PDF
vs HTML dimension conflict; Aptiv 13897598 pinout unpublished by Rivian; Maxxima U3 marking to
confirm; no DD6139 force curve; limiter stock PNs behind McMaster's login.

Also fixed in the generated BOM this pass: 40 purchased parts (latch housings, rotors, pawls,
handles, hinge leaves) had been classed `CUSTOM` in the manifest and listed as fabricated; the
cable splitter carried the handle's PN; the fabricated table listed each socket's copy separately.
The latch note no longer carries the previous pass's 383 N (it was for the old 640 × 353 socket);
`latch_sustained_rating` computes 207 N per latch from the current geometry.

## 6. Portability and provenance (ask 5)

* Deleted: `blender/s1_truck.py` … `s8_mechanism.py`, `render_clip.py`, `render_clips.sh`,
  `render_configs.py` (all carried `/home/...` paths or described the superseded geometry).
* `blender/r1t_lib.py` and `s11`–`s15` resolve every path from `__file__`; the run directory
  comes from `BLENDER_LOOP_RUN_DIR`. `no_hardcoded_home_paths` scans `blender/*.py`,
  `step27/cad/*.py` and `step27/style/*.py`.
* `out/COMMIT.txt` deleted (`no_self_hash_claim` checks it stays deleted). `cad/provenance.py`
  writes SHA-256 of every input (params, hardware, reference JSON + script, every `cad/*.py`)
  and output (STEP, manifest, kinematics, checks, drawings, BOM) plus the command order.
* Part STLs (`out/parts*`, `out/reference`) are regenerable render inputs and git-ignored.

## 7. Checks (ask 6) — `cad/checks_step27.py`: 72 PASS, 0 FAIL, 7 OPEN

New this pass include: `style_sources_fingerprinted`, `side_view_scale_validated`,
`rail_height_two_views_agree`, `spoiler_two_views_agree`, `truck_params_match_reference`,
`roof_meets_cab_roof`, `roof_level_like_r1s`, `tumblehome_matches_r1t_r1s`,
`rear_rake_matches_r1s_liftgate`, `base_lands_on_rail_cap`, `rear_corner_roll_off_r1s_like`,
`side_dlo_band_vs_r1s`, `carbon_bridge_between_openings_ge_76`, `no_top_centre_protrusion`,
`shell_one_valid_solid`, `shell_wall_22mm`, `bond_flanges_seat_on_flat_skin`,
`topper_clear_of_r1t_keepouts`, `cab_gap_ge_20mm`, `hatch_sweep_clear_of_shell_and_frame`
(plus `no_hardcoded_home_paths`, `no_self_hash_claim`).

OPEN (true unknowns, printed by the suite, not failures):

| Check | Why it is open |
|---|---|
| `rear_sill_tailgate_seal` | Rivian's side view puts the tailgate top 32 mm below the flat rail; the rear sill needs a closing seal across the tailgate. Select after the tape session. |
| `truck_tape_session` | Every truck number is drawing-derived (rail height band 1,344–1,366 mm). |
| `latch_sustained_rating` | 207 N/latch is under Southco's 222 N "max dynamic working load", but Southco defines neither "dynamic" nor a sustained rating. |
| `hinge_coupler_curve` | GN 7233 is a linkage; every hatch clearance assumes pure rotation about the design pivot. |
| `keyed_t_handle_grip` | E3-18-15 grip cannot reach a keeper through the 52.25 mm stack. |
| `control_well_positions` | OEM button positions provisional until taped (T1–T3); well lids not modelled. |
| `bom_series_only_release_cable` | Needs Southco (§5). |

Not checked by the suite (printed as such): FEA, water/dust sealing, real-truck fit, vendor
endurance/salt/UV, rotor internals (a representation), the GN 7233 coupler curve, fabrication,
purchasing, Nate-only approval.

**Coverage change against the previous suite (59 checks at `57634ea0`).** 36 of its names are
not in this suite; each is accounted for:

* **25 renamed or superseded by a stronger check**, e.g. the per-part "no clash when shut"
  checks → the all-pairs `no_interference_closed_assembly`; `hatch_mass_estimate` → the computed
  leaf mass inside `struts_hold_open_with_margin`; `latch_static_margin` → `latch_ultimate_sanity`
  + the OPEN `latch_sustained_rating`.
* **1 moved into an OPEN item:** `hinge_install_space_available` (a y-distance proxy) is now
  stated inside the OPEN `hinge_coupler_curve` (the 105 × 135 mm GN 7233 installation space is
  not placed).
* **2 restored** after this audit: `hinge_swing_exceeds_hatch_open`,
  `latch_fasteners_reachable_from_inside` (now computed from the latch planes).
* **5 removed with the feature they checked — a regression in modelled scope, not a pass:** the
  rebuilt hatch has **no gutter** above the aperture (`gutter_above_seal_line`, and
  `leaf_swing_clears_gutter`, which was hard-coded to pass) and **no interior closeout panels**
  (`closeouts_clear_the_strut_path`); the OEM control wells are plain cut-outs with **no modelled
  lid or drain** (`control_well_finger_depth`, `control_well_drains`). See G12.
* **3 dropped as weak proxies:** `handle_travel_recorded` (record-only),
  `bar_longer_than_fork_thickness` (the bar crossing the housing is covered by the interference
  matrix), `leaf_open_clears_tailgate_drop` (a bounding-box x comparison).

## 8. Sources

Rivian (fetched, SHA-256 verified, rasters never committed):
* R1T Owner's Guide (`r1t-og-en-us-20240527.pdf`, `e6c54434…75b6`): p.14 rear view, p.16 bed,
  p.17 driver side. `https://assets.rivian.com/2md5qhoeajym/530xs9hu11xOKefT2JrvA5/46f6cb5d5756b8320d3eb494a902e66c/r1t-og-en-us-20240527.pdf`
* R1S Owner's Guide (`r1s-og-en-us-20240722.pdf`, `27eda35d…7061`): p.14 rear, p.16 driver side.
  `https://assets.rivian.com/2md5qhoeajym/7Ao7NIFkLxOZtvdc7Fqh70/c8c4a585ae141effce63b41ead2b8ce0/r1s-og-en-us-20240722.pdf`
* R1T Upfitting Guide 2025-09-24 (`847d036f…552a`): pp.28–30 dimensions, p.59 plan view, p.65
  CHMSL responsibility, pp.100–102 J019 upfitter port.
  `https://assets.ctfassets.net/2md5qhoeajym/5ysf6K5UtGtHedY1fMeClC/b83307f7e8f03838a1906bff88707f95/r1t-upfitting-guide-en-us-20250924.pdf`
* rivian.com support (wheelbase 135.8 in R1T / 121.1 in R1S); stories.rivian.com (R1S 200.8 in).

Vendors (URLs and page references per item in `hardware.json`): Southco R4 catalogue
(`marek.eu` mirror, pp.260, 300–302), AC-CA cable literature pp.321–323, AC catalogue
pp.317–321, E3 catalogue pp.90–121, Southco glossary (archive.org); MISUMI part-number service
(`api.us.misumi-ec.com`, series 110300557320 and 110302666420); Stabilus Standard Program EN
pp.17, 37; JW Winco GN 7233 datasheet; Trim-Lok catalogue p.23; Maxxima M63319R (distributor
pages); Aptiv 13897598 via the Upfitting Guide.

## 9. Remaining gaps — why Step 27 is not complete

| # | Gap | What closes it |
|---|---|---|
| G1 | Styling is drawing-derived and not approved: rear roll-off and DLO proportion deviate from the R1S (stated), no R1S-style liftgate leaf or flush-glazed module was built, the front transition is a vertical face behind the spoiler. | Nate's styling review; the liftgate-leaf / flush-glass levers in `STYLE27.md`. |
| G2 | "Real R1T context" is a Blender loft of Rivian's line art, not a scan, photo plate or OEM CAD, and not Nate's truck. | Gaussian-splat capture (Studio 75072) or a tape session. |
| G3 | Shell is geometry only: no ply book, core/insert detail or FEA; mass is an areal estimate. | Laminate definition + FEA gate. |
| G4 | Release cable SERIES_ONLY; T-handle grip mismatch; the other open notes in §5. | Southco configurator / rep; re-select the keyed lock. |
| G5 | GN 7233 coupler curve unknown (pure rotation assumed). | JW Winco CAD, then re-run the hatch sweep. |
| G6 | R4-30 internals are a representation; the new tilted stations rely on it. | Southco 2D/3D CAD, then re-run the latch and sweep checks. |
| G7 | Truck tape measurements T1–T8, control-well positions, bed-port interface. | Tape session on the truck. |
| G8 | Hatch opening from outside is not resolved: the rotary latches release only from inside, the keyed T-handle is a separate lock with a grip mismatch, and the hatch's release handle and cables are counted in the BOM but not modelled. | Hatch access concept decision, then CAD. |
| G9 | Rear sill-to-tailgate seal not designed (`rear_sill_tailgate_seal`). | After T5. |
| G10 | Southco sustained-load reading (`latch_sustained_rating`). | Southco answer. |
| G11 | Mass not optimised: 88.7 kg estimated for everything Step 27 owns. | Pocketing / layup pass. |
| G12 | Previous-pass features not carried into the rebuilt geometry: hatch gutter, interior closeout panels, control-well lid and drain (§7). | Re-model on the styled shell, restore their checks. |

Later gates, unchanged and unclaimed: FEA, prototype fit, real-truck calibration, fabrication
release, purchasing, Nate-only design approval.

## 10. Files

```
models/r1t_topper/step27/
  RESULT27.md  BOM27.md  TAILGATE_CONTROL.md  hardware.json  research/
  style/   rivian_reference.py  rivian_reference.json  STYLE27.md
  cad/     geom.py shell.py side_socket.py hatch.py hw.py mounts.py truck.py
           assembly_step27.py checks_step27.py make_drawings.py make_bom.py provenance.py
  out/     R1T_TOPPER_STEP27.step  R1T_TOPPER_STEP27_open.step  R1T_REFERENCE_KEEPOUTS.step
           parts_manifest.json  kinematics.json  checks.json  PROVENANCE.json
  drawings/ DWG-27-000,001,003,004,006,007,008,010,011  SEC-27-001..007
models/r1t_topper/blender/
  params.json  r1t_lib.py  s11_truck.py  s12_topper.py  s13_hero.py  s14_anim.py  s15_clip.py
```

Branch `agents/claude/r1t-opus-pass`, parent `57634ea0`. Rev 10: branch `agents/claude/task-136191-r1t-hardware-bom`, parent `df01d411`.
