# Step 30 review packet — decision2154445
**WORK IN PROGRESS — NOT COMPLETE.** Final full regression: **95 PASS, 1 FAIL,
12 OPEN**. The remaining failure is a **491.0 mm³ dry-surround / bulb-seal
interference** in the closed assembly. Do not approve, fabricate, or promote this
revision. Focused leaf/mount checks and visual inspection do not override that
whole-assembly failure. Independent review and Nate-only approval are not claimed. Task147368 attempt1, 2026-10-12.

Repository: `n8guru/text-to-cad`; branch
`agents/codex/task-147368-r1t-hatch-mount`. Baseline:
`79935a1933381268592c8a1b6d80b61b6b40ef37`.
The containing immutable commit is the review pin; Studio step30 records its full SHA.
**DEPLOY-N/A:** standalone CAD, not a Forage serving-code deployment.

## Scope delivered
- Actual1299 mm straight lower hatch edge, matching provisional tailgate-width
  estimate, with widened shell opening and open-bottom surround. Not a cosmetic
  bounding-box rename. See [hatch rationale](STEP30_HATCH.md).
- Source-informed primary four-foot bridge capture: C-jaws, continuous bridge entry
  and slider pocket. Weistec/TWRAPS imagery actually inspected; every proprietary
  mating dimension/orientation remains provisional. See [mount rationale](STEP30_MOUNTING.md).
- Complete closed/open assembly STEP, individual parts and rear-access mesh set,
  sections, dimensioned drawings and regenerated BOM, all bound by
  `out/PROVENANCE.json`. Existing filenames retain Step27 for downstream consumers.

## Producer checks
- Strict hatch suite:18 checks; actual lower-edge slice1299.0 mm against1299.0 mm
  target,0.1 mm tolerance; matching shell-cut chord1316.0 mm; correct leaf
  extrusion datum; valid single-solid leaf/surround; sampled shell/frame/gate
  clearance from0 to95 degrees.
- Mount suite:68 checks; one reference bridge, valid primary jaw/body, closed/caught
  uplift capture, sampled slider release, open vertical extraction, and use of the
  same jaw in all four primary foot assemblies.
- Managed Blender closed import:220 parts,22.4 mm nominal cab gap;4 mm pad gap
  agrees with the authored compressed EPDM datum. First invocation's incorrect
  bare-contact assertion is retained as a failed loop entry, not hidden.
- Open-access scene:220 parts, lowest raised leaf316.83 mm above rail,
  cargo top135 mm above rail,10/10 sampled exit rays clear. Cargo is a700 x600 x550 mm
  proxy, not a tested load.
- Full regression output is `out/checks.json`; read its PASS/FAIL/OPEN counts and
  exclusions rather than interpreting a nominal geometry result as physical approval.

## Fresh inspected visuals
The exact imported CAD is rendered; no AI redesign or image substitution.
The inherited truck is a rough drawing-derived **proxy**, not a photoreal scan.
Its lighting/body artifacts are visible and not represented as new accuracy.

| View | Public evidence |
|---|---|
| Closed, orthographic rear | [Image](https://forage.ink/static/uploads/r1t147368_S8_closed_final_closed_rear.png) |
| Closed, rear three-quarter | [Image](https://forage.ink/static/uploads/r1t147368_S8_closed_final_closed_rear3q.png) |
| Raised hatch + lowered gate, cargo access | [Image](https://forage.ink/static/uploads/r1t147368_S9_access_final_access_rear3q.png) |
| Open, straight rear | [Image](https://forage.ink/static/uploads/r1t147368_S9_access_final_access_rear.png) |
| Primary mount assembled, closed | [Image](https://forage.ink/static/uploads/r1t147368_S1_mount_closed_mount_closed_assembled.png) |
| Closed C-jaw bridge capture | [Image](https://forage.ink/static/uploads/r1t147368_S1_mount_closed_mount_closed_capture_cutaway.png) |
| Released C-jaw bridge clearance | [Image](https://forage.ink/static/uploads/r1t147368_S2_mount_released_mount_released_capture_cutaway.png) |

`evidence/step30/EVIDENCE_MANIFEST.json` binds source/mesh/image hashes and public
byte matches. Adjacent registration receipts record canonical gen_request
registered-artifact IDs. Loop JSON records the look-after-each-step sequence.
Neither registration nor producer inspection is an independent QC verdict.

## Reproduce / review
Fetch the exact published pin and its LFS assets. From the repo root, with the
existing build123d0.11.1 Python environment:
```sh
PY=/home/n8/text-to-cad/.venv/bin/python
$PY models/r1t_topper/step27/cad/provenance.py --check
$PY models/r1t_topper/step27/cad/checks_step30_hatch_width.py
$PY models/r1t_topper/step27/cad/checks_step30_mount.py
$PY models/r1t_topper/step27/cad/checks_step27.py
```
The full suite rewrites its report; use the source tree's provenance generator
after a deliberate regeneration. Generator order is recorded in PROVENANCE.json.
Blender import scripts live under `blender/`; acquire the singleton lease and use
the existing blender-loop skill, then inspect each step before advancing.

## Boundaries / next authorized work
No purchase, vehicle change, measured OEM fit, rated custom clamp load, sealing,
FEA, fatigue/crash retention, fabrication release or final visual approval.
Paddle drive linkage/lock interlock and interface calibration remain explicitly
OPEN; legacy lower-lip stress arithmetic is OPEN for the new C-jaw geometry.
Camera provision belongs to step31; improved licensed/source-derived truck
reconstruction to32. Fresh final Nate-only visual card belongs to21 after those
dependencies and independent reviews, not a producer self-signoff here.
Process learning is recorded in [PLAYBOOK-PHASE-30.md](PLAYBOOK-PHASE-30.md).
