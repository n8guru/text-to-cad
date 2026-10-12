"""Step 30: camera-only rear evidence of the unchanged imported CAD geometry.
Run after S12. Orthographic rear view avoids perspective ambiguity in hatch width.
The truck remains the Step29 drawing-derived proxy, not a measured vehicle.
"""
import os
import sys
import bpy
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r1t_lib as L

views = {
    "closed_rear": ((5.5, 0, 0.08), (1.25, 0, 0.08), 50),
    "closed_rear3q": ((4.8, 3.2, 0.85), (0.72, 0, -0.10), 42),
}
cam = L.camera("CAM_closed_rear", *views["closed_rear"])
cam.data.type = "ORTHO"
cam.data.ortho_scale = 2.35
paths = L.look(views, res=(1600, 1100), engine="CYCLES",
               samples=int(os.environ.get("R1T_SAMPLES", "48")))
scores = {}
for path in paths:
    im = bpy.data.images.load(path)
    px = np.asarray(im.pixels[:]).reshape(-1, 4)[:, :3]
    scores["mean_linear_luminance_" + os.path.basename(path)] = float(
        (px @ np.array([0.2126, 0.7152, 0.0722])).mean())
    bpy.data.images.remove(im)
scores["cad_mesh_count"] = sum(
    o.type == "MESH" and any(c.name == "10_TOPPER_CAD" for c in o.users_collection)
    for o in bpy.data.objects)
L.report_scores(scores)
