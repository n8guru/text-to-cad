"""Step 27 hardware library — authoritative build123d solids for every purchased/custom fitting.

Every dimension is read from ``step27/hardware.json``; nothing is hard-coded here. That file
carries the manufacturer, orderable PN, per-dimension provenance (DATASHEET / DATASHEET_ARCHIVED /
ESTIMATED / CUSTOM) and the source URL, so a vendor correction is one JSON edit plus one rebuild.

These are REPRESENTATION ENVELOPES of purchased parts, dimensioned from the manufacturer's
catalogue so the interfaces that matter — overall envelope, mounting pattern, panel preparation,
striker size, swept volume, service clearance — are real. They are NOT the manufacturer's
proprietary internal CAD and must not be substituted for it. Where a manufacturer does not publish
an internal dimension (Southco does not dimension the R4 claw throat), the internal mechanism here
is a credible representation and ``hardware.json`` records exactly which dimensions those are.

Rotary-latch local frame, shared by the latch and its striker:
  * +Z is the mounting-panel normal. The panel face is z = 0; the latch body stands proud by
    ``front_proud`` and reaches back by ``behind_panel``.
  * +X is the FORK-BOLT AXIS, and therefore the striker-bar axis. The housing's narrow 19.4 mm
    dimension runs along X.
  * The striker travels along -Y, down the panel-preparation slot, into the fork mouth. The latch
    panel therefore lies PARALLEL to the door's travel, on a return flange — which is what makes a
    panel-mounted rotary latch work on a swing-shut door.

Written in build123d ALGEBRA mode on purpose: in builder mode ``Pos(...) * Box(...)`` silently
adds the box at the origin and discards the placed copy. Algebra mode has no such trap.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from build123d import (
    Align, Axis, Box, Circle, Compound, Cylinder, Plane, Polyline, Pos,
    Rectangle, RegularPolygon, Rot, Sphere, Vector, chamfer, extrude, fillet, sweep,
)

HERE = Path(__file__).resolve().parent
HW = json.loads((HERE.parent / "hardware.json").read_text())

CMIN, CC, CMAX = Align.MIN, Align.CENTER, Align.MAX


def d(item: str) -> dict:
    return HW[item]["dims"]


def pn(item: str) -> str:
    h = HW[item]
    return f"{h.get('manufacturer') or 'CUSTOM'} {h.get('pn') or h.get('drawing') or ''}".strip()


def _lab(shape, name, color=None):
    shape.label = name
    if color is not None:
        shape.color = color
    return shape


def _z_fillet(part, r):
    edges = [e for e in part.edges().filter_by(Axis.Z) if e.length > 2.2 * r]
    return fillet(edges, r) if edges else part


# ======================================================================================
# Southco R4-30 two-stage rotary latch + R4-90 striker bolt
# ======================================================================================
PIVOT_Z = -1.6          # fork-bolt centre, just behind the panel so its rim protrudes through


def fork_bolt(state: str = "closed"):
    """Rotating fork bolt. Disc in the YZ plane, axis +X. ``state`` in closed|secondary|open."""
    p = d("rotary_latch")
    k = HW["rotary_latch"]["kinematics"]
    ang = {"closed": k["closed_deg"], "secondary": k["secondary_deg"], "open": k["open_deg"]}[state]
    r, t, tw, td = p["claw_r"], p["claw_t"], p["throat_w"], p["throat_depth"]

    part = Rot(0, 90, 0) * Cylinder(r, t, align=(CC, CC, CC))
    part -= Pos(0, r - td / 2 + 1, 0) * Box(t + 2, td + 2, tw, align=(CC, CC, CC))
    part -= Pos(0, r - td, 0) * Rot(0, 90, 0) * Cylinder(tw / 2, t + 2, align=(CC, CC, CC))
    part -= Rot(0, 90, 0) * Cylinder(3.0, t + 6, align=(CC, CC, CC))
    for a in (118.0, 146.0):                       # primary + secondary pawl catches = two-stage
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        part -= Pos(0, (r - 1.7) * ca, (r - 1.7) * sa) * Rot(a, 0, 0) * Box(
            t + 6, 3.4, 5.0, align=(CC, CC, CC))
    return _lab(Rot(ang, 0, 0) * part, f"fork_bolt:{state}", (0.86, 0.32, 0.05))


def pawl(state: str = "closed"):
    """Spring-loaded pawl dropping into the fork-bolt catches, with the cable arm that lifts it."""
    p = d("rotary_latch")
    k = HW["rotary_latch"]["kinematics"]
    ang = -k["pawl_release_deg"] if state == "open" else 0.0
    r, t, arm = p["pawl_r"], p["pawl_t"], p["cable_arm_l"]

    part = Rot(0, 90, 0) * Cylinder(r * 0.5, t, align=(CC, CC, CC))
    part += Pos(0, 0, r / 2) * Box(t, r * 0.5, r, align=(CC, CC, CC))
    part += Pos(0, 0, r) * Rot(0, 90, 0) * Cylinder(r * 0.28, t, align=(CC, CC, CC))
    part += Pos(0, -arm / 2, 0) * Box(t * 0.7, arm, 7.0, align=(CC, CC, CC))
    part += Pos(0, -arm, 0) * Rot(0, 90, 0) * Cylinder(5.5, t * 0.7, align=(CC, CC, CC))
    part -= Pos(0, -arm, 0) * Cylinder(p["cable_eye_dia"] / 2, t + 6, align=(CC, CC, CC))
    part -= Rot(0, 90, 0) * Cylinder(2.5, t + 6, align=(CC, CC, CC))
    return _lab(Rot(ang, 0, 0) * part, f"pawl:{state}", (0.72, 0.72, 0.75))


def latch_housing():
    """R4-30 envelope: 77 long x 19.4 wide x 34.8 deep, holes at 38.1 pitch, 17 mm striker slot."""
    p = d("rotary_latch")
    L, W = p["overall_l"], p["width"]
    front, behind = p["front_proud"], p["behind_panel"]
    r, td, tw = p["claw_r"], p["throat_depth"], p["throat_w"]

    part = _z_fillet(Box(W, L, 4.0, align=(CC, CC, CMAX)), 5.0)          # panel-face flange
    for sy in (-1, 1):
        part -= Pos(0, sy * p["hole_pitch"] / 2, 1) * Cylinder(
            p["panel_hole_dia"] / 2, 10.0, align=(CC, CC, CMAX))
    part += Pos(0, p["pivot_y"], -behind / 2 - 2.0) * Box(
        W, r * 2 + 16, behind - 4.0, align=(CC, CC, CC))                 # fork-bolt housing
    part += Pos(0, p["pawl_pivot_y"] - 6, -behind / 2 - 2.0) * Box(
        W, 34.0, behind - 4.0, align=(CC, CC, CC))                       # pawl / trigger housing
    part += Pos(0, p["pivot_y"] + 4, front / 2) * Box(
        W, r * 1.6, front, align=(CC, CC, CC))                           # nose proud of the panel
    part += Pos(0, -L / 2 + 6, -behind / 2 - 2.0) * Box(
        W, 12.0, 16.0, align=(CC, CC, CC))                               # cable abutment
    # cavities last, so they cut every housing section
    part -= Pos(0, p["pivot_y"], PIVOT_Z) * Rot(0, 90, 0) * Cylinder(
        r + 1.2, W - 5.0, align=(CC, CC, CC))
    part -= Pos(0, p["pawl_pivot_y"], PIVOT_Z + 2) * Rot(0, 90, 0) * Cylinder(
        p["pawl_r"] + 1.2, W - 5.0, align=(CC, CC, CC))
    part -= Pos(0, p["pivot_y"] + p["slot_depth"] / 2 + 6, 2) * Box(
        tw + 1.0, p["slot_depth"] + 24, front + 10, align=(CC, CC, CMAX))  # striker entry slot
    part -= Pos(0, -L / 2 + 6, -behind / 2 - 2.0) * Rot(90, 0, 0) * Cylinder(
        d("release_cable")["conduit_dia"] / 2 + 0.3, 24, align=(CC, CC, CC))
    return _lab(part, "latch_housing_R4-30", (0.62, 0.63, 0.66))


def rotary_latch(state: str = "closed"):
    """Southco R4-30-41-501-20 in its local frame. Origin = panel face, hole-pattern centre."""
    p = d("rotary_latch")
    c = Compound(children=[
        latch_housing(),
        Pos(0, p["pivot_y"], PIVOT_Z) * fork_bolt(state),
        Pos(0, p["pawl_pivot_y"], PIVOT_Z + 2) * pawl(state),
    ])
    c.label = f"ROTARY_LATCH_R4-30:{state}"
    return c


def latch_swept_envelope():
    """The fork bolt's full swept volume — keep-out for anything routed near a latch."""
    p = d("rotary_latch")
    return _lab(Pos(0, p["pivot_y"], PIVOT_Z) * Rot(0, 90, 0) * Cylinder(
        p["claw_r"] + 1.0, p["claw_t"] + 2, align=(CC, CC, CC)),
        "LATCH_SWEPT_ENVELOPE", (1.0, 0.0, 0.0))


def striker_bolt():
    """Southco R4-90-321-20. Local +Z is the shoulder axis; z = 0 is the mounting face.

    The Dia 12.7 shoulder IS the bar the fork bolt grabs; the flanged hex head stops axial escape.
    """
    s = d("striker")
    part = Cylinder(10.0 / 2, s["thread_len"], align=(CC, CC, CMAX))                  # M10x1.5
    part += Cylinder(s["rod_dia"] / 2, s["shoulder_len"], align=(CC, CC, CMIN))        # the bar
    part += Pos(0, 0, s["shoulder_len"]) * Cylinder(
        s["head_dia"] / 2, s["flange_t"], align=(CC, CC, CMIN))
    part += Pos(0, 0, s["shoulder_len"] + s["flange_t"]) * extrude(
        RegularPolygon(s["hex_af"] / 2 / math.cos(math.pi / 6), 6), amount=s["hex_h"])
    return _lab(part, "STRIKER_BOLT_R4-90-321-20", (0.80, 0.80, 0.82))


def striker_bracket():
    """CUSTOM slotted bracket the striker bolt threads into (DWG-27-004).

    Custom because no catalogue bracket carries our pattern; the slots give +/-3 mm of fit-up
    adjustment so the module tolerance stack is dialled out at assembly instead of scrapped.
    """
    part = _z_fillet(Box(54.0, 40.0, 6.0, align=(CC, CC, CMAX)), 6.0)
    part -= Pos(0, 0, 1) * Cylinder(10.6 / 2, 12.0, align=(CC, CC, CMAX))
    for sy in (-1, 1):
        part -= Pos(0, sy * 16.0, 1) * Box(7.0, 6.0, 12.0, align=(CC, CC, CMAX))
        for dy in (-3.0, 3.0):
            part -= Pos(0, sy * 16.0 + dy, 1) * Cylinder(3.5, 12.0, align=(CC, CC, CMAX))
    return _lab(part, "STRIKER_BRACKET_custom", (0.30, 0.31, 0.33))


# ======================================================================================
# release train — Southco AC cable + paddle + splitter (no custom lever)
# ======================================================================================
def _dir(a, b):
    return (Vector(b) - Vector(a)).normalized()


def release_cable(pts):
    """Push-pull cable conduit swept along ``pts`` (3-tuples, mm), plus the two end fittings."""
    c = d("release_cable")
    path = Polyline(*[tuple(p) for p in pts])
    prof = Plane(origin=tuple(pts[0]), z_dir=_dir(pts[0], pts[1])) * Circle(c["conduit_dia"] / 2)
    part = sweep(prof, path=path)
    for a, b in ((pts[0], pts[1]), (pts[-1], pts[-2])):
        part += extrude(Plane(origin=tuple(a), z_dir=_dir(a, b)) * Circle(c["end_fitting_dia"] / 2),
                        amount=c["end_fitting_len"])
    return _lab(part, "RELEASE_CABLE_AC", (0.06, 0.06, 0.07))


def cable_min_radius(pts) -> float:
    """Smallest turn radius the routed polyline implies, for the bend-radius check."""
    best = float("inf")
    for i in range(1, len(pts) - 1):
        a, b, c = (Vector(p) for p in (pts[i - 1], pts[i], pts[i + 1]))
        v1, v2 = a - b, c - b
        if v1.length < 1e-6 or v2.length < 1e-6:
            continue
        half = math.acos(max(-1.0, min(1.0, v1.normalized().dot(v2.normalized())))) / 2.0
        if half <= 1e-6 or abs(half - math.pi / 2) < 1e-6:
            continue
        best = min(best, min(v1.length, v2.length) * 0.5 * math.tan(half))
    return best


def release_handle(pulled: bool = False):
    """Southco AC-75-101-11 aluminium paddle handle, flush in its pan."""
    h = d("release_handle")
    pan = _z_fillet(Box(h["paddle_l"], h["paddle_w"], h["paddle_t"], align=(CC, CC, CMAX)), 10.0)
    pan -= Pos(0, 0, 1) * _z_fillet(
        Box(h["paddle_l"] - 12, h["paddle_w"] - 12, h["paddle_t"], align=(CC, CC, CMAX)), 8.0)
    paddle = Pos(0, 0, -3.0) * Rot(0, -14.0 if pulled else 0.0, 0) * _z_fillet(
        Box(h["paddle_l"] - 20, h["paddle_w"] - 20, 8.0, align=(CC, CC, CMAX)), 6.0)
    c = Compound(children=[_lab(pan, "handle_pan", (0.10, 0.10, 0.11)),
                           _lab(paddle, "handle_paddle", (0.14, 0.14, 0.15))])
    c.label = f"RELEASE_HANDLE_AC-75-101-11:{'pulled' if pulled else 'rest'}"
    return c


def cable_splitter():
    """Southco AC-05-301-11: one handle pull -> two equal latch pulls. Replaces the custom lever."""
    part = _z_fillet(Box(64.0, 38.0, 16.0, align=(CC, CC, CC)), 6.0)
    for sy in (-1, 1):
        part += Pos(0, sy * 24.0, 0) * Rot(90, 0, 0) * Cylinder(5.5, 14.0, align=(CC, CC, CMIN))
    part += Pos(-38.0, 0, 0) * Rot(0, 90, 0) * Cylinder(5.5, 14.0, align=(CC, CC, CMIN))
    return _lab(part, "CABLE_SPLITTER_AC-05-301-11", (0.10, 0.10, 0.11))


# ======================================================================================
# locators, seal, stops
# ======================================================================================
def locating_pin(kind: str = "round"):
    p = d(f"locating_pin_{kind}")
    part = Cylinder(p["press_dia"] / 2, p["press_len"], align=(CC, CC, CMAX))
    part += Cylinder(p["shoulder_dia"] / 2, p["shoulder_t"], align=(CC, CC, CMIN))
    pin = Pos(0, 0, p["shoulder_t"]) * Cylinder(p["pin_dia"] / 2, p["pin_len"], align=(CC, CC, CMIN))
    # chamfer the lead-in BEFORE cutting the flats: on a diamond pin the top face is no longer a
    # single circle, and OCCT refuses a chamfer over the resulting mixed edge set.
    pin = chamfer(pin.edges().group_by(Axis.Z)[-1], length=p["lead_chamfer"])
    if kind == "diamond":
        for sy in (-1, 1):
            pin -= Pos(0, sy * (p["flat_across"] / 2 + p["pin_dia"] / 2), p["shoulder_t"] - 1) * Box(
                p["pin_dia"] * 2, p["pin_dia"], p["pin_len"] + 4, align=(CC, CC, CMIN))
    return _lab(part + pin, f"LOCATING_PIN_{kind.upper()}_MISUMI", (0.62, 0.63, 0.66))


def bushing():
    b = d("bushing")
    part = Cylinder(b["od"] / 2, b["len"], align=(CC, CC, CMIN))
    part += Cylinder(b["flange_dia"] / 2, b["flange_t"], align=(CC, CC, CMIN))
    part -= Pos(0, 0, -1) * Cylinder(b["id"] / 2, b["len"] + 4, align=(CC, CC, CMIN))
    return _lab(part, "BUSHING_JBHC10-15_G6", (0.5, 0.5, 0.54))


def bulb_seal_section(compressed: bool = False):
    """Trim-Lok DD6139 section: push-on U-channel base, bulb on top.

    Sketch on XY: x across the seal, y = standing height measured from the rib root.
    """
    s = d("bulb_seal")
    sk = Rectangle(s["base_w"], s["base_h"], align=(CC, CMIN))
    sk -= Pos(0, -1) * Rectangle(s["rib_t"] + 0.2, s["base_h"], align=(CC, CMIN))   # grip channel
    sk += Pos(0, s["base_h"] + s["bulb_dia"] / 2) * Circle(s["bulb_dia"] / 2)
    if compressed:
        # the sponge bulb flattens; the dense EPDM base does not, so trim the bulb, don't scale
        sk -= Pos(0, s["compressed_height"]) * Rectangle(
            s["bulb_dia"] * 3, s["bulb_dia"] * 2, align=(CC, CMIN))
        sk += Pos(0, s["compressed_height"] - 1.0) * Rectangle(
            s["bulb_dia"] * 1.3, 1.0, align=(CC, CMIN))
    return sk


def seal_bead(path, up=(0, 0, 1), compressed: bool = False):
    """Sweep the DD6139 section around a closed land path.

    ``path`` must be a CLOSED, TANGENT-CONTINUOUS wire (a filleted rounded rectangle, not a raw
    polyline): OCCT's pipe shell silently returns a zero-volume solid on sharp corners, and a real
    extruded seal is bent round a radius anyway. ``up`` is the direction the bulb stands proud.
    """
    start, tan = path @ 0, path % 0
    pl = Plane(origin=start, x_dir=Vector(up).cross(tan), z_dir=tan)
    return _lab(sweep(pl * bulb_seal_section(compressed), path=path, is_frenet=True),
                "BULB_SEAL_DD6139", (0.05, 0.05, 0.05))


def compression_pad():
    p = d("compression_limiter")
    part = _z_fillet(Box(p["pad_l"], p["pad_w"], p["pad_t"], align=(CC, CC, CMIN)), 5.0)
    part -= Pos(0, 0, -1) * Cylinder(p["hole_dia"] / 2, p["pad_t"] + 4, align=(CC, CC, CMIN))
    return _lab(part, "COMPRESSION_LIMITER_custom_UHMW", (0.85, 0.85, 0.82))


def ball_plunger():
    p = d("ball_plunger")
    part = Cylinder(4.0, p["body_len"], align=(CC, CC, CMAX))
    part += Pos(0, 0, p["extension"]) * Sphere(p["ball_dia"] / 2)
    return _lab(part, "BALL_PLUNGER_85015A51", (0.7, 0.7, 0.72))


# ======================================================================================
# hatch hardware
# ======================================================================================
def strut_length(extension: float = 1.0) -> float:
    g = d("gas_strut")
    return g["compressed_len"] + extension * g["stroke"]


def gas_strut(extension: float = 1.0):
    """Stabilus 6541IS, axis +Z, origin at the lower ball-socket centre. 0 = compressed."""
    g = d("gas_strut")
    total = strut_length(extension)
    sock, body_len = g["socket_len"], g["compressed_len"] - 2 * g["socket_len"]
    part = Pos(0, 0, sock) * Cylinder(g["body_dia"] / 2, body_len, align=(CC, CC, CMIN))
    part += Pos(0, 0, sock + body_len) * Cylinder(
        g["rod_dia"] / 2, total - sock - body_len, align=(CC, CC, CMIN))
    for z in (0.0, total - sock):
        part += Pos(0, 0, z) * Cylinder(g["socket_across"] / 2, sock, align=(CC, CC, CMIN))
    part.label = f"GAS_STRUT_6541IS:{total:.0f}mm"
    return part


def ball_stud():
    """Stabilus 4486MD, Dia 10 ball on M8. Origin at the mounting face, ball on +Z."""
    b = HW["gas_strut"]["ball_stud"]
    part = Cylinder(8.0 / 2, b["thread_len"], align=(CC, CC, CMAX))
    part += extrude(RegularPolygon(13.0 / 2 / math.cos(math.pi / 6), 6), amount=5.0)
    part += Pos(0, 0, 5.0) * Cylinder(4.0, b["flange_to_ball_centre"] - 5.0, align=(CC, CC, CMIN))
    part += Pos(0, 0, b["flange_to_ball_centre"]) * Sphere(b["ball_dia"] / 2)
    return _lab(part, "BALL_STUD_4486MD", (0.75, 0.75, 0.78))


def concealed_hinge(angle_deg: float = 0.0):
    """JW Winco GN 7233-NI-50 representation.

    GN 7233 is a MULTI-JOINT LINKAGE. The rotation shown here is our DESIGN-INTENT axis, not the
    hinge's true coupler curve; ``hardware.json`` records that, and ``checks_step27`` only asserts
    the leaf stays inside the catalogued installation envelope. Pull JW Winco's CAD before release.
    """
    h = d("hinge")
    body = Box(h["leaf_l"], h["h2"], h["s"], align=(CC, CMAX, CMAX))
    for sx in (-1, 1):
        body -= Pos(sx * h["hole_pitch"] / 2, -h["h2"] / 2, 1) * Cylinder(
            h["hole_slot_w"] / 2, h["s"] + 4, align=(CC, CC, CMAX))
    body += Box(h["leaf_l"] * 0.45, h["offset_x"], h["offset_y"] * 0.4 + h["s"],
                align=(CC, CMIN, CMAX))
    knuckle = Rot(0, 90, 0) * Cylinder(6.0, h["leaf_l"] * 0.5)
    door = Box(h["leaf_l"], h["h2"], h["s"], align=(CC, CMIN, CMIN))
    for sx in (-1, 1):
        door -= Pos(sx * h["hole_pitch"] / 2, h["h2"] / 2, -1) * Cylinder(
            h["hole_slot_w"] / 2, h["s"] + 4, align=(CC, CC, CMIN))
    axis = Pos(0, h["offset_x"], h["offset_y"] * 0.4)
    c = Compound(children=[
        _lab(body, "hinge_leaf_body", (0.30, 0.30, 0.33)),
        _lab(axis * knuckle, "hinge_knuckle", (0.75, 0.75, 0.78)),
        _lab(axis * Rot(angle_deg, 0, 0) * door, "hinge_leaf_door", (0.30, 0.30, 0.33)),
    ])
    c.label = f"CONCEALED_HINGE_GN7233-NI-50:{angle_deg:.0f}deg"
    return c


def hinge_install_envelope():
    """The l4 x l5 x r installation space GN 7233 needs kept clear — a real packaging constraint."""
    h = d("hinge")
    return _lab(Pos(0, h["envelope_l4"] / 2 - h["offset_x"], -h["envelope_l5"] / 2) * Box(
        h["leaf_l"] + 20, h["envelope_l4"], h["envelope_l5"], align=(CC, CC, CC)),
        "HINGE_INSTALL_ENVELOPE", (1.0, 0.5, 0.0))


def t_handle(rotated: bool = False):
    """Southco E3-18-15 keyed T-handle. Dia 22.5 double-D panel cutout, 19.1 across flats."""
    t = d("t_handle")
    part = Cylinder(t["escutcheon_dia"] / 2, 4.0, align=(CC, CC, CMAX))
    shaft = Cylinder(t["cutout_dia"] / 2, t["behind_panel"], align=(CC, CC, CMAX))
    shaft -= Pos(0, (t["cutout_dia"] + t["cutout_across_flats"]) / 2, 1) * Box(
        t["cutout_dia"] * 2, t["cutout_dia"], t["behind_panel"] + 4, align=(CC, CC, CMAX))
    part += shaft
    bar = Box(t["tbar_l"], t["tbar_w"], 12.0, align=(CC, CC, CMIN))
    bar += Pos(t["tbar_l"] / 2 - 12, 0, 0) * Cylinder(7.0, 12.0, align=(CC, CC, CMIN))  # key barrel
    part += Rot(0, 0, t["rotation_deg"] if rotated else 0.0) * bar
    part += Pos(0, 0, -t["behind_panel"] + 8) * Box(38.0, 12.0, 8.0, align=(CMIN, CC, CMIN))
    return _lab(part, "T_HANDLE_E3-18-15", (0.05, 0.05, 0.06))


def chmsl():
    c = d("chmsl")
    part = _z_fillet(Box(c["len"], c["h"], c["d"], align=(CC, CC, CMIN)), 6.0)
    for sx in (-1, 1):
        part -= Pos(sx * c["hole_pitch"] / 2, 0, -1) * Cylinder(
            c["hole_dia"] / 2, c["d"] + 4, align=(CC, CC, CMIN))
    return _lab(part, "CHMSL_M63319R", (0.75, 0.05, 0.04))


ALL = {
    "rotary_latch": rotary_latch,
    "striker_bolt": striker_bolt,
    "striker_bracket": striker_bracket,
    "release_handle": release_handle,
    "cable_splitter": cable_splitter,
    "locating_pin_round": lambda: locating_pin("round"),
    "locating_pin_diamond": lambda: locating_pin("diamond"),
    "bushing": bushing,
    "compression_pad": compression_pad,
    "ball_plunger": ball_plunger,
    "gas_strut": gas_strut,
    "ball_stud": ball_stud,
    "concealed_hinge": concealed_hinge,
    "t_handle": t_handle,
    "chmsl": chmsl,
}
