# Step 31 — rear-camera visibility provision (decision 2154445)

Project r1t-topper (924515), ledger step 31. Base: `agents/forge/r1t-topper@0bb4c68121eb`
(step 30a seal repair; its ancestor `2cabd89ef0`, the base the step names, is unchanged in the
rear geometry this step touches). Scope is **source-only design authority**: nothing was
purchased, no vehicle or hardware was touched, and Nate's sign-off is not implied.

Nate's request (decision 2154445): *"We also need a rear camera OR optics (maybe fiberoptic?)
extension to feed the rear camera, that is on the back of cab."*

## 1. Sources (all primary, SHA-256 pinned)

| Tag | Document | Where used |
|---|---|---|
| UPFIT | Rivian R1T Upfitting Guide, September 2025, `https://assets.ctfassets.net/2md5qhoeajym/5ysf6K5UtGtHedY1fMeClC/b83307f7e8f03838a1906bff88707f95/r1t-upfitting-guide-en-us-20250924.pdf`, sha256 `847d036f3977764d151689442ea54e4141bf70113b9d8380d46d796c3982552a` (same file the Step 27 package already pins) | p.49 rear view: item 10 **Truck bed camera** sits at the top centre of the cab back, under the roof edge between the two CHMSL lamps; item 11 **Rear surround view camera** sits at the centre of the rear bumper fascia above the hitch. p.105 item 5 repeats the bed camera. p.107: the bed camera view appears automatically *"When in R (Reverse) and the tailgate is down"*. p.108 *Modifications to Cameras*: *"Do not block the exterior camera field of view"*, *"Keep the camera in its current position"*, *"Do not modify the camera harness, including connectors"*, *"Avoid placing any light sources within the camera's field of view (FOV) limits"*, *"If a camera is moved … a calibration must be performed"*. p.109: sensors stay in their original positions; do not alter their mounting points or wiring. |
| OG | Rivian R1T Owner's Guide 2024-05-27, `https://assets.rivian.com/2md5qhoeajym/530xs9hu11xOKefT2JrvA5/46f6cb5d5756b8320d3eb494a902e66c/r1t-og-en-us-20240527.pdf`, sha256 `e6c544346ef87548d956934a46c2a656c24d3196ed271ff929ec213e59b775b6` | p.218 item 5 truck bed camera; p.219 automatic camera *"When in Reverse and the tailgate is down (truck bed view)"*; p.307 Gear Guard: *"A camera monitors the truck bed"*. |
| FMVSS | 49 CFR 571.111 (read at law.cornell.edu/cfr/text/49/571.111, 2026-11-27) | S6.2: trucks/MPVs ≤ 4,536 kg GVWR display a rearview image meeting S6.2.1–S6.2.7. S14.1.3: seven 0.8 m × 0.3 m test cylinders (A–E top band, F/G vertical stripe). S14.1.4: F/G 0.3 m, D/E 3.05 m, A/B/C 6.1 m behind the rear-bumper plane; A/D/F 1.52 m left, C/E/G 1.52 m right, B on the centreline. |
| USC | 49 U.S.C. 30122(b) (make-inoperative prohibition) | A manufacturer, distributor, dealer, rental company or repair business may not knowingly make inoperative a device installed in compliance with an FMVSS. Relevant because the product is commercial (insight 83761). |

Rivian rasters are **not** redistributed (same rule as the Step 4 reference package); the
measurements below cite page + item.

## 2. The gap, measured in the model

**Camera positions** (`cad/camera.py: CAMERAS`). Rivian publishes no coordinates. Both lenses are
scaled off the p.49 rear-view line drawing rendered at 400 dpi: the bed-camera lens is 10 px below
the roof line, the bumper camera 613 px below it. Two scale anchors disagree (roof→tailgate-top
gives 1.96 mm/px, roof→tyre-contact gives 1.78 mm/px), and the side-photo cab model in
`blender/params.json` tops out at the spoiler tip z 427, lower than the drawing reading
(z 443–446), which would float the lens in front of the modelled cab. The nominal bed-camera lens
is therefore placed **on** the modelled cab-back face (glass top (−180, 355) → spoiler tip
(−132, 427)) at z 420, the CHMSL strip — check `nominal_bed_camera_lens_lies_on_modelled_cab_back`
measures 0.03 mm to the cab keep-out — and the band runs up to the drawing reading. The checks
re-run at every band corner:

| Camera | Nominal (x, y, z) mm | Band |
|---|---|---|
| Truck bed camera (item 10) | (−136.7, 0, 420) | x −155…−130, z 405…450 |
| Rear surround view camera (item 11) | (1554, 0, −690) | x 1534…1564, z −750…−630 |

Frame: X rearward, Z up, origin bed front wall / rail top. The topper front face is x0 = −100, so
the bed-camera lens is **30–55 mm from the topper's carbon front wall** (37 mm nominal), at cab-roof height,
**above** the original front pass-through window (top z 315).

**Method** (`cad/camera.py: SightLines`). Camera aim and FOV are not published, so the
measurement is target-based: an exact B-rep line/face intersection (OCC
`IntCurvesFace_ShapeIntersector`) from the lens to each target, against every one of the 220
leaves of the closed Step 27 assembly plus the shell. A line that crosses any non-glazing part is
BLOCKED; one that crosses only `*PANE*` parts is THROUGH_GLAZING. The truck itself is not an
occluder (it hides what it hides with or without a topper).

Targets: (a) **bed view** — 121 points on the bed floor, x 100…1350, y −550…550; (b) **rear view**
— 21 axis points (base +50, mid-height, upper −75 mm) of the seven S14.1.4 object positions. (b) is a
line-of-sight screen at those positions, **not** the S14.1 photometric test.

| Measurement (nominal lens) | Pre-step-31 shell | Step 31 provision |
|---|---|---|
| Bed camera → bed floor, visible | **11 / 121 (9.1 %)**, 110 blocked by the shell front wall | **121 / 121 (100 %)** through the pane, all 11 rows x 100…1350 |
| Bed camera → S14.1.4 points (tailgate-down reverse role, hatch closed) | 0 / 21 | **21 / 21** through the front pane + one-piece hatch pane (rev 2; rev 1 was 6 / 21) |
| Bumper camera → S14.1.4 points, hatch closed **and** open 95° | 21 / 21 at nominal + 4 band corners | 21 / 21 at nominal + 4 band corners — **no topper part intersects any sampled sight line** |

Rear-view lens-band sensitivity (baseline → provision, OPEN `rear_view_lens_band_sensitivity_recorded`): (−155, 405) 0 % → 76 %; (−130, 405) 0 % → 76 % (the steepest centre/near rays pass under the hatch pane's bottom chord in the T-handle zone); (−155, 450) 0 % → 29 %; (−130, 450) 0 % → 0 % (a lens above the modelled cab looks over the slot into the roof roll). The full rear view is therefore claimed **only at the nominal lens**; tape-measure the lens at Step 22 and re-run.

Lens-band sensitivity, bed view (baseline → provision): (−155, 405) 27 % → 100 %;
(−155, 450) 9 % → 64 %; (−130, 405) 9 % → 100 %; (−130, 450) 0 % → 36 %. Improvement at every
corner, but if the real lens sits at the drawing-scaled height (z ≈ 445) the roof header hides the
rear rows of the bed again — tape-measure the lens at Step 22 and re-run the check before any
"full bed view" wording is used.

## 3. Routes considered

| Route | Verdict | Why |
|---|---|---|
| **A. Optical window in the topper front wall, in front of the unmodified camera** | **SELECTED** | Nothing electrical; the camera stays put and keeps its calibration; no harness work; it only *removes* an obstruction the topper itself created (UPFIT p.108). Same 5 mm hard-coat PC and VHB 5952 bond as the existing front pass-through pane (DWG-27-020, BOM line already sourced). |
| B. Relocate the bed camera to the topper hatch / extend its harness | Rejected | UPFIT p.108–109 forbid moving the camera, modifying its harness/connectors or mounting points, and require recalibration if moved. |
| C. "Fiber-optic extension" (coherent imaging bundle relaying the hatch view to the OEM lens) | Rejected, **no capability claimed** | No product was sourced that does this, and it would put an object directly in front of the lens (p.108: do not block the FOV, do not touch the lens). Resolution, FOV and light loss of such a relay are unknown; inventing them is exactly what this step must not do. |
| D. Notch or lower the topper roof header in front of the lens | Rejected as a **header-wide** change; rev 2 uses only a **160 mm glazed slot** in the front roll | A full-width notch breaks the charter's uninterrupted R1S-like top plane and weakens the front frame. The glazed slot stays below the roof plane (z 418–421 vs roof 462) and is the narrowest cut the measured rear rays need. |
| E. Separate aftermarket hatch camera + own display | Not selected here (OPEN) | Does not "feed" the Rivian camera; adds electronics and an unsourced part. Candidate for a later optional accessory step with its own sourcing. |

## 4. What is drawn (authoritative CAD)

* `cad/shell.py: CAMERA_TAB, _camera_tab_cut()` — a 440 mm wide centre **camera tab** extending
  the front window from z 280 to the top of the flat front face. The through-cut is **raked 0.60**
  (dz/dx of the far-bed sight line): inner edge z 392, outer edge z 405.2 at the outer face
  (SEC-31-001; the check's 1 mm probe 0.5 mm inside the face reads 404.6 and a measured rake of
  0.600), below the outer R50 roll start z 412. The rake lets the shallow rays clear both skins of the 22 mm wall.
* `cad/shell.py: front_pane()` — the front pane is now **one piece**: main outline + tab outline,
  each grown by its bond overlap (20 mm; 15 mm at the tab top so the pane stops 5 mm below the
  inner R28 roof roll). Measured pane-to-shell overlap 0 mm³.
* `shell(camera_tab=False)` / `front_pane(camera_tab=False)` rebuild the previous geometry **only**
  as the measured baseline.
* **Rev 2 (defect 61517, verify 165504: "does not restore its rearward view with the tailgate
  down").** Rev 1 left 15 / 21 rear sight lines blocked: all 15 crossed the front wall at
  z 407–415 (above the tab, in the inner R28 / outer R50 roof rolls) and 5 of them also hit the
  hatch leaf (3 on the 140 mm solid mullion, 2 at the lower outboard corners x ≈ ±490,
  y −90…−104 hatch-local). Two sourced-geometry changes, no new material or supplier:
  * `cad/shell.py: REAR_VIEW_SLOT, _raked_cut(), rear_view_pocket()` — a **160 mm centre slot**
    raked 0.15 (the shallowest sampled rear ray is 0.136) from z 360 to z 418 on the inner face
    (≈ 421 at the outer face). The rays fan only ±25 mm across the wall because the lens is
    ~37 mm away, so the slot stays narrow; it notches the front roll below the roof plane and the
    R1S-like top plane (z 462) is untouched (check `rear_view_slot_narrow_raked_and_roof_top_plane_untouched`).
    The one-piece front pane grows a 190 mm tongue to z 426 that bonds to the slot's cut face; a
    0.5 mm-clear pocket removes the inner-roll laminate that overhangs it (pane-to-shell
    overlap still ≈ 0 mm³).
  * `cad/hatch.py: WIN, _win_outline()` — the hatch's two windows + solid mullion become **one
    inside-glazed pane** (same 5 mm PC, 3 mm lip, screwed 6061 retainer). Bottom chord y −105.5,
    a 42 mm relief over each striker arm keeps the arm's full bonded footprint on carbon, and
    outboard of the arm the window drops to y −108 and widens to x ±520 for the D/E rays. The
    pocket/retainer is clipped at y −116 (10.5 mm overlap there) so it stays off the T-handle hole
    (check `hatch_one_piece_pane_keeps_striker_arms_on_carbon_and_clears_t_handle`). DWG-27-011 and
    DWG-27-014 (now 1 + 1 OFF) are regenerated; leaf mass and the retainer screw count follow
    the new outline.
  * Not claimed: the leaf's stiffness without the mullion (the Step 33 load pack did not include
    it — re-run its hatch hand-calc on this pin), image quality through two PC panes and a cabin
    in between, glare/reflections, or any Rivian software behaviour.
* Line of sight is SAMPLED (121 + 21 points); the 1 mm lens/target trims and the face-only
  intersector are documented limits of `SightLines.trace`.
* Section **SEC-31-001** (`drawings/SEC-31-001_bed_camera_sightline.svg`): centreline side profile
  with cab keep-out, shell, pane and the `00_REFERENCE` bed-camera sight fan (nominal lens → bed
  floor x 100…1350). DWG-27-020 notes carry the tab and the p.108 rule. The STEP/STL outputs are
  regenerated from these sources (`out/PROVENANCE.json`).
* Mass: −0.21 kg carbon (789,236 mm³ removed), +0.20 kg PC (163,733 mm³ added): net ≈ 0.

## 5. Checks

`python step27/cad/checks_step31_camera.py` → `out/checks_step31_camera.json`
(15 PASS / 0 FAIL / 1 OPEN at this pin). The full Step 27 suite and provenance check are re-run on
the regenerated package (counts in the commit message / step evidence).

## 6. Open items and boundaries (nothing here is claimed)

1. **Bed-camera rear view with the tailgate down: restored at the nominal lens only** (rev 2,
   check `provision_restores_bed_camera_rear_view_tailgate_down_at_nominal_lens`, 21 / 21 sampled
   sight lines through glazing, hatch closed). It depends on the drawing-scaled lens height (OPEN
   `rear_view_lens_band_sensitivity_recorded`); until the lens is measured, owner notes must not
   promise the view. Line of sight only — two PC panes and the topper interior sit in the image.
2. **Which camera Rivian certifies for FMVSS 111 S6.2 is not published.** The measured result is
   that the topper does not enter any sampled bumper-camera sight line to the S14.1.4 positions (hatch
   closed or open). If Rivian's certified image used the bed camera with the tailgate down, the
   rear view in (1), if it fails at the measured lens, becomes a 49 U.S.C. 30122 make-inoperative question — ask through the Rivian
   Upfit program (step 38 packet) before commercial release.
3. **Image quality through 5 mm PC at 30–55 mm from the lens** (reflections, haze, night glare,
   dirt/condensation between cab and topper) is untested — physical check at the prototype
   (step 24). No light source may be placed in the sight fan (UPFIT p.108); the package has no
   interior lamp today.
4. **Lens position** is drawing-scaled (± band above); tape-measure at Step 22 and re-run the
   check. Gear Guard / Rivian software behaviour is not modelled.
5. Front-wall structure: the tab removes 0.79 L of front-wall laminate above the window; the
   step 33 load pack did not include this aperture — re-run its front-frame hand-calc on this pin.
