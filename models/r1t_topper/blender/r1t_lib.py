"""R1T topper opus-pass: shared Blender helpers (geometry, materials, look/render).

Metres. X rearward, Y driver(+), Z up; origin = centreline, forward edge of bed-rail top plane.
Every builder reads params.json so a measurement update is one edit + rebuild.
"""
import json
import math
import os
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent
P = json.loads((HERE / "params.json").read_text())
T, S, K, H = P["truck"], P["shell"], P["socket"], P["hatch"]
KEY = P["keying"]


# ---------- collections / materials ----------
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


def mat(name, rgb, metal=0.0, rough=0.4, coat=0.0, emit=0.0, alpha=1.0, trans=0.0):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = coat
    if trans:
        b.inputs["Transmission Weight"].default_value = trans
        b.inputs["IOR"].default_value = 1.52
    if emit:
        b.inputs["Emission Color"].default_value = (*rgb, 1)
        b.inputs["Emission Strength"].default_value = emit
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
    return m


def carbon_mat():
    """2x2 twill look: fine checker drives colour + bump; glossy clear coat."""
    m = bpy.data.materials.get("CARBON_2x2_TWILL")
    if m:
        return m
    m = mat("CARBON_2x2_TWILL", (0.018, 0.018, 0.02), metal=0.0, rough=0.32, coat=1.0)
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value = (0, 0, math.radians(45))
    ck = nt.nodes.new("ShaderNodeTexChecker")
    ck.inputs["Scale"].default_value = 180.0
    ck.inputs["Color1"].default_value = (0.012, 0.012, 0.014, 1)
    ck.inputs["Color2"].default_value = (0.045, 0.045, 0.05, 1)
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.08
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], ck.inputs["Vector"])
    nt.links.new(ck.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(ck.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def M():
    return {
        "paint": mat("PAINT_LAUNCH_GREEN", (0.10, 0.14, 0.09), metal=0.6, rough=0.28, coat=1.0),
        "black": mat("BLACK_GLOSS", (0.01, 0.01, 0.012), rough=0.15, coat=1.0),
        "trim": mat("BLACK_TRIM", (0.02, 0.02, 0.02), rough=0.6),
        "glass": mat("GLASS_TINT", (0.03, 0.035, 0.04), rough=0.03, coat=1.0),
        "tire": mat("TIRE", (0.015, 0.015, 0.015), rough=0.85),
        "rim": mat("RIM", (0.35, 0.36, 0.37), metal=1.0, rough=0.3),
        "light": mat("LIGHT_WHITE", (1.0, 0.95, 0.9), emit=4.0),
        "tail": mat("LIGHT_RED", (1.0, 0.03, 0.02), emit=3.0),
        "alu": mat("ALU_BLACK_ANODIZE", (0.03, 0.03, 0.035), metal=1.0, rough=0.35),
        "alu_raw": mat("ALU_6061_CLEAR", (0.75, 0.76, 0.78), metal=1.0, rough=0.25),
        "ss": mat("SS316", (0.7, 0.7, 0.72), metal=1.0, rough=0.18),
        "epdm": mat("EPDM", (0.02, 0.02, 0.02), rough=0.9),
        "orange": mat("KEY_ORANGE", (0.9, 0.3, 0.02), rough=0.4),
        "carbon": carbon_mat(),
        "ground": mat("GROUND_CONCRETE", (0.32, 0.31, 0.3), rough=0.8),
    }


def assign(obj, m):
    obj.data.materials.clear()
    obj.data.materials.append(m)
    return obj


# ---------- mesh builders ----------
def mesh_obj(name, verts, faces, cname=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.validate()
    me.update()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    if cname:
        link(o, cname)
    return o


def rrect(w, h, r, n=8):
    """Rounded rectangle, centred, CCW, (u,v) pairs."""
    r = min(r, w / 2 - 1e-4, h / 2 - 1e-4)
    pts = []
    for cx, cy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90),
                       (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def prism(name, pts, d0, d1, mw=None, cname=None):
    """Extrude 2D (u,v) loop along local n from d0 to d1; mw = frame matrix."""
    n = len(pts)
    verts = [(u, v, d0) for u, v in pts] + [(u, v, d1) for u, v in pts]
    faces = [list(range(n))[::-1], list(range(n, 2 * n))]
    faces += [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
    o = mesh_obj(name, verts, faces, cname)
    if mw is not None:
        o.matrix_world = mw
    return o


def ring(name, outer, inner, d0, d1, mw=None, cname=None):
    """Planar frame (outer loop minus inner loop, same point count) extruded d0..d1."""
    n = len(outer)
    assert n == len(inner)
    V = []
    for d in (d0, d1):
        V += [(u, v, d) for u, v in outer] + [(u, v, d) for u, v in inner]
    F = []
    for i in range(n):
        j = (i + 1) % n
        o0, i0, o1, i1 = 0, n, 2 * n, 3 * n
        F.append([o1 + i, o1 + j, i1 + j, i1 + i])      # top face
        F.append([o0 + j, o0 + i, i0 + i, i0 + j])      # bottom face
        F.append([o0 + i, o0 + j, o1 + j, o1 + i])      # outer wall
        F.append([i0 + j, i0 + i, i1 + i, i1 + j])      # inner wall
    o = mesh_obj(name, V, F, cname)
    if mw is not None:
        o.matrix_world = mw
    return o


def box(name, c, size, cname=None, mw=None):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0] + c[0], v.co.y * size[1] + c[1], v.co.z * size[2] + c[2]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    if cname:
        link(o, cname)
    if mw is not None:
        o.matrix_world = mw
    return o


def cyl(name, r, depth, loc, rot=(0, 0, 0), verts=48, cname=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=r, radius2=r, depth=depth)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = rot
    if cname:
        link(o, cname)
    return o


def extrude_profile_y(name, xz, half_w, cname=None):
    """Side profile polygon in (x,z) extruded symmetric in Y."""
    n = len(xz)
    V = [(x, -half_w, z) for x, z in xz] + [(x, half_w, z) for x, z in xz]
    F = [list(range(n)), list(range(n, 2 * n))[::-1]]
    F += [[(i + 1) % n, i, n + i, n + (i + 1) % n] for i in range(n)]
    o = mesh_obj(name, V, F, cname)
    fix_normals(o)
    return o


def fix_normals(o):
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(o.data)
    bm.free()


def bevel(o, w, seg=4, angle=30):
    m = o.modifiers.new("bevel", "BEVEL")
    m.width, m.segments, m.limit_method = w, seg, "ANGLE"
    m.angle_limit = math.radians(angle)
    m.harden_normals = False
    return m


def boolean(target, cutter, op="DIFFERENCE", apply=True):
    m = target.modifiers.new("bool_" + cutter.name, "BOOLEAN")
    m.operation, m.object, m.solver = op, cutter, "EXACT"
    if apply:
        bpy.context.view_layer.objects.active = target
        bpy.ops.object.modifier_apply(modifier=m.name)
        bpy.data.objects.remove(cutter, do_unlink=True)
    return m


def apply_mods(o):
    bpy.context.view_layer.objects.active = o
    for m in list(o.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)


def smooth(o, angle=35):
    for p in o.data.polygons:
        p.use_smooth = True
    try:
        o.data.set_sharp_from_angle(angle=math.radians(angle))
    except Exception:
        pass


def empty(name, mw=None, parent=None, cname=None):
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = 0.05
    bpy.context.scene.collection.objects.link(e)
    if cname:
        link(e, cname)
    if parent:
        e.parent = parent
    if mw is not None:
        e.matrix_world = mw
    return e


def parent_keep(child, parent):
    mw = child.matrix_world.copy()
    child.parent = parent
    child.matrix_parent_inverse = parent.matrix_world.inverted()
    child.matrix_world = mw


# ---------- shell math ----------
def lean():
    return math.atan2(S["base_half_w"] - S["land_half_w"], S["land_top_z"])


def roof_z(x):
    t = (x - S["x0"]) / (S["x1"] - S["x0"])
    return S["roof_z_front"] + (S["roof_z_rear"] - S["roof_z_front"]) * t


def land_y(z):
    return S["base_half_w"] - z * math.tan(lean())


def socket_frame(side, i):
    """Matrix for socket (side 'L'|'R', index i): origin on outer land plane at opening centre.
    Local axes: u along shell, v up the lean, n outward normal (u x v = n); identical module geometry
    fits every socket because L uses u=-X and R uses u=+X (rotation, not mirror)."""
    a = lean()
    s, c = math.sin(a), math.cos(a)
    zc = (K["z_bot"] + K["z_top"]) / 2
    x = K["centers_x"][i]
    if side == "L":
        u, v, n, o = Vector((-1, 0, 0)), Vector((0, -s, c)), Vector((0, c, s)), Vector((x, land_y(zc), zc))
    else:
        u, v, n, o = Vector((1, 0, 0)), Vector((0, s, c)), Vector((0, -c, s)), Vector((x, -land_y(zc), zc))
    m = Matrix.Identity(4)
    for r in range(3):
        m[r][0], m[r][1], m[r][2], m[r][3] = u[r], v[r], n[r], o[r]
    return m


def opening_hw():
    """Opening (w, h) measured in the socket plane."""
    return K["width"], (K["z_top"] - K["z_bot"]) / math.cos(lean())


# ---------- look (blender-loop stills) ----------
CAMS = {
    "fl3q": ((-6.4, 6.6, 1.0), (-1.0, 0.0, -0.3), 32),
    "rl3q": ((5.0, 5.2, 1.4), (-0.3, 0.0, -0.2), 32),
    "side": ((-1.2, 9.5, 0.0), (-1.2, 0.0, -0.3), 35),
    "top": ((0.3, 0.0, 7.0), (0.3, 0.0, 0.0), 35),
    "rear": ((6.0, 0.0, 0.6), (0.9, 0.0, 0.0), 40),
    "sockL": ((2.0, 2.6, 0.9), (0.45, 0.8, 0.25), 40),
    "inside": ((0.80, -0.45, 0.36), (0.80, 0.78, 0.25), 22),
    "topper3q": ((3.0, 3.0, 1.5), (0.7, 0.0, 0.25), 40),
}


def setup_world(strength=1.0, hdri="/home/n8/forge-cut/textscene/assets/hdris/fish_hoek_beach_2k.hdr"):
    sc = bpy.context.scene
    w = sc.world or bpy.data.worlds.new("W")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    env = nt.nodes.get("Environment Texture")
    if env is None and os.path.exists(hdri):
        env = nt.nodes.new("ShaderNodeTexEnvironment")
        nt.links.new(env.outputs["Color"], nt.nodes["Background"].inputs["Color"])
    if env is not None:                       # absolute path: blends get copied to evidence dirs
        env.image = bpy.data.images.load(hdri, check_existing=True)
        env.image.filepath = hdri
    nt.nodes["Background"].inputs["Strength"].default_value = strength


def camera(name, loc, target, lens):
    cam = bpy.data.objects.get(name)
    if cam is None:
        cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
        bpy.context.scene.collection.objects.link(cam)
    cam.data.lens = lens
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return cam


def look(views=("fl3q", "rl3q", "side"), res=(800, 500), label=None, engine="BLENDER_EEVEE"):
    sc = bpy.context.scene
    label = label or os.environ.get("BLENDER_LOOP_STEP", "look")
    run = Path(os.environ.get("BLENDER_LOOP_RUN_DIR", "/tmp/r1t_look"))
    (run / "stills").mkdir(parents=True, exist_ok=True)
    setup_world()
    sc.render.engine = engine
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.view_settings.view_transform = "AgX"
    out = []
    for v in views:
        loc, tgt, lens = CAMS[v]
        sc.camera = camera("CAM_" + v, loc, tgt, lens)
        sc.render.filepath = str(run / "stills" / f"{label}_{v}.png")
        bpy.ops.render.render(write_still=True)
        out.append(sc.render.filepath)
    print("LOOK_STILLS=" + json.dumps(out), flush=True)
    return out


def bbox(o):
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return [min(p[i] for p in pts) for i in range(3)], [max(p[i] for p in pts) for i in range(3)]
