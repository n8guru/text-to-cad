"""R1T topper: shared Blender helpers for the Step 27 render lane.

Metres. X rearward, Y driver(+), Z up; origin = centreline at the bed's inside front wall, z = 0 on
the bed-rail top. Nothing here models product geometry: the topper is IMPORTED from the build123d
STLs (step27/out/parts), and the truck is built from the Rivian-measured reference
(step27/style/rivian_reference.json). All paths resolve from this file; the only environment
inputs are optional:

  R1T_HDRI         an equirect .hdr for lighting (falls back to a procedural sky)
  BLENDER_LOOP_*   set by the blender-loop CLI
"""
import json
import math
import os
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent
MODEL = HERE.parent
STEP27 = MODEL / "step27"
P = json.loads((HERE / "params.json").read_text())
T, S, K, H = P["truck"], P["shell"], P["socket"], P["hatch"]
REF = json.loads((STEP27 / "style" / "rivian_reference.json").read_text())
KIN_PATH = STEP27 / "out" / "kinematics.json"
PARTS = STEP27 / "out" / "parts"
MM = 0.001


# ------------------------------------------------------------------ scene / collections
def clear_scene():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for b in list(coll):
            if b.users == 0:
                coll.remove(b)


def coll(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c


def link(obj, cname):
    for c in obj.users_collection:
        c.objects.unlink(obj)
    coll(cname).objects.link(obj)
    return obj


# ------------------------------------------------------------------ materials
def mat(name, rgb, metal=0.0, rough=0.4, coat=0.0, emit=0.0, trans=0.0, alpha=1.0):
    """Get-or-create, and ALWAYS (re)apply the parameters: a saved scene keeps old materials by
    name, so a create-only helper silently ignores every look change."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Transmission Weight"].default_value = trans
    if trans:
        b.inputs["IOR"].default_value = 1.52
    b.inputs["Emission Strength"].default_value = emit
    if emit:
        b.inputs["Emission Color"].default_value = (*rgb, 1)
    b.inputs["Alpha"].default_value = alpha
    return m


def carbon_mat():
    m = mat("CARBON_2x2_TWILL", (0.008, 0.008, 0.009), rough=0.42, coat=0.65)
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Coat Roughness"].default_value = 0.06
    ck = nt.nodes.get("TWILL") or nt.nodes.new("ShaderNodeTexChecker")
    if ck.name != "TWILL":
        ck.name = "TWILL"
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Rotation"].default_value = (0, 0, math.radians(45))
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.06
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], ck.inputs["Vector"])
        nt.links.new(ck.outputs["Color"], b.inputs["Base Color"])
        nt.links.new(ck.outputs["Fac"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    ck.inputs["Scale"].default_value = 160.0
    ck.inputs["Color1"].default_value = (0.006, 0.006, 0.007, 1)
    ck.inputs["Color2"].default_value = (0.03, 0.03, 0.034, 1)
    return m


def M():
    return {
        "paint": mat("PAINT_LAUNCH_GREEN", (0.11, 0.16, 0.10), metal=0.55, rough=0.3, coat=1.0),
        "black": mat("BLACK_GLOSS", (0.01, 0.01, 0.012), rough=0.15, coat=1.0),
        "trim": mat("BLACK_TRIM", (0.025, 0.025, 0.025), rough=0.6),
        "glass": mat("GLASS_TINT", (0.008, 0.01, 0.012), rough=0.03, coat=0.5),
        "tire": mat("TIRE", (0.018, 0.018, 0.018), rough=0.85),
        "rim": mat("RIM", (0.12, 0.12, 0.13), metal=1.0, rough=0.35),
        "light": mat("LIGHT_WHITE", (1.0, 0.95, 0.9), emit=3.0),
        "tail": mat("LIGHT_RED", (1.0, 0.04, 0.02), emit=2.5),
        "alu": mat("ALU_BLACK_ANODIZE", (0.035, 0.035, 0.04), metal=1.0, rough=0.35),
        "alu_raw": mat("ALU_6061_CLEAR", (0.72, 0.73, 0.75), metal=1.0, rough=0.28),
        "ss": mat("SS316", (0.72, 0.72, 0.74), metal=1.0, rough=0.2),
        "epdm": mat("EPDM", (0.02, 0.02, 0.02), rough=0.9),
        "orange": mat("KEY_ORANGE", (0.9, 0.32, 0.03), rough=0.4),
        "carbon": carbon_mat(),
        "ground": mat("GROUND", (0.34, 0.33, 0.32), rough=0.85),
        "uhmw": mat("UHMW", (0.9, 0.9, 0.86), rough=0.6),
    }


def assign(obj, m):
    obj.data.materials.clear()
    obj.data.materials.append(m)
    return obj


def smooth(o, angle=35):
    for p in o.data.polygons:
        p.use_smooth = True
    try:
        o.data.set_sharp_from_angle(angle=math.radians(angle))
    except Exception:
        pass


# ------------------------------------------------------------------ CAD import
LOOK = [
    ("SHELL_CARBON", "carbon"), ("HATCH_LEAF_CARBON", "carbon"), ("TOOLBOX_DOOR", "carbon"),
    ("GLAZING_PANE", "glass"), ("WINDOW_PANE", "glass"), ("FRONT_PASS_THROUGH", "glass"),
    ("fork_bolt", "orange"), ("pawl", "ss"), ("latch_housing", "ss"), ("STRIKER_BOLT", "ss"),
    ("J_HOOK", "ss"), ("CAGE_BAR", "ss"), ("CAGE_RAIL", "ss"), ("BALL_PLUNGER", "ss"),
    ("BUSHING", "rim"), ("LOCATING_PIN", "rim"), ("BULB_SEAL", "epdm"), ("RELEASE_CABLE", "trim"),
    ("SPLITTER", "black"), ("handle_paddle", "orange"), ("handle_pan", "black"),
    ("COMPRESSION_LIMITER", "uhmw"), ("CHMSL", "tail"), ("T_HANDLE", "black"),
    ("GAS_STRUT", "black"), ("BALL_STUD", "ss"), ("TOOLBOX_TUB", "trim"),
    ("PORT_ADAPTER", "alu_raw"), ("PORT_SPACER", "alu_raw"), ("PORT_STUD", "ss"),
    ("PORT_NUT", "ss"), ("WEDGE_WASHER", "ss"), ("PORT_SLOT_WASHER", "ss"), ("PORT_SHIM", "ss"),
    ("FOOT_PAD", "epdm"), ("ROOF_HARDPOINT", "alu"), ("HATCH_DRAIN", "trim"),
]


def look_for(name, m):
    for frag, key in LOOK:
        if frag.lower() in name.lower():
            return m[key]
    return m["alu"]


def import_stl(path, name, cname, material=None):
    before = set(bpy.data.objects)
    bpy.ops.wm.stl_import(filepath=str(path), global_scale=MM)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        o.name = name
        link(o, cname)
        if material is not None:
            assign(o, material)
        smooth(o, 30)
    return new[0] if new else None


def import_parts(parts_dir=None, cname="10_TOPPER_CAD", select=None):
    """Import every CAD STL (vehicle coordinates, mm -> m). Returns {name: object}."""
    parts_dir = Path(parts_dir or PARTS)
    m = M()
    out = {}
    for f in sorted(parts_dir.glob("*.stl")):
        if select and not select(f.stem):
            continue
        o = import_stl(f, f.stem, cname, look_for(f.stem, m))
        if o is not None:
            out[f.stem] = o
    return out


# ------------------------------------------------------------------ world / cameras / look
def setup_world(strength=1.0):
    sc = bpy.context.scene
    w = sc.world or bpy.data.worlds.new("W")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    hdri = os.environ.get("R1T_HDRI", "")
    if hdri and os.path.exists(hdri):
        env = nt.nodes.get("Environment Texture") or nt.nodes.new("ShaderNodeTexEnvironment")
        env.image = bpy.data.images.load(hdri, check_existing=True)
        nt.links.new(env.outputs["Color"], bg.inputs["Color"])
    else:
        sky = nt.nodes.get("Sky Texture") or nt.nodes.new("ShaderNodeTexSky")
        try:
            sky.sky_type = "NISHITA"
            sky.sun_elevation = math.radians(35)
            sky.sun_rotation = math.radians(210)
        except Exception:
            pass
        nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength


def camera(name, loc, target, lens):
    cam = bpy.data.objects.get(name)
    if cam is None:
        cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
        bpy.context.scene.collection.objects.link(cam)
    cam.data.lens = lens
    cam.data.clip_start = 0.01
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return cam


def run_dir():
    return Path(os.environ.get("BLENDER_LOOP_RUN_DIR", "/tmp/r1t_look"))


def look(views, res=(1280, 800), label=None, engine="BLENDER_EEVEE", samples=None):
    """Render named views -> <run>/stills/<label>_<view>.png. ``views``: {name: (loc, tgt, lens)}."""
    sc = bpy.context.scene
    label = label or os.environ.get("BLENDER_LOOP_STEP", "look")
    (run_dir() / "stills").mkdir(parents=True, exist_ok=True)
    setup_world()
    sc.render.engine = engine
    if engine == "CYCLES":
        sc.cycles.samples = samples or 96
        sc.cycles.use_denoising = True
        try:
            if os.environ.get("R1T_CYCLES_DEVICE", "GPU").upper() == "CPU":   # GPU busy elsewhere
                raise RuntimeError("CPU requested")
            prefs = bpy.context.preferences.addons["cycles"].preferences
            prefs.compute_device_type = "OPTIX"
            prefs.get_devices()
            for d in prefs.devices:
                d.use = True
            sc.cycles.device = "GPU"
        except Exception:
            sc.cycles.device = "CPU"
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.view_settings.view_transform = "AgX"
    out = []
    for v, (loc, tgt, lens) in views.items():
        sc.camera = camera("CAM_" + v, loc, tgt, lens)
        sc.render.filepath = str(run_dir() / "stills" / f"{label}_{v}.png")
        bpy.ops.render.render(write_still=True)
        out.append(sc.render.filepath)
    print("LOOK_STILLS=" + json.dumps(out), flush=True)
    return out


def bbox(o):
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return [min(p[i] for p in pts) for i in range(3)], [max(p[i] for p in pts) for i in range(3)]


def world_bbox(objs):
    mn, mx = [1e9] * 3, [-1e9] * 3
    for o in objs:
        a, b = bbox(o)
        mn = [min(mn[i], a[i]) for i in range(3)]
        mx = [max(mx[i], b[i]) for i in range(3)]
    return mn, mx


def world_bvh(objs_):
    """BVH of evaluated meshes in WORLD space (imported STLs carry their 0.001 scale on the
    object, so BVHTree.FromObject would answer in millimetres of local space)."""
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()
    verts, polys, off = [], [], 0
    for o in objs_:
        me = o.evaluated_get(dg).to_mesh()
        mw = o.matrix_world
        verts += [mw @ v.co for v in me.vertices]
        polys += [[off + i for i in p.vertices] for p in me.polygons]
        off += len(me.vertices)
        o.evaluated_get(dg).to_mesh_clear()
    return BVHTree.FromPolygons(verts, polys) if polys else None


# ------------------------------------------------------------------ blender-loop score hook
def report_scores(scores: dict):
    """Put this step's numeric scores into the blender-loop ledger so ``--assert`` can use them.

    The CLI's runtime only scores armature poses; it calls runtime.after_step() after this script.
    Wrapping that function (same module object the driver imports) adds our scores to the step
    entry before the CLI reads it back.
    """
    try:
        import runtime as rt
    except ImportError:
        print("SCORES=" + json.dumps(scores), flush=True)
        return
    orig = rt.after_step

    def after():
        entry = orig()
        entry["scores"] = dict(scores, kind="r1t_cad")
        rd = Path(os.environ["BLENDER_LOOP_RUN_DIR"])
        (rd / f"step_{rt.STEP_LABEL}.json").write_text(json.dumps(entry, indent=2, default=float))
        lp = rd / "ledger.json"
        led = json.loads(lp.read_text())
        for s in led["steps"]:
            if s.get("step") == rt.STEP_LABEL:
                s["scores"] = entry["scores"]
        lp.write_text(json.dumps(led, indent=2, default=float))
        return entry

    rt.after_step = after
    print("SCORES=" + json.dumps(scores, default=float), flush=True)
