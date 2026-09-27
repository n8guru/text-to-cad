"""Shared geometry for the Step 27 authoritative CAD.

Reads the SAME ``blender/params.json`` the render lane reads, so the CAD and the visuals cannot
drift. params.json is in METRES (vehicle convention); this module publishes MILLIMETRES, which is
what every drawing, tolerance and vendor datasheet in this package uses.

Vehicle frame: X rearward, Y driver(+)/left, Z up. Origin = centreline at the forward edge of the
bed-rail top plane.

Socket frame (u, v, n): u along the shell, v up the lean of the side land, n outward normal.
A socket-local point maps to the vehicle frame through ``socket_plane(side, i)``.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from build123d import Plane, Vector

HERE = Path(__file__).resolve().parent
PARAMS = json.loads((HERE.parents[1] / "blender" / "params.json").read_text())

M = 1000.0  # params.json metres -> mm


def _mm(node):
    if isinstance(node, dict):
        return {k: _mm(v) for k, v in node.items()}
    if isinstance(node, list):
        return [_mm(v) for v in node]
    if isinstance(node, (int, float)):
        return node * M
    return node


T = _mm(PARAMS["truck"])
S = _mm(PARAMS["shell"])
K = _mm(PARAMS["socket"])
H = _mm(PARAMS["hatch"])
KEY = _mm(PARAMS["keying"])
ROOF_PORTS_X = _mm(PARAMS["roof_ports_x"])
ROOF_PORTS_Y = _mm(PARAMS["roof_ports_y"])
H["open_deg"] = PARAMS["hatch"]["open_deg"]          # an angle, not a length


def lean_rad() -> float:
    """Inward lean of the flat side land, radians."""
    return math.atan2(S["base_half_w"] - S["land_half_w"], S["land_top_z"])


def land_y(z: float) -> float:
    return S["base_half_w"] - z * math.tan(lean_rad())


def roof_z(x: float) -> float:
    t = (x - S["x0"]) / (S["x1"] - S["x0"])
    return S["roof_z_front"] + (S["roof_z_rear"] - S["roof_z_front"]) * t


def opening_wh() -> tuple[float, float]:
    """Socket aperture (width, height) measured in the leaned land plane, mm."""
    return K["width"], (K["z_top"] - K["z_bot"]) / math.cos(lean_rad())


def socket_plane(side: str, i: int) -> Plane:
    """Plane whose origin is the aperture centre on the outer land, x=u, y=v, z=n (outward).

    L sockets use u = -X and R sockets u = +X, so one module part fits either side by rotation
    rather than by being mirrored -- that is what makes four identical sockets possible.
    """
    a = lean_rad()
    s, c = math.sin(a), math.cos(a)
    zc = (K["z_bot"] + K["z_top"]) / 2
    x = K["centers_x"][i]
    if side == "L":
        o, u, n = Vector(x, land_y(zc), zc), Vector(-1, 0, 0), Vector(0, c, s)
    else:
        o, u, n = Vector(x, -land_y(zc), zc), Vector(1, 0, 0), Vector(0, -c, s)
    return Plane(origin=o, x_dir=u, z_dir=n)


def hatch_plane() -> Plane:
    """Rear hatch aperture plane. Origin at the aperture centre, x = +Y(driver), y = up-the-rake,
    z = outward (rearward). The leaf is raked back by ``shell.rear_rake`` over the roof height."""
    rz = roof_z(S["x1"])
    b = math.atan2(S["rear_rake"], rz)
    z0, z1 = H["z_bot"] + 30.0, rz - 130.0
    zc = (z0 + z1) / 2
    o = Vector(S["x1"] - S["rear_rake"] * zc / rz, 0, zc)
    return Plane(origin=o, x_dir=Vector(0, 1, 0), z_dir=Vector(math.cos(b), 0, math.sin(b)))


def hatch_wh() -> tuple[float, float]:
    rz = roof_z(S["x1"])
    b = math.atan2(S["rear_rake"], rz)
    z0, z1 = H["z_bot"] + 30.0, rz - 130.0
    return H["width"], (z1 - z0) / math.cos(b)


def hatch_rake_rad() -> float:
    rz = roof_z(S["x1"])
    return math.atan2(S["rear_rake"], rz)


# --- interface constants that the socket, the module and the hatch all have to agree on --------
WALL = S["wall"]                       # carbon sandwich wall thickness
POCKET_MARGIN = K["pocket_margin"]     # land step out from the aperture to the flange
SHUTLINE = K["shutline"]               # visible gap module-to-shell
LATCH_U = KEY["latch_u"]               # u positions of the two rotary latches per socket
PIN_U = KEY["pin_u"]                   # u positions of the round + diamond locating pins

LATCH_V = None                         # filled below: v of the latch mounting flange
LATCH_N = -60.0                        # n of the latch mounting flange centre (inboard)
STRIKER_V_DROP = 12.0                  # striker base sits this far below the latch plate
LEDGE_DROP = 105.0                     # ledge shelf below the aperture centre
PLUG_DEPTH = 85.0                      # how far the module plug reaches inboard

_W, _H = opening_wh()
LATCH_V = _H / 2 + 14.0

TOL = {
    "bushing_true_position": 0.05,
    "land_flatness": 0.30,
    "ledge_lip_height": 0.10,
    "seal_groove_depth": 0.10,
    "module_profile": 0.30,
    "hinge_axis_straightness": 0.50,
    "latch_pattern": 0.20,
}
