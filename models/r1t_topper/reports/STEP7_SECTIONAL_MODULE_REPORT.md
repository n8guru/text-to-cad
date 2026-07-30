# Step 7 sectional flat-pack and modular side-panel report

Status: **provisional authoritative CAD, pending independent verification**

## Result

Step 7 derives a sectional/module assembly from the unchanged Step 6 shell:

- three shell segments with approximate X lengths of `569 / 316 / 569 mm`;
- `4 mm` assembly-control gaps at `X=571` and `X=891 mm`;
- an `80 mm`-wide by `4 mm`-thick internal splice-doubler envelope at each
  joint;
- two `24 × 30 × 8 mm` roof alignment keys per joint;
- three common `285 × 420 mm` module openings per side, centered at
  `X=411 / 731 / 1051 mm` and `Z=330 mm`;
- six identical common-interface frames with `22 mm` perimeter lands and
  `35 mm` depth;
- six installed cartridges covering the full positive compatibility set:
  solid, window, mesh, recovery-board, and utility.

The joints fall between the module openings. Every shell segment is shorter
than the `600 mm` driveway-handling envelope. Every cartridge retains the same
opening-width and opening-height boundary; visual subfeatures vary only within
that common cartridge envelope.

## Authority and boundaries

The Step 6 exterior, `22 mm` shell thickness, datums, base flanges, keep-outs,
and load-path references remain unchanged inputs. Step 7 adds engineered CAD
authority for the provisional section split, splice/interface packaging, real
side openings, common frames, and cartridge envelopes.

The model does **not** claim joint strength, fastener or adhesive selection,
laminate schedule, manufacturing tolerance, sealing, drainage, glazing
retention, rated accessory load, vehicle fitment, or fabrication readiness.
Step 8 owns hatch/weather/service design, Step 9 vehicle mounting, Step 10
electrical integration, and Step 11 structure, layup, hardpoints, tooling,
fasteners, and assembly validation.

## Checks

`step7_checks.py` proves positive, non-null outcomes: three non-empty shell
segments; two non-empty joint doublers whose four keys physically intersect
their doublers; six actual shell openings; six common frames physically
intersecting the source shell; six non-empty cartridges; all five required
module variants; common cartridge X/Z boundaries; no cutter/segment residual
volume; joint placement between openings; and the sub-`600 mm` segment
handling limit.

The unchanged Step 6 checks still pass. The full exporter regenerates the STEP,
GLB, and six stable review views for independent inspection.
