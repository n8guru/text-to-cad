# Design decisions — Step 11 production intent

- Step 11 preserves the exact verified Step 7, 8, 9, and remediated Step 10
  commits as merge ancestors, then composes their component geometry into one
  nonduplicated shell assembly.
- The integrated shell retains the three real section gaps and six module
  openings, then applies the rear-hatch, camera, and brake-light cuts.
- Two provisional `80 × 80 mm` transverse sandwich-frame envelopes connect
  the four roof hardpoint regions. Four mount, four crossbar, and five
  hatch/strut insert plates make local load-transfer intent explicit.
- The layup schedule is zone-based: general shell, reinforced transverse
  frames, section-joint doublers, mount inserts, and hatch inserts.
- Three CNC master/fixture envelopes follow the verified section boundaries.
  Final mold surfaces, trim/drill templates, and travelers remain Step 13/14
  calibration and release outputs.
- Structural screening uses a `9.0 kN` factored placeholder total load split
  across four paths. It predicts `71.64 MPa` local skin stress, `7.97 mm`
  frame deflection, `0.370 MPa` core shear, and `0.104 MPa` bondline shear.
  Positive screening margins are not design allowables, ratings, or proof.

- Step 10 derives from the unchanged verified Step 6 shell so the parallel
  Step 7, Step 8, and Step 9 packages remain independently composable.
- A centered rear camera provision is packaged at `X=1380 mm, Z=700 mm` with
  a rearward optical keep-out. This is a packaging location, not a calibrated
  field of view or Rivian-camera compatibility claim.
- A `900 mm` high-mounted brake-light envelope is centered in the rear header
  at `Z=720 mm`. Its shell passage is real CAD; lamp photometry, certification,
  visibility angles, and legal sufficiency remain untested.
- Two symmetric `760 × 24 × 12 mm` interior task-light envelopes sit below the
  roof. Light output, glare, switching, thermal behavior, and sealing remain
  downstream engineering work.
- The mechanical harness path is a driver-side base raceway, rear riser,
  header branch, camera drop, and accessible service junction. It reserves
  space only; circuit count, conductor gauge, fusing, grounding, EMC, and
  connector selection remain deliberately unspecified.
- The forward driver-side vehicle-ingress volume is labeled
  `PROTOCOL_UNKNOWN` and `PLACEHOLDER_REQUIRING_SCAN`. Unknown Rivian camera,
  brake-light, interior-light, power, and control protocols are not inferred.

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
