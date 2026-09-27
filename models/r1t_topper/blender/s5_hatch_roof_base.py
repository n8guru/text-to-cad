"""S5: flush two-pane rear hatch (top hinge, gas struts, 2 rotary latches + keyed T-handle, CHMSL),
4 roof hardpoint ports, 2 base rails + 4 bed accessory-port adapters, front pass-through glass."""
import math
import sys

sys.path.insert(0, "/home/n8/text-to-cad-worktrees/r1t-opus-pass/models/r1t_topper/blender")
import bpy
from mathutils import Matrix, Vector
import r1t_lib as L

S, Hp, T = L.S, L.H, L.T
m = L.M()
C = "40_HATCH_ROOF_BASE"
Tr = Matrix.Translation
shell = bpy.data.objects["SHELL_CARBON"]
for o in list(bpy.data.objects):
    if o.name.startswith(("HATCH", "ROOF_PORT", "BASE_", "PORT_ADAPT", "FRONT_GLASS", "STRUT")):
        bpy.data.objects.remove(o, do_unlink=True)

# ---- rear hatch frame (n = outward +X, tilted by rake) ----
rz = L.roof_z(S["x1"])
b = math.atan2(S["rear_rake"], rz)
z0, z1 = Hp["z_bot"] + 0.03, rz - 0.13
zc = (z0 + z1) / 2
HW, HH = Hp["width"], (z1 - z0) / math.cos(b)
mg = Hp["margin"]
Fm = Matrix.Identity(4)
u, v, n = Vector((0, 1, 0)), Vector((-math.sin(b), 0, math.cos(b))), Vector((math.cos(b), 0, math.sin(b)))
o = Vector((S["x1"] - S["rear_rake"] * zc / rz, 0, zc))
for r_ in range(3):
    Fm[r_][0], Fm[r_][1], Fm[r_][2], Fm[r_][3] = u[r_], v[r_], n[r_], o[r_]
hatch_frame = L.empty("HATCH_FRAME", Fm, cname=C)
L.boolean(shell, L.prism("cut_hatch", L.rrect(HW + 2 * mg, HH + 2 * mg, Hp["corner_r"] + mg), -0.08, 0.06, Fm))
parts = [L.assign(L.ring("HATCH_SURROUND", L.rrect(HW + 2 * mg + 0.09, HH + 2 * mg + 0.09, Hp["corner_r"] + mg + 0.045),
                         L.rrect(HW, HH, Hp["corner_r"]), -0.030, -0.022, Fm, C), m["alu"]),
         L.assign(L.ring("HATCH_SEAL", L.rrect(HW + 2 * mg - 0.008, HH + 2 * mg - 0.008, Hp["corner_r"] + mg - 0.004),
                         L.rrect(HW + 2 * mg - 0.022, HH + 2 * mg - 0.022, Hp["corner_r"] + mg - 0.011), -0.022, -0.016, Fm, C), m["epdm"])]
for p in parts:
    L.parent_keep(p, hatch_frame)

# ---- hatch leaf, pivot on top hinge line ----
hinge = Fm @ Tr((0, HH / 2 + mg - 0.004, -0.012))
piv = L.empty("HATCH_PIV", hinge, cname=C)
L.parent_keep(piv, hatch_frame)
LW, LH = HW + 2 * mg - 0.008, HH + 2 * mg - 0.008
leaf = [L.assign(L.prism("HATCH_LEAF", L.rrect(LW, LH, Hp["corner_r"] + mg - 0.004), -0.018, -0.006, Fm, C), m["carbon"])]
pw = (HW - Hp["mullion"]) / 2
for sgn in (-1, 1):                                               # two flush panes, 140 mm carbon mullion
    pane = L.prism(f"HATCH_PANE_{'L' if sgn > 0 else 'R'}", L.rrect(pw, HH - 0.02, Hp["corner_r"]), -0.006, -0.0005,
                   Fm @ Tr((sgn * (Hp["mullion"] / 2 + pw / 2), 0, 0)), C)
    leaf.append(L.assign(pane, m["glass"]))
leaf.append(L.assign(L.prism("HATCH_MULLION_SKIN", L.rrect(Hp["mullion"] + 0.004, HH, 0.01), -0.006, 0.0, Fm, C), m["carbon"]))
leaf.append(L.assign(L.prism("HATCH_BORDER", [(x, y) for x, y in L.rrect(LW, LH, Hp["corner_r"] + mg - 0.004)], -0.006, 0.0, Fm, C), m["carbon"]))
# border skin is a ring: cut the pane windows out of it
brd = leaf[-1]
for sgn in (-1, 1):
    L.boolean(brd, L.prism("cut_pane", L.rrect(pw, HH - 0.02, Hp["corner_r"]), -0.01, 0.01,
                           Fm @ Tr((sgn * (Hp["mullion"] / 2 + pw / 2), 0, 0))))
L.boolean(brd, L.prism("cut_mull", L.rrect(Hp["mullion"] + 0.004, HH, 0.01), -0.01, 0.01, Fm))
leaf.append(L.assign(L.box("HATCH_CHMSL", (0, HH / 2 + 0.012, 0.0005), (0.36, 0.010, 0.002), C, Fm), m["tail"]))
leaf.append(L.assign(L.box("HATCH_THANDLE", (0, -HH / 2 - 0.004, 0.004), (0.11, 0.026, 0.010), C, Fm), m["black"]))
for sy in (-0.45, 0.45):                                          # same rotary latch as the sockets (commonality)
    leaf.append(L.assign(L.box("HATCH_STRIKER", (sy, -HH / 2 + 0.01, -0.040), (0.03, 0.008, 0.024), C, Fm), m["ss"]))
    lh = L.box("HATCH_LATCH_HSG", (sy, -HH / 2 + 0.01, -0.062), (0.05, 0.04, 0.034), C, Fm)
    L.parent_keep(L.assign(lh, m["ss"]), hatch_frame)
for sy in (-0.42, 0.42):                                          # concealed hinges
    hg = L.box("HATCH_HINGE", (sy, HH / 2 + mg - 0.004, -0.030), (0.08, 0.02, 0.03), C, Fm)
    L.parent_keep(L.assign(hg, m["alu"]), hatch_frame)
for p in leaf:
    L.parent_keep(p, piv)

# ---- gas struts (self-aligning via damped-track constraints) ----
for sy in (-1, 1):
    y = sy * (HW / 2 - 0.02)
    a_sh = L.empty(f"STRUT_ANCHOR_SHELL_{sy}", Tr((S["x1"] - 0.30, y, 0.30)), cname=C)
    a_lf = L.empty(f"STRUT_ANCHOR_LEAF_{sy}", Fm @ Tr((y, -0.02, -0.03)), cname=C)
    L.parent_keep(a_lf, piv)
    body = L.cyl(f"STRUT_BODY_{sy}", 0.011, 0.26, (0, 0, 0), verts=16, cname=C)
    rod = L.cyl(f"STRUT_ROD_{sy}", 0.005, 0.24, (0, 0, 0), verts=12, cname=C)
    for mesh_o in (body, rod):                                    # shift so origin is at one end, axis +Z
        for vv in mesh_o.data.vertices:
            vv.co.z += 0.13 if mesh_o is body else 0.12
    body.location, rod.location = a_sh.location, a_lf.matrix_world.translation
    for ob, tgt in ((body, a_lf), (rod, a_sh)):
        c = ob.constraints.new("DAMPED_TRACK")
        c.target, c.track_axis = tgt, "TRACK_Z"
    c = rod.constraints.new("COPY_LOCATION")
    c.target = a_lf
    rod.constraints.move(1, 0)
    L.assign(body, m["black"])
    L.assign(rod, m["ss"])

# ---- roof hardpoints (topper-owned, flush oval caps over bonded M8 inserts) ----
cy = S["land_half_w"] - (L.roof_z(0) - S["land_top_z"])
for x in L.P["roof_ports_x"]:
    for sy in (1, -1):
        y = sy * L.P["roof_ports_y"]
        z = L.roof_z(x) + S["roof_crown"] * (1 - (y / cy) ** 2)
        cap = L.prism(f"ROOF_PORT_{x:.2f}_{sy}", L.rrect(0.075, 0.034, 0.016), -0.004, 0.002, Tr((x, y, z)), C)
        L.assign(cap, m["black"])

# ---- base rails + bed accessory-port adapters (Rivian port: 2,500 N rating, 4 ports) ----
for sy in (1, -1):
    y = sy * (S["base_half_w"] - 0.06)
    L.assign(L.box(f"BASE_RAIL_{sy}", ((S["x0"] + S["x1"]) / 2, y, 0.020), (S["x1"] - S["x0"] - 0.04, 0.090, 0.040), C), m["alu"])
    for px, py in T["bed_ports"]:
        a = L.cyl(f"PORT_ADAPTER_{px:.2f}_{sy}", 0.028, 0.030, (px, sy * py, 0.015), verts=24, cname=C)
        L.assign(a, m["orange"])

# ---- front bulkhead pass-through glass (aligns to cab rear glass) ----
Ff = Matrix(((0, 0, -1, S["x0"] + 0.0), (-1, 0, 0, 0), (0, 1, 0, 0.36), (0, 0, 0, 1)))
L.boolean(shell, L.prism("cut_front", L.rrect(1.00, 0.30, 0.06), -0.06, 0.06, Ff))
L.assign(L.prism("FRONT_GLASS", L.rrect(1.00, 0.30, 0.06), -0.018, -0.006, Ff, C), m["glass"])

L.look(("rear", "rl3q", "topper3q"))
print("SCORE hatch_opening_w=%.3f h=%.3f rake_deg=%.1f mullion=%.3f" % (HW, HH, math.degrees(b), Hp["mullion"]))
