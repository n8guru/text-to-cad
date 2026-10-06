"""Joint and fastener schedule for everything Step 27 owns (Step 27 rev 10).

Every joint in the product is listed ONCE here with: what it joins, how many times it occurs (a
count taken from the geometry model's parts manifest, never typed), the fastener(s) per
occurrence, torque, thread treatment and the grip arithmetic where the stack is in the CAD.
``make_bom`` turns this into the fastener and consumable sections of BOM27.md, and
``checks_step27.check_fastener_schedule`` asserts each count against the manifest.

Torques for metric screws come from the R1T Upfitting Guide p.57 table (8.8 ~ A4-80 strength;
A4-70 taken at 75 % of it); a joint into tapped 6061 or a soft/mixed joint uses the "soft joint"
column, as Rivian's own table directs.
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def family(part: str) -> str:
    fam = re.sub(r"^(L0|L1|R0|R1)_", "", part.split("__")[-1])
    fam = re.sub(r"_(\d{1,2}|L0|L1|R0|R1)$", "", fam)
    return fam.split("-")[0]


def manifest_counts(man=None) -> Counter:
    man = man if man is not None else json.loads((ROOT / "out" / "parts_manifest.json").read_text())
    return Counter(family(m["part"]) for m in man)


def count_of(c: Counter, *patterns: str) -> int:
    """Instances whose family contains ANY of the patterns (substring, case-sensitive)."""
    return sum(n for f, n in c.items() if any(p in f for p in patterns))


def _rr_perimeter(w, h, r):
    return 2 * (w + h) - 8 * r + 2 * math.pi * r


def glazing_retainer_screws() -> int:
    """Hatch glazing retainers: M4 at <= 90 mm pitch round each window's retainer centreline."""
    import hatch as HA
    w = HA.WIN
    pw = (w["x1"] - w["x0"]) + 2 * w["overlap"] - 10
    ph = 2 * w["y"] + 2 * w["overlap"] - 10
    return max(6, math.ceil(_rr_perimeter(pw, ph, w["r"]) / 90.0))


def bond_area_m2() -> dict:
    """Modelled bond areas (one face of each joint), for the adhesive quantity."""
    import geom as G
    import mounts
    import shell as SH
    W, HH = G.opening_wh()
    k_r = G.K["corner_r"]
    e_mid = (G.RECESS_OUT - 1.0 + G.BOND_OUT) / 2
    sock = 4 * _rr_perimeter(W + 2 * e_mid, HH + 2 * e_mid, k_r + e_mid) * (G.BOND_OUT - G.RECESS_OUT + 1.0)
    hw_, hh_ = G.hatch_wh()
    he = (G.H_RECESS_OUT - 1.0 + G.H_BOND_OUT) / 2
    hatch = _rr_perimeter(hw_ + 2 * he, hh_ + 2 * he, G.H["corner_r"] + he) * (G.H_BOND_OUT - G.H_RECESS_OUT + 1.0)
    rails = sum(r.bounding_box().size.X * r.bounding_box().size.Y for r in mounts.base_rails()) * 0.9
    hp = 4 * (math.pi * (SH.HARDPOINT["dia"] / 2) ** 2 + math.pi * SH.HARDPOINT["dia"] * SH.HARDPOINT["depth"])
    small = (2 * 22 * 22 + 2 * 30 * 22) + (glazing_retainer_screws() * 2 + 2) * math.pi * 10 * 12
    out = {"socket_frames": sock, "hatch_surround": hatch, "base_rails_to_foot": rails,
           "roof_hardpoints": hp, "leaf_bosses_blocks_inserts": small}
    return {k: round(v / 1e6, 4) for k, v in out.items()}


def adhesive_cartridges(bondline_mm=0.25, waste=0.6, cartridge_ml=50.0):
    a = sum(bond_area_m2().values())
    ml = a * 1e6 * bondline_mm / 1000.0 * (1 + waste)
    return round(a, 3), round(ml, 1), math.ceil(ml / cartridge_ml)


# --------------------------------------------------------------------------------- the schedule
# count: (patterns...) counted in the manifest, or an int, or a callable(counter) -> int
def joints():
    import mounts
    st = mounts.stack_report()
    retainer_n = glazing_retainer_screws()
    return [
        {"id": "J01", "joint": "Port Latch Foot (Rivian-crossbar style): hook teeth -> OEM port latch pins; "
                               "PLF body -> base rail strip (shop fit-up, topper off the truck)",
         "count": ("PLF_BODY",),
         "per": [("SHCS_M6x30_A4", 2), ("SSCREW_M6x20_A4", 1), ("PIN_DOWEL_5x80_A4", 1)],
         "custom_per": [("PLF_PADDLE_6061", 1), ("PLF_HOOK_SLIDER_17_4PH", 1), ("PLF_SHIM_316_1p0", 2)],
         "torque": "rail screws 6 Nm (A4-70 M6 into tapped 6061, soft joint), Tef-Gel, Loctite 243 once the shim "
                   "pack is set; tuning screw: set at P-CAL-01b / prototype; hinge pin: press fit in one ear",
         "grip": f"rail screw: seat to strip face {st['screw_grip']:.1f} mm (incl. {st['shim_nominal']:.1f} mm "
                 f"shim pack, kit 0 - {st['shim_range'][1]:.0f}), {st['screw_engagement']:.1f} mm thread in a "
                 f"{st['rail_strip_t_min']:.1f} mm strip (>= 1.5 d = 9.0 required); in the field the foot is "
                 f"latched by the paddle - no fastener, no tool but the key. Purchased per station: 1 x CompX "
                 f"C8053 lock, 1 x M8 detent plunger (BOM section 1)",
         "access": "paddle + lock face INBOARD, serviced from the bed (check_plf_paddle_sweep)"},
        {"id": "J02", "joint": "R4-30 rotary latch -> latch carrier plate (3.5 mm), cable bracket "
                               "R4-0-50253-1 sandwiched", "count": ("latch_housing_R4",),
         "per": [("SHCS_1/4-20x5/8_316", 2)], "torque": "5 Nm, Loctite 243 (into the latch's "
         "1/4-20 inserts; Southco publishes no torque for the threaded-mount option - confirm)",
         "grip": "plate 3.5 + bracket <= 2.5 -> 9.9 mm into the latch insert"},
        {"id": "J03", "joint": "R4-90-321-20 striker bolt (own M10 thread) through the slotted 316 "
                               "bracket into the tapped 6061 arm/plug frame", "count": ("STRIKER_BOLT",),
         "per": [], "torque": "20 Nm, Loctite 243 (Upfit p.57 M10 soft joint 13.4-40.5 Nm)",
         "grip": "bracket 6 mm; M10 tapped 20 deep in 6061"},
        {"id": "J04", "joint": "316 J-hook -> module plug-tube floor (5 mm 6061)", "count": ("J_HOOK",),
         "per": [("SHCS_M6x20_A4", 2), ("NUT_M6_NYLOC_A4", 2), ("WASHER_M6_A4", 4)],
         "torque": "8 Nm (Upfit p.57 M6 8.8 hard 5.7-11.3, A4-70 ~ 75 %)",
         "grip": "hook 6 + tube 5 + 2 washers 3.2 = 14.2; nut 5.2 + 2 pitches -> 20"},
        {"id": "J05", "joint": "UHMW compression-limiter pad -> 6061 frame boss",
         "count": ("COMPRESSION_LIMITER",), "per": [("FHCS_M6x12_A4", 1)],
         "torque": "3 Nm (soft joint, UHMW must not cold-flow under the head)",
         "grip": "head 3.3 deep in a 90 deg countersink, 0.5 below the pad face"},
        {"id": "J06", "joint": "GN 7233 hinge brackets -> surround hinge block and leaf hinge block",
         "count": ("HINGE_GN7233_door_leaf",), "per": [("BHCS_M6x16_A4", 4)],
         "torque": "6 Nm, Loctite 243 (into tapped 6061)",
         "grip": "bracket s = 5 mm; 11 mm thread in the block"},
        {"id": "J07", "joint": "Stabilus 4486MD ball stud (own M8) -> leaf boss / surround bracket",
         "count": ("BALL_STUD",), "per": [], "torque": "15 Nm, Loctite 243 (Upfit p.57 M8 soft 6.8-20.5)",
         "grip": "M8 x 13 thread in a 14 deep tapped hole"},
        {"id": "J08", "joint": "AC-75-101-11 release handle -> release bracket plate (2x Dia 4.5 thru, "
                               "Southco p.317)", "count": ("handle_pan",),
         "per": [("BHCS_M4x12_A4", 2), ("NUT_M4_NYLOC_A4", 2), ("WASHER_M4_A4", 2)],
         "torque": "1.5 Nm (Southco AC actuators: <= 2 Nm)", "grip": "flange + 6 mm plate"},
        {"id": "J09", "joint": "AC-05-301-11 cable splitter -> release bracket plate",
         "count": ("CABLE_SPLITTER",),
         "per": [("BHCS_M4x12_A4", 2), ("NUT_M4_NYLOC_A4", 2), ("WASHER_M4_A4", 2)],
         "torque": "1.5 Nm", "grip": "verify the splitter's mounting-hole size on receipt (VR-01)"},
        {"id": "J10", "joint": "Ball plunger (own M8 body) -> plug-frame boss", "count": ("BALL_PLUNGER",),
         "per": [], "torque": "set to flush preload, Loctite 243", "grip": "M8 boss 22 deep"},
        {"id": "J11", "joint": "CHMSL M63319R -> hatch leaf (2x Dia 4.8 at 370)", "count": ("CHMSL",),
         "per": [("BHCS_M4x12_A4", 2)], "custom_per": [("POTTED_INSERT_M4_6061", 2)],
         "torque": "1.5 Nm", "grip": "lamp foot + potted 6061 insert"},
        {"id": "J12", "joint": "Glazing retainer -> hatch leaf (inside-glazed pane clamp)",
         "count": ("GLAZING_RETAINER",), "per": [("BHCS_M4x12_A4", retainer_n)],
         "custom_per": [("POTTED_INSERT_M4_6061", retainer_n)],
         "torque": "1.2 Nm (PC pane: clamp, do not crush)",
         "grip": f"retainer 5 + pane 5 on a 1 mm EPDM glazing gasket; {retainer_n} per window at <= 90 mm"},
        {"id": "J13", "joint": "CAGE rail -> module plug frame", "count": ("CAGE_RAIL",),
         "per": [("SHCS_M6x16_A4", 2)], "torque": "8 Nm, Tef-Gel", "grip": "rail 4 + 12 thread"},
        {"id": "J14", "joint": "TOOLBOX tub flange -> module plug frame", "count": ("TOOLBOX_TUB",),
         "per": [("BHCS_M5x10_A4", 10)], "torque": "2 Nm (thermoformed ABS flange)", "grip": "3 + 7"},
        {"id": "J15", "joint": "WINDOW pane -> plug-frame flange", "count": ("WINDOW_PANE",),
         "per": [], "tape": "glazing_tape", "torque": "-", "grip": "3M VHB 5952 perimeter, 12 mm"},
        {"id": "J16", "joint": "Bonded: socket frames, hatch surround, base rails, roof hardpoints, "
                               "leaf bosses/blocks, potted inserts", "count": 1, "per": [],
         "adhesive": True, "torque": "-", "grip": "0.25 mm bondline, glass-bead spacers"},
        {"id": "J17", "joint": "Press fits: MISUMI pins into module bosses, JBHC bushings into frame land",
         "count": ("LOCATING_PIN", "BUSHING"), "per": [], "torque": "-",
         "grip": "per MISUMI fits (pin m6 press, bushing p6 in H7)"},
    ]


def schedule(man=None):
    """Joint rows with resolved counts and fastener totals."""
    c = manifest_counts(man)
    rows, totals, custom = [], Counter(), Counter()
    for j in joints():
        cnt = j["count"]
        n = cnt if isinstance(cnt, int) else count_of(c, *cnt)
        for key, q in j.get("per", []):
            totals[key] += n * q
        for key, q in j.get("custom_per", []):
            custom[key] += n * q
        rows.append(dict(j, n=n))
    return rows, totals, custom


def window_tape_m(man=None) -> float:
    import side_socket as SS
    import geom as G
    c = manifest_counts(man)
    n = count_of(c, "WINDOW_PANE")
    hu, hv = SS.AU - G.PLUG_CLR - 5.5, SS.AV - G.PLUG_CLR - 5.5
    return round(n * _rr_perimeter(2 * hu, 2 * hv, max(SS.R0 - 10.0, 3.0)) / 1000 * 1.1, 2)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(HERE))
    rows, tot, cus = schedule()
    for r in rows:
        print(r["id"], r["n"], r["joint"][:60])
    print(dict(tot))
    print(dict(cus))
    print(bond_area_m2(), adhesive_cartridges(), window_tape_m())
