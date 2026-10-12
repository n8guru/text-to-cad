"""Actual lower-edge chord and matching opening checks; nominal CAD, not real fit.
The named 1299 mm tailgate estimate is drawing-derived bed width, not calibration.
No bbox-only or hundreds-of-mm acceptance tolerance is allowed for the bottom.
"""
import json
from pathlib import Path
from build123d import Box, Location, Pos
import geom as G
import hatch as H
import shell as S
import truck as T

def run():
    rows=[]
    def check(name, ok, **data):
        rows.append(dict(name=name, passed=bool(ok), **data))
    hp=G.hatch_plane()
    leaf=H.leaf_shell()
    cut=Location(hp).inverse()*S.hatch_cut()
    def chord(solid,y):
        # 0.01 mm slice immediately inside the actual bottom boundary.
        hit=solid & (Pos(0,y+.005,0)*Box(4000,.01,500))
        return hit.bounding_box().size.X if hit.volume>.001 else 0
    width=chord(leaf,-H.AY-G.H_LEAF_OUT)
    cw=chord(cut,-H.AY-G.H_SHELL_CUT)
    check("actual_leaf_lower_edge_equals_tailgate_estimate",
          abs(width-G.TAILGATE_WIDTH_ESTIMATE_MM)<.1,
          measured_mm=width,target_mm=G.TAILGATE_WIDTH_ESTIMATE_MM,
          slice_thickness_mm=.01, physical_measurement=False)
    check("shell_cut_lower_chord_follows_leaf_with_clearance",
          abs(cw-(width+2*(G.H_SHELL_CUT-G.H_LEAF_OUT)))<.1,
          measured_mm=cw,expected_mm=width+2*(G.H_SHELL_CUT-G.H_LEAF_OUT))
    # Uppermost strip cannot widen beyond the prior nominal 1052 mm budget.
    upper=leaf & (Pos(0,H.AY+G.H_LEAF_OUT-5,0)*Box(4000,10,500))
    check("upper_shoulders_stay_within_original_width_budget",
          upper.bounding_box().size.X <= H.W+2*G.H_LEAF_OUT+.01,
          upper_strip_mm=upper.bounding_box().size.X,budget_mm=H.W+2*G.H_LEAF_OUT)
    check("two_pane_leaf_single_valid_solid",leaf.is_valid and len(leaf.solids())==1,
          solids=len(leaf.solids()))
    bb=leaf.bounding_box()
    check("leaf_extrudes_in_correct_datum_direction",abs(bb.min.Z+H.LEAF_T)<.01 and abs(bb.max.Z)<.01,
          zmin_mm=bb.min.Z,zmax_mm=bb.max.Z)
    surround=H.hatch_surround()
    check("surround_single_valid_solid",surround.is_valid and len(surround.solids())==1,
          solids=len(surround.solids()))
    bead=H.seal_bead()
    check("open_bottom_seal_is_valid_bounded_U",bead.is_valid and 0<bead.volume<1e6
          and bead.bounding_box().size.Z<30 and (bead&H.bottom_run_cutter()).volume<.5,
          volume_mm3=bead.volume,height_mm=bead.bounding_box().size.Z)
    shell=S.shell(); tg=T.tailgate_lowered_keepout()
    for angle in sorted(set(range(0,int(H.OPEN_DEG)+1,10))|{H.OPEN_DEG}):
        local=H.leaf_location(float(angle))*leaf
        world=hp*local
        overlaps={"shell_mm3":(world&shell).volume,
                  "dry_surround_mm3":(local&surround).volume,
                  "lowered_gate_mm3":(world&tg).volume}
        check(f"widened_leaf_clearance_{angle:g}",all(v<.5 for v in overlaps.values()),**overlaps)
    out=Path(__file__).resolve().parents[1]/"out"/"checks_step30_hatch_width.json"
    out.write_text(json.dumps({"scope":"nominal_geometry_not_fitment","results":rows},indent=2)+"\n")
    for row in rows: print(row,flush=True)
    return rows

if __name__=="__main__":
    rows=run()
    failed=[r["name"] for r in rows if not r["passed"]]
    print("STEP30_HATCH_WIDTH_PASS" if not failed else "STEP30_HATCH_WIDTH_FAIL "+str(failed))
    raise SystemExit(bool(failed))
