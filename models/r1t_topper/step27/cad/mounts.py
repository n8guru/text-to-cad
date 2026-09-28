"""Topper-to-truck mounting: base rails, bed-port adapters, OEM control-well cut-outs.

The shell's foot sits on the OEM bed-rail caps (z = 0). A 6061 base rail runs along each foot and
is bolted to Rivian's own bed accessory ports (Upfitting Guide p.59: 2 per side, 2,500 N each),
through an adapter whose lower half is Rivian's proprietary port interface (not published: G7).

OEM controls on the rail caps (TAILGATE_CONTROL.md) must stay pressable, so the foot and the rail
are cut through over each button. Positions are PROVISIONAL until taped (T1-T3).
"""
from __future__ import annotations

from build123d import Align, Box, Cylinder, Pos

import geom as G

CC, CMIN, CMAX = Align.CENTER, Align.MIN, Align.MAX
BR = G.BR
T = G.T
RAIL_X = (G.S["x0"] + 60.0, G.S["x1"] - 130.0)   # clear of the front roll and rear wrap
# flange clamps the base rail; Dia 46 stays on the 75 mm rail (a Dia 56 overhung its outer edge
# into the socket frames' lower bond flange)
ADAPTER = {"shank_d": 30.0, "flange_d": 46.0, "flange_t": 4.0, "below": 25.0}
# (name, x, side) - side +1 = driver (+Y). Well clear opening 120 x 70 (DWG-27-009).
WELLS = (("WELL_GT_L", 60.0, 1), ("WELL_GT_R", 60.0, -1), ("WELL_TG", 1300.0, 1))
WELL = {"lx": 120.0, "ly": 70.0, "y": 700.0}


def _rail_solid(sy):
    y0, y1 = BR["y_in"], BR["y_out"]
    return Pos((RAIL_X[0] + RAIL_X[1]) / 2, sy * (y0 + y1) / 2, G.WALL) * Box(
        RAIL_X[1] - RAIL_X[0], y1 - y0, BR["h"], align=(CC, CC, CMIN))


def well_cut(x, sy):
    return Pos(x, sy * WELL["y"], -1.0) * Box(WELL["lx"], WELL["ly"], G.WALL + BR["h"] + 10.0,
                                             align=(CC, CC, CMIN))


def adapter_hole(x, y):
    return Pos(x, y, -1.0) * Cylinder(ADAPTER["shank_d"] / 2 + 0.5, G.WALL + BR["h"] + 10.0,
                                      align=(CC, CC, CMIN))


def base_rails():
    out = []
    for sy in (-1, 1):
        r = _rail_solid(sy)
        for x, y in T["bed_ports"]:
            r -= adapter_hole(x, sy * y)
        for _, x, side in WELLS:
            if side == sy:
                r -= well_cut(x, sy)
        r.label = f"BASE_RAIL_6061_{'L' if sy > 0 else 'R'}"
        out.append(r)
    return out


def port_adapters():
    out = []
    top = G.WALL + BR["h"]
    for x, y in T["bed_ports"]:
        for sy in (-1, 1):
            a = Pos(x, sy * y, -ADAPTER["below"]) * Cylinder(
                ADAPTER["shank_d"] / 2, ADAPTER["below"] + top, align=(CC, CC, CMIN))
            a += Pos(x, sy * y, top) * Cylinder(ADAPTER["flange_d"] / 2, ADAPTER["flange_t"],
                                                align=(CC, CC, CMIN))
            a.label = "PORT_ADAPTER_6061"
            out.append(a)
    return out


def foot_cuts():
    """Everything the shell foot must be cut for: adapter shanks and control wells."""
    cuts = [adapter_hole(x, sy * y) for x, y in T["bed_ports"] for sy in (-1, 1)]
    cuts += [well_cut(x, side) for _, x, side in WELLS]
    return cuts
