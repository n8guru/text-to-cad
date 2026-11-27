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
# cut the WHOLE gate block (verify task 165492):
#  * above the floor, from inside the bed (BED1 - 0.05: S11's loft ramps the bed's end wall across one
#    30 mm station bay before BED1) up to the traced tailgate face S11 lofted (1.461 > params 1.441,
#    so the old cut left an 18 mm wall across the doorway);
#  * below the floor, from x0 down through the folded slab's full thickness plus the same 20 mm
#    clearance the S11 rear bumper keeps (the old cut stopped at -0.477, inside the -0.525..-0.465 slab).
GATE_T, GATE_CLR = 0.06, 0.02
floor = -T["bed_depth"]
x1 = max(T["tailgate_x"], float(bpy.data.objects["R1T_BODY"].get("TAILGATE_FACE_X", 0.0))) + 0.002
zb = floor - GATE_T - GATE_CLR
xa = T["bed_len"] - 0.004 - 0.05


def boxo(name, c, s):
    bpy.ops.mesh.primitive_cube_add(size=1, location=c)
    o = bpy.context.object
    o.name = name
    o.scale = s
    bpy.ops.object.transform_apply(scale=True)
    return o


def cut_box(c, s):
    cutter = boxo("cut_tailgate", c, s)
    mod = body.modifiers.new("gate", "BOOLEAN")
    mod.operation, mod.object, mod.solver = "DIFFERENCE", cutter, "EXACT"
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter, do_unlink=True)


if body.get("TAILGATE_CUT_DONE") != 3:           # each version's cut contains the previous one
    za = floor + 0.0005                          # keep the bed floor itself
    cut_box(((xa + x1) / 2, 0, (za + 0.06) / 2), (x1 - xa, T["bed_w"] - 0.004, 0.06 - za))
    cut_box(((x0 + x1) / 2, 0, (zb + 0.06) / 2), (x1 - x0, T["bed_w"] + 0.02, 0.06 - zb))
    body["TAILGATE_CUT_DONE"] = 3
# the rear light bar is mounted on the tailgate's top edge; with the block folded away it would float
# in the doorway, so it leaves with the gate (the folded slab is an untextured context proxy)
if "REAR_LIGHTBAR" in bpy.data.objects:
    bpy.data.objects.remove(bpy.data.objects["REAR_LIGHTBAR"], do_unlink=True)
gate_len = T["bed_depth"] + GATE_T
gate = boxo("TAILGATE_LOWERED", (x0 + gate_len / 2, 0, -T["bed_depth"] - GATE_T / 2),
            (gate_len, T["bed_w"], GATE_T))
L.assign(gate, m["paint"])
L.link(gate, "20_ACCESS")

# ---- cargo proxy: 0.70 W x 0.60 H x 0.55 L, half-way in over the gate ---------------------------
cw, ch, cl = 0.70, 0.60, 0.55
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
topper_names = set(objs[n].name for n in objs)
IGNORE = {"CARGO_PROXY", "GROUND"}
gx0, gx1 = x0, x0 + gate_len
g_top, g_bot = floor, floor - GATE_T


def cast(origin, d, dist):
    """First hit along d that is not cargo/ground (those are stepped through)."""
    o = Vector(origin)
    left = dist
    while left > 0:
        hit, loc, nrm, idx, ob, mw = bpy.context.scene.ray_cast(dg, o, d, distance=left)
        if not hit:
            return None, None
        if ob.name not in IGNORE:
            return ob.name, loc
        step = (loc - o).length + 1e-4
        o, left = loc + d * 1e-4, left - step
    return None, None


# (1) full bed-to-tailgate path: rays from the front of the bed, straight back (+x), over the floor,
# through the doorway and across the lowered gate to its end. EVERY mesh (truck body, gate, lights,
# topper) is a blocker; only the cargo proxy (stepped through) and the ground are ignored.
clear, tot, blockers = 0, 0, set()
# below the rail: full doorway width; above it, the cargo's own width (the fitted side modules sit
# outboard of |y| ~0.4 above the rail by design, not in the loading path)
for yy, zz in ([(y, z) for y in (-0.50, -0.30, -0.15, 0.0, 0.15, 0.30, 0.50)
                for z in (floor + 0.01, floor + 0.15, floor + 0.30, -0.02)]
               + [(y, top_cargo - 0.02) for y in (-0.30, -0.15, 0.0, 0.15, 0.30)]):
    x_start = 0.05
    name, loc = cast((x_start, yy, zz), Vector((1, 0, 0)), gx1 + 0.05 - x_start)
    tot += 1
    if name is None:
        clear += 1
    else:
        blockers.add(f"{name}@x={loc.x:.3f},y={yy:+.2f},z={zz:+.3f}")
# (2) vertical probes through the lowered gate on a 25 mm x 100 mm grid. The gate and the cargo proxy
# are hidden, and each probe drops from just below the rail plane: the first truck/topper surface it
# meets must lie at least 10 mm below the gate's underside, i.e. nothing above the gate, nothing
# inside the slab, and a measured clearance under it. (A probe started inside the slab would first
# meet the slab's own faces, which is how an interference can hide from a naive probe.)
gate.hide_viewport = cargo.hide_viewport = True
dg = bpy.context.evaluated_depsgraph_get()
probe_bad, probe_n, under_clear = set(), 0, 9.0
xs = [gx0 + 0.0125 + 0.025 * i for i in range(int((gx1 - gx0) / 0.025))]
ys = [-T["bed_w"] / 2 + 0.05 + 0.1 * k for k in range(int((T["bed_w"] - 0.1) / 0.1) + 1)]
for xx in xs:
    for yy in ys:
        probe_n += 1
        name, loc = cast((xx, yy, -0.01), Vector((0, 0, -1)), 3.0)
        if name is None:
            continue
        under_clear = min(under_clear, g_bot - loc.z)
        if g_bot - loc.z < 0.010:
            probe_bad.add(f"{name}@x={xx:.3f},y={yy:+.2f},z={loc.z:+.3f}")
gate.hide_viewport = cargo.hide_viewport = False
dg = bpy.context.evaluated_depsgraph_get()
# (3) volumetric: BVH overlap of the gate slab (0.5 mm inset) against the truck body and every topper part
import bmesh  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402


def bvh(ob):
    bm = bmesh.new()
    bm.from_object(ob, dg)
    bm.transform(ob.matrix_world)
    t = BVHTree.FromBMesh(bm)
    bm.free()
    return t


# the gate inset by 0.5 mm: its hinge face abuts the bed end (x0) by construction, which is contact,
# not interference; anything that reaches 0.5 mm into the slab counts (the 165492 bumper reached 20 mm)
gmin, gmax = L.bbox(gate)
e = 0.0005
gx = (gmin[0] + e, gmax[0] - e)
gy = (gmin[1] + e, gmax[1] - e)
gz = (gmin[2] + e, gmax[2] - e)
gv = [(x, y, z) for x in gx for y in gy for z in gz]
gf = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
gt = BVHTree.FromPolygons(gv, gf)
overlaps = []
for o in bpy.data.objects:
    if o.type == "MESH" and o is not gate and o.name not in IGNORE:
        pairs = gt.overlap(bvh(o))
        if pairs:
            overlaps.append(o.name)
            print("OVERLAP", o.name, len(pairs), [tuple(round(c, 3) for c in o.matrix_world @
                                                       o.data.polygons[b].center) for _, b in pairs[:6]])
print("PATH_BLOCKERS", sorted(blockers))
print("GATE_PROBE_BAD", sorted(probe_bad))
print("GATE_OVERLAPS", overlaps)
scores = {
    "imported_parts": len(objs),
    "lowest_open_leaf_point_mm": lowest_leaf * 1000,
    "cargo_top_above_rail_mm": top_cargo * 1000,
    "bed_to_gate_path_rays_clear": clear,
    "bed_to_gate_path_rays_total": tot,
    "gate_probes_total": probe_n,
    "gate_probes_bad": len(probe_bad),
    "gate_mesh_penetrations": len(overlaps),
    "gate_underside_clearance_mm": under_clear * 1000,
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
