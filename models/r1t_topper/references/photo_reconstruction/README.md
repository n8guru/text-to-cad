# Photo-derived reconstruction package

Status: Step 4 visual-reference package. This package constrains the next
styling step; it does not change the authoritative CAD envelope and does not
establish vehicle fit.

## What is here

- `sources.json` identifies the exact official Rivian source pages/assets,
  page or frame used, local-review fingerprint, licensing boundary, and view
  role. The source rasters are intentionally not redistributed.
- `observations.json` records normalized image-space landmarks and the camera
  interpretation used for each view. Coordinates are relative to each listed
  crop, not vehicle millimetres.
- `reconstruction.json` turns the cross-view observations into bounded,
  dimensionless silhouette targets. It also records the current five-station
  surrogate as the Step 5 starting hypothesis.
- `build_reference_package.py` generates the review linework and a machine
  readable target summary using only the checked-in JSON.
- `check_reference_package.py` validates source coverage, provenance,
  perspective handling, target bands, current-hypothesis status, and exact
  regeneration.

Generated review artifacts live in `outputs/reference/photo_reconstruction/`.

## Method

The package separates three kinds of evidence:

1. **Orthographic anchors.** Official owner-guide front/rear and side
   illustrations constrain symmetry, roof crown, shoulder easing, roof-edge
   parallelism, and localized rear-corner taper. They are illustrations rather
   than manufacturing drawings, so only normalized ratios and broad bands are
   retained.
2. **Perspective cross-check.** The official three-quarter R1S photograph
   confirms the same qualitative roof and rear-corner behavior. It is not used
   to infer width or length directly because foreshortening is not calibrated.
3. **Target-truck context.** Official R1T rear and bed views identify the target
   visual frame and open-bed context. They do not turn the provisional rail or
   cab blocks into measured interfaces.

The current five-station CAD surrogate is evaluated against the derived bands
but remains only a starting hypothesis. Step 5 must author and visually compare
the aesthetic skin; it may adjust sparse profiles inside the target bands and
must not promote image ratios to measured dimensions.

## Regenerate and check

From `models/r1t_topper`:

```bash
python3 references/photo_reconstruction/build_reference_package.py
python3 references/photo_reconstruction/check_reference_package.py
```

Both scripts use the Python standard library and do not fetch network assets.
To audit a source, retrieve it from its `asset_url`, confirm the recorded
SHA-256 and pixel/page identity, and review the specified crop. A changed
remote asset requires a deliberate manifest update; never silently accept a
new fingerprint.

## Interpretation boundary

- All observation coordinates are normalized image-space annotations.
- All reconstruction targets are dimensionless visual ratios or qualitative
  constraints with uncertainty.
- Perspective views are explicitly excluded from direct metric inference.
- The checked-in CAD datum, scale, station X positions, footprint, and
  engineering authority remain unchanged.
- No fitment, clearance, sealing, structure, fabrication, or production claim
  follows from this package.
