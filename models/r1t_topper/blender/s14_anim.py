"""S14: CAD-driven mechanism animation on the S12 scene (truck + imported CAD topper).

Sequence (24 fps): L1 release (handle pull -> rotors -26.5 deg, pawls lift) -> slide out to the
safety catch -> lift off the fin -> withdraw -> swap the CAGE payload for the TOOLBOX -> hang on
the fin -> slide home -> rotors click -> handle returns; then the hatch unlatches, opens to 95 deg
and closes. Every pivot, axis and travel is read from step27/out/kinematics.json (exported by the
build123d assembly), and the two gas struts telescope as their CAD body + rod solids.

``ANIM_KEYS=1`` (default) renders the key poses as stills and scores them against the CAD numbers.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r1t_lib as L  # noqa: E402

KIN = json.loads(L.KIN_PATH.read_text())
HWJ = json.loads((L.STEP27 / "hardware.json").read_text())
MM = 0.001
sc = bpy.context.scene
sc.render.fps = 24
V = lambda a: Vector(a) * MM              # noqa: E731


def objs(pred):
    return [o for o in bpy.data.objects if o.type == "MESH" and pred(o.name)]


def pivot(name, loc, children):
    e = bpy.data.objects.get(name) or bpy.data.objects.new(name, None)
    if e.name not in sc.collection.objects:
        sc.collection.objects.link(e)
    e.empty_display_size = 0.05
    e.location = loc
    bpy.context.view_layer.update()
    for c in children:
        mw = c.matrix_world.copy()
        c.parent = e
        c.matrix_parent_inverse = e.matrix_world.inverted()
        c.matrix_world = mw
    return e


def key_loc(e, f, loc):
    e.location = loc
    e.keyframe_insert("location", frame=f)


def key_rot(e, f, axis, deg):
    e.rotation_mode = "QUATERNION"
    from mathutils import Quaternion
    e.rotation_quaternion = Quaternion(axis, math.radians(deg))
    e.keyframe_insert("rotation_quaternion", frame=f)


def vis(os_, f, on):
    for o in os_:
        o.hide_render = o.hide_viewport = not on
        o.keyframe_insert("hide_render", frame=f)
        o.keyframe_insert("hide_viewport", frame=f)


# ------------------------------------------------------------------ L1 socket rig
k1 = KIN["sockets"]["L1"]
n, v = Vector(k1["n"]), Vector(k1["v"])
mod_objs = objs(lambda s: s.startswith("L1_MOD_"))
cage = [o for o in mod_objs if "CAGE" in o.name]
payload_dir = L.STEP27 / "out" / "parts_payloads"
m = L.M()
tool = []
for f in sorted(payload_dir.glob("*L1_TOOLBOX_*.stl")):     # PAYLOADS_L1__L1_TOOLBOX_...
    o = L.import_stl(f, "L1_MOD_SWAP_" + f.stem, "10_TOPPER_CAD", L.look_for(f.stem, m))
    tool.append(o)
home = V(k1["origin"])
mod = pivot("PIV_L1_MODULE", home, mod_objs + tool)
forks, pawls = [], []
for lt in k1["latches"]:
    sfx = "" if lt["index"] == 0 else "_2"
    fk = bpy.data.objects[f"L1_LATCH_fork_bolt-closed{sfx}"]
    pw = bpy.data.objects[f"L1_LATCH_pawl-closed{sfx}"]
    forks.append((pivot(f"PIV_L1_FORK{sfx}", V(lt["fork_pivot"]), [fk]), Vector(lt["axis"]), lt["fork_release_deg"]))
    pawls.append((pivot(f"PIV_L1_PAWL{sfx}", V(lt["pawl_pivot"]), [pw]), Vector(lt["axis"]), lt["pawl_release_deg"]))
paddle = bpy.data.objects["L1_HANDLE_handle_paddle"]
hpiv = pivot("PIV_L1_HANDLE", V(k1["handle_axis_point"]), [paddle])
h_axis, h_deg = Vector(k1["handle_axis"]), k1["handle_pull_deg"]

slide, lift = k1["removal"][0][1] * MM, k1["removal"][1][1] * MM
withdraw = k1["removal"][2][1] * MM
away = n * 0.60 + Vector((0, 0, -0.35))
P = {  # module pivot positions
    "home": home, "catch": home + n * slide, "lifted": home + n * slide + v * lift,
    "clear": home + n * withdraw + v * lift, "away": home + n * withdraw + v * lift + away}


def latch_state(f, released):
    for e, ax, d in forks:
        key_rot(e, f, ax, d if released else 0.0)
    for e, ax, d in pawls:
        key_rot(e, f, ax, d if released else 0.0)


def handle_state(f, pulled):
    key_rot(hpiv, f, h_axis, h_deg if pulled else 0.0)


F = {}
key_loc(mod, 1, P["home"]); latch_state(1, False); handle_state(1, False)
vis(tool, 1, False); vis(cage, 1, True)
handle_state(12, False); handle_state(24, True); F["pulled"] = 24
latch_state(18, False); latch_state(30, True); F["released"] = 30
key_loc(mod, 30, P["home"]); key_loc(mod, 54, P["catch"]); F["catch"] = 54
key_loc(mod, 64, P["lifted"]); F["lifted"] = 64
key_loc(mod, 100, P["clear"]); key_loc(mod, 130, P["away"]); F["away"] = 130
vis(cage, 130, True); vis(cage, 131, False); vis(tool, 130, False); vis(tool, 131, True)
key_loc(mod, 131, P["away"]); key_loc(mod, 160, P["clear"]); key_loc(mod, 196, P["lifted"])
key_loc(mod, 206, P["catch"]); F["hung"] = 206
key_loc(mod, 226, P["home"]); latch_state(226, True); latch_state(232, False); F["locked"] = 232
handle_state(232, True); handle_state(242, False)

# ------------------------------------------------------------------ hatch rig
kh = KIN["hatch"]
leaf = objs(lambda s: s.startswith("HATCH_LEAF_"))
hinge = pivot("PIV_HATCH_LEAF", V(kh["hinge_point"]), leaf)
ax_h = Vector(kh["hinge_axis"])
hforks = []
for i, lt in enumerate(kh["latches"]):
    sfx = "" if i == 0 else "_2"
    fk = bpy.data.objects[f"HATCH_LATCH_fork_bolt-closed{sfx}"]
    hforks.append((pivot(f"PIV_H_FORK{sfx}", V(lt["fork_pivot"]), [fk]), Vector(lt["axis"])))
rel = HWJ["rotary_latch"]["kinematics"]["open_deg"] - HWJ["rotary_latch"]["kinematics"]["closed_deg"]
for e, ax in hforks:
    key_rot(e, 1, ax, 0.0); key_rot(e, 252, ax, 0.0); key_rot(e, 262, ax, rel)
    key_rot(e, 366, ax, rel); key_rot(e, 372, ax, 0.0)
key_rot(hinge, 1, ax_h, 0.0); key_rot(hinge, 262, ax_h, 0.0)
key_rot(hinge, 310, ax_h, -kh["open_deg"]); F["hatch_open"] = 310
key_rot(hinge, 330, ax_h, -kh["open_deg"]); key_rot(hinge, 368, ax_h, 0.0); F["hatch_shut"] = 372

# struts: CAD body + rod re-framed on their stud axis, then tracked
bodies = sorted(objs(lambda s: "GAS_STRUT_BODY" in s), key=lambda o: o.name)
rods = sorted(objs(lambda s: "GAS_STRUT_ROD" in s), key=lambda o: o.name)
fstuds = [V(p) for p in kh["strut_frame_studs"]]
lstuds = [V(p) for p in kh["strut_leaf_studs"]]


def reframe(o, origin, z):
    z = z.normalized()
    x = z.orthogonal().normalized()
    y = z.cross(x)
    M_ = Matrix((x, y, z)).transposed().to_4x4()
    M_.translation = origin
    o.data.transform(M_.inverted())
    o.matrix_world = M_


def nearest(p, cands):
    return min(cands, key=lambda q: (q - p).length)


strut_pairs = []
for b in bodies:
    c = b.matrix_world @ (sum((Vector(vv.co) for vv in b.data.vertices), Vector()) / len(b.data.vertices))
    fs = nearest(c, fstuds)
    ls = lstuds[fstuds.index(fs)]
    rod = min(rods, key=lambda r: ((r.matrix_world @ r.data.vertices[0].co) - ls).length)
    ef = bpy.data.objects.new(f"STUD_F_{b.name[-2:]}", None); sc.collection.objects.link(ef); ef.location = fs
    el = bpy.data.objects.new(f"STUD_L_{b.name[-2:]}", None); sc.collection.objects.link(el); el.location = ls
    bpy.context.view_layer.update()
    pivot(hinge.name, hinge.location, [el])
    reframe(b, fs, ls - fs)
    reframe(rod, ls, fs - ls)
    t = b.constraints.new("DAMPED_TRACK"); t.target, t.track_axis = el, "TRACK_Z"
    cl = rod.constraints.new("COPY_LOCATION"); cl.target = el
    t2 = rod.constraints.new("DAMPED_TRACK"); t2.target, t2.track_axis = ef, "TRACK_Z"
    strut_pairs.append((ef, el))

for o in bpy.data.objects:
    ad = o.animation_data
    if ad and ad.action:
        for fc in getattr(ad.action, "fcurves", []):
            for kp in fc.keyframe_points:
                kp.interpolation = "BEZIER"
sc.frame_start, sc.frame_end = 1, 384
print("ANIM_FRAMES=" + json.dumps(F))

# ------------------------------------------------------------------ key poses: look + score
if os.environ.get("ANIM_KEYS", "1") == "1":
    s1 = L.K["centers_x"][1]
    VW = {
        "anim_rear3q": ((4.4, 3.4, 1.10), (0.75, 0.25, 0.05), 34),
        "anim_socket": ((s1 + 0.05, 2.35, 0.55), (s1, 0.72, 0.20), 34),
        "anim_latch_inside": ((s1 - 0.02, 0.05, 0.30), (s1, 0.60, 0.26), 30),
    }
    scores = {}

    def world_bvh(os_):
        from mathutils.bvhtree import BVHTree as B
        verts, polys, off = [], [], 0
        d = bpy.context.evaluated_depsgraph_get()
        for o in os_:
            if o.hide_render:
                continue
            me = o.evaluated_get(d).to_mesh()
            mw = o.matrix_world
            verts += [mw @ vv.co for vv in me.vertices]
            polys += [[off + i for i in p.vertices] for p in me.polygons]
            off += len(me.vertices)
            o.evaluated_get(d).to_mesh_clear()
        return B.FromPolygons(verts, polys) if polys else None

    # designed CONTACTS at the home pose (touching faces read as triangle overlaps): proven
    # instead by the CAD contact checks (limiters_stop_the_flange, weight_on_the_fin_not_the_tube,
    # ball_plungers_preload_the_lip, pin_head_engages_bushing, rotor escape corridor)
    CONTACT_M = ("J_HOOK", "BALL_PLUNGER", "LOCATING_PIN", "STRIKER")
    CONTACT_S = ("COMPRESSION_LIMITER", "BUSHING", "latch_housing", "fork", "pawl", "BULB_SEAL")

    def moving(home=False):
        return [o for o in objs(lambda s: s.startswith("L1_MOD_"))
                if not (home and any(c in o.name for c in CONTACT_M))]

    def static(home=False):
        return [o for o in objs(lambda s: s.startswith("L1_") and not s.startswith("L1_MOD_"))
                if not any(c in o.name for c in (CONTACT_S if home else CONTACT_S[3:]))]
    for tag, fr in (("released", F["released"]), ("lifted", F["lifted"]), ("away", F["away"]),
                    ("hung", F["hung"]), ("locked", F["locked"]), ("hatch_open", F["hatch_open"])):
        sc.frame_set(fr)
        bpy.context.view_layer.update()
        d = mod.matrix_world.translation - home
        scores[f"{tag}_n_mm"] = d.dot(n) / MM
        scores[f"{tag}_v_mm"] = d.dot(v) / MM
        shown = [o for o in cage + tool if not o.hide_render]
        scores[f"{tag}_cage_parts_shown"] = sum(o in cage for o in shown)
        scores[f"{tag}_toolbox_parts_shown"] = sum(o in tool for o in shown)
        if tag in ("released", "lifted", "hung", "locked"):
            home_pose = tag in ("released", "locked")
            bm, bs = world_bvh(moving(home_pose)), world_bvh(static(home_pose))
            scores[f"{tag}_overlap_tris"] = len(bm.overlap(bs)) if bm and bs else -1
        if tag == "released":
            q = forks[0][0].rotation_quaternion
            scores["fork_release_deg"] = -math.degrees(q.angle) if q.angle > 1e-6 else 0.0   # signed as CAD
        if tag == "hatch_open":
            q = hinge.rotation_quaternion
            scores["hatch_open_deg"] = math.degrees(q.angle)
            ef, el = strut_pairs[0]
            scores["strut_L_open_mm"] = (el.matrix_world.translation - ef.matrix_world.translation).length / MM
        L.look({f"{tag}_{k}": vv for k, vv in VW.items()
                if tag in ("released", "lifted", "locked", "hung") or k == "anim_rear3q"},
               res=(1280, 800), label=os.environ.get("BLENDER_LOOP_STEP", "S14"))
    sc.frame_set(1)
    ef, el = strut_pairs[0]
    scores["strut_L_closed_mm"] = (el.matrix_world.translation - ef.matrix_world.translation).length / MM
    ig = HWJ["gas_strut"]["installed_geometry"]
    scores["strut_L_closed_cad_mm"], scores["strut_L_open_cad_mm"] = ig["L_closed"], ig["L_open"]
    print("SCORE " + " ".join(f"{k}={val:.2f}" for k, val in scores.items()))
    L.report_scores(scores)
