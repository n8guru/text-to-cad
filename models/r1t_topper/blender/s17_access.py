"""S17 (Step 29): rear access -- hatch raised, tailgate lowered, cargo going in over the gate.

Nate (operator card 2081357): "a topper is meant to allow the truck tail-gate to open, and the hatch
of the topper to open, and then have a large access to truck bed."

Run after S11 (truck) and S12 (topper import). This step:
  * replaces the closed topper with the CAD export in ``out/parts_access`` (hatch at its open angle,
    side modules fitted - assembly_step27.py writes it),
  * folds the TAILGATE down: the traced body's tailgate block (x from the bed's end to the tailgate
    face, rail plane down to the bed floor) is cut away and a 60 mm slab flush with the bed floor is
    laid behind the bed (the same envelope as step27/cad/truck.py::tailgate_lowered_keepout),
  * lays a cardboard cargo proxy half-way in over the gate and measures that it clears the
    doorway (top of cargo vs the header).
Blender models none of the topper; the cargo proxy and the folded gate are reference/context only.
"""
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r1t_lib as L  # noqa: E402

T = L.T
for o in list(bpy.data.objects):                 # idempotent
    if any(c.name in ("10_TOPPER_CAD", "20_ACCESS") for c in o.users_collection):
        bpy.data.objects.remove(o, do_unlink=True)
objs = L.import_parts(L.STEP27 / "out" / "parts_access", "10_TOPPER_CAD")
body = bpy.data.objects["R1T_BODY"]
m = L.M()

# ---- fold the tailgate down -----------------------------------------------------------------
x0 = T["bed_len"] - 0.004 + 0.002                # first station past the bed (S11 BED1)
x1 = T["tailgate_x"] + 0.002
zb = -T["bed_depth"] - 0.012


def boxo(name, c, s):
    bpy.ops.mesh.primitive_cube_add(size=1, location=c)
    o = bpy.context.object
    o.name = name
    o.scale = s
    bpy.ops.object.transform_apply(scale=True)
    return o


if "TAILGATE_CUT_DONE" not in body:
    cutter = boxo("cut_tailgate", ((x0 + x1) / 2, 0, (zb + 0.06) / 2), (x1 - x0, T["bed_w"] + 0.02, 0.06 - zb))
    mod = body.modifiers.new("gate", "BOOLEAN")
    mod.operation, mod.object, mod.solver = "DIFFERENCE", cutter, "EXACT"
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter, do_unlink=True)
    body["TAILGATE_CUT_DONE"] = 1
gate_len = T["bed_depth"] + 0.06
gate = boxo("TAILGATE_LOWERED", (x0 - 0.06 + gate_len / 2 + 0.06, 0, -T["bed_depth"] - 0.03),
            (gate_len, T["bed_w"], 0.06))
L.assign(gate, m["paint"])
L.link(gate, "20_ACCESS")

# ---- cargo proxy: 0.70 W x 0.60 H x 0.55 L, half-way in over the gate ---------------------------
cw, ch, cl = 0.70, 0.60, 0.55
floor = -T["bed_depth"]
cx = T["tailgate_x"] - 0.06 - 0.05
cargo = boxo("CARGO_PROXY", (cx, 0.0, floor + ch / 2), (cl, cw, ch))
L.assign(cargo, L.mat("CARDBOARD", (0.42, 0.30, 0.17), rough=0.9))
L.link(cargo, "20_ACCESS")

# ---- measures -------------------------------------------------------------------------------
shell = objs["SHELL_CARBON_SANDWICH"]
top_cargo = floor + ch
leaf = [o for n, o in objs.items() if n.startswith("HATCH_LEAF_HATCH_LEAF_CARBON")]
lowest_leaf = min(L.bbox(o)[0][2] for o in leaf)
dg = bpy.context.evaluated_depsgraph_get()
# rays from the cargo's rear face, straight back (+x) through the doorway: no TOPPER part may be hit
topper_names = set(objs[n].name for n in objs)
clear, tot, blockers = 0, 0, set()
for yy in (-0.30, -0.15, 0.0, 0.15, 0.30):
    for zz in (top_cargo - 0.02, top_cargo - 0.30):
        hit, loc, nrm, idx, ob, mw = bpy.context.scene.ray_cast(
            dg, Vector((cx + cl / 2 + 0.01, yy, zz)), Vector((1, 0, 0)), distance=3.0)
        tot += 1
        if hit and ob.name in topper_names:
            blockers.add(ob.name)
        else:
            clear += 1
print("BLOCKERS", sorted(blockers))
scores = {
    "imported_parts": len(objs),
    "lowest_open_leaf_point_mm": lowest_leaf * 1000,
    "cargo_top_above_rail_mm": top_cargo * 1000,
    "cargo_exit_rays_clear": clear,
    "cargo_exit_rays_total": tot,
    "bed_floor_below_rail_mm": T["bed_depth"] * 1000,
}
print("SCORE " + " ".join(f"{k}={v:.2f}" for k, v in scores.items()))

V = {
    "access_rear3q": ((4.7, 3.3, 1.15), (1.05, 0.0, -0.20), 34),
    "access_rear": ((5.6, 0.0, 0.75), (1.1, 0.0, -0.10), 34),
    "access_side": ((1.15, 7.0, 0.05), (1.15, 0.0, -0.10), 30),
    "access_top_rear": ((3.6, 1.2, 2.6), (1.2, 0.0, -0.20), 36),
}
L.look(V, res=(1600, 1000), engine="CYCLES", samples=int(os.environ.get("R1T_SAMPLES", "96")))
L.report_scores(scores)
