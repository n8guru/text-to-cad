# Step 11 production-intent report

## Scope

Step 11 composes the independently verified Step 7 sectional/module package,
Step 8 hatch package, Step 9 vehicle-interface package, and remediated Step 10
electrical package. The final assembly contains one integrated three-section
shell, not four duplicated baseline shells.

## Layup and hardpoints

| Zone | Provisional construction |
| --- | --- |
| General shell | 1.0 mm quasi-isotropic carbon / 20 mm foam / 1.0 mm carbon |
| Transverse frames | 2.0 mm carbon faces / 76 mm core at two load stations |
| Section joints | 4.0 mm internal doubler plus bonded keyed splice |
| Mount hardpoints | 4.0 mm aluminum insert in locally reinforced laminate |
| Hatch hardpoints | 4.0 mm aluminum insert in locally reinforced laminate |

The CAD exposes four mount inserts, four crossbar inserts, and five
hinge/strut inserts. Exact alloys, surface treatment, isolation plies,
fasteners, adhesive, ply drops, overlap, cure cycle, and inspection criteria
remain supplier/process selections and must be validated by coupons.

## Structural screening

The runnable check in `cad/step11_checks.py` uses a 3.0 dynamic factor on a
3,000 N placeholder load and splits 9,000 N across four paths.

| Check | Result | Screening threshold |
| --- | ---: | ---: |
| Frame skin stress | 71.64 MPa | 180 MPa |
| Frame deflection | 7.97 mm | 15.50 mm |
| Core shear | 0.370 MPa | 0.550 MPa |
| Mount bondline shear | 0.104 MPa | 4.000 MPa |

These are transparent first-order checks, not FEA, certified allowables,
structural capacity, payload rating, or fabrication authority.

## Tooling and assembly

Three CNC master/fixture envelopes align to the verified section joints and
include 12 mm trim stock plus 75 mm bag-seal/handling allowance. The assembly
sequence is:

1. CNC machine three female tool sections and trim/drill templates.
2. Lay outer skin, core, local frame plies, and hardpoint inserts.
3. Vacuum cure each section; trim and drill from common datums.
4. Bond/index both section joints and install module frames.
5. Install hatch, seals, drains, mounts, controls, lighting, and harness.
6. Perform dimensional, coupon, leak, electrical, and proof-load acceptance.

Final mold surfaces, calibrated drill coordinates, travelers, material batch
controls, cure records, inspection plans, proof loads, and fabrication release
remain Step 13/14 outputs.
