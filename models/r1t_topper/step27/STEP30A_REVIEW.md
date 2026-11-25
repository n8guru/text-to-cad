# Step 30a — hatch surround / DD6139 seal clash repair + OPEN #5-#8 disposition

Producer record (task 164576, attempt 1, 2026-11-25). **Not** an independent review,
not a fitment, structural, sealing or approval claim; every PROVISIONAL label stays.
Base: `n8guru/text-to-cad` `agents/codex/task-147368-r1t-hatch-mount` @
`2cabd89ef0cdf4b5cef645356074e60f2bddf9fd` (95 PASS / 1 FAIL / 12 OPEN).
Branch: `agents/forge/r1t-topper` (the containing commit is the review pin).
**DEPLOY-N/A:** standalone CAD, not Forage serving code.

## 1. The 491 mm³ clash — root cause and geometric repair

Measured on the base pin (hatch-local, `hatch_surround() & seal_bead(True)`): 490.97 mm³
in six solids, all in z −46.25 … −36.25, i.e. **exactly the push-on rib height above the
land** (FACE_Z … FACE_Z + rib_h):

| where | volume each |
|---|---|
| both top shoulder fillets + tapered side tops (x ≈ ±488 … ±556, y ≈ 60 … 158) | 114.4 / 114.6 mm³ ×4 |
| both lower bead ends at the sharp bottom corners (x ≈ ±636 … ±638, y ≈ −163 … −160) | 16.4 mm³ ×2 |

Cause: the rib was built with `border_ring_trapezoid(H_SEAL_OFF ± rib_t/2)`, which offsets
the trapezoid by shifting its **vertices** (half-height, both half-widths, radius + e).
On the 23° tapered sides and the shoulder fillets that is not a true offset of the
seal path, so the 3.0 mm rib wandered out of the bead's 3.2 mm grip channel. The rib
was also a closed ring (minus the doorway cutter), so at the sharp lower corners its
bottom-run stub crossed the open-bottom U bead's end faces.

Repair (`cad/hatch.py`, `seal_rib()`): the rib is now swept with the **same open-bottom
U path (`seal_land_path()`) and the same Frenet frame** as the DD6139 bead, section
rib_t × rib_h (+0.5 mm into the land so it fuses). It is centred in the channel
everywhere (0.1 mm/side) and ends where the bead ends. Unchanged: the 1299.0 mm actual
lower chord, the open-bottom U seal path, the seal section/compression and the
interference check itself (no allow-list entry, no tolerance change). Result on the
fixed part: `hatch_surround() & seal_bead(True)` volume **0**; surround is 1 valid solid.

## 2. Agent-closable OPEN checks #5-#8

Each was worked; none could be honestly *closed* without inventing data, so each is
**justified** in its `checks.json` detail with a CLOSES-WHEN condition and owner.

| # | check | disposition |
|---|---|---|
| 5 | `rear_leaf_bottom_seal_on_tailgate` | Justified OPEN. Gap (leaf edge 7.7 mm above the rail-cap plane to the tailgate top 32 mm below) and the tailgate-cap/rail-end section are drawing-derived (TAILGATE_CONTROL.md **T5**, medium confidence); a seal picked on that guess could sit 5-10 mm outside its compression band. Closes after the T5 tape, then a leaf-bottom seal is selected and swept against the closed and opening tailgate (next CAD step). |
| 6 | `keyed_t_handle_grip` | Justified OPEN with a **new measured finding**: the fixed surround has **0 mm³** of material behind the T-handle station (x = 0, inside the open-bottom doorway; the same probe at a corner stub finds 26 895 mm³). So no keeper exists for any cam to engage, and "re-select a longer-grip E3" would not fix it. Leaf-only grip (26 mm) is inside the E3 11.4-27.2 mm range. This is a design-route decision, not a part swap: (a) move the keyed lock to a corner stub with a standoff keeper on the land, or (b) let the exterior key drive the existing rotary-latch release cable. Closes when the operator picks a route and the next CAD step models it and re-runs sweep + interference. |
| 7 | `hinge_coupler_curve` | Justified OPEN (vendor data). JW Winco publishes the GN 7233 coupler path only in its registered CAD download; inventing link lengths would be fabricated kinematics. Closes when GN 7233 size-50 CAD is placed in research/ and the hatch sweep re-runs on the true curve. |
| 8 | `plf_drive_link_and_lock_interlock` | Justified OPEN (blocked by P-CAL-01b). Link geometry and hook/detent forces follow from the port pin position and bridge stiffness, which are PROVISIONAL; drawing the link now would fix lengths to unmeasured numbers. Closes after P-CAL-01b measures the reference foot/port; then draw cam→slider link + lock keeper, sweep, compute preload/detent force. |

## 3. Every remaining OPEN check (who / what closes it)

| check | closes it |
|---|---|
| `truck_tape_session` | Physical tape session on Nate's Gen-1 R1T (rail height, cab back, spoiler tip, rail-cap edges, tailgate face); Step 13 calibration. |
| `control_well_positions` | Tape T1-T3 of the rail-cap OEM controls, then model well lids. |
| `bed_port_positions_P-CAL-02` | Tape all four bed-port centres before foot pockets are cut. |
| `plf_port_internals_P-CAL-01b` | Operator-approved purchase of one Rivian Cargo Crossbars set as reference article; photograph/measure foot + a real port, set mount.* params, re-run. |
| `latch_sustained_rating` | Southco engineering: sustained/dynamic rating definition for the R4 rotary latch. |
| `bom_series_only_release_cable` | Southco quote: fitting letters, TA, type-9 availability, conduit OD for AC-75-101-11 / AC-05-301-11 / R4-30. |
| `port_crash_pulse_vs_rating` | Analysis/test: crash-pulse case vs Rivian's port rating (information only). |
| `plf_hook_and_screws_within_allowable_at_port_rating` | Analysis (FEA) of the C-jaw web/upper lip and bridge after P-CAL-01b; establish an allowable clamp load. |
| `rear_leaf_bottom_seal_on_tailgate` (#5) | See §2. |
| `keyed_t_handle_grip` (#6) | See §2 — operator route choice, then CAD. |
| `hinge_coupler_curve` (#7) | See §2 — JW Winco CAD. |
| `plf_drive_link_and_lock_interlock` (#8) | See §2 — after P-CAL-01b. |

## 4. Regression and outputs

Regenerated in PROVENANCE `commands_in_order` (rivian_reference.py inputs unchanged, not
re-run), build123d 0.11.1, this worktree:

- `checks_step27.py` full regression: **96 PASS, 0 FAIL, 12 OPEN** (`out/checks.json`).
  `no_interference_closed_assembly` **PASS** — 220 parts, 24 090 pairs, the same 9-entry
  designed-contact allow-list and 0.5 mm³ threshold as the base pin (neither touched).
  `seal_rib_measured_in_grip_range` still measures 3.00 mm; `hatch_sweep_clear_of_shell_and_frame`,
  `fabricated_parts_are_single_solids` PASS. The +1 PASS vs base is the repaired clash.
- `checks_step30_hatch_width.py`: STEP30_HATCH_WIDTH_PASS (1299.0 mm actual lower chord kept).
- `checks_step30_mount.py`: STEP30_MOUNT_PASS, 68 solid checks.
- STEP (closed/open/keep-outs/mount details), part STLs, sections, 18 drawing sheets, BOM
  regenerated; `provenance.py --check`: PROVENANCE_OK 22 inputs, 759 outputs (same output set
  as the base pin).

Tooling fix needed to regenerate at all on the 11 GB worker cap: build123d 0.11
`Shape.located()` deep-copies `__dict__`, including the anytree parent, so every flattened
leaf dragged a BRep copy of the whole assembly (OOM-killed at 11.8 GB). New `geom.placed()`
re-locates the shared TShape instead (verified identical volume/bbox/label to `located()` on
all 33 hatch-assembly leaves); `assembly_step27.main` also frees each assembly before the
next. Assembly export now peaks at ~1.0 GB / 47 s; the full regression ~1.1 GB / 521 s.

## 5. Not done here
- No Blender/visual work: the change is a 3 mm rib re-path hidden under the leaf, and
  no render was authorised by this step's pass criteria; fresh visuals belong to the
  step-30 independent review / step 21 card.
- No physical calibration, purchase, vendor contact, fitment, structural, sealing or
  approval claim. Independent review is step 30 (different provider/model).
