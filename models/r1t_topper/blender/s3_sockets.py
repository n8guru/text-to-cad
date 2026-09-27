"""S3: four identical side sockets = carbon pocket cut + bonded 6061 socket frame + EPDM seal +
ledge rail + keyed pin bushings + 2 rotary latches (claw pivots animatable) + interior release lever."""
import math
import sys

sys.path.insert(0, "/home/n8/text-to-cad-worktrees/r1t-opus-pass/models/r1t_topper/blender")
import bpy
from mathutils import Matrix
import r1t_lib as L

K = L.K
m = L.M()
C = "20_SOCKETS"
shell = bpy.data.objects["SHELL_CARBON"]
W, Hh = L.opening_hw()
mg, r = K["pocket_margin"], K["corner_r"]
PW, PH, PR = W + 2 * mg, Hh + 2 * mg, r + mg
WALL = L.S["wall"]             # shell wall thickness — params.json shell.wall (single source)
PIN_U = tuple(L.KEY["pin_u"])   # asymmetric -> keyed: module cannot go in upside down
LATCH_U = tuple(L.KEY["latch_u"])
Tr = Matrix.Translation


def geo():
    return dict(W=W, H=Hh, PW=PW, PH=PH, PR=PR, PIN_U=PIN_U, LATCH_U=LATCH_U, WALL=WALL)


def build_socket(side, i):
    tag = f"{side}{i}"
    F = L.socket_frame(side, i)
    e = L.empty("SOCKET_" + tag, F, cname=C)
    parts = []
    # 1 pocket cut through carbon
    L.boolean(shell, L.prism("cut_pocket", L.rrect(PW, PH, PR), -0.08, 0.06, F))
    # 2 socket frame: bond flange ring + opening return lip (machined 6061-T6, black anodise)
    fr = L.ring(f"SOCKET_FRAME_{tag}", L.rrect(PW + 0.09, PH + 0.09, PR + 0.045), L.rrect(W, Hh, r),
                -WALL - 0.008, -WALL, F, C)
    lip = L.ring(f"SOCKET_LIP_{tag}", L.rrect(W + 0.012, Hh + 0.012, r + 0.006), L.rrect(W, Hh, r),
                 -0.085, -WALL - 0.008, F, C)
    parts += [L.assign(fr, m["alu"]), L.assign(lip, m["alu"])]
    # 3 EPDM bulb seal on land (shown at 30 % compression when a module is installed)
    parts.append(L.assign(L.ring(f"SOCKET_SEAL_{tag}", L.rrect(PW - 0.008, PH - 0.008, PR - 0.004),
                                 L.rrect(PW - 0.022, PH - 0.022, PR - 0.011), -WALL, -WALL + 0.006, F, C), m["epdm"]))
    # 4 ledge rail: shelf + up-lip the module hooks hang on (carries module weight in shear)
    shelf = L.box(f"SOCKET_LEDGE_{tag}", (0, -Hh / 2 - 0.004, -0.105), (0.50, 0.008, 0.050), C, F)
    uplip = L.box(f"SOCKET_LEDGE_LIP_{tag}", (0, -Hh / 2 + 0.009, -0.126), (0.50, 0.018, 0.008), C, F)
    parts += [L.assign(shelf, m["alu_raw"]), L.assign(uplip, m["alu_raw"])]
    # 5 pin bushings in top land (hardened steel, press-fit)
    for k, u in enumerate(PIN_U):
        b = L.cyl(f"SOCKET_BUSH_{tag}_{k}", 0.009, 0.010, (0, 0, 0))
        b.matrix_world = F @ Tr((u, Hh / 2 + mg / 2, -WALL - 0.004))
        parts.append(L.assign(b, m["ss"]))
    # 6 rotary latches (housing fixed, claw rotates about local u through pivot)
    for k, u in enumerate(LATCH_U):
        hsg = L.box(f"LATCH_HSG_{tag}_{k}", (u, Hh / 2 - 0.030, -0.112), (0.050, 0.040, 0.034), C, F)
        brk = L.box(f"LATCH_BRKT_{tag}_{k}", (u, Hh / 2 - 0.005, -0.090), (0.056, 0.010, 0.060), C, F)
        parts += [L.assign(hsg, m["ss"]), L.assign(brk, m["alu"])]
        claw = L.box(f"LATCH_CLAW_{tag}_{k}", (0, -0.012, 0.010), (0.012, 0.024, 0.020), C,
                     F @ Tr((u + 0.031, Hh / 2 - 0.030, -0.104)))
        L.assign(claw, m["orange"])
        parts.append(claw)
    # 7 interior release lever (one pull opens both latches via push-pull cables)
    lev = L.box(f"RELEASE_LEVER_{tag}", (0, -0.035, -0.008), (0.090, 0.07, 0.012), C,
                F @ Tr((0, Hh / 2 - 0.010, -0.122)))
    parts.append(L.assign(lev, m["orange"]))
    for k, u in enumerate(LATCH_U):
        cab = L.cyl(f"RELEASE_CABLE_{tag}_{k}", 0.003, abs(u) - 0.05, (0, 0, 0))
        cab.matrix_world = F @ Tr((u / 2, Hh / 2 - 0.012, -0.118)) @ Matrix.Rotation(math.pi / 2, 4, "Y")
        parts.append(L.assign(cab, m["trim"]))
    for p in parts:
        L.parent_keep(p, e)
    return e


if __name__ in ("__main__", "__blender_loop_step__"):
    for o in list(bpy.data.objects):
        if o.name.startswith(("SOCKET", "LATCH", "RELEASE")):
            bpy.data.objects.remove(o, do_unlink=True)
    for side in "LR":
        for i in range(2):
            build_socket(side, i)
    L.look(("rl3q", "sockL", "inside"))
    print("SCORE opening_w=%.3f opening_h=%.3f pocket=%.3fx%.3f lean_deg=%.2f" % (W, Hh, PW, PH, math.degrees(L.lean())))
