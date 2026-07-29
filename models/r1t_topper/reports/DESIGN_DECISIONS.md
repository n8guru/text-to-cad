# Design decisions — Step 7 provisional sectional module system

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
- Modules, hatch, seals, joints, hardpoints, controls, ports, anchors, and
  mounting geometry remain assigned to later design steps; absent hard
  measurements do not gate their provisional design.
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
- Step 6 rebuilds the Step 5 return artifact as the CAD exterior loft and an
  inset provisional `22 mm` sandwich shell. Shape provenance remains
  `ESTIMATED`; no mesh-to-STEP path or fitment inference is accepted.
- Datum A is the `Z=0` bed-rail mounting plane, datum B is the `Y=0` vehicle
  centerline, and datum C is the `X=1462 mm` rear closure plane.
- Two `70 × 80 mm` longitudinal base flanges and two `45 mm` transverse shell
  bands establish provisional load-path intent. They are design controls, not
  structural-capacity claims.
- A `60 mm` base-interface reserve remains
  `PLACEHOLDER REQUIRING SCAN`; the rear opening is a Step 8 keep-out, not
  completed hatch geometry.
- Step 7 retains the Step 6 shell generator unchanged and derives a separate
  sectional/module assembly from it, so the verified exterior and thickness
  controls remain reproducible.
- Three shell sections use X extents of approximately `569 / 316 / 569 mm`,
  separated by `4 mm` gaps at `X=571` and `X=891 mm`. Both joints sit between,
  rather than through, module openings and keep every section inside the
  `600 mm` driveway-handling envelope.
- Each joint uses an `80 mm`-wide, `4 mm`-thick internal splice-doubler envelope
  and two `24 × 30 × 8 mm` roof alignment keys. These define assembly indexing
  and overlap packaging only; Step 11 owns fastening, laminate, strength,
  tolerance, and tooling authority.
- Each side has three common `285 × 420 mm` openings centered at
  `X=411 / 731 / 1051 mm`, with a `22 mm` perimeter land and `35 mm` frame
  depth. The six installed cartridges share that boundary.
- The positive compatibility set is solid, window, mesh, recovery-board, and
  utility. Recovery-board and utility details are attachment-envelope examples,
  not rated cargo retention or accessory-load claims.
- Step 7 does not implement the Step 8 hatch, seals, drainage, or service
  access; Step 9 vehicle mounts; Step 10 wiring; or Step 11 layup, hardpoints,
  tooling, structural checks, and assembly release.
