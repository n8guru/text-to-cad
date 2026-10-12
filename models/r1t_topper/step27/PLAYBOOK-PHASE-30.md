# Physical-product playbook — Step 30 revision
Task147368 / attempt1, 2026-10-12. Producer record, not independent verification.

## Scope and authority
Decision2154445 separates a hatch-bottom-width/mounting revision (this step) from
camera provisions (31), improved reference vehicle (32), Nate-only visual sign-off
(21), and late calibration/fabrication. Start from reviewed text-to-cad
79935a1933381268592c8a1b6d80b61b6b40ef37 in an isolated source clone. No live vehicle,
purchases, fabrication or fitment authorization.

## What worked
- Inspect original product images as well as page text. The Weistec installation
  animation distinguishes a bolted bridge-capture adapter from an assumed threaded
  port stud. TWRAPS is a garage surrogate, not an on-vehicle load-rated part.
- Change the *primary* four-foot attachment, not an auxiliary security accessory:
  continuous provisional reference bridge, wrapped C-jaw slider, and matching body
  entry/slider channels. Test retained and released geometry independently.
- Carry uncertainty into dimensions, drawings and result captions. Public topology
  does not reveal proprietary OEM dimensions, orientation or preload.
- Export solids once, render those exact meshes in the managed Blender loop, and
  look after every step. Orange jaw / violet reference bridge cutaways make capture
  and release legible without pretending the hidden housing is absent.
- Register external CAD evidence through the canonical gen_request frontdoor,
  publish inspected bytes and fetch them back for byte equality. Registration is
  provenance, not a reviewer verdict.

## What failed / avoid
- One delegated attempt drifted into a detached anti-theft hook rather than the
  requested primary mounting revision. It was stopped; its two untracked files
  were removed, and none of its geometry is submitted.
- A second delegated hatch draft widened only a nominal envelope and accepted a250 mm
  lower-chord tolerance. Producer solid slicing found1092 mm instead of1299 mm;
  that run was stopped. The final producer correction uses a true straight1299 mm
  lower chord,0.1 mm test tolerance, correct counter-clockwise extrusion orientation,
  and a connected strut support web preserving the existing solved stud positions.
- Generic Blender-loop cameras are poorly framed for a full truck. Keep mandatory
  loop stills for audit, but provide purpose-framed orthographic rear and mechanism
  views for the review. Do not substitute the attractive perspective for a width
  check.
- A wall fixture's plate dimensions and advertised load do not define the truck
  port or rate a custom topper. Legacy lower-lip stress arithmetic cannot validate
  the new C-jaw web/upper lip; keep that check OPEN.
- Full assembly regression caught a real defect missed by the leaf-only checks:
  sweeping a closed bulb-seal pipe through square lower corners produced invalid
  Boolean behavior and apparent crossbar/interference. Fix the seal as a tangent-
  continuous open-bottom U path, fail closed on invalid solids, add bounded-volume
  and no-bottom-run checks, then regenerate all artifacts and replace the visuals.
  The flange test also had to sample the actual flared bond strip rather than the
  old rectangular aperture. Do not relax its physical bond-gap criterion.
- The first closed-import invocation incorrectly asserted a bare-contact gap <=1 mm.
  It measured4 mm, matching the existing compressed EPDM pad. Preserve that failed
  invocation in the loop ledger; compare against the authored pad datum on rerun,
  rather than translating the topper to hide the failure.
- Existing truck reference is a visibly approximate drawing-derived proxy.
  Improving it belongs to step32, not silent remodeling under this narrower task.

## Tools, time, cost
Native build123d0.11.1 source/STEP/STL; Blender5.2.2 CPU Cycles via blender-loop;
Studio authenticated helpers; webx/page and image inspection. No paid images,
purchases, quotes or GPU claim. CPU renders use32 samples for mounting detail;
model/API compute billing was not exposed and is not estimated. Work began around
04:57UTC; exact stage timestamps are recorded in the blender-loop evidence ledger
and immutable commit history. This phase is a design-study iteration, not a
generalized proven manufacturing process.

## Reuse boundary
Generalizable: source-topology audit, source-bound mesh evidence, cross-section
width checks, separated nominal geometry and physical qualification.
Not established: OEM fit, clamp actuation forces, ratings, fatigue, crash retention,
sealing, tooling, or production acceptance. Independent exact-pin review still
owns the technical verdict; Nate alone owns subjective final approval.
