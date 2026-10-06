"""Step 27 carbon shell — authoritative build123d A-surface and laminate envelope.

The shell is generated from ONE styled cross-section plus two end faces, all read from
``blender/params.json`` (shell block) and justified against Rivian's own R1T/R1S line art in
``step27/style/STYLE27.md``:

  section (y, z)   base on the rail cap -> flat land leaning ``lean_deg`` (the R1T C-pillar /
                   R1S D-pillar tumblehome) -> R``shoulder_r`` shoulder -> shallow crown whose
                   top meets the R1T cab roof height
  front face       vertical at ``x0``, behind the cab-roof spoiler tip, R``front_r`` roll
  rear face        raked ``rear_rake_deg`` (the R1S liftgate), R``rear_r`` roof roll-off and plan-view
                   corner wrap (one radius: see outer_body)

The flat land and the flat raked rear face are not styling accidents: the four identical sockets
and the hatch frame bond to them, so the style is built AROUND those two planes and the checks
prove every bond flange lands on flat skin.

Laminate envelope only: 22 mm sandwich (skins + core) is represented as one solid; layup lives in
the Step 11 schedule. The shell is hollowed with its base open, then gets a rail-cap foot, the
interface through-cuts, the front pass-through window and four roof hardpoint inserts.
"""
from __future__ import annotations

import math
from functools import lru_cache

from build123d import (
    Align, Axis, Box, Compound, Cylinder, Edge, Face, Plane, Polygon, Pos, Rot, Vector, Wire,
    extrude, fillet, offset,
)

import geom as G

CC, CMIN, CMAX = Align.CENTER, Align.MIN, Align.MAX
S = G.S
LONG = 3000.0          # prism length before the end cuts


# ------------------------------------------------------------------------------ section
def section_geometry():
    """Key points of the styled section, right half (y > 0), mm.

    Returns a dict with the land/shoulder tangent T1, the shoulder centre P, the shoulder/crown
    tangent T2, the crown centre Oc and radius Rc, and the top of the crown.
    """
    B, th = S["base_half_w"], G.lean_rad()
    R = S["shoulder_r"]
    zc = S["roof_z"]
    # crown: circular arc through the roof top whose drop at the shoulder is ``roof_crown``
    y_ref = 550.0
    Rc = (y_ref ** 2 + S["roof_crown"] ** 2) / (2 * S["roof_crown"])
    Oc = (0.0, zc - Rc)
    # shoulder centre P: distance R from the land line (inside) and Rc - R from Oc
    #   land line through (B, 0), inward unit normal n_in = (-cos th, -sin th)
    #   (P - (B, 0)) . n_in = R  ->  Py = B - (R + Pz sin th) / cos th
    c, s = math.cos(th), math.sin(th)
    lo, hi = S["land_top_z"] - 50.0, zc
    for _ in range(200):                                   # bisection on Pz
        pz = (lo + hi) / 2
        py = B - (R + pz * s) / c
        f = math.hypot(py - Oc[0], pz - Oc[1]) - (Rc - R)
        if f > 0:          # f grows with pz: too far from the crown centre -> go lower
            hi = pz
        else:
            lo = pz
    P = (py, pz)
    T1 = (py + R * c, pz + R * s)                         # tangent on the land
    k = Rc / (Rc - R)
    T2 = (Oc[0] + (py - Oc[0]) * k, Oc[1] + (pz - Oc[1]) * k)
    return {"B": B, "T1": T1, "P": P, "T2": T2, "Oc": Oc, "Rc": Rc, "top": (0.0, zc), "R": R}


def _arc(p0, pm, p1):
    return Edge.make_three_point_arc(Vector(*p0), Vector(*pm), Vector(*p1))


def section_face() -> Face:
    """Closed section on Plane.YZ coordinates (u = vehicle Y, v = vehicle Z)."""
    g = section_geometry()
    B, T1, P, T2, Oc, Rc, R = g["B"], g["T1"], g["P"], g["T2"], g["Oc"], g["Rc"], g["R"]

    def mid_on(c, r, a, b):
        ang = (math.atan2(a[1] - c[1], a[0] - c[0]) + math.atan2(b[1] - c[1], b[0] - c[0])) / 2
        return (c[0] + r * math.cos(ang), c[1] + r * math.sin(ang))

    mir = lambda p: (-p[0], p[1])
    pts = {
        "bl": (-B, 0.0), "br": (B, 0.0),
    }
    e = [
        Edge.make_line(Vector(*pts["bl"]), Vector(*pts["br"])),
        Edge.make_line(Vector(*pts["br"]), Vector(*T1)),
        _arc(T1, mid_on(P, R, T1, T2), T2),
        _arc(T2, (0.0, g["top"][1]), mir(T2)),
        _arc(mir(T2), mir(mid_on(P, R, T1, T2)), mir(T1)),
        Edge.make_line(Vector(*mir(T1)), Vector(*pts["bl"])),
    ]
    return Face(Wire(e))


def section_half_width(z: float) -> float:
    """Outer half-width of the styled section at height z (for checks and the render lane)."""
    g = section_geometry()
    if z <= g["T1"][1]:
        return G.land_y(z)
    if z <= g["T2"][1]:
        P, R = g["P"], g["R"]
        return P[0] + math.sqrt(max(R ** 2 - (z - P[1]) ** 2, 0.0))
    Oc, Rc = g["Oc"], g["Rc"]
    return math.sqrt(max(Rc ** 2 - (z - Oc[1]) ** 2, 0.0))


# ------------------------------------------------------------------------------ solids
def _prism():
    f = Plane.YZ * section_face()
    return Pos(-LONG / 2 + (S["x0"] + S["x1"]) / 2, 0, 0) * extrude(f, amount=LONG)


def _side_cut():
    """Side-profile region: x0 <= x <= rear face, z >= 0, extruded across Y."""
    top = S["roof_z"] + 200.0
    r = G.rake_rad()
    poly = Polygon((S["x0"], 0.0), (S["x1"], 0.0), (S["x1"] - top * math.tan(r), top),
                   (S["x0"], top), align=None)
    return extrude(Plane.XZ * poly, amount=1500.0, both=True)


def _edges_on_plane(solid, point, normal, tol=0.5, skip_bottom=True):
    n = Vector(*normal).normalized()
    p0 = Vector(*point)
    out = []
    for e in solid.edges():
        pts = [e @ t for t in (0.0, 0.25, 0.5, 0.75, 1.0)]
        if all(abs((q - p0).dot(n)) < tol for q in pts):
            if skip_bottom and all(abs(q.Z) < tol for q in pts):
                continue
            out.append(e)
    return out


@lru_cache(maxsize=1)
def outer_body():
    """Closed outer A-surface solid (not hollow), filleted at the ends."""
    body = _prism() & _side_cut()
    # front perimeter: one radius for the whole loop keeps the vertex blends simple
    fe = _edges_on_plane(body, (S["x0"], 0, 0), (1, 0, 0))
    body = fillet(fe, S["front_r"])
    # One radius per end loop: the section is tangent-continuous (land -> shoulder -> crown), so
    # OCC propagates a fillet round the whole loop whether you ask it to or not. R100 is both the
    # plan-view corner wrap and the roof roll-off into the raked rear face.
    r = G.rake_rad()
    rear = _edges_on_plane(body, (S["x1"], 0, 0), (math.cos(r), 0, math.sin(r)))
    body = fillet(rear, S["rear_r"])
    return body


@lru_cache(maxsize=1)
def hollow():
    """22 mm laminate envelope, base open."""
    body = outer_body()
    bottom = body.faces().sort_by(Axis.Z)[0]
    return offset(body, amount=-G.WALL, openings=[bottom])


def foot():
    """Inward flange along both sides: the shell's bearing strip on the OEM rail caps."""
    B, w = S["base_half_w"], S["foot_w"]
    xa, xb = S["x0"] + 30.0, G.T["rail_flat_end_x"] - 5.0     # stop on the FLAT rail cap
    parts = []
    for sy in (-1, 1):
        y0 = B - w
        blk = Pos((xa + xb) / 2, sy * (y0 + (B - y0) / 2), 0) * Box(
            xb - xa, B - y0, G.WALL, align=(CC, CC, CMIN))
        parts.append(blk)
    return parts[0] + parts[1]


def _rrect_prism(pl, half_w, half_h, r, n0, n1):
    """Rounded-rectangle prism in a local plane, spanning local z from n0 to n1."""
    sk = G.rrect(2 * half_w, 2 * half_h, r)
    return pl * (Pos(0, 0, n0) * extrude(sk, amount=n1 - n0))


def socket_cut(side: str, i: int):
    W, HH = G.opening_wh()
    e = G.SHELL_CUT
    return _rrect_prism(G.socket_plane(side, i), W / 2 + e, HH / 2 + e, G.K["corner_r"] + e,
                        -80.0, 40.0)


def hatch_cut():
    W, HH = G.hatch_wh()
    e = G.H_SHELL_CUT
    return _rrect_prism(G.hatch_plane(), W / 2 + e, HH / 2 + e, G.H["corner_r"] + e, -80.0, 40.0)


def drain_exit_holes():
    """Step 29: none (the hatch's bottom run is open; the wet channel drains out of the stub ends)."""
    return []


FRONT_WIN = {"w": 900.0, "h": 230.0, "r": 45.0, "zc": 200.0, "overlap": 20.0, "t": 5.0}


def front_window_cut():
    pl = Plane(origin=(S["x0"], 0, FRONT_WIN["zc"]), x_dir=(0, 1, 0), z_dir=(-1, 0, 0))
    return _rrect_prism(pl, FRONT_WIN["w"] / 2, FRONT_WIN["h"] / 2, FRONT_WIN["r"], -60.0, 40.0)


def front_pane():
    """5 mm hard-coat PC, bonded to the inner skin with a 20 mm overlap all round."""
    t, ov = FRONT_WIN["t"], FRONT_WIN["overlap"]
    pl = Plane(origin=(S["x0"] + G.WALL, 0, FRONT_WIN["zc"]), x_dir=(0, 1, 0), z_dir=(-1, 0, 0))
    sk = G.rrect(FRONT_WIN["w"] + 2 * ov, FRONT_WIN["h"] + 2 * ov, FRONT_WIN["r"] + ov)
    pane = pl * (Pos(0, 0, -t) * extrude(sk, amount=t))
    pane.label = "FRONT_PASS_THROUGH_PANE_PC"
    return pane


HARDPOINT = {"dia": 40.0, "depth": 16.0}


def roof_hardpoints():
    """Topper-owned crossbar hardpoints: bonded 6061 M8 inserts flush with the roof skin."""
    out = []
    for x in G.ROOF_PORTS_X:
        for sy in (-1, 1):
            y = sy * G.ROOF_PORTS_Y
            z = section_top_z(y)
            ins = Pos(x, y, z) * Cylinder(HARDPOINT["dia"] / 2, HARDPOINT["depth"],
                                         align=(CC, CC, CMAX))
            ins -= Pos(x, y, z + 1) * Cylinder(4.0, 14.0, align=(CC, CC, CMAX))   # M8 tapped
            ins.label = f"ROOF_HARDPOINT_{'L' if sy > 0 else 'R'}{0 if x < 500 else 1}"
            out.append(ins)
    return out


def section_top_z(y: float) -> float:
    g = section_geometry()
    Oc, Rc = g["Oc"], g["Rc"]
    return Oc[1] + math.sqrt(max(Rc ** 2 - y ** 2, 0.0))


@lru_cache(maxsize=1)
def shell():
    """The carbon shell: hollow envelope + foot, minus every interface through-cut."""
    sh = hollow() + foot()
    for side in "LR":
        for i in range(2):
            sh -= socket_cut(side, i)
    sh -= hatch_cut()
    sh -= front_window_cut()
    import mounts                                        # noqa: WPS433 (avoid a cycle at import)
    for c in mounts.foot_cuts():
        sh -= c
    for c in drain_exit_holes():
        sh -= c
    for hp in roof_hardpoints():
        sh -= _hp_hole(hp)
    sh.label = "SHELL_CARBON_SANDWICH"
    return sh


def _hp_hole(hp):
    bb = hp.bounding_box()
    c = bb.center()
    return Pos(c.X, c.Y, bb.max.Z + 0.5) * Cylinder(HARDPOINT["dia"] / 2 + 0.3,
                                                  HARDPOINT["depth"] + 0.5, align=(CC, CC, CMAX))


def mass_kg() -> float:
    """22 mm sandwich at 5.8 kg/m^2 (same areal density the hatch leaf check uses)."""
    return shell().volume / G.WALL * 5.8e-6


if __name__ == "__main__":
    import time
    t0 = time.time()
    g = section_geometry()
    print({k: (tuple(round(v, 2) for v in val) if isinstance(val, tuple) else round(val, 2))
           for k, val in g.items()})
    ob = outer_body()
    bb = ob.bounding_box()
    print("outer body vol %.3e  bbox x[%.1f,%.1f] y[%.1f,%.1f] z[%.1f,%.1f]  %.1fs" % (
        ob.volume, bb.min.X, bb.max.X, bb.min.Y, bb.max.Y, bb.min.Z, bb.max.Z, time.time() - t0))
    sh = shell()
    print("shell solids", len(sh.solids()), "vol %.3e  mass %.1f kg  %.1fs" % (
        sh.volume, mass_kg(), time.time() - t0))
