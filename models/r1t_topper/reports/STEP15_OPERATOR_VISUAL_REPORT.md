# Step 15 operator_visual package

This package is a presentation-only derivative of the independently verified
Step 11 geometry at commit `6e0229cecefee0043aed9ea607c5241c1fe7f815`.

The visible exterior is one continuous five-station lofted shell with the
R1S-like near-level roofline and curved shoulder edges retained. Each side has
six shell-conformal glazing bays (twelve total) separated by five 110 mm
structural carbon mullions. The rear is one clean hatch leaf over one shell
opening with one centered pane; no split leaf, duplicate leaf, center mullion, or top-center
protrusion is included. The `00_REFERENCE` truck dummy, top accessory-port
blocks, and engineering
keep-outs are excluded from the review assembly.

The dimensions remain provisional visual-design controls. This artifact does
not claim calibrated fitment, sealing performance, structural rating,
fabrication readiness, or production release. Step 13 may apply research or
physical calibration at any time, and Step 14 remains the production authority.

Regenerate with:

```bash
../../.venv/bin/python cad/exports_step15.py
../../.venv/bin/python cad/step15_checks.py
```
