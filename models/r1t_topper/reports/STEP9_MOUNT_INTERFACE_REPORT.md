# Step 9 mount and vehicle-interface package

## Delivered geometry

Step 9 derives a new assembly from the unchanged verified Step 6 shell:

- Four anchor-to-flange stacks, each with a placeholder factory-anchor
  receiver, removable bridge, and `160 × 90 × 16 mm` load-spreader pad.
- Two non-electronic mechanical control paths. Each retains a scan-required
  source coupler, connected vertical/outboard push-pull routing envelope, and a
  driver-side service pod at provisional `Y=905 mm`, `Z=150 mm`.
- Four topper-roof port envelopes at `X=350/850 mm`, `Y=±775 mm`, each
  connected to a `120 × 100 × 20 mm` shell hardpoint envelope.
- Eleven keep-out solids: cab relative motion, tailgate closed-to-open sweep,
  tonneau cassette/service, four mount release-access volumes, and four
  crossbar latch-service volumes.

The model deliberately uses simple inspectable solids rather than fabricating
unknown Rivian mating details. All components are parameterized in
`cad/parameters.py`, generated in `cad/mount_interfaces.py`, and guarded by
`cad/step9_checks.py`.

The regenerated STEP contains 91 occurrences, 72 leaf shapes, 456 faces, 936
edges, and no inspection warnings. Two consecutive export passes reproduced
all six PNGs byte-identically.

## Authority and downstream work

This step has CAD packaging authority only. It does not establish:

- factory anchor or accessory-port mating geometry;
- quick-release hardware selection, retention, fasteners, or rated loads;
- control function order, stroke, force, weather sealing, or tactile labeling;
- crossbar compatibility, capacity, laminate, or hardpoint strength;
- calibrated cab, tonneau, tailgate, rail, or human-access clearance;
- production fitment or fabrication authority.

Step 10 owns electrical systems. Step 11 owns laminate, hardpoints, hardware,
tooling, assembly sequence, and structural checks. Step 13 performs the late
bounded physical calibration, and Step 14 is the only fabrication-release
authority.
