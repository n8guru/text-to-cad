# Step 6 engineered CAD shell report

Status: **provisional authoritative CAD, pending independent verification**

## Result

The selected Step 5 sparse profiles are rebuilt directly in CAD as
`TOPPER_ENGINEERED_SANDWICH_SHELL_PROVISIONAL`. The rear shoulder is now
`1600 mm`, matching the selected photo-derived profile set. The shell is the
outer loft minus an inset loft using the provisional `22 mm` sandwich total.
It remains `ESTIMATED` in shape and makes no measured-fit or structural-rating
claim.

The engineered subassembly also identifies:

- datum A: the provisional bed-rail mounting plane at `Z=0`;
- datum B: the vehicle centerline at `Y=0`;
- datum C: the rear closure plane at `X=1462 mm`;
- two provisional longitudinal base flanges;
- the late-calibration base-interface reserve and the Step 8 hatch reserve;
- two transverse shell load-path bands aligned to provisional topper
  crossbar stations.

These named solids are review and downstream-design controls. The load-path
bands are not a capacity result. Later steps remain responsible for sectional
joints/modules, hatch and sealing, mounts/interfaces, integrated systems,
layup/hardpoints/tooling, and late hard-measurement calibration.

## Authority and provenance

CAD is authoritative for units, axes, datums, solid geometry, naming, and the
generated STEP. Exterior styling remains photo-derived `ESTIMATED`; base
interface geometry remains `PLACEHOLDER REQUIRING SCAN` until the bounded late
calibration step. The model does not claim rail contact, sealing, clearances,
load capacity, fabrication readiness, or production fitment.

## Checks

`step6_checks.py` proves that CAD station tuples match every selected sparse
profile, the engineered shell is a non-empty inset of the selected envelope,
and all flange, datum, keep-out, and load-path artifacts are present and
explicitly provisional.
