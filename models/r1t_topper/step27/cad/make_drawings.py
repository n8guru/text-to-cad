"""Dimensioned drawing sheets for the CUSTOM parts, plus an exploded view. SVG, no dependencies.

    python cad/make_drawings.py

Purchased parts do not get a drawing — they get a part number, which is in BOM27.md. Only parts we
control need a controlled drawing, and every one of them gets one here:

  DWG-27-000  carbon shell (styled)     DWG-27-006  compression limiter
  DWG-27-001  socket frame (top-hat)    DWG-27-007  J-hook
  DWG-27-003  module plug frame         DWG-27-008  hatch surround (top-hat)
  DWG-27-004  striker bracket           DWG-27-010  base rail + OEM control-well cut-outs
  DWG-27-011  hatch leaf (inside-glazed)
  DWG-27-012  Port Latch Foot body              DWG-27-013  PLF paddle + hook slider + shim
  DWG-27-014..020  glazing/retainer, cage, toolbox, window pane, hardpoint + potted insert,
                   leaf arm + strut boss, front pane
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build123d import Axis, ExportSVG, LineType, Plane, Pos, Vector  # noqa: E402

import geom as G  # noqa: E402
import hatch as HA  # noqa: E402
import hw  # noqa: E402
import mounts  # noqa: E402
import shell as SH  # noqa: E402
import side_socket as SS  # noqa: E402

DWG = Path(__file__).resolve().parents[1] / "drawings"


def sheet(name, shape, plane, title, dims, notes, scale=0.35):
    """One drawing sheet: an outline projection, dimension callouts, and a notes block."""
    DWG.mkdir(parents=True, exist_ok=True)
    ex = ExportSVG(scale=scale, margin=30)
    ex.add_layer("outline", line_weight=0.6, line_type=LineType.CONTINUOUS)
    ex.add_layer("hidden", line_weight=0.25, line_type=LineType.DASHED)
    # A true orthographic projection, not a planar section: ExportSVG.add_shape on a solid trips
    # over full circles (svgpathtools rejects a zero-length arc), and a section only shows one cut.
    o = plane.origin + plane.z_dir * 4000.0
    vis, hid = shape.project_to_viewport(
        viewport_origin=tuple(o), viewport_up=tuple(plane.y_dir), look_at=tuple(plane.origin))
    ex.add_shape(vis, layer="outline")
    if hid:
        ex.add_shape(hid, layer="hidden")
    path = DWG / f"{name}.svg"
    ex.write(str(path))
    txt = path.read_text()
    y = 20
    block = [f'<text x="12" y="{y}" font-family="monospace" font-size="15" '
             f'font-weight="bold">{name}  {title}</text>']
    y += 20
    block.append(f'<text x="12" y="{y}" font-family="monospace" font-size="11">'
                 f'DIMENSIONS (mm) — all from step27/hardware.json + blender/params.json</text>')
    for k, v in dims:
        y += 14
        block.append(f'<text x="18" y="{y}" font-family="monospace" font-size="11">'
                     f'{k:.<46}{v}</text>')
    y += 22
    block.append(f'<text x="12" y="{y}" font-family="monospace" font-size="11" '
                 f'font-weight="bold">NOTES</text>')
    for i, n in enumerate(notes, 1):
        y += 14
        block.append(f'<text x="18" y="{y}" font-family="monospace" font-size="11">'
                     f'{i}. {n}</text>')
    y += 22
    block.append(f'<text x="12" y="{y}" font-family="monospace" font-size="10" '
                 f'fill="#a00">NOT RELEASED FOR FABRICATION. Uncalibrated against the physical '
                 f'vehicle. No FEA performed.</text>')
    path.write_text(txt.replace("</svg>", "".join(block) + "</svg>"))
    return path


def main():
    made = []
    W, HH = G.opening_wh()
    S = G.S
    sl = hw.d("bulb_seal")
    b = hw.d("bushing")
    lim = hw.d("compression_limiter")
    stamp = ("All socket/hatch border offsets are measured OUTWARD FROM THE APERTURE EDGE and are "
             "shared with the module, seal, shell cut and checks (cad/geom.py).")

    made.append(sheet(
        "DWG-27-000_carbon_shell", SH.shell(), Plane.XZ,
        "CARBON SHELL, 22 mm SANDWICH, 1 OFF - styled A-surface, authoritative",
        [("length at rail, x0 .. x1", f'{S["x0"]:.0f} .. {S["x1"]:.0f}'),
         ("roof crown top z (R1T cab roof 463)", f'{S["roof_z"]:.0f}'),
         ("crown drop at y=550", f'{S["roof_crown"]:.0f}'),
         ("base half-width at rail", f'{S["base_half_w"]:.0f}'),
         ("side land lean (tumblehome)", f'{S["lean_deg"]:.1f} deg'),
         ("shoulder radius", f'R{S["shoulder_r"]:.0f}'),
         ("front face / roll radius", f'vertical at x0 / R{S["front_r"]:.0f}'),
         ("rear face rake / roll + corner radius", f'{S["rear_rake_deg"]:.0f} deg / R{S["rear_r"]:.0f}'),
         ("wall (sandwich envelope)", f'{G.WALL:.0f}'),
         ("socket cut, offset from aperture", f"{G.SHELL_CUT:.1f}"),
         ("hatch cut, offset from aperture", f"{G.H_SHELL_CUT:.1f}"),
         ("rail-cap foot width", f'{S["foot_w"]:.0f}'),
         ("mass estimate (5.8 kg/m^2)", f"{SH.mass_kg():.1f} kg")],
        ["Styling targets and sources: step27/style/STYLE27.md; truck values from Rivian line art "
         "(rivian_reference.json), TAPE-REQUIRED.",
         "The flat side land and the flat raked rear face carry every bond flange: flatness 0.3 "
         "over each socket footprint (bond_flanges_seat_on_flat_skin).",
         "Layup per the Step 11 schedule; this sheet controls the envelope, cuts and datums only."],
        scale=0.18))

    made.append(sheet(
        "DWG-27-001_socket_frame", SS.socket_frame(), Plane.XY,
        "SOCKET FRAME, 6061-T6 TOP-HAT, 4 OFF (one program, one fixture)",
        [("aperture W x H (in land plane)", f"{W:.1f} x {HH:.1f}"),
         ("aperture corner radius", f'{G.K["corner_r"]:.1f}'),
         ("seal land plate, offsets / t", f"0 .. {G.RECESS_OUT:.0f} / {G.LAND_T:.0f}"),
         ("seal rib, offset / t x h", f'{G.SEAL_OFF:.0f} / {sl["rib_t"]:.1f} x {sl["rib_h"]:.0f}'),
         ("recess wall, offsets", f"{G.RECESS_IN:.0f} .. {G.RECESS_OUT:.0f}"),
         ("bond flange, offsets / n", f"{G.RECESS_OUT:.0f} .. {G.BOND_OUT:.0f} / {G.BOND_N[0]:.1f}..{G.BOND_N[1]:.1f}"),
         ("return lip t x depth", f"{G.LIP_T:.0f} x {G.LIP_DEPTH:.0f}"),
         ("hook fin seat v", f"{SS.FIN_TOP:.1f}"),
         ("bushing bores", f'Dia {b["od"]:.0f} H7 at u = {G.PIN_U[0]:.0f} / {G.PIN_U[1]:.0f}, v = {HH / 2 + G.PIN_OFF:.1f}'),
         ("latch stations", f"u = {G.LATCH_U[0]:.0f} / {G.LATCH_U[1]:.0f}, panel v = {SS.LATCH_VP:.1f}"),
         ("seal land datum", f"n = {G.FACE_N:.2f}")],
        [stamp,
         f'Bushing pair true position {G.TOL["bushing_true_position"]} to datum A-B; land flatness '
         f'{G.TOL["land_flatness"]}.',
         "Rib thickness 3.00 +/-0.05 is a DD6139 grip dimension (1.52-3.18), not cosmetic.",
         "Limiter bosses: top = n -13.40 +0/-0.05 with the 7.40 pad; they set the seal compression."],
        scale=0.45))

    made.append(sheet(
        "DWG-27-003_module_plug_frame", SS.module_plug_frame(), Plane.XY,
        "MODULE PLUG FRAME, 6061-T6, 1 PER MODULE (common to WINDOW / CAGE / TOOLBOX)",
        [("flange, offsets / t", f"{G.MF_IN:.0f} .. {G.MF_OUT:.0f} / {G.MODULE_FLANGE_T:.0f}"),
         ("plug tube, offsets / depth", f"-11 .. {-G.PLUG_CLR:.0f} / {G.PLUG_DEPTH:.0f}"),
         ("visible shut line", f"{G.SHUTLINE:.1f}"),
         ("pin bosses", f"Dia 18, seat n = {SS.PIN_SEAT:.2f}, Dia 6 H7 press bore"),
         ("striker arms", f"u = latch + {SS.ARM_DU[0]:.1f} .. {SS.ARM_DU[1]:.1f}, M10 tapped"),
         ("outer profile tolerance", f'{G.TOL["module_profile"]}')],
        [stamp, "Outer profile sets the visible 4 mm shut line to the frame recess wall."],
        scale=0.45))

    made.append(sheet(
        "DWG-27-004_striker_bracket", SS.striker_bracket_at(0.0), SS.striker_plane(0.0),
        "STRIKER BRACKET, 316, 10 OFF", [
            ("plate", f'{SS.BRACKET["n"]:.0f} x {SS.BRACKET["v"]:.0f} x {SS.BRACKET["t"]:.0f}'),
            ("striker hole", "10.6 x 16.6 slot, +/-3 mm fit-up along the closing travel"),
            ("mates", f'Southco {hw.HW["striker"]["pn"]}')],
        ["The slot dials the module tolerance stack out at assembly instead of scrapping parts."],
        scale=2.0))

    made.append(sheet(
        "DWG-27-006_compression_limiter", hw.compression_pad(), Plane.XY,
        "COMPRESSION LIMITER PAD, UHMW-PE, 12 OFF", [
            ("pad l x w", f'{lim["pad_l"]:.0f} x {lim["pad_w"]:.0f}'),
            ("THICKNESS", f'{lim["pad_t"]:.2f} +0 / -0.05'),
            ("clearance hole", f'dia {lim["hole_dia"]:.1f}'),
            ("stack", "sits on a 12.85 frame boss: boss + pad = the seal's compressed height")],
        ["The previous pad sat 12.85 mm short of the flange and stopped nothing; the boss fixes that."],
        scale=3.0))

    made.append(sheet(
        "DWG-27-007_j_hook", SS.j_hook(0.0), Plane.YZ, "J-HOOK, 316 STAINLESS 6 mm, 8 OFF", [
            ("bridge seat", f"v = {SS.FIN_TOP:.1f} (rests on the frame fin)"),
            ("safety catch travel", f"{SS.CATCH_TRAVEL:.0f} mm before the leg meets the fin"),
            ("leg drop below fin top", f"{SS.CATCH_DROP:.0f} mm (lift 5 to clear)")],
        ["Carries the module weight into the fin; the leg is an anti-fall catch, not the pivot."],
        scale=1.2))

    made.append(sheet(
        "DWG-27-008_hatch_surround", HA.hatch_surround(), Plane.XY,
        "HATCH SURROUND, 6061-T6 TOP-HAT, 1 OFF", [
            ("aperture W x H", f"{HA.W:.1f} x {HA.HH:.1f}"),
            ("corner radius", f"{HA.CR:.1f}"),
            ("seal, offset", f"{G.H_SEAL_OFF:.0f}"),
            ("recess wall, offsets", f"{G.H_RECESS_IN:.0f} .. {G.H_RECESS_OUT:.0f}"),
            ("bond flange, offsets", f"{G.H_RECESS_OUT:.0f} .. {G.H_BOND_OUT:.0f}"),
            ("latch stations", f"x = {HA.LATCH_XS[0]:.0f} / {HA.LATCH_XS[1]:.0f}, closed bar "
                               f"y {HA.BAR_Y:.0f} z {HA.BAR_Z:.0f}, slot tilt {HA.LATCH_TILT:.1f} deg"),
            ("strut frame studs", f"({HA.STRUT_FRAME[0]:.0f}, {HA.STRUT_FRAME[1]:.0f}, {HA.STRUT_FRAME[2]:.0f})"),
            ("seal land datum", f"z = {HA.FACE_Z:.2f}")],
        [stamp, "Wet channel between seal and recess wall drains at both ends of the bottom run."],
        scale=0.3))

    st = mounts.stack_report()
    MT = G.MT
    stn = ", ".join(f"({x:.0f}, {y:+.0f})" for x, y in mounts.stations())
    made.append(sheet(
        "DWG-27-010_base_rail", mounts.base_rails()[0], Plane.XY,
        "BASE RAIL, 6061-T6, 2 OFF (L/R mirror), bonded to the shell foot", [
            ("section y / height", f'{G.BR["y_in"]:.0f} .. {G.BR["y_out"]:.0f} x {G.BR["h"]:.0f}'),
            ("length (x)", f"{mounts.RAIL_X[0]:.0f} .. {mounts.RAIL_X[1]:.0f}"),
            ("PLF notches (2 per rail)", f'{mounts.NOTCH_X:.0f} wide (x), open to the inboard edge, to the strip face '
                                          f'u = +{mounts.NOTCH_WALL_U:.0f} from the port centre, at {stn}'),
            ("  notch position tol", "+/-0.2 to datum A (rail inner face) / B (front end); width 78 +0.2/0"),
            ("strip (outboard of the notch)", f'{st["rail_strip_t_min"]:.0f} mm thick min (front stations)'),
            ("rail-screw taps (2 per notch)", f'M6x1-6H, tap drill 5.0, {MT["rail_tap_depth"]:.1f} deep, x +/-{MT["rail_screw_x"]:.0f}, '
                                              f'z {MT["rail_screw_z"]:.0f} above the rail underside datum - match-drilled from the PLF body at shop fit-up'),
            ("underside (bond face)", "flatness 0.3 over 1,346; masked from anodise, Ra 3.2"),
            ("control wells (clear)", f'{mounts.WELL["lx"]:.0f} x {mounts.WELL["ly"]:.0f} at '
                                      + ", ".join(f"{n} x={x:.0f}" for n, x, _ in mounts.WELLS)),
            ("general tol", "ISO 2768-mK; break edges 0.3")],
        ["Material 6061-T6 (AMS-QQ-A-200/8 bar 80 x 30), CNC; black anodise MIL-A-8625 Type II "
         "Class 2 except the bond face. Notch and well x-positions PROVISIONAL until taped "
         "(T1-T3, P-CAL-02) and until the port is measured (P-CAL-01b)."],
        scale=0.3))

    x0, y0 = mounts.stations()[0]
    made.append(sheet(
        "DWG-27-012_plf_body", mounts.body_local(), Plane.YZ,
        "PORT LATCH FOOT BODY, 6061-T6, 4 OFF (one part; the passenger side is the same part rotated 180 deg)", [
            ("stem (through the foot pocket, into the port)", f'{MT["stem_x"]:.0f} x {MT["stem_u1"] - MT["stem_u0"]:.0f}, '
                                                               f'z {MT["stem_bottom"]:.0f} .. {MT["head_z0"] + 2:.1f} (PROVISIONAL)'),
            ("seat flange (the pad STOP)", f'{MT["flange_x"]:.0f} x {MT["flange_u1"] - MT["flange_u0"]:.0f} x {MT["flange_t"]:.1f}; '
                                           f'top z {MT["flange_t"]:.2f} +0/-0.05, underside z 0 (bears on the rail cap)'),
            ("head (in the rail notch)", f'{MT["head_x"]:.0f} x {MT["head_u1"] - MT["head_u0"]:.0f}, z {MT["head_z0"]:.1f} .. {MT["head_top"]:.1f}'),
            ("hook slider cross-slot", f'{MT["slot_x"]:.0f} wide, z {MT["slot_z0"]:.1f} .. {MT["slot_z1"]:.1f}; floor/roof parallel 0.03'),
            ("pin channels (2)", f'{MT["chan_w"]:.0f} wide at x +/-{MT["pin_pitch"] / 2:.1f}, u {MT["chan_u0"]:.0f} .. {MT["chan_u1"]:.0f}, '
                                  f'open at the stem bottom (the stem drops past the pins)'),
            ("hinge ears (2) + pin bore", f'x {MT["ear_x0"]:.1f} .. {MT["ear_x1"]:.0f}, bore 5.0 H7 coaxial 0.03 at '
                                          f'u {MT["hinge_u"]:.1f}, z {MT["hinge_z"]:.1f}'),
            ("lock bore", f'{MT["lock_bore"]:.1f} H11 x {MT["lock_len"]:.1f} deep from the inboard face, axis // u, z {MT["lock_z"]:.0f}; '
                          f'cam pocket {MT["lock_cam_pocket_d"]:.0f}'),
            ("rail-screw holes (2)", f'obround 6.6 x {6.6 + 2 * MT["rail_slot_z"]:.1f} (z +/-{MT["rail_slot_z"]:.0f}), cbore '
                                      f'{MT["rail_cbore_d"]:.0f} x {MT["rail_cbore_depth"]:.0f}, x +/-{MT["rail_screw_x"]:.0f}, z {MT["rail_screw_z"]:.0f}'),
            ("tuning-screw tap", f'M6, tap drill 5.0, x {MT["tune_x"]:.0f}, z {MT["tune_z"]:.0f}, 14 deep'),
            ("detent bore", f'M8x1.25 (tap 6.8) in the +x ear, {MT["detent_len"]:.0f} deep, {MT["detent_r"]:.1f} above the hinge axis'),
            ("finish", "hard anodise Type III clear; seat flange, slot floor, ear faces ground / masked"),
            ("general tol", "ISO 2768-mK; break edges 0.3")],
        ["EVERY dimension that touches the port (stem, channels, pin height, slot) is PROVISIONAL: Rivian publishes "
         "neither the port nor the crossbar foot. Calibration P-CAL-01b before release.",
         "Rivian forbids modifying the ports: nothing here cuts or drills the truck.",
         "Stem depth leaves 2 mm above the (provisional) recess floor; the SEAT FLANGE, not the stem, sets height."],
        scale=1.2))

    from build123d import Compound
    shim = mounts.shims_local()[0]
    pk = Compound(children=[mounts.paddle_closed_local(), mounts.slider_closed_local(), shim])
    made.append(sheet(
        "DWG-27-013_plf_paddle_slider_shim", pk, Plane.YZ,
        "PLF PADDLE 6061 (4 OFF) + HOOK SLIDER 17-4PH (4 OFF) + SHIM 316 1.0 (8 OFF + fit-up kit)", [
            ("paddle plate", f'{MT["paddle_x"]:.0f} x {MT["paddle_t"]:.0f} x {MT["paddle_h"]:.0f}; knuckle dia {MT["knuckle_d"]:.0f} x {MT["paddle_x"]:.0f}, bore 5.2 H8'),
            ("paddle detent dimples", f'2 x sphere R2.3 +/-0.05 at {MT["detent_r"]:.1f} from the axis, at {mounts.DIMPLE_DEG[0]:.0f} / '
                                       f'{mounts.DIMPLE_DEG[1]:.0f} deg (closed / stage 1, {mounts.STAGE1_DEG:.0f} deg apart)'),
            ("paddle states", f'closed 0, stage 1 {mounts.STAGE1_DEG:.0f}, open {mounts.OPEN_DEG:.0f} deg (inboard)'),
            ("hook slider", f'bar {MT["bar_x"]:.0f} x {MT["bar_u1"] - MT["bar_u0"]:.0f} x {MT["bar_z1"] - MT["bar_z0"]:.1f}; 2 teeth '
                            f'{MT["tooth_w"]:.0f} wide at x +/-{MT["pin_pitch"] / 2:.1f}, z {MT["tooth_z0"]:.0f} .. {MT["tooth_z1"]:.0f}, '
                            f'tip +{MT["tooth_tip"]:.0f} past the datum (clamped pose)'),
            ("  tooth top faces", "ground flat 0.02; pin-bottom datum z -18.00 +/-0.05 from the cap"),
            ("  travel", f'{MT["slider_travel"]:.1f} along u: dwell closed -> stage 1 (0.45), retract by stage 1 -> open'),
            ("shim", "316, 1.0 +/-0.02, 42 x 14, two obround 6.6 x 12.6; kit 0.5 / 1.0 for a 0 - 4 mm pack"),
            ("finish", "paddle black anodise Type II; slider + shim passivate ASTM A967")],
        ["Slider 17-4 PH H1025, wire-EDM + ground, sliding fit 0.2 in the slot (DWG-27-012).",
         "Drive link paddle cam -> slider and the lock-cam keeper are NOT drawn (OPEN plf_drive_link_and_lock_interlock).",
         "Paddle hinge pin: ISO 2338 d5 m6 x 80, cut/ground to 76, press fit in one ear. Detent: M8 ball plunger "
         "(McMaster 85015A51, same as the module plunger)."],
        scale=1.4))

    made.append(sheet(
        "DWG-27-011_hatch_leaf", HA.leaf_shell(), Plane.XY,
        "HATCH LEAF, CARBON 26 mm, INSIDE-GLAZED, 1 OFF", [
            ("leaf outline", f"{2 * (HA.AX + G.H_LEAF_OUT):.0f} x {2 * (HA.AY + G.H_LEAF_OUT):.0f}"),
            ("windows (visible)", f'{HA.WIN["x1"] - HA.WIN["x0"]:.0f} x {2 * HA.WIN["y"]:.0f}, R{HA.WIN["r"]:.0f}'),
            ("outer lip / pane overlap", f'{HA.WIN["lip"]:.0f} / {HA.WIN["overlap"]:.0f}'),
            ("mullion (solid carbon)", f"{HA.MULLION:.0f}")],
        ["Pane sits behind a 3 mm carbon lip (cannot leave outward) and is clamped by a screwed "
         "6061 retainer (cannot fall inward)."],
        scale=0.3))

    # ---- rev 10: a controlled sheet for EVERY remaining fabricated family (BOM27 cites these)
    from build123d import Cylinder, Align
    gen = "ISO 2768-mK unless stated; break edges 0.3"
    an = "black anodise MIL-A-8625 Type II Class 2"

    def _at_origin(p):
        c = p.bounding_box().center()
        return Pos(-c.X, -c.Y, -c.Z) * p

    def _bb(p):
        b = p.bounding_box().size
        return f"{b.X:.1f} x {b.Y:.1f} x {b.Z:.1f}"

    pane = HA.glazing_pane(1)
    ret = HA.glazing_retainer(1)
    made.append(sheet(
        "DWG-27-014_hatch_glazing_pane_retainer", _at_origin(ret), Plane.XY,
        "HATCH GLAZING PANE (PC) + RETAINER (6061), 2 + 2 OFF (L/R mirror)", [
            ("pane envelope", _bb(pane)), ("pane", "5 mm hard-coat PC (Makrolon AR / Lexan Margard MR10)"),
            ("pane profile tol", "+/-0.5; edges routed + flame-free polish"),
            ("retainer envelope", _bb(ret)), ("retainer", f"6061-T6 5 mm plate, CNC; {an}"),
            ("retainer screws", "M4 at <= 90 mm pitch into potted inserts (DWG-27-018)"),
            ("general", gen)],
        ["Pane is inside-glazed behind the 3 mm carbon lip; 1 mm EPDM glazing gasket each face; "
         "1.2 Nm on the retainer screws (clamp, do not crush)."], scale=0.6))
    cage = SS.payload("CAGE")
    bar = [c for c in cage if "BAR" in c.label][0]
    rail = [c for c in cage if "RAIL" in c.label][0]
    made.append(sheet(
        "DWG-27-015_cage_bar_rail", _at_origin(rail), Plane.XY,
        f"CAGE MODULE: BAR 316 Dia 10 x {len([c for c in cage if 'BAR' in c.label])} + RAIL 316 8 x 4, 2 OFF",
        [("bar envelope", _bb(bar)), ("rail envelope", _bb(rail)),
         ("bar pitch", "equal, ends on the straight run of the R34 plug-tube corners"),
         ("weld", "TIG, ER316L, bars to rails, fixture-welded; flatness of the welded cage 1.0"),
         ("rail fixing", "2 x M6x16 A4 per rail end-tab into the plug frame (J13)"),
         ("finish", "electropolish ASTM B912"), ("general", gen)],
        ["Dog-safe: no exposed weld spatter; all bar ends radiused R2."], scale=0.6))
    tb = SS.payload("TOOLBOX")
    door = [c for c in tb if "DOOR" in c.label][0]
    tub = [c for c in tb if "TUB" in c.label][0]
    made.append(sheet(
        "DWG-27-016_toolbox_door_tub", _at_origin(tub), Plane.XY,
        "TOOLBOX MODULE: DOOR (carbon 6 mm) + TUB (3 mm ABS/PMMA), 1 + 1 OFF", [
            ("door envelope", _bb(door)), ("door", "carbon/PET 6 mm sandwich, vacuum infusion, UV clear"),
            ("tub envelope", _bb(tub)), ("tub", "3 mm ABS/PMMA (Kydex-class) thermoform, grained black"),
            ("tub fixing", "10 x M5x10 BHCS A4 through the flange into the plug frame (J14)"),
            ("profile tol", "door +/-0.3 to the module flange; tub +/-1.0"), ("general", gen)],
        ["Door hinge/lock (E3-108-015 keyed, key-alike) is NOT modelled: Step 27 open item."], scale=0.6))
    wp = SS.payload("WINDOW")[0]
    made.append(sheet(
        "DWG-27-017_window_module_pane", _at_origin(wp), Plane.XY,
        "WINDOW MODULE PANE, 5 mm HARD-COAT PC, FLAT, 2 OFF", [
            ("envelope", _bb(wp)), ("flatness", "1.0 (flat by Nate's direction, decision 1320686)"),
            ("bond", "3M VHB 5952 12 mm perimeter to the plug-frame flange (J15)"),
            ("profile tol", "+/-0.5"), ("general", gen)],
        ["Edges routed and polished; hard coat both faces."], scale=0.6))
    hp = SH.roof_hardpoints()[0]
    ins = Cylinder(5.0, 12.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    ins += Cylinder(7.0, 1.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    ins -= Pos(0, 0, -1) * Cylinder(1.7, 14.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    made.append(sheet(
        "DWG-27-018_roof_hardpoint_potted_insert", _at_origin(hp), Plane.XZ,
        "ROOF HARDPOINT 6061 M8 (4 OFF) + POTTED INSERT 6061 M4 (26 OFF)", [
            ("hardpoint", f'Dia {SH.HARDPOINT["dia"]:.0f} x {SH.HARDPOINT["depth"]:.0f}, M8x1.25-6H 14 deep, top flush 0/-0.3'),
            ("potted insert", "Dia 10 x 12, flange Dia 14 x 1, M4x0.7-6H thru, knurled OD (straight 0.8 pitch)"),
            ("insert installation", "core-out Dia 12, pot in 3M DP460, flange flush with the inner skin"),
            ("finish", "clear anodise Type II; bond faces masked"), ("general", gen)],
        ["Hardpoint load is limited to the 24 kg dynamic roof allowance (check_mounting) until FEA."],
        scale=2.0))
    made.append(sheet(
        "DWG-27-019_leaf_arm_strut_boss", _at_origin(HA.leaf_striker_arm(HA.LATCH_XS[1])), Plane.XY,
        "HATCH LEAF STRIKER ARM (2 OFF) + STRUT BOSS (2 OFF), 6061-T6", [
            ("striker arm", f"envelope {_bb(HA.leaf_striker_arm(HA.LATCH_XS[1]))}, M10x1.5-6H 20 deep"),
            ("strut boss", "22 x 22, M8x1.25-6H 14 deep (Stabilus 4486MD)"),
            ("bond", "both bonded to the leaf inner skin, DP460, 0.25 bondline"),
            ("position", "+/-0.5 to the hinge axis datum (drives strut geometry)"),
            ("finish", an), ("general", gen)],
        ["Striker bolt R4-90-321-20 is adjusted +/-3 mm in its slotted bracket (DWG-27-004) before torque."],
        scale=2.0))
    fp = SH.front_pane()
    made.append(sheet(
        "DWG-27-020_front_pass_through_pane", _at_origin(fp), Plane.YZ,
        "FRONT PASS-THROUGH PANE, 5 mm HARD-COAT PC, 1 OFF", [
            ("envelope", _bb(fp)), ("bond", "DP460 is NOT used on PC: 3M VHB 5952 20 mm overlap all round"),
            ("profile tol", "+/-0.5"), ("general", gen)],
        ["Faces the R1T cab back glass; drain path below."], scale=0.5))

    for m in made:
        print(f"  {m.relative_to(DWG.parent)}")
    print(f"{len(made)} drawing sheets")


if __name__ == "__main__":
    main()
