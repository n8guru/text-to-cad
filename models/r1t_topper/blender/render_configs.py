"""Photo-real Cycles stills of the three module configs (+ hatch open).
blender -b <S6 scene.blend> --python render_configs.py -- <outdir> [samples]"""
import sys

sys.path.insert(0, "/home/n8/text-to-cad-worktrees/r1t-opus-pass/models/r1t_topper/blender")
import bpy
import r1t_lib as L
import s4_modules as S4

args = sys.argv[sys.argv.index("--") + 1:]
out, samples = args[0], int(args[1]) if len(args) > 1 else 128
sc = bpy.context.scene
sc.frame_set(1)
for o in bpy.data.objects:                       # freeze S6 animation at closed state
    if o.animation_data:
        o.animation_data_clear()
hp = bpy.data.objects["HATCH_PIV"]
hp.rotation_euler = (0, 0, 0)
L.setup_world(1.0)
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"   # forge GPU is shared/full; CPU is the batch-lane default
sc.render.threads_mode = "AUTO"
sc.cycles.samples = samples
sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1600, 1000
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Medium High Contrast"
VIEWS = {"fl3q": ((-5.0, 5.6, 0.35), (-0.5, 0.0, -0.15), 42),
         "rl3q": ((4.9, 4.6, 0.55), (0.25, 0.0, -0.05), 40),
         "side": ((0.4, 6.8, -0.05), (0.4, 0.0, -0.05), 40)}
CONFIGS = {"WINDOW": {"fl3q", "rl3q"}, "CAGE": {"rl3q", "side"}, "TOOLBOX": {"rl3q", "side"}}
for kind, views in CONFIGS.items():
    S4.clear_modules()
    for tag in ("L0", "L1", "R0", "R1"):
        S4.build_module(kind, tag)
    for v in sorted(views):
        loc, tgt, lens = VIEWS[v]
        sc.camera = L.camera("CAM_HERO", loc, tgt, lens)
        sc.render.filepath = f"{out}/r1t_topper_{kind.lower()}_{v}.png"
        bpy.ops.render.render(write_still=True)
        print("WROTE", sc.render.filepath, flush=True)
# hatch open with the dog-canopy kit
S4.clear_modules()
for tag in ("L0", "R0"):
    S4.build_module("WINDOW", tag)
for tag in ("L1", "R1"):
    S4.build_module("CAGE", tag)
import math
hp.rotation_euler = (math.radians(-L.H["open_deg"]), 0, 0)
sc.camera = L.camera("CAM_HERO", (4.6, 2.2, 0.9), (1.0, 0.0, 0.15), 38)
sc.render.filepath = f"{out}/r1t_topper_hatch_open_mixed_kit.png"
bpy.ops.render.render(write_still=True)
print("WROTE", sc.render.filepath, flush=True)
