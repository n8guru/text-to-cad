# Visual silhouette references

These sources inform the editable Phase 2 silhouette station table. They do
not establish mounting, clearance, or production body geometry.

- Five operator-supplied R1S screenshots dated 2026-07-27, including direct
  side, front, and rear views plus rear three-quarter views. These are the
  primary references for the nearly level longitudinal roofline, parallel roof
  edges, shallow crown, rounded upper corners, and localized rear-corner taper.
- Rivian, *R1T Owner's Guide, Model Year 2022–2024*, exterior and truck-bed
  overview illustrations:
  <https://assets.rivian.com/2md5qhoeajym/530xs9hu11xOKefT2JrvA5/46f6cb5d5756b8320d3eb494a902e66c/r1t-og-en-us-20240527.pdf>
- Rivian model comparison, used for published overall and cargo-bed dimensions:
  <https://rivian.com/en-CA/compare>
- “Rivian R1T 2022 [Free!]” by 3dblender_1, Sketchfab model
  `89ec895feb8145768f93382f356affb5`, 308,001 triangles, licensed CC BY 4.0:
  <https://sketchfab.com/3d-models/rivian-r1t-2022-free-89ec895feb8145768f93382f356affb5>

The screenshots are perspective images, and the Sketchfab asset is an artist
mesh rather than a scan or manufacturer CAD model. Neither can establish
dimensions or fit. The artist mesh is used only as a visual proportion
cross-check and is not redistributed in this repository. A later vehicle scan
should replace the numeric section rows in `cad/parameters.py` while preserving
the loft and assembly workflow.

The Step 4 reproducible source manifest and normalized multi-view annotations
are in `photo_reconstruction/`. That package adds official R1S owner-guide
front/rear and side illustrations, official R1T rear/bed context, and an
official Rivian three-quarter R1S photograph. Source rasters remain remote;
only their URLs, fingerprints, normalized annotations, and project-authored
linework are checked in. Perspective observations are qualitative and are
never used for direct metric inference.
