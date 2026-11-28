# Step 32: R1T reference assets, rights, dimensions and the improved truck proxy

Ledger: project 924515 (r1t-topper), step 32. Decision 2154445 asks for a web search for usable Rivian R1T
assets and a better estimate of the truck's size and shape for rendering. Revisions: task 165486 (first pin
`8024b241`), task 165497 (tailgate fix, `2a282d69`, section 5), task 165622 (this record corrected after verify
task 165502, section 6).

What this step is: a rights and provenance record for every truck reference the render lane touches, plus a
render-lane accuracy pass on the truck proxy. What it is not: a scan, a measurement of any real truck, a
calibration, a fitment approval, or legal advice. It changes no topper CAD. `blender/params.json`,
`step27/style/rivian_reference.json` and every `step27/cad/*.py` module are byte-identical to the base pin
`0bb4c68121eb6974c6f739c8db10159f3394a967` (the step 30a seal-repair revision, which carries 29 + 30). The
truck values the CAD checks use are therefore unchanged.

## 1. Reference assets and rights

How to read the table. "Observed" is what the source itself showed on the date given, and nothing more. Where
a row says "not established", this project did not find out and makes no claim either way. "Project decision"
is this project's own choice about using the asset. It is not a finding about the asset, and nothing here is
a legal opinion. Anything going into commercial marketing (the product is commercial, built at CubCrafters,
insight 83761) needs review by counsel first. Step 34 already includes a light Rivian trademark/naming check.
The machine-readable copy of the observations is `step27/evidence/step32/source_observations.json`.

| # | Asset | Where | Observed | Use in this project | Project decision for commercial renders |
|---|---|---|---|---|---|
| A1 | Rivian R1T Upfitting Guide, September 2025 (130 pages) | `assets.ctfassets.net/.../r1t-upfitting-guide-en-us-20250924.pdf`, sha256 `847d036f…552a` | Downloaded again 2026-11-28 (HTTP 200); the sha256 matches the local copy of 2026-10-13. Notice on p.2: "© 2025 Rivian Automotive, LLC. All rights reserved." and "This material may not be modified, reproduced, or copied, in whole or in part, without the prior written permission of Rivian Automotive, LLC, its affiliates, or its licensors." | Numeric specifications from printed pp.28-29 (section 2 gives the page of each value), and the p.59 plan-view outline traced into coordinates. The PDF and page rasters are not committed. | Do not reproduce its pages or drawings. The published numbers are used as numbers. Whether tracing an outline into coordinates needs Rivian's permission under that notice is not established here. It is a question for counsel before commercial use. |
| A2 | Rivian R1T Owner's Guide, Model Year 2022-2024, version 2024.19 (450 pages) | `assets.rivian.com/.../r1t-og-en-us-20240527.pdf`, sha256 `e6c54434…75b6` | Downloaded and re-hashed 2026-11-28. Notice on p.2: "© 2021-2024 Rivian Automotive, LLC. All rights reserved.", followed by the same no-reproduction sentence as A1. | Side and rear line art traced into the numeric silhouette (`rivian_reference.json`). The rasters are not committed. | Do not reproduce the artwork. The same open question as A1 applies to the traced numbers. |
| A3 | Rivian R1S Owner's Guide, Model Year 2022-2024, version 2024.27 (465 pages) | `assets.rivian.com/.../r1s-og-en-us-20240722.pdf`, sha256 `27eda35d…7061` | Downloaded and re-hashed 2026-11-28. Same notice as A2. | R1S style targets for the topper (lean and rake). | As A2. |
| A4 | The six entries of `references/photo_reconstruction/sources.json` | Rivian owner's guides (A2, A3), stories.rivian.com, and operator-supplied screenshots | Four owner's-guide illustrations and one photograph from stories.rivian.com carry the project's own note "remote reference only; Rivian copyright". The sixth entry is a set of operator-supplied R1S screenshots, noted "not available for redistribution"; where those screenshots came from is not recorded. The terms of the stories.rivian.com page were not re-read in this pass. | Qualitative silhouette observations. Fingerprints only, no committed rasters. | Do not use in marketing. |
| A5 | Sketchfab "Rivian R1T (2022)" by geyges, uid `6eca29c11ca44840baf93f47ef800006` | sketchfab.com | Sketchfab API, 2026-11-28: licence label "Free Standard", downloadable, 394,462 faces, published 2026-10-12, description "2022 Rivian R1T", tags `truck, pickup, offroad, forza, animated, interior, electric, rivian, r1t`. The listing does not say who made the mesh, what it was made from, or how it was dimensioned. | **Not used.** | **Do not use.** Where the mesh came from is not established. The `forza` tag is the uploader's own tag, the listing does not explain it, and this project did not trace the mesh to any source. The licence label is the uploader's statement, and whether the uploader can grant those rights for this model was not checked. With no stated origin and no dimensional provenance, the project leaves it out. |
| A6 | Sketchfab "Rivian R1S (2022)" by geyges, uid `ec0499cccfa74b52939e1491b2434a71` | sketchfab.com | Sketchfab API, 2026-11-28: licence label "Free Standard", downloadable, 298,611 faces, published 2026-10-12, description "2022 Rivian R1S", tags include `forza`. | Not used. | Do not use, on the same grounds as A5. Its origin is likewise not established. |
| A7 | Sketchfab "Rivian R1T 2022 [Free!]" by 3dblender_1, uid `89ec895feb8145768f93382f356affb5` | sketchfab.com | Sketchfab API, 2026-11-27 and again 2026-11-28: HTTP 404, body `{"detail":"Not found."}`. The public page answered automated requests with an empty HTTP 202, as it did for control URLs, so it shows nothing either way. Why the API no longer serves the model is not established. The project note of 2026-07-28 (`references/visual_reference_sources.md`) recorded the listing as CC BY 4.0. No capture of that listing was kept, so the note cannot be re-checked. | Earlier, a visual proportion cross-check only. It was never committed or redistributed. | **Do not use.** Its current terms could not be read. The 2026-07-28 note is a record of what was read then and must not be taken as a current licence. |
| A8 | Sketchfab interior photogrammetry by acheparev: "Rivian R1T Charging Pad Scan" (`36d35d51942a4e7d8effd7fe02ad0520`) and "Rivian R1T Front Divider Storage Scan" (`55b1874953b14bc89b8344db6eec366a`) | sketchfab.com | Sketchfab API, 2026-11-28: licence label "CC Attribution" on both. | Not used. These are interior parts and say nothing about the exterior or the bed. | Not used and not needed. Whether the uploader's licence label reaches Rivian's design or marks was not examined. |
| A9 | Front Runner FARR001 / RRSTUNI install PDFs | instructions.dometic.com | Manufacturer instructions. Their reuse terms were not read in this pass. | Hardware facts (step 27 and 29 research). | Numbers only. Do not reproduce the documents. |
| A10 | Hum3D / 3DModels.org blueprints | cdn.hum3d.com index | Search of 2026-10-13 (`~/r1t-topper-research/3d-sources.md`), not repeated since: the readable vector index listed a paid Rivian R2 blueprint and no R1T or R1S entry. The 3dmodels.org pages returned HTTP 403. Nothing was purchased. | None. | None available to this project. |
| A11 | TurboSquid, CGTrader, GrabCAD | n/a | Search of 2026-10-13, not repeated since: the TurboSquid search returned HTTP 403, the CGTrader search returned HTTP 202 with an empty body, and site-restricted web searches for all three returned no model listings. | None. | Not established. Their catalogues were not read, so no claim is made about what they hold. |

Outcome: this search found no 3D R1T exterior model with both a stated origin and traceable dimensions, and
none is used. That is a statement about this search, not about what exists. The only truck in the renders is
the project-authored proxy, generated in Blender from published numbers and from coordinates traced off
Rivian line art. Three limits apply, and none of this is a legal opinion: the truck it depicts is Rivian's
design, the traced coordinates derive from Rivian drawings that carry a no-reproduction notice (A1, A2), and
Rivian's names, logos and trade dress are not licensed to this project. No Rivian logo or wordmark is
modelled.

Commercial path, if photoreal marketing imagery is wanted: (a) photograph a real customer or owned truck with
the prototype (step 24 and later), (b) license a model whose listing states where it came from and whose terms
explicitly allow commercial renders, or (c) ask Rivian through the Upfit Program (step 38, optional) for
marketing assets or CAD.

## 2. Dimensions and uncertainty

Published values come from the Upfitting Guide (A1), printed pages 28 to 30. In this file the printed page
number equals the PDF page number. Page 28 holds the overall dimensions, page 29 the tyre size, angles and
ground clearance, and page 30 the storage dimensions. Printed page 27 holds no specification. Values are for
34 in tyres at standard ride height and are recorded in `step27/style/r1t_published_specs_32.json`. Proxy
values are measured on the generated mesh by `blender/s11_truck.py`, and the "Proxy now" column is checked
against the scores of the blender-loop run named in `step27/evidence/step32/EVIDENCE_MANIFEST.json` each time
the manifest is written (`make_manifest.py`).

| Quantity (mm unless stated) | Published | Page | Proxy before (step 30a run S0) | Proxy now | Status / uncertainty |
|---|---|---|---|---|---|
| Overall length | 5514 | 28 | 5318 (-196, -3.6 %) | 5510 (-4) | The front ends at the published overhang. The rear ends where the plan-view outline ends (x 1.560 m), 4 mm short of axle + 1155. |
| Front overhang | 909 | 28 | 817 | 909 | Published x-extent. The bumper's vertical form is unsourced (top z -0.400 m, a visual assumption). |
| Rear overhang | 1155 | 28 | 1052 (traced rear face) | 1151 | Published extent. The plan-view outline ends 99 mm behind the traced rear face (x 1.461 m). The bumper top is unsourced: z -0.545 m, set 20 mm below the lowered tailgate's underside (z -0.525 m), not taken from any source. It was z -0.505 m in the first pin (section 5). **The traced rear face (x 1.461 m) is unchanged.** `params.json` keeps `tailgate_x` 1.441 m for the CAD keep-outs. |
| Approach angle (standard) | 30.4 deg | 29 | not modelled (ad hoc +0.30 m ramp) | 30.40 deg | The underside follows the published line, tangent to the 275/65R20 tyre. The angle is reproduced by construction, not measured from a source drawing. |
| Departure angle (standard) | 25.6 deg | 29 | not modelled (ad hoc +0.25 m ramp) | 25.60 deg | Same as approach. |
| Width without mirrors | 2014 | 28 | 2014 | 2014 | Published. |
| Width with mirrors | 2246 | 28 | no mirrors (clamped out) | 2246 | The x-range is the p.59 plan-view mirror bump (x -2.28 to -2.04 m). Mirror height and shape are unsourced. |
| Wheelbase / track | 3450 / 1730 | 28 | same | same | Published. |
| Tyre | 275/65R20 | 29 | same | same | Published (34 in option). |
| Roof height, no antenna | 1834 | 28 | 1835 | 1835 | Side trace scaled to the wheelbase. Agrees within 0.1 %. |
| Rail height above ground | not published | n/a | 1366 | 1366 | Traced (band 1344-1366). TAPE-REQUIRED (protocol from step 22a). |
| Bed length at rail / width / depth | 1381 / 1299 / 465 | 28 and 30 | same | same | Published (without tonneau). |
| Bed width at wheelhouse | 1277 | 28 | not modelled | not modelled | An 11 mm-per-side wheelhouse step inside the bed. Below render significance, recorded here only. |
| Bed length at floor, tailgate down | 2130 | 30 | not modelled | not modelled | The lowered-gate slab in `s17_access.py` is 525 mm long (bed depth + 60 mm, the length of the step 29 CAD keep-out `truck.tailgate_lowered_keepout`) and ends at x 1.904 m. The CAD keep-out itself sits 59 mm higher (z -0.466 to -0.406 m); the render slab is flush with the bed floor (z -0.525 to -0.465 m). If the published length runs from the bed's inside front wall, a real lowered gate reaches about 0.23 m further. The guide does not draw the datum. The section 5 interference checks cover the slab as modelled, which spans the whole bumper (it ends at x 1.560 m). |
| Ground clearance (standard) | 288 | 29 | sill 341 | sill 341 | The proxy sill is a side-trace value. The guide does not say where its clearance is measured, and the proxy models no underbody below the sill, so the two figures are not comparable. |
| Accessory-port positions | not published (drawn, not dimensioned, p.59) | 59 | from drawing | unchanged | Drawing-derived, P-CAL-02. TAPE-REQUIRED. |

Every value above remains TAPE-REQUIRED before fabrication. The guide gives different heights, angles and
clearances by tyre option and ride height (pp.28-29). The proxy targets the 34 in tyre at standard height.
The guide is the September 2025 edition; the traced line art is from the Model Year 2022-2024 owner's guide.
No dimension was checked against any other model year or against a real truck.

## 3. What changed in the proxy (render lane only)

`blender/s11_truck.py` makes four changes:

1. The loft now runs from `front_axle - 909 mm` to the end of the plan view, not just across the side-trace
   extent. Outside the side trace, a bumper zone takes over. Its x-extent is published, its form is assumed,
   and it follows the plan-view taper in width.
2. In the overhangs the underside is clamped to the published approach and departure lines. Both are tangent
   to the tyre, so the measured angles equal the published ones. This replaces the earlier ad hoc ramps.
3. Mirrors are restored from the plan-view bump and sized to the published 2246 mm width.
4. Lamps and the rear light bar stay on the traced faces (`x_front_tr`, `x_rear_tr`), and the cab back,
   spoiler, rails and bed are untouched. All the datums the topper is checked against stay where they were.
   (Section 5 later lowered the bumper top and made the rear face vertical. Neither is a topper datum.)

The proxy is still a lofted drawing-and-spec body. It is **not a scan and not a calibration**, and it carries no
fitment authority. CAD checks never read it: `step27/cad/truck.py` keep-outs come from `params.json`, which is
unchanged.

## 4. Renders

The renders in `step27/evidence/step32/` show the unchanged authoritative CAD at the base pin. The closed
parts are the STLs that pin's `assembly_step27.step27_assembly(0.0)` exports to `out/parts` (not committed),
and the open-hatch parts are the committed `out/parts_access` STLs. `make_manifest.py` checks every one of
them against the sha256 recorded in the base pin's `out/PROVENANCE.json`. Both sets are imported onto the
revised proxy through the standard render lane (`s12_topper.py`, `s13_hero.py`, `s17_access.py`) with
blender-loop. Blender models no topper geometry. The images, hashes and in-scene scores are listed in
`step27/evidence/step32/EVIDENCE_MANIFEST.json`. They are operator-visual context only. They are not a design
sign-off (21b is Nate-only) and not a fitment approval.

## 5. Revision after verify task 165492 (defect 61514): the lowered tailgate

The first step-32 pin (`8024b241`) failed independent review. In the open-access scene (`s17_access.py`) the
new rear bumper ran through the lowered tailgate: probes through the gate hit `R1T_BODY` at x = 1.484 m and
1.549 m. The old cargo rays missed it. They started behind the interference and only counted topper parts as
blockers. The manifest also hashed the 133-byte Git LFS pointer instead of the STEP payload.

What was wrong, and the fix:

| Cause | Fix |
|---|---|
| The bumper top (`_unsourced_form.rear_bumper_top_z = -0.505`) sat inside the folded slab (z -0.525..-0.465). | Now `-0.545`: bed floor 0.465 + gate 0.060 + 20 mm clearance. `s11_truck.py` asserts the bound, so a later form tweak cannot re-enter the gate. |
| The loft ramped from the tailgate top down to the bumper across one 30 mm station bay behind the tailgate face. | `s11_truck.py` adds stations at `x_rear_tr` and `x_rear_tr + 2 mm`, so the tailgate face is vertical. |
| `s17_access.py` cut the gate block only to `params.tailgate_x` (1.441). The traced face S11 lofts is at 1.461, which left an 18 mm wall across the doorway. The cut also stopped at z -0.477, inside the slab. The bed's end wall was a sloped loft bay before `bed_len`. | Two cuts: above the floor from `bed_len - 54 mm` to the traced face (`R1T_BODY["TAILGATE_FACE_X"]`), and below the floor through the slab plus 20 mm. The rear light bar (mounted on the gate) leaves with the gate. |
| The checks did not cover the whole path. | `s17_access.py` now measures: (1) 33 rays along +x from the front of the bed to the end of the lowered gate, with every truck and topper mesh counted as a blocker; (2) 240 vertical probes on a 25 x 100 mm grid with the gate and cargo hidden, where the first surface each probe meets must be at least 10 mm below the gate's underside; (3) a BVH overlap of the gate (0.5 mm inset, so the hinge contact at the bed end is not counted) against every mesh. |
| The manifest hashed the LFS pointer. | `evidence/step32/make_manifest.py` hashes the payload. For an LFS file it records the payload sha256 and size, and checks them against the pointer oid; the pointer hash is kept as a separate field. |

The same new checks were also run against the parent proxy (blender-loop run `r1t-task165497-cf`):
**12/33** path rays clear, **47/240** probes bad (bumper top found at z -0.505), and 71 gate/body
overlapping faces. They reproduce the reviewer's finding. On the revised proxy the result is **33/33**,
**0/240** and **0** overlaps, with 20.0 mm of clearance under the gate. Overall length, overhangs,
approach/departure angles, mirror width and every topper datum are unchanged from `8024b241`.

## 6. Revision after verify task 165502 (defect 61514): this record

The second pin (`2a282d69`) passed the proxy and render checks and failed on this document. Nothing in the
geometry was wrong. The record stated more than had been observed, and it had not been brought up to date
with the section 5 fix.

| What the record said | What was actually observed | Now |
|---|---|---|
| A5/A6: "The `forza` tag points to a mesh taken from a video game." | A tag on the listing. Nothing traced the mesh to any source. | The row reports the tag and says the origin is not established. The assets stay excluded because the listing states no origin and no dimensional provenance. |
| A7: "The model has been withdrawn." | The API returned HTTP 404. | The row reports the 404 and says the reason is not established. `references/visual_reference_sources.md` is corrected the same way. |
| Commercial path: "(no game rips)". | No such origin was established for any asset. | Removed. The path now asks for a listing that states its origin. |
| A1: "No licence grant to reproduce found." | The guide carries an explicit no-reproduction notice on p.2. So do both owner's guides. | The notice is quoted in A1 to A3, and the status of the traced coordinates is recorded as an open question for counsel. |
| A4: "Each one already reads 'remote reference only; Rivian copyright'." | Five of the six entries read that. The sixth is operator-supplied screenshots with a different note. | The row describes all six. |
| Section 2: bumper top "z -0.505 m, about the tailgate bottom". | The pinned geometry and section 5 use z -0.545 m. | Corrected, with the basis of the value. |
| Section 2: values cited to "pp.27-28". | Page 27 holds no specification. Overall dimensions are on p.28. The angles, tyre size and ground clearance are on p.29. | Each row carries its page. `r1t_published_specs_32.json` and the `s11_truck.py` docstring are corrected. |
| Section 2: bumper "about 120 mm behind the tailgate face". | The outline ends 99 mm behind the traced rear face (1.560 - 1.461 m). 119 mm is the distance from `params.tailgate_x`. | Corrected. |
| Section 2: mirror bump "about x -2.26 to -2.06". | The outline points used are at x -2.28 to -2.04 m. | Corrected. |
| Section 2: "Gen-2 R1T is reported to look similar on the outside." | No source was read for it. | Removed. |
| A8 "could be used with attribution", A9 "no reuse licence", A11 "blocked (403/202)", and the ground-clearance row's "to the lowest underbody point". | None of these was read from its source in that form. | Each row now states only what was read, and says what was not. |
| Section 2 had no row for the published tailgate-down bed length. | The guide gives 2130 mm (p.30). The modelled gate slab is shorter. | Row added as a stated limitation. |

To stop the dimension table drifting again, `evidence/step32/make_manifest.py` now compares the "Proxy now"
figures in section 2 with the run's measured scores and refuses to write the manifest if they differ. It
also hashes this document and `source_observations.json`, and checks the closed-part STLs against the base
pin's `out/PROVENANCE.json`.

Geometry is unchanged from `2a282d69`. In `s11_truck.py` only a page reference in the docstring changed, and
in `r1t_published_specs_32.json` only the page fields. Because both files are hashed render inputs, the
renders were regenerated from the corrected files rather than carried over (run named in the manifest).
