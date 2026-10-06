"""S16: close-ups of the Port Latch Foot (PLF) on the S12 scene (one move: add mount cameras).

Nothing is modelled here: every foot part (PLF_BODY, PLF_PADDLE, PLF_HOOK_SLIDER, PLF_LOCK_CYLINDER,
hinge pin, detent plunger, tuning screw, rail screws, shims), the base rail and the EPDM foot pad is
the STL exported by step27/cad/assembly_step27.py (paddle CLOSED). Cameras are aimed from the imported
PLF_BODY positions, so the views follow the CAD if the stations move. The paddle sweep itself is in
out/kinematics.json -> port_latch (hinge axis per station, 0 / stage 1 / open angles, cam law).

Views (rear-left station, the one nearest the tailgate):
  mount_cutaway   shell, hatch and modules hidden from the render: the foot on the rail cap
  mount_service   shell visible, looking outboard from the bed: the paddle + lock face INBOARD
  mount_overview  shell hidden, all four feet on the truck's rail caps

Scores (measured between the imported meshes):
  stations          number of complete feet (body + paddle + slider + lock) found
  paddle_inboard_mm worst (min over feet) distance the paddle sits INBOARD of its body, mm (> 0)
  lock_under_paddle_mm  worst lateral offset between the lock cylinder and the paddle plate (0 by design)
"""
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r1t_lib as L  # noqa: E402


def wb(o):
    return L.world_bbox([o])


def ctr(o):
    lo, hi = wb(o)
    return (Vector(lo) + Vector(hi)) / 2


objs = {o.name: o for o in bpy.data.objects
        if any(c.name == "10_TOPPER_CAD" for c in o.users_collection)}
fam = lambda p: sorted((o for n, o in objs.items() if n.startswith(p)), key=lambda o: tuple(ctr(o)))  # noqa: E731
bd, pd, sl, lk = fam("PLF_BODY"), fam("PLF_PADDLE"), fam("PLF_HOOK_SLIDER"), fam("PLF_LOCK")
rails = fam("BASE_RAIL")
stations = min(len(bd), len(pd), len(sl), len(lk))

inb, off = [], []
for b_ in bd:
    p_ = min(pd, key=lambda p: (ctr(p) - ctr(b_)).length)
    l_ = min(lk, key=lambda k: (ctr(k) - ctr(b_)).length)
    # inboard = toward the truck centreline: |y| of the paddle < |y| of the body
    inb.append((abs(ctr(b_).y) - abs(ctr(p_).y)) * 1000)
    off.append(abs(ctr(l_).x - ctr(p_).x) * 1000)

# rear-left station = largest x (rearward), positive y (hide list, cameras below)
rl = max(bd, key=lambda n: (round(ctr(n).y > 0), ctr(n).x))
c = ctr(rl)
side = 1.0 if c.y > 0 else -1.0

hide = [o for n, o in objs.items()
        if n.startswith(("SHELL", "HATCH", "L0_", "L1_", "R0_", "R1_", "SOCKET", "GLAZING",
                         "ROOF_HARDPOINT", "CHMSL", "FRONT_PASS", "GAS_STRUT", "T_HANDLE",
                         "LEAF_", "STRIKER", "MODULE", "COMPRESSION", "J_HOOK", "BULB_SEAL"))]


def render(views, hidden):
    for o in hidden:
        o.hide_render = True
    paths = L.look(views, res=(1600, 1000), engine="CYCLES",
                   samples=int(os.environ.get("R1T_SAMPLES", "96")))
    for o in hidden:
        o.hide_render = False
    return paths


tgt = tuple(c)
paths = render({"mount_cutaway": ((c.x + 0.42, c.y + side * 0.40, c.z + 0.30), tgt, 70)}, hide)
paths += render({"mount_service": ((c.x - 0.10, c.y - side * 0.55, c.z + 0.22), tgt, 55)}, [])
mid = Vector((sum(ctr(n).x for n in bd) / len(bd), 0.0, c.z))
paths += render({"mount_overview": ((mid.x + 2.4, mid.y + 2.2, mid.z + 1.9), tuple(mid), 40)}, hide)

scores = {"stations": float(stations), "paddle_inboard_mm": min(inb), "lock_under_paddle_mm": max(off)}
for p in paths:
    img = bpy.data.images.load(p)
    px = np.array(img.pixels[:]).reshape(-1, 4)[:, :3]
    scores["lum_" + os.path.basename(p)[:-4].split("_mount_")[-1]] = float(
        (px @ np.array([0.2126, 0.7152, 0.0722])).mean())
    bpy.data.images.remove(img)
print("SCORE " + " ".join(f"{k}={v:.3f}" for k, v in scores.items()))
L.report_scores(scores)
