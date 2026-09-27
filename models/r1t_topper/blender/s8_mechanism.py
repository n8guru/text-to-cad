"""S8: hardware-only mechanism close-ups, imported straight from the Step 27 build123d CAD.

In-context stills cannot read a 77 x 19 x 35 mm latch buried against black carbon, so this is the
standard design-package view: one socket's hardware and its mating module hardware, alone, lit,
on a neutral ground. Nothing here is modelled in Blender — every object is an STL exported from
``cad/assembly_step27.py``.

``STEP27_STATE=open`` loads the released set (fork bolts rotated 58 deg, module lifted 160 mm off
the land, handle pulled) so shut and released can be compared frame to frame.
``MECH_CUTAWAY=1`` ghosts the latch housings to expose the fork bolt and pawl.
"""
import os
import sys

sys.path.insert(0, "/home/n8/text-to-cad-worktrees/r1t-opus-pass/models/r1t_topper/blender")
import bpy
from mathutils import Vector
import r1t_lib as L

STEP27 = "/home/n8/text-to-cad-worktrees/r1t-opus-pass/models/r1t_topper/step27"
STATE = os.environ.get("STEP27_STATE", "closed")
CUTAWAY = os.environ.get("MECH_CUTAWAY", "0") == "1"
PARTS = os.path.join(STEP27, "out", "parts" if STATE == "closed" else "parts_open")
KEEP = ("L1_",)                       # one socket + its module hardware is the whole story
# MECH_SUBSET=train isolates the latch train itself. The socket frame and the module plug frame are
# 800 x 500 mm panels; at close-up distance one of them fills the frame whichever side you shoot
# from, which is why the first two attempts photographed a flat sheet instead of a latch.
SUBSET = os.environ.get("MECH_SUBSET", "all")
TRAIN = ("LATCH_", "STRIKER_", "RELEASE_CABLE", "SPLITTER", "LOCATING_PIN", "BUSHING",
         "BALL_PLUNGER", "COMPRESSION_LIMITER")
# ONE station only. There are two latches per socket and they sit 500 mm apart, so even the
# "train" subset frames a half-metre box around a 77 mm part.
ONE = ("L1_LATCH_fork_bolt", "L1_LATCH_pawl", "L1_LATCH_latch_housing",
       "L1_MOD_STRIKER_BOLT_R4-90-321-20.", "L1_MOD_STRIKER_BRACKET_custom.",
       "L1_RELEASE_CABLE_AC.")
C = "60_MECHANISM"
MM = 0.001
m = L.M()

LOOK = [
    ("fork_bolt", "orange"), ("pawl", "rim"), ("latch_housing", "ss"),
    ("STRIKER_BOLT", "ss"), ("STRIKER_BRACKET", "alu"),
    ("J_HOOK", "ss"), ("BALL_PLUNGER", "ss"), ("BUSHING", "rim"),
    ("LOCATING_PIN", "rim"), ("BULB_SEAL", "epdm"), ("RELEASE_CABLE", "trim"),
    ("SPLITTER", "black"), ("handle_paddle", "orange"), ("handle_pan", "black"),
    ("LIMITER", "light"), ("LEDGE", "alu_raw"), ("SOCKET_FRAME", "alu"),
    ("MODULE_PLUG_FRAME", "alu"),
]


def look_for(name):
    for frag, key in LOOK:
        if frag.lower() in name.lower():
            return m[key]
    return m["alu"]


def studio():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.mesh.primitive_plane_add(size=6, location=(0.8, 0.6, 0.05))
    L.assign(bpy.context.object, m["ground"])
    for loc, e, sz in (((0.2, 0.2, 1.4), 400.0, 1.2), ((1.6, 1.2, 0.9), 220.0, 0.9),
                       ((0.3, 1.6, 0.5), 160.0, 0.8)):
        lt = bpy.data.lights.new("KEY", "AREA")
        lt.energy, lt.size = e, sz
        ob = bpy.data.objects.new("KEY", lt)
        bpy.context.scene.collection.objects.link(ob)
        ob.location = loc
        ob.rotation_euler = (Vector((0.8, 0.72, 0.42)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()


def import_parts():
    n = 0
    for fn in sorted(os.listdir(PARTS)):
        if not fn.endswith(".stl") or not fn.startswith(KEEP):
            continue
        if SUBSET == "train" and not any(t in fn for t in TRAIN):
            continue
        if SUBSET == "one" and not (any(fn.startswith(t) and "_2" not in fn for t in ONE[:3])
                                    or any(fn.startswith(t[:-1]) and fn.endswith(t[-1] + "stl")
                                           for t in ONE[3:])):
            continue
        if CUTAWAY and "latch_housing" in fn:
            continue
        before = set(bpy.data.objects)
        try:
            bpy.ops.wm.stl_import(filepath=os.path.join(PARTS, fn), global_scale=MM)
        except AttributeError:
            bpy.ops.import_mesh.stl(filepath=os.path.join(PARTS, fn), global_scale=MM)
        for o in set(bpy.data.objects) - before:
            o.name = fn[:-4]
            L.link(o, C)
            L.assign(o, look_for(fn))
            L.smooth(o, 28)
            n += 1
    return n


if __name__ in ("__main__", "__blender_loop_step__"):
    studio()
    n = import_parts()
    if SUBSET == "one":
        # keep exactly ONE latch station: drop the socket's second station (the "_2" instances)
        for o in list(bpy.data.objects):
            if o.name.endswith("_2") or o.name.endswith("_3"):
                bpy.data.objects.remove(o, do_unlink=True)
                n -= 1
    objs = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith(KEEP)]
    # Frame on the FOCUS parts, not on everything imported. The release cable alone is 300 mm
    # long, so framing the whole import put the camera 1.4 m from a 77 mm latch.
    focus = [o for o in objs if any(k in o.name for k in ("fork_bolt", "STRIKER_BOLT", "pawl",
                                                          "latch_housing"))]
    if focus:
        objs = focus
    mn = Vector((1e9, 1e9, 1e9))
    mx = Vector((-1e9, -1e9, -1e9))
    for o in objs:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            mn = Vector((min(mn[i], w[i]) for i in range(3)))
            mx = Vector((max(mx[i], w[i]) for i in range(3)))
    ctr = (mn + mx) / 2
    diag = (mx - mn).length
    # auto-frame off the ACTUAL imported bbox instead of hand-guessed coordinates
    def cam(dirv, k=1.25, lens=50):
        d = Vector(dirv).normalized()
        return (tuple(ctr + d * (diag * k)), tuple(ctr), lens)
    L.CAMS["mech3q"] = cam((-0.9, -1.0, 0.55), 2.1, 50)
    L.CAMS["latch3q"] = cam((-0.5, -1.0, 0.35), 1.8, 55)
    L.CAMS["latchtop"] = cam((0.1, -0.35, 1.0), 1.9, 50)
    L.CAMS["latchout"] = cam((-0.3, 1.0, 0.30), 1.8, 55)
    L.look(("mech3q", "latch3q", "latchtop", "latchout"), res=(1200, 820))
    print("SCORE state=%s subset=%s cutaway=%d parts=%d focus=%d bbox=%.3fx%.3fx%.3f diag=%.3f"
          % (STATE, SUBSET, CUTAWAY, n, len(objs), mx.x - mn.x, mx.y - mn.y, mx.z - mn.z, diag))
    print("OBJECTS=" + ",".join(sorted(o.name for o in bpy.data.objects
                                       if o.type == "MESH" and o.name.startswith(KEEP))))
