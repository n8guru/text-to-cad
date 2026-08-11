# Step 15 operator_visual package

This package is a presentation-only derivative of the independently verified
Step 11 geometry at commit `6e0229cecefee0043aed9ea607c5241c1fe7f815`.

The visible exterior is a freshly re-embodied continuous rounded loft: its
sidewalls, shoulder transitions, and crown use radiused curves rather than the
old flat six-cartridge form. Each side has exactly two broad shell-conformal
glazing lights with actual radiused cut geometry. The 110 mm carbon bridge
between those lights is positive remaining shell material and exceeds the 76 mm
/ three-inch minimum. The rear is one clean, closed, continuous-corner hatch
leaf with exactly two rounded broad panes and a 140 mm center carbon bridge.
No duplicated hatch leaf or top-center protrusion is included.

The B-side hatch derivative explicitly carries the closed and open panel,
continuous frame, hinge/latch package, seal, gutter, and drainage package; it
is inspectable without obscuring the operator's clean closed-product render.
The `00_REFERENCE` truck dummy and engineering keep-outs are excluded from the
review assembly. The eight retained port/hardpoint envelopes are re-seated into
the curved crown and are shell-intersecting topper-owned interfaces only. No
rigid or freestanding `CROSSBAR_REFERENCE` bar is included; an accessory bar is
a separate fit-check item, not product geometry.

The dimensions remain provisional visual-design controls. This artifact does
not claim calibrated fitment, sealing performance, structural rating,
fabrication readiness, or production release. Step 13 may apply research or
physical calibration at any time, and Step 14 remains the production authority.

Regenerate with:

```bash
../../.venv/bin/python cad/exports_step15.py
../../.venv/bin/python cad/step15_checks.py
```

The checker derives side, rear, and port labels from the design ranges and
compares their sets for equality. Its adversarial source mutations reject wrong
side/rear bridge widths and replacement of either rounded opening profile with
a square one.
