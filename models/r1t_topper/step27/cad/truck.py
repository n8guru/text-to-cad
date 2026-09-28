"""R1T reference keep-outs for the topper checks (00_REFERENCE, not product geometry).

Built only from the Rivian-measured numbers in ``blender/params.json`` (truck block; provenance in
``step27/style/rivian_reference.json``). Every number here is TAPE-REQUIRED before fabrication:
the checks prove the topper clears these envelopes, not that the envelopes are the truck.

  cab       cab back under the roof spoiler, the spoiler, and the cab roof, across the cab width
  body      everything below the bed-rail top plane outside the bed opening (rail caps, sides)
  tailgate  the tailgate shell below the rail plane, behind the bed
"""
from __future__ import annotations

from build123d import Align, Box, Plane, Polygon, Pos, extrude

import geom as G

CC, CMIN, CMAX = Align.CENTER, Align.MIN, Align.MAX
T = G.T
CAB_HALF_W = 800.0        # cab greenhouse half-width at the rail (rear view 0.81 x body half)


def cab_keepout():
    pts = [(-1500.0, 0.0)] + [tuple(p) for p in T["cab_back"]] + [
        tuple(T["spoiler_tip"]), tuple(T["spoiler_root"]),
        (-1500.0, T["cab_roof_max_z"])]
    return extrude(Plane.XZ * Polygon(*pts, align=None), amount=CAB_HALF_W, both=True)


def body_keepout():
    """Below the rail plane, outside the bed opening and the tailgate: the OEM body."""
    L = 3000.0
    blk = Pos(T["bed_len"] / 2, 0, -1) * Box(L, 2 * T["body_width"] / 2, 400.0, align=(CC, CC, CMAX))
    bed = Pos(T["bed_len"] / 2, 0, 0) * Box(T["bed_len"], T["bed_w"], 1000.0, align=(CC, CC, CMAX))
    return blk - bed


def tailgate_keepout():
    t = 60.0
    return Pos(T["tailgate_x"] - t / 2, 0, -1) * Box(t, T["bed_w"], T["bed_depth"],
                                                     align=(CC, CC, CMAX))


def port_holes():
    """The OEM bed accessory ports: where the topper is ALLOWED below the rail plane."""
    from build123d import Cylinder
    out = []
    for x, y in T["bed_ports"]:
        for sy in (-1, 1):
            out.append(Pos(x, sy * y, 0) * Cylinder(16.0, 60.0, align=(CC, CC, CMAX)))
    return out
