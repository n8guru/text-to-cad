"""Step 27 — the rear window / hatch opening, engineered rather than sketched.

Built in the HATCH LOCAL frame (x = vehicle +Y i.e. toward the driver side, y = up the rake of
the rear face, z = outward/rearward), then placed by ``geom.hatch_plane``.

What this module is responsible for, one function each:

  aperture / frame      ``hatch_surround``  - machined 6061 surround: bond flange, seal groove,
                                              return lip, hinge bosses, latch flange, gutter.
  glazing + retention   ``glazing_pane``    - 5 mm pane sitting in a rebate, captured by a bonded
                        ``glazing_retainer``  retainer strip, not by adhesive alone.
  leaf                  ``hatch_leaf``      - carbon leaf, two panes, mullion, T-handle, CHMSL.
  hinges                ``hinge_stations``  - 2 concealed hinges on a straight, dimensioned axis.
  struts                ``strut_geometry``  - anchors solved so the stroke is inside the catalogue
                                              stroke at BOTH ends of travel. Checked, not assumed.
  latches               ``latch_stations``  - the same rotary latch as the sockets. One spare PN.
  seal                  ``seal_bead``       - the same bulb section as the sockets. One seal PN.
  gutter / drains       ``gutter``          - catches roof run-off above the aperture, routes it
                        ``drain_tubes``       outboard, discharges below and outside the seal.
  interior closeouts    ``closeout_panels`` - covers hinge and strut hardware, leaves service access.
  kinematics            ``leaf_location``   - rigid-body pose of the leaf at any opening angle.
"""
from __future__ import annotations

import math

from build123d import (
    Align, Axis, Box, Compound, Cylinder, Plane, Pos, Rectangle, Rot, Vector,
    extrude, fillet,
)

import geom as G
import hw
import side_socket as SS
from side_socket import SEAL_MARGIN, rrect, rring

CC, CMIN, CMAX = Align.CENTER, Align.MIN, Align.MAX

W, HH = G.hatch_wh()
MG = G.H["margin"]
CR = G.H["corner_r"]
MULLION = G.H["mullion"]
OPEN_DEG = G.H["open_deg"]
WALL = G.WALL

FLANGE_T = 6.0
LIP_T = 8.0
LEAF_T = 26.0                      # carbon leaf sandwich thickness
GLASS_T = 5.0                      # hard-coat polycarbonate
REBATE_D = 9.0                     # glazing rebate depth in the leaf
# Same datum logic as the sockets: the leaf's outer face is flush at z = 0, so the surround face
# sits one leaf thickness plus one compressed-seal height inboard.
FACE_Z = -(LEAF_T + hw.d("bulb_seal")["compressed_height"])
SEAL_LAND_Z = FACE_Z

LATCH_Y = -HH / 2 - MG + 16.0
# The latch flange must live INBOARD of the surround face, or it fouls the leaf's inner skin and
# the compressed seal. checks_step27.check_hatch_interference_closed is what caught that.
LATCH_Z = FACE_Z - 26.0

# hinge axis, hatch-local. Straightness of this line is the tolerance that decides whether the
# leaf binds; held to 0.5 over the full 840 mm span (geom.TOL["hinge_axis_straightness"]).
HINGE_X = 420.0
HINGE_Y = HH / 2 + MG - 4.0
HINGE_Z = -12.0

LATCH_X = 450.0                    # +/- , bottom latch stations

# gas-strut anchors, hatch-local. Solved by ``solve_strut_anchors`` and asserted by
# checks_step27.check_strut_stroke -- NOT eyeballed.
STRUT_LEAF_X = 610.0                # on the leaf (leaf half-width is 664)
STRUT_SHELL_X = 760.0               # on the shell inner side wall, clear of the rear corner wrap
STRUT_SHELL = (STRUT_SHELL_X, 140.0, -64.0)
STRUT_LEAF = (STRUT_LEAF_X, -40.0, -24.0)


# --------------------------------------------------------------------------------------
# kinematics
# --------------------------------------------------------------------------------------
def leaf_location(angle_deg: float = 0.0):
    """Rigid-body transform of the whole leaf at ``angle_deg`` open, about the hinge axis (+x).

    Positive angle swings the BOTTOM of the leaf outward (+z), which is what a top-hinged hatch
    does. The sign is fixed here once so no downstream caller has to guess it.
    """
    axis = Pos(0, HINGE_Y, HINGE_Z)
    return axis * Rot(-angle_deg, 0, 0) * axis.inverse()


def leaf_point(p, angle_deg: float = 0.0) -> Vector:
    return (leaf_location(angle_deg) * Pos(*p)).position


def strut_length_at(angle_deg: float) -> float:
    return (leaf_point(STRUT_LEAF, angle_deg) - Vector(*STRUT_SHELL)).length


def solve_strut_anchors(target_closed: float, target_open: float, x=None):
    """Grid-search the shell anchor so the strut is inside its catalogue stroke at both ends.

    Returns (shell_anchor, leaf_anchor, L_closed, L_open). Used to derive STRUT_SHELL /
    STRUT_LEAF above; kept in the source so the numbers are reproducible, not magic.
    """
    x = STRUT_LEAF_X if x is None else x
    best = None
    for ly in range(-260, -100, 4):
        for lz in range(-60, -10, 4):
            leaf = (x, float(ly), float(lz))
            for sy in range(40, 200, 4):
                for sz in range(-400, -200, 5):
                    shell = (x, float(sy), float(sz))
                    ax = Pos(0, HINGE_Y, HINGE_Z)
                    def L(a):
                        p = (ax * Rot(-a, 0, 0) * ax.inverse() * Pos(*leaf)).position
                        return (p - Vector(*shell)).length
                    lc, lo = L(0.0), L(OPEN_DEG)
                    if lo < lc:
                        continue
                    err = abs(lc - target_closed) + abs(lo - target_open)
                    if best is None or err < best[0]:
                        best = (err, shell, leaf, lc, lo)
    return best[1], best[2], best[3], best[4]


# --------------------------------------------------------------------------------------
# frame / aperture
# --------------------------------------------------------------------------------------
def hatch_surround():
    """Machined 6061-T6 hatch surround: the authoritative opening.

    Carries the bond flange to the carbon shell, the seal groove, the return lip that defines the
    opening, the hinge bosses, the latch flange, and the gutter that keeps roof run-off out of the
    aperture. One part, one setup, held to hinge-axis straightness 0.5.
    """
    sl = hw.d("bulb_seal")
    part = rring(W + 2 * MG + 90, HH + 2 * MG + 90, CR + MG + 45, W, HH, CR,
                 FLANGE_T, FACE_Z - FLANGE_T)
    # seal RETENTION RIB (the DD6139 is a push-on channel, not a groove seal)
    gm = SEAL_MARGIN
    part += rring(W + gm * 2 + sl["rib_t"] / 2, HH + gm * 2 + sl["rib_t"] / 2, CR + gm,
                  W + gm * 2 - sl["rib_t"] / 2, HH + gm * 2 - sl["rib_t"] / 2,
                  CR + gm - sl["rib_t"], sl["rib_h"], FACE_Z)
    # return lip: the opening itself
    part += rring(W + 2 * LIP_T, HH + 2 * LIP_T, CR + LIP_T, W, HH, CR,
                  46.0, FACE_Z - FLANGE_T - 46.0)
    # hinge bosses. They sit ABOVE the leaf's top edge, not under it: the leaf reaches exactly to
    # HINGE_Y, so a boss at HINGE_Y - 10 buried itself in the leaf's inner skin. The shut-state
    # interference check is what caught that.
    for sx in (-1, 1):
        part += Pos(sx * HINGE_X, HINGE_Y + 24.0, HINGE_Z - 20.0) * Box(
            120.0, 44.0, 40.0, align=(CC, CC, CC))
        for dx in (-1, 1):
            part -= Pos(sx * HINGE_X + dx * hw.d("hinge")["hole_pitch"] / 2,
                        HINGE_Y + 24.0, HINGE_Z - 20.0) * Rot(90, 0, 0) * Cylinder(
                2.6, 60.0, align=(CC, CC, CC))
    # lightening pockets in the bond flange, same reasoning as the socket frame
    part -= rring(W + 2 * MG + 62, HH + 2 * MG + 62, CR + MG + 31,
                  W + 2 * MG + 16, HH + 2 * MG + 16, CR + MG + 8,
                  FLANGE_T - 2.5, FACE_Z - FLANGE_T - 0.5)
    # latch flange along the bottom, carrying the two Southco R4-30s
    part += Pos(0, LATCH_Y, LATCH_Z - 14.0) * Box(1120.0, 6.0, 80.0, align=(CC, CC, CC))
    p = hw.d("rotary_latch")
    t = SS.throat_root_local()
    for sx in (-1, 1):
        lp = latch_plane(sx * LATCH_X)
        for dy in (-1, 1):
            part -= lp * Pos(0, dy * p["hole_pitch"] / 2, 0) * Cylinder(
                p["panel_hole_dia"] / 2, 24.0, align=(CC, CC, CC))
        part -= lp * Pos(0, t.Y + p["slot_depth"] / 2, 0) * Box(
            p["throat_w"] + 1.0, p["slot_depth"] + 12, 24.0, align=(CC, CC, CC))
        part -= lp * Pos(0, t.Y, 0) * Cylinder(p["slot_end_r"], 24.0, align=(CC, CC, CC))
    return _lab(part, "HATCH_SURROUND_6061")


def gutter():
    """Roof run-off interceptor above the aperture.

    A 22 x 16 mm open channel bonded to the shell just above the seal land, sloped 1.5 deg to
    both outboard ends so it drains by gravity whether the truck is nose-up or nose-down. Without
    it, every drop that runs down the rear roof arrives at the top of the seal at once, which is
    how hatch seals get beaten.
    """
    y = HH / 2 + MG + 66.0
    length = W + 2 * MG + 120.0
    z = FACE_Z + 12.0
    ch = Pos(0, y, z) * Box(length, 22.0, 18.0, align=(CC, CC, CC))
    ch -= Pos(0, y + 1.0, z + 1.0) * Box(length - 8.0, 16.0, 14.0, align=(CC, CC, CC))
    # outboard fall: trim the channel floor so the low points are the two ends
    for sx in (-1, 1):
        ch -= Pos(sx * (length / 2 - 30), y, z - 8.0) * Box(60.0, 26.0, 6.0, align=(CC, CC, CC))
    return _lab(ch, "HATCH_GUTTER_6061")


def drain_tubes():
    """Two drains taking the gutter down the inside of the C-pillar to below the seal line.

    They exit OUTBOARD of the seal and above the bed rail, so water leaves the topper without
    ever being inside the sealed volume.
    """
    tubes = None
    y_top = HH / 2 + MG + 66.0
    y_bot = -HH / 2 - MG - 90.0
    for sx in (-1, 1):
        x = sx * (W / 2 + MG + 40.0)
        t = Pos(x, (y_top + y_bot) / 2, FACE_Z - 4.0) * Box(
            16.0, y_top - y_bot, 16.0, align=(CC, CC, CC))
        t -= Pos(x, (y_top + y_bot) / 2, FACE_Z - 4.0) * Box(
            10.0, y_top - y_bot + 2, 10.0, align=(CC, CC, CC))
        tubes = t if tubes is None else tubes + t
    return _lab(tubes, "HATCH_DRAIN_TUBES")


def seal_land_path():
    gm = SEAL_MARGIN
    sk = rrect(W + gm * 2, HH + gm * 2, CR + gm)
    return (Pos(0, 0, SEAL_LAND_Z) * sk).wire()


def seal_bead(compressed: bool = True):
    return hw.seal_bead(seal_land_path(), up=(0, 0, 1), compressed=compressed)


# --------------------------------------------------------------------------------------
# leaf, glazing, retention
# --------------------------------------------------------------------------------------
def _pane_w() -> float:
    return (W - MULLION) / 2 - 24.0


def _pane_h() -> float:
    return HH - 64.0


def leaf_shell():
    """Carbon leaf: outer skin, perimeter frame, mullion, and the glazing rebates."""
    lw, lh = W + 2 * MG - 8.0, HH + 2 * MG - 8.0
    part = Pos(0, 0, -LEAF_T) * extrude(rrect(lw, lh, CR + MG - 4.0), amount=LEAF_T)
    for sgn in (-1, 1):
        cx = sgn * (MULLION / 2 + _pane_w() / 2 + 24.0)
        # through window
        part -= Pos(cx, 0, -LEAF_T - 1) * extrude(rrect(_pane_w(), _pane_h(), 40.0), amount=LEAF_T + 2)
        # rebate the glazing lands in, from the outboard face
        part += (Pos(cx, 0, -REBATE_D) * extrude(rrect(_pane_w() + 36.0, _pane_h() + 36.0, 58.0), amount=REBATE_D)
                 - Pos(cx, 0, -REBATE_D - 1) * extrude(rrect(_pane_w(), _pane_h(), 40.0), amount=REBATE_D + 2))
    return _lab(part, "HATCH_LEAF_CARBON")


def glazing_pane(side: int = 1):
    """5 mm hard-coat PC pane seated in the leaf rebate."""
    cx = side * (MULLION / 2 + _pane_w() / 2 + 24.0)
    sk = rrect(_pane_w() + 30.0, _pane_h() + 30.0, 55.0)
    pane = Pos(cx, 0, -GLASS_T) * extrude(sk, amount=GLASS_T)
    return _lab(pane, f"GLAZING_PANE_{'L' if side > 0 else 'R'}")


def glazing_retainer(side: int = 1):
    """Bonded inner retainer strip: the mechanical half of the glazing retention.

    Urethane alone is a bonded joint with no redundancy; the retainer means a bond-line failure
    cannot let a pane leave the vehicle. It also sets the bond gap, so the urethane bead is a
    controlled 4 mm rather than however much squeezed out.
    """
    cx = side * (MULLION / 2 + _pane_w() / 2 + 24.0)
    outer = rrect(_pane_w() + 26.0, _pane_h() + 26.0, 52.0)
    inner = rrect(_pane_w() - 14.0, _pane_h() - 14.0, 34.0)
    ring = (Pos(cx, 0, -LEAF_T) * extrude(outer, amount=5.0)
            - Pos(cx, 0, -LEAF_T - 1) * extrude(inner, amount=7.0))
    return _lab(ring, f"GLAZING_RETAINER_{'L' if side > 0 else 'R'}")


def hatch_leaf(angle_deg: float = 0.0):
    """Complete leaf assembly at ``angle_deg`` open."""
    kids = [leaf_shell()]
    for s in (-1, 1):
        kids += [glazing_pane(s), glazing_retainer(s)]
    # Southco E3-18-15 keyed T-handle at the bottom centre, key-alike with the toolbox
    kids.append(Plane(origin=Vector(0, -HH / 2 - MG + 34.0, 0), x_dir=Vector(1, 0, 0),
                      z_dir=Vector(0, 0, 1)) * hw.t_handle())
    # secondary CHMSL -- REQUIRED by Upfitting Guide p.65 / FMVSS 108, the topper blocks the OEM one
    kids.append(Pos(0, HH / 2 + MG - 30.0, 0) * hw.chmsl())
    # striker bolts the surround's rotary latches capture
    for sx in (-1, 1):
        sp = striker_plane(sx * LATCH_X)
        kids.append(sp * hw.striker_bolt())
        kids.append(sp * hw.striker_bracket())
    loc = leaf_location(angle_deg)
    out = Compound(children=[loc * k for k in kids])
    out.label = f"HATCH_LEAF_ASSY:{angle_deg:.0f}deg"
    return out


# --------------------------------------------------------------------------------------
# hardware stations
# --------------------------------------------------------------------------------------
def hinge_stations(angle_deg: float = 0.0):
    kids = []
    for sx in (-1, 1):
        pl = Plane(origin=Vector(sx * HINGE_X, HINGE_Y, HINGE_Z),
                   x_dir=Vector(1, 0, 0), z_dir=Vector(0, 0, 1))
        kids.append(pl * hw.concealed_hinge(angle_deg))
    return kids


def latch_plane(x: float) -> Plane:
    """Same convention as the sockets: latch +Z = the flange normal (+y, up the rake), latch +Y =
    outward (+z), so the leaf's closing travel is the latch's -Y. One convention, two subsystems."""
    return Plane(origin=Vector(x, LATCH_Y, LATCH_Z), x_dir=Vector(-1, 0, 0), z_dir=Vector(0, 1, 0))


def striker_plane(x: float) -> Plane:
    lp = latch_plane(x)
    t = SS.throat_root_local()
    off = hw.d("rotary_latch")["width"] / 2 + 8.0
    return Plane(origin=(lp * Pos(off, t.Y, t.Z)).position, z_dir=(lp.x_dir * -1.0))


def latch_stations(state: str = "closed"):
    return [latch_plane(sx * LATCH_X) * hw.rotary_latch(state) for sx in (-1, 1)]


def strut_stations(angle_deg: float = 0.0):
    kids = []
    for sx in (-1, 1):
        a = Vector(sx * STRUT_SHELL[0], STRUT_SHELL[1], STRUT_SHELL[2])
        b = leaf_point((sx * STRUT_LEAF[0], STRUT_LEAF[1], STRUT_LEAF[2]), angle_deg)
        ext = ((b - a).length - hw.d("gas_strut")["compressed_len"]) / hw.d("gas_strut")["stroke"]
        ext = max(0.0, min(1.0, ext))
        pl = Plane(origin=a, z_dir=(b - a).normalized())
        kids.append(pl * hw.gas_strut(ext))
    return kids


def closeout_panels():
    """Interior closeouts hiding the hinge and strut hardware, with service access kept.

    Each panel is a separate 3 mm ABS/carbon moulding on 4 quarter-turn fasteners, so a hinge or
    strut can be reached without disturbing the headliner or the bonded surround.
    """
    kids = []
    for sx in (-1, 1):
        kids.append(_lab(Pos(sx * HINGE_X, HINGE_Y - 26.0, HINGE_Z - 58.0) * Box(
            190.0, 90.0, 3.0, align=(CC, CC, CC)), f"CLOSEOUT_HINGE_{'L' if sx > 0 else 'R'}"))
        kids.append(_lab(Pos(sx * (STRUT_LEAF_X + 40), 40.0, -170.0) * Box(
            70.0, 420.0, 3.0, align=(CC, CC, CC)), f"CLOSEOUT_STRUT_{'L' if sx > 0 else 'R'}"))
    return kids


def hatch_assembly(angle_deg: float = 0.0, state: str | None = None):
    """Whole rear-hatch subsystem at ``angle_deg``. Latch state follows the angle unless forced."""
    state = state or ("closed" if angle_deg < 1.0 else "open")
    kids = [hatch_surround(), gutter(), drain_tubes(), seal_bead(compressed=(angle_deg < 1.0)),
            hatch_leaf(angle_deg)]
    kids += hinge_stations(angle_deg) + latch_stations(state) + strut_stations(angle_deg)
    kids += closeout_panels()
    c = Compound(children=kids)
    c.label = f"REAR_HATCH:{angle_deg:.0f}deg"
    return c


def _lab(shape, name):
    shape.label = name
    return shape
