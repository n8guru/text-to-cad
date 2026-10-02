"""Step 27 export: authoritative STEP assembly, per-part STL for the render lane, SVG sections.

    python cad/assembly_step27.py

Outputs under ``step27/out`` and ``step27/drawings``:
  out/R1T_TOPPER_STEP27.step        whole Step 27 subsystem, closed
  out/R1T_TOPPER_STEP27_open.step   hatch at 95 deg, one module off the socket
  out/parts/*.stl                   one file per part, for Blender to IMPORT rather than re-model
  out/parts_manifest.json           part -> file, PN, material, process, finish, mass
  drawings/SEC-*.svg                section and interface views
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build123d import (  # noqa: E402
    Axis, CenterOf, Compound, ExportSVG, LineType, Location, Plane, Pos, Rot, Vector,
    export_step, export_stl, section,
)

import geom as G  # noqa: E402
import hatch as HA  # noqa: E402
import hw  # noqa: E402
import mounts  # noqa: E402
import shell as SH  # noqa: E402
import side_socket as SS  # noqa: E402
import truck as TR  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out"
PARTS = OUT / "parts"
DWG = ROOT / "drawings"

# material / process / finish per part family — this is what makes the BOM orderable rather than
# a picture. Density in kg/mm^3 for the mass rollup.
MATERIAL = {
    "SHELL_CARBON": ("carbon/PET-foam sandwich, 22 mm: 2x 200 gsm 2x2 twill + 300 gsm biax each skin",
                     "vacuum infusion, female tool, post-cure", "UV-stable clear coat", None),
    "SOCKET_FRAME": ("6061-T6", "3+2-axis CNC, one program + one fixture for all four",
                     "black anodise Type II", 2.70e-6),
    "BASE_RAIL": ("6061-T6", "CNC from 80x30 bar", "black anodise Type II", 2.70e-6),
    "PORT_SPACER": ("6061-T6", "CNC turn from Dia 38 bar, faces ground parallel 0.02",
                    "clear anodise Type II", 2.70e-6),
    "PORT_SHIM": ("316 stainless shim stock 0.5 mm", "laser cut, deburr", "passivate", 8.00e-6),
    "PORT_SLOT_WASHER": ("316 stainless 4 mm plate", "laser cut + surface grind", "passivate",
                         8.00e-6),
    "PORT_ADAPTER_WEISTEC": ("billet 6061, clear anodise (vendor)", "purchased", "as supplied",
                             2.70e-6),
    "PORT_STUD": ("A4-70 stainless (ISO 3506-1)", "purchased", "plain", 8.00e-6),
    "PORT_NUT": ("A4-80 stainless (ISO 3506-2)", "purchased", "plain", 8.00e-6),
    "WEDGE_WASHER": ("stainless 1.4404 / 316L (Nord-Lock ss)", "purchased", "as supplied",
                     8.00e-6),
    "FOOT_PAD_EPDM": ("closed-cell EPDM sponge, ASTM D1056 2B2, PSA one side",
                      "purchased strip, knife-cut to the drawing", "black", 0.15e-6),
    "ROOF_HARDPOINT": ("6061-T6 bonded insert, M8", "CNC turn", "clear anodise", 2.70e-6),
    "FRONT_PASS_THROUGH_PANE": ("5 mm hard-coat polycarbonate", "CNC rout + polish",
                                "hard coat both faces", 1.20e-6),
    "WINDOW_PANE": ("5 mm hard-coat polycarbonate", "CNC rout + polish", "hard coat both faces",
                    1.20e-6),
    "CAGE_BAR": ("316 stainless, Dia 10", "cut + TIG to rails", "electropolish", 8.00e-6),
    "CAGE_RAIL": ("316 stainless 8 x 4 bar", "laser + TIG", "electropolish", 8.00e-6),
    "TOOLBOX_DOOR": ("carbon/PET sandwich 6 mm", "vacuum infusion", "UV clear", 0.60e-6),
    "TOOLBOX_TUB": ("3 mm ABS/PMMA", "thermoform", "grained black", 1.10e-6),
    "LEAF_STRIKER_ARM": ("6061-T6", "CNC", "black anodise Type II", 2.70e-6),
    "LEAF_STRUT_BOSS": ("6061-T6 bonded boss, M8", "CNC", "black anodise Type II", 2.70e-6),
    "HATCH_DRAIN_TUBE": ("PA12 tube 8 x 5, representation solid", "cut to length", "black", 1.01e-6),
    "MODULE_PLUG_FRAME": ("6061-T6", "CNC", "black anodise Type II", 2.70e-6),
    "J_HOOK": ("316 stainless", "laser + press brake", "passivate", 8.00e-6),
    "HATCH_SURROUND": ("6061-T6", "CNC from 12 mm plate", "black anodise Type II", 2.70e-6),
    "HATCH_LEAF_CARBON": ("carbon/PET sandwich, 200 gsm 2x2 twill + 300 gsm biax over 20 mm core",
                          "vacuum infusion, female mould", "UV clear", 0.223e-6),
    "GLAZING_PANE": ("5 mm hard-coat polycarbonate (Makrolon AR / Lexan Margard)",
                     "CNC rout + polish", "hard coat both faces", 1.20e-6),
    "GLAZING_RETAINER": ("6061-T6", "CNC", "black anodise Type II", 2.70e-6),
    "STRIKER_BRACKET": ("316 stainless", "laser + machine, slotted +/-3 mm", "passivate", 8.00e-6),
    "COMPRESSION_LIMITER": ("UHMW-PE virgin", "waterjet + surface grind to 7.40 +0/-0.05",
                            "as machined", 0.94e-6),
    "BULB_SEAL": ("EPDM sponge bulb on dense EPDM 70 Shore A base, aluminium wire carrier",
                  "purchased extrusion, cut and bonded at the joint", "black", 0.70e-6),
}
PURCHASED_PREFIX = {      # label substring -> hardware.json item (or (item, pn field))
    "ROTARY_LATCH": "rotary_latch", "LATCH_HOUSING_R4": "rotary_latch", "FORK_BOLT": "rotary_latch",
    "LATCH_PAWL": "rotary_latch", "STRIKER_BOLT": "striker", "RELEASE_CABLE": "release_cable",
    "RELEASE_HANDLE": "release_handle", "HANDLE_HANDLE_": "release_handle",
    "CABLE_SPLITTER": ("release_handle", "splitter_pn"),
    "LOCATING_PIN_ROUND": "locating_pin_round", "LOCATING_PIN_DIAMOND": "locating_pin_diamond",
    "BUSHING": "bushing", "BALL_PLUNGER": "ball_plunger", "GAS_STRUT": "gas_strut",
    "BALL_STUD": ("gas_strut", "ball_stud"), "CONCEALED_HINGE": "hinge", "HINGE_GN7233": "hinge",
    "T_HANDLE": "t_handle", "CHMSL": "chmsl", "COMPRESSION_LIMITER": "compression_limiter",
    "BULB_SEAL": "bulb_seal",
    "PORT_ADAPTER_WEISTEC": "port_adapter", "PORT_STUD": ("fasteners", "STUD_M10x60_A4"),
    "PORT_NUT": ("fasteners", "NUT_M10_A4"),
    "WEDGE_WASHER": ("fasteners", "NL10SS"), "FOOT_PAD_EPDM": "foot_pad",
}


def _mass(label: str, volume: float, dens) -> float:
    if dens is None:                                  # sandwich: areal density, not volume
        return volume / G.WALL * 5.8e-6
    return volume * dens


def _classify(label: str):
    """Match ANYWHERE in the label: parts carry a position prefix (L0_, HATCH_) in the assembly.

    Matching on startswith silently fell through to the steel-density fallback and inflated the
    mass rollup by ~3x. Longest key first, so LOCATING_PIN_DIAMOND never matches LOCATING_PIN.
    """
    up = (label or "").upper()
    for k in sorted(MATERIAL, key=len, reverse=True):
        if k in up:
            return MATERIAL[k]
    return ("PURCHASED - see hardware.json for PN and material", "purchased",
            "as supplied", 7.85e-6)


def _pn_for(label: str):
    up = (label or "").upper()
    for k in sorted(PURCHASED_PREFIX, key=len, reverse=True):
        item, field = (PURCHASED_PREFIX[k], "pn") if isinstance(PURCHASED_PREFIX[k], str) \
            else PURCHASED_PREFIX[k]
        if k in up:
            if item == "fasteners":
                f = hw.HW["fasteners"][field]
                return (f.get("manufacturer"), f.get("pn"), f.get("status"), f.get("source_url"))
            h = hw.HW[item]
            pn = h.get(field)
            pn = pn.get("pn") if isinstance(pn, dict) else pn
            return (h.get("manufacturer"), pn, h.get("status"), h.get("source_url"))
    return (None, None, "CUSTOM", None)


# --------------------------------------------------------------------------------------
DEFAULT_KIT = {"L0": "WINDOW", "L1": "CAGE", "R0": "WINDOW", "R1": "TOOLBOX"}


def step27_assembly(hatch_deg: float = 0.0, module_gap: float = 0.0, state: str = "closed",
                    kit: dict | None = None, with_shell: bool = True):
    """Everything Step 27 owns, in the vehicle frame: shell, mounts, 4 sockets + modules, hatch."""
    kit = DEFAULT_KIT if kit is None else kit
    kids = []
    if with_shell:
        # a COPY: SH.shell() is cached and an assembly node can have one parent, so appending the
        # cached object to a second assembly silently removes it from the first one
        sh = copy.copy(SH.shell())
        sh.label = "SHELL_CARBON_SANDWICH"
        kids.append(sh)
    kids += SH.roof_hardpoints() + [SH.front_pane()]
    kids += mounts.base_rails() + mounts.foot_pads() + mounts.port_stations()
    for side in "LR":
        for i in range(2):
            tag = f"{side}{i}"
            pl = G.socket_plane(side, i)
            gap = module_gap if tag == "L1" else 0.0
            st = state if tag == "L1" else "closed"
            for c in SS.socket_assembly(st).children:
                c2 = pl * c
                c2.label = f"{tag}_{c.label}"
                kids.append(c2)
            for c in SS.module_interface(gap).children:
                c2 = pl * c
                c2.label = f"{tag}_MOD_{c.label}"
                kids.append(c2)
            for c in SS.payload(kit[tag]):
                c2 = pl * (Pos(0, 0, gap) * c)
                c2.label = f"{tag}_MOD_{c.label}"
                kids.append(c2)
    hp = G.hatch_plane()
    for c in HA.hatch_assembly(hatch_deg).children:
        c2 = hp * c
        c2.label = f"HATCH_{c.label}"
        kids.append(c2)
    a = Compound(children=kids)
    a.label = f"R1T_TOPPER_STEP27_hatch{hatch_deg:.0f}"
    return a


def payload_set(tag: str = "L1"):
    """All three payload variants placed at one socket, for the render lane's module swap."""
    side, i = tag[0], int(tag[1])
    pl = G.socket_plane(side, i)
    kids = []
    for kind in ("WINDOW", "CAGE", "TOOLBOX"):
        for c in SS.payload(kind):
            c2 = pl * c
            c2.label = f"{tag}_{kind}_{c.label}"
            kids.append(c2)
    a = Compound(children=kids)
    a.label = f"PAYLOADS_{tag}"
    return a


def truck_reference():
    kids = [TR.cab_keepout(), TR.body_keepout(), TR.tailgate_keepout()]
    for k, n in zip(kids, ("CAB_KEEPOUT", "BODY_BELOW_RAIL_KEEPOUT", "TAILGATE_KEEPOUT")):
        k.label = n
    c = Compound(children=kids)
    c.label = "00_REFERENCE_R1T_KEEPOUTS"
    return c


def _flatten(node, out=None, prefix="", loc=None):
    """Depth-first leaves, each tagged with its full ancestry path AND baked into world coordinates.

    Two bugs lived here, both of which showed up as wrong renders rather than as errors:

    1. Without the ancestry prefix, the eight rotary latches all flattened to a child labelled
       "latch_housing_R4-30" and the de-duplicating exporter wrote exactly one of them.
    2. ``export_stl`` does NOT compose nested Compound locations. A leaf two levels down exported
       at the ORIGIN, so the render lane imported a latch sitting at the vehicle datum instead of
       on its flange. Composing the location chain here and calling ``.located()`` bakes the world
       placement into every leaf before it is written.
    """
    out = [] if out is None else out
    loc = Location() if loc is None else loc
    here = loc * node.location
    label = node.label or "UNNAMED"
    full = f"{prefix}{label}" if not prefix else f"{prefix}__{label}"
    kids = getattr(node, "children", None)
    if kids:
        for c in kids:
            _flatten(c, out, full, here)
    else:
        out.append((full, node.located(here)))
    return out


SHORTEN = [
    (r"^R1T_TOPPER_STEP27_hatch\d+__", ""),
    (r"ROTARY_LATCH_R4-30-(closed|open|secondary)__", "LATCH_"),
    (r"HATCH_LEAF_ASSY-\d+deg__", "LEAF_"),
    (r"CONCEALED_HINGE_GN7233-NI-50-\d+deg__", "HINGE_"),
    (r"RELEASE_HANDLE_AC-75-101-11-(rest|pulled)__", "HANDLE_"),
    (r"MODULE_INTERFACE-gap\d+__", ""),
    (r"SOCKET-(closed|open)__", ""),
]


def short_name(n: str) -> str:
    """Blender truncates object names at 63 characters, and the full ancestry path is longer.

    Shorten deterministically HERE so the render lane's name-based material and visibility rules
    keep working, instead of post-processing the files by hand.
    """
    import re
    for pat, rep in SHORTEN:
        n = re.sub(pat, rep, n)
    return n[:52]


def export_parts(assembly=None, outdir=None, write_manifest=True):
    """One STL per distinct part, in VEHICLE coordinates and millimetres.

    The render lane IMPORTS these. That is the whole point: Blender never re-models a latch, so a
    still can never show geometry the CAD does not contain.
    """
    outdir = PARTS if outdir is None else outdir
    assembly = step27_assembly(0.0) if assembly is None else assembly
    PARTS_DIR = outdir
    PARTS_DIR.mkdir(parents=True, exist_ok=True)
    for old in PARTS_DIR.glob("*.stl"):          # a stale STL is an unrequested part in a render
        old.unlink()
    manifest, seen = [], {}
    for full, part in _flatten(assembly):
        base = short_name(full.replace(":", "-").replace("/", "-"))
        # Two latches in the same socket share a label, so the ancestry path alone is not unique.
        # Index the repeats instead of dropping them -- dropping is how 8 latches became 1.
        if base in seen:
            seen[base] += 1
            base = f"{base}_{seen[base]}"
        else:
            seen[base] = 1
        try:
            v = part.volume
        except Exception:
            continue
        if v < 1.0:
            continue
        fn = PARTS_DIR / f"{base}.stl"
        try:
            coarse = "SHELL" in base or "KEEPOUT" in base
            export_stl(part, str(fn), tolerance=0.4 if coarse else 0.08,
                       angular_tolerance=0.3 if coarse else 0.2)
        except Exception as exc:
            print(f"  stl skip {base}: {exc}")
            continue
        mat, proc, fin, dens = _classify(base)
        try:
            cg = part.center(CenterOf.MASS)
        except Exception:
            cg = part.bounding_box().center()
        mfr, p_n, status, url = _pn_for(base)
        manifest.append({
            "part": base, "stl": fn.name, "volume_mm3": round(v, 1),
            "mass_kg": round(_mass(base, v, dens), 3), "material": mat, "process": proc, "finish": fin,
            "manufacturer": mfr, "pn": p_n, "status": status, "source_url": url,
            "centroid_mm": [round(cg.X, 1), round(cg.Y, 1), round(cg.Z, 1)],
        })
    if write_manifest:
        (OUT / "parts_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def _svg(name, shapes, plane, title):
    DWG.mkdir(parents=True, exist_ok=True)
    ex = ExportSVG(scale=1.0, margin=12)
    ex.add_layer("section", line_weight=0.5, line_type=LineType.CONTINUOUS)
    for sh in shapes:
        try:
            cut = section(sh, section_by=plane, height=0.0)
        except Exception:
            continue
        if cut is None:
            continue
        try:
            ex.add_shape(plane.to_local_coords(cut), layer="section")
        except Exception:
            continue
    path = DWG / f"{name}.svg"
    ex.write(str(path))
    # stamp a title so a reviewer knows what plane they are looking at
    txt = path.read_text()
    txt = txt.replace("</svg>",
                      f'<text x="14" y="22" font-family="monospace" font-size="13">{title}'
                      f'</text></svg>')
    path.write_text(txt)
    return path


def _leaves(c):
    return [part for _, part in _flatten(c)]


def export_sections():
    made = []
    pl = G.socket_plane("L", 1)
    sock = [pl * k for k in _leaves(SS.socket_assembly("closed"))]
    sock += [pl * k for k in _leaves(SS.module_interface())]
    sock += [pl * k for k in SS.payload("CAGE")]
    shell = SH.shell()
    u_l = G.LATCH_U[1]
    cut = Plane(origin=(pl * Pos(u_l, 0, 0)).position, x_dir=pl.z_dir, z_dir=pl.x_dir)
    made.append(_svg("SEC-27-001_socket_through_latch", sock + [shell], cut,
                     f"SEC-27-001  socket L1, section through the u={u_l:+.0f} latch station"))
    cut2 = Plane(origin=pl.origin, x_dir=pl.z_dir, z_dir=pl.x_dir)
    made.append(_svg("SEC-27-002_socket_centreline", sock + [shell], cut2,
                     "SEC-27-002  socket L1 centreline: seal under the flange, fin + J-hook, pins"))
    hp = G.hatch_plane()
    shut = [hp * k for k in _leaves(HA.hatch_assembly(0.0))]
    cut3 = Plane(origin=hp.origin, x_dir=hp.z_dir, z_dir=hp.x_dir)
    made.append(_svg("SEC-27-003_hatch_shut_centreline", shut + [shell], cut3,
                     "SEC-27-003  rear hatch shut, centreline: seal under the leaf, inside-glazed pane"))
    cut4 = Plane(origin=(hp * Pos(HA.LATCH_XS[1], 0, 0)).position, x_dir=hp.z_dir, z_dir=hp.x_dir)
    made.append(_svg("SEC-27-004_hatch_latch_station", shut + [shell], cut4,
                     "SEC-27-004  rear hatch latch station: R4-30 + R4-90-321-20 on the leaf arm"))
    op = [hp * k for k in _leaves(HA.hatch_assembly(HA.OPEN_DEG))]
    cut5 = Plane(origin=(hp * Pos(HA.STRUT_LEAF[0], 0, 0)).position, x_dir=hp.z_dir, z_dir=hp.x_dir)
    made.append(_svg("SEC-27-005_hatch_open_strut", op + [shell], cut5,
                     f"SEC-27-005  rear hatch at {HA.OPEN_DEG:.0f} deg, strut plane: Stabilus "
                     f"{hw.HW['gas_strut']['pn']}"))
    xs = G.K["centers_x"][0]
    both = [G.socket_plane(sd, 0) * k for sd in "LR" for k in
            _leaves(SS.socket_assembly("closed")) + _leaves(SS.module_interface())]
    cut6 = Plane(origin=(xs, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
    made.append(_svg("SEC-27-006_shell_styled_section", [shell] + both, cut6,
                     f"SEC-27-006  styled shell section at x={xs:.0f}: {G.S['lean_deg']:.0f} deg "
                     f"land, R{G.S['shoulder_r']:.0f} shoulder, crown, sockets L0/R0"))
    cut7 = Plane(origin=(0, 0, 0), x_dir=(1, 0, 0), z_dir=(0, -1, 0))
    made.append(_svg("SEC-27-007_cab_to_topper_profile", [shell, TR.cab_keepout(), TR.tailgate_keepout()]
                     + shut, cut7,
                     "SEC-27-007  centreline side profile: R1T cab back + spoiler keep-out, front face, "
                     f"{G.S['rear_rake_deg']:.0f} deg rear rake"))
    xs0, ys0 = mounts.stations()[0]
    near = [G.socket_plane("L", 0) * k for k in _leaves(SS.socket_assembly("closed"))]
    stn = mounts.base_rails() + mounts.foot_pads() + mounts.port_station(xs0, ys0)
    cut8 = Plane(origin=(xs0, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
    made.append(_svg("SEC-27-008_port_station", [shell] + stn + near + [TR.body_keepout()], cut8,
                     f"SEC-27-008  port station x={xs0:.0f}: Weistec adapter, shims, spacer stop, "
                     "rail + wrench pocket, NL10ss, M10 stud/nut, EPDM pad at 33 %"))
    made.append(_detail(made[-1], "SEC-27-008D_port_station_detail", ys0 - 90.0, 150.0, 200.0,
                        f"SEC-27-008D  port station detail (x={xs0:.0f}), 1:1 viewBox, mm"))
    return made


def _detail(src, name, h0, v1, size, title):
    """Crop a section sheet to a square detail window (horizontal h0..h0+size, vertical down from v1)."""
    import re
    txt = src.read_text()
    txt = re.sub(r'width="[^"]+" height="[^"]+" viewBox="[^"]+"',
                 f'width="{size:.0f}mm" height="{size:.0f}mm" viewBox="{h0:.1f} {-v1:.1f} {size:.1f} {size:.1f}"',
                 txt, count=1)
    txt = txt.replace('stroke-width="0.5"', 'stroke-width="0.3"')
    txt = re.sub(r'<text x="14" y="22".*?</text>',
                 f'<text x="{h0 + 3:.1f}" y="{-v1 + 8:.1f}" font-family="monospace" font-size="4">{title}</text>',
                 txt)
    path = DWG / f"{name}.svg"
    path.write_text(txt)
    return path


def _compose(pl, lp):
    """A plane given in ``pl``'s local coordinates, expressed in the world frame."""
    o = pl.from_local_coords(lp.origin)
    xd = pl.from_local_coords(lp.origin + lp.x_dir) - o
    zd = pl.from_local_coords(lp.origin + lp.z_dir) - o
    return Plane(origin=o, x_dir=xd, z_dir=zd)


def kinematics():
    """Pivots and travel directions, vehicle frame (mm), for the render lane's animation.

    The render lane animates the CAD-exported STLs about THESE axes, so a motion in a clip is the
    motion the checks swept, not a hand-placed hinge.
    """
    import math
    out = {"units": "mm", "frame": "vehicle: X rearward, Y driver, Z up, origin bed front / rail top",
           "sockets": {}, "hatch": {}}
    k = hw.HW["rotary_latch"]["kinematics"]
    for side in "LR":
        for i in range(2):
            tag = f"{side}{i}"
            pl = G.socket_plane(side, i)
            latches = []
            for idx, u in enumerate(G.LATCH_U):
                lp = _compose(pl, SS.latch_plane(u))
                piv = (lp * Pos(0, hw.d("rotary_latch")["pivot_y"], hw.PIVOT_Z)).position
                pawl = (lp * Pos(0, hw.d("rotary_latch")["pawl_pivot_y"], hw.PAWL_Z)).position
                latches.append({"index": idx, "fork_pivot": list(piv), "pawl_pivot": list(pawl),
                                "axis": list(lp.x_dir), "fork_release_deg": k["open_deg"] - k["closed_deg"],
                                "pawl_release_deg": k["pawl_release_deg"]})
            hpl = _compose(pl, SS.handle_plane())
            out["sockets"][tag] = {
                "origin": list(pl.origin), "n": list(pl.z_dir), "v": list(pl.y_dir), "u": list(pl.x_dir),
                "removal": [["slide_n", SS.CATCH_TRAVEL - 1.0], ["lift_v", SS.CATCH_DROP + 1.0],
                            ["slide_n", 130.0]],
                "latches": latches,
                "handle_axis_point": list(hpl.origin), "handle_axis": list(hpl.x_dir),
                "handle_pull_deg": -14.0}
    hp = G.hatch_plane()
    ax_pt = (hp * Pos(0, HA.HINGE_Y, HA.HINGE_Z)).position
    out["hatch"] = {"hinge_point": list(ax_pt), "hinge_axis": list(hp.x_dir),
                    "open_deg": HA.OPEN_DEG, "sign": "positive swings the leaf bottom outward",
                    "strut_frame_studs": [list((hp * Pos(sx * HA.STRUT_FRAME[0], HA.STRUT_FRAME[1],
                                                          HA.STRUT_FRAME[2])).position) for sx in (-1, 1)],
                    "strut_leaf_studs": [list((hp * Pos(sx * HA.STRUT_LEAF[0], HA.STRUT_LEAF[1],
                                                         HA.STRUT_LEAF[2])).position) for sx in (-1, 1)],
                    "latches": [{"fork_pivot": list((_compose(hp, HA.latch_plane(x)) * Pos(
                        0, hw.d("rotary_latch")["pivot_y"], hw.PIVOT_Z)).position),
                        "axis": list(_compose(hp, HA.latch_plane(x)).x_dir)} for x in HA.LATCH_XS]}
    (OUT / "kinematics.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print("building closed assembly ...")
    shut = step27_assembly(0.0)
    export_step(shut, str(OUT / "R1T_TOPPER_STEP27.step"))
    print("building open assembly ...")
    opened = step27_assembly(HA.OPEN_DEG, module_gap=160.0, state="open")
    export_step(opened, str(OUT / "R1T_TOPPER_STEP27_open.step"))
    export_step(truck_reference(), str(OUT / "R1T_REFERENCE_KEEPOUTS.step"))
    print("exporting parts (closed) ...")
    man = export_parts(shut)
    print("exporting parts (open) ...")
    export_parts(opened, OUT / "parts_open", write_manifest=False)
    export_parts(truck_reference(), OUT / "reference", write_manifest=False)
    export_parts(payload_set("L1"), OUT / "parts_payloads", write_manifest=False)
    kinematics()
    print("exporting sections ...")
    secs = export_sections()
    total = sum(m["mass_kg"] for m in man)
    shell_kg = sum(m["mass_kg"] for m in man if "SHELL" in m["part"])
    print(f"\n{len(man)} distinct parts, estimated mass {total:.1f} kg "
          f"(shell {shell_kg:.1f} kg at 5.8 kg/m^2 sandwich)")
    for s_ in secs:
        print(f"  {s_.relative_to(ROOT)}")
    print("STEP27_EXPORT_OK")


if __name__ == "__main__":
    main()
