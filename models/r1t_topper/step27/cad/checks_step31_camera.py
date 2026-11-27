"""Step 31 focused checks: OEM camera sight lines through the topper, measured on the CAD solids.

    python step27/cad/checks_step31_camera.py   -> out/checks_step31_camera.json, exit 1 on FAIL

PASS = measured from the solids; OPEN = measured and recorded but NOT claimed; FAIL = defect.
Scope is nominal line-of-sight geometry against camera positions scaled off Rivian's Upfitting Guide
line drawing (camera.py). Nothing here claims image quality, field-of-view coverage, calibration,
Rivian software behaviour, FMVSS 111 compliance or fitment on a real truck.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build123d import Align, Box, Pos  # noqa: E402

import camera as C  # noqa: E402
import geom as G  # noqa: E402
import hatch as HA  # noqa: E402
import shell as SH  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "out" / "checks_step31_camera.json"
BED_VIEW_MIN = 0.70          # acceptance floor for the restored bed view at the nominal lens point


def run():
    rows = []

    def check(name, ok, state=None, **data):
        rows.append(dict(name=name, state=state or ("PASS" if ok else "FAIL"), **data))
        print(rows[-1], flush=True)

    bed = C.bed_floor_targets()
    fm = [p for _, p in C.fmvss_targets()]
    cam = "TRUCK_BED_CAMERA"
    rear = "REAR_SURROUND_VIEW_CAMERA"

    check("camera_positions_carry_source_and_band",
          all(c.get("source") and c.get("band") for c in C.CAMERAS.values()),
          cameras={k: {"xyz": v["xyz"], "band": v["band"], "source": v["source"]}
                   for k, v in C.CAMERAS.items()})

    import truck as TR
    from build123d import Vector
    lens_gap = TR.cab_keepout().distance_to(Vector(*C.CAMERAS[cam]["xyz"]))
    check("nominal_bed_camera_lens_lies_on_modelled_cab_back", lens_gap <= 3.0,
          lens_to_cab_keepout_mm=lens_gap,
          note="the lens is placed ON the side-photo cab model, not floating in front of it")

    # ---------------------------------------------------------------- the gap (pre-Step-31 shell)
    sl0 = C.SightLines(C.occluders(camera_tab=False))
    base_bed = C.measure(cam, bed, False, sl=sl0)
    base_fm = C.measure(cam, fm, False, sl=sl0)
    check("gap_measured_bed_camera_bed_view_baseline", base_bed["BLOCKED"] > 0,
          note="pre-Step-31 shell: the carbon front wall fills the bed camera's view of the bed",
          **base_bed)
    check("gap_measured_bed_camera_rear_view_baseline", base_fm["BLOCKED"] > 0,
          note="tailgate-down reverse role (UPFIT p.107) toward the S14.1.4 object positions",
          **base_fm)

    # ---------------------------------------------------------------- the provision
    sl1 = C.SightLines(C.occluders(camera_tab=True))
    new_bed = C.measure(cam, bed, True, sl=sl1)
    check("provision_restores_bed_view_at_nominal_lens",
          new_bed["visible_fraction"] >= BED_VIEW_MIN
          and new_bed["visible_fraction"] > base_bed["visible_fraction"]
          and set(new_bed["blocked_by"]) <= {"SHELL_CARBON_SANDWICH"},
          floor=BED_VIEW_MIN, baseline_visible_fraction=base_bed["visible_fraction"], **new_bed)
    corners = []
    for xyz in C.band_corners(cam):
        b0 = C.measure(cam, bed, False, xyz=xyz, sl=sl0)["visible_fraction"]
        b1 = C.measure(cam, bed, True, xyz=xyz, sl=sl1)["visible_fraction"]
        corners.append({"xyz": list(xyz), "baseline": b0, "provision": b1})
    check("provision_improves_bed_view_across_lens_position_band",
          all(c["provision"] > c["baseline"] for c in corners),
          min_provision=min(c["provision"] for c in corners), corners=corners)
    new_fm = C.measure(cam, fm, True, sl=sl1)
    check("provision_restores_bed_camera_rear_view_tailgate_down_at_nominal_lens",
          new_fm["visible_fraction"] == 1.0 and not new_fm["blocked_by"]
          and base_fm["visible_fraction"] < 1.0,
          note=("tailgate-down reverse role (UPFIT p.107), hatch CLOSED: every sampled sight line "
                "to the 21 S14.1.4 axis points passes only through glazing -- the front pane "
                "(camera tab + raked rear-view slot, shell.REAR_VIEW_SLOT) and the one-piece "
                "hatch pane (hatch.WIN, no mullion). Line of sight only, not the S14.1 "
                "photometric test, not image quality."),
          baseline_visible_fraction=base_fm["visible_fraction"], **new_fm)
    rcorners = []
    for xyz in C.band_corners(cam):
        r0 = C.measure(cam, fm, False, xyz=xyz, sl=sl0)["visible_fraction"]
        r1 = C.measure(cam, fm, True, xyz=xyz, sl=sl1)
        rcorners.append({"xyz": list(xyz), "baseline": r0, "provision": r1["visible_fraction"],
                         "blocked_by": r1["blocked_by"]})
    check("rear_view_lens_band_sensitivity_recorded", True, state="OPEN",
          corners=rcorners,
          note=("NOT claimed beyond the nominal lens: the lens position is scaled off the p.49 "
                "drawing (camera.py band). A lens higher than the modelled cab (z 450 corners) "
                "looks over the slot into the roof roll; a lower lens (z 405 corners) sends the "
                "steepest centre/near rays under the hatch pane's bottom chord (T-handle zone). Closes when the lens is tape-measured "
                "(Step 22) and this check is re-run at the measured point."))

    # ---------------------------------------------------------------- the camera the topper must never touch
    worst = []
    for deg in (0.0, float(HA.OPEN_DEG)):
        slh = sl1 if deg == 0.0 else C.SightLines(C.occluders(camera_tab=True, hatch_deg=deg))
        for xyz in [C.CAMERAS[rear]["xyz"]] + C.band_corners(rear):
            r = C.measure(rear, fm, True, xyz=xyz, sl=slh)
            worst.append({"hatch_deg": deg, "xyz": list(xyz), "visible_fraction":
                          r["visible_fraction"], "blocked_by": r["blocked_by"]})
    check("rear_surround_camera_sightlines_unoccluded_hatch_closed_and_open",
          all(w["visible_fraction"] == 1.0 for w in worst), cases=worst,
          note="line of sight to all 21 S14.1.4 object points; not the S14.1 photometric test")

    # ---------------------------------------------------------------- geometry of the provision
    sh = SH.shell(True)
    check("shell_single_valid_solid", sh.is_valid and len(sh.solids()) == 1,
          solids=len(sh.solids()))
    tab = SH.CAMERA_TAB
    x0, w = G.S["x0"], G.WALL
    flat_top_outer = G.S["roof_z"] - G.S["front_r"]          # start of the R50 front roll
    flat_top_inner = G.S["roof_z"] - w - (G.S["front_r"] - w)  # start of the R28 inner roll

    def header_bottom(x):
        """Lowest shell material on the centreline above the tab, in a 1 mm slab at x."""
        # y = 150: inside the 440 mm tab, outboard of the 160 mm rear-view slot (own check below)
        probe = Pos(x, 150.0, (tab["z_bot"] + G.S["roof_z"]) / 2 + 40) * Box(
            1.0, 20.0, G.S["roof_z"] - tab["z_bot"] + 40, align=(Align.CENTER,) * 3)
        hit = sh & probe
        return hit.bounding_box().min.Z if hit.volume > 1e-3 else None

    outer = header_bottom(x0 + 0.5)
    inner = header_bottom(x0 + w - 0.5)
    check("camera_tab_raked_along_sight_line_and_on_flat_front_face",
          outer is not None and inner is not None and outer > inner
          and abs((outer - inner) / (w - 1.0) - tab["rake"]) < 0.02
          and outer <= flat_top_outer,
          header_bottom_outer_mm=outer, header_bottom_inner_mm=inner,
          rake_measured=None if outer is None else (outer - inner) / (w - 1.0),
          flat_face_top_outer_mm=flat_top_outer)
    pane = SH.front_pane(True)
    pb = pane.bounding_box()
    slot = SH.REAR_VIEW_SLOT
    tongue_hw, _, tongue_top = SH._rear_view_tongue_bounds()
    above = pane & (Pos(0, 0, flat_top_inner + 500.0) * Box(
        200.0, 4000.0, 1000.0, align=(Align.CENTER,) * 3))
    above_in_tongue = above & (Pos(0, 0, flat_top_inner + 500.0) * Box(
        200.0, 2 * tongue_hw + 0.2, 1000.0, align=(Align.CENTER,) * 3))
    check("one_piece_pane_bonds_below_inner_roof_roll_except_pocketed_tongue_and_clears_shell",
          pane.is_valid and len(pane.solids()) == 1 and (pane & sh).volume < 0.5
          and abs(pb.min.X - (x0 + w)) < 1e-6 and pb.max.Z <= tongue_top + 1e-6
          and abs(above.volume - above_in_tongue.volume) < 1.0,
          pane_top_mm=pb.max.Z, tongue_half_width_mm=tongue_hw, inner_roll_start_mm=flat_top_inner,
          pane_shell_overlap_mm3=round((pane & sh).volume, 2), pane_bbox=[tuple(round(v, 3) for v in pb.min), tuple(round(v, 3) for v in pb.max)],
          note="only the rear-view tongue rises above the inner roll start; it sits in "
               "rear_view_pocket (0.5 mm clear) and bonds to the slot's cut face")
    roof_top = sh.bounding_box().max.Z
    slot_cut = SH._raked_cut(slot)
    sc = slot_cut.bounding_box()
    check("rear_view_slot_narrow_raked_and_roof_top_plane_untouched",
          abs(roof_top - G.S["roof_z"]) < 0.5 and sc.max.Z < G.S["roof_z"] - 25.0
          and slot["w"] <= 200.0 and abs(slot["rake"] - 0.15) < 1e-9,
          roof_top_mm=roof_top, roof_z=G.S["roof_z"], slot_cut_top_mm=sc.max.Z,
          slot_w_mm=slot["w"], rake=slot["rake"],
          note="the slot notches the front roll below the roof plane; the R1S-like top plane "
               "(charter) is not cut")
    leaf = HA.leaf_shell()
    arm_ok = []
    for x in HA.LATCH_XS:
        ab = HA.leaf_striker_arm(x).bounding_box()
        foot = Pos((ab.min.X + ab.max.X) / 2, (ab.min.Y + ab.max.Y) / 2, -HA.LEAF_T + 0.5) * Box(
            ab.max.X - ab.min.X, ab.max.Y - ab.min.Y, 1.0, align=(Align.CENTER,) * 3)
        arm_ok.append(round((foot & leaf).volume / foot.volume, 4))
    th = HA.hw.d("t_handle")
    hole_top = -HA.AY + 14.0 + th["escutcheon_dia"] / 2 + 0.3
    hp, hr = HA.glazing_pane(), HA.glazing_retainer()
    check("hatch_one_piece_pane_keeps_striker_arms_on_carbon_and_clears_t_handle",
          len([c for c in HA.hatch_leaf(0.0).children if "GLAZING_PANE" in (c.label or "")]) == 1
          and all(a > 0.999 for a in arm_ok) and hp.bounding_box().min.Y > hole_top
          and hr.bounding_box().min.Y > hole_top
          and HA.WIN["y_bot"] - HA.WIN["y_clip"] >= 10.0 and leaf.is_valid
          and len(leaf.solids()) == 1,
          striker_arm_footprint_on_carbon=arm_ok, pane_bottom_mm=hp.bounding_box().min.Y,
          escutcheon_top_mm=hole_top, bottom_overlap_mm=HA.WIN["y_bot"] - HA.WIN["y_clip"],
          leaf_mass_kg=round(HA.leaf_mass_kg(), 4))
    lens = C.CAMERAS[cam]
    gaps = [min(abs(x0 - xyz[0]), math.inf) for xyz in [lens["xyz"]] + C.band_corners(cam)]
    check("optical_only_no_part_forward_of_front_face_no_camera_or_harness_change",
          SH._camera_tab_cut() is not None and min(gaps) > 0
          and all(s.bounding_box().min.X >= x0 - 1e-6 for _, s in C.occluders(True)),
          min_lens_to_wall_mm=min(gaps),
          note="the provision is a window: nothing is added at or forward of the cab back, the "
               "camera is not moved and no wire is touched (UPFIT p.108)")
    removed = SH.shell(False).volume - sh.volume
    added = pane.volume - SH.front_pane(False).volume
    check("carbon_removed_and_pc_added_recorded", removed > 0 and added > 0,
          carbon_removed_mm3=round(removed, 1), carbon_removed_kg=round(removed / w * 5.8e-6, 4),
          pane_added_mm3=round(added, 1))

    OUT.parent.mkdir(exist_ok=True)
    n = {s: sum(r["state"] == s for r in rows) for s in ("PASS", "FAIL", "OPEN")}
    OUT.write_text(json.dumps({"scope": "nominal_line_of_sight_not_image_quality_or_fitment",
                               "counts": n, "results": rows}, indent=2, default=str) + "\n")
    return rows


if __name__ == "__main__":
    rows = run()
    failed = [r["name"] for r in rows if r["state"] == "FAIL"]
    print("STEP31_CAMERA_PASS" if not failed else "STEP31_CAMERA_FAIL " + str(failed))
    raise SystemExit(bool(failed))
