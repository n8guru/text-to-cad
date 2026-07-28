# Step 5 aesthetic outer-skin report

Status: **PASS for sparse photo-derived styling selection**

## Selected result

The selected return artifact is
`interchange/reference_only/blender_to_cad_style_selected.json`. It contains
five closed, symmetric, world-space sections and five named longitudinal
character lines in the verified millimetre-native `+X` rearward, `+Y` driver,
`+Z` up handoff convention.

The styling delta is deliberately minimal. Only the symmetric rear-shoulder Y
coordinates change, from `±815 mm` to `±800 mm`; the other 103 numeric point
coordinates remain unchanged from the Step 4 CAD starting scaffold. This
changes the full rear shoulder from `1630 mm` to `1600 mm` and resolves the
sole Step 4 mismatch without changing roof, height, base, length, datum, or any
vehicle interface.

## Multi-view validation

`outputs/reference/photo_reconstruction/step5_style_comparison.svg` provides
source-free side, rear, plan, and three-quarter comparisons between the Step 4
baseline and selected sparse curves. The evidence uses actual profile-derived
ratios and projected character lines. It does not redistribute source rasters
or treat perspective imagery as metric input.

| Target | Selected | Band | Result |
| --- | ---: | ---: | --- |
| Roof height at `x=0.78` | `0.993421` | `0.990..1.000` | PASS |
| Rear roof height | `0.980263` | `0.970..0.990` | PASS |
| Roof width at `x=0.78` | `0.992357` | `0.985..0.997` | PASS |
| Rear roof width | `0.961783` | `0.950..0.975` | PASS |
| Rear shoulder width | `0.946746` | `0.930..0.955` | PASS |
| Base width range | `1.000000..1.000000` | `0.995..1.005` | PASS |

Every selected value is inside its target band. There are no deliberate target
exceptions. The selected rear retains a broad upper body; its sparse section
is intended for the same rounded CAD transitions used by the baseline, not
planar facets.

## Reproducible checks

```text
STEP5_STYLE_COMPARISON_BUILD_PASS
STEP5_STYLE_SELECTION_CHECKS_PASS
PHOTO_RECONSTRUCTION_REFERENCE_CHECKS_PASS
CHECKPOINT_1_REFERENCE_CHECKS_PASS
PHASE_2_CONCEPT_ENVELOPE_CHECKS_PASS
git diff --check: PASS
```

The Step 5 check proves the handoff schema, axes, units, origin, five planar
closed sections, bilateral symmetry, exact two-coordinate delta, character-line
set, every target-band result, authority boundary, absence of mesh content, and
byte-identical regeneration of the SVG and JSON summary.

## Authority boundary and Step 6 input

The selected profiles remain `ESTIMATED` aesthetic exterior-silhouette input.
The Step 4 CAD/STEP baseline is intentionally unchanged. Step 6 must review and
rebuild these sparse curves into authoritative engineered CAD while defining
provisional thickness, datums, keep-outs, flanges, and structural load paths.

This step makes no measured-geometry, vehicle-fitment, rail-contact, sealing,
clearance, structural-capacity, tooling, fabrication, or production-release
claim. Dense mesh-to-STEP conversion remains prohibited.
