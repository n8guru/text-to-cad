"""Dimensioned drawing sheets for the CUSTOM parts, plus an exploded view. SVG, no dependencies.

    python cad/make_drawings.py

Purchased parts do not get a drawing — they get a part number, which is in BOM27.md. Only parts we
control need a controlled drawing, and every one of them gets one here:

  DWG-27-000  carbon shell (styled)     DWG-27-006  compression limiter
  DWG-27-001  socket frame (top-hat)    DWG-27-007  J-hook
  DWG-27-003  module plug frame         DWG-27-008  hatch surround (top-hat)
  DWG-27-004  striker bracket           DWG-27-010  base rail + OEM control-well cut-outs
  DWG-27-011  hatch leaf (inside-glazed)
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

    made.append(sheet(
        "DWG-27-010_base_rail", mounts.base_rails()[0], Plane.XY,
        "BASE RAIL, 6061-T6, 2 OFF, with OEM control-well cut-outs", [
            ("section y", f'{G.BR["y_in"]:.0f} .. {G.BR["y_out"]:.0f} x {G.BR["h"]:.0f}'),
            ("port adapter bores", f'{mounts.ADAPTER["shank_d"] + 1:.0f} at the 4 Rivian bed ports'),
            ("control wells (clear)", f'{mounts.WELL["lx"]:.0f} x {mounts.WELL["ly"]:.0f} at '
                                      + ", ".join(f"{n} x={x:.0f}" for n, x, _ in mounts.WELLS))],
        ["Well x-positions PROVISIONAL until taped (TAILGATE_CONTROL.md T1-T3); lids not drawn."],
        scale=0.3))

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

    for m in made:
        print(f"  {m.relative_to(DWG.parent)}")
    print(f"{len(made)} drawing sheets")


if __name__ == "__main__":
    main()
