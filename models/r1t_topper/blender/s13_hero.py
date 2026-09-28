"""S13: photoreal Cycles views of the CAD topper on the traced R1T (one move: switch to Cycles).

Default kit (L0 WINDOW, L1 CAGE, R0 WINDOW, R1 TOOLBOX). Scores are image statistics, so a black
or blown frame cannot pass silently, plus the in-scene roof step (continuity with the cab roof).
"""
import os
import sys

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r1t_lib as L  # noqa: E402

V = {
    "hero_rear3q": ((4.9, 3.9, 0.85), (0.45, 0.05, -0.10), 38),
    "hero_front3q": ((-6.0, 4.3, 0.95), (-0.6, 0.0, -0.20), 40),
    "hero_side": ((-0.3, 8.2, -0.10), (-0.3, 0.0, -0.20), 36),
    "hero_junction": ((-0.9, 3.2, 0.75), (-0.05, 0.3, 0.25), 45),
}
paths = L.look(V, res=(1600, 1000), engine="CYCLES", samples=int(os.environ.get("R1T_SAMPLES", "128")))
scores = {}
for p in paths:
    img = bpy.data.images.load(p)
    px = np.array(img.pixels[:]).reshape(-1, 4)[:, :3]
    lum = float((px @ np.array([0.2126, 0.7152, 0.0722])).mean())
    scores[f"lum_{os.path.basename(p)[:-4].split('_hero_')[-1]}"] = lum
    bpy.data.images.remove(img)
shell = bpy.data.objects["SHELL_CARBON_SANDWICH"]
body = bpy.data.objects["R1T_BODY"]
top = max((shell.matrix_world @ v.co).z for v in shell.data.vertices)
cab = max(v.co.z for v in body.data.vertices if not -0.47 < v.co.x < -0.36)
scores["roof_step_mm"] = (top - cab) * 1000
scores["min_lum"] = min(v for k, v in scores.items() if k.startswith("lum_"))
scores["max_lum"] = max(v for k, v in scores.items() if k.startswith("lum_"))
print("SCORE " + " ".join(f"{k}={v:.3f}" for k, v in scores.items()))
L.report_scores(scores)
