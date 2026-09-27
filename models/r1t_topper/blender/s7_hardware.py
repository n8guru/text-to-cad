"""S7: import the Step 27 CAD hardware into the topper scene, replacing the placeholder blocks.

This is the fix for the rejection "the latch is only meaningless white square chunks". Blender no
longer MODELS any latch. It imports ``step27/out/parts/*.stl``, which are exported from the
build123d assembly in vehicle coordinates and millimetres, so a still cannot show geometry the
authoritative CAD does not contain.

``STEP27_STATE=open`` imports the open-state part set (fork bolts rotated to release, hatch at
95 deg, one module lifted off) instead.
"""
import math
import os
import sys

sys.path.insert(0, "/home/n8/text-to-cad-worktrees/r1t-opus-pass/models/r1t_topper/blender")
import bpy
import r1t_lib as L

STEP27 = "/home/n8/text-to-cad-worktrees/r1t-opus-pass/models/r1t_topper/step27"
STATE = os.environ.get("STEP27_STATE", "closed")
PARTS = os.path.join(STEP27, "out", "parts" if STATE == "closed" else "parts_open")
C = "50_STEP27_HARDWARE"
MM = 0.001
m = L.M()

# material by name fragment -> the same look the rest of the topper uses
LOOK = [
    ("FORK_BOLT", "orange"), ("fork_bolt", "orange"),
    ("PAWL", "ss"), ("pawl", "ss"),
    ("LATCH", "ss"), ("STRIKER", "ss"), ("J_HOOK", "ss"), ("BALL", "ss"),
    ("PIN", "ss"), ("BUSHING", "ss"), ("CHMSL", "tail"),
    ("SEAL", "epdm"), ("CABLE", "trim"), ("CLOSEOUT", "trim"),
    ("GLAZING_PANE", "glass"), ("CARBON", "carbon"),
    ("LIMITER", "trim"), ("HANDLE", "orange"), ("SPLITTER", "black"),
    ("STRUT", "black"), ("HINGE", "alu"), ("GUTTER", "alu"), ("DRAIN", "alu"),
]


def look_for(name):
    for frag, key in LOOK:
        if frag.lower() in name.lower():
            return m[key]
    return m["alu"]


PLACEHOLDER = ("LATCH_", "RELEASE_", "SOCKET_", "HATCH_STRIKER", "HATCH_LATCH",
               "HATCH_HINGE", "HATCH_SURROUND", "HATCH_SEAL", "STRUT_", "HW_")


def wipe():
    """Delete every S3/S5 placeholder. The imported CAD is now the only hardware in the scene."""
    n = 0
    for o in list(bpy.data.objects):
        if o.name.startswith(PLACEHOLDER):
            bpy.data.objects.remove(o, do_unlink=True)
            n += 1
    return n


def hide_for_closeup(hide=True):
    """Hide the module payloads and the far side so the mechanism is actually visible.

    The socket hardware sits on the INBOARD face of the shell, so the camera has to be inside the
    topper; the cage grille and toolbox tub would otherwise fill the frame.
    """
    for o in bpy.data.objects:
        nm = o.name.upper()
        far = "_R0" in nm or "_R1" in nm or nm.startswith(("R0_", "R1_"))
        payload = any(k in nm for k in ("CAGE", "TOOLBOX", "MESH", "BAR_"))
        if payload or far:
            o.hide_render = hide


def import_parts():
    n = 0
    for fn in sorted(os.listdir(PARTS)):
        if not fn.endswith(".stl"):
            continue
        before = set(bpy.data.objects)
        try:
            bpy.ops.wm.stl_import(filepath=os.path.join(PARTS, fn), global_scale=MM)
        except AttributeError:                       # Blender < 4.2 operator name
            bpy.ops.import_mesh.stl(filepath=os.path.join(PARTS, fn), global_scale=MM)
        for o in set(bpy.data.objects) - before:
            o.name = "HW_" + fn[:-4]
            L.link(o, C)
            L.assign(o, look_for(fn))
            L.smooth(o, 28)
            n += 1
    return n


if __name__ in ("__main__", "__blender_loop_step__"):
    removed = wipe()
    n = import_parts()
    # Mechanism cameras live INSIDE the topper: the latch flange is on the inboard face of the
    # shell at n = -60 mm, so any camera outboard of the skin is looking at the wrong side.
    # Socket L1 latch station, in vehicle metres, derived from geom.socket_plane("L", 1):
    #   u = +250 -> x = 0.80 ; v = 190, n = -60 -> y = 0.756, z = 0.445
    # Hatch latch station, from geom.hatch_plane(): (1.363, 0.450, 0.041)
    L.CAMS["latchcam"] = ((0.80, 0.16, 0.26), (0.80, 0.756, 0.445), 45)
    L.CAMS["strikercam"] = ((0.66, 0.46, 0.35), (0.81, 0.757, 0.443), 85)
    L.CAMS["hatchcam"] = ((0.95, 0.30, 0.34), (1.363, 0.450, 0.041), 42)
    # interior fill: the mechanism lives inside a closed carbon box, so the HDRI alone leaves it
    # black. This is a light, not geometry.
    for nm, loc, e in (("FILL_SOCK", (0.6, 0.0, 0.30), 120.0), ("FILL_HATCH", (1.05, 0.0, 0.30), 90.0)):
        if nm not in bpy.data.objects:
            lt = bpy.data.lights.new(nm, "AREA")
            lt.energy, lt.size = e, 0.45
            ob = bpy.data.objects.new(nm, lt)
            bpy.context.scene.collection.objects.link(ob)
            ob.location = loc
    hide_for_closeup(True)
    L.look(("latchcam", "strikercam", "hatchcam"), res=(1100, 760))
    # cutaway: ghost the latch housings so the fork bolt, pawl and striker bolt are actually
    # visible. A closed housing photographs as a black block, which is the complaint we are fixing.
    for o in bpy.data.objects:
        if "latch_housing" in o.name.lower():
            o.hide_render = True
    L.look(("latchcam", "strikercam"), res=(1100, 760),
           label=(os.environ.get("BLENDER_LOOP_STEP", "S7") + "_CUTAWAY"))
    for o in bpy.data.objects:
        if "latch_housing" in o.name.lower():
            o.hide_render = False
    hide_for_closeup(False)
    objs = [o for o in bpy.data.objects if o.name.startswith("HW_")]
    tris = sum(len(o.data.polygons) for o in objs if o.type == "MESH")
    print("SCORE state=%s placeholders_removed=%d imported=%d objects=%d faces=%d boxes=%d"
          % (STATE, removed, n, len(objs), tris,
             sum(1 for o in objs if o.type == "MESH" and len(o.data.polygons) <= 6)))
