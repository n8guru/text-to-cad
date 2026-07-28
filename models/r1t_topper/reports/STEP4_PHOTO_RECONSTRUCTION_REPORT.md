# Step 4 photo-derived reconstruction report

Status: **PASS for reproducible visual-target package**

## Evidence set

- Five reproducible official Rivian source views are pinned by source URL,
  asset SHA-256, document page or image identity, review resolution, view
  class, use, and redistribution boundary in
  `references/photo_reconstruction/sources.json`.
- Coverage includes R1S front/rear and side orthographic illustrations, R1T
  front/rear and bed context, and an R1S three-quarter manufacturer
  photograph.
- Normalized crop-space landmark traces, camera class, interpretations, and
  uncertainty are recorded in
  `references/photo_reconstruction/observations.json`.
- Dimensionless silhouette target bands, qualitative constraints, the current
  five-station starting hypothesis, and explicit Step 5 inputs are recorded in
  `references/photo_reconstruction/reconstruction.json`.
- `outputs/reference/photo_reconstruction/multi_view_reconstruction.svg`
  presents project-authored side, rear, plan, and three-quarter linework
  without redistributing the source rasters.
- `outputs/reference/photo_reconstruction/target_summary.json` records the
  machine-evaluated relationship between the current surrogate and the new
  target bands.

## Source audit

The exact remote assets used during authoring were fetched on 2026-07-28 and
matched these SHA-256 values:

| Asset | SHA-256 |
| --- | --- |
| R1S Owner's Guide PDF, version 2024.27 | `27eda35d31ee2d38baae97d336d2fb38e128f1fdc04ab9f9334c21e8e8977061` |
| R1T Owner's Guide PDF, version 2024.19 | `e6c544346ef87548d956934a46c2a656c24d3196ed271ff929ec213e59b775b6` |
| Rivian story R1S three-quarter image, 1200 × 520 review rendition | `9bb5df6cdb485892e0b061ce255ba31e760217a53f612e403328cf0dceeaa616` |

The five operator-supplied 2026-07-27 screenshots remain historical,
external-only qualitative references. They are not presented as reproducible
numeric evidence because their original files are not in the repository.

## Reconstruction findings

- The references support a nearly level roof and nearly parallel roof edges
  through `x=0.78`, with visible drop and narrowing concentrated in the final
  rear segment.
- The rear target stays broad, with a shallow crown and continuously rounded
  upper corners rather than planar chamfers.
- The current sparse-station surrogate falls inside the new target bands for
  roof height at `x=0.78`, rear roof height, roof width at `x=0.78`, rear roof
  width, and constant base width.
- Its rear shoulder ratio is `0.964497`, outside the derived
  `0.930..0.955` target. This is a concrete Step 5 styling input, not a reason
  to rewrite Step 4 evidence or to claim the current skin is accepted.
- Perspective views are explicitly excluded from direct width, length, and
  station-position inference.

## Checks run

```text
PHOTO_RECONSTRUCTION_BUILD_PASS
PHOTO_RECONSTRUCTION_REFERENCE_CHECKS_PASS
CHECKPOINT_1_REFERENCE_CHECKS_PASS
PHASE_2_CONCEPT_ENVELOPE_CHECKS_PASS
git diff --check: PASS
```

The reference check validates source coverage and fingerprints, normalized
landmark bounds, perspective exclusions, target-band consistency, the one
expected current-hypothesis mismatch, and byte-identical regeneration of both
generated artifacts in a temporary directory.

## Authority boundary

This report completes the visual reconstruction/reference-package step only.
It does not accept an aesthetic skin and does not change the authoritative CAD
datum, scale, footprint, interfaces, or station provenance. Step 5 must author
and compare sparse editable styling profiles, resolve or explicitly justify
the rear-shoulder mismatch, and retain `ESTIMATED` provenance. No fitment,
clearance, sealing, structural, fabrication, or production claim is made.
