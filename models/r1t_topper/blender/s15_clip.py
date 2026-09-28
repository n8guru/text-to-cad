"""S15: render the S14 animation to frames and encode MP4s (one move: render the timeline).

Clips go to <blender-loop run>/clips/: the whole sequence from the rear three-quarter, and the
L1 socket sequence from inside the topper (latches, handle, safety catch, swap).
"""
import os
import shutil
import subprocess
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r1t_lib as L  # noqa: E402

sc = bpy.context.scene
run = L.run_dir()
clips = run / "clips"
clips.mkdir(parents=True, exist_ok=True)
L.setup_world()
sc.render.engine = "BLENDER_EEVEE"
try:
    sc.eevee.taa_render_samples = 16
except Exception:
    pass
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
sc.view_settings.view_transform = "AgX"
sc.render.image_settings.file_format = "PNG"
s1 = L.K["centers_x"][1]
CLIPS = {
    "r1t_topper_mechanism_rear3q": (((4.4, 3.4, 1.10), (0.75, 0.25, 0.05), 34), 1, sc.frame_end),
    "r1t_topper_socket_inside": (((s1 - 0.02, 0.05, 0.30), (s1, 0.60, 0.26), 30), 1, 250),
}
made = {}
for name, ((loc, tgt, lens), f0, f1) in CLIPS.items():
    frames = run / f"frames_{name}"
    if frames.exists():
        shutil.rmtree(frames)
    frames.mkdir()
    sc.camera = L.camera("CAM_" + name, loc, tgt, lens)
    sc.frame_start, sc.frame_end = f0, f1
    sc.render.filepath = str(frames / "f_")
    bpy.ops.render.render(animation=True)
    mp4 = clips / f"{name}.mp4"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", "24", "-pattern_type", "glob",
                    "-i", str(frames / "f_*.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                    str(mp4)], check=True)
    made[name] = (mp4, len(list(frames.glob("f_*.png"))))          # frames actually on disk
sc.frame_start, sc.frame_end = 1, 384
sc.frame_set(1)
scores = {f"frames_{k}": n for k, (p, n) in made.items()}
scores.update({f"mb_{k}": p.stat().st_size / 1e6 for k, (p, n) in made.items()})
print("CLIPS=" + ", ".join(str(p) for p, _ in made.values()))
L.report_scores(scores)
