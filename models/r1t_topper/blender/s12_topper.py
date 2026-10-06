"""S12: import the authoritative CAD topper onto the traced R1T (one move: add the topper).

Everything in 10_TOPPER_CAD is an STL exported by step27/cad/assembly_step27.py in vehicle
coordinates: the styled carbon shell, 4 top-hat socket frames with latches, the default module kit
(L0 WINDOW, L1 CAGE, R0 WINDOW, R1 TOOLBOX), the hatch, base rails and the four Port Latch Feet (PLF_*). Blender
models none of it.

Scores are measured in this scene, between the imported CAD meshes and the traced truck:
  roof_step_mm     topper roof top minus the truck's cab roof (continuity, R1S target ~0)
  cab_gap_mm       closest shell-to-truck-body distance over the cab back / spoiler (>= 20)
  base_gap_mm      worst gap between the shell foot and the rail caps (seated ~0)
"""
import os
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r1t_lib as L  # noqa: E402

for o in list(bpy.data.objects):                 # idempotent re-run of this step
    if any(c.name == "10_TOPPER_CAD" for c in o.users_collection):
        bpy.data.objects.remove(o, do_unlink=True)
objs = L.import_parts(L.PARTS, "10_TOPPER_CAD")
shell = objs["SHELL_CARBON_SANDWICH"]
body = bpy.data.objects["R1T_BODY"]


def bvh(o):
    dg = bpy.context.evaluated_depsgraph_get()
    return BVHTree.FromObject(o, dg)


tb, ts = L.world_bvh([body]), L.world_bvh([shell])
mw = shell.matrix_world
# cab gap: CAB faces only (above the rail, ahead of the bed) -> nearest point on the shell
bw = body.matrix_world
cab_pts = [bw @ p.center for p in body.data.polygons
           if (bw @ p.center).z > 0.03 and (bw @ p.center).x < 0.0]
gap = min((ts.find_nearest(p)[3] for p in cab_pts if ts.find_nearest(p)[0] is not None), default=-1)
# base seating: foot-bottom vertices over the FLAT rail cap, ray down onto the traced truck
foot = [mw @ v.co for v in shell.data.vertices
        if abs((mw @ v.co).z) < 0.0005 and abs((mw @ v.co).y) > L.T["rail_cap_in"] + 0.01
        and (mw @ v.co).x < L.T["rail_flat_end_x"]]
gaps = []
for p in foot[::7]:
    hit = tb.ray_cast(p + Vector((0, 0, 0.01)), Vector((0, 0, -1)), 0.08)
    if hit[0] is not None:
        gaps.append((p.z - hit[0].z))
top = max((mw @ v.co).z for v in shell.data.vertices)
body_roof = max(v.co.z for v in body.data.vertices if not -0.47 < v.co.x < -0.36)
scores = {
    "imported_parts": len(objs),
    "roof_step_mm": (top - body_roof) * 1000,
    "cab_gap_mm": gap * 1000,
    "base_gap_max_mm": max(gaps) * 1000 if gaps else -1,
    "base_gap_min_mm": min(gaps) * 1000 if gaps else -1,
    "base_samples": len(gaps),
}
print("SCORE " + " ".join(f"{k}={v:.2f}" for k, v in scores.items()))

V = {
    "ctx_side_L": ((0.3, 7.6, 0.05), (0.3, 0.0, -0.30), 38),
    "ctx_rear3q": ((4.6, 3.6, 1.05), (0.55, 0.0, 0.0), 34),
    "ctx_front3q": ((-5.8, 4.6, 1.35), (0.2, 0.0, -0.05), 36),
    "ctx_junction": ((-0.20, 2.2, 0.50), (-0.10, 0.62, 0.30), 42),
    "ctx_top": ((0.4, 0.0, 6.5), (0.4, 0.0, 0.0), 32),
}
L.look(V, res=(1400, 800))
L.report_scores(scores)
