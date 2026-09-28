"""S11: Gen-1 R1T context body built from Rivian's own line art (00_REFERENCE, not fitment).

Every shape input comes from step27/style/rivian_reference.json:
  side silhouette   r1t_side.top_profile_x_z   (owner's guide p.17, wheelbase-scaled)
  plan outline      r1t_plan.body_half_width_outline_x_y   (Upfitting Guide p.59)
  greenhouse        r1t_rear.greenhouse_section_zfrac_halfwfrac (owner's guide p.14 rear view)
and the published wheelbase / track / tyre size. The body is lofted station by station so the
cab-back, spoiler, rail and tailgate positions the topper is checked against are the ones in the
render, not a separately guessed proxy.
"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r1t_lib as L  # noqa: E402

L.clear_scene()
m = L.M()
C = "00_REFERENCE_R1T"
T, REF = L.T, L.REF
g = T["ground_z"]
side, plan, rear = REF["r1t_side"], REF["r1t_plan"], REF["r1t_rear"]

# ---- profiles as functions of x (bed frame, metres) -----------------------------------------
tp = np.array(side["top_profile_x_z"])                   # (x, z) silhouette top
xs_top, zs_top = tp[:, 0], tp[:, 1]
po = np.array(plan["body_half_width_outline_x_y"])       # (x, half-width) incl. mirrors
x_mir0, x_mir1 = -2.45, -1.85                            # A-pillar mirror bump: clamp it out
keep = (po[:, 0] < x_mir0) | (po[:, 0] > x_mir1)
xs_w, ws = po[keep, 0], po[keep, 1]
ws = np.minimum(ws, T["body_width"] / 2)
sec = np.array(rear["greenhouse_section_zfrac_halfwfrac"])   # (zfrac rail->roof, half/bodyhalf)
sec = sec[np.argsort(sec[:, 0])]
x_front, x_rear = float(xs_top.min()), float(xs_top.max())
sill = side["sill_z"]
fa, ra = side["front_axle_x"], side["rear_axle_x"]


def ztop(x):
    return float(np.interp(x, xs_top, zs_top))


def halfw(x):
    return float(np.interp(x, xs_w, ws))


def zbot(x):
    """Sill between the axles, rising through the overhangs (approach / departure)."""
    if x < fa:
        return sill + 0.30 * min(1.0, (fa - x) / (fa - x_front))
    if x > ra:
        return sill + 0.25 * min(1.0, (x - ra) / (x_rear - ra))
    return sill


def gh_half(zf, body_half):
    """Greenhouse half-width at height fraction zf (0 = rail, 1 = roof), rear-view shape."""
    return body_half * float(np.interp(zf, sec[:, 0], sec[:, 1]))


N_BOT, N_SIDE, N_BED, N_GH, N_SH, N_ROOF = 6, 10, 4, 6, 5, 7
TH = math.radians(rear["greenhouse_tumblehome_deg"])      # R1T C-pillar tumblehome (21.8 deg)
BED0, BED1 = 0.0, T["bed_len"] - 0.004
BED_HW = T["bed_w"] / 2


def in_bed(x):
    return BED0 + 0.01 < x < BED1 - 0.01


def section(x):
    """Closed (y, z) loop, right half then mirrored, constant vertex count for bridging.

    bottom -> lower side -> [bed U-channel | collapsed] -> greenhouse (tumblehome) -> shoulder ->
    crowned roof. Stations without a greenhouse collapse it onto the deck line.
    """
    w = halfw(x)
    zb, zt = zbot(x), ztop(x)
    zbelt = min(zt, 0.0)
    pts = []
    for i in range(N_BOT):
        pts.append((w * 0.9 * i / (N_BOT - 1), zb))
    for i in range(1, N_SIDE + 1):
        t = i / N_SIDE
        zz = zb + (zbelt - zb) * t
        bulge = (1 - (2 * t - 1) ** 6) ** 0.25
        pts.append((w * (0.9 + 0.1 * bulge), zz))
    # bed: rail cap inward, down the inner wall, across to the floor (collapsed elsewhere)
    cap_in = T["rail_cap_in"]
    for i in range(N_BED):
        f = (i + 1) / N_BED
        if in_bed(x):
            yy = w - (w - BED_HW) * min(1.0, f * 2)
            zz = 0.0 if f <= 0.5 else -T["bed_depth"] * (f - 0.5) / 0.5
        else:
            yy, zz = w - (w - cap_in) * 0.25 * f, zbelt
        pts.append((yy, zz))
    y_deck = pts[-1][0]
    gh = zt > 0.02 and not in_bed(x)
    g0 = min(0.81 * T["body_width"] / 2, w * 0.9)
    h_sh = 0.10
    for i in range(N_GH):
        f = (i + 1) / N_GH
        if gh:
            zz = max(zbelt, 0.0) + (zt - 0.015 - h_sh - max(zbelt, 0.0)) * f
            yy = g0 - (zz - max(zbelt, 0.0)) * math.tan(TH)
            if in_bed(x):
                yy = BED_HW * (1 - f)
        else:
            zz = pts[-1][1] if in_bed(x) else zbelt
            yy = y_deck * (1 - 0.5 * f)
        pts.append((yy, zz))
    y0, z0 = pts[-1]
    for i in range(1, N_SH + 1):                              # rounded shoulder
        a = math.radians(90 * i / N_SH)
        if gh:
            pts.append((y0 - h_sh * (1 - math.cos(a)) * 0.9, z0 + h_sh * math.sin(a)))
        else:
            pts.append((y0 * (1 - 0.1 * i / N_SH), z0))
    y_edge, z_edge = pts[-1]
    for i in range(1, N_ROOF + 1):                            # crown: the traced line is the TOP
        f = i / N_ROOF
        pts.append((y_edge * (1 - f), (z_edge + (zt - z_edge) * (1 - (1 - f) ** 2)) if gh else z_edge))
    right = pts
    left = [(-y, z) for y, z in reversed(right[1:-1])]
    return right + left


stations = np.concatenate([np.linspace(x_front, x_front + 0.12, 6)[:-1],
                           np.arange(x_front + 0.12, x_rear - 0.10, 0.03),
                           np.linspace(x_rear - 0.10, x_rear, 5)])
bm = bmesh.new()
rings = []
for x in stations:
    loop = [bm.verts.new((x, y, z)) for y, z in section(float(x))]
    rings.append(loop)
n = len(rings[0])
for a, b in zip(rings, rings[1:]):
    for j in range(n):
        bm.faces.new((a[j], a[(j + 1) % n], b[(j + 1) % n], b[j]))
bm.faces.new(list(reversed(rings[0])))
bm.faces.new(rings[-1])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
me = bpy.data.meshes.new("R1T_BODY")
bm.to_mesh(me)
bm.free()
body = bpy.data.objects.new("R1T_BODY", me)
bpy.context.scene.collection.objects.link(body)
L.link(body, C)


def cut(target, cutter):
    mod = target.modifiers.new("cut", "BOOLEAN")
    mod.operation, mod.object, mod.solver = "DIFFERENCE", cutter, "EXACT"
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter, do_unlink=True)


def box(name, c, s):
    bpy.ops.mesh.primitive_cube_add(size=1, location=c)
    o = bpy.context.object
    o.name = name
    o.scale = s
    bpy.ops.object.transform_apply(scale=True)
    return o


def cyl(name, r, d, loc, rot, verts=64):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    return o


# wheel arches (published wheelbase / tyre); the bed U-channel is built into the sections
wz = g + T["tire_r"]
for x in (fa, ra):
    cut(body, cyl("cut_arch", T["tire_r"] + 0.055, 2.4, (x, 0, wz), (math.pi / 2, 0, 0)))
# materials by height: paint below the belt, glass/black greenhouse above it
body.data.materials.clear()
for k in ("paint", "glass", "black"):
    body.data.materials.append(m[k])
for p in body.data.polygons:
    c = p.center
    if c.z > 0.035 and c.x < T["cab_back"][0][0] + 0.02:
        p.material_index = 2 if c.z > T["cab_roof_z"] - 0.02 and abs(c.y) < 0.55 else 1
L.smooth(body, 32)
wm = body.modifiers.new("wn", "WEIGHTED_NORMAL")
wm.keep_sharp = True

# wheels: 275/65R20 on the published track
for x in (fa, ra):
    for sy in (1, -1):
        y = sy * (T["track"] / 2)
        t = cyl(f"TIRE_{x:.2f}_{sy}", T["tire_r"], T["tire_w"], (x, y, wz), (math.pi / 2, 0, 0), 72)
        bev = t.modifiers.new("b", "BEVEL")
        bev.width, bev.segments = 0.05, 5
        L.assign(t, m["tire"])
        L.smooth(t)
        L.link(t, C)
        r = cyl(f"RIM_{x:.2f}_{sy}", 0.254, T["tire_w"] + 0.012, (x, y, wz), (math.pi / 2, 0, 0), 48)
        L.assign(r, m["rim"])
        L.link(r, C)

# signature lighting: stadium headlamps + front bar, full-width rear bar
xf = x_front
for sy in (1, -1):
    h = cyl(f"HEADLAMP_{sy}", 0.06, 0.03, (xf - 0.004, sy * (halfw(xf + 0.05) - 0.18), ztop(xf + 0.05) - 0.13),
            (0, math.pi / 2, 0), 32)
    h.scale = (1.0, 1.0, 1.9)
    L.assign(h, m["light"])
    L.link(h, C)
bar = box("FRONT_LIGHTBAR", (xf - 0.004, 0, ztop(xf + 0.05) - 0.035), (0.02, 2 * halfw(xf + 0.05) - 0.3, 0.016))
L.assign(bar, m["light"])
L.link(bar, C)
rb = box("REAR_LIGHTBAR", (x_rear + 0.004, 0, -0.08), (0.012, 2 * halfw(x_rear - 0.05) - 0.16, 0.028))
L.assign(rb, m["tail"])
L.link(rb, C)
gp = box("GROUND", (0, 0, g - 0.01), (60, 60, 0.02))
L.assign(gp, m["ground"])
L.link(gp, C)

# ---- look + score ---------------------------------------------------------------------------
V = {   # "ctx_" prefix: the blender-loop runtime writes its own side/front/overhead stills
    "ctx_side": ((-1.0, -9.0, 0.10), (-1.0, 0.0, -0.40), 33),
    "ctx_rear3q": ((5.2, -4.4, 1.2), (0.2, 0.0, -0.25), 34),
    "ctx_front3q": ((-7.4, -5.2, 1.0), (-1.8, 0.0, -0.35), 33),
    "ctx_top": ((-1.0, 0.0, 8.5), (-1.0, 0.0, -0.5), 30),
}
L.look(V, res=(1400, 800))
bmin, bmax = L.bbox(body)
fin = (-0.47, -0.36)                      # antenna fin x-range (side view)
roof = max(v.co.z for v in body.data.vertices if not fin[0] < v.co.x < fin[1])
top = max(v.co.z for v in body.data.vertices)
dg = bpy.context.evaluated_depsgraph_get()
hit, loc, *_ = bpy.context.scene.ray_cast(dg, Vector((0.7, 0.0, 0.6)), Vector((0, 0, -1)))
bed_floor = loc.z if hit else 0.0
scores = {
    "length_m": bmax[0] - bmin[0], "width_m": bmax[1] - bmin[1],
    "roof_no_fin_above_ground_m": roof - g, "top_with_fin_above_ground_m": top - g,
    "rail_above_ground_m": -g, "bed_depth_m": -bed_floor,
    "cab_back_x": T["cab_back"][0][0], "wheelbase_m": ra - fa,
}
print("SCORE " + " ".join(f"{k}={v:.3f}" for k, v in scores.items()))
L.report_scores(scores)
