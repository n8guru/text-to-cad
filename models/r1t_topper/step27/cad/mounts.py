"""Topper-to-truck attachment (Step 27 rev 10): port clamp stations, base rails, foot pad.

The shell's foot bears on the OEM bed-rail caps (z = 0) through a closed-cell EPDM pad. Each 6061
base rail is bonded on the foot and clamped to Rivian's own bed accessory ports (Upfitting Guide
p.59: 2 per side, 2,500 N per port) at four PORT STATIONS. Rivian does not publish the port, so
the station starts from a PURCHASED, non-modifying adapter that latches into it and presents an
M10 thread (Weistec / Direct Current Engineering 09-111-00078-7, "R1T needs 4 for the bed").

Clamp path at a station, top down (all metal; the carbon is NOT in the bolt's clamp path, so the
laminate cannot creep the preload away):

    M10 ISO 4032 A4-80 hex nut        (16 AF: ratcheting box wrench swung INBOARD, horizontally -
                                       there is no room above the front stations for a hex key)
    Nord-Lock NL10ss wedge-locking washer pair
    M10 x 60 A4-70 stud, DIN 976-1    (Loctite 243 into the adapter; stays put when the topper
                                       is lifted off, so the stations re-locate on the studs)
    316 slot washer, 40 x 36 x 4      (covers the rail's +/-6 x +/-2.75 obround: port tolerance)
    6061 base rail, 25 thick          (bonded on the foot; 12 deep wrench pocket at the station,
                                       open to the rail's inboard edge)
    6061 port spacer, Dia 36          (in a through-pocket in the foot)
    316 shims, 0.5 / 1.0              (nominal 1.0: sets the stop height, +/-1 mm at fit-up)
    Weistec port adapter              (latched into the OEM port; M10 female)

Preload/compression stop: the pad is 6 mm free and 4 mm (33 %) when the spacer bottoms on the
shims; the spacer is the stop, so torque can never over-crush the pad or load the paint. Lateral
and fore-aft load cross the station by FRICTION in two slip planes, checked against the port
loads in ``port_loads`` (checks_step27.check_mounting).

Everything sized here from the adapter is PROVISIONAL (P-CAL-01): Weistec publishes no drawing.
OEM controls on the rail caps (TAILGATE_CONTROL.md) stay pressable: foot, pad and rail are cut
through over each button. Positions are PROVISIONAL until taped (T1-T3).
"""
from __future__ import annotations

import math

from build123d import Align, Box, Cylinder, Pos, extrude

import geom as G

CC, CMIN, CMAX = Align.CENTER, Align.MIN, Align.MAX
BR = G.BR
T = G.T
MT = G.MT
RAIL_X = (G.S["x0"] + 60.0, G.S["x1"] - 130.0)   # clear of the front roll and rear wrap
# (name, x, side) - side +1 = driver (+Y). Well clear opening 120 x 70.
WELLS = (("WELL_GT_L", 60.0, 1), ("WELL_GT_R", 60.0, -1), ("WELL_TG", 1300.0, 1))
WELL = {"lx": 120.0, "ly": 70.0, "y": 700.0}

# ---------------------------------------------------------------- the stack, derived not typed
FOOT_TOP = G.WALL                                 # rail underside / foot top
RAIL_TOP = G.WALL + BR["h"]
PAD_C = MT["pad_comp"]                            # pad compressed = foot underside height
ADAPTER_TOP = MT["adapter_env_h"]                 # PROVISIONAL (P-CAL-01)
SHIM_TOP = ADAPTER_TOP + MT["shim_nom"]
SPACER_H = FOOT_TOP - SHIM_TOP                    # the stop: closes when the pad is at PAD_C
POCKET_FLOOR = RAIL_TOP - MT["rail_pocket_depth"]   # wrench pocket milled in the rail top
WASHER_TOP = POCKET_FLOOR + MT["slot_washer_t"]
HEAD_SEAT = WASHER_TOP + MT["wedge_washer_t"]     # nut bearing face
NUT_TOP = HEAD_SEAT + MT["nut_h"]
ENGAGEMENT = MT["stud_engagement"]                # stud thread inside the adapter (P-CAL-01)
BOLT_TIP = ADAPTER_TOP - ENGAGEMENT               # stud bottom
STUD_TOP = BOLT_TIP + MT["bolt_len"]
PROTRUSION = STUD_TOP - NUT_TOP                   # stud past the nut (>= 1 pitch)
GRIP = HEAD_SEAT - ADAPTER_TOP                    # clamped length
POCKET_X = MT["adapter_env_x"] + 2 * MT["pocket_clear"]
POCKET_Y = MT["adapter_env_y"] + 2 * MT["pocket_clear"]
CLEAR_D = 10.5                                    # M10 clearance, ISO 273 medium


def stations():
    """(x, y) of the four port stations, vehicle frame."""
    return [(x, sy * y) for x, y in T["bed_ports"] for sy in (1, -1)]


def _rr(lx, ly, r, h, z0):
    return Pos(0, 0, z0) * extrude(G.rrect(lx, ly, r), amount=h)


def _obround(lx, ly, h, z0):
    return _rr(lx, ly, ly / 2 - 0.01, h, z0)


# ---------------------------------------------------------------- cut-outs (shell foot, rail, pad)
def well_cut(x, sy):
    return Pos(x, sy * WELL["y"], -1.0) * Box(WELL["lx"], WELL["ly"], G.WALL + BR["h"] + 10.0,
                                             align=(CC, CC, CMIN))


def foot_pocket(x, y):
    """Through-pocket in the foot over the adapter; the spacer and shims live in it."""
    return Pos(x, y, 0) * _rr(POCKET_X, POCKET_Y, MT["pocket_r"], FOOT_TOP + 2.0, -1.0)


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
    """Everything the shell must lose for the attachment: pad relief, adapter pockets, wells."""
    cuts = pad_relief()
    cuts += [foot_pocket(x, y) for x, y in stations()]
    cuts += [well_cut(x, side) for _, x, side in WELLS]
    return cuts


# ---------------------------------------------------------------- custom parts
def _rail_solid(sy):
    y0, y1 = BR["y_in"], BR["y_out"]
    return Pos((RAIL_X[0] + RAIL_X[1]) / 2, sy * (y0 + y1) / 2, FOOT_TOP) * Box(
        RAIL_X[1] - RAIL_X[0], y1 - y0, BR["h"], align=(CC, CC, CMIN))


def base_rails():
    out = []
    for sy in (-1, 1):
        r = _rail_solid(sy)
        for x, y in stations():
            if y * sy > 0:
                r -= Pos(x, y, 0) * _obround(MT["rail_slot_x"], MT["rail_slot_y"],
                                             BR["h"] + 2.0, FOOT_TOP - 1.0)
                r -= wrench_pocket(x, y)
        for _, x, side in WELLS:
            if side == sy:
                r -= well_cut(x, sy)
        r.label = f"BASE_RAIL_6061_{'L' if sy > 0 else 'R'}"
        out.append(r)
    return out


def wrench_pocket(x, y):
    """Spot-face in the rail top, open to the rail's INBOARD edge: drops the nut 12 mm below the
    socket frame's return lip and lets a ratcheting box wrench swing in from the bed side."""
    sy = 1 if y > 0 else -1
    y_out = abs(y) + MT["rail_pocket_out"]
    y_in = BR["y_in"] - 2.0
    return Pos(x, sy * (y_in + y_out) / 2, POCKET_FLOOR) * Box(
        MT["rail_pocket_x"], y_out - y_in, MT["rail_pocket_depth"] + 1.0, align=(CC, CC, CMIN))


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
        for _, x, side in WELLS:
            if side == sy:
                p -= well_cut(x, sy)
        p.label = f"FOOT_PAD_EPDM_{'L' if sy > 0 else 'R'}"
        out.append(p)
    return out


def port_spacer(x, y):
    s = Pos(x, y, SHIM_TOP) * Cylinder(MT["spacer_d"] / 2, SPACER_H, align=(CC, CC, CMIN))
    s -= Pos(x, y, SHIM_TOP - 1) * Cylinder(CLEAR_D / 2, SPACER_H + 2, align=(CC, CC, CMIN))
    s.label = "PORT_SPACER_6061"
    return s


def port_shims(x, y):
    """Nominal stack 2 x 0.5 (the fit-up kit adds 0.5 / 1.0 to range 0 .. 2.0 mm)."""
    out = []
    t = MT["shim_nom"] / 2
    for k in range(2):
        s = Pos(x, y, ADAPTER_TOP + k * t) * Cylinder(MT["shim_d"] / 2, t, align=(CC, CC, CMIN))
        s -= Pos(x, y, ADAPTER_TOP - 1) * Cylinder(CLEAR_D / 2, 3.0, align=(CC, CC, CMIN))
        s.label = "PORT_SHIM_316_0p5"
        out.append(s)
    return out


def slot_washer(x, y):
    w = Pos(x, y, POCKET_FLOOR) * _rr(MT["slot_washer_x"], MT["slot_washer_y"], 6.0,
                                      MT["slot_washer_t"], 0.0)
    w -= Pos(x, y, POCKET_FLOOR - 1) * Cylinder(CLEAR_D / 2, MT["slot_washer_t"] + 2, align=(CC, CC, CMIN))
    w.label = "PORT_SLOT_WASHER_316"
    return w


# ---------------------------------------------------------------- purchased parts (envelopes)
def port_adapter(x, y):
    """Weistec 09-111-00078-7 REPRESENTATION: plug into the OEM port + above-cap body, M10 female.

    The envelope is PROVISIONAL (P-CAL-01): no public drawing. Its job here is to reserve space
    and carry the thread the station is designed around.
    """
    a = Pos(x, y, 0) * _rr(MT["adapter_env_x"], MT["adapter_env_y"], 6.0, ADAPTER_TOP, 0.0)
    a += Pos(x, y, 0) * Cylinder(MT["adapter_plug_d"] / 2, MT["adapter_plug_depth"],
                                 align=(CC, CC, CMAX))
    a -= Pos(x, y, ADAPTER_TOP + 1) * Cylinder(8.5 / 2, ENGAGEMENT + 3.0, align=(CC, CC, CMAX))
    a.label = "PORT_ADAPTER_WEISTEC"
    return a


def port_stud(x, y):
    """M10 x 60 A4-70 stud (DIN 976-1), shown at the minor diameter so it threads, not clashes."""
    s = Pos(x, y, BOLT_TIP) * Cylinder(MT["bolt_d"] / 2 - 0.8, MT["bolt_len"], align=(CC, CC, CMIN))
    s.label = "PORT_STUD_M10x60_A4"
    return s


def port_nut(x, y):
    """M10 ISO 4032 A4-80 hex nut, 16 AF."""
    from build123d import RegularPolygon
    af = MT["nut_af"]
    n = Pos(x, y, HEAD_SEAT) * extrude(RegularPolygon(af / 2 / math.cos(math.pi / 6), 6),
                                       amount=MT["nut_h"])
    n -= Pos(x, y, HEAD_SEAT - 1) * Cylinder(MT["bolt_d"] / 2 - 0.75, MT["nut_h"] + 2, align=(CC, CC, CMIN))
    n.label = "PORT_NUT_M10_A4"
    return n


def wedge_washer(x, y):
    w = Pos(x, y, WASHER_TOP) * Cylinder(MT["wedge_washer_od"] / 2, MT["wedge_washer_t"],
                                         align=(CC, CC, CMIN))
    w -= Pos(x, y, WASHER_TOP - 1) * Cylinder(10.7 / 2, MT["wedge_washer_t"] + 2, align=(CC, CC, CMIN))
    w.label = "WEDGE_WASHER_NL10SS"
    return w


def port_station(x, y):
    return ([port_adapter(x, y)] + port_shims(x, y)
            + [port_spacer(x, y), slot_washer(x, y), wedge_washer(x, y), port_stud(x, y),
               port_nut(x, y)])


def port_stations():
    out = []
    for x, y in stations():
        out += port_station(x, y)
    return out


def port_adapters():
    """Back-compat name used by assembly/checks: every part of every station."""
    return port_stations()


# ---------------------------------------------------------------- engineering numbers
def stack_report() -> dict:
    return {
        "foot_top": FOOT_TOP, "rail_top": RAIL_TOP, "pad_comp": PAD_C, "pad_free": MT["pad_free"],
        "pad_strain": 1 - PAD_C / MT["pad_free"], "adapter_top": ADAPTER_TOP,
        "pocket_floor": POCKET_FLOOR, "rail_under_pocket": POCKET_FLOOR - FOOT_TOP,
        "shim_top": SHIM_TOP, "spacer_h": SPACER_H, "head_seat": HEAD_SEAT, "bolt_tip": BOLT_TIP,
        "engagement": ENGAGEMENT, "grip": GRIP, "nut_top": NUT_TOP, "protrusion": PROTRUSION,
        "slot_float_x": (MT["rail_slot_x"] - CLEAR_D) / 2, "slot_float_y": (MT["rail_slot_y"] - CLEAR_D) / 2,
        "washer_land_x": (MT["slot_washer_x"] - MT["rail_slot_x"]) / 2,
        "washer_land_y": (MT["slot_washer_y"] - MT["rail_slot_y"]) / 2,
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

    Statically indeterminate in z with 4 supports: elastic bolt-group distribution about the
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
        # moments about the pattern centroid at the port plane (z = 0); bolt-group distribution
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


def preload(torque_nm, k_nut, d_mm):
    return torque_nm * 1000.0 / (k_nut * d_mm)
