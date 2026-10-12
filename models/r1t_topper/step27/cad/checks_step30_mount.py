"""Step30 solid checks: C-jaws wrap a bridge in the actual four-foot load path.
Run with the existing build123d environment. These prove nominal CAD geometry,
NOT OEM compatibility, preload, stress, pad force or physical retention ratings.
"""
import json
from pathlib import Path
from build123d import Pos
import mounts as M


def run():
    bridge = M.port_pins_local()[0]
    body = M.body_local()
    results = []
    def check(name, ok, **evidence):
        results.append(dict(name=name, passed=bool(ok), **evidence))
        assert ok, results[-1]
    check("continuous_reference_bridge", len(M.port_pins_local()) == 1 and
          len(bridge.solids()) == 1 and bridge.is_valid,
          provisional=True, length_mm=bridge.bounding_box().size.X)
    check("body_single_solid", body.is_valid and len(body.solids()) == 1)
    for angle in sorted(set(M.SWEEP_DEG)):
        jaw = M.slider_local(angle)
        clash = (jaw & bridge).volume
        body_clash = (jaw & body).volume
        check(f"nominal_motion_{angle:g}", jaw.is_valid and len(jaw.solids()) == 1
              and clash < 1e-6 and body_clash < 1e-6
              and (jaw - M.port_recess_local()).volume < 1e-6,
              bridge_interference_mm3=clash, body_interference_mm3=body_clash)
    for angle in (0.0, M.STAGE1_DEG):
        jaw = M.slider_local(angle)
        catch = ((Pos(0, 0, 0.5) * jaw) & bridge).volume
        upper = jaw.bounding_box().max.Z > bridge.bounding_box().max.Z
        lower = jaw.bounding_box().min.Z < bridge.bounding_box().min.Z
        check(f"captured_against_uplift_{angle:g}", catch > 1.0 and upper and lower,
              virtual_half_mm_uplift_overlap_mm3=catch,
              wraps_above_and_below=upper and lower)
    released = M.slider_local(M.OPEN_DEG)
    for z in range(0, 41):
        overlap = ((Pos(0, 0, z) * released) & bridge).volume
        body_overlap = ((Pos(0, 0, z) * body) & bridge).volume
        check(f"released_lift_{z}", overlap < 1e-6 and body_overlap < 1e-6,
              hook_interference_mm3=overlap, body_interference_mm3=body_overlap)
    for x, y in M.stations():
        loc = M.station_loc(x, y)
        foot = M.port_station(x, y)
        actual = next(p for p in foot if p.label == "PLF_HOOK_SLIDER_17_4PH")
        wanted = loc * M.slider_local(0)
        delta = (actual - wanted).volume + (wanted - actual).volume
        check(f"primary_assembly_uses_wrap_{x:g}_{y:g}", delta < 1e-6,
              symmetric_difference_mm3=delta)
    return results

if __name__ == "__main__":
    results = run()
    out = Path(__file__).resolve().parents[1] / "out" / "checks_step30_mount.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"scope": "provisional_nominal_geometry_only", "results": results}, indent=2) + "\n")
    print(f"STEP30_MOUNT_PASS {len(results)} solid checks; no OEM fit or load rating asserted")
