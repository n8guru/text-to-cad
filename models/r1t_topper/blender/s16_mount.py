"""S16: close-ups of the bed-port attachment station on the S12 scene (one move: add mount cameras).

Nothing is modelled here: every station part (Weistec adapter, shims, spacer, base rail, slot
washer, Nord-Lock pair, nut, stud, EPDM foot pad) is the STL exported by
step27/cad/assembly_step27.py. Cameras are aimed from the imported nut positions, so the views
follow the CAD if the stations move.

Views (rear-left station, the one nearest the tailgate):
  mount_cutaway   shell, hatch and modules hidden from the render: the clamp stack on the rail cap
  mount_service   shell visible, looking outboard from the bed: the wrench pocket open to the bed
  mount_overview  shell hidden, all four stations on the truck's rail caps

Scores (measured between the imported meshes):
  stations          number of complete stations (adapter+spacer+stud+nut+washer+lock) found
  stud_offset_mm    worst stud-to-adapter axis offset in plan (concentric by design: 0)
  nut_over_rail_mm  worst nut-bottom height above the rail top (nut sits in the 12 mm pocket: < 0)
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
ad, sp, st, nu = fam("PORT_ADAPTER"), fam("PORT_SPACER"), fam("PORT_STUD"), fam("PORT_NUT")
wa, lk = fam("PORT_SLOT_WASHER"), fam("WEDGE_WASHER")
rails = fam("BASE_RAIL")
stations = min(len(ad), len(sp), len(st), len(nu), len(wa), len(lk))

off = []
for s in st:
    a = min(ad, key=lambda a: (ctr(a) - ctr(s)).xy.length)
    off.append((ctr(a) - ctr(s)).xy.length * 1000)
rail_top = max(wb(r)[1][2] for r in rails)
nut_over = max((wb(n)[0][2] - rail_top) * 1000 for n in nu)

# rear-left station = largest x (rearward), positive y
rl = max(nu, key=lambda n: (round(ctr(n).y > 0), ctr(n).x))
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
mid = Vector((sum(ctr(n).x for n in nu) / len(nu), 0.0, c.z))
paths += render({"mount_overview": ((mid.x + 2.4, mid.y + 2.2, mid.z + 1.9), tuple(mid), 40)}, hide)

scores = {"stations": float(stations), "stud_offset_mm": max(off), "nut_over_rail_mm": nut_over}
for p in paths:
    img = bpy.data.images.load(p)
    px = np.array(img.pixels[:]).reshape(-1, 4)[:, :3]
    scores["lum_" + os.path.basename(p)[:-4].split("_mount_")[-1]] = float(
        (px @ np.array([0.2126, 0.7152, 0.0722])).mean())
    bpy.data.images.remove(img)
print("SCORE " + " ".join(f"{k}={v:.3f}" for k, v in scores.items()))
L.report_scores(scores)
