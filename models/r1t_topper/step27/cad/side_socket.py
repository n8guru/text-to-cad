"""Step 27 — the side socket and its mating module interface, as authoritative solids.

Built in the SOCKET LOCAL frame (x = u along the shell, y = v up the land lean, z = n outward
normal), then placed into the vehicle frame by ``geom.socket_plane``.

The four sockets are geometrically identical: one CNC program, one fixture, one seal length, one
latch pattern. ``checks_step27.py`` asserts that identity rather than asserting it in prose.

Load path, so the latch selection is traceable:
  * module weight  -> 2x J-hooks -> machined ledge lip, in SHEAR. The latches carry no dead weight.
  * outward pull   -> 2x Southco R4-30 fork bolts on R4-90-321-20 striker bolts.
  * seal preload   -> the Trim-Lok DD6139 bulb at 33 % deflection pushes the module outward onto
                      the forks, so the joint is always loaded and cannot rattle.
  * over-crush     -> 3x UHMW compression limiters set a hard metal stop before the bulb bottoms.
"""
from __future__ import annotations

import math

from build123d import (
    Align, Axis, Box, Compound, Cylinder, Plane, Pos, Rectangle, Rot, Vector,
    extrude, fillet,
)

import geom as G
import hw

CC, CMIN, CMAX = Align.CENTER, Align.MIN, Align.MAX

W, HH = G.opening_wh()
MG = G.POCKET_MARGIN
PW, PH, PR = W + 2 * MG, HH + 2 * MG, G.K["corner_r"] + MG
FLANGE_T = 6.0
LIP_T = 8.0
MODULE_FLANGE_T = 6.0                 # module flange: outer face flush at n = 0
# The seal stack sets the datum, not the other way round: the socket flange face sits exactly one
# compressed-seal height inboard of the module flange's inner face, so the bulb is at its designed
# 33 % deflection when the module is home and nothing has to be shimmed at assembly.
FACE_N = -(MODULE_FLANGE_T + hw.d("bulb_seal")["compressed_height"])
SEAL_LAND_N = FACE_N                  # the rib root, i.e. where the seal's base sits
LATCH_FLANGE_T = 6.0
SEAL_MARGIN = MG + 26.0               # seal line, outboard of the aperture


def rrect(w: float, h: float, r: float):
    """Rounded-rectangle sketch on Plane.XY, centred."""
    r = min(r, w / 2 - 0.01, h / 2 - 0.01)
    return fillet(Rectangle(w, h).vertices(), radius=r)


def rring(wo, ho, ro, wi, hi, ri, t, z0=0.0):
    """Extruded rounded-rectangular ring, z0 to z0+t."""
    return (Pos(0, 0, z0) * extrude(rrect(wo, ho, ro), amount=t)
            - Pos(0, 0, z0 - 1) * extrude(rrect(wi, hi, ri), amount=t + 2))


# --------------------------------------------------------------------------------------
# placement frames — one definition, used by the CAD, the checks and the Blender lane
# --------------------------------------------------------------------------------------
def latch_plane(u: float) -> Plane:
    """Placement plane for one Southco R4-30 on the socket's latch flange.

    latch +Z -> socket +v (the flange normal), latch +Y -> socket +n (so closing travel, which is
    -n, is the latch's -Y), latch +X -> socket -u (the fork-bolt and striker-bar axis).
    """
    return Plane(origin=Vector(u, G.LATCH_V, G.LATCH_N),
                 x_dir=Vector(-1, 0, 0), z_dir=Vector(0, 1, 0))


def throat_root_local() -> Vector:
    """Where the striker bar sits when the latch is SHUT, in latch-local coordinates.

    The bar stays at a fixed radius from the fork pivot and the fork rotates around it, so the
    shut position is the mouth root swung through the closing angle -- not the root at 0 deg,
    which is where the fork RECEIVES the bar.
    """
    p = hw.d("rotary_latch")
    r = p["claw_r"] - p["throat_depth"]
    a = math.radians(hw.HW["rotary_latch"]["kinematics"]["closed_deg"])
    return Vector(0.0, p["pivot_y"] + r * math.cos(a), hw.PIVOT_Z + r * math.sin(a))


def striker_plane(u: float) -> Plane:
    """Striker-bolt plane: shoulder axis coaxial with the fork-bolt axis, bar in the throat."""
    lp = latch_plane(u)
    t = throat_root_local()
    # The bracket sits on the FAR side of the fork bolt, so the Dia 12.7 shoulder crosses the
    # fork's 8 mm thickness on its way in. Offsetting the other way put the bolt's THREAD in the
    # fork and the shoulder 40 mm past it -- caught by the solid-intersection check below.
    off = hw.d("rotary_latch")["width"] / 2 + 8.0
    origin = lp * Pos(off, t.Y, t.Z)
    return Plane(origin=origin.position, z_dir=(lp.x_dir * -1.0))


def cable_route(u: float):
    """Interior push-pull cable polyline, splitter -> one latch's cable eye, mm."""
    p = hw.d("rotary_latch")
    eye = latch_plane(u) * Pos(0, -p["cable_arm_l"] - 6, hw.PIVOT_Z + 2)
    split = Vector(0.0, G.LATCH_V - 30.0, G.LATCH_N - 40.0)
    mid = Vector(u * 0.5, G.LATCH_V - 26.0, G.LATCH_N - 36.0)
    knee = Vector(u * 0.88, G.LATCH_V - 14.0, G.LATCH_N - 18.0)
    return [tuple(split), tuple(mid), tuple(knee), tuple(eye.position)]


# --------------------------------------------------------------------------------------
# socket-side (shell) parts
# --------------------------------------------------------------------------------------
def socket_frame():
    """Machined 6061-T6 socket frame: bond flange, seal RIB, return lip, latch flange, bushings.

    One part, one CNC program, four off. Tolerance-critical features are listed in ``geom.TOL``
    and dimensioned on DWG-27-001.

    The seal is a Trim-Lok DD6139 PUSH-ON channel, so the frame carries a 3 mm retention RIB, not
    a groove. That supersedes the earlier groove design and is why the rib thickness sits inside
    the seal's published .060-.125 in grip range.
    """
    s = hw.d("bulb_seal")
    r = G.K["corner_r"]
    part = rring(PW + 90, PH + 90, PR + 45, W, HH, r, FLANGE_T, FACE_N - FLANGE_T)
    # seal retention rib, standing proud of the flange face
    part += rring(PW + SEAL_MARGIN * 2 + s["rib_t"] / 2, PH + SEAL_MARGIN * 2 + s["rib_t"] / 2,
                  PR + SEAL_MARGIN,
                  PW + SEAL_MARGIN * 2 - s["rib_t"] / 2, PH + SEAL_MARGIN * 2 - s["rib_t"] / 2,
                  PR + SEAL_MARGIN - s["rib_t"], s["rib_h"], FACE_N)
    # return lip: the aperture wall the module plug slides into
    part += rring(W + 2 * LIP_T, HH + 2 * LIP_T, r + LIP_T, W, HH, r,
                  55.0, FACE_N - FLANGE_T - 55.0)
    # latch mounting flange across the top of the aperture, inboard
    lf = Pos(0, G.LATCH_V - LATCH_FLANGE_T / 2, (G.LATCH_N - 30.0) / 2) * Box(
        620.0, LATCH_FLANGE_T, 80.0, align=(CC, CC, CC))
    p = hw.d("rotary_latch")
    for u in G.LATCH_U:
        for sy in (-1, 1):                          # 38.1 mm pattern, Dia 7.8 panel prep
            lf -= latch_plane(u) * Pos(0, sy * p["hole_pitch"] / 2, 0) * Cylinder(
                p["panel_hole_dia"] / 2, LATCH_FLANGE_T + 8, align=(CC, CC, CC))
        # striker entry slot: 17 deep with an R8 end, per the Southco panel preparation
        t = throat_root_local()
        lf -= latch_plane(u) * Pos(0, t.Y + p["slot_depth"] / 2, 0) * Box(
            p["throat_w"] + 1.0, p["slot_depth"] + 12, LATCH_FLANGE_T + 8, align=(CC, CC, CC))
        lf -= latch_plane(u) * Pos(0, t.Y, 0) * Cylinder(
            p["slot_end_r"], LATCH_FLANGE_T + 8, align=(CC, CC, CC))
    part += lf
    # bushing bores in the top land
    for u in G.PIN_U:
        part -= Pos(u, HH / 2 + MG / 2, FACE_N - FLANGE_T - 1) * Cylinder(
            hw.d("bushing")["od"] / 2, FLANGE_T + 4, align=(CC, CC, CMIN))
    # lightening pockets: the bond flange only needs full section at the seal rib and the bolt
    # band. Leaving it solid made a 7 kg socket frame, which is not a premium part.
    part -= rring(PW + 62, PH + 62, PR + 31, PW + 16, PH + 16, PR + 8,
                  FLANGE_T - 2.5, FACE_N - FLANGE_T - 0.5)
    # weep slots: water past the shut line leaves before it reaches the seal
    for su in (-1, 1):
        part -= Pos(su * (W / 2 - 40), -HH / 2 - MG / 2, FACE_N - FLANGE_T - 1) * Box(
            14, 6, FLANGE_T + 4, align=(CC, CC, CMIN))
    return _lab(part, "SOCKET_FRAME_6061")


def ledge_rail():
    """Machined 6061 ledge rail: the shelf and up-lip the module J-hooks hang on.

    Lip height to the land datum decides whether the module sits flush, so it is held to +/-0.1
    and dimensioned FROM THE LAND PLANE, not from the extrusion.
    """
    part = Pos(0, -HH / 2 - 4.0, -G.LEDGE_DROP) * Box(500.0, 50.0, 8.0, align=(CC, CMAX, CC))
    part += Pos(0, -HH / 2 - 46.0, -G.LEDGE_DROP - 21.0) * Box(
        500.0, 8.0, 18.0, align=(CC, CMAX, CC))
    for su in (-1, 1):                                    # drain slots through the shelf
        part -= Pos(su * 180.0, -HH / 2 - 25.0, -G.LEDGE_DROP) * Box(
            10, 60, 14, align=(CC, CC, CC))
    return _lab(part, "LEDGE_RAIL_6061")


def seal_land_path():
    """Closed, tangent-continuous wire the DD6139 is bent around, on the seal rib."""
    s = hw.d("bulb_seal")
    _ = s
    sk = rrect(PW + SEAL_MARGIN * 2, PH + SEAL_MARGIN * 2, G.K["corner_r"] + SEAL_MARGIN)
    return (Pos(0, 0, SEAL_LAND_N) * sk).wire()


def seal_bead(compressed: bool = False):
    return hw.seal_bead(seal_land_path(), up=(0, 0, 1), compressed=compressed)


def socket_assembly(state: str = "closed", with_seal: bool = True):
    """Shell-side socket: frame, ledge, seal, bushings, 2 latches, handle, splitter, 2 cables."""
    kids = [socket_frame(), ledge_rail()]
    if with_seal:
        kids.append(seal_bead(compressed=(state == "closed")))
    for u, kind in zip(G.PIN_U, ("round", "diamond")):
        b = Pos(u, HH / 2 + MG / 2, FACE_N) * hw.bushing()
        b.label = f"BUSHING_{kind}"
        kids.append(b)
    for u in G.LATCH_U:
        kids.append(latch_plane(u) * hw.rotary_latch(state))
        kids.append(hw.release_cable(cable_route(u)))
    split_pl = Plane(origin=Vector(0, G.LATCH_V - 30.0, G.LATCH_N - 40.0),
                     x_dir=Vector(1, 0, 0), z_dir=Vector(0, 1, 0))
    kids.append(split_pl * hw.cable_splitter())
    kids.append(Plane(origin=Vector(0, G.LATCH_V - 96.0, G.LATCH_N - 30.0),
                      x_dir=Vector(1, 0, 0), z_dir=Vector(0, 0, -1))
                * hw.release_handle(pulled=(state == "open")))
    for su, sv in ((-1, 1), (1, 1), (0, -1)):
        kids.append(Pos(su * 240.0, sv * (HH / 2 + MG / 2 + 8), FACE_N) * hw.compression_pad())
    c = Compound(children=kids)
    c.label = f"SOCKET:{state}"
    return c


# --------------------------------------------------------------------------------------
# module-side parts (identical on WINDOW / CAGE / TOOLBOX)
# --------------------------------------------------------------------------------------
def module_plug_frame():
    """Machined 6061 plug frame common to every module: flange, plug, hook and striker mounts."""
    r = G.K["corner_r"]
    clr = 6.0                                  # per-side plug clearance into the return lip
    part = rring(PW + 90 - G.SHUTLINE * 2, PH + 90 - G.SHUTLINE * 2, PR + 45,
                 W - 40, HH - 40, max(r - 20, 6), MODULE_FLANGE_T, -MODULE_FLANGE_T)
    part += rring(W - clr * 2, HH - clr * 2, max(r - clr, 4),
                  W - clr * 2 - 10, HH - clr * 2 - 10, max(r - clr - 5, 4),
                  G.PLUG_DEPTH - 20, -G.PLUG_DEPTH)
    part += Pos(0, G.LATCH_V - G.STRIKER_V_DROP - 3.0, (G.LATCH_N - 20.0) / 2) * Box(
        600.0, 6.0, 90.0, align=(CC, CC, CC))          # top return the striker brackets bolt to
    return _lab(part, "MODULE_PLUG_FRAME_6061")


def j_hook():
    """316 SS J-hook, 2 per module. Carries the whole module weight into the ledge lip in shear."""
    t = 6.0
    part = Box(60.0, t, 46.0, align=(CC, CC, CMAX))
    part += Pos(0, -22.0, -46.0) * Box(60.0, 44.0, 10.0, align=(CC, CMAX, CMAX))
    part += Pos(0, -44.0 + t / 2, -34.0) * Box(60.0, t, 24.0, align=(CC, CC, CMAX))
    for sx in (-1, 1):
        part -= Pos(sx * 20.0, 0, 1) * Rot(90, 0, 0) * Cylinder(3.4, t + 6, align=(CC, CC, CC))
    return _lab(part, "J_HOOK_316")


def module_interface(open_gap: float = 0.0):
    """Module-side hardware only (no payload): plug frame, 2 hooks, 2 striker bolts + brackets,
    2 locating pins, 2 ball plungers.

    ``open_gap`` (mm outward along +n) drives the module through its closing travel so the checker
    can prove hooks, pins, seal and latch engage in the right order.
    """
    kids = [module_plug_frame()]
    for su in (-1, 1):
        kids.append(Pos(su * 170.0, -HH / 2 - 14.0, -G.LEDGE_DROP + 34.0) * j_hook())
    for u in G.LATCH_U:
        sp = striker_plane(u)
        kids.append(sp * hw.striker_bolt())
        kids.append(sp * hw.striker_bracket())
    for u, kind in zip(G.PIN_U, ("round", "diamond")):
        kids.append(Plane(origin=Vector(u, HH / 2 + MG / 2, -14.0), x_dir=Vector(1, 0, 0),
                          z_dir=Vector(0, 0, -1)) * hw.locating_pin(kind))
    for su in (-1, 1):
        kids.append(Plane(origin=Vector(su * 280.0, 0, -40.0), x_dir=Vector(0, 1, 0),
                          z_dir=Vector(su, 0, 0)) * hw.ball_plunger())
    c = Compound(children=[Pos(0, 0, open_gap) * k for k in kids])
    c.label = f"MODULE_INTERFACE:gap{open_gap:.0f}"
    return c


def _lab(shape, name):
    shape.label = name
    return shape
