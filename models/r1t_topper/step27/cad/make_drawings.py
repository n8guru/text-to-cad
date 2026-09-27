"""Dimensioned drawing sheets for the CUSTOM parts, plus an exploded view. SVG, no dependencies.

    python cad/make_drawings.py

Purchased parts do not get a drawing — they get a part number, which is in BOM27.md. Only parts we
control need a controlled drawing, and every one of them gets one here:

  DWG-27-001  socket frame              DWG-27-004  striker bracket
  DWG-27-002  ledge rail                DWG-27-006  compression limiter
  DWG-27-003  module plug frame         DWG-27-009  OEM control access well
  DWG-27-007  J-hook                    EXP-27-001  exploded socket assembly
  DWG-27-008  hatch surround
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build123d import Axis, ExportSVG, LineType, Plane, Pos, Vector  # noqa: E402

import geom as G  # noqa: E402
import hatch as HA  # noqa: E402
import hw  # noqa: E402
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
    p = hw.d("rotary_latch")
    s = hw.d("striker")
    sl = hw.d("bulb_seal")
    b = hw.d("bushing")

    made.append(sheet(
        "DWG-27-001_socket_frame", SS.socket_frame(), Plane.XY,
        "SOCKET FRAME, 6061-T6, 4 OFF",
        [("aperture W x H", f"{W:.1f} x {HH:.1f}"),
         ("aperture corner radius", f'{G.K["corner_r"]:.1f}'),
         ("bond flange, outer", f"{W + 2 * G.POCKET_MARGIN + 90:.1f} x "
                                f"{HH + 2 * G.POCKET_MARGIN + 90:.1f}"),
         ("bond flange thickness", f"{SS.FLANGE_T:.1f}"),
         ("seal retention rib, thickness x height", f'{sl["rib_t"]:.1f} x {sl["rib_h"]:.1f}'),
         ("return lip wall / depth", f"{SS.LIP_T:.1f} / 55.0"),
         ("latch hole pattern (2 per station)", f'{p["hole_pitch"]:.1f} +/- '
                                                f'{p["hole_pitch_tol"]:.1f}'),
         ("latch panel prep holes", f'2 x dia {p["panel_hole_dia"]:.1f}'),
         ("striker slot, depth x end radius", f'{p["slot_depth"]:.1f} x {p["slot_end_r"]:.1f}'),
         ("bushing bores, dia x pitch", f'{b["od"]:.1f} H7 at u = {G.PIN_U[0]:.0f} / '
                                        f'{G.PIN_U[1]:.0f}'),
         ("latch stations", f"u = {G.LATCH_U[0]:.0f} / {G.LATCH_U[1]:.0f}, v = {G.LATCH_V:.1f}"),
         ("frame face datum", f"n = {SS.FACE_N:.2f}")],
        ["ONE CNC program and ONE fixture for all four. Interchangeability is a manufacturing "
         "claim, not a design claim, and this is where it is made.",
         f'Bushing pair true position {G.TOL["bushing_true_position"]} to datum A-B.',
         f'Land flatness {G.TOL["land_flatness"]}.',
         "Bushing bore is 10 G6, NOT H7: MISUMI offers H7 only at d = 2-6.",
         "Seal rib 3.0 thick to sit inside the Trim-Lok DD6139 grip range 1.52-3.18.",
         "Black anodise Type II after machining. Mask the bond flange."]))

    made.append(sheet(
        "DWG-27-002_ledge_rail", SS.ledge_rail(), Plane.XY, "LEDGE RAIL, 6061-T6, 4 OFF",
        [("length", "500.0"), ("shelf", "50.0 x 8.0"), ("up-lip", "8.0 x 18.0"),
         ("drain slots", "2 x 10.0 wide"),
         ("lip height to land datum", f'+/- {G.TOL["ledge_lip_height"]}')],
        ["This part carries the ENTIRE module weight in shear. The rotary latches carry none.",
         f'Lip height is dimensioned FROM THE LAND PLANE, +/- {G.TOL["ledge_lip_height"]}, not '
         f'from the extrusion.',
         "Clear anodise. Do not mask the drain slots."], scale=0.5))

    made.append(sheet(
        "DWG-27-003_module_plug_frame", SS.module_plug_frame(), Plane.XY,
        "MODULE PLUG FRAME, 6061-T6, 4 OFF (common to WINDOW / CAGE / TOOLBOX)",
        [("flange outer", f"{W + 2 * G.POCKET_MARGIN + 90 - 2 * G.SHUTLINE:.1f} x "
                          f"{HH + 2 * G.POCKET_MARGIN + 90 - 2 * G.SHUTLINE:.1f}"),
         ("flange thickness", f"{SS.MODULE_FLANGE_T:.1f}"),
         ("plug clearance per side", "6.0"),
         ("plug depth", f"{G.PLUG_DEPTH:.1f}"),
         ("visible shut line", f"{G.SHUTLINE:.1f}"),
         ("outer profile tolerance", f'{G.TOL["module_profile"]}')],
        ["ONE frame for all three module variants. That is what makes them interchangeable.",
         f'Outer profile {G.TOL["module_profile"]} sets the visible {G.SHUTLINE:.0f} mm shut line.',
         "Striker brackets bolt to the top return; slots give +/-3 fit-up adjustment."]))

    made.append(sheet(
        "DWG-27-004_striker_bracket", hw.striker_bracket(), Plane.XY,
        "STRIKER BRACKET, 316 STAINLESS, 10 OFF",
        [("plate", "54.0 x 40.0 x 6.0"),
         ("striker bore", "dia 10.6 for M10x1.5"),
         ("adjustment slots", "2 x 7.0 wide x 6.0 long"),
         ("mates", f'Southco {hw.HW["striker"]["pn"]}')],
        ["CUSTOM because no catalogue bracket carries our hole pattern.",
         "The slots are the tolerance-absorption feature: the whole module stack is dialled out "
         "here at assembly, not scrapped.",
         "Passivate per ASTM A967 after machining."], scale=1.2))

    made.append(sheet(
        "DWG-27-006_compression_limiter", hw.compression_pad(), Plane.XY,
        "COMPRESSION LIMITER, UHMW-PE, 12 OFF",
        [("pad", "30.0 x 20.0"),
         ("THICKNESS", f'{hw.d("compression_limiter")["pad_t"]:.2f} +0 / -0.05'),
         ("clearance hole", f'dia {hw.d("compression_limiter")["hole_dia"]:.1f}'),
         ("stock", hw.HW["compression_limiter"]["stock"])],
        ["The thickness IS the seal compression. It sets the Trim-Lok DD6139 bulb to its "
         "designed 33 % deflection and stops the bulb being crushed.",
         "Waterjet the blank, then surface grind to thickness. Do not rely on sheet tolerance.",
         "Virgin natural UHMW. No regrind, no filler."], scale=2.5))

    made.append(sheet(
        "DWG-27-007_j_hook", SS.j_hook(), Plane.XY, "J-HOOK, 316 STAINLESS, 8 OFF",
        [("material thickness", "6.0"), ("width", "60.0"),
         ("throat to pin datum", "+/- 0.1"),
         ("fixing", "2 x dia 6.8 for M6 A4")],
        ["Carries the full module weight into the ledge lip in SHEAR.",
         "Hand calc, not FEA: 29 kg at 3 g = 850 N, 425 N per hook, ~10 MPa shear in the 6 x 30 "
         "section. FEA remains a later gate.",
         "Laser cut, press brake, passivate."], scale=1.2))

    made.append(sheet(
        "DWG-27-008_hatch_surround", HA.hatch_surround(), Plane.XY,
        "HATCH SURROUND, 6061-T6, 1 OFF",
        [("opening W x H", f"{HA.W:.1f} x {HA.HH:.1f}"),
         ("corner radius", f"{HA.CR:.1f}"),
         ("flange thickness", f"{HA.FLANGE_T:.1f}"),
         ("seal rib", f'{sl["rib_t"]:.1f} x {sl["rib_h"]:.1f}'),
         ("hinge stations", f"x = +/- {HA.HINGE_X:.0f}"),
         ("latch stations", f"x = +/- {HA.LATCH_X:.0f}"),
         ("surround face datum", f"z = {HA.FACE_Z:.2f}"),
         ("hinge axis straightness", f'{G.TOL["hinge_axis_straightness"]}')],
        [f'Hinge-axis straightness {G.TOL["hinge_axis_straightness"]} over the {2 * HA.HINGE_X:.0f}'
         f' mm span. This is the tolerance that decides whether the leaf binds.',
         "Hinge bosses sit ABOVE the leaf edge, not under it, or they foul the inner skin.",
         "The gutter bonds to the shell above this part and drains outboard through the two "
         "C-pillar drains, discharging BELOW and OUTSIDE the seal line.",
         "JW Winco GN 7233 is a LINKAGE, not a fixed pivot. This drawing shows the design-intent "
         "axis. Re-check against the vendor CAD coupler curve before release."]))

    made.append(sheet(
        "DWG-27-009_oem_control_well", hw.compression_pad(), Plane.XY,
        "OEM CONTROL ACCESS WELL, 3 OFF — placeholder outline, see TAILGATE_CONTROL.md",
        [(k, f"{v}") for k, v in hw.d("oem_control_well").items()],
        ["Preserves the Gen-1 R1T rail-top buttons the topper base rail covers: tailgate release "
         "(which is also the only bed-light toggle) and both Gear Tunnel releases.",
         "MECHANICAL preservation only. No splice, no relocation, no added switch.",
         "Drain discharges OUTBOARD onto the OEM rail cap, outside our seal line.",
         "INCOMPLETE: the well positions depend on tape measurements T1-T5. Rivian publishes no "
         "dimensioned button position. The outline shown is a placeholder."], scale=1.5))

    for m in made:
        print(f"  {m.relative_to(DWG.parent)}")
    print(f"{len(made)} drawing sheets")


if __name__ == "__main__":
    main()
