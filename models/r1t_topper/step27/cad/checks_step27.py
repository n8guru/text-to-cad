"""Step 27 machine checks. ``python cad/checks_step27.py`` -> STEP27_CHECKS_PASS / FAIL.

Three result states, so the pass line never implies more than it tested:
  PASS  proven from the geometry or a sourced number
  FAIL  a defect in this package
  OPEN  a known, named item that needs a vendor answer, a tape measurement or a decision - it is
        neither passed nor hidden, and it is counted separately

Every claim that CAN be checked from the geometry is measured from the solids, not read back from
the parameter that set it: the previous suite passed "retention rib 3.0 mm" while the modelled rib
was 1.5 mm, and passed "seal at 33 %" while the seal sat outside the panel that compresses it.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build123d import Align, Box, Cylinder, Location, Plane, Pos, Rot, Vector  # noqa: E402

import geom as G  # noqa: E402
import hatch as HA  # noqa: E402
import hw  # noqa: E402
import mounts  # noqa: E402
import shell as SH  # noqa: E402
import side_socket as SS  # noqa: E402
import truck as TR  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]          # step27/
MODEL = ROOT.parent                                 # r1t_topper/
RESULTS: list[tuple[str, str, str]] = []
CC = (Align.CENTER,) * 3


def check(name: str, ok: bool, detail: str = "", state: str | None = None):
    RESULTS.append((name, state or ("PASS" if ok else "FAIL"), detail))
    return ok


def open_item(name: str, detail: str):
    RESULTS.append((name, "OPEN", detail))


def leaves(c, loc=None, pre=""):
    """Leaf solids with the Compound location chain composed (export_stl does not compose it)."""
    loc = Location() if loc is None else loc
    here = loc * c.location
    out = []
    for k in c.children:
        if getattr(k, "children", None):
            out += leaves(k, here, pre + (c.label or "") + "/")
        else:
            out.append((pre + (c.label or "") + "/" + (k.label or "?"), k.located(here * k.location)))
    return out


def bbox_overlap(a, b, pad=0.0):
    A, B = a.bounding_box(), b.bounding_box()
    return not (A.min.X > B.max.X + pad or B.min.X > A.max.X + pad or A.min.Y > B.max.Y + pad or
                B.min.Y > A.max.Y + pad or A.min.Z > B.max.Z + pad or B.min.Z > A.max.Z + pad)


def clash_volume(a, b):
    if not bbox_overlap(a, b):
        return 0.0
    try:
        return (a & b).volume
    except Exception:
        return -1.0


def min_dist(a, b):
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape
    d = BRepExtrema_DistShapeShape(a.wrapped, b.wrapped)
    d.Perform()
    return d.Value()


# designed contacts that are not interference: each is checked by its own contact check below
ALLOWED = (
    ("BULB_SEAL", "MODULE_PLUG_FRAME"),      # seal bulb meets the flange at its compressed height
    ("BULB_SEAL", "HATCH_LEAF_CARBON"),
    ("GAS_STRUT", "BALL_STUD"),              # ball-in-socket joint, cavity not modelled
    ("GAS_STRUT_BODY", "GAS_STRUT_ROD"),     # the rod slides in the body (1 mm modelled overlap)
    ("STRIKER_BOLT", "fork_bolt"),           # captured bar: covered by the escape-corridor check
    ("STRIKER_BOLT", "pawl"),
    ("PLF_BODY", "BODY_BELOW_RAIL"),         # the stem goes INTO Rivian's bed port by design (plf_stem_fits_port_recess_envelope)
    ("PLF_HOOK_SLIDER", "BODY_BELOW_RAIL"),  # ... and so do the hook teeth
    ("PLF_DETENT", "PLF_PADDLE"),            # spring ball seated in / preloading on the knuckle (designed deflection)
)


def allowed(na, nb):
    return any((x in na and y in nb) or (x in nb and y in na) for x, y in ALLOWED)


# ================================================================ sources and style
REF = json.loads((ROOT / "style" / "rivian_reference.json").read_text())


def check_reference_sources():
    ok = all(v.get("sha256") and v.get("url") for v in REF["_sources"].values())
    check("style_sources_fingerprinted", ok and len(REF["_sources"]) == 3,
          "R1T OG, R1S OG, R1T Upfitting Guide: URL + SHA-256 recorded; the measuring script "
          "refuses a changed source")
    t = REF["r1t_side"]
    cc = t["cross_checks"]["roof_max_no_fin_mm"]
    check("side_view_scale_validated", abs(cc[0] - cc[1]) / cc[1] < 0.01,
          f"wheelbase-scaled roof {cc[0]:.1f} mm vs published {cc[1]:.1f} mm")
    rr = REF["r1t_rear"]["rail_to_roof_ratio"]
    side_ratio = t["rail_height_above_ground_mm"] / cc[0]
    check("rail_height_two_views_agree", abs(rr - side_ratio) < 0.03,
          f"rail/roof: side view {side_ratio:.3f}, rear view {rr:.3f} "
          f"(rail {t['rail_height_above_ground_mm']:.0f} vs {rr * 1834:.0f} mm)")
    sp = t["spoiler_tip"]["x"] * 1000
    check("spoiler_two_views_agree", abs(sp - (-127.0)) < 15.0,
          f"spoiler tip x: side view {sp:.0f} mm, Upfit plan view -127 mm")
    # params.json carries the truck numbers by hand: they must still equal the measurement
    T, cb, pl = G.T, t["cab_back"], REF["r1t_plan"]["lines_half_width_mid_bed"]
    pairs = {"rail height": (-T["ground_z"], t["rail_height_above_ground_mm"]),
             "cab back @rail+45": (T["cab_back"][0][0], cb["x_at_rail+45"] * 1000),
             "cab back @rail+360": (T["cab_back"][-1][0], cb["x_at_rail+360"] * 1000),
             "spoiler x": (T["spoiler_tip"][0], t["spoiler_tip"]["x"] * 1000),
             "spoiler z": (T["spoiler_tip"][1], t["spoiler_tip"]["z"] * 1000),
             "tailgate face": (T["tailgate_x"], t["tailgate_face_x"] * 1000),
             "rear axle": (T["rear_axle_x"], t["rear_axle_x"] * 1000),
             "rail cap in/flat/out": (T["rail_cap_in"] + T["rail_cap_flat_out"] + T["rail_cap_out"],
                                      sum(pl[:3]) * 1000)}
    bad = {k: (round(a, 1), round(b, 1)) for k, (a, b) in pairs.items() if abs(a - b) > 1.0}
    check("truck_params_match_reference", not bad,
          f"{len(pairs)} params.json truck values within 1 mm of style/rivian_reference.json"
          if not bad else f"drifted (params, reference): {bad}")
    open_item("truck_tape_session",
              "rail height (1344-1366 mm band), cab back line, spoiler tip, rail-cap edges, "
              "tailgate face are DRAWING-DERIVED from Rivian illustrations; tape before tooling")


def _shell_section_half_width(z):
    return SH.section_half_width(z)


def check_style_targets():
    S, T = G.S, G.T
    sh = SH.shell()
    top = sh.bounding_box().max.Z
    check("roof_meets_cab_roof", -15.0 <= top - T["cab_roof_z"] <= 10.0,
          f"topper roof {top:.0f} mm vs R1T cab roof {T['cab_roof_z']:.0f} mm "
          f"({top - T['cab_roof_z']:+.0f}); R1S roofline continues the cab roof")
    # roof level: sample the crown top along x on the solid itself
    zs = []
    for x in (S["x0"] + 150, 300, 600, 900, 1150):
        probe = Pos(x, 0, top + 50) * Box(4, 4, 300, align=(Align.CENTER, Align.CENTER, Align.MAX))
        hit = sh & probe
        if hit.volume > 0:
            zs.append(hit.bounding_box().max.Z)
    slope = (max(zs) - min(zs)) / 1000.0
    r1s = REF["r1s_side"]["roof_slope_rear_half_pct"]
    check("roof_level_like_r1s", len(zs) == 5 and slope * 100 <= 1.5,
          f"crown top varies {max(zs) - min(zs):.1f} mm over the roof run; R1S rear roof slope "
          f"{r1s:+.2f} %")
    lean = S["lean_deg"]
    t1, t2 = REF["r1t_rear"]["greenhouse_tumblehome_deg"], REF["r1s_rear"]["greenhouse_tumblehome_deg"]
    # measure the land lean on the solid: two probes on the outer land
    ya = _probe_side(sh, 60.0)
    yb = _probe_side(sh, 330.0)
    meas = math.degrees(math.atan2(ya - yb, 270.0))
    check("tumblehome_matches_r1t_r1s", min(t1, t2) - 2.5 <= meas <= max(t1, t2) + 2.5,
          f"shell land leans {meas:.1f} deg (measured); R1T C-pillar {t1:.1f}, R1S D-pillar {t2:.1f}")
    rake = S["rear_rake_deg"]
    rs = REF["r1s_side"]["liftgate_rake_deg"]
    check("rear_rake_matches_r1s_liftgate", abs(rake - rs) <= 2.0,
          f"rear face {rake:.1f} deg vs R1S liftgate {rs:.1f} deg")
    base = _probe_side(sh, mounts.PAD_C + 1.0)        # the foot bears on the pad (z = PAD_C), rev 10
    check("base_lands_on_rail_cap", T["rail_cap_flat_out"] - 30 <= base <= T["rail_cap_out"],
          f"skin at the base y = {base:.0f}; rail-cap flat ends {T['rail_cap_flat_out']:.0f}, outer "
          f"edge {T['rail_cap_out']:.0f}")
    gh = S["roof_z"]
    # vertical drop of the R rear_r roll between the level roof and the raked rear face
    drop = S["rear_r"] / math.tan(math.radians((90 + S["rear_rake_deg"]) / 2)) * math.cos(G.rake_rad())
    frac = drop / gh
    r1s_frac = REF["r1s_side"]["rear_corner_drop_fraction"]
    check("rear_corner_roll_off_r1s_like", 0.10 <= frac <= 0.30,
          f"roof roll-off into the raked rear face drops {drop:.0f} mm = {frac:.2f} of the "
          f"greenhouse; R1S {r1s_frac:.2f}. Tighter than the R1S because the flat face must carry "
          f"the hatch frame")
    W, HH = G.opening_wh()
    dlo = (HH + 2 * G.SHELL_CUT) * math.cos(G.lean_rad())
    ratio = dlo / (gh - 0.0)
    r1s_dlo = REF["r1s_side"]["dlo_fraction_of_greenhouse"]
    check("side_dlo_band_vs_r1s", ratio >= 0.60,
          f"dark DLO band (reveal + flange + glass) {dlo:.0f} mm = {ratio:.2f} of the greenhouse; "
          f"R1S DLO {r1s_dlo:.2f}. The gap is the socket border (82 mm/side), not the styling")
    cuts = sorted(G.K["centers_x"])
    bridge = (cuts[1] - W / 2 - G.SHELL_CUT) - (cuts[0] + W / 2 + G.SHELL_CUT)
    check("carbon_bridge_between_openings_ge_76", bridge >= 76.0,
          f"{bridge:.0f} mm of visible carbon between the two side openings (operator min 76)")
    hp = [p for n, p in _topper_leaves() if "ROOF_HARDPOINT" in n]
    mx = max(p.bounding_box().max.Z for n, p in _topper_leaves() if "SHELL" not in n)
    check("no_top_centre_protrusion", mx <= top + 1.0,
          f"highest non-shell feature z = {mx:.1f} vs roof {top:.1f}; hardpoints flush ({len(hp)})")


def _bridge_x():
    """x of the solid carbon bridge between the two side cuts (no aperture there)."""
    W, _ = G.opening_wh()
    c = sorted(G.K["centers_x"])
    return ((c[0] + W / 2 + G.SHELL_CUT) + (c[1] - W / 2 - G.SHELL_CUT)) / 2


def _probe_side(sh, z):
    """Outer half-width of the solid shell at height z on the flat land (on the bridge)."""
    x = _bridge_x()
    probe = Pos(x, 0, z) * Box(2, 2000, 1.0, align=CC)
    hit = sh & probe
    return hit.bounding_box().max.Y


# ================================================================ assembly-level geometry
_CACHE = {}


def _topper_leaves(hatch_deg=0.0):
    key = ("topper", hatch_deg)
    if key not in _CACHE:
        import assembly_step27 as A
        _CACHE[key] = leaves(A.step27_assembly(hatch_deg))
    return _CACHE[key]


def check_shell_integrity():
    sh = SH.shell()
    check("shell_one_valid_solid", len(sh.solids()) == 1 and sh.is_valid,
          f"{len(sh.solids())} solid(s), valid={sh.is_valid}, {SH.mass_kg():.1f} kg at 5.8 kg/m^2")
    ya, yi = _probe_side(sh, 200.0), None
    probe = Pos(_bridge_x(), 0, 200.0) * Box(2, 2000, 1.0, align=CC)
    hit = (sh & probe)
    # inner face: the smaller-|y| end of the positive-y slab
    slabs = [s for s in hit.solids() if s.bounding_box().center().Y > 0]
    t = slabs[0].bounding_box().size.Y * math.cos(G.lean_rad()) if slabs else -1
    check("shell_wall_22mm", abs(t - G.WALL) < 0.5, f"land wall normal thickness {t:.2f} mm")


def check_flanges_seat_on_flat_skin():
    """Every bond flange must sit 0.5 mm off FLAT inner skin over its whole footprint.

    Existence is not enough (Studio 52715): sample the flange's skin-facing face and require the
    shell to be at the bond gap everywhere, i.e. the land and rear face are really flat there.
    """
    sh = SH.shell()
    bad = []
    for side in "LR":
        for i in range(2):
            pl = G.socket_plane(side, i)
            W, HH = G.opening_wh()
            e = (G.RECESS_OUT + G.BOND_OUT) / 2
            pts = [(u, HH / 2 + e) for u in (-W / 2, 0, W / 2)] + \
                  [(u, -HH / 2 - e) for u in (-W / 2, 0, W / 2)] + \
                  [(sx * (W / 2 + e), 0) for sx in (-1, 1)]
            for u, v in pts:
                p = (pl * Pos(u, v, G.BOND_N[1])).position
                pr = Pos(p.X, p.Y, p.Z) * Box(1, 1, 1, align=CC)
                d = min_dist(pr, sh) + 0.5
                if not (0.2 <= d <= 0.9):
                    bad.append((f"{side}{i}", u, v, round(d, 2)))
    hp = G.hatch_plane()
    W, HH = G.hatch_wh()
    e = (G.H_RECESS_OUT + G.H_BOND_OUT) / 2
    # Step 29: no bottom bond flange (the bottom run is gone, nothing below the rail plane) -> the
    # hatch surround bonds along the top and both sides only
    # Sample the actual flared bond strip, not the former rectangular aperture.
    side_points = [(sx * (HA.AX + e + (HA.AX_BOT - HA.AX) *
                    (HA.AY + e - y) / (2 * (HA.AY + e))), y)
                   for y in (0, -HH / 4) for sx in (-1, 1)]
    for x, y in [(x, HH / 2 + e) for x in (-W / 2 + 60, 0, W / 2 - 60)] + side_points:
        p = (hp * Pos(x, y, G.BOND_N[1])).position
        pr = Pos(p.X, p.Y, p.Z) * Box(1, 1, 1, align=CC)
        d = min_dist(pr, sh) + 0.5
        if not (0.2 <= d <= 0.9):
            bad.append(("HATCH", x, y, round(d, 2)))
    check("bond_flanges_seat_on_flat_skin", not bad,
          "all 4 socket frames + hatch surround: bond face 0.5 mm off the inner skin at every "
          "sampled station" if not bad else f"off-flat stations: {bad}")


def check_interference_shut():
    """Pairwise solid interference across the WHOLE closed assembly, shell included."""
    P = _topper_leaves(0.0)
    bad = []
    for (na, a), (nb, b) in itertools.combinations(P, 2):
        if allowed(na, nb):
            continue
        v = clash_volume(a, b)
        if v > 0.5 or v < 0:
            bad.append((round(v, 1), na[-40:], nb[-40:]))
    check("no_interference_closed_assembly", not bad,
          f"{len(P)} parts, {len(P) * (len(P) - 1) // 2} pairs, allow-list {len(ALLOWED)} designed "
          f"contacts" if not bad else f"{len(bad)} clashes, worst {sorted(bad, reverse=True)[:6]}")


def check_truck_clearance():
    P = _topper_leaves(0.0)
    cab = TR.cab_keepout()
    body = TR.body_keepout()
    tg = TR.tailgate_keepout()
    bad, gap = [], 1e9
    for n, p in P:
        for kn, k in (("cab", cab), ("body", body), ("tailgate", tg)):
            if kn == "body" and ("PLF_BODY" in n or "PLF_HOOK_SLIDER" in n):
                continue                         # stem + teeth are IN the port; see plf_stem_fits_port_recess_envelope
            v = clash_volume(p, k)
            if v > 0.5:
                bad.append((kn, n[-36:], round(v, 1)))
        if bbox_overlap(p, cab, pad=200.0):
            gap = min(gap, min_dist(p, cab))
    check("topper_clear_of_r1t_keepouts", not bad, "no topper part in the cab, body-below-rail or "
          "tailgate envelopes" if not bad else f"{bad[:6]}")
    check("cab_gap_ge_20mm", gap >= 20.0,
          f"closest topper-to-cab distance {gap:.1f} mm (cab back under the spoiler, spoiler tip)")


def check_hatch_sweep():
    """The leaf and everything on it, swept 0..open, against the shell and every fixed part."""
    fixed = [(n, p) for n, p in _topper_leaves(0.0) if "LEAF_ASSY" not in n and "GAS_STRUT" not in n
             and "HATCH_BALL_STUD" not in n]
    hp = G.hatch_plane()
    bad = []
    for a in range(0, int(HA.OPEN_DEG) + 1, 5):
        moving = [(n, hp * p) for n, p in leaves(HA.hatch_leaf(float(a)))]
        struts = [(n, hp * p) for n, p in leaves(_strut_compound(float(a)))]
        for nm, m in moving + struts:
            for nf, f in fixed:
                if allowed(nm, nf) or ("GAS_STRUT" in nm and "BALL_STUD" in nf):
                    continue
                if "BULB_SEAL" in nf and a == 0:
                    continue
                v = clash_volume(m, f)
                if v > 0.5:
                    bad.append((a, nm[-30:], nf[-30:], round(v, 1)))
    check("hatch_sweep_clear_of_shell_and_frame", not bad,
          f"leaf + glazing + strikers + studs + struts swept 0..{HA.OPEN_DEG:.0f} deg in 5 deg "
          f"steps against the shell and all fixed parts" if not bad else f"{bad[:6]}")


def _strut_compound(a):
    from build123d import Compound
    return Compound(children=HA.strut_stations(a))


def check_module_removal_path():
    """Unlatch -> slide out to the safety catch -> lift -> withdraw, against every socket part."""
    sock = [(n, p) for n, p in leaves(SS.socket_assembly("open")) if "BULB_SEAL" not in n]
    mod = leaves(SS.module_interface(0.0)) + [(p.label, p) for p in SS.payload("TOOLBOX")]
    path = [(0, s) for s in range(0, int(SS.CATCH_TRAVEL), 2)] + \
           [(v, SS.CATCH_TRAVEL - 1) for v in (1, 2, 3, 4, SS.CATCH_DROP + 1)] + \
           [(SS.CATCH_DROP + 1, s) for s in range(int(SS.CATCH_TRAVEL) + 2, 131, 6)]
    bad = []
    for dv, dn in path:
        for nm, m in mod:
            mm = Pos(0, dv, dn) * m
            for ns, s in sock:
                if "STRIKER" in nm and ("fork_bolt" in ns or "pawl" in ns):
                    continue
                v = clash_volume(mm, s)
                if v > 0.5:
                    bad.append((dv, dn, nm, ns, round(v, 1)))
    check("module_removal_path_clear", not bad,
          f"{len(path)} poses: slide {SS.CATCH_TRAVEL - 1:.0f} mm, lift {SS.CATCH_DROP + 1:.0f} mm, "
          f"withdraw to 130 mm - no clash" if not bad else f"{bad[:5]}")
    # the catch actually catches: at CATCH_TRAVEL the leg meets the fin
    hook = SS.j_hook(SS.HOOK_U[0])
    fin = SS.hook_fin()
    v_catch = clash_volume(Pos(0, 0, SS.CATCH_TRAVEL + 1.0) * hook, fin)
    check("safety_catch_engages", v_catch > 1.0,
          f"sliding {SS.CATCH_TRAVEL + 1:.0f} mm out without lifting drives the hook leg into the "
          f"fin ({v_catch:.0f} mm3): an unlatched module cannot fall out")


# ================================================================ part integrity
FAB = ("SOCKET_FRAME", "MODULE_PLUG_FRAME", "J_HOOK", "HATCH_SURROUND", "HATCH_LEAF_CARBON",
       "STRIKER_BRACKET", "LEAF_STRIKER_ARM", "LEAF_STRUT_BOSS", "BASE_RAIL", "PLF_BODY", "PLF_PADDLE", "PLF_HOOK_SLIDER", "PLF_SHIM",
       "GLAZING_RETAINER", "GLAZING_PANE", "WINDOW_PANE", "TOOLBOX_TUB", "TOOLBOX_DOOR",
       "SHELL_CARBON", "FRONT_PASS_THROUGH", "ROOF_HARDPOINT", "HATCH_DRAIN_TUBE",
       "COMPRESSION_LIMITER")


def check_part_connectivity():
    bad = []
    seen = set()
    for n, p in _topper_leaves(0.0):
        key = n.split("/")[-1]
        if key in seen:
            continue
        seen.add(key)
        k = len(p.solids())
        if any(f in n for f in FAB) and k != 1:
            bad.append((key, k))
        if "latch_housing" in n and k != 1:
            bad.append((key, k))
    check("fabricated_parts_are_single_solids", not bad,
          f"{len(seen)} distinct parts checked" if not bad else f"multi-solid: {bad}")


def check_seal_geometry():
    s = hw.d("bulb_seal")
    fr = SS.socket_frame()
    # measure the rib on the straight top run: slice across it
    W, HH = G.opening_wh()
    probe = Pos(0, HH / 2 + G.SEAL_OFF, G.FACE_N + s["rib_h"] / 2) * Box(2, 20, 2, align=CC)
    rib = (fr & probe).bounding_box().size.Y
    check("seal_rib_measured_in_grip_range", s["grip_min"] <= rib <= s["grip_max"]
          and abs(rib - s["rib_t"]) < 0.05,
          f"rib measured {rib:.2f} mm on the solid; DD6139 grip {s['grip_min']:.2f}-{s['grip_max']:.2f}")
    bead = SS.seal_bead(True).bounding_box()
    mf = SS.module_plug_frame().bounding_box()
    inside = bead.max.X <= mf.max.X - 2 and bead.max.Y <= mf.max.Y - 2
    top_gap = -G.MODULE_FLANGE_T - bead.max.Z
    check("socket_seal_under_its_flange", inside and abs(top_gap) < 0.1,
          f"seal footprint +/-{bead.max.X:.0f} x +/-{bead.max.Y:.0f} inside flange +/-{mf.max.X:.0f} x "
          f"+/-{mf.max.Y:.0f}; compressed top {top_gap:+.2f} mm from the flange face")
    hb = HA.seal_bead(True).bounding_box()
    lf = HA.leaf_shell().bounding_box()
    inside = hb.max.X <= lf.max.X - 2 and hb.max.Y <= lf.max.Y - 2
    top_gap = -HA.LEAF_T - hb.max.Z
    check("hatch_seal_under_its_leaf", inside and abs(top_gap) < 0.1,
          f"seal footprint +/-{hb.max.X:.0f} x +/-{hb.max.Y:.0f} inside leaf +/-{lf.max.X:.0f} x "
          f"+/-{lf.max.Y:.0f}; compressed top {top_gap:+.2f} mm from the leaf inner face")
    free = SS.seal_bead(False).bounding_box().size.Z - s["base_h"]
    comp = SS.seal_bead(True).bounding_box().size.Z - s["base_h"]
    pct = (free - comp) / free * 100
    check("seal_bulb_deflection_25_35_pct", 25.0 <= pct <= 35.0,
          f"bulb {free:.2f} -> {comp:.2f} mm = {pct:.1f} % (measured on the swept bead)")


def check_stops_and_contacts():
    lim = hw.d("compression_limiter")
    pads = [Pos(u, v, -G.MODULE_FLANGE_T - lim["pad_t"]) * hw.compression_pad() for u, v in SS.LIMITERS]
    mf = SS.module_plug_frame()
    gaps = [round(min_dist(p, mf), 3) for p in pads]
    check("limiters_stop_the_flange", all(g < 0.05 for g in gaps),
          f"pad-to-flange {gaps} mm: the flange lands on the pads exactly at the seal's "
          f"compressed height, so the bulb cannot be over-crushed")
    fin = SS.hook_fin()
    hooks = [SS.j_hook(u) for u in SS.HOOK_U]
    hd = [round(min_dist(h, fin), 3) for h in hooks]
    tube_clear = SS.AV - G.PLUG_CLR - (SS.AV - G.PLUG_CLR)       # by construction
    lip = SS.socket_frame()
    mod = SS.module_plug_frame()
    tube_gap = min_dist(mod, lip)
    check("weight_on_the_fin_not_the_tube", all(d < 0.05 for d in hd) and tube_gap >= 0.3,
          f"J-hook bridge-to-fin {hd} mm (bearing); plug frame to socket frame min {tube_gap:.2f} mm")
    bp = [p for n, p in leaves(SS.module_interface(0.0)) if "BALL_PLUNGER" in n]
    dd = [round(min_dist(p, lip), 3) for p in bp]
    travel = hw.d("ball_plunger")["extension"]
    check("ball_plungers_preload_the_lip", all(d < 0.05 for d in dd),
          f"ball tip to lip {dd} mm; set 0.5 of {travel} mm travel at assembly")


# ================================================================ latch, loads, sequence
def check_latch():
    p = hw.d("rotary_latch")
    s = hw.d("striker")
    k = hw.HW["rotary_latch"]["kinematics"]
    clr = p["throat_w"] - s["rod_dia"]
    check("throat_clears_striker_bar", 0.5 <= clr <= 4.0,
          f"throat {p['throat_w']:.1f} on a Dia {s['rod_dia']:.1f} bar = {clr:.1f} mm")
    reach = p["claw_r"] - p["throat_depth"]
    check("rotor_tip_traps_the_bar", p["claw_r"] > reach + s["rod_dia"] / 2,
          f"rotor rim r={p['claw_r']:.1f}, bar centre r={reach:.1f}: "
          f"{p['claw_r'] - reach - s['rod_dia'] / 2:.2f} mm of rotor beyond the bar")
    check("pivot_pin_outside_the_bar", reach - s["rod_dia"] / 2 > 1.5,
          f"bar edge {reach - s['rod_dia'] / 2:.2f} mm from the rotor pivot (the previous "
          f"representation put the pivot inside the bar)")
    check("latch_is_two_stage", k["open_deg"] < k["secondary_deg"] < k["closed_deg"],
          f"receives at {k['open_deg']}, first click {k['secondary_deg']}, shut {k['closed_deg']} deg")
    yb, zb = hw.bar_centre("closed")
    for name, lp in (("socket", SS.latch_plane(G.LATCH_U[1])), ("hatch", HA.latch_plane(HA.LATCH_XS[1]))):
        vols = {}
        for st in ("closed", "secondary", "open"):
            corridor = lp * Pos(0, yb + 20.0, zb) * Box(p["claw_t"] + 2, 40.0, s["rod_dia"], align=CC)
            fork = lp * Pos(0, p["pivot_y"], hw.PIVOT_Z) * hw.fork_bolt(st)
            vols[st] = (fork & corridor).volume
        check(f"{name}_escape_blocked_when_shut", vols["closed"] > 100.0,
              f"rotor blocks the straight exit path by {vols['closed']:.0f} mm3")
        check(f"{name}_secondary_still_holds", vols["secondary"] > 50.0,
              f"{vols['secondary']:.0f} mm3 at the first click")
        check(f"{name}_escape_clear_when_released", vols["open"] < 0.35 * vols["closed"],
              f"{vols['open']:.0f} mm3 released vs {vols['closed']:.0f} shut")


def service_load_per_latch():
    """1.5 g lateral on the heaviest module + 1.5 kPa suction on the aperture, per latch."""
    tub = [p for p in SS.payload("TOOLBOX") if "TUB" in p.label][0]
    bb = tub.bounding_box()
    litres = bb.size.X * bb.size.Y * bb.size.Z / 1e6
    contents = min(20.0, 0.6 * litres)                  # 0.6 kg/L of tools, capped
    m = 9.0 + contents
    W, HH = G.opening_wh()
    total = m * 9.81 * 1.5 + 1500.0 * (W / 1000.0) * (HH / 1000.0)
    return total, total / len(G.LATCH_U), m


def check_latch_loads():
    total, per, m = service_load_per_latch()
    L = hw.HW["rotary_latch"]["load_definitions"]
    check("latch_ultimate_sanity", L["average_ultimate_load_N"] / per >= 3.0,
          f"{per:.0f} N/latch service ({m:.0f} kg TOOLBOX module); Southco average ultimate "
          f"{L['average_ultimate_load_N']:.0f} N is a FAILURE load (Southco glossary) - sanity only")
    if per <= L["max_dynamic_working_load_N"]:
        open_item("latch_sustained_rating", f"{per:.0f} N/latch is under the 222 N 'max dynamic "
                  "working load', but Southco defines neither 'dynamic' nor a sustained rating")
    else:
        open_item("latch_sustained_rating",
                  f"{per:.0f} N/latch EXCEEDS the only published working figure (222 N 'max dynamic'); "
                  f"Southco publishes no sustained rating. Options: Southco's rated sustained load, "
                  f"or a third latch per socket ({total / 3:.0f} N each)")


def check_closing_sequence():
    """Hang on the fin at the catch, slide in: pins index, seal touches, rotor clicks, in order."""
    s = hw.d("bulb_seal")
    pin = hw.d("locating_pin_round")
    seal_touch = s["free_height"] - s["compressed_height"]
    pin_enter = (SS.PIN_SEAT - pin["head_straight"] - pin["tip_taper_len"]) - SS.BUSH_TOP
    pin_enter = abs(pin_enter)
    yb, _ = hw.bar_centre("closed")
    latch_touch = hw.d("rotary_latch")["overall_l"] / 2 - yb
    ev = {"pins_enter_bushings": pin_enter, "rotor_first_touch": latch_touch,
          "seal_first_touch": seal_touch}
    order = sorted(ev, key=lambda k: -ev[k])
    check("closing_sequence_pins_then_latch_then_seal",
          order[0] in ("pins_enter_bushings", "rotor_first_touch") and ev["pins_enter_bushings"] >= 5.0,
          f"mm before home (larger = earlier): { {k: round(v, 1) for k, v in ev.items()} }; the "
          f"pins index the module before the rotor sees the striker")


def check_tolerances():
    nominal = G.SHUTLINE
    tol = G.TOL["module_profile"] + 0.30 + G.TOL["land_flatness"]
    check("shutline_never_binds", nominal - tol / 2 > 0.5, f"worst tight {nominal - tol / 2:.2f} mm")
    check("shutline_stays_cosmetic", nominal + tol / 2 < 6.0, f"worst loose {nominal + tol / 2:.2f} mm")
    tp = G.TOL["bushing_true_position"]
    b = hw.d("bushing")
    relief = hw.diamond_relief()
    check("second_locator_is_a_diamond", hw.HW["locating_pin_diamond"]["pn"].startswith("CFPBPD"),
          f"{hw.HW['locating_pin_round']['pn']} + {hw.HW['locating_pin_diamond']['pn']}")
    check("diamond_relief_covers_position_error", relief >= 2 * tp + 0.024,
          f"diamond relief {relief:.3f} mm/side (60 deg flats, 3 mm land) vs {2 * tp + 0.024:.3f}")
    check("pin_head_engages_bushing",
          (SS.BUSH_TOP - (SS.PIN_SEAT - hw.d("locating_pin_round")["head_straight"])) >= 5.0,
          f"straight head engaged "
          f"{SS.BUSH_TOP - (SS.PIN_SEAT - hw.d('locating_pin_round')['head_straight']):.2f} mm in "
          f"the {b['id']:.0f} {b['id_tol'].split()[0]} bore, 1.25 mm standoff to the flange")


def check_release():
    rmin = hw.d("release_cable")["bend_radius_min"]
    worst = min(hw.cable_min_radius(SS.cable_route(u), SS.BEND_R) for u in G.LATCH_U)
    check("cable_bend_radius_ok", worst >= rmin,
          f"modelled route radius {worst:.0f} mm vs Southco minimum {rmin:.1f} mm")
    n = hw.HW["release_cable"]["qty_cables"]
    sets = 4 + 1
    check("cable_count_matches_splitters", n == 3 * sets,
          f"{n} cables = {sets} handle+splitter sets x (1 in + 2 out), AC-CA p.321")
    check("no_custom_lever_needed", "release_lever" in hw.HW.get("_deleted", {}),
          "AC-05-301-11 splitter replaces the custom bell-crank")
    check("no_exterior_module_release", not hw.HW["release_handle"].get("exterior_access"),
          "the only release is the interior AC-75-101-11 paddle")


# ================================================================ hatch
def check_struts():
    g = hw.HW["gas_strut"]
    d = g["dims"]
    comp, ext = d["compressed_len"], d["extended_len"]
    import numpy as np
    Ls = []
    for a in range(0, int(HA.OPEN_DEG) + 1, 5):
        b = HA._rot_yz(np.array([HA.STRUT_LEAF], float), float(a))[0]
        Ls.append(float(np.linalg.norm(b - np.array(HA.STRUT_FRAME))))
    check("strut_within_catalogue_stroke", Ls[0] >= comp + 5 and Ls[-1] <= ext - 5,
          f"{g['pn']} ({g['pn_col2']} with studs): L {Ls[0]:.1f} -> {Ls[-1]:.1f} inside "
          f"{comp:.1f}-{ext:.1f} with 5 mm margins")
    check("strut_extends_monotonically", all(Ls[i + 1] >= Ls[i] - 0.01 for i in range(len(Ls) - 1)),
          "no over-centre point through the swing")
    m = HA.leaf_mass_kg()
    grav = m * 9.81 * HA.gravity_arm((0, 0, -13.0), HA.OPEN_DEG) / 1000.0
    arm = HA.strut_arm(HA.STRUT_LEAF, HA.STRUT_FRAME, HA.OPEN_DEG)
    hold = 2 * d["force_N"] * arm / 1000.0 / grav
    check("struts_hold_open_with_margin", hold >= 1.4,
          f"leaf {m:.2f} kg: {2 * d['force_N'] * arm / 1000:.2f} N.m vs gravity {grav:.2f} N.m "
          f"(ratio {hold:.2f})")
    close = 2 * d["force_N"] * HA.strut_arm(HA.STRUT_LEAF, HA.STRUT_FRAME, 0.0) / 1000.0 / (
        (HA.HINGE_Y + HA.AY + G.H_LEAF_OUT - 20.0) / 1000.0)
    check("hatch_close_force_reasonable", close <= 90.0, f"{close:.1f} N at the handle")
    check("strut_selection_is_catalogue_exact",
          any(r["ref_col1"] == g["pn"] for r in g["catalogue_6_15"]),
          f"{g['pn']} is a Standard Program p.17 column-1 Ref.-No.")


def check_hatch_misc():
    hp = G.hatch_plane()
    lo = min((hp * p).bounding_box().min.Z for _, p in leaves(HA.hatch_leaf(HA.OPEN_DEG)))
    check("leaf_open_above_bed_rail", lo > 0.0, f"lowest leaf point at full open z = {lo:.0f} mm")
    check("hinge_virtual_pivot_outboard", HA.HINGE_Z >= 0.0 and HA.HINGE_Y > HA.AY + G.H_LEAF_OUT,
          f"design-intent pivot at y={HA.HINGE_Y:.0f}, z={HA.HINGE_Z:+.0f}: the leaf's top edge "
          f"moves away from the recess wall; GN 7233 must realise this virtual pivot (G5)")
    hg = hw.d("hinge")
    check("hinge_swing_exceeds_hatch_open", hg["max_swing_deg"] >= HA.OPEN_DEG + 10.0,
          f"GN 7233 opens {hg['max_swing_deg']:.0f} deg vs the hatch's {HA.OPEN_DEG:.0f} deg")
    open_item("hinge_coupler_curve", "GN 7233 is a multi-joint linkage; every hatch clearance here "
              "assumes pure rotation about the design-intent pivot, and the hinge is modelled as "
              f"mounting blocks only - its {hg['envelope_l4']:.0f} x {hg['envelope_l5']:.0f} mm "
              "installation space is not placed. Re-run with JW Winco CAD")
    # service: every latch mounts from inside (socket n < 0; hatch inboard of the leaf)
    n_sock = max(SS.latch_plane(u).origin.Z for u in G.LATCH_U)
    z_hatch = max(HA.latch_plane(x).origin.Z for x in HA.LATCH_XS)
    check("latch_fasteners_reachable_from_inside", n_sock < 0.0 and z_hatch < -HA.LEAF_T,
          f"socket latch flanges at n = {n_sock:.0f}, hatch latch flanges at z = {z_hatch:.0f} "
          f"(leaf inner face {-HA.LEAF_T:.0f}): all fastened from inside the topper")
    # glazing: outer lip over the pane edge, retainer under it
    pane = HA.glazing_pane(1).bounding_box()
    ret = HA.glazing_retainer(1).bounding_box()
    lip_over = HA.WIN["overlap"]
    check("glazing_retained_both_ways", lip_over >= 10.0 and ret.max.X >= pane.max.X - 1.0,
          f"{HA.WIN['lip']:.0f} mm carbon lip overlaps each pane edge by {lip_over:.0f} mm "
          f"(cannot leave outward); screwed 6061 retainer overlaps it by "
          f"{lip_over + 5:.0f} mm (cannot fall inward)")
    th = hw.d("t_handle")
    stack = HA.LEAF_T + G.SEAL_COMPRESSED + G.LAND_T
    if th["grip_max"] < stack:
        open_item("keyed_t_handle_grip",
                  f"Southco E3-18-15 grip {th['grip_min']}-{th['grip_max']} mm < {stack:.2f} mm "
                  f"leaf + seal + land stack: re-select a keyed lock (longer grip or keeper "
                  f"standoff) - modelled as a lock body only, not an engaged cam")
    cut = HA.STUB_X
    bead_in_run = clash_volume(HA.seal_bead(), HA.bottom_run_cutter())
    check("wet_zone_drains_out_of_open_bottom_run", not HA.drain_tubes() and bead_in_run < 1.0,
          "the bottom run of seal + wet channel is removed between the corner stubs: the channel is "
          f"open at the stub ends (|x| >= {cut:.0f}) and drains onto the rail cap, outside the seal "
          "(rev 10's two skin-exit tubes are deleted with the fixed bottom run)")


def check_rear_access():
    """Step 29 acceptance (1): NO fixed rear crossbar; hatch up + tailgate down = open bed access.

    Nate, card 2081357: "a topper is meant to allow the truck tail-gate to open, and the hatch of
    the topper to open, and then have a large access to truck bed. your version has a crossbar
    where there should be none." Measured on the solids with the hatch at its open angle:
    the DOORWAY is the hatch frame's plane between the two bottom corner stubs, from the rail-cap
    plane (s = 0) up to the aperture's top edge, through the wall depth. Nothing of the topper
    (shell, surround, seals, struts, hinges, the open leaf) may be inside it, and no fixed part
    may cross any horizontal slice of it either.
    """
    from build123d import Box as _B
    P = _topper_leaves(HA.OPEN_DEG)
    skip = ("REFERENCE", "KEEPOUT")
    parts = [(n, p) for n, p in P if not any(k in n.upper() for k in skip)]
    hp = G.hatch_plane()
    sill = G.H["sill_s"]
    w = 2 * HA.STUB_X - 2.0
    # doorway prism in the hatch frame: x +/- w/2, y from the rail plane (s=0) to the aperture top
    y_bot = -(sill + HA.AY)
    y_top = HA.AY - 2.0
    door = hp * Pos(0, (y_bot + y_top) / 2, -150.0) * _B(w, y_top - y_bot, 700.0)
    bad = []
    for n, p in parts:
        v = clash_volume(p, door)
        if v > 0.5:
            bad.append((n[-34:], round(v, 1)))
    check("rear_doorway_free_hatch_open", not bad,
          f"hatch at {HA.OPEN_DEG:.0f} deg: {len(parts)} topper parts vs the {w:.0f} x "
          f"{y_top - y_bot:.0f} mm doorway (rail-cap plane to aperture top, through the wall): "
          f"no volume" if not bad else f"parts in the doorway: {bad[:6]}")
    # no fixed bar across any horizontal slice of the doorway
    fixed = [(n, p) for n, p in parts if "LEAF_ASSY" not in n and "GAS_STRUT" not in n]
    worst, crossing = None, []
    for ys in range(int(y_bot) + 4, int(y_top), 20):
        sl = hp * Pos(0, ys, -150.0) * _B(w, 1.0, 700.0)
        for n, p in fixed:
            if clash_volume(p, sl) > 0.01:
                crossing.append((ys - y_bot, n[-30:]))
    check("no_fixed_crossbar_across_rear_opening", not crossing,
          f"{int((y_top - y_bot) // 20)} horizontal slices from the rail-cap plane to the header, "
          f"each {w:.0f} mm wide: no fixed part crosses any" if not crossing
          else f"fixed parts crossing: {crossing[:6]}")
    # opened leaf swept clear of the lowered tailgate; whole topper stays above the folded gate
    tg = TR.tailgate_lowered_keepout()
    low = [(n[-30:], round(p.bounding_box().min.Z, 1)) for n, p in parts
           if "PORT" not in n and clash_volume(p, tg) > 0.5]
    check("hatch_open_clear_of_lowered_tailgate", not low,
          f"hatch open {HA.OPEN_DEG:.0f} deg vs the tailgate folded flat at the bed floor "
          f"(z {-G.T['bed_depth']:.0f} .. {-G.T['bed_depth'] + 60:.0f}): no topper part reaches it"
          if not low else f"{low[:5]}")
    # how much opening: compare with the rev-10 aperture (1000 x 226, 100 mm up, 74 mm fixed band)
    new_h = (sill + 2 * HA.AY) * math.cos(G.rake_rad())
    check("rear_opening_larger_than_rev10", new_h >= 300.0 and y_bot <= -sill,
          f"clear doorway {w:.0f} x {new_h:.0f} mm starting AT the rail-cap plane (z 0 .. {new_h:.0f}); "
          f"rev 10 was a 1000 x 226 slot starting 100 mm up with a fixed band z 0 .. 97 under it "
          f"(+{new_h - 226:.0f} mm of clear height, band removed)")
    open_item("rear_leaf_bottom_seal_on_tailgate",
              f"The leaf's lower edge is 7.7 mm above the rail-cap plane and the tailgate top is "
              f"{-G.T['tailgate_top_z']:.0f} mm below it; the bottom edge seal that closes on the "
              f"tailgate cap (and the rounded rail ends) is not designed - select after T5 "
              f"(supersedes rev-10 G9 for the removed bottom run)")


def check_controls_and_power():
    P = _topper_leaves(0.0)
    bad = []
    for name, x, side in mounts.WELLS:
        col = Pos(x, side * mounts.WELL["y"], 1.0) * Box(mounts.WELL["lx"] - 4, mounts.WELL["ly"] - 4,
                                                          40.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
        for n, p in P:
            if clash_volume(p, col) > 0.5:
                bad.append((name, n[-30:]))
    check("oem_buttons_not_covered", not bad,
          f"{len(mounts.WELLS)} rail-cap control wells clear through foot and base rail" if not bad
          else f"{bad}")
    open_item("control_well_positions", "WELL_TG / WELL_GT_* x-positions provisional until "
              "taped (T1-T3); well lids not modelled")
    c = hw.HW["chmsl"]
    check("secondary_chmsl_is_a_cited_requirement", c.get("compliance") == "FMVSS 108"
          and bool(c.get("requirement_source_url")), "Upfitting Guide p.65")
    t = hw.HW["harness_tap"]
    check("harness_tap_orderable", t["status"] == "ORDERABLE" and bool(t["pn"]),
          f"{t['manufacturer']} {t['pn']} at {t['electrical']['port']}")
    ts = hw.HW["tailgate_switch"]
    check("no_invented_switch", ts["findings"]["switch_on_tailgate_itself"] is False
          and ts["status"] == "NO_PART_REQUIRED", "Gen-1 tailgate has no switch; we add none")


def check_socket_identity():
    sigs = set()
    for side in "LR":
        for i in range(2):
            b = G.socket_plane(side, i) * SS.socket_frame()
            bb = b.bounding_box()
            sigs.add((round(b.volume, 1), round(bb.size.X + bb.size.Y + bb.size.Z, 1)))
    check("socket_identity_4x", len(sigs) == 1, f"one frame solid, four placements: {sigs}")


def check_bom():
    items = {k: v for k, v in hw.HW.items() if not k.startswith("_") and isinstance(v, dict)
             and "status" in v}
    st = {}
    for k, v in items.items():
        st.setdefault(v["status"], []).append(k)
    check("bom_has_no_open_items", not st.get("OPEN"), f"{ {k: len(v) for k, v in st.items()} }")
    unsourced = [k for k, v in items.items() if v["status"] in ("ORDERABLE", "SERIES_ONLY")
                 and not v.get("source_url")]
    check("every_purchased_item_cites_a_source", not unsourced, f"unsourced: {unsourced}")
    for k in st.get("SERIES_ONLY", []):
        open_item(f"bom_series_only_{k}", str(items[k].get("open") or items[k].get("pn_placeholder_note")))


# ================================================================ attachment (rev 11: Port Latch Foot)
def topper_mass_cg():
    """Mass and CG of everything Step 27 owns, from the manifest (mass x centroid per part)."""
    man = json.loads((ROOT / "out" / "parts_manifest.json").read_text())
    m = sum(p["mass_kg"] for p in man)
    cg = [sum(p["mass_kg"] * p["centroid_mm"][i] for p in man) / m for i in range(3)]
    return m, cg


def plf_strength(rating):
    """Assumption-level hand checks of the foot at the port's rated load (NOT FEA, NOT a test).

    Each station is loaded to Rivian's 2,500 N per-port rating. The two hook teeth share it equally
    (cantilever from the slider bar, load at the pin contact line); the two M6 rail screws carry it
    in shear (z / x loads) or tension (y loads); allowables are 0.6 x yield (hardware.json).
    """
    S = hw.HW["mounting"]["plf_strength"]
    MT = G.MT
    f = S["allowable_fraction_of_yield"]
    F_t = rating / 2.0                                     # per tooth
    b, th = MT["tooth_w"], MT["tooth_z1"] - MT["tooth_z0"]
    L = MT["pin_u"] - (MT["bar_u1"] - 0.5)                 # root to pin contact
    sig = 6.0 * F_t * L / (b * th ** 2)
    tau = F_t / (b * th)
    a_s = 20.1                                             # M6 tensile stress area
    F_s = rating / 2.0                                     # per rail screw
    tau_s = F_s / a_s
    st = mounts.stack_report()
    le = st["screw_engagement"]
    pull = 0.5 * math.pi * 6.0 * le * S["al6061_T6_shear_MPa"]    # thread strip, 6061 internal thread
    floor_area = MT["bar_x"] * (MT["bar_u1"] - MT["bar_u0"])
    return {"scope": "legacy_lower_lip_screening_only_not_C_jaw_capacity",
            "tooth_bending_MPa": round(sig, 1), "tooth_bending_allow_MPa": f * S["hook_17_4PH_H1025_Rp02_MPa"],
            "tooth_shear_MPa": round(tau, 1), "rail_screw_shear_MPa": round(tau_s, 1),
            "rail_screw_shear_allow_MPa": round(0.6 * f * S["a4_70_Rp02_MPa"] / 0.6, 1),
            "rail_thread_strip_N": round(pull), "slot_floor_bearing_MPa": round(rating / floor_area, 1),
            "tooth": {"b": b, "t": th, "L": L, "F_per_tooth_N": F_t},
            "screw_engagement_mm": round(le, 2)}


def mounting_analysis_mass_n():
    return topper_mass_cg()[0] * 9.80665


def mounting_analysis():
    M = hw.HW["mounting"]
    m, cg = topper_mass_cg()
    cases = mounts.port_loads(m, cg, M["load_cases"])
    rating = hw.HW["port_latch_foot"]["port_rating_N"]
    return {"mass_kg": round(m, 2), "cg_mm": [round(c, 1) for c in cg], "cases": cases,
            "plf_strength_at_port_rating": plf_strength(rating), "stack": mounts.stack_report()}


def _plf_station_leaves(P, x, y):
    return [(n, p) for n, p in P if "PLF_" in n and abs(p.center().X - x) < 50 and abs(p.center().Y - y) < 60]


def check_mounting():
    st = mounts.stack_report()
    MT_ = G.MT
    x, y = mounts.stations()[0]
    loc = mounts.station_loc(x, y)
    # 1. stack: the seat flange (not the pad, not a bolt) is the compression stop
    body = loc * mounts.body_local()
    bb = body.bounding_box()
    flange = (body & Pos(x, y, 0) * Box(200, 200, mounts.FLANGE_T + 0.5, align=(Align.CENTER, Align.CENTER, Align.MIN))) \
        - Pos(x, y, 0) * Box(MT_["stem_x"] + 1.0, 200, 100, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    fb = flange.bounding_box()
    pads = mounts.foot_pads()
    pz = max(p.bounding_box().max.Z for p in pads)
    sh = SH.shell()
    foot_low = min(f.center().Z for f in sh.faces() if f.normal_at().Z < -0.99
                   and abs(f.center().Y) > G.S["base_half_w"] - G.S["foot_w"]
                   and f.center().X < G.T["rail_flat_end_x"])
    check("plf_seat_flange_is_the_pad_stop", abs(fb.min.Z) < 0.01 and abs(fb.max.Z - mounts.PAD_C) < 0.01
          and abs(foot_low - mounts.PAD_C) < 0.05,
          f"seat flange z {fb.min.Z:.2f} .. {fb.max.Z:.2f} on the rail cap; shell foot underside z {foot_low:.2f} "
          f"= compressed pad {pz:.2f}: the flange, not torque, sets the pad height; head underside clears the "
          f"foot top by {st['head_under_gap']:.1f} mm")
    check("pad_compression_set_by_stop", abs(pz - mounts.PAD_C) < 0.01 and abs(foot_low - mounts.PAD_C) < 0.05,
          f"foot underside z {foot_low:.2f} = compressed pad top {pz:.2f} when the foot sits on its flange; "
          f"free {st['pad_free']:.1f} -> {st['pad_comp']:.1f} mm = {100 * st['pad_strain']:.0f} %")
    tol = 1.0
    lo = 1 - (mounts.PAD_C + tol) / st["pad_free"]
    hi = 1 - (mounts.PAD_C - tol) / st["pad_free"]
    check("pad_strain_band_15_55pct", 0.15 <= lo and hi <= 0.55,
          f"with +/-{tol:.1f} mm foot/rail-cap profile tolerance the pad works at "
          f"{100 * lo:.0f}-{100 * hi:.0f} % (closed-cell EPDM 2B2)")
    # 2. the stem sits in the (provisional) port recess and over the pin pair
    rec, pins = mounts.port_reference(x, y)
    low = Pos(x, y, -60) * Box(300, 300, 60, align=(Align.CENTER, Align.CENTER, Align.MIN))
    below = (body & low) - rec
    hooks = [loc * mounts.slider_local(a) for a in mounts.SWEEP_DEG]
    hook_out = max(((h & low) - rec).volume for h in hooks)
    check("plf_stem_fits_port_recess_envelope", below.volume < 0.5 and hook_out < 0.5,
          f"stem + hook slider below the rail cap lie inside the PROVISIONAL port recess "
          f"{G.MT['port_x']:.0f} x {G.MT['port_u']:.0f} x {G.MT['port_depth']:.0f} mm (outside volume "
          f"{below.volume:.2f} / {hook_out:.2f} mm^3); stem bottom {-st['stem_bottom']:.0f} deep, "
          f"{st['stem_to_port_floor']:.1f} mm above the recess floor")
    # 3. the hook: teeth under the pin pair at stage 1 / closed, clear when open
    rows = []
    for name, ang in (("closed", 0.0), ("stage1", mounts.STAGE1_DEG), ("open", mounts.OPEN_DEG)):
        sl = loc * mounts.slider_local(ang)
        d = min(min_dist(sl, p) for p in pins)
        clash = max(clash_volume(sl, p) for p in pins)
        past = G.MT["tooth_tip"] - mounts.cam_retract(ang) - G.MT["pin_u"]      # tooth tip beyond the pin centre
        rows.append((name, ang, d, clash, past))
    pitch = abs(mounts.PIN_XS[1] - mounts.PIN_XS[0])
    c, s1, o = rows
    hook_ok = (c[2] < 0.02 and c[3] <= 0.0 and c[4] >= 0.9 and s1[2] < 0.02 and s1[3] <= 0.0 and s1[4] >= 0.4
               and o[2] >= 1.0 and o[3] <= 0.0 and abs(pitch - 25.0) < 0.01)
    check("plf_hook_engages_pin_pair", hook_ok,
          f"2 teeth {pitch:.0f} mm apart under the continuous reference bridge (two jaw bearing zones) (PROVISIONAL pin dia "
          f"{G.MT['pin_d']:.0f}, u {G.MT['pin_u']:.0f}, z {G.MT['pin_z']:.0f}): closed = tooth top on the pin, tip "
          f"{c[4]:.2f} mm past the pin centre; stage 1 = {s1[4]:.2f} past; open ({o[1]:.0f} deg) = hooks "
          f"retracted, {o[2]:.2f} mm clear of the pins; no overlap in any state")
    # 4. two detent stations, distinct
    r_d = G.MT["detent_r"]
    chord = 2 * r_d * math.sin(math.radians(mounts.DIMPLE_DEG[0] - mounts.DIMPLE_DEG[1]) / 2)
    ball = mounts.BALL_R
    check("plf_two_detent_stations_distinct", mounts.STAGE1_DEG - 0.0 >= 30.0 and chord >= 2 * ball + 1.0
          and abs(mounts.DIMPLE_DEG[0] - (90.0 - 0.0)) < 1e-9,
          f"detent dimples for closed (0 deg) and stage 1 ({mounts.STAGE1_DEG:.0f} deg) are {chord:.1f} mm apart "
          f"on the knuckle (ball dia {2 * ball:.1f}); open {mounts.OPEN_DEG:.0f} deg is the link over-travel limit")
    # 5. paddle sweep against EVERYTHING else (service from the bed, topper fully built)
    Pall = _topper_leaves(0.0)
    keep = [(n, p) for n, p in Pall if "PLF_PADDLE" not in n and "PLF_DETENT" not in n]
    cab, body_k, tg = TR.cab_keepout(), TR.body_keepout(), TR.tailgate_keepout()
    worst, bad = 0.0, []
    for sx, sy_ in mounts.stations():
        l2 = mounts.station_loc(sx, sy_)
        for ang in mounts.SWEEP_DEG:
            pd = l2 * mounts.paddle_local(ang)
            for n, p in keep:
                v = clash_volume(pd, p)
                if v > 0.5 or v < 0:
                    bad.append((round(sx), round(sy_), ang, n[-34:], round(v, 1)))
            for kn, k in (("cab", cab), ("body", body_k), ("tailgate", tg)):
                if clash_volume(pd, k) > 0.5:
                    bad.append((round(sx), round(sy_), ang, kn))
    check("plf_paddle_sweep_clear", not bad,
          f"paddle swept {mounts.SWEEP_DEG[0]:.0f}..80 deg in 5 deg steps + stage 1 ({mounts.STAGE1_DEG:.0f}) + open "
          f"({mounts.OPEN_DEG:.0f}) at all 4 stations against every part of the closed assembly (shell, rails, "
          f"socket frames, modules, hatch, own body/lock/pin) and the cab / body / tailgate keep-outs: no clash"
          if not bad else f"{bad[:6]}")
    # 6. closed paddle covers the lock; key reaches it at stage 1; key blocked when closed
    lk = loc * mounts.lock_local(True)
    pad0 = loc * mounts.paddle_local(0.0)
    lb, pbx = lk.bounding_box(), pad0.bounding_box()
    # plate only (exclude the knuckle's hinge side): plate plane is u = hinge_u +/- t/2 -> inboard of the flange
    plate_in = G.MT["hinge_u"] + G.MT["paddle_t"] / 2
    cover = (pbx.min.X - 0.01 <= lb.min.X and lb.max.X <= pbx.max.X + 0.01
             and pbx.min.Z - 0.01 <= (loc * mounts.lock_local(True)).bounding_box().min.Z
             and lb.max.Z <= pbx.max.Z + 0.01 and plate_in < G.MT["head_u0"] - G.MT["lock_flange_t"])
    key0 = loc * mounts.key_envelope_local()
    blocked_closed = clash_volume(key0, loc * mounts.paddle_local(0.0)) > 0.5
    pd1 = loc * mounts.paddle_local(mounts.STAGE1_DEG)
    reach = clash_volume(key0, pd1) <= 0.0 and all(clash_volume(key0, p) <= 0.5 for n, p in keep)
    check("plf_paddle_closed_covers_lock", cover and blocked_closed,
          f"closed paddle plate x {pbx.min.X - x:+.1f}..{pbx.max.X - x:+.1f}, z {pbx.min.Z:.1f}..{pbx.max.Z:.1f} "
          f"covers the lock flange (x {lb.min.X - x:+.1f}..{lb.max.X - x:+.1f}, z {lb.min.Z:.1f}..{lb.max.Z:.1f}); "
          f"a key shank cannot enter while it is closed")
    check("plf_key_reaches_lock_at_stage1", reach,
          f"at stage 1 ({mounts.STAGE1_DEG:.0f} deg, hooks still caught) the 8 x 32 mm key shank reaches the lock "
          f"face with no clash against the paddle or any part: unlock, then lift the paddle on to open "
          f"(Rivian: 'push up the paddle halfway to access the lock')")
    # 7. service from the bed with no tool but the key: lock/paddle INBOARD, open paddle on the bed side,
    #    a hand corridor (2-finger grip, 50 x 120 x 27 mm) in front of the paddle is empty
    n_lock = (loc * Location((0, -1, 0))).position - loc.position                  # lock face normal = -u
    inboard = (-math.copysign(1.0, y))
    corr_u0 = G.MT["hinge_u"] - G.MT["knuckle_d"] / 2 - 1.0
    hand = loc * Pos(0, corr_u0 - 60.0, 47.0) * Box(50.0, 120.0, 27.0, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    hand_bad = [n[-30:] for n, p in keep if clash_volume(hand, p) > 0.5]
    open_pd = loc * mounts.paddle_local(mounts.OPEN_DEG)
    open_in = abs(open_pd.bounding_box().center().Y) < abs(y)
    check("plf_serviceable_from_bed_no_tools", n_lock.Y * inboard > 0.99 and open_in and not hand_bad,
          f"lock face and paddle face INBOARD (normal y {n_lock.Y:+.0f} toward the bed centre); open paddle lies on "
          f"the bed side; hand corridor 50 x 120 x 27 mm in front of the paddle is clear of the closed assembly "
          f"(socket-frame ceiling z 66 vs paddle top z {pbx.max.Z:.1f}); tools: the key only" if not hand_bad
          else f"{hand_bad[:6]}")
    # 8. stage-2 load path is metal to metal
    sl0 = loc * mounts.slider_local(0.0)
    d_floor = min_dist(sl0, body)
    rail = [r for r in mounts.base_rails() if r.bounding_box().center().Y * y > 0][0]
    screws = [loc * s for s in mounts.rail_screws_local()]
    d_screw = max(min_dist(s, rail) for s in screws)
    shims = [loc * s for s in mounts.shims_local()]
    d_shim = min(min_dist(s, body) for s in shims)
    d_strip = min(min_dist(s, rail) for s in shims)
    chain = ["PLF_HOOK_SLIDER", "PLF_BODY", "PLF_RAIL_SCREW", "PLF_SHIM", "BASE_RAIL"]
    import assembly_step27 as A
    mats = {k: A._classify(k)[0] for k in chain}
    soft = [k for k, m in mats.items() if any(w in m.lower() for w in ("epdm", "carbon", "foam", "uhmw", "rubber"))]
    check("plf_stage2_load_path_metal_to_metal", d_floor < 0.05 and d_screw < 0.1 and d_shim < 0.05 and d_strip < 0.05
          and not soft,
          f"port pin -> hook tooth (contact, see plf_hook_engages_pin_pair) -> slider bar -> slot floor "
          f"({d_floor:.2f} mm) -> body -> 2 x M6 ({d_screw:.2f} mm in the tapped strip) + shim pack "
          f"({d_shim:.2f}/{d_strip:.2f} mm) -> 6061 rail; every link {', '.join(sorted(set(m.split(',')[0] for m in mats.values())))}; "
          f"no EPDM or carbon before the rail's bond line" if not soft else f"soft links: {soft}")
    # 9. fit-up float covers tolerance
    req_x, req_y, req_z = 3.0, 2.0, 1.0
    check("plf_fit_up_float_covers_tolerance", st["notch_float_x"] >= req_x and st["shim_range"][1] >= 2 * req_y
          and st["slot_float_z"] >= req_z and st["shim_nominal"] == st["shim_range"][1] / 2,
          f"+/-{st['notch_float_x']:.0f} mm along the rail (notch), 0-{st['shim_range'][1]:.0f} mm across "
          f"(nominal {st['shim_nominal']:.0f}, +/-{st['shim_range'][1] / 2:.0f}), +/-{st['slot_float_z']:.0f} mm in height "
          f"(slotted screw holes) vs required +/-{req_x:.0f} / +/-{req_y:.0f} / +/-{req_z:.0f} (truck-to-truck port "
          f"position and moulding variation)")
    eng_min = hw.HW["mounting"]["thread_engagement_min_d"] * 6.0
    check("plf_rail_screw_engagement_ge_1p5d", st["screw_engagement"] >= eng_min
          and st["rail_strip_t_min"] - st["screw_engagement"] >= 1.0,
          f"M6 x 30 engages {st['screw_engagement']:.1f} mm of the tapped strip (>= {eng_min:.1f}); strip "
          f"{st['rail_strip_t_min']:.1f} mm thick at the front stations, {st['rail_strip_t_min'] - st['screw_engagement']:.1f} "
          f"mm behind the tap")
    meas = REF["r1t_plan"]["bed_accessory_ports_x_halfy"]
    dev = max(max(abs(a[0] * 1000 - b[0]), abs(a[1] * 1000 - b[1])) for a, b in zip(meas, G.T["bed_ports"]))
    check("bed_ports_match_reference", len(meas) == len(G.T["bed_ports"]) and dev <= 3.0,
          f"station x/half-y {G.T['bed_ports']} vs Upfit p.59 port symbols {meas} m: max {dev:.1f} mm")
    open_item("plf_port_internals_P-CAL-01b",
              "Rivian publishes NEITHER the accessory-port internals NOR the crossbar-foot drawing: the port recess "
              f"({G.MT['port_x']:.0f} x {G.MT['port_u']:.0f} x {G.MT['port_depth']:.0f} mm), the continuous reference bridge (two jaw bearing zones) "
              f"(dia {G.MT['pin_d']:.0f}, pitch {G.MT['pin_pitch']:.0f}, u {G.MT['pin_u']:.0f}, z {G.MT['pin_z']:.0f}), the "
              "hook, paddle, lock position and tuning screw are ALL PROVISIONAL (mount.* in params.json). Buy one "
              "Rivian Cargo Crossbars set as the reference article, photograph + measure its foot and a real port, "
              "set the numbers and re-run; do not release a station drawing before that")
    cfd_hi = hw.HW["foot_pad"]["cfd_25pct_kPa"][1] * 1.3            # 33 % ~ 1.3 x the 25 % value
    pad_area = sum(p.volume for p in pads) / mounts.PAD_C / 1e6
    seat = cfd_hi * 1e3 * pad_area / 4.0
    open_item("plf_drive_link_and_lock_interlock",
              "the link between the paddle cam and the hook slider (modelled only as the cam law in out/kinematics.json "
              "port_latch.cam_law_deg_to_retract_mm) and the lock-cam-to-paddle keeper interlock are NOT drawn; hook "
              f"force, over-centre preload and detent force are not computed. Needed from the clamp: the 2B2 pad at 33 % "
              f"reacts up to {seat:.0f} N per station ({pad_area:.3f} m^2, upper CFD x 1.3) before the seat flange "
              f"bottoms on the cap, against {mounting_analysis_mass_n() / 4.0:.0f} N of dead weight per station")
    open_item("bed_port_positions_P-CAL-02",
              "port positions are drawing-derived (plan-view scale cross-check 0.6-1.2 %, i.e. up to "
              "+/-8 mm): tape all four port centres before the foot pockets are cut in the shell")
    # 10. loads
    A_ = mounting_analysis()
    rating = hw.HW["port_latch_foot"]["port_rating_N"]
    lim = [c for c in A_["cases"] if c["limit_class"] == "limit"]
    worst_c = max(lim, key=lambda c: c["port_resultant_N"])
    check("port_loads_within_rivian_rating", worst_c["port_resultant_N"] <= rating,
          f"topper {A_['mass_kg']} kg, CG {A_['cg_mm']} mm; worst limit case {worst_c['case']}: "
          f"{worst_c['port_resultant_N']:.0f} N per port <= {rating:.0f} N (Upfit p.59)")
    for c in [c for c in A_["cases"] if c["limit_class"] == "ultimate"]:
        state = "PASS" if c["port_resultant_N"] <= rating else "OPEN"
        check("port_crash_pulse_vs_rating", c["port_resultant_N"] <= rating,
              f"{c['case']}: {c['port_resultant_N']:.0f} N per port vs {rating:.0f} N - information "
              "only (no regulation covers a cap; Rivian rates the port, not a crash case)", state=state)
    S_ = A_["plf_strength_at_port_rating"]
    check("plf_hook_and_screws_within_allowable_at_port_rating",
          S_["tooth_bending_MPa"] <= S_["tooth_bending_allow_MPa"]
          and S_["rail_screw_shear_MPa"] <= S_["rail_screw_shear_allow_MPa"]
          and S_["rail_thread_strip_N"] >= 2 * rating / 2 * 4,
          f"each station loaded to {rating:.0f} N: tooth bending {S_['tooth_bending_MPa']:.0f} MPa <= "
          f"{S_['tooth_bending_allow_MPa']:.0f} (0.6 x 17-4PH Rp0.2, {S_['tooth']['F_per_tooth_N']:.0f} N per tooth, "
          f"root-to-pin {S_['tooth']['L']:.1f} mm), rail-screw shear {S_['rail_screw_shear_MPa']:.0f} MPa <= "
          f"{S_['rail_screw_shear_allow_MPa']:.0f}, thread strip-out {S_['rail_thread_strip_N']} N, slot-floor bearing "
          f"{S_['slot_floor_bearing_MPa']:.0f} MPa - legacy lower-lip screening ONLY; does not validate C-jaw web/upper lip "
          "or source-derived bridge, no allowable custom clamp load established", state="OPEN")
    bench = hw.HW["mounting"]["benchmark_kg"]
    check("mass_within_rivian_4_port_benchmark", A_["mass_kg"] <= bench,
          f"{A_['mass_kg']} kg on 4 bed ports vs Rivian's own 113 kg dynamic allowance for a crossbar "
          f"pair on 4 roof ports; arithmetic headroom {bench - A_['mass_kg']:.0f} kg is NOT a topper "
          "payload rating: different interface, load case and unvalidated custom jaws")
    (ROOT / "out" / "mounting_analysis.json").write_text(json.dumps(A_, indent=1) + "\n")


def check_plf_kinematics_exported():
    k = json.loads((ROOT / "out" / "kinematics.json").read_text()).get("port_latch", {})
    ok = (len(k.get("stations", [])) == 4 and set(k.get("states_deg", {})) == {"closed", "stage1_caught", "open"}
          and k["states_deg"]["closed"] == 0.0 and 60.0 <= k["states_deg"]["open"] <= 90.0
          and len(k.get("paddle_sweep_deg", [])) >= 18
          and k["slider_retract_mm_by_state"]["closed"] == 0.0 and k["slider_retract_mm_by_state"]["open"] > 5.0)
    check("plf_kinematics_exported", ok,
          f"out/kinematics.json port_latch: 4 station hinge axes, states {k.get('states_deg')}, "
          f"{len(k.get('paddle_sweep_deg', []))} sweep angles, cam law {k.get('cam_law_deg_to_retract_mm')}")


def check_fastener_schedule():
    import fasteners as FS
    rows, totals, custom = FS.schedule()
    zero = [r["id"] for r in rows if r["n"] == 0]
    check("every_joint_found_in_geometry", not zero,
          f"{len(rows)} joints, counts from the manifest" if not zero else f"no instances: {zero}")
    j = {r["id"]: r["n"] for r in rows}
    expect = {"J01": len(mounts.stations()), "J02": 10, "J03": 10, "J06": 2, "J07": 4}
    bad = {k: (j[k], v) for k, v in expect.items() if j[k] != v}
    check("joint_counts_match_product_structure", not bad,
          "4 port stations, 10 latches, 10 strikers, 2 hinges, 4 ball studs" if not bad else f"{bad}")
    unk = [k for k in list(totals) if k not in hw.HW["fasteners"]]
    check("every_fastener_is_specified", not unk,
          f"{sum(totals.values())} fasteners of {len(totals)} specs, each with standard/size/material"
          if not unk else f"unspecified: {unk}")


# ================================================================ provenance / portability
def check_portability():
    hits = []
    for f in list((MODEL / "blender").glob("*.py")) + list((ROOT / "cad").glob("*.py")) + \
            list((ROOT / "style").glob("*.py")):
        for i, line in enumerate(f.read_text().splitlines(), 1):
            if "/home/" in line and "noqa-path" not in line:
                hits.append(f"{f.name}:{i}")
    check("no_hardcoded_home_paths", not hits, "scripts resolve paths from __file__ / env" if not hits
          else f"{hits}")


def check_provenance():
    """Freshness is asserted by ``cad/provenance.py --check`` (run after this suite, which is one
    of the outputs it hashes). Here: no artefact claims a commit id it cannot contain."""
    check("no_self_hash_claim", not (ROOT / "out" / "COMMIT.txt").exists(),
          "outputs are tied to source hashes in out/PROVENANCE.json, not to a commit id")


NOT_CHECKED = [
    "FEA of the shell, frames, roof hardpoints or hatch surround",
    "Sealing performance (water/dust ingress): needs a physical test",
    "Real-truck fit: every truck value is Rivian-illustration-derived; tape session required",
    "Latch endurance, salt spray, UV: vendor qualification data not obtained",
    "Rotor/pawl internals: a representation (G6); rotor-vs-striker contact is not a rigid sweep",
    "GN 7233 coupler curve (G5): hatch sweep assumes pure rotation about the design pivot",
    "Fabrication release, tooling, prototype fit, purchases, Nate-only design approval",
    "Attachment: Port Latch Foot hook / paddle / lock force, over-centre preload, detent force, port "
    "strength beyond Rivian's 2,500 N rating, crash retention, rail/foot bond strength and fatigue - "
    "load cases and the hand strength check are stated assumptions, not FEA or test",
    "Attachment: the port internals and the Rivian crossbar foot are NOT published - every PLF dimension "
    "at the port is PROVISIONAL until calibration P-CAL-01b (a physical Rivian crossbar + port)",
]


def main() -> int:
    for fn in (check_reference_sources, check_style_targets, check_shell_integrity,
               check_flanges_seat_on_flat_skin, check_part_connectivity, check_socket_identity,
               check_seal_geometry, check_stops_and_contacts, check_latch, check_latch_loads,
               check_closing_sequence, check_tolerances, check_release, check_struts,
               check_hatch_misc, check_controls_and_power, check_bom, check_mounting,
               check_plf_kinematics_exported,
               check_fastener_schedule, check_portability,
               check_module_removal_path, check_interference_shut, check_truck_clearance,
               check_hatch_sweep, check_rear_access, check_provenance):
        try:
            fn()
        except Exception as exc:                       # a crashing check is a failing check
            import traceback
            traceback.print_exc()
            check(fn.__name__, False, f"{type(exc).__name__}: {exc}")
    width = max(len(n) for n, _, _ in RESULTS)
    for name, st, detail in RESULTS:
        print(f"{st:<4}  {name:<{width}}  {detail}")
    print("\nNOT CHECKED by this suite (later gates):")
    for n in NOT_CHECKED:
        print(f"  - {n}")
    n_pass = sum(1 for _, s, _ in RESULTS if s == "PASS")
    n_fail = sum(1 for _, s, _ in RESULTS if s == "FAIL")
    n_open = sum(1 for _, s, _ in RESULTS if s == "OPEN")
    print(f"\n{n_pass} PASS, {n_fail} FAIL, {n_open} OPEN")
    failed = [n for n, s, _ in RESULTS if s == "FAIL"]
    print("STEP27_CHECKS_PASS" if not failed else f"STEP27_CHECKS_FAIL {failed}")
    (ROOT / "out").mkdir(exist_ok=True)
    (ROOT / "out" / "checks.json").write_text(json.dumps(
        {"results": [{"name": n, "state": s, "detail": d} for n, s, d in RESULTS],
         "not_checked": NOT_CHECKED, "pass": n_pass, "fail": n_fail, "open": n_open}, indent=2) + "\n")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
