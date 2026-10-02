"""Shared geometry for the Step 27 authoritative CAD.

Reads the SAME ``blender/params.json`` the render lane reads, so the CAD and the visuals cannot
drift. params.json is in METRES (vehicle convention); this module publishes MILLIMETRES, which is
what every drawing, tolerance and vendor datasheet in this package uses.

Vehicle frame: X rearward, Y driver(+), Z up. Origin = centreline at the bed's inside front wall,
z = 0 on the bed-rail top (the plane the topper foot sits on).

Socket frame (u, v, n): u along the shell, v up the lean of the side land, n outward normal.
Hatch frame (x, y, z): x = vehicle +Y, y = up the rake of the rear face, z = outward.

The socket and hatch BORDERS below are the interface stack, measured outward from the aperture
edge. They are one set of numbers shared by the frame, the module, the seal, the shell cut and the
checks, which is the point: the previous pass let each part pick its own offset and the seal ended
up outside the panel that was supposed to compress it.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from build123d import Plane, Pos, Rectangle, Vector, extrude, fillet

HERE = Path(__file__).resolve().parent
PARAMS_PATH = HERE.parents[1] / "blender" / "params.json"
PARAMS = json.loads(PARAMS_PATH.read_text())

M = 1000.0  # params.json metres -> mm
ANGLES = {"lean_deg", "rear_rake_deg", "open_deg"}


def _mm(node, key=""):
    if isinstance(node, dict):
        return {k: _mm(v, k) for k, v in node.items()}
    if isinstance(node, list):
        return [_mm(v, key) for v in node]
    if isinstance(node, (int, float)) and key not in ANGLES:
        return node * M
    return node


T = _mm(PARAMS["truck"])
S = _mm(PARAMS["shell"])
K = _mm(PARAMS["socket"])
H = _mm(PARAMS["hatch"])
KEY = _mm(PARAMS["keying"])
BR = _mm(PARAMS["base_rail"])
MT = _mm(PARAMS["mount"])              # topper-to-truck attachment stack (mounts.py)
ROOF_PORTS_X = _mm(PARAMS["roof_ports_x"])
ROOF_PORTS_Y = _mm(PARAMS["roof_ports_y"])

WALL = S["wall"]                       # carbon sandwich wall thickness
SHUTLINE = K["shutline"]               # visible gap module-to-frame and leaf-to-frame
LATCH_U = KEY["latch_u"]               # u of the two rotary latches per socket
PIN_U = KEY["pin_u"]                   # u of the round + diamond locating pins (asymmetric)


# ------------------------------------------------------------------------------ sketch helpers
def rrect(w: float, h: float, r: float):
    """Rounded-rectangle sketch on Plane.XY, centred."""
    r = min(r, w / 2 - 0.01, h / 2 - 0.01)
    return fillet(Rectangle(w, h).vertices(), radius=r)


def rring(wo, ho, ro, wi, hi, ri, t, z0=0.0):
    """Extruded rounded-rectangular ring from z0 to z0 + t."""
    return (Pos(0, 0, z0) * extrude(rrect(wo, ho, ro), amount=t)
            - Pos(0, 0, z0 - 1) * extrude(rrect(wi, hi, ri), amount=t + 2))


def border_ring(a_u, a_v, r, e0, e1, n0, n1):
    """Ring between border offsets e0 < e1 (mm outward from an a_u x a_v half-size aperture with
    corner radius r), spanning local z n0..n1. Concentric corners: radius r + e."""
    return rring(2 * (a_u + e1), 2 * (a_v + e1), r + e1,
                 2 * (a_u + e0), 2 * (a_v + e0), max(r + e0, 0.5), n1 - n0, n0)


# ------------------------------------------------------------------------------ side land
def lean_rad() -> float:
    """Inward lean (tumblehome) of the flat side land, radians."""
    return math.radians(S["lean_deg"])


def land_y(z: float) -> float:
    """Half-width of the outer side land at height z (flat plane through the base line)."""
    return S["base_half_w"] - z * math.tan(lean_rad())


def opening_wh() -> tuple[float, float]:
    """Socket aperture (width, height) measured in the leaned land plane, mm."""
    return K["width"], (K["z_top"] - K["z_bot"]) / math.cos(lean_rad())


def socket_plane(side: str, i: int) -> Plane:
    """Aperture-centre plane on the outer land: x = u, y = v (up the lean), z = n (outward).

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


# ------------------------------------------------------------------------------ rear face
def rake_rad() -> float:
    return math.radians(S["rear_rake_deg"])


def rear_face_x(z: float) -> float:
    """x of the (flat, raked) rear face at height z."""
    return S["x1"] - z * math.tan(rake_rad())


def hatch_wh() -> tuple[float, float]:
    return H["width"], H["height"]


def hatch_plane() -> Plane:
    """Aperture-centre plane on the rear face: x = vehicle +Y, y = up the rake, z = outward."""
    r = rake_rad()
    s_c = H["sill_s"] + H["height"] / 2          # in-plane distance from the rail up the face
    o = Vector(S["x1"] - s_c * math.sin(r), 0, s_c * math.cos(r))
    return Plane(origin=o, x_dir=Vector(0, 1, 0), z_dir=Vector(math.cos(r), 0, math.sin(r)))


def hatch_rake_rad() -> float:
    return rake_rad()


# ------------------------------------------------------------------------------ interface stack
# Socket border, mm outward from the aperture edge (same numbers top, bottom and both ends).
MODULE_FLANGE_T = 6.0        # module flange, outer face flush with the shell at n = 0
SEAL_COMPRESSED = 20.25      # DD6139 compressed height (hardware.json, checked in checks_step27)
FACE_N = -(MODULE_FLANGE_T + SEAL_COMPRESSED)   # socket seal land
LAND_T = 6.0                 # seal-land plate thickness
LIP_T = 8.0                  # return lip (the aperture wall the plug slides in)
LIP_DEPTH = 55.0
SEAL_OFF = 32.0              # seal centreline
PIN_OFF = 16.0               # bushings / locating pins (top border, inside the seal line)
MF_IN = -20.0                # module flange overlaps the aperture by 20 mm
MF_OUT = 44.0                # module flange outer edge
RECESS_IN = MF_OUT + SHUTLINE            # frame recess wall, inner face
RECESS_WALL_T = 4.0
RECESS_OUT = RECESS_IN + RECESS_WALL_T   # frame recess wall, outer face
BOND_GAP = 0.5
SHELL_CUT = RECESS_OUT + BOND_GAP        # through-cut in the carbon shell
BOND_W = 30.0                            # bond flange on the shell inner skin
BOND_OUT = RECESS_OUT + BOND_W
BOND_N = (-(WALL + BOND_GAP + 6.0), -(WALL + BOND_GAP))   # bond flange n-range
PLUG_CLR = 6.0               # plug tube to return lip, per side
PLUG_DEPTH = 85.0            # how far the module plug reaches inboard

# Hatch border, mm outward from the hatch aperture edge (hatch-local x/y).
LEAF_T = 26.0
HATCH_FACE_Z = -(LEAF_T + SEAL_COMPRESSED)
H_SEAL_OFF = 16.0
H_LEAF_OUT = 26.0
H_RECESS_IN = H_LEAF_OUT + SHUTLINE
H_RECESS_OUT = H_RECESS_IN + RECESS_WALL_T
H_SHELL_CUT = H_RECESS_OUT + BOND_GAP
H_BOND_OUT = H_RECESS_OUT + BOND_W
H_LIP_DEPTH = 22.0

TOL = {
    "bushing_true_position": 0.05,
    "land_flatness": 0.30,
    "ledge_lip_height": 0.10,
    "seal_groove_depth": 0.10,
    "module_profile": 0.30,
    "hinge_axis_straightness": 0.50,
    "latch_pattern": 0.20,
}
