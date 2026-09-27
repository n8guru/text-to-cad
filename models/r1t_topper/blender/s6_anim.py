"""S6: keyframe the shared lock sequence. One socket (L1) cycles CAGE -> TOOLBOX -> WINDOW -> CAGE,
each: lever pull -> claws open -> pop 3 mm -> tilt 8 deg on hooks -> lift 25 mm off ledge -> withdraw;
then next module: approach -> drop onto ledge -> swing shut -> claws snap (two-stage) -> lever home.
Hatch opens/closes after. ANIM_PREVIEW=1 renders key-pose stills only (blender-loop look)."""
import math
import os
import sys

sys.path.insert(0, "/home/n8/text-to-cad-worktrees/r1t-opus-pass/models/r1t_topper/blender")
import bpy
from mathutils import Matrix
import r1t_lib as L
import s3_sockets as S3
import s4_modules as S4

sc = bpy.context.scene
sc.render.fps = 24
TAG = "L1"
sock = bpy.data.objects["SOCKET_" + TAG]
Hh = S3.geo()["H"]


def normalize(obj, local_mat):
    obj.matrix_parent_inverse = Matrix.Identity(4)
    obj.matrix_basis = local_mat


# modules at L1: build the two not yet present
for kind in ("CAGE", "TOOLBOX", "WINDOW"):
    if f"MOD_{TAG}_{kind}" not in bpy.data.objects:
        S4.build_module(kind, TAG)
mods = {k: bpy.data.objects[f"MOD_{TAG}_{k}"] for k in ("CAGE", "TOOLBOX", "WINDOW")}
for k, root in mods.items():
    normalize(root, Matrix.Identity(4))
    normalize(bpy.data.objects[root.name + "_PIV"], Matrix.Translation(S4.PIVOT))
claws = [bpy.data.objects[f"LATCH_CLAW_{TAG}_{k}"] for k in range(2)]
for k, c in enumerate(claws):
    normalize(c, Matrix.Translation((S3.LATCH_U[k] + 0.031, Hh / 2 - 0.030, -0.104)))
lever = bpy.data.objects["RELEASE_LEVER_" + TAG]
normalize(lever, Matrix.Translation((0, Hh / 2 - 0.010, -0.122)))


def vis(kind, frame, on):
    for o in [mods[kind]] + list(mods[kind].children_recursive):
        o.hide_render = o.hide_viewport = not on
        o.keyframe_insert("hide_render", frame=frame)
        o.keyframe_insert("hide_viewport", frame=frame)


def pose(kind, f, n=0.0, v=0.0, tilt=0.0):
    root, piv = mods[kind], bpy.data.objects[mods[kind].name + "_PIV"]
    root.location = (0, v, n)
    root.keyframe_insert("location", frame=f)
    piv.rotation_euler = (math.radians(tilt), 0, 0)
    piv.keyframe_insert("rotation_euler", frame=f)


def latch(f, open_):
    for c in claws:
        c.rotation_euler = (math.radians(-75 if open_ else 0), 0, 0)
        c.keyframe_insert("rotation_euler", frame=f)


def lev(f, pulled):
    lever.rotation_euler = (math.radians(-35 if pulled else 0), 0, 0)
    lever.keyframe_insert("rotation_euler", frame=f)


OUT_N, OUT_V = 0.55, -0.10


def remove(kind, f0):
    """unlock -> remove; returns end frame."""
    pose(kind, f0)
    lev(f0, False); latch(f0 + 4, False)
    lev(f0 + 10, True)
    latch(f0 + 12, True)                        # both claws release from one pull
    pose(kind, f0 + 12)
    pose(kind, f0 + 16, n=0.003)                # seal spring-back pops module 3 mm
    lev(f0 + 18, True); lev(f0 + 24, False)
    pose(kind, f0 + 32, n=0.003, tilt=8)        # tilt on hooks: pins clear bushings
    pose(kind, f0 + 42, n=0.003, v=0.025, tilt=8)   # lift hooks off ledge lip
    pose(kind, f0 + 64, n=OUT_N, v=0.025, tilt=0)   # withdraw
    pose(kind, f0 + 76, n=OUT_N, v=OUT_V)
    vis(kind, f0 + 77, False)
    return f0 + 78


def insert(kind, f0):
    vis(kind, f0 - 1, False)
    vis(kind, f0, True)
    pose(kind, f0, n=OUT_N, v=OUT_V)
    pose(kind, f0 + 14, n=OUT_N, v=0.025)
    pose(kind, f0 + 36, n=0.012, v=0.025, tilt=8)   # hooks pass over ledge lip (plug lead-in chamfer guides)
    pose(kind, f0 + 44, n=0.012, v=0.0, tilt=8)     # drop onto ledge: weight now on hooks
    pose(kind, f0 + 58, n=0.003, v=0.0, tilt=0)     # swing shut: pins find bushings (round + diamond)
    latch(f0 + 58, True)
    pose(kind, f0 + 61, n=0.0)                      # push compresses seal 30 %, claws snap: primary catch
    latch(f0 + 61, False)
    return f0 + 72


# initial states
for k in mods:
    vis(k, 1, k == "CAGE")
    pose(k, 1, n=OUT_N, v=OUT_V)
pose("CAGE", 1)
latch(1, False); lev(1, False)
f = 12
order = ["CAGE", "TOOLBOX", "WINDOW", "CAGE"]
marks = {}
for a, b in zip(order, order[1:]):
    marks[f"{a}_out"] = f
    f = remove(a, f) + 6
    marks[f"{b}_in"] = f
    f = insert(b, f) + 12
swap_end = f
# hatch: open 95 deg (bottom swings out/up about top hinge), hold, close
hp = bpy.data.objects["HATCH_PIV"]
hf = bpy.data.objects["HATCH_FRAME"]
loc_local = (hf.matrix_world.inverted() @ hp.matrix_world).translation
normalize(hp, Matrix.Translation(loc_local))
for fr, ang in ((swap_end + 10, 0), (swap_end + 50, -L.H["open_deg"]), (swap_end + 80, -L.H["open_deg"]), (swap_end + 115, 0)):
    hp.rotation_euler = (math.radians(ang), 0, 0)
    hp.keyframe_insert("rotation_euler", frame=fr)
for o in bpy.data.objects:
    if o.animation_data and o.animation_data.action:
        for fc in getattr(o.animation_data.action, "fcurves", []):
            for kp in fc.keyframe_points:
                kp.interpolation = "BEZIER"
sc.frame_start, sc.frame_end = 1, swap_end + 125
print("ANIM_MARKS=%s swap_end=%d hatch=%d..%d" % (marks, swap_end, swap_end + 10, swap_end + 115))

if os.environ.get("ANIM_PREVIEW", "1") == "1":
    L.CAMS["swap"] = ((2.4, 2.6, 1.0), (0.75, 0.85, 0.22), 35)
    L.CAMS["lock"] = ((0.60, 0.25, 0.30), (0.80, 0.74, 0.42), 26)
    run_label = os.environ.get("BLENDER_LOOP_STEP", "S6")
    probes = [("cage_tilted", marks["CAGE_out"] + 32), ("cage_out", marks["CAGE_out"] + 64),
              ("toolbox_ledge", marks["TOOLBOX_in"] + 44), ("toolbox_locked", marks["TOOLBOX_in"] + 66),
              ("hatch_open", swap_end + 60)]
    for name, fr in probes:
        sc.frame_set(fr)
        views = ("rl3q",) if name == "hatch_open" else ("swap", "lock")
        L.look(views, res=(640, 400), label=f"{run_label}_{name}")
