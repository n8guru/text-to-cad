"""S2: carbon shell A-surface (R1S roofline continuation) as 22 mm hollow wall, open bottom."""
import math
import sys

sys.path.insert(0, "/home/n8/text-to-cad-worktrees/r1t-opus-pass/models/r1t_topper/blender")
import bpy
import r1t_lib as L

S = L.S
m = L.M()
C = "10_TOPPER"
for o in list(bpy.data.objects):
    if o.name.startswith(("SHELL", "cut_")):
        bpy.data.objects.remove(o, do_unlink=True)


def contour(x, inset=0.0, zb=0.0):
    """(y,z) loop from left base over roof to right base."""
    bw, lw, lt = S["base_half_w"] - inset, S["land_half_w"] - inset, S["land_top_z"]
    rz = L.roof_z(x) - inset
    r = rz - lt
    left = [(bw + (lw - bw) * (z - zb) / (lt - zb), z) for z in [zb + (lt - zb) * i / 6 for i in range(6)]]
    cy = lw - r
    for i in range(11):                               # shoulder arc 0..90 deg
        a = math.radians(90 * i / 10)
        left.append((cy + r * math.cos(a), lt + r * math.sin(a)))
    for i in range(1, 9):                             # crowned roof to centre
        y = cy * (1 - i / 9)
        left.append((y, rz + S["roof_crown"] * (1 - (y / cy) ** 2)))
    right = [(-y, z) for y, z in reversed(left)]
    return left + [(0.0, rz + S["roof_crown"])] + right


def solid(name, inset, zb, x0, x1, rc_r, rc_f, rake):
    xs = []
    for i in range(5):                                 # front round-over
        t = math.radians(90 * i / 4)
        xs.append((x0 + rc_f - rc_f * math.sin(t), rc_f * (1 - math.cos(t))))
    xs = xs[::-1]
    for i in range(1, 12):
        xs.append((x0 + rc_f + (x1 - rc_r - x0 - rc_f) * i / 12, 0.0))
    for i in range(9):                                 # rear corner wrap
        t = math.radians(90 * i / 8)
        xs.append((x1 - rc_r + rc_r * math.sin(t), rc_r * (1 - math.cos(t))))
    V, rings = [], []
    for x, ins in xs:
        pts = contour(x, inset + ins, zb)
        base = len(V)
        rz = L.roof_z(x)
        for y, z in pts:
            k = max(0.0, (x - (x1 - 0.45)) / 0.45)
            V.append((x - rake * (z / rz) * k, y, z))
        rings.append(base)
    n = len(contour(x0))
    F = []
    for a, b in zip(rings, rings[1:]):
        for j in range(n - 1):
            F.append([a + j, a + j + 1, b + j + 1, b + j])
        F.append([a + n - 1, a, b, b + n - 1])        # bottom strip
    F.append(list(range(rings[0], rings[0] + n))[::-1])
    F.append(list(range(rings[-1], rings[-1] + n)))
    o = L.mesh_obj(name, V, F, C)
    L.fix_normals(o)
    return o


outer = solid("SHELL_CARBON", 0.0, 0.0, S["x0"], S["x1"], 0.11, 0.03, S["rear_rake"])
inner = solid("cut_inner", S["wall"], -0.06, S["x0"] + S["wall"], S["x1"] - S["wall"], 0.09, 0.02, S["rear_rake"])
L.boolean(outer, inner)
L.assign(outer, m["carbon"])
L.smooth(outer, 40)

L.look(("fl3q", "rl3q", "side"))
import bmesh
bm = bmesh.new()
bm.from_mesh(outer.data)
vol = bm.calc_volume()
bm.free()
bmin, bmax = L.bbox(outer)
print("SCORE shell_len=%.3f width=%.3f top_z=%.3f wall_volume_m3=%.4f mass_est_kg=%.1f" % (
    bmax[0] - bmin[0], bmax[1] - bmin[1], bmax[2], vol, vol * 330))   # ~330 kg/m3 foam-core sandwich
