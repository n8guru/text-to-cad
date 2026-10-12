"""One move: import an exact primary-foot CAD state, then inspect assembled/capture detail.
Orange = custom primary C-jaw; violet = PROVISIONAL source-inspired bridge reference.
Cutaway view HIDES the housing/paddle, never reshapes product solids.
"""
import os
import sys
import bpy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r1t_lib as L

state = os.environ.get("R1T_MOUNT_STATE", "closed")
assert state in ("closed", "caught", "released")
for obj in list(bpy.data.objects):
    if any(c.name == "30_MOUNT_DETAIL" for c in obj.users_collection):
        bpy.data.objects.remove(obj, do_unlink=True)
objs = L.import_parts(L.STEP27 / "out" / ("parts_step30_mount_" + state), "30_MOUNT_DETAIL")
assert objs, "Generate the exact CAD detail packet first"
hook = next(o for n, o in objs.items() if n.startswith("PLF_HOOK_SLIDER"))
bridge = next(o for n, o in objs.items() if n.startswith("PORT_REF_BRIDGE"))
L.assign(hook, L.mat("STEP30_JAW_ORANGE", (0.90, 0.22, 0.035), metal=0.3, rough=0.35))
L.assign(bridge, L.mat("STEP30_REFERENCE_VIOLET", (0.38, 0.07, 0.65), metal=0.2, rough=0.4))
lo, hi = L.bbox(bridge)
c = [(a + b) / 2 for a, b in zip(lo, hi)]
old_hidden = {o: o.hide_render for o in bpy.data.objects if o.type == "MESH"}
for o in old_hidden:
    o.hide_render = o not in objs.values()
L.look({"mount_" + state + "_assembled": ((c[0] + .19, c[1] - .26, c[2] + .14),
                                         (c[0], c[1] - .006, c[2] + .035), 65)},
       res=(1400, 1000), engine="CYCLES", samples=int(os.environ.get("R1T_SAMPLES", "40")))
for o in objs.values():
    o.hide_render = o not in (hook, bridge)
name = "mount_" + state + "_capture_cutaway"
loc, target = (c[0] + .16, c[1] - .08, c[2] + .045), tuple(c)
cam = L.camera("CAM_" + name, loc, target, 60)
cam.data.type = "ORTHO"
cam.data.ortho_scale = .075
L.look({name: (loc, target, 60)}, res=(1400, 1000), engine="CYCLES",
       samples=int(os.environ.get("R1T_SAMPLES", "40")))
for o, hidden in old_hidden.items():
    o.hide_render = hidden
L.report_scores({"imported_mount_parts": len(objs), "bridge_reference_count": 1,
                 "bridge_span_mm": (hi[0]-lo[0])*1000,
                 "jaw_vertices": len(hook.data.vertices),
                 "release_state": float(state == "released")})
