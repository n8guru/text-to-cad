# Design decisions — Phase 2 conceptual envelope

- Global coordinates follow the requested vehicle convention: +X rearward,
  +Y driver side, +Z upward.
- The pickup tailgate remains a separate, bed-rail-height reference body.
- The conceptual topper footprint begins at the forward bed plane. This zero
  layout offset is not a production cab contact or seal specification.
- Crossbar references are boxes elongated only along Y, making all four
  crossbars transverse and perpendicular to vehicle travel.
- Reference geometry uses muted gray; keep-outs use amber; anchors use yellow;
  crossbars use cyan; the coordinate artifact uses RGB axes.
- Checkpoint 1 uses simple closed solids. Curved body styling, tooling, and
  structural claims are intentionally deferred.
- The target vehicle is a 2022 Gen 1 R1T. Published bed-envelope dimensions are
  promoted to manufacturer references, while every topper-contacting interface
  remains provisional until the target truck is measured.
- Phase 2 adds one translucent, closed master-envelope volume for silhouette
  review. Its full bed-edge base width, rear alignment to the tailgate outer
  plane, roof crown, and rear-corner treatment are design decisions—not
  production fitment claims.
- Five editable cross-sections now approximate the R1S upper-body silhouette
  over the R1T bed: nearly vertical lower sides, eased shoulders, a shallow
  roof crown, and a roofline/plan outline that stays almost parallel before
  narrowing and dropping locally at the rear corner. Their dimensions are
  `ESTIMATED` visual inputs designed to be replaced row-for-row by scan slices.
- Detailed shell offsets, modules, hatch, seals, joints, hardpoints, controls,
  ports, anchors, and mounting geometry remain intentionally absent until scan
  data establishes the vehicle interfaces.
- Step 4 separates reproducible visual observations from geometry authority.
  Official Rivian orthographic illustrations provide normalized silhouette
  anchors; an official three-quarter photo is a perspective-only cross-check.
  The resulting target bands constrain Step 5 while leaving the five-station
  CAD surrogate `ESTIMATED` and explicitly unaccepted as an aesthetic skin.
- Source rasters are not redistributed. The reference package records URLs,
  SHA-256 fingerprints, page/crop identity, normalized landmarks, uncertainty,
  and project-authored derived linework.
- Step 5 selects a minimal sparse styling delta: the rear section's full
  shoulder width changes from `1630 mm` to `1600 mm`; the other profile
  coordinates remain unchanged. The resulting front-normalized rear-shoulder
  ratio is `0.946746`, inside the photo-derived `0.930..0.955` band. All five
  other target checks remain inside their bands, with no deliberate exception.
- The Step 5 return artifact remains `ESTIMATED`, exterior-silhouette-only
  input. The existing CAD and STEP remain the verified baseline. Step 6 must
  review and rebuild the sparse curves into authoritative engineered CAD; no
  mesh-to-STEP path, fitment inference, or interface change is accepted here.
