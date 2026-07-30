# Step 8 rear hatch, weather seal, drainage, and service report

Status: **provisional authoritative CAD, pending independent verification**

## Result

Step 8 derives a hatch-ready shell from the unchanged verified Step 6 shell.
The rear wall now has a real `1450 × 620 mm` opening beginning at the
provisional `Z=80 mm` base-rail plane. A four-sided `35 mm`-deep frame carries
a closed `22 mm` sandwich hatch leaf with a `20 mm` perimeter overlap.

The assembly also packages:

- a continuous four-segment primary compression-seal envelope;
- a header gutter and two side gutters feeding symmetric low-point outlets;
- a full-width rear-header hinge-axis envelope;
- symmetric body/hatch gas-strut mount service envelopes;
- lower-center latch service access; and
- the hatch leaf rotated to the provisional `75°` open position as a swept
  review keep-out.

The closed leaf is authoritative layout geometry. The open leaf is a keep-out,
not a second physical hatch.

## Authority and limits

All Step 8 dimensions are `DESIGN DECISION`, `ESTIMATED`, or
`PLACEHOLDER REQUIRING SCAN`. This step does not claim water tightness, bulb
seal selection, drain flow rate, gas-strut force, latch strength, rear-light
clearance, camera/brake-light integration, structural capacity, calibrated
tailgate clearance, fitment, or fabrication release. Electronics remain Step
10 work; laminate, hardpoints, hardware sizing, and rated structure remain
Step 11 work.

## Checks

`step8_checks.py` proves that the opening removes real Step 6 shell material,
the derived shell remains non-empty, all frame/seal/drain/service components
exist, drainage has two low-point outlets, mechanism envelopes remain
symmetric and scan-labeled, the open leaf moves rearward from the closed
position, and the exported assembly uses the Step 8 hatch-system label.
