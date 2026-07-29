# R1T modular topper digital prototype

This directory contains a source-controlled, STEP-first build123d engineering
prototype. Step 7 derives three sectional shell pieces and a common modular
side-panel system from the verified Step 6 provisional authoritative sandwich
shell, alongside nonproprietary vehicle reference envelopes. It is not
production-ready, structurally validated, sealed, or fitment-trustworthy.

## Regenerate

Create the repository CAD environment per `CONTRIBUTING.md`, then run from this
directory:

```bash
../../.venv/bin/python cad/exports.py
```

The script generates:

- `outputs/step/R1T_TOPPER_ASSEMBLY.step`
- hidden adjacent CAD Viewer GLB/topology sidecars
- stable orthographic and three-quarter PNGs under `outputs/renders/`

Run the Checkpoint 1 source checks with:

```bash
../../.venv/bin/python cad/checkpoint1_checks.py
```

Run the Phase 2 concept-envelope checks with:

```bash
../../.venv/bin/python cad/phase2_checks.py
```

Run the Step 6 engineered-shell checks with:

```bash
../../.venv/bin/python cad/step6_checks.py
```

Run the Step 7 sectional/module checks with:

```bash
../../.venv/bin/python cad/step7_checks.py
```

## Parameter provenance

Every major dimension is a `Parameter` in `cad/parameters.py` with one of:
`MEASURED`, `MANUFACTURER REFERENCE`, `ESTIMATED`, `DESIGN DECISION`, or
`PLACEHOLDER REQUIRING SCAN`.

Checkpoint 1 targets a 2022 Gen 1 R1T. It contains three
manufacturer-reference bed-envelope values: length, exposed cargo width, and
maximum bed height. They are corroborated where possible by Rivian's 2022
material, but come from the September 2025 R1T Upfitting Guide and must be
checked on the target vehicle during the late bounded calibration pass. Rail,
cab, port, control, and swept-envelope geometry remains provisional.
Calibration must update affected parameter records and provenance, regenerate
the design, and revalidate every downstream artifact before fabrication
release.

## Known limitations

See `reports/OPEN_ITEMS.md` and `references/measurement_requirements.md`.
The cab is a block envelope and vehicle interfaces are placeholders. The blue
topper is a provisional `22 mm` sandwich shell, with labeled datums, base
flanges, keep-outs, and transverse load-path bands. Step 7 divides that shell
into three sub-`600 mm` X-length sections using two `4 mm` assembly gaps,
`80 × 4 mm` internal splice-doubler envelopes, and provisional alignment keys.
It cuts three `285 × 420 mm` openings per side and installs six identical
common-interface frames plus swappable solid, window, mesh, recovery-board,
and utility cartridges. Those controls define downstream CAD intent but do not
prove joint capacity, fit, sealing, laminate schedule, hardware selection, or
tooling. No hatch mechanism, rated structure, vehicle mounting geometry,
weather seal, or tooling exists yet.

The concept footprint covers the full provisional bed-plus-tailgate top plane:
`X=0..1462 mm` and `Y=-865..865 mm`. Its rear face shares the provisional
tailgate outer plane. These are editable layout decisions, not measured
fitment, contact, or sealing geometry.

The R1S-like visual surrogate is driven by five editable cross-sections in
`cad/parameters.py`. See `references/visual_reference_sources.md` for the
operator-supplied R1S screenshots, official imagery, and CC-BY artist mesh used
only as proportion references. Replace those section rows with
late hard-measurement calibration inputs; the loft, assembly, export, and
validation workflow can remain unchanged.

For aesthetic work in Blender, follow
`references/BLENDER_CAD_HANDOFF.md`. Blender is styling/visual-envelope
authoring only; the CAD datum, interfaces, engineered geometry, STEP, and
validation remain authoritative.

The reproducible multi-view visual target package lives under
`references/photo_reconstruction/`. It records official Rivian source URLs and
fingerprints, normalized landmarks, uncertainty, perspective exclusions, and
bounded silhouette targets without redistributing the source rasters. Its
generated linework lives under `outputs/reference/photo_reconstruction/`.
The selected Step 5 aesthetic proposal is
`interchange/reference_only/blender_to_cad_style_selected.json`: five sparse
editable sections and five longitudinal character lines, all still
`ESTIMATED`. The deterministic comparison evidence beside the Step 4 outputs
shows every selected ratio inside its target band. Step 6 rebuilds those curves
as authoritative CAD while retaining `ESTIMATED` shape provenance; it does not
promote any image-derived ratio to measured geometry.

## CAD Explorer / CAD Viewer

Start CAD Viewer with the repository's `cad-viewer` skill and use the repository
`models/` directory as `?dir=`. Select
`r1t_topper/outputs/step/R1T_TOPPER_ASSEMBLY.step`.

Stable follow-up references use the selector tokens returned by:

```bash
../../.venv/bin/python ../../skills/cad/scripts/inspect refs \
  outputs/step/R1T_TOPPER_ASSEMBLY.step --facts --planes --positioning
```

Selector tokens are local to this STEP file and should be paired with its
viewer link in revision requests.
