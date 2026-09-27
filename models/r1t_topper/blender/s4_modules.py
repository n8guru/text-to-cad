"""S4: WINDOW / CAGE / TOOLBOX modules sharing one plug: flush flange + plug tube + 2 hooks +
2 strikers + 2 keyed pins. Hierarchy per module: MOD_<tag> (translate) -> MOD_<tag>_PIV (tilt about
hook line, local X) -> geometry. Default kit: L0 WINDOW, L1 CAGE, R0 WINDOW, R1 TOOLBOX."""
import math
import sys

sys.path.insert(0, "/home/n8/text-to-cad-worktrees/r1t-opus-pass/models/r1t_topper/blender")
import bpy
from mathutils import Matrix
import r1t_lib as L
import s3_sockets as S3

g = S3.geo()
W, Hh, PW, PH, PR = g["W"], g["H"], g["PW"], g["PH"], g["PR"]
r = L.K["corner_r"]
SH = L.K["shutline"]
m = L.M()
C = "30_MODULES"
PIVOT = (0.0, -Hh / 2 + 0.024, -0.130)       # hook arm resting on ledge lip = tilt axis
Tr = Matrix.Translation
DEFAULT_KIT = {"L0": "WINDOW", "L1": "CAGE", "R0": "WINDOW", "R1": "TOOLBOX"}


def common(name, F):
    """Shared plug geometry in socket-local coords (F = socket frame at installed pose)."""
    out = []
    out.append(L.assign(L.ring(f"{name}_PLUG", L.rrect(W - 0.012, Hh - 0.012, r - 0.006),
                               L.rrect(W - 0.040, Hh - 0.040, r - 0.02), -0.080, -0.018, F, C), m["alu"]))
    for u in (-0.20, 0.20):                                     # hooks (316 SS, 6 mm plate)
        out.append(L.assign(L.box(f"{name}_HOOK_ARM", (u, -Hh / 2 + 0.024, -0.1125), (0.030, 0.008, 0.065), C, F), m["ss"]))
        out.append(L.assign(L.box(f"{name}_HOOK_FINGER", (u, -Hh / 2 + 0.015, -0.140), (0.030, 0.026, 0.010), C, F), m["ss"]))
    for u in S3.LATCH_U:                                        # U strikers (Ø8 SS) into latch throats
        out.append(L.assign(L.box(f"{name}_STRIKER", (u + 0.006, Hh / 2 - 0.030, -0.092), (0.030, 0.008, 0.024), C, F), m["ss"]))
    for k, u in enumerate(S3.PIN_U):                            # keyed pins: round + diamond
        p = L.cyl(f"{name}_PIN{k}", 0.005, 0.018, (0, 0, 0))
        p.matrix_world = F @ Tr((u, Hh / 2 + L.K["pocket_margin"] / 2, -0.027))
        out.append(L.assign(p, m["ss"] if k == 0 else m["orange"]))
    return out


def flange(name, F, inner_w, inner_h, inner_r):
    return L.assign(L.ring(f"{name}_FLANGE", L.rrect(PW - 2 * SH, PH - 2 * SH, PR - SH),
                           L.rrect(inner_w, inner_h, inner_r), -0.018, 0.0, F, C), m["carbon"])


def window(name, F):
    out = [flange(name, F, W + 0.004, Hh + 0.004, r + 0.002)]
    out.append(L.assign(L.ring(f"{name}_GLAZE_SEAT", L.rrect(W + 0.004, Hh + 0.004, r + 0.002),
                               L.rrect(W - 0.04, Hh - 0.04, r - 0.02), -0.018, -0.006, F, C), m["black"]))
    out.append(L.assign(L.prism(f"{name}_PANE", L.rrect(W, Hh, r), -0.006, -0.0005, F, C), m["glass"]))
    return out


def cage(name, F):
    out = [flange(name, F, W - 0.012, Hh - 0.012, r - 0.006)]
    n = 13
    for k in range(n):                                          # vertical Ø12 bars, 48 mm pitch
        u = -W / 2 + 0.05 + (W - 0.10) * k / (n - 1)
        b = L.cyl(f"{name}_BAR", 0.006, Hh - 0.03, (0, 0, 0), verts=16)
        b.matrix_world = F @ Tr((u, 0, -0.010)) @ Matrix.Rotation(math.pi / 2, 4, "X")
        out.append(L.assign(b, m["ss"]))
    for v in (-Hh / 4, Hh / 4):
        out.append(L.assign(L.box(f"{name}_RAIL", (0, v, -0.016), (W - 0.03, 0.012, 0.008), C, F), m["ss"]))
    nu, nv = 64, 36                                             # 10 mm woven SS mesh behind bars
    V = [(-W / 2 + 0.02 + (W - 0.04) * a / nu, -Hh / 2 + 0.02 + (Hh - 0.04) * b / nv, -0.024)
         for b in range(nv + 1) for a in range(nu + 1)]
    Fq = [[b * (nu + 1) + a, b * (nu + 1) + a + 1, (b + 1) * (nu + 1) + a + 1, (b + 1) * (nu + 1) + a]
          for b in range(nv) for a in range(nu)]
    mesh = L.mesh_obj(f"{name}_MESH", V, Fq, C)
    mesh.matrix_world = F
    wf = mesh.modifiers.new("wf", "WIREFRAME")
    wf.thickness = 0.0015
    out.append(L.assign(mesh, m["ss"]))
    return out


def toolbox(name, F):
    out = [flange(name, F, W - 0.012, Hh - 0.012, r - 0.006)]
    door = L.prism(f"{name}_DOOR", L.rrect(W - 0.016, Hh - 0.016, r - 0.008), -0.016, -0.001, F, C)
    out.append(L.assign(door, m["carbon"]))
    th = L.box(f"{name}_THANDLE", (0, Hh / 2 - 0.05, 0.004), (0.10, 0.028, 0.010), C, F)
    out.append(L.assign(th, m["black"]))
    tub_h = Hh - 0.080
    tub = L.box(f"{name}_TUB", (0, -Hh / 2 + 0.008 + tub_h / 2, -0.19), (W - 0.03, tub_h, 0.34), C, F)
    out.append(L.assign(tub, m["alu_raw"]))
    return out


BUILD = {"WINDOW": window, "CAGE": cage, "TOOLBOX": toolbox}


def build_module(kind, tag):
    sock = bpy.data.objects["SOCKET_" + tag]
    F = sock.matrix_world.copy()
    name = f"MOD_{tag}_{kind}"
    root = L.empty(name, F, cname=C)
    L.parent_keep(root, sock)
    piv = L.empty(name + "_PIV", F @ Tr(PIVOT), cname=C)
    L.parent_keep(piv, root)
    for p in common(name, F) + BUILD[kind](name, F):
        L.parent_keep(p, piv)
    return root


def clear_modules():
    for o in list(bpy.data.objects):
        if o.name.startswith("MOD_"):
            bpy.data.objects.remove(o, do_unlink=True)


if __name__ in ("__main__", "__blender_loop_step__"):
    clear_modules()
    for tag, kind in DEFAULT_KIT.items():
        build_module(kind, tag)
    L.look(("fl3q", "sockL", "inside"))
    bpy.context.view_layer.update()
    # interference proxy: plug outer vs opening (6 mm/side clearance by construction), flange vs pocket (shut-line)
    print("SCORE plug_clear_mm=%.1f shutline_mm=%.1f pins_u=%s latches_u=%s" % (6.0, SH * 1000, S3.PIN_U, S3.LATCH_U))
