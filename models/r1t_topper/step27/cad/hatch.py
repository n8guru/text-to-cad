"""Step 27 — the rear hatch, engineered on the styled (raked) rear face.

Built in the HATCH LOCAL frame (x = vehicle +Y, y = up the rake of the rear face, z = outward),
placed by ``geom.hatch_plane``. Border offsets come from ``geom`` (H_*), measured outward from the
aperture edge, so the leaf, seal, surround, shell cut and checks share one set of numbers.

Stack at the aperture border, outboard to inboard:
  leaf (carbon)   z -26 .. 0     flush with the skin          offsets .. 26
  seal (comp.)    z -46 .. -26   DD6139 under the leaf edge    offset 16 +/- 5.6
  surround land   z -52 .. -46   (top-hat, 6061)               offsets 0 .. 34
  recess wall     z -52 .. 0                                   offsets 30 .. 34
  bond flange     z -28.5..-22.5 on the shell inner skin       offsets 34 .. 64
  return lip      z -74 .. -52                                 offsets 0 .. 8

Retention of the glazing is mechanical in BOTH directions: each pane is inside-glazed behind a
3 mm carbon lip (it cannot leave outward) and clamped by a screwed 6061 retainer (it cannot fall
inward). The previous pass bonded the pane to the outer face and put the "retainer" on the inner
face, where it retained nothing.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from build123d import (
    Align, Box, Compound, Cylinder, Plane, Pos, Rot, Vector, extrude,
)

import geom as G
import hw

CC, CMIN, CMAX = Align.CENTER, Align.MIN, Align.MAX

W, HH = G.hatch_wh()
AX, AY = W / 2, HH / 2
CR = G.H["corner_r"]
MULLION = G.H["mullion"]
OPEN_DEG = G.H["open_deg"]
LEAF_T = G.LEAF_T
FACE_Z = G.HATCH_FACE_Z
LAND0, LAND1 = FACE_Z - G.LAND_T, FACE_Z
LIP0 = LAND0 - G.H_LIP_DEPTH
LATCH = hw.d("rotary_latch")

# design-intent virtual pivot of the concealed linkage hinge: just outside the leaf's top edge,
# 2 mm outboard of the A-surface. A pivot inside the leaf (the previous z = -12) drives the top
# edge into the recess wall above it; see check_hatch_sweep_vs_frame.
HINGE_Y = AY + G.H_LEAF_OUT + 2.0
HINGE_Z = 2.0
HINGE_X = AX - 48.0

# glazing: two inside-glazed windows either side of the mullion
WIN = {"x0": MULLION / 2 + 12.0, "x1": AX - 80.0, "y": AY - 20.0, "r": 40.0,
       "lip": 3.0, "overlap": 12.0, "pane_t": 5.0, "ret_t": 5.0}

# latch stations (bottom corners, symmetric). The leaf swings about the hinge axis at the TOP, so
# a striker hung ~100 mm inboard of the skin (the previous stations, latch below the return lip)
# left on an arc 22 deg off the face normal and swept down through the aperture's bottom land
# (check_hatch_sweep). Each latch now sits up in the aperture tube behind the leaf's bottom
# strip with the closed bar only 50 mm below the skin, and is tilted about the bar axis so its
# slot lies on the CHORD of the bar's exit arc (deviation s^2/8R ~ 0.2 mm inside the 0.4 mm slot
# clearance). The bar crosses the whole latch (both side plates are slotted), so one PN serves
# both stations: each puts its bracket + arm OUTBOARD on solid leaf and the bolt head inboard.
LATCH_XS = (-(AX - 75.0), AX - 75.0)
BAR_Y, BAR_Z = -AY + 28.0, -50.0     # closed striker-bar centre, hatch-local
STRIKER_OFF = LATCH["width"] / 2 + 5.0
BRACKET = {"n": 40.0, "v": 26.0, "t": 6.0}


def _side(x: float) -> int:
    """+1: striker bracket on the latch's +X (= hatch -x) side; stations keep it outboard."""
    return 1 if x < 0 else -1


def _latch_tilt() -> float:
    yb, _ = hw.bar_centre("closed")
    r = math.hypot(BAR_Y - HINGE_Y, BAR_Z - HINGE_Z)
    tangent = math.degrees(math.atan2(HINGE_Z - BAR_Z, HINGE_Y - BAR_Y))
    exit_arc = math.degrees((LATCH["overall_l"] / 2 - yb) / r)   # bar travel to the mouth
    return tangent - exit_arc / 2


LATCH_TILT = _latch_tilt()

# strut solve inputs (hatch-local): leaf stud on the leaf inner face, frame stud on the side lip
STRUT = json.loads((Path(__file__).resolve().parents[1] / "hardware.json").read_text())["gas_strut"]
LEAF_STUD_Z = -LEAF_T - 12.0
FRAME_STUD_X = AX - 12.0
LEAF_STUD_X = AX - 26.0
STRUT_LEAF = tuple(STRUT["installed_geometry"]["leaf_stud"])     # solved, see solve_struts
STRUT_FRAME = tuple(STRUT["installed_geometry"]["frame_stud"])


def ring(e0, e1, z0, z1):
    return G.border_ring(AX, AY, CR, e0, e1, z0, z1)


def _lab(shape, name):
    shape.label = name
    return shape


# ------------------------------------------------------------------------------ kinematics
def leaf_location(angle_deg: float = 0.0):
    """Rigid-body pose of the leaf at ``angle_deg`` open about the design-intent hinge axis (+x).
    Positive angle swings the BOTTOM of the leaf outward (+z)."""
    axis = Pos(0, HINGE_Y, HINGE_Z)
    return axis * Rot(-angle_deg, 0, 0) * axis.inverse()


def leaf_point(p, angle_deg: float = 0.0) -> Vector:
    return (leaf_location(angle_deg) * Pos(*p)).position


# ------------------------------------------------------------------------------ surround
def latch_plane(x: float) -> Plane:
    """R4-30 at a bottom station: +X = -x; +Y = the slot, tilted LATCH_TILT from +z towards -y
    (mouth faces the leaf along the bar's exit chord); +Z = nose, up and slightly outward.
    Origin (panel face, hole-pattern centre) placed so the closed bar is at (x, BAR_Y, BAR_Z)."""
    t = math.radians(LATCH_TILT)
    ydir = Vector(0, -math.sin(t), math.cos(t))
    zdir = Vector(0, math.cos(t), math.sin(t))
    yb, zb = hw.bar_centre("closed")
    return Plane(origin=Vector(x, BAR_Y, BAR_Z) - ydir * yb - zdir * zb,
                 x_dir=Vector(-1, 0, 0), z_dir=zdir)


def striker_plane(x: float) -> Plane:
    """Bolt frame: +Z along the bolt from the bracket face through the latch to the head."""
    s = _side(x)
    y, z = hw.bar_centre("closed")
    o = (latch_plane(x) * Pos(s * STRIKER_OFF, y, z)).position
    return Plane(origin=o, x_dir=Vector(0, 0, 1), z_dir=Vector(s, 0, 0))


def bar_point(x: float) -> Vector:
    y, z = hw.bar_centre("closed")
    return (latch_plane(x) * Pos(0, y, z)).position


def latch_carrier():
    """Per station: a shelf plate under the latch flange (aft of the nose, tilted with the latch)
    and a 6 mm gusset beside the latch on the bolt-head side, down onto the bottom return lip.
    Both stay deeper than the bolt head, which only moves outward as the leaf opens."""
    from build123d import Polygon
    parts = []
    t, hwid = LATCH["panel_t"], LATCH["width"] / 2
    for x in LATCH_XS:
        s, lp = _side(x), latch_plane(x)
        xa, xb = sorted((-s * (hwid + 6.5), s * (hwid + 3.0)))           # latch-local X span
        plate = lp * Pos((xa + xb) / 2, -22.625, t / 2) * Box(xb - xa, 42.75, t)
        plate -= lp * Pos(0, -LATCH["hole_pitch"] / 2, t / 2) * Cylinder(
            LATCH["panel_hole_dia"] / 2, t + 2)
        far, near = (lp * Pos(0, -44.0, t)).position, (lp * Pos(0, -1.25, t)).position
        y_lip = -AY - G.LIP_T
        gusset = Polygon((y_lip, LIP0), (y_lip, far.Z), (far.Y, far.Z), (near.Y, near.Z),
                         align=None)
        gx = x + s * (hwid + 0.5) if s > 0 else x + s * (hwid + 6.5)       # low-x face
        parts += [plate, extrude(Plane.YZ.offset(gx) * gusset, amount=6.0)]
    out = parts[0]
    for p in parts[1:]:
        out += p
    return out


def hatch_surround():
    """Machined 6061-T6 top-hat surround: the authoritative opening."""
    sl = hw.d("bulb_seal")
    part = ring(0.0, G.H_RECESS_OUT, LAND0, LAND1)                      # seal land
    part += ring(G.H_RECESS_IN, G.H_RECESS_OUT, LAND0, 0.0)            # recess wall
    part += ring(G.H_RECESS_OUT - 1.0, G.H_BOND_OUT, *G.BOND_N)        # bond flange
    part += ring(0.0, G.LIP_T, LIP0, LAND0)                            # return lip
    part += ring(G.H_SEAL_OFF - sl["rib_t"] / 2, G.H_SEAL_OFF + sl["rib_t"] / 2,
                 FACE_Z, FACE_Z + sl["rib_h"])                          # seal rib
    part += latch_carrier()
    for sx in (-1, 1):                                                  # hinge body blocks
        part += Pos(sx * HINGE_X, AY - 11.0, (LIP0 + LAND0) / 2) * Box(
            30.0, 22.0, LAND0 - LIP0, align=(CC, CC, CC))
    for sx in (-1, 1):                                                  # strut frame brackets
        y0, y1 = STRUT_FRAME[1] - 20.0, STRUT_FRAME[1] + 20.0
        z0 = STRUT_FRAME[2] - 12.0
        br = Pos(sx * (AX + 3.0), (y0 + y1) / 2, (z0 + LIP0) / 2) * Box(
            6.0, y1 - y0, LIP0 - z0, align=(CC, CC, CC))
        br -= Pos(sx * (AX + 3.0), STRUT_FRAME[1], STRUT_FRAME[2]) * Rot(0, 90, 0) * Cylinder(
            4.0, 8.0, align=(CC, CC, CC))                                # M8 tapped
        part += br
    for x in _drain_x():                                                # drain spigot holes
        part -= Pos(x, -AY - (G.H_SEAL_OFF + 6.0 + G.H_RECESS_IN) / 2, LAND0 - 1) * Cylinder(
            2.5, G.LAND_T + 2, align=(CC, CC, CMIN))
    return _lab(part, "HATCH_SURROUND_6061")


def _drain_x():
    """Ends of the straight bottom run of the wet channel (the corners start beyond AX - CR)."""
    return (-(AX - CR), AX - CR)


def drain_tubes():
    """Wet-zone drains: from the channel between the seal and the recess wall, at the ends of its
    straight bottom run, down behind the surround and out through the rear skin below the bond
    flange. Two separate tubes."""
    out = []
    y0 = -AY - (G.H_SEAL_OFF + 6.0 + G.H_RECESS_IN) / 2
    y1 = -AY - G.H_BOND_OUT - 10.0
    for x in _drain_x():
        run = Pos(x, (y0 + y1) / 2, LAND0 - 5.0) * Box(8.0, y0 - y1, 8.0, align=(CC, CC, CC))
        exit_ = Pos(x, y1 + 4.0, (LAND0 - 9.0 + 1.0) / 2) * Box(8.0, 8.0, 1.0 - (LAND0 - 9.0),
                                                              align=(CC, CC, CC))
        spigot = Pos(x, y0, (LAND0 - 1.0 + LAND0 - 9.0) / 2) * Box(8.0, 8.0, 8.0, align=(CC, CC, CC))
        out.append(_lab(run + exit_ + spigot, f"HATCH_DRAIN_TUBE_{'L' if x > 0 else 'R'}"))
    return out


def seal_land_path():
    sk = G.rrect(2 * (AX + G.H_SEAL_OFF), 2 * (AY + G.H_SEAL_OFF), CR + G.H_SEAL_OFF)
    return (Pos(0, 0, FACE_Z) * sk).wire()


def seal_bead(compressed: bool = True):
    return hw.seal_bead(seal_land_path(), up=(0, 0, 1), compressed=compressed)


# ------------------------------------------------------------------------------ leaf
def _win_centres():
    cx = (WIN["x0"] + WIN["x1"]) / 2
    return (-cx, cx)


def _win_sketch(grow):
    w = WIN["x1"] - WIN["x0"] + 2 * grow
    h = 2 * WIN["y"] + 2 * grow
    return G.rrect(w, h, WIN["r"] + grow)


def leaf_shell():
    """Carbon leaf, flush: outer skin lip over each pane, inside-glazed pockets, solid mullion."""
    e = G.H_LEAF_OUT
    part = Pos(0, 0, -LEAF_T) * extrude(G.rrect(2 * (AX + e), 2 * (AY + e), CR + e), amount=LEAF_T)
    for cx in _win_centres():
        part -= Pos(cx, 0, -LEAF_T - 1) * extrude(_win_sketch(0.0), amount=LEAF_T + 2)
        part -= Pos(cx, 0, -LEAF_T - 1) * extrude(_win_sketch(WIN["overlap"] + 0.5),
                                                  amount=LEAF_T + 1 - WIN["lip"])
    return _lab(part, "HATCH_LEAF_CARBON")


def glazing_pane(side: int = 1):
    cx = _win_centres()[0 if side < 0 else 1]
    z1 = -WIN["lip"]
    pane = Pos(cx, 0, z1 - WIN["pane_t"]) * extrude(_win_sketch(WIN["overlap"]), amount=WIN["pane_t"])
    return _lab(pane, f"GLAZING_PANE_{'L' if side > 0 else 'R'}")


def glazing_retainer(side: int = 1):
    cx = _win_centres()[0 if side < 0 else 1]
    z1 = -WIN["lip"] - WIN["pane_t"]
    outer = _win_sketch(WIN["overlap"])
    inner = _win_sketch(-5.0)
    ring_ = (Pos(cx, 0, z1 - WIN["ret_t"]) * extrude(outer, amount=WIN["ret_t"])
             - Pos(cx, 0, z1 - WIN["ret_t"] - 1) * extrude(inner, amount=WIN["ret_t"] + 2))
    return _lab(ring_, f"GLAZING_RETAINER_{'L' if side > 0 else 'R'}")


def leaf_striker_arm(x: float):
    """6061 arm from the leaf inner face down to the striker bracket, outboard of the pocket."""
    bar = bar_point(x)
    face = x - _side(x) * (STRIKER_OFF + BRACKET["t"])                  # bracket back face
    u0, u1 = sorted((face, face - _side(x) * 12.0))
    y0, y1 = bar.Y - BRACKET["v"] / 2, bar.Y + BRACKET["v"] / 2
    z0 = bar.Z - BRACKET["n"] / 2
    arm = Pos((u0 + u1) / 2, (y0 + y1) / 2, (z0 - LEAF_T) / 2) * Box(
        u1 - u0, y1 - y0, -LEAF_T - z0, align=(CC, CC, CC))
    arm -= striker_plane(x) * Cylinder(5.0, 20.0, align=(CC, CC, CMAX))
    return _lab(arm, "LEAF_STRIKER_ARM_6061")


def striker_bracket_at(x: float):
    b = BRACKET
    part = Box(b["n"], b["v"], b["t"], align=(CC, CC, CMAX))
    part -= Pos(0, 0, 1) * Box(16.6, 10.6, b["t"] + 2, align=(CC, CC, CMAX))    # +/-3 mm slot
    part.label = "STRIKER_BRACKET_custom"
    return striker_plane(x) * part


def hinge_door_blocks():
    return [_lab(Pos(sx * HINGE_X, AY - 11.0, -LEAF_T - 5.0) * Box(30.0, 22.0, 10.0,
                                                                  align=(CC, CC, CC)),
                 "HINGE_GN7233_door_leaf") for sx in (-1, 1)]


def t_handle_plane():
    return Plane(origin=Vector(0, -AY + 14.0, 0), x_dir=Vector(1, 0, 0), z_dir=Vector(0, 0, 1))


def hatch_leaf(angle_deg: float = 0.0):
    """Complete leaf assembly at ``angle_deg`` open."""
    leaf = leaf_shell()
    th = hw.d("t_handle")
    tp = t_handle_plane()
    leaf -= tp * Pos(0, 0, -LEAF_T - 1) * Cylinder(th["cutout_dia"] / 2 + 0.3, LEAF_T + 2,
                                                  align=(CC, CC, CMIN))
    leaf -= tp * Pos(0, 0, -4.2) * Cylinder(th["escutcheon_dia"] / 2 + 0.3, 5.0, align=(CC, CC, CMIN))

    leaf.label = "HATCH_LEAF_CARBON"
    kids = [leaf]
    for s in (-1, 1):
        kids += [glazing_pane(s), glazing_retainer(s)]
    kids.append(t_handle_plane() * hw.t_handle())
    kids.append(Pos(0, AY + G.H_LEAF_OUT - 20.0, 0) * hw.chmsl())
    for x in LATCH_XS:
        kids.append(striker_plane(x) * hw.striker_bolt())
        kids.append(striker_bracket_at(x))
        kids.append(leaf_striker_arm(x))
    kids += hinge_door_blocks()
    for sx in (-1, 1):
        face_z = STRUT_LEAF[2] + hw.HW["gas_strut"]["ball_stud"]["flange_to_ball_centre"]
        boss = Pos(sx * STRUT_LEAF[0], STRUT_LEAF[1], (face_z - LEAF_T) / 2) * Box(
            22.0, 22.0, -LEAF_T - face_z, align=(CC, CC, CC))
        boss -= Pos(sx * STRUT_LEAF[0], STRUT_LEAF[1], face_z - 1) * Cylinder(
            4.0, 14.0, align=(CC, CC, CMIN))                             # M8 tapped
        kids.append(_lab(boss, "LEAF_STRUT_BOSS_6061"))
        kids.append(Plane(origin=Vector(sx * STRUT_LEAF[0], STRUT_LEAF[1], face_z),
                          x_dir=Vector(1, 0, 0), z_dir=Vector(0, 0, -1)) * hw.ball_stud())
    loc = leaf_location(angle_deg)
    out = Compound(children=[loc * k for k in kids])
    out.label = f"HATCH_LEAF_ASSY:{angle_deg:.0f}deg"
    return out


# ------------------------------------------------------------------------------ struts
def strut_table():
    """Stabilus LIFT-O-MAT HD 6-15, column 1 (ball sockets), Standard Program p.17."""
    return [dict(r) for r in STRUT["catalogue_6_15"]]


def _rot_yz(pts, a_deg):
    """numpy: rotate hatch-local points (N,3) about the hinge axis (+x) by -a (bottom outward)."""
    import numpy as np
    a = math.radians(a_deg)
    y, z = pts[:, 1] - HINGE_Y, pts[:, 2] - HINGE_Z
    c, s_ = math.cos(-a), math.sin(-a)
    out = pts.copy()
    out[:, 1] = HINGE_Y + y * c - z * s_
    out[:, 2] = HINGE_Z + y * s_ + z * c
    return out


def strut_arm(leaf, frame, a):
    """Moment arm of the strut line about the hinge AXIS (+x), mm."""
    import numpy as np
    b = _rot_yz(np.array([leaf], float), a)[0]
    f = np.array(frame, float)
    d = (f - b) / np.linalg.norm(f - b)
    h = np.array([b[0], HINGE_Y, HINGE_Z])
    r = b - h
    return abs(r[1] * d[2] - r[2] * d[1])


def gravity_arm(cg, a):
    """Horizontal (vehicle-frame) lever of the leaf CG about the hinge axis at angle a, mm."""
    import numpy as np
    p = _rot_yz(np.array([cg], float), a)[0]
    r = G.hatch_rake_rad()
    return abs(-(p[1] - HINGE_Y) * math.sin(r) + (p[2] - HINGE_Z) * math.cos(r))


def solve_struts(mass_kg=None, cg=(0.0, 0.0, -13.0)):
    """Search stud positions x catalogue entries; keep the lowest force that holds the leaf open.

    Constraints: installed length inside the catalogue stroke with 5 mm margin at both ends,
    monotonic extension through 0..OPEN_DEG, hold-open ratio >= 1.4 at full open, close force at
    the handle <= 90 N, and the closed strut stays inside the aperture side strip (no crossing of
    the seal line). Returns (entry, leaf_stud, frame_stud, metrics) or None.
    """
    import numpy as np
    mass_kg = leaf_mass_kg() if mass_kg is None else mass_kg
    angles = np.arange(0.0, OPEN_DEG + 0.1, 5.0)
    ly = np.arange(-AY + 30.0, AY - 25.0, 5.0)
    fy = np.arange(-AY + 20.0, AY - 20.0, 5.0)
    fz = np.arange(-60.0, -201.0, -10.0)
    lzs = np.arange(LEAF_STUD_Z, LEAF_STUD_Z - 41.0, -10.0)
    L_, F_ = np.meshgrid(ly, fy, indexing="ij")
    grav = mass_kg * 9.81 * gravity_arm(cg, OPEN_DEG) / 1000.0
    handle_lever = (HINGE_Y - (-AY - G.H_LEAF_OUT + 20.0)) / 1000.0
    best = None
    for entry in strut_table():
        comp, ext = entry["extended"] - entry["stroke"], entry["extended"]
        for z_f, z_l in ((a, b) for a in fz for b in lzs):
            leaf = np.stack([np.full(L_.size, LEAF_STUD_X), L_.ravel(), np.full(L_.size, z_l)], 1)
            frame = np.stack([np.full(L_.size, FRAME_STUD_X), F_.ravel(), np.full(L_.size, z_f)], 1)
            lens = np.stack([np.linalg.norm(_rot_yz(leaf, a) - frame, axis=1) for a in angles], 1)
            ok = (lens[:, 0] >= comp + 5) & (lens[:, -1] <= ext - 5)
            ok &= np.all(np.diff(lens, axis=1) >= -0.01, axis=1)
            for k in np.nonzero(ok)[0]:
                lf, fr = tuple(leaf[k]), tuple(frame[k])
                arm_o, arm_c = strut_arm(lf, fr, OPEN_DEG), strut_arm(lf, fr, 0.0)
                hold = 2 * entry["force"] * arm_o / 1000.0 / max(grav, 1e-6)
                close = 2 * entry["force"] * arm_c / 1000.0 / handle_lever
                if hold < 1.4 or close > 90.0:
                    continue
                key = (entry["force"], -hold)
                if best is None or key < best[0]:
                    best = (key, entry, lf, fr, {"L_closed": float(lens[k, 0]),
                                                 "L_open": float(lens[k, -1]), "hold_ratio": hold,
                                                 "close_N": close, "arm_open": arm_o,
                                                 "arm_closed": arm_c, "mass_kg": mass_kg,
                                                 "gravity_Nm_open": grav})
    return None if best is None else best[1:]


def leaf_mass_kg() -> float:
    dens = {"CARBON": None, "GLAZ": 1.20e-6, "RETAIN": 2.70e-6}
    m = 0.0
    for c in hatch_leaf(0.0).children:
        lab = (c.label or "").upper()
        if "CARBON" in lab:
            m += c.volume / LEAF_T * 5.8e-6        # 26 mm sandwich at 5.8 kg/m^2
        elif "GLAZ" in lab and "PANE" in lab:
            m += c.volume * dens["GLAZ"]
        else:
            m += c.volume * 2.7e-6 if "RETAIN" in lab or "ARM" in lab else c.volume * 3.0e-6
    return m


def strut_stations(angle_deg: float = 0.0):
    g = hw.d("gas_strut")
    kids = []
    for sx in (-1, 1):
        a = Vector(sx * STRUT_FRAME[0], STRUT_FRAME[1], STRUT_FRAME[2])
        b = leaf_point((sx * STRUT_LEAF[0], STRUT_LEAF[1], STRUT_LEAF[2]), angle_deg)
        ext = ((b - a).length - g["compressed_len"]) / g["stroke"]
        ext = max(0.0, min(1.0, ext))
        pl = Plane(origin=a, z_dir=(b - a).normalized())
        s = pl * hw.gas_strut(ext)
        kids.append(s)
        kids.append(Plane(origin=Vector(sx * AX, STRUT_FRAME[1], STRUT_FRAME[2]),
                          x_dir=Vector(0, 1, 0), z_dir=Vector(-sx, 0, 0)) * hw.ball_stud())
    return kids


def latch_stations(state: str = "closed"):
    return [latch_plane(x) * hw.rotary_latch(state) for x in LATCH_XS]


def hatch_assembly(angle_deg: float = 0.0, state: str | None = None):
    state = state or ("closed" if angle_deg < 1.0 else "open")
    kids = [hatch_surround(), *drain_tubes(), seal_bead(compressed=(angle_deg < 1.0)),
            hatch_leaf(angle_deg)]
    kids += latch_stations(state) + strut_stations(angle_deg)
    c = Compound(children=kids)
    c.label = f"REAR_HATCH:{angle_deg:.0f}deg"
    return c
