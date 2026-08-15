# Step 15 operator_visual package

This package is a presentation-only derivative of the independently verified
Step 11 geometry at commit `6e0229cecefee0043aed9ea607c5241c1fe7f815`.

The packet also includes a dedicated `interchangeability.png` view and
`R1T_TOPPER_STEP15_INSERT_INTERCHANGEABILITY.step`/`.glb` evidence assembly.
It isolates one driver-side aperture and the three normal-direction exploded
choices so the shared interface is visible without relying on the full-vehicle
camera framing.

The visible exterior is a freshly re-embodied continuous rounded loft: its
sidewalls, shoulder transitions, and crowned roof use radiused curves rather
than the old flat six-cartridge form. The review packet includes a restrained
R1T presentation context (cab mass, bed, tailgate, rails, and wheels) so the
roof/side/corner relationship is judged on a recognizable pickup rather than
as an isolated shell.

Each side has two broad apertures with a shared interface: an aperture datum,
continuous flange/seal land, four provisional retention fastener envelopes,
and a positive shell load-path bridge. The window is a separate, constant-Y
planar pane with its own mating flange and retention pattern. An exploded
interchangeability proof places that same first driver-side aperture beside
three insert choices—WINDOW, CAGE, and TOOLBOX—using identical X/Z profile,
flange, seal land, and retention centers. This demonstrates interchangeability
as CAD geometry rather than asserting it from labels.

The 110 mm carbon bridge between the side apertures is positive remaining shell
material and exceeds the 76 mm / three-inch minimum. The rear is one clean,
closed, continuous-corner hatch leaf with exactly two rounded broad panes and
a 140 mm center carbon bridge. No duplicated hatch leaf or top-center
protrusion is included.

The B-side hatch derivative explicitly carries the closed and open panel,
continuous frame, hinge/latch package, seal, gutter, and drainage package; it
is inspectable without obscuring the operator's clean closed-product render.
The engineering `00_REFERENCE` dummy and keep-outs are excluded from the review
assembly; the new presentation context is deliberately limited to recognizable
vehicle cues and carries no fitment authority. The eight retained
port/hardpoint envelopes are re-seated into the curved crown and are
shell-intersecting topper-owned interfaces only. No rigid or freestanding
`CROSSBAR_REFERENCE` bar is included; an accessory bar is a separate fit-check
item, not product geometry.

The dimensions remain provisional visual-design controls. This artifact does
not claim calibrated fitment, sealing performance, structural rating,
fabrication readiness, or production release. The interface is an embodiment
contract and packaging proof; seal compression, fastener sizing, laminate
allowables, and vehicle mating geometry remain open calibration/proof work.
Step 13 may apply research or physical calibration at any time, and Step 14
remains the production authority.

Regenerate with:

```bash
../../.venv/bin/python cad/exports_step15.py
../../.venv/bin/python cad/step15_checks.py
```

The checker derives side, rear, insert, interface, and port labels from the
design ranges and compares their sets for equality. Its adversarial source
mutations reject wrong side/rear bridge widths and replacement of either
rounded aperture profile with a square one. It also verifies constant-Y pane
thickness, four-point retention, shell-intersecting load-path bridges, the
WINDOW/CAGE/TOOLBOX shared-profile proof, and the served 2400x1600 (3:2)
delivery dimensions recorded in the manifest.
