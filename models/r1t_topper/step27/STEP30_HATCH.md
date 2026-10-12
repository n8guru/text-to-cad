# Step 30 — true tailgate-width lower hatch chord
Decision2154445, task147368 attempt1, 2026-10-12. Design-source only.

## Authoritative change
The actual carbon leaf has a **1299 mm straight bottom edge**, not merely a
1299 mm nominal or bounding-box width. Its upper width budget remains1052 mm;
the upper corners stay rounded and the two existing inside-glazed panes/mullion
remain. The lower corners are square in this design-intent revision so the
bottom chord reaches the named datum rather than curving inward. Edge finishing,
local stress, seal corner treatment and fabrication remain later qualification.

The 1299 mm datum is `geom.TAILGATE_WIDTH_ESTIMATE_MM`: the existing published
bed-width anchor is used as a **tailgate-width estimate**, not a published
tailgate measurement or a physical calibration. The inherited reference record cites
[Rivian Upfitting Guide, September2025, p.28](https://assets.ctfassets.net/2md5qhoeajym/5ysf6K5UtGtHedY1fMeClC/b83307f7e8f03838a1906bff88707f95/r1t-upfitting-guide-en-us-20250924.pdf)
for bed width1299 mm. This pass reuses that pinned source record; it did not remeasure a vehicle. It is traceable to
`blender/params.json truck.bed_w` and the existing Rivian reference record.
The aperture bottom is1247 mm before its frame offsets; the leaf overhang is26 mm
per side. The matching shell cut and open-bottom surround flare with the leaf.

The bulb seal follows a tangent-continuous **open-bottom U path**: a closed sweep
through the square lower corners is invalid in OCCT. The seal is explicitly checked
for validity, bounded volume/height and absence from the removed bottom run.
The old fixed bottom crossbar is still absent. Strut frame studs retain their
previous solved positions; 6 mm bracket reach webs join their support to the
widened side return behind the leaf. Moving only the bracket to the new side
without moving the stud would create disconnected evidence, so that is not done.
The existing hinge/strut/load assumptions remain provisional.

## Acceptance checks
`cad/checks_step30_hatch_width.py` intersects the real leaf with a **0.01 mm slice
at its actual lower edge**, then requires agreement with the1299 mm datum within
0.1 mm. It measures the matching shell-cut chord, checks the upper width budget,
valid single-solid leaf and surround, and sweeps the widened leaf against the
shell, dry surround and lowered-gate keepout. Full assembly checks add hardware,
truck and rear-access regressions. This is nominal CAD clearance, not real fit.

An intermediate rounded-all-corners proposal was rejected: its nominal width
looked right but its bottom chord was only about1092 mm. A250 mm test tolerance
would have hidden that failure. Neither the narrow chord nor that test is the
submitted design.

## Drawings and visual evidence
Regenerated DWG-27-011 labels the actual bottom datum. All assembly STEP/STL and
sections are regenerated from the same source. Purpose-framed rear and open-access
renders show those exported solids on the existing approximate truck proxy.
Improved truck reconstruction is separately authorized step32, and no photoreal
or physical-scan accuracy is claimed for this inherited proxy.
