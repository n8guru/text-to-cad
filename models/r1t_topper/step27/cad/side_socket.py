"""Step 27 — the side socket and its mating module interface, as authoritative solids.

Built in the SOCKET LOCAL frame (x = u along the shell, y = v up the land lean, z = n outward
normal; n = 0 is the shell's outer skin), then placed into the vehicle frame by
``geom.socket_plane``. Every offset below is a border distance measured outward from the aperture
edge and comes from ``geom`` (MF_OUT, SEAL_OFF, RECESS_IN ...), so the frame, the module, the seal,
the shell cut and the checks cannot disagree.

Stack at the aperture border, outboard to inboard:
  module flange  n  -6 ..  0   (flush with the skin)      offsets -20 .. 44
  seal (comp.)   n -26 .. -6   DD6139 on a 3 mm rib        offset 32 +/- 5.6
  frame land     n -32 .. -26  (top-hat frame, 6061)       offsets 0 .. 52
  recess wall    n -32 ..  0                               offsets 48 .. 52
  bond flange    n -28.5 .. -22.5 on the shell inner skin  offsets 52 .. 82
  return lip     n -87 .. -32  (the aperture wall)         offsets 0 .. 8

Load path, so the latch selection is traceable:
  * module weight -> two 316 J-hooks -> the upturned fin at the inner end of the bottom lip.
  * outward pull  -> two Southco R4-30 rotors on R4-90-321-20 striker bars.
  * seal preload  -> DD6139 bulb at its designed compressed height; three limiter stacks stop the
                     flange at exactly that height, so the seal can never be over-crushed.
  * lateral       -> two ball plungers preloading the plug tube against the lip (anti-rattle).

The latch carrier lives INBOARD of the plug-tube end, inside the aperture footprint. That is the
only place a striker can escape along +n when the module tilts out: the previous layout put the
striker's removal path through the frame's own seal land.
"""
from __future__ import annotations

import math

from build123d import (
    Align, Box, Compound, Cylinder, Plane, Pos, Rot, Vector,
)

import geom as G
import hw

CC, CMIN, CMAX = Align.CENTER, Align.MIN, Align.MAX

W, HH = G.opening_wh()
AU, AV = W / 2, HH / 2
R0 = G.K["corner_r"]
FACE_N = G.FACE_N
LAND0, LAND1 = FACE_N - G.LAND_T, FACE_N
LIP0 = LAND0 - G.LIP_DEPTH
SEAL = hw.d("bulb_seal")
LATCH = hw.d("rotary_latch")

# latch station (socket-local mm); see module docstring
LATCH_N = -127.5                     # latch origin (panel face / hole-pattern centre) along n
LATCH_VP = AV - 19.0                 # panel face: the lifted striker head still clears the lip
STRIKER_OFF = LATCH["width"] / 2 + 5.0   # bar spans both side plates: 5 mm bracket side
PLATE_T = LATCH["panel_t"]
CARRIER_N = (-178.0, -172.0)         # crossbar joining the two latch plates
WEB_DU = (39.0, 45.0)                # web offset in u from the latch, beyond the striker arm
ARM_DU = (STRIKER_OFF + 6.0, STRIKER_OFF + 18.0)   # module striker arm, behind the bracket
BRACKET = {"n": 40.0, "v": 26.0, "t": 6.0}

# weight path
FIN_N = (LIP0 - 12.0, LIP0 - 6.0)    # upturned fin at the inner end of the bottom lip
FIN_TOP = -AV + 11.0                 # the hook seat (= the plug tube's inner bottom face)
HOOK_U = (-AU + 70.0, AU - 70.0)
HOOK_T = 6.0
CATCH_TRAVEL = 30.0                  # module slides out this far before the hook leg meets the fin
CATCH_DROP = 4.0                     # leg engagement below the fin top (lift 5 mm to clear it)

# limiter stacks: 6061 boss on the land + 7.4 mm UHMW pad, top = module flange back face
# on the straight runs of the seal path (it turns the corner at |u| > AU - R0), clear of the pins
LIMITERS = ((-165.0, AV + 13.5), (95.0, AV + 13.5), (0.0, -(AV + 13.5)))
BUSH_TOP = FACE_N + 4.0              # bushing flange top (flange sits on the land)
PIN_SEAT = BUSH_TOP + 1.25           # pin head seating face on the module boss, 1.25 above it
PLUNGER_N = -45.0
RELEASE_N = (-232.0, -226.0)         # release bracket plate (handle + splitter), inboard
BEND_R = 60.0                        # cable fillet radius, > Southco 50.8 minimum


def ring(e0, e1, n0, n1):
    return G.border_ring(AU, AV, R0, e0, e1, n0, n1)


def _lab(shape, name):
    shape.label = name
    return shape


# ------------------------------------------------------------------------------ frames
def latch_plane(u: float) -> Plane:
    """R4-30 placement: latch +X = +u (rotor axis), +Y = +n (mouth faces the module),
    +Z = -v (nose points down into the aperture, body hangs up towards the lip)."""
    return Plane(origin=Vector(u, LATCH_VP, LATCH_N), x_dir=Vector(1, 0, 0),
                 z_dir=Vector(0, -1, 0))


def striker_plane(u: float, state: str = "closed") -> Plane:
    """Striker-bolt plane: shoulder axis along -u through the rotor, bar at the throat root.
    x_dir = +n so the bracket's long side runs along the closing travel."""
    y, z = hw.bar_centre(state)
    lp = latch_plane(u)
    o = (lp * Pos(STRIKER_OFF, y, z)).position
    return Plane(origin=o, x_dir=Vector(0, 0, 1), z_dir=Vector(-1, 0, 0))


def bar_point(u: float, state: str = "closed") -> Vector:
    y, z = hw.bar_centre(state)
    return (latch_plane(u) * Pos(0, y, z)).position


# ------------------------------------------------------------------------------ socket parts
def latch_carrier():
    """Two latch plates, their webs back to the top lip, and the crossbar joining them."""
    parts = []
    for u in G.LATCH_U:
        bar = bar_point(u)
        n_back = bar.Z - BRACKET["n"] / 2 - 1.5          # plate stays behind the striker bracket
        plate = Pos(u + (WEB_DU[1] - 12.0) / 2, LATCH_VP - PLATE_T / 2,
                    (CARRIER_N[1] + n_back) / 2) * Box(
            WEB_DU[1] + 12.0, PLATE_T, n_back - CARRIER_N[1], align=(CC, CC, CC))
        plate -= Pos(u, LATCH_VP - PLATE_T / 2, LATCH_N - LATCH["hole_pitch"] / 2) * Rot(
            90, 0, 0) * Cylinder(LATCH["panel_hole_dia"] / 2, PLATE_T + 2, align=(CC, CC, CC))
        web = Pos(u + sum(WEB_DU) / 2, (LATCH_VP - PLATE_T + AV + G.LIP_T) / 2,
                  (CARRIER_N[1] + LIP0) / 2) * Box(
            WEB_DU[1] - WEB_DU[0], AV + G.LIP_T - (LATCH_VP - PLATE_T), LIP0 - CARRIER_N[1],
            align=(CC, CC, CC))
        parts += [plate, web]
    u0, u1 = G.LATCH_U[0] - 12.0, G.LATCH_U[1] + WEB_DU[1]
    parts.append(Pos((u0 + u1) / 2, LATCH_VP - PLATE_T / 2, sum(CARRIER_N) / 2) * Box(
        u1 - u0, PLATE_T, CARRIER_N[1] - CARRIER_N[0], align=(CC, CC, CC)))
    # release bracket: a plate in the u-v plane inboard of the crossbar, on two ribs
    parts.append(Pos(0, (LATCH_VP - PLATE_T + AV + 150.0) / 2, sum(RELEASE_N) / 2) * Box(
        140.0, AV + 150.0 - (LATCH_VP - PLATE_T), RELEASE_N[1] - RELEASE_N[0], align=(CC, CC, CC)))
    for su in (-1, 1):
        parts.append(Pos(su * 60.0, LATCH_VP - PLATE_T / 2, (RELEASE_N[1] + CARRIER_N[0]) / 2) * Box(
            6.0, PLATE_T, CARRIER_N[0] - RELEASE_N[1], align=(CC, CC, CC)))
    out = parts[0]
    for p in parts[1:]:
        out += p
    return out


def hook_fin():
    """Bottom-lip extension with the upturned fin the module J-hooks hang on."""
    u = AU - 25.0
    base = Pos(0, -AV - G.LIP_T / 2, (FIN_N[0] + LIP0) / 2) * Box(
        2 * u, G.LIP_T, LIP0 - FIN_N[0], align=(CC, CC, CC))
    fin = Pos(0, (-AV + FIN_TOP) / 2 - G.LIP_T / 2, sum(FIN_N) / 2) * Box(
        2 * u, FIN_TOP + AV + G.LIP_T, FIN_N[1] - FIN_N[0], align=(CC, CC, CC))
    return base + fin


def socket_frame():
    """Machined 6061-T6 top-hat frame: one program, one fixture, four off.

    Seal land + retention rib, recess wall (the reveal), bond flange on the shell inner skin,
    return lip, hook fin, latch carrier, bushing bores, limiter bosses, weep slots.
    """
    part = ring(0.0, G.RECESS_OUT, LAND0, LAND1)                       # seal land plate
    part += ring(G.RECESS_IN, G.RECESS_OUT, LAND0, 0.0)                 # recess wall
    part += ring(G.RECESS_OUT - 1.0, G.BOND_OUT, *G.BOND_N)             # bond flange
    part += ring(0.0, G.LIP_T, LIP0, LAND0)                             # return lip
    part += ring(G.SEAL_OFF - SEAL["rib_t"] / 2, G.SEAL_OFF + SEAL["rib_t"] / 2,
                 FACE_N, FACE_N + SEAL["rib_h"])                         # seal retention rib
    part += hook_fin()
    part += latch_carrier()
    lim = hw.d("compression_limiter")
    for u, v in LIMITERS:                                                # limiter bosses
        part += Pos(u, v, FACE_N) * Box(lim["pad_l"], lim["pad_w"],
                                        -G.MODULE_FLANGE_T - lim["pad_t"] - FACE_N,
                                        align=(CC, CC, CMIN))
    bush = hw.d("bushing")
    for u in G.PIN_U:                                                    # bushing bores
        part -= Pos(u, AV + G.PIN_OFF, LAND0 - 1) * Cylinder(
            bush["od"] / 2, G.LAND_T + 2, align=(CC, CC, CMIN))
    for su in (-1, 1):                                                   # weep slots
        part -= Pos(su * (AU - 30.0), -AV - (G.SEAL_OFF + G.RECESS_IN) / 2, LAND0 - 1) * Box(
            14.0, 6.0, G.LAND_T + 2, align=(CC, CC, CMIN))
    return _lab(part, "SOCKET_FRAME_6061")


def seal_land_path():
    sk = G.rrect(2 * (AU + G.SEAL_OFF), 2 * (AV + G.SEAL_OFF), R0 + G.SEAL_OFF)
    return (Pos(0, 0, FACE_N) * sk).wire()


def seal_bead(compressed: bool = True):
    return hw.seal_bead(seal_land_path(), up=(0, 0, 1), compressed=compressed)


def bushing_at(u: float, kind: str):
    """JBHC10-15, flange on the land's top face, body pressed down through the land."""
    b = Plane(origin=Vector(u, AV + G.PIN_OFF, BUSH_TOP), x_dir=Vector(1, 0, 0),
              z_dir=Vector(0, 0, -1)) * hw.bushing()
    return _lab(b, f"BUSHING_{kind}")


def cable_route(u: float):
    """Latch cable abutment -> inboard -> up past the aperture top -> splitter side port."""
    lp = latch_plane(u)
    start = (lp * Pos(0, -LATCH["overall_l"] / 2 - 2.0, hw.PAWL_Z)).position
    side = -1 if u < 0 else 1
    n_run = RELEASE_N[0] - 24.0
    p1 = Vector(start.X, start.Y, n_run)
    p2 = Vector(start.X, SPLIT_V, n_run)
    p3 = Vector(side * 40.0, SPLIT_V, n_run)
    return [tuple(start), tuple(p1), tuple(p2), tuple(p3)]


SPLIT_V = AV + 125.0


def splitter_plane():
    """AC-05-301-11 on the release bracket, latch ports along +/-u, handle port down (-v)."""
    return Plane(origin=Vector(0, SPLIT_V, RELEASE_N[0] - 8.0), x_dir=Vector(0, 1, 0),
                 z_dir=Vector(0, 0, -1))


def handle_plane():
    """AC-75-101-11 paddle on the bracket's inboard face, paddle facing the interior (-n)."""
    return Plane(origin=Vector(0, AV + 45.0, RELEASE_N[0] - 18.0), x_dir=Vector(1, 0, 0),
                 z_dir=Vector(0, 0, -1))


def socket_assembly(state: str = "closed", with_seal: bool = True):
    """Shell-side socket: frame, seal, bushings, 2 latches, 2 cables, splitter, handle, limiters."""
    kids = [socket_frame()]
    if with_seal:
        kids.append(seal_bead(compressed=(state == "closed")))
    for u, kind in zip(G.PIN_U, ("round", "diamond")):
        kids.append(bushing_at(u, kind))
    for u in G.LATCH_U:
        kids.append(latch_plane(u) * hw.rotary_latch("closed" if state == "closed" else "open"))
        kids.append(hw.release_cable(cable_route(u), BEND_R))
    kids.append(splitter_plane() * hw.cable_splitter())
    kids.append(handle_plane() * hw.release_handle(pulled=(state == "open")))
    lim = hw.d("compression_limiter")
    for u, v in LIMITERS:
        kids.append(Pos(u, v, -G.MODULE_FLANGE_T - lim["pad_t"]) * hw.compression_pad())
    c = Compound(children=kids)
    c.label = f"SOCKET:{state}"
    return c


# ------------------------------------------------------------------------------ module side
def module_plug_frame():
    """Machined 6061 plug frame common to every module: flange, plug tube, pin bosses, arms."""
    part = ring(G.MF_IN, G.MF_OUT, -G.MODULE_FLANGE_T, 0.0)            # flange
    part += ring(-G.PLUG_CLR - 5.0, -G.PLUG_CLR, -G.PLUG_DEPTH,
                 -G.MODULE_FLANGE_T + 0.01)                              # plug tube
    for u in G.PIN_U:                                                    # locating-pin bosses
        top = -G.MODULE_FLANGE_T
        part += Pos(u, AV + G.PIN_OFF, PIN_SEAT) * Cylinder(9.0, top - PIN_SEAT, align=(CC, CC, CMIN))
        pin = hw.d("locating_pin_round")
        part -= Pos(u, AV + G.PIN_OFF, PIN_SEAT - 0.5) * Cylinder(
            pin["shank_dia"] / 2, pin["shank_len"] + 0.5, align=(CC, CC, CMIN))  # press bore
    for u in G.LATCH_U:                                                  # striker arms
        bar = bar_point(u)
        v0, v1 = bar.Y - BRACKET["v"] / 2, AV - G.PLUG_CLR
        n0 = bar.Z - BRACKET["n"] / 2
        arm = Pos(u + sum(ARM_DU) / 2, (v0 + v1) / 2, (n0 - G.PLUG_DEPTH) / 2) * Box(
            ARM_DU[1] - ARM_DU[0], v1 - v0, -G.PLUG_DEPTH - n0, align=(CC, CC, CC))
        part += arm
        part -= striker_plane(u) * Cylinder(5.0, 20.0, align=(CC, CC, CMAX))   # M10 tapped
    for su in (-1, 1):                                                   # plunger bosses
        part += Pos(su * (AU - G.PLUG_CLR - 10.0), 0, PLUNGER_N) * Box(
            10.0, 24.0, 24.0, align=(CC, CC, CC))
        part -= Pos(su * (AU - 12.0), 0, PLUNGER_N) * Rot(0, 90, 0) * Cylinder(
            4.0, 22.0, align=(CC, CC, CC))                                # M8 tapped
    return _lab(part, "MODULE_PLUG_FRAME_6061")


def j_hook(u: float):
    """316 SS J-hook, 6 mm plate: tab on the tube floor, bridge riding on the fin, safety leg.

    Shut, the bridge rests on the fin top (the weight path) and the leg hangs CATCH_TRAVEL inboard
    of the fin. Unlatched, the module slides out until the leg meets the fin and is caught; it is
    then lifted CATCH_DROP + 1 mm and withdrawn. A leg tight behind the fin (the previous design)
    deadlocks: the striker cannot leave the rotor without the outward travel the leg forbids.
    """
    t = HOOK_T
    v_seat = FIN_TOP
    tab = Pos(u, v_seat + t / 2, -62.0) * Box(40.0, t, 40.0, align=(CC, CC, CC))
    n_end = FIN_N[0] - CATCH_TRAVEL - t
    bridge = Pos(u, v_seat + t / 2, (-G.PLUG_DEPTH + 3.0 + n_end) / 2) * Box(
        40.0, t, -G.PLUG_DEPTH + 3.0 - n_end, align=(CC, CC, CC))
    leg = Pos(u, (v_seat + t + v_seat - CATCH_DROP) / 2, n_end + t / 2) * Box(
        40.0, t + CATCH_DROP, t, align=(CC, CC, CC))
    part = tab + bridge + leg
    for du in (-10.0, 10.0):
        part -= Pos(u + du, v_seat + t / 2, -62.0) * Rot(90, 0, 0) * Cylinder(
            3.3, t + 4, align=(CC, CC, CC))
    return _lab(part, "J_HOOK_316")


def striker_bracket_at(u: float, state: str = "closed"):
    """CUSTOM slotted 316 bracket (DWG-27-004), +/-3 mm fit-up along n and v."""
    b = BRACKET
    part = Box(b["n"], b["v"], b["t"], align=(CC, CC, CMAX))
    part -= Pos(0, 0, 1) * Box(16.6, 10.6, b["t"] + 2, align=(CC, CC, CMAX))    # +/-3 mm slot
    part.label = "STRIKER_BRACKET_custom"
    return striker_plane(u, state) * part


def module_interface(open_gap: float = 0.0):
    """Module-side hardware only (no payload): plug frame, 2 J-hooks, 2 strikers + brackets,
    2 locating pins, 2 ball plungers.

    ``open_gap`` (mm outward along +n) drives the module through its closing travel so the checker
    can prove hooks, pins, seal and latch engage in the right order.
    """
    kids = [module_plug_frame()]
    for u in HOOK_U:
        kids.append(j_hook(u))
    for u in G.LATCH_U:
        sp = striker_plane(u)
        kids.append(sp * hw.striker_bolt())
        kids.append(striker_bracket_at(u))
    for u, kind in zip(G.PIN_U, ("round", "diamond")):
        kids.append(Plane(origin=Vector(u, AV + G.PIN_OFF, PIN_SEAT),
                          x_dir=Vector(1, 0, 0), z_dir=Vector(0, 0, -1))
                    * hw.locating_pin(kind))
    bp = hw.d("ball_plunger")
    for su in (-1, 1):
        # nose at the lip face: the ball is shown pushed flush, i.e. at its working preload
        tip = su * AU
        kids.append(Plane(origin=Vector(tip - su * (bp["ball_dia"] / 2 + bp["extension"]), 0,
                                        PLUNGER_N),
                          x_dir=Vector(0, 1, 0), z_dir=Vector(su, 0, 0)) * hw.ball_plunger())
    c = Compound(children=[Pos(0, 0, open_gap) * k for k in kids])
    c.label = f"MODULE_INTERFACE:gap{open_gap:.0f}"
    return c


# ------------------------------------------------------------------------------ payloads
def payload(kind: str):
    """What makes a module a WINDOW, CAGE or TOOLBOX. Everything else is module_interface()."""
    if kind == "WINDOW":
        pane = Pos(0, 0, -G.MODULE_FLANGE_T - 5.0) * _plate(AU - G.PLUG_CLR - 5.5,
                                                           AV - G.PLUG_CLR - 5.5, 5.0)
        return [_lab(pane, "WINDOW_PANE_PC")]
    if kind == "CAGE":
        out = []
        n = int((W - 60.0) // 38.0) + 1
        span = AU - 50.0                  # bar ends stay on the straight run of the R34 tube corners
        for k in range(n):
            u = -span + k * 2 * span / (n - 1)
            out.append(_lab(Pos(u, 0, -14.0) * Rot(90, 0, 0) * Cylinder(
                5.0, HH - 2 * G.PLUG_CLR - 10.0, align=(CC, CC, CC)), "CAGE_BAR_316"))
        for v in (-AV / 2, AV / 2):
            out.append(_lab(Pos(0, v, -21.0) * Box(W - 2 * G.PLUG_CLR - 10.0, 8.0, 4.0,
                                                   align=(CC, CC, CC)), "CAGE_RAIL_316"))
        return out
    if kind == "TOOLBOX":
        door = Pos(0, 0, -G.MODULE_FLANGE_T) * _plate(AU + G.MF_IN - 1.0, AV + G.MF_IN - 1.0,
                                                      G.MODULE_FLANGE_T)
        tub_v0, tub_v1 = FIN_TOP + HOOK_T + 1.0, LATCH_VP - 40.0
        tw = W - 2 * (G.PLUG_CLR + 29.0)                  # inside the plunger bosses and the R34 tube corners
        tub = Pos(0, (tub_v0 + tub_v1) / 2, -G.MODULE_FLANGE_T - 150.0) * Box(
            tw, tub_v1 - tub_v0, 290.0, align=(CC, CC, CC))
        tub -= Pos(0, (tub_v0 + tub_v1) / 2, -G.MODULE_FLANGE_T - 150.0 + 2.0) * Box(
            tw - 6.0, tub_v1 - tub_v0 - 6.0, 290.0, align=(CC, CC, CC))
        return [_lab(door, "TOOLBOX_DOOR_CARBON"), _lab(tub, "TOOLBOX_TUB_ABS")]
    raise ValueError(kind)


def _plate(hu, hv, t):
    from build123d import extrude
    return extrude(G.rrect(2 * hu, 2 * hv, max(R0 - 10.0, 3.0)), amount=t)
