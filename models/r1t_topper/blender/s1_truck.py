"""S1: Gen-1 R1T reference dummy (00_REFERENCE) from params.json — context only, not fitment authority."""
import math
import sys

sys.path.insert(0, "/home/n8/text-to-cad-worktrees/r1t-opus-pass/models/r1t_topper/blender")
import bpy
import r1t_lib as L

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
T = L.T
m = L.M()
g = T["ground_z"]
C = "00_REFERENCE"
rx = T["rear_axle_x"]
fx = rx - T["wheelbase"]
wz = g + T["tire_r"]
xr = T["rear_end_x"]
xf = xr - T["overall_length"]   # front bumper x
hw = T["body_width"] / 2

# lower body side profile (x,z)
prof = [(xf + 0.05, g + 0.33), (xf, g + 0.60), (xf + 0.02, -0.20), (xf + 0.22, -0.10), (T["windshield_base_x"] - 0.05, -0.03),
        (T["windshield_base_x"], -0.03), (T["tailgate_x"], 0.0), (xr - 0.02, -0.08), (xr, -0.55), (xr - 0.05, g + 0.36),
        (rx + 0.70, g + 0.33), (fx - 0.70, g + 0.33)]
body = L.extrude_profile_y("R1T_BODY", prof, hw, C)
L.bevel(body, 0.07, 4)
L.apply_mods(body)
# bed cavity
bed = L.box("cut_bed", (T["tailgate_x"] - T["bed_len"] / 2, 0, -T["bed_depth"] / 2 + 0.05),
            (T["bed_len"], T["bed_w"], T["bed_depth"] + 0.1))
L.boolean(body, bed)
# wheel arches
for x in (fx, rx):
    L.boolean(body, L.cyl("cut_arch", T["tire_r"] + 0.06, 2.4, (x, 0, wz), (math.pi / 2, 0, 0), 64))
L.assign(body, m["paint"])
L.smooth(body)

# greenhouse
gh = [(T["windshield_base_x"], -0.03), (T["roof_front_x"], T["cab_roof_z"] - 0.02), (T["cab_back_x"] - 0.25, T["cab_roof_z"]), (T["cab_back_x"], T["cab_roof_z"] - 0.06),
      (T["cab_back_x"], -0.01)]
cab = L.extrude_profile_y("R1T_GREENHOUSE", gh, hw - 0.14, C)
for v in cab.data.vertices:
    k = max(0.0, v.co.z) / T["cab_roof_z"]
    v.co.y *= 1 - 0.13 * k
L.bevel(cab, 0.09, 5)
L.apply_mods(cab)
L.assign(cab, m["glass"])
L.smooth(cab)
roof = L.box("R1T_ROOF", ((T["roof_front_x"] + T["cab_back_x"]) / 2 + 0.05, 0, T["cab_roof_z"] - 0.004), (T["cab_back_x"] - T["roof_front_x"] - 0.35, 2 * (hw - 0.14) * 0.87 - 0.2, 0.02), C)
L.bevel(roof, 0.009, 3)
L.assign(roof, m["black"])

# wheels
for x in (fx, rx):
    for sy in (1, -1):
        y = sy * (T["track"] / 2)
        t = L.cyl(f"TIRE_{x:.1f}_{sy}", T["tire_r"], T["tire_w"], (x, y, wz), (math.pi / 2, 0, 0), 64, C)
        L.bevel(t, 0.06, 4, 60)
        L.assign(t, m["tire"])
        L.smooth(t)
        r = L.cyl(f"RIM_{x:.1f}_{sy}", T["tire_r"] * 0.62, T["tire_w"] + 0.01, (x, y, wz), (math.pi / 2, 0, 0), 48, C)
        L.assign(r, m["rim"])

# signature lights: stadium headlamps, front bar, rear bar
for sy in (1, -1):
    h = L.cyl(f"HEADLAMP_{sy}", 0.075, 0.03, (xf - 0.005, sy * (hw - 0.26), -0.33), (0, math.pi / 2, 0), 32, C)
    h.scale = (1.6, 1.0, 1.0)
    L.assign(h, m["light"])
L.assign(L.box("FRONT_LIGHTBAR", (xf + 0.01, 0, -0.26), (0.02, 2 * hw - 0.55, 0.018), C), m["light"])
L.assign(L.box("REAR_LIGHTBAR", (xr + 0.005, 0, -0.07), (0.02, 2 * hw - 0.2, 0.03), C), m["tail"])

# ground
gp = L.box("GROUND", (0, 0, g - 0.01), (40, 40, 0.02), C)
L.assign(gp, m["ground"])

L.look(("fl3q", "rl3q", "side"))
bmin, bmax = L.bbox(body)
print("SCORE truck_len=%.3f width=%.3f cab_top_above_ground=%.3f" % (
    bmax[0] - bmin[0], bmax[1] - bmin[1], T["cab_roof_z"] - g))
