# Step 32: R1T reference assets, rights, dimensions and the improved truck proxy

Ledger: project 924515 (r1t-topper), step 32, task 165486. Decision 2154445 asks for a web search for usable
Rivian R1T assets and a better estimate of the truck's size and shape for rendering.

What this step is: a rights and provenance record for every truck reference the render lane touches, plus a
render-lane accuracy pass on the truck proxy. What it is not: a scan, a measurement of any real truck, a
calibration, a fitment approval, or legal advice. It changes no topper CAD. `blender/params.json`,
`step27/style/rivian_reference.json` and every `step27/cad/*.py` module are byte-identical to the base pin
`0bb4c68121eb6974c6f739c8db10159f3394a967` (the step 30a seal-repair revision, which carries 29 + 30). The
truck values the CAD checks use are therefore unchanged.

## 1. Reference assets and rights

"Use" means how this project uses the asset today. "Rights basis" records only what the source itself
states. None of the rows below are a legal opinion. Anything going into commercial marketing (the product is
commercial, built at CubCrafters, insight 83761) needs review by counsel first. Step 34 already includes a
light Rivian trademark/naming check.

| # | Asset | Where | Stated terms (as read 2026-11-27) | Use in this project | Commercial-render status |
|---|---|---|---|---|---|
| A1 | Rivian R1T Upfitting Guide, Sept 2025 (130 pp) | `assets.ctfassets.net/.../r1t-upfitting-guide-en-us-20250924.pdf`, sha256 `847d036f…552a` | Rivian publication, publicly hosted. No licence grant to reproduce found. | Numeric specs (pp.27-28) and the plan-view outline (p.59) traced into numbers. The PDF and page rasters are not committed. | Facts (dimensions) only. Do not reproduce its pages or drawings in marketing. |
| A2 | Rivian R1T Owner's Guide MY2022-24 | `assets.rivian.com/.../r1t-og-en-us-20240527.pdf`, sha256 `e6c54434…75b6` | Rivian copyright. No reuse licence. | Side and rear line art traced into the numeric silhouette (`rivian_reference.json`). The rasters are not committed. | Reference only. Derived numbers are used, the artwork is not. |
| A3 | Rivian R1S Owner's Guide | `assets.rivian.com/.../r1s-og-en-us-20240722.pdf`, sha256 `27eda35d…7061` | Rivian copyright. | R1S style targets for the topper (lean/rake). | Reference only. |
| A4 | Official Rivian photos and illustrations in `references/photo_reconstruction/sources.json` | rivian.com / Rivian guides | Each one already reads "remote reference only; Rivian copyright". | Qualitative silhouette observations. Fingerprints only, no committed rasters. | Not usable in marketing. |
| A5 | Sketchfab "Rivian R1T (2022)" by geyges, uid `6eca29c11ca44840baf93f47ef800006` | sketchfab.com | API (re-read 2026-11-27): licence label "Free Standard", downloadable, 394,462 faces, published 2026-10-12, tags include **`forza`**. Description is only "2022 Rivian R1T". | **Not used.** | **Do not use.** The `forza` tag points to a mesh taken from a video game. The uploader may not hold the rights it licenses, and the listing gives no dimensional provenance. |
| A6 | Sketchfab "Rivian R1S (2022)" by geyges, uid `ec0499cccfa74b52939e1491b2434a71` | sketchfab.com | Same as A5 ("Free Standard", `forza` tag). | Not used. | Do not use, for the same reason. |
| A7 | Sketchfab "Rivian R1T 2022 [Free!]" by 3dblender_1, uid `89ec895feb8145768f93382f356affb5` | sketchfab.com | `references/visual_reference_sources.md` recorded it as CC BY 4.0. **The API now returns 404** (2026-11-27). The model has been withdrawn, and its current terms cannot be checked. | Earlier, a visual proportion cross-check only. It was never committed or redistributed. | **Do not use.** Earlier notes must not be read as a current licence. |
| A8 | Sketchfab interior photogrammetry by acheparev (charging pad `36d35d51…`, front divider `55b18749…`) | sketchfab.com | Licence label "CC Attribution". | Not used. These are interior parts and say nothing about the exterior or the bed. | Could be used with attribution under the stated CC licence, but they are irrelevant to the topper. Rivian marks are not covered by that licence. |
| A9 | Front Runner FARR001 / RRSTUNI install PDFs | instructions.dometic.com | Manufacturer documents. No reuse licence. | Hardware facts (step 27/29 research). | Facts only. |
| A10 | Hum3D / 3DModels.org blueprints | cdn.hum3d.com index | Paid. The readable index lists an R2 only. Not purchased. | None. | Not available. |
| A11 | TurboSquid, CGTrader, GrabCAD | n/a | Automated access was blocked (403/202) in the 2026-10-13 search (`~/r1t-topper-research/3d-sources.md`). | None. | Unknown. Not checked, so no claim is made either way. |

Outcome: no licensed, dimensionally traceable 3D R1T exterior model was found, and none is used. The only truck
in the renders is the project-authored proxy, generated in Blender from published numbers and traced Rivian
line art. That proxy is the project's own work. Two limits still apply, and none of this is a legal opinion:
the truck it depicts is Rivian's design, and Rivian's names, logos and trade dress are not licensed to this
project. No Rivian logo or wordmark is modelled.

Commercial path, if photoreal marketing imagery is wanted: (a) photograph a real customer or owned truck with
the prototype (step 24 and later), (b) license a model under terms that explicitly allow commercial
renders, checking where it came from (no game rips), or (c) ask Rivian through the Upfit Program (step 38,
optional) for marketing assets or CAD.

## 2. Dimensions and uncertainty

Published values come from the Upfitting Guide (A1) pp.27-28 for 34 in tyres at standard ride height, and are
recorded in `step27/style/r1t_published_specs_32.json`. Proxy values are measured on the generated mesh by
`blender/s11_truck.py` (blender-loop run `r1t-task165486`, step `S0_truck_published`).

| Quantity | Published | Proxy before (step 30a run S0) | Proxy now | Status / uncertainty |
|---|---|---|---|---|
| Overall length | 5514 | 5318 (-196, -3.6 %) | 5510 (-4) | Front ends at the published overhang. The rear ends at the plan-view outline (1560), 4 mm short of axle + 1155. |
| Front overhang | 909 | 817 | 909 | Published x-extent. The bumper's vertical form is unsourced (top z -0.40 m, visual assumption). |
| Rear overhang | 1155 | 1052 (tailgate face) | 1151 | Published extent, with Rivian's plan view showing a bumper about 120 mm behind the tailgate face. The bumper top (z -0.505 m, about the tailgate bottom) is unsourced. **The tailgate face (x 1.461) is unchanged.** |
| Approach angle (std) | 30.4 deg | not modelled (ad hoc +0.30 m ramp) | 30.40 deg | The underside follows the published line tangent to the 275/65R20 tyre. |
| Departure angle (std) | 25.6 deg | not modelled (ad hoc +0.25 m ramp) | 25.60 deg | Same as approach. |
| Width without mirrors | 2014 | 2014 | 2014 | Published. |
| Width with mirrors | 2246 | no mirrors (clamped out) | 2246 | The x-range is the p.59 plan-view mirror bump (about x -2.26 to -2.06). Mirror height and shape are unsourced. |
| Wheelbase / track / tyre | 3450 / 1730 / 275/65R20 | same | same | Published. |
| Roof height, no antenna | 1834 | 1835 | 1835 | Side trace scaled to the wheelbase. Agrees within 0.1 %. |
| Rail height above ground | not published | 1366 | 1366 | Traced (band 1344-1366). TAPE-REQUIRED (protocol from step 22a). |
| Bed length / width / depth | 1381 / 1299 / 465 | same | same | Published. |
| Bed width at wheelhouse | 1277 | not modelled | not modelled | An 11 mm-per-side wheelhouse step inside the bed. Below render significance, recorded here only. |
| Ground clearance (std) | 288 | sill 341 | sill 341 | The proxy sill is a side-trace value. Published clearance is to the lowest underbody point, which the proxy does not model. |
| Accessory-port positions | not published (drawn, not dimensioned, p.59) | from drawing | unchanged | Drawing-derived, P-CAL-02. TAPE-REQUIRED. |

Every value above remains TAPE-REQUIRED before fabrication. Published nominal values vary with ride height, tyre
option and model year. The proxy targets Gen-1 R1T on 34 in tyres at standard height. Gen-2 R1T is reported to
look similar on the outside, but none of its dimensions were checked here.

## 3. What changed in the proxy (render lane only)

`blender/s11_truck.py` makes four changes:

1. The loft now runs from `front_axle - 909 mm` to the end of the plan view, not just across the side-trace
   extent. Outside the side trace, a bumper zone takes over. Its x-extent is published, its form is assumed,
   and it follows the plan-view taper in width.
2. In the overhangs the underside is clamped to the published approach and departure lines. Both are tangent
   to the tyre, so the measured angles equal the published ones. This replaces the earlier ad hoc ramps.
3. Mirrors are restored from the plan-view bump and sized to the published 2246 mm width.
4. Lamps and the rear light bar stay on the traced faces (`x_front_tr`, `x_rear_tr`), and the cab back,
   spoiler, rails, bed and tailgate are untouched. All the datums the topper is checked against stay where they were.

The proxy is still a lofted drawing-and-spec body. It is **not a scan and not a calibration**, and it carries no
fitment authority. CAD checks never read it: `step27/cad/truck.py` keep-outs come from `params.json`, which is
unchanged.

## 4. Renders

The renders in `step27/evidence/step32/` show the unchanged authoritative CAD at the base pin. The closed
parts were regenerated from that pin's `assembly_step27.step27_assembly(0.0)`, and the open-hatch parts are
the committed `out/parts_access` STLs. Both are imported onto the revised proxy through the standard render
lane (`s12_topper.py`, `s13_hero.py`, `s17_access.py`) with blender-loop. Blender models no topper geometry. The
images, hashes and in-scene scores are listed in `step27/evidence/step32/EVIDENCE_MANIFEST.json`. They are
operator-visual context only. They are not a design sign-off (21b is Nate-only) and not a fitment approval.
