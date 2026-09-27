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

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build123d import (  # noqa: E402
    Axis, Compound, ExportSVG, LineType, Location, Plane, Pos, Rot, Vector,
    export_step, export_stl, section,
)

import geom as G  # noqa: E402
import hatch as HA  # noqa: E402
import hw  # noqa: E402
import side_socket as SS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out"
PARTS = OUT / "parts"
DWG = ROOT / "drawings"

# material / process / finish per part family — this is what makes the BOM orderable rather than
# a picture. Density in kg/mm^3 for the mass rollup.
MATERIAL = {
    "SOCKET_FRAME": ("6061-T6", "3-axis CNC, one program + one fixture for all four",
                     "black anodise Type II", 2.70e-6),
    "LEDGE_RAIL": ("6061-T6", "CNC from 50x30 bar", "clear anodise", 2.70e-6),
    "MODULE_PLUG_FRAME": ("6061-T6", "CNC", "black anodise Type II", 2.70e-6),
    "J_HOOK": ("316 stainless", "laser + press brake", "passivate", 8.00e-6),
    "HATCH_SURROUND": ("6061-T6", "CNC from 12 mm plate", "black anodise Type II", 2.70e-6),
    "HATCH_GUTTER": ("6061-T6", "press brake", "black anodise Type II", 2.70e-6),
    "HATCH_DRAIN": ("6061-T6", "extrusion, cut to length", "black anodise Type II", 2.70e-6),
    "HATCH_LEAF_CARBON": ("carbon/PET sandwich, 200 gsm 2x2 twill + 300 gsm biax over 20 mm core",
                          "vacuum infusion, female mould", "UV clear", 0.223e-6),
    "GLAZING_PANE": ("5 mm hard-coat polycarbonate (Makrolon AR / Lexan Margard)",
                     "CNC rout + polish", "hard coat both faces", 1.20e-6),
    "GLAZING_RETAINER": ("6061-T6", "CNC", "black anodise Type II", 2.70e-6),
    "CLOSEOUT": ("3 mm ABS", "thermoform", "grained black", 1.04e-6),
    "STRIKER_BRACKET": ("316 stainless", "laser + machine", "passivate", 8.00e-6),
    "COMPRESSION_LIMITER": ("UHMW-PE virgin", "waterjet + surface grind to 7.40 +0/-0.05",
                            "as machined", 0.94e-6),
    "BULB_SEAL": ("EPDM sponge bulb on dense EPDM 70 Shore A base, aluminium wire carrier",
                  "purchased extrusion, cut and bonded at the joint", "black", 0.70e-6),
}
PURCHASED_PREFIX = {
    "ROTARY_LATCH": "rotary_latch", "STRIKER_BOLT": "striker", "RELEASE_CABLE": "release_cable",
    "RELEASE_HANDLE": "release_handle", "CABLE_SPLITTER": "release_handle",
    "LOCATING_PIN_ROUND": "locating_pin_round", "LOCATING_PIN_DIAMOND": "locating_pin_diamond",
    "BUSHING": "bushing", "BALL_PLUNGER": "ball_plunger", "GAS_STRUT": "gas_strut",
    "BALL_STUD": "gas_strut", "CONCEALED_HINGE": "hinge", "T_HANDLE": "t_handle",
    "CHMSL": "chmsl", "COMPRESSION_LIMITER": "compression_limiter", "BULB_SEAL": "bulb_seal",
}


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
        item = PURCHASED_PREFIX[k]
        if k in up:
            h = hw.HW[item]
            return (h.get("manufacturer"), h.get("pn"), h.get("status"), h.get("source_url"))
    return (None, None, "CUSTOM", None)


# --------------------------------------------------------------------------------------
def step27_assembly(hatch_deg: float = 0.0, module_gap: float = 0.0, state: str = "closed"):
    """Everything Step 27 owns, in the vehicle frame."""
    kids = []
    for side in "LR":
        for i in range(2):
            pl = G.socket_plane(side, i)
            gap = module_gap if (side, i) == ("L", 1) else 0.0
            st = state if (side, i) == ("L", 1) else "closed"
            for c in SS.socket_assembly(st).children:
                c2 = pl * c
                c2.label = f"{side}{i}_{c.label}"
                kids.append(c2)
            for c in SS.module_interface(gap).children:
                c2 = pl * c
                c2.label = f"{side}{i}_MOD_{c.label}"
                kids.append(c2)
    hp = G.hatch_plane()
    for c in HA.hatch_assembly(hatch_deg).children:
        c2 = hp * c
        c2.label = f"HATCH_{c.label}"
        kids.append(c2)
    a = Compound(children=kids)
    a.label = f"R1T_TOPPER_STEP27_hatch{hatch_deg:.0f}"
    return a


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
            export_stl(part, str(fn), tolerance=0.08, angular_tolerance=0.2)
        except Exception as exc:
            print(f"  stl skip {base}: {exc}")
            continue
        mat, proc, fin, dens = _classify(base)
        mfr, p_n, status, url = _pn_for(base)
        manifest.append({
            "part": base, "stl": fn.name, "volume_mm3": round(v, 1),
            "mass_kg": round(v * dens, 3), "material": mat, "process": proc, "finish": fin,
            "manufacturer": mfr, "pn": p_n, "status": status, "source_url": url,
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


def export_sections():
    made = []
    # 1. socket section through a latch station: land, seal, plug, fork bolt, striker bolt
    pl = G.socket_plane("L", 1)
    socket_parts = [pl * c for c in SS.socket_assembly("closed").children]
    socket_parts += [pl * c for c in SS.module_interface().children]
    cut = Plane(origin=(pl * Pos(G.LATCH_U[1], 0, 0)).position,
                x_dir=Vector(0, 0, 1), z_dir=(pl.x_dir))
    made.append(_svg("SEC-27-001_socket_through_latch", socket_parts, cut,
                     "SEC-27-001  socket, vertical section through the u=+250 latch station"))

    # 2. socket section through the seal / ledge on the centreline
    cut2 = Plane(origin=pl.origin, x_dir=pl.z_dir, z_dir=pl.x_dir)
    made.append(_svg("SEC-27-002_socket_seal_and_ledge", socket_parts, cut2,
                     "SEC-27-002  socket centreline: seal rib, bulb at 33 %, hook ledge"))

    # 3. hatch section on the centreline, shut: gutter, seal, leaf, glazing rebate
    hp = G.hatch_plane()
    shut = [hp * c for c in HA.hatch_assembly(0.0).children]
    cut3 = Plane(origin=hp.origin, x_dir=hp.z_dir, z_dir=hp.x_dir)
    made.append(_svg("SEC-27-003_hatch_shut_centreline", shut, cut3,
                     "SEC-27-003  rear hatch shut, centreline: gutter, seal, glazing retention"))

    # 4. hatch section at the latch station, shut
    cut4 = Plane(origin=(hp * Pos(HA.LATCH_X, 0, 0)).position, x_dir=hp.z_dir, z_dir=hp.x_dir)
    made.append(_svg("SEC-27-004_hatch_latch_station", shut, cut4,
                     "SEC-27-004  rear hatch latch station: R4-30 + R4-90-321-20 striker bolt"))

    # 5. hatch open at 95 deg, strut station, showing the swept path
    op = [hp * c for c in HA.hatch_assembly(HA.OPEN_DEG).children]
    cut5 = Plane(origin=(hp * Pos(HA.STRUT_LEAF_X, 0, 0)).position, x_dir=hp.z_dir, z_dir=hp.x_dir)
    made.append(_svg("SEC-27-005_hatch_open_strut", op, cut5,
                     "SEC-27-005  rear hatch at 95 deg: Stabilus 6541IS at 369.5 of 375.5 mm"))
    return made


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print("building closed assembly ...")
    shut = step27_assembly(0.0)
    export_step(shut, str(OUT / "R1T_TOPPER_STEP27.step"))
    print("building open assembly ...")
    opened = step27_assembly(HA.OPEN_DEG, module_gap=160.0, state="open")
    export_step(opened, str(OUT / "R1T_TOPPER_STEP27_open.step"))
    print("exporting parts (closed) ...")
    man = export_parts()
    print("exporting parts (open) ...")
    export_parts(opened, OUT / "parts_open", write_manifest=False)
    print("exporting sections ...")
    secs = export_sections()
    total = sum(m["mass_kg"] for m in man)
    print(f"\n{len(man)} distinct parts, estimated hardware mass {total:.1f} kg "
          f"(excludes the shell, which lives in the Blender model)")
    for s in secs:
        print(f"  {s.relative_to(ROOT)}")
    print("STEP27_EXPORT_OK")


if __name__ == "__main__":
    main()
