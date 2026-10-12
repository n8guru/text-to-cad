"""Topper-to-truck attachment (Step 27 rev 11): four PORT LATCH FEET (PLF), Rivian-crossbar style.

WHY (operator card 2081357): the Rivian crossbar does not bolt to the bed accessory port with a stud
and nut. Each crossbar END is a foot with a hinged PADDLE latch (Owner's Guide 2022-10-17 p.152-154):
lift the paddle, set the foot into the port (click 1: the foot is caught on the port's cleat / latch
pin), push the paddle down (click 2: clamped); a key lock cylinder under the paddle locks it; the
latch can be tuned. Step30 represents the source-visible bridge as one continuous reference bar
and wraps it with two C-jaws. This is OUR provisional crossbar-style capture concept, not an OEM
reverse-engineering claim. Bridge axis, dimensions and 25 mm jaw spacing remain assumptions.
Sources and dates: step27/research/PORT_MECHANISM_SOURCES.md and STEP30_MOUNTING.md.

NOTHING about the port interior or the Rivian foot is published. Every dimension below that touches
the port (recess, pin pair, depth) or the foot (hook, paddle, lock) is PROVISIONAL, comes from
blender/params.json ``mount`` and is flagged by the OPEN check ``plf_port_internals_P-CAL-01b``.

Station frame (local): x along the rail, u OUTBOARD (the +Y side for the driver stations, a 180 deg
rotation about Z for the passenger stations, so the four feet are ONE part), z up from the rail-cap
top. Parts of one station (inboard to outboard):

    PLF_PADDLE_6061          hinged drop-down flap on the INBOARD face (axis // x). Closed it covers
                             the lock cylinder and the tuning screw; opened 82 deg it lies out over
                             the bed side, clear of the socket frames (ceiling z 66 above the rail).
    PLF_LOCK_CYLINDER_COMPX  purchased cam lock, axis // u, face INBOARD, under the paddle.
    PLF_BODY_6061            machined foot: head (in a notch of the base rail), stem (through the
                             foot pocket and into the port recess), seat flange (z 0..4, bears on
                             the rail cap and is the pad's compression STOP), two hinge ears.
    PLF_HOOK_SLIDER_17_4PH   two open-sided C-jaws in a cross-slot: upper and lower lips wrap
                             around the reference bridge; retraction opens the capture throat.
                             Kinematic law only: dwell closed .. stage1, then release. The cam
                             linkage and preload remain OPEN, not secretly claimed engineered.
    PLF_HINGE_PIN, PLF_DETENT_PLUNGER (2 dimples: closed / stage 1), PLF_TUNE_SCREW (closed
    stop = latch tuning), PLF_RAIL_SCREW x2 + PLF_SHIM x2 (shop fit-up of the base rail to the body).

Load path at stage 2 (closed), all metal: port pin -> hook tooth -> slider bar -> slot floor ->
body -> 2 x M6 (in shear, 1 mm shim-able) -> 6061 base rail strip -> bond line -> carbon foot. The
EPDM pad (33 % compressed) is NOT in the clamp path: the seat flange, not the pad, sets the height.

Everything sized here is checked by checks_step27.check_mounting / check_plf_*; none of it is a
fitment, structural or sealing result.
"""
from __future__ import annotations

import math
from functools import lru_cache

from build123d import Align, Box, Cylinder, Location, Pos, Rot, Sphere, extrude

import geom as G

CC, CMIN, CMAX = Align.CENTER, Align.MIN, Align.MAX
BR = G.BR
T = G.T
MT = G.MT
RAIL_X = (G.S["x0"] + 60.0, G.S["x1"] - 130.0)   # clear of the front roll and rear wrap
# (name, x, side) - side +1 = driver (+Y). Well clear opening 120 x 70.
WELLS = (("WELL_GT_L", 60.0, 1), ("WELL_GT_R", 60.0, -1), ("WELL_TG", 1300.0, 1))
WELL = {"lx": 120.0, "ly": 70.0, "y": 700.0}

# ---------------------------------------------------------------- derived heights, not typed
FOOT_TOP = G.WALL                                 # rail underside / foot top
RAIL_TOP = G.WALL + BR["h"]
PAD_C = MT["pad_comp"]                            # pad compressed = foot underside = seat-flange top
FLANGE_T = MT["flange_t"]
POCKET_X = MT["stem_x"] + 2 * MT["pocket_clear"]
POCKET_U0 = MT["stem_u0"] - MT["pocket_clear"]
POCKET_U1 = MT["stem_u1"] + MT["pocket_clear"]
NOTCH_X = MT["head_x"] + 2 * MT["notch_clear_x"]
NOTCH_WALL_U = MT["head_u1"] + MT["notch_shim_nom"]     # rail strip inboard face, local u
HEAD_UNDER_GAP = MT["head_z0"] - FOOT_TOP
# paddle states (deg). Stage 1 = "caught / halfway": hooks under the pins, lock face reachable.
STAGE1_DEG = 68.0
OPEN_DEG = 82.0
# cam law: paddle angle -> slider retraction along u (mm, 0 = fully advanced = clamped). Dwell
# from closed to stage 1 (hooks stay under the pins), then the hooks retract by the full travel
# between stage 1 and open. PROVISIONAL: the drive link is not drawn.
CAM_LAW = ((0.0, 0.0), (STAGE1_DEG, 0.45), (OPEN_DEG, MT["slider_travel"]))
SWEEP_DEG = tuple(float(a) for a in range(0, 81, 5)) + (STAGE1_DEG, OPEN_DEG)


def cam_retract(theta: float) -> float:
    """Slider retraction (mm, along -u) at paddle angle theta (deg), piecewise linear."""
    pts = CAM_LAW
    if theta <= pts[0][0]:
        return pts[0][1]
    for (a0, d0), (a1, d1) in zip(pts, pts[1:]):
        if theta <= a1:
            return d0 + (d1 - d0) * (theta - a0) / (a1 - a0)
    return pts[-1][1]


def stations():
    """(x, y) of the four port stations, vehicle frame."""
    return [(x, sy * y) for x, y in T["bed_ports"] for sy in (1, -1)]


def station_loc(x, y):
    """Local -> vehicle: origin at the port centre on the rail-cap top; u outboard."""
    return Location((x, y, 0)) * Rot(0, 0, 0 if y > 0 else 180)


# ---------------------------------------------------------------- local-frame helpers
def _box(x0, x1, u0, u1, z0, z1):
    return Pos((x0 + x1) / 2, (u0 + u1) / 2, z0) * Box(x1 - x0, u1 - u0, z1 - z0, align=(CC, CC, CMIN))


def _rrbox(x0, x1, u0, u1, z0, z1, r):
    return Pos((x0 + x1) / 2, (u0 + u1) / 2, z0) * extrude(G.rrect(x1 - x0, u1 - u0, r), amount=z1 - z0)


def _cyl_u(x, z, d, u0, u1):
    """Cylinder with its axis along u (local +Y), from u0 to u1."""
    return Pos(x, (u0 + u1) / 2, z) * Rot(X=90) * Cylinder(d / 2, u1 - u0)


def _cyl_x(u, z, d, x0, x1):
    return Pos((x0 + x1) / 2, u, z) * Rot(Y=90) * Cylinder(d / 2, x1 - x0)


def _cyl_z(x, u, d, z0, z1):
    return Pos(x, u, z0) * Cylinder(d / 2, z1 - z0, align=(CC, CC, CMIN))


def _vslot_u(x, z, d, dz, u0, u1):
    """Obround hole (diameter d, vertical float +/-dz) along u."""
    s = _cyl_u(x, z - dz, d, u0, u1) + _cyl_u(x, z + dz, d, u0, u1)
    s += _box(x - d / 2, x + d / 2, u0, u1, z - dz, z + dz)
    return s


# ---------------------------------------------------------------- the port (REFERENCE, PROVISIONAL)
PORT_X, PORT_U, PORT_R, PORT_DEPTH = MT["port_x"], MT["port_u"], MT["port_r"], MT["port_depth"]
PIN_XS = (-MT["pin_pitch"] / 2, MT["pin_pitch"] / 2)


def port_recess_local():
    """The port recess as a SOLID (the void in the rail cap), local frame. Reference only."""
    return _rrbox(-PORT_X / 2, PORT_X / 2, -PORT_U / 2, PORT_U / 2, -PORT_DEPTH, 0.0, PORT_R)


def port_pins_local():
    """One continuous provisional bridge with two jaw bearing zones.

    Weistec installation imagery and TWRAPS wall surrogate show a bridge/bar,
    not two isolated studs. Its axis and ALL mating dimensions are provisional.
    The historical function name is retained for callers; no OEM geometry claim.
    """
    half = (MT["pin_pitch"] + MT["pin_len"]) / 2
    bridge = _cyl_x(MT["pin_u"], MT["pin_z"], MT["pin_d"], -half, half)
    bridge.label = "PORT_REF_BRIDGE_PROVISIONAL"
    return [bridge]


def port_reference(x, y):
    """(recess, [pin A, pin B]) in the vehicle frame for the station at (x, y)."""
    loc = station_loc(x, y)
    rec = loc * port_recess_local()
    rec.label = "PORT_REF_RECESS"
    return rec, [loc * p for p in port_pins_local()]


# ---------------------------------------------------------------- the machined foot (local frame)
def _ears_x():
    return [(MT["ear_x0"], MT["ear_x1"]), (-MT["ear_x1"], -MT["ear_x0"])]


@lru_cache(maxsize=1)
def body_local():
    sb = MT["stem_bottom"]
    stem = _rrbox(-MT["stem_x"] / 2, MT["stem_x"] / 2, MT["stem_u0"], MT["stem_u1"], sb,
                  MT["head_z0"] + 2.0, MT["stem_r"])
    head = _rrbox(-MT["head_x"] / 2, MT["head_x"] / 2, MT["head_u0"], MT["head_u1"], MT["head_z0"],
                  MT["head_top"], 2.0)
    flange = _rrbox(-MT["flange_x"] / 2, MT["flange_x"] / 2, MT["flange_u0"], MT["flange_u1"], 0.0,
                    FLANGE_T, MT["flange_r"])
    b = stem + head + flange
    for x0, x1 in _ears_x():
        b += _box(x0, x1, MT["ear_u0"], MT["head_u0"] + 0.5, MT["head_z0"], MT["ear_z1"])
    # hook slider cross-slot and the two vertical pin channels (the stem drops past the pins)
    b -= _box(-MT["slot_x"] / 2, MT["slot_x"] / 2, MT["stem_u0"] - 1, MT["stem_u1"] + 1,
              MT["slot_z0"], MT["pin_z"] + MT["pin_d"] / 2 + 3.0)
    # Continuous bridge needs a continuous downward-open entry channel; two
    # disconnected pin slots would obstruct lowering the foot onto that bar.
    bridge_half = (MT["pin_pitch"] + MT["pin_len"]) / 2
    b -= _box(-bridge_half - 0.5, bridge_half + 0.5, MT["chan_u0"], MT["chan_u1"],
              sb - 1, MT["chan_top"])
    # lock bore (axis // u from the inboard face) and the cam pocket behind it
    u0 = MT["head_u0"]
    b -= _cyl_u(0.0, MT["lock_z"], MT["lock_bore"], u0 - 1, u0 + MT["lock_len"] + 0.3)
    b -= _cyl_u(0.0, MT["lock_z"], MT["lock_cam_pocket_d"], u0 + MT["lock_len"] - 0.5,
                u0 + MT["lock_len"] + 2.3)
    # rail screws: obround through-holes (vertical float) with a counterbore from the inboard face
    for sx in (-1, 1):
        x = sx * MT["rail_screw_x"]
        b -= _vslot_u(x, MT["rail_screw_z"], 6.6, MT["rail_slot_z"], u0 - 1, MT["head_u1"] + 1)
        b -= _vslot_u(x, MT["rail_screw_z"], MT["rail_cbore_d"], MT["rail_slot_z"], u0 - 1,
                      u0 + MT["rail_cbore_depth"])
    # tuning screw: M6 tapped, from the inboard face (tap drill 5.0), x < 0 side
    b -= _cyl_u(MT["tune_x"], MT["tune_z"], 5.0, u0 - 1, u0 + 14.0)
    # hinge pin through both ears; detent plunger bore (M8 tap drill 6.8) in the +x ear
    hu, hz = MT["hinge_u"], MT["hinge_z"]
    b -= _cyl_x(hu, hz, MT["hinge_pin_d"], -MT["ear_x1"] - 1, MT["ear_x1"] + 1)
    b -= _cyl_x(hu, hz + MT["detent_r"], 6.8, MT["ear_x1"] - MT["detent_len"], MT["ear_x1"] + 1)
    b.label = "PLF_BODY_6061"
    return b


# ---------------------------------------------------------------- paddle, slider, purchased parts
HU, HZ = MT["hinge_u"], MT["hinge_z"]
PLUNGER_X0 = MT["ear_x1"] - MT["detent_len"]                  # plunger body inner end (x)
PLUNGER_BALL_X = PLUNGER_X0 + 0.75                            # ball centre (1.5 mm extension)
BALL_R = 2.25
DIMPLE_DEG = (90.0, 90.0 - STAGE1_DEG)                        # dimples on the knuckle end: closed, stage 1
# (the open position has no dimple: it is the cam-link over-travel limit, 82 deg, not drawn)


@lru_cache(maxsize=1)
def paddle_closed_local():
    px = MT["paddle_x"] / 2
    plate = _box(-px, px, HU - MT["paddle_t"] / 2, HU + MT["paddle_t"] / 2, HZ, HZ + MT["paddle_h"])
    knuckle = _cyl_x(HU, HZ, MT["knuckle_d"], -px, px)
    p = plate + knuckle
    p -= _cyl_x(HU, HZ, MT["hinge_pin_d"] + 0.2, -px - 1, px + 1)
    # detent dimples on the +x knuckle end, r = detent_r from the hinge axis
    for a in DIMPLE_DEG:
        ar = math.radians(a)
        p -= Pos(PLUNGER_BALL_X, HU + MT["detent_r"] * math.cos(ar), HZ + MT["detent_r"] * math.sin(ar)) \
            * Sphere(BALL_R + 0.05)
    p.label = "PLF_PADDLE_6061"
    return p


def rot_about_hinge(shape, theta):
    """Rotate about the hinge axis (// local x); + = the paddle top swings INBOARD (toward -u)."""
    return Pos(0, HU, HZ) * Rot(X=theta) * Pos(0, -HU, -HZ) * shape


def paddle_local(theta=0.0):
    p = paddle_closed_local()
    q = rot_about_hinge(p, theta) if theta else Pos(0, 0, 0) * p
    q.label = "PLF_PADDLE_6061"
    return q


def slider_closed_local():
    """Two C-jaws wrap the provisional bridge, driven by the existing slider.

    Step30 replaces flat teeth with explicit open-sided wrap geometry. The lower
    lip retains the original tangent bearing face; an upper lip and inboard web
    prevent the old flat-tooth depiction being mistaken for a threaded adapter.
    All dimensions remain design assumptions, NOT a reverse-engineered OEM foot.
    """
    s = _box(-MT["bar_x"] / 2, MT["bar_x"] / 2, MT["bar_u0"], MT["bar_u1"], MT["bar_z0"], MT["bar_z1"])
    for px in PIN_XS:
        x0, x1 = px - MT["tooth_w"] / 2, px + MT["tooth_w"] / 2
        jaw = _box(x0, x1, MT["bar_u0"], MT["tooth_tip"], MT["bar_z0"], MT["pin_z"] + MT["pin_d"] / 2 + 3.0)
        # Flat-sided throat open toward +u; 0.5 mm upper clearance, bottom
        # tangent to the reference bridge. Retraction lets the pin leave the mouth.
        jaw -= _box(x0 - 1, x1 + 1, MT["pin_u"] - MT["pin_d"] / 2 - 0.5,
                    MT["tooth_tip"] + 1, MT["pin_z"] - MT["pin_d"] / 2,
                    MT["pin_z"] + MT["pin_d"] / 2 + 0.5)
        s += jaw
    s.label = "PLF_HOOK_SLIDER_17_4PH"
    return s


def slider_local(theta=0.0):
    s = Pos(0, -cam_retract(theta), 0) * slider_closed_local()
    s.label = "PLF_HOOK_SLIDER_17_4PH"
    return s


def lock_local(locked=True):
    """CompX C8053 cam lock envelope: flange on the inboard face, body in the bore, cam behind."""
    u0 = MT["head_u0"]
    fl = _cyl_u(0.0, MT["lock_z"], MT["lock_flange_d"], u0 - MT["lock_flange_t"], u0)
    body = _cyl_u(0.0, MT["lock_z"], MT["lock_d"], u0, u0 + MT["lock_len"])
    cu0 = u0 + MT["lock_len"]
    if locked:      # blade across the keeper (horizontal), unlocked = vertical
        cam = _box(-MT["lock_cam_x"] / 2, MT["lock_cam_x"] / 2, cu0, cu0 + MT["lock_cam_t"],
                   MT["lock_z"] - 1.5, MT["lock_z"] + 1.5)
    else:
        cam = _box(-1.5, 1.5, cu0, cu0 + MT["lock_cam_t"], MT["lock_z"] - MT["lock_cam_x"] / 2,
                   MT["lock_z"] + MT["lock_cam_x"] / 2)
    lk = fl + body + cam
    lk.label = "PLF_LOCK_CYLINDER_COMPX"
    return lk


def key_envelope_local():
    """Key shank swept into the lock face (a reach test, not a part): dia 8 x 32 along -u."""
    u0 = MT["head_u0"] - MT["lock_flange_t"]
    return _cyl_u(0.0, MT["lock_z"], 8.0, u0 - 32.0, u0)


def hinge_pin_local():
    p = _cyl_x(HU, HZ, MT["hinge_pin_d"], -MT["ear_x1"], MT["ear_x1"])
    p.label = "PLF_HINGE_PIN_5x76_A4"
    return p


def plunger_local():
    body = _cyl_x(HU, HZ + MT["detent_r"], 6.8, PLUNGER_X0, MT["ear_x1"])    # shown at the thread minor
    ball = Pos(PLUNGER_BALL_X, HU, HZ + MT["detent_r"]) * Sphere(BALL_R)
    p = body + ball
    p.label = "PLF_DETENT_PLUNGER_M8"
    return p


def tune_screw_local():
    u0 = MT["head_u0"]
    # M6 x 20 ISO 4026 flat-point set screw (tap minor 5.0): tip on the closed paddle's inner face
    tip = HU + MT["paddle_t"] / 2
    s = _cyl_u(MT["tune_x"], MT["tune_z"], 5.0, tip, tip + MT["tune_len"])
    s.label = "PLF_TUNE_SCREW_M6x20_A4"
    return s


def rail_screws_local():
    out = []
    seat = MT["head_u0"] + MT["rail_cbore_depth"]
    for sx in (-1, 1):
        x = sx * MT["rail_screw_x"]
        head = _cyl_u(x, MT["rail_screw_z"], 10.0, seat - 6.0, seat)
        shank = _cyl_u(x, MT["rail_screw_z"], 5.0, seat, seat + MT["rail_screw_len"])
        s = head + shank
        s.label = "PLF_RAIL_SCREW_M6x30_A4"
        out.append(s)
    return out


def shims_local():
    """Two 1.0 mm 316 plates between the head's outboard face and the rail strip (0..4 mm kit)."""
    out = []
    n = int(round(MT["notch_shim_nom"] / MT["shim_t"]))
    for k in range(n):
        u0 = MT["head_u1"] + k * MT["shim_t"]
        s = _box(-21.0, 21.0, u0, u0 + MT["shim_t"], MT["rail_screw_z"] - 7.0, MT["rail_screw_z"] + 7.0)
        for sx in (-1, 1):
            s -= _vslot_u(sx * MT["rail_screw_x"], MT["rail_screw_z"], 6.6, MT["rail_slot_z"], u0 - 1,
                          u0 + MT["shim_t"] + 1)
        s.label = "PLF_SHIM_316_1p0"
        out.append(s)
    return out


# ---------------------------------------------------------------- placed station parts
def _place(shape, loc, label=None):
    s = loc * shape
    s.label = label or shape.label
    return s


def port_station(x, y, theta=0.0):
    """Every part of the foot at station (x, y), vehicle frame, paddle at ``theta`` deg."""
    loc = station_loc(x, y)
    parts = [body_local(), paddle_local(theta), slider_local(theta), lock_local(True),
             hinge_pin_local(), plunger_local(), tune_screw_local()] + rail_screws_local() + shims_local()
    return [_place(p, loc) for p in parts]


def port_stations(theta=0.0):
    out = []
    for x, y in stations():
        out += port_station(x, y, theta)
    return out


def port_adapters():
    """Back-compat name used by assembly/checks: every part of every station."""
    return port_stations()


# ---------------------------------------------------------------- cut-outs (shell foot, rail, pad)
def well_cut(x, sy):
    return Pos(x, sy * WELL["y"], -1.0) * Box(WELL["lx"], WELL["ly"], G.WALL + BR["h"] + 10.0,
                                             align=(CC, CC, CMIN))


def foot_pocket(x, y):
    """Through-pocket in the shell foot for the stem (the seat flange is below the foot, z 0..4)."""
    loc = station_loc(x, y)
    return loc * _rrbox(-POCKET_X / 2, POCKET_X / 2, POCKET_U0, POCKET_U1, -1.0, FOOT_TOP + 2.0,
                        MT["pocket_r"])


def flange_pad_cut(x, y):
    """The pad strip is cut round the seat flange (it occupies the pad plane, z 0..4)."""
    loc = station_loc(x, y)
    return loc * _rrbox(-MT["flange_x"] / 2 - 2.0, MT["flange_x"] / 2 + 2.0, MT["flange_u0"] - 2.0,
                        MT["flange_u1"] + 2.0, -1.0, PAD_C + 0.5, MT["flange_r"] + 2.0)


def pad_relief():
    """The foot underside is relieved PAD_C over the pad footprint (the pad replaces it)."""
    B, w = G.S["base_half_w"], G.S["foot_w"]
    xa, xb = G.S["x0"] - 5.0, G.T["rail_flat_end_x"] + 5.0
    out = []
    for sy in (-1, 1):
        y0 = B - w - 15.0
        out.append(Pos((xa + xb) / 2, sy * (y0 + B + 15.0) / 2, -1.0) * Box(
            xb - xa, B + 15.0 - y0, PAD_C + 1.0, align=(CC, CC, CMIN)))
    return out


def foot_cuts():
    """Everything the shell must lose for the attachment: pad relief, stem pockets, wells."""
    cuts = pad_relief()
    cuts += [foot_pocket(x, y) for x, y in stations()]
    cuts += [well_cut(x, side) for _, x, side in WELLS]
    return cuts


# ---------------------------------------------------------------- custom parts: rail, pad
def _rail_solid(sy):
    y0, y1 = BR["y_in"], BR["y_out"]
    return Pos((RAIL_X[0] + RAIL_X[1]) / 2, sy * (y0 + y1) / 2, FOOT_TOP) * Box(
        RAIL_X[1] - RAIL_X[0], y1 - y0, BR["h"], align=(CC, CC, CMIN))


def rail_notch(x, y):
    """U-notch in the rail at a station, open to the inboard edge (paddle bay + head pocket)."""
    loc = station_loc(x, y)
    u_in = -(abs(y) - (BR["y_in"] - 1.0))
    return loc * _box(-NOTCH_X / 2, NOTCH_X / 2, u_in, NOTCH_WALL_U, FOOT_TOP - 1.0, RAIL_TOP + 1.0)


def rail_taps(x, y):
    """Two M6 tapped blind holes (tap drill 5.0) in the strip's inboard face, for the rail screws."""
    loc = station_loc(x, y)
    t = None
    for sx in (-1, 1):
        h = _cyl_u(sx * MT["rail_screw_x"], MT["rail_screw_z"], 5.0, NOTCH_WALL_U - 0.5,
                   NOTCH_WALL_U + MT["rail_tap_depth"])
        t = h if t is None else t + h
    return loc * t


def base_rails():
    out = []
    for sy in (-1, 1):
        r = _rail_solid(sy)
        for x, y in stations():
            if y * sy > 0:
                r -= rail_notch(x, y)
                r -= rail_taps(x, y)
        for _, x, side in WELLS:
            if side == sy:
                r -= well_cut(x, sy)
        r.label = f"BASE_RAIL_6061_{'L' if sy > 0 else 'R'}"
        out.append(r)
    return out


def foot_pads():
    """ASTM D1056 2B2 closed-cell EPDM, PSA one side, shown COMPRESSED (PAD_C)."""
    B, w = G.S["base_half_w"], G.S["foot_w"]
    xa, xb = G.S["x0"] + 30.0, G.T["rail_flat_end_x"] - 10.0
    out = []
    for sy in (-1, 1):
        yc = sy * (B - w / 2 - 2.0)
        p = Pos((xa + xb) / 2, yc, 0) * Box(xb - xa, MT["pad_w"], PAD_C, align=(CC, CC, CMIN))
        for x, y in stations():
            if y * sy > 0:
                p -= foot_pocket(x, y)
                p -= flange_pad_cut(x, y)
        for _, x, side in WELLS:
            if side == sy:
                p -= well_cut(x, sy)
        p.label = f"FOOT_PAD_EPDM_{'L' if sy > 0 else 'R'}"
        out.append(p)
    return out


# ---------------------------------------------------------------- kinematics (written to out/kinematics.json)
def plf_kinematics() -> dict:
    """Paddle + hook sweep for the render lane: hinge axis, states, cam law, per-station frames."""
    states = {"closed": 0.0, "stage1_caught": STAGE1_DEG, "open": OPEN_DEG}
    sts = []
    for x, y in stations():
        loc = station_loc(x, y)
        o = loc * Location((0, HU, HZ))
        axis = (loc * Location((1, 0, 0))).position - loc.position
        uvec = (loc * Location((0, 1, 0))).position - loc.position
        sts.append({"station": [x, y], "hinge_point": [round(c, 3) for c in o.position],
                    "hinge_axis": [round(c, 4) for c in axis], "outboard": [round(c, 4) for c in uvec],
                    "slider_axis": [round(c, 4) for c in uvec]})
    return {
        "note": "PROVISIONAL (P-CAL-01b). + angle swings the paddle top INBOARD about the hinge axis "
                "(right-hand rule about hinge_axis); slider retracts along -outboard by cam_law_mm.",
        "states_deg": states, "paddle_sweep_deg": list(SWEEP_DEG),
        "cam_law_deg_to_retract_mm": [list(p) for p in CAM_LAW],
        "slider_retract_mm_by_state": {k: round(cam_retract(v), 3) for k, v in states.items()},
        "detent_dimple_deg_on_knuckle": {"closed": DIMPLE_DEG[0], "stage1_caught": DIMPLE_DEG[1]},
        "paddle_size_mm": [MT["paddle_x"], MT["paddle_t"], MT["paddle_h"]],
        "stations": sts,
    }


# ---------------------------------------------------------------- engineering numbers
def stack_report() -> dict:
    return {
        "foot_top": FOOT_TOP, "rail_top": RAIL_TOP, "pad_comp": PAD_C, "pad_free": MT["pad_free"],
        "pad_strain": 1 - PAD_C / MT["pad_free"], "flange_top": FLANGE_T,
        "stem_bottom": MT["stem_bottom"], "stem_to_port_floor": PORT_DEPTH + MT["stem_bottom"],
        "head_z0": MT["head_z0"], "head_under_gap": HEAD_UNDER_GAP, "head_top": MT["head_top"],
        "hinge_z": HZ, "hinge_u": HU,
        "notch_float_x": MT["notch_clear_x"], "shim_nominal": MT["notch_shim_nom"],
        "shim_range": (0.0, 4.0), "slot_float_z": MT["rail_slot_z"],
        "rail_strip_t_min": BR["y_out"] - (max(abs(y) for _, y in stations()) + NOTCH_WALL_U),
        "screw_engagement": (MT["head_u0"] + MT["rail_cbore_depth"] + MT["rail_screw_len"]) - NOTCH_WALL_U,
        "screw_grip": NOTCH_WALL_U - (MT["head_u0"] + MT["rail_cbore_depth"]),
        "tooth_tip_past_pin_centre": MT["tooth_tip"] - MT["pin_u"],
        "slider_travel": MT["slider_travel"],
    }


G0 = 9.80665


def load_cases(mount: dict) -> list[dict]:
    """Design LIMIT load cases for the attachment (stated assumptions, not a standard).

    accel in g along (x rearward, y, z up), gravity included in z. 'aero_lift_N' acts up at the
    plan centroid. Values from hardware.json mounting.load_cases.
    """
    return mount["load_cases"]


def port_loads(mass_kg, cg, cases, plan_c=None):
    """Rigid-body reactions at the four ports for each case.

    Statically indeterminate in z with 4 supports: elastic port-group distribution about the
    pattern centroid (equal stiffness; exact for the near-rectangular port pattern, which is
    slightly trapezoidal on the R1T). Shear (x, y) is shared equally. Returns per case the
    worst port's tension, compression, shear and resultant, in newtons.
    """
    st = stations()
    xm = sum(x for x, _ in st) / len(st)
    ym = sum(y for _, y in st) / len(st)
    Sxx = sum((x - xm) ** 2 for x, _ in st)
    Syy = sum((y - ym) ** 2 for _, y in st)
    plan_c = plan_c or (xm, 0.0)
    out = []
    for c in cases:
        ax, ay, az = c["accel_g"]
        F = [mass_kg * G0 * ax, mass_kg * G0 * ay, mass_kg * G0 * az]   # load ON the topper
        lift = c.get("aero_lift_N", 0.0)
        Fz_down = -F[2] - lift                       # net downward force the ports must react
        h = cg[2]
        Mx_tip = F[1] * h + (-F[2]) * (cg[1] - ym)  # loads the +y (driver) ports
        My_pitch = F[0] * h + (-F[2]) * (cg[0] - xm) - lift * (plan_c[0] - xm)
        reac = []
        for x, y in st:
            r = Fz_down / len(st) + Mx_tip * (y - ym) / Syy + My_pitch * (x - xm) / Sxx
            reac.append(r)                          # + = port pushed down (compression)
        shear = math.hypot(F[0], F[1]) / 4.0
        worst_t = max(0.0, -min(reac))
        worst_c = max(0.0, max(reac))
        res = max(math.hypot(abs(r), shear) for r in reac)
        out.append({"case": c["name"], "accel_g": c["accel_g"], "aero_lift_N": lift,
                    "port_compression_N": round(worst_c, 1), "port_tension_N": round(worst_t, 1),
                    "port_shear_N": round(shear, 1), "port_resultant_N": round(res, 1),
                    "limit_class": c.get("class", "limit")})
    return out
