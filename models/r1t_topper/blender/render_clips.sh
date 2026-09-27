#!/usr/bin/env bash
set -e
cd ~/evidence/r1t-opus-pass
B=/home/n8/text-to-cad-worktrees/r1t-opus-pass/models/r1t_topper/blender
for c in "$@"; do
  mkdir -p frames_$c
  ~/.local/bin/blender -b anim.blend --python $B/render_clip.py -- $c $PWD/frames_$c > log_$c.txt 2>&1
  ffmpeg -loglevel error -y -framerate 24 -pattern_type glob -i "frames_$c/${c}_*.png" -c:v libx264 -pix_fmt yuv420p -crf 20 clips/r1t_${c}.mp4
  echo "done $c"
done
