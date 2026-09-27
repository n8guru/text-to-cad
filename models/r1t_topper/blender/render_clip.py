"""Render one clip from the S6 scene: blender -b scene.blend --python render_clip.py -- <clip> <outdir>"""
import sys

sys.path.insert(0, "/home/n8/text-to-cad-worktrees/r1t-opus-pass/models/r1t_topper/blender")
import bpy
import r1t_lib as L

clip, out = sys.argv[sys.argv.index("--") + 1:][:2]
CLIPS = {  # name: (camera loc, target, lens, frame_start, frame_end)
    "swap": ((2.4, 2.6, 1.0), (0.75, 0.85, 0.22), 35, 1, 516),
    "lock": ((0.42, 0.36, 0.24), (0.80, 0.74, 0.40), 24, 340, 516),
    "hatch": ((4.2, 2.6, 1.2), (1.2, 0.0, 0.25), 32, 520, 641),
}
loc, tgt, lens, f0, f1 = CLIPS[clip]
sc = bpy.context.scene
L.setup_world()
sc.camera = L.camera("CAM_CLIP", loc, tgt, lens)
sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x, sc.render.resolution_y = 960, 540
sc.eevee.taa_render_samples = 12
sc.view_settings.view_transform = "AgX"
sc.frame_start, sc.frame_end = f0, f1
sc.render.image_settings.file_format = "PNG"
sc.render.filepath = f"{out}/{clip}_"
bpy.ops.render.render(animation=True)
