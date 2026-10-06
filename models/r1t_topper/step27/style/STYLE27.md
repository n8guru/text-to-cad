# Step 27 styling pass — R1T/R1S, measured from Rivian's own line art

Status: **a sourced styling pass on drawing-derived truck geometry. Not a fit, not a sign-off.**
Every truck number below is measured from Rivian illustrations and must be confirmed with a tape
(or the Gaussian-splat capture Nate proposed, Studio 75072) before any tooling.

## 1. Sources (fetched, SHA-256 verified, not redistributed)

| Id | Document | Pages used | SHA-256 |
|---|---|---|---|
| R1T_OG | R1T Owner's Guide MY2022-24 v2024.19 | p.14 rear view, p.16 bed, p.17 driver side | `e6c54434…75b6` |
| R1S_OG | R1S Owner's Guide MY2022-24 v2024.27 | p.14 rear view, p.16 driver side | `27eda35d…7061` |
| R1T_UPFIT | R1T Upfitting Guide 2025-09-24 | pp.28-30 dimension tables, p.59 plan view | `847d036f…552a` |
| wheelbase | rivian.com support "What is the wheelbase length?" | R1S 121.1 in, R1T 135.8 in | — |
| R1S length | stories.rivian.com "Sizing up the R1S" | 200.8 in | — |

URLs are in `rivian_reference.json` (`_sources`). `rivian_reference.py` downloads to a cache
outside the repo, refuses any source whose hash changed, renders the pages with `pdftoppm`, and
writes only derived numbers. Rivian rasters are never committed.

## 2. Method and how good the numbers are

Each view is scaled by a **published** dimension and cross-checked against a second one:

| View | Scale anchor | Cross-check | Result |
|---|---|---|---|
| R1T side | wheelbase 3,450 mm (tyre circles fitted to 0.5 px) | published roof 1,834 mm | **1,834.7 mm (0.04 %)** |
| R1T side | — | overall length 5,514 | 5,318 (−3.6 %: illustration shortens the overhangs) |
| R1T rear | outer tyre edges 1,730 + 275 | body width 2,014 | 2,015 |
| R1T plan | length 5,514 | bed inside length 1,381 | 1,364 (−1.2 %) |
| R1S side | wheelbase 3,076 | length 5,100 | 4,975 (−2.5 %) |

Heights come from the side view (its scale is validated by the roof height). Angles and ratios are
scale-free. Where two views measure the same thing they are both reported.

## 3. The R1T, as Rivian draws it — and what the previous pass had wrong

| Quantity (bed frame: x from the bed's inside front wall, z from the rail top) | Rivian line art | Previous `params.json` |
|---|---|---|
| Rail top above ground | **1,366 mm** side view; 1,344 mm rear view (band) | 1,185 mm ("derived ±40", never measured) |
| Cab roof above rail (topper roof target) | **463–469 mm** | 649 mm |
| Cab back, at the rail / 360 mm up | **x = −150 / −180 mm**, top leaning forward 5.6° | x = −480 mm |
| Roof spoiler tip | **x = −132 mm, z = +427** (side view); x = −127 (plan view) | not modelled |
| Rail cap: inner edge / flat / outer edge (half-width) | 644 / 783 / 828 mm (plan view) | outer 850 mm |

Two consequences, both found by measuring rather than assuming:

1. **The old shell overlapped the real cab by ~300 mm.** It started at x = −460 because the plan
   view's roof-glass trailing edge (x ≈ −480) had been read as the cab back. On Rivian's own plan
   and side views the roof continues behind the glass to a spoiler at x ≈ −130, and the cab back is
   150–180 mm ahead of the bed.
2. **The old shell stood ~180 mm above the cab roof** (640 mm above a rail placed 180 mm too low).
   The proxy truck used the same numbers, so every previous render looked blended while describing
   a topper that could not match the R1S profile on a real R1T. That is the structural reason the
   earlier styling "did not blend".

## 4. R1S / R1T style targets (measured) and what the shell does

| Target | Measured on Rivian art | Styled shell | Check |
|---|---|---|---|
| Roofline continues the cab roof | R1T cab roof 463–469 above rail | crown top **462** | `roof_meets_cab_roof` |
| Roof level to the rear | R1S rear roof slope −0.57 % | level (prismatic) | `roof_level_like_r1s` |
| Greenhouse tumblehome | R1T C-pillar **21.8°**, R1S D-pillar **20.1°** | flat land at **21.0°** | `tumblehome_matches_r1t_r1s` |
| Rear face rake | R1S liftgate **15.2°** | **15.0°** | `rear_rake_matches_r1s_liftgate` |
| Rear roof roll-off | R1S drops 0.215 of the greenhouse | R100 roll: 0.16 | `rear_corner_roll_off_r1s_like` |
| Base width | cab greenhouse at the rail 0.81 × body half; rail cap to 828 | skin at **805** | `base_lands_on_rail_cap` |
| Side DLO proportion | R1S DLO **0.83** of the greenhouse | dark band 0.63 | `side_dlo_band_vs_r1s` |
| Carbon between openings | operator ≥ 76 mm (Studio 41645) | **77 mm** | `carbon_bridge_between_openings_ge_76` |
| Cab-to-topper transition | spoiler tip x −132 | front face x −100, R50 roll: **32 mm** behind the tip, ≥ 20 everywhere | `cab_gap_ge_20mm` |

The shell is one styled section (flat 21° land → R100 shoulder tangent to a shallow crown), a
vertical front face tucked behind the spoiler, and a 15° raked rear face. The flat land and the
flat raked face are deliberate: every socket and hatch bond flange sits on them, and
`bond_flanges_seat_on_flat_skin` proves it at every sampled station.

### Deliberate deviations, stated

* **Rear roll-off is tighter than the R1S** (R100, 0.16 vs 0.21 of the greenhouse): the flat raked
  face has to carry the whole hatch frame. A liftgate-style leaf that wraps the roll-off would
  match the R1S better and is the next styling lever.
* **Side DLO band is 0.63 of the greenhouse vs the R1S 0.83.** The limit is the socket interface
  border (82 mm per side from aperture to bond-flange edge), not the surface. A slimmer border or a
  flush-glazed WINDOW module is the lever if Nate wants the R1S glass proportion.
* **Front face is vertical**, not parallel to the forward-leaning cab back: parallel would put the
  roof's leading edge inside the spoiler.

## 5. What the real-truck geometry did to the interfaces

A cab-height shell behind the real cab has a flat side land ~1.33 m long and ~380 mm tall, and a
flat rear face ~0.41 m tall. The engineered interfaces were kept as designs and re-dimensioned to
fit, then re-verified:

* Sockets: two per side, aperture **470 × 208** (was 640 × 353) on a tightened border.
* Hatch: aperture **1,000 × 226** (was 1,280 × 412), 3.28 kg leaf, struts re-selected from the
  Stabilus table (6462II, 50 N) — the old 150 N strut would have been ~3× over-sprung.
  **Superseded in Step 29 (task 139737, Nate's change request on card 2081357):** the slot started
  100 mm above the rail with a fixed ~74 mm band under it, which is the "crossbar where there should
  be none". The aperture is now **1,000 × 292** with its lower edge 34 mm up the face (leaf lower
  edge 1 mm above the rail-cap plane), the surround's bottom run is removed between two corner
  stubs, and the leaf is 3.75 kg on 6467IK struts. See `REVISION29.md`.

## 6. Not done here, and why

* **Exact profile of Nate's own truck.** Drawing-derived numbers carry a ~±35 mm band on rail
  height and similar on the cab line. The Gaussian-splat capture from Nate's video (Studio 75072) or
  a tape session is required; it needs Nate's footage or his truck.
* R1S-style liftgate leaf, flush-glazed modules: styling levers named above, not built.
