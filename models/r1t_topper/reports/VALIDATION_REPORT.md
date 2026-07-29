# Validation report — Step 9 mount and vehicle interfaces

Status: **PASS for producer-side Step 9 review; independent verification pending**

## Checks run

- Python compilation passed for all CAD sources.
- `cad/checkpoint1_checks.py` still passes the manufacturer-reference bed
  envelope, tailgate, coordinate, and crossbar checks.
- `cad/phase2_checks.py` still passes the five ordered `ESTIMATED` silhouette
  sections, localized rear taper, full provisional footprint, and placeholder
  interface provenance checks.
- `cad/step6_checks.py` still passes the selected-profile, shell, flange,
  datum, keep-out, and transverse-load-path invariants.
- `cad/step9_checks.py` verifies:
  - all four receiver/bridge/pad stacks are connected, receiver envelopes
    intersect the corresponding factory-anchor references, and pads intersect
    the correct Step 6 base flange;
  - the tonneau and tailgate source couplers intersect the existing control
    keep-outs, and each mechanical route is continuous to its side pod;
  - four port envelopes sit symmetrically at the two intended topper stations,
    with hardpoint-to-shell and hardpoint-to-port intersections;
  - eleven vehicle/service keep-outs are present, labeled scan-required, and
    conservatively span the cab, tailgate, tonneau, release, and latch cases;
  - the top-level assembly contains the unchanged Step 6 baseline plus the
    four Step 9 interface groups.
- STEP generation passed for `R1T_TOPPER_ASSEMBLY.step`.
- CAD inspection reports 91 occurrences, 72 leaf shapes, 456 faces, 936
  edges, no warnings, and bounds `[-685, -875, -540]..[2002, 935, 813.93534]
  mm`. The extended rearward and downward bounds are the explicit tailgate
  motion/service reserves.
- Six regenerated snapshots were visually reviewed at original resolution.
  The four anchor stacks meet the lower flanges, both control paths terminate
  at driver-side pods, the roof ports are symmetric at both stations, and the
  translucent keep-outs remain distinguishable from physical components.

## Intent review

| Requirement | Result |
| --- | --- |
| Reference occupies the pickup bed, not an SUV conversion | PASS |
| Original pickup tailgate remains at/below bed-rail plane | PASS |
| Engineered shell matches the selected Step 5 sparse profiles | PASS |
| Four factory-anchor adapter stacks connect to the base flanges | PASS |
| Tonneau and tailgate mechanical relocation paths are continuous | PASS |
| Four symmetric topper crossbar port/hardpoint envelopes exist | PASS |
| Vehicle-motion and service keep-outs are explicit | PASS |
| Factory mating profiles and control travel | NOT TESTED — late calibration |
| Mount/crossbar strength and hardware | NOT TESTED — Step 11 |
| Production cab/body interfaces | NOT TESTED — late calibration |
| Structural capacity and laminate schedule | NOT TESTED — Step 11 |

## Known limitations

No vehicle value has yet been physically measured. The bed length, exposed
cargo width, and maximum bed height are manufacturer references; their precise
values require confirmation on the target 2022 Gen 1 vehicle during the late
calibration step. The cab and bed rails remain crude block envelopes. The
shell is authoritative CAD but remains photo-derived and provisional. Step 9
supplies connected interface packaging, not calibrated mating surfaces or
verified motion. This report does not claim fitment, quick-release retention,
control operation, crossbar compatibility/capacity, structural capacity,
legal compliance, aerodynamic performance, electronics compatibility,
manufacturability, or production readiness.
