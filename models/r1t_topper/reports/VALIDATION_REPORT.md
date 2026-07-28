# Validation report — Step 6 provisional engineered shell

Status: **PASS for producer-side Step 6 review; independent verification pending**

## Checks run

- Python compilation passed for all CAD sources.
- `cad/checkpoint1_checks.py` still passes the manufacturer-reference bed
  envelope, tailgate, coordinate, and crossbar checks.
- `cad/phase2_checks.py` still passes the five ordered `ESTIMATED` silhouette
  sections, localized rear taper, full provisional footprint, and placeholder
  interface provenance checks. It now also pins the selected `1600 mm` rear
  shoulder.
- `cad/step6_checks.py` verifies:
  - every CAD station coordinate matches the selected Step 5 sparse profiles;
  - the shell is a non-empty inset of the selected exterior envelope;
  - the two base flanges, three controlling datums, two keep-out groups, and
    two transverse shell load-path bands are present and labeled provisional;
  - shell thickness is a design decision and the base-interface reserve
    remains `PLACEHOLDER REQUIRING SCAN`.
- STEP generation passed for `R1T_TOPPER_ASSEMBLY.step`.
- CAD inspection reported a labeled assembly with 33 leaf
  occurrences/shapes, 222 faces, 468 edges, no warnings, and overall bounds:
  - minimum `[-685, -875, -510] mm`
  - maximum `[1462, 875, 813] mm`
- The `Z=0` datum plane spans the full `1462 × 1730 mm` provisional
  footprint.
- Six regenerated snapshots were visually reviewed. The blue sandwich shell,
  amber rear-hatch reserve, cyan datums/crossbar references, dark base flanges,
  and yellow transverse load-path bands are distinct and correctly placed.

## Intent review

| Requirement | Result |
| --- | --- |
| Reference occupies the pickup bed, not an SUV conversion | PASS |
| Original pickup tailgate remains at/below bed-rail plane | PASS |
| Engineered shell matches the selected Step 5 sparse profiles | PASS |
| Shell has a provisional sandwich thickness | PASS |
| Controlling datums and longitudinal base flanges are explicit | PASS |
| Interface and rear-hatch keep-outs are explicit | PASS |
| Provisional transverse load paths are explicit | PASS |
| Production cab/body interfaces | NOT TESTED — late calibration |
| Structural capacity and laminate schedule | NOT TESTED — Step 11 |

## Known limitations

No vehicle value has yet been physically measured. The bed length, exposed
cargo width, and maximum bed height are manufacturer references; their precise
values require confirmation on the target 2022 Gen 1 vehicle during the late
calibration step. The cab and bed rails remain crude block envelopes. The shell
is authoritative CAD but remains photo-derived and provisional; it is not a
calibrated mounting system, clearance proof, laminate schedule, or mold
definition. This report does not claim fitment, structural capacity, legal
compliance, aerodynamic performance, electronics compatibility,
manufacturability, or production readiness.
