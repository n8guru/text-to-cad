#!/usr/bin/env python3
"""Generate source-free review linework for the R1T topper photo reconstruction."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
DEFAULT_OUTPUT = HERE.parents[1] / "outputs" / "reference" / "photo_reconstruction"


def _load(name: str) -> dict:
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def _points(points: list[list[float]], box: tuple[float, float, float, float]) -> str:
    x, y, width, height = box
    return " ".join(
        f"{x + u * width:.1f},{y + v * height:.1f}" for u, v in points
    )


def _line(points: list[list[float]], box: tuple[float, float, float, float], cls: str) -> str:
    return f'<polyline class="{cls}" points="{_points(points, box)}"/>'


def _candidate_points(
    stations: list[dict],
    key: str,
    value_low: float = 0.92,
    value_high: float = 1.01,
) -> list[list[float]]:
    """Map ratio values to the same fixed vertical scale used by target bands."""
    return [
        [
            station["x_fraction"],
            1.0 - (station[key] - value_low) / (value_high - value_low),
        ]
        for station in stations
    ]


def _band_rect(
    x_fraction: float,
    band: list[float],
    box: tuple[float, float, float, float],
    value_low: float = 0.92,
    value_high: float = 1.01,
) -> str:
    x, y, width, height = box
    px = x + x_fraction * width
    top = y + (1.0 - (band[1] - value_low) / (value_high - value_low)) * height
    bottom = y + (1.0 - (band[0] - value_low) / (value_high - value_low)) * height
    return (
        f'<rect class="band" x="{px - 10:.1f}" y="{top:.1f}" '
        f'width="20" height="{bottom - top:.1f}"/>'
    )


def build(output_dir: Path) -> None:
    observations = _load("observations.json")["observations"]
    reconstruction = _load("reconstruction.json")
    sources = _load("sources.json")["sources"]
    by_id = {item["id"]: item for item in observations}
    bands = reconstruction["target_bands"]
    stations = reconstruction["current_cad_starting_hypothesis"]["stations"]

    side_box = (70.0, 150.0, 560.0, 210.0)
    rear_box = (770.0, 150.0, 500.0, 210.0)
    plan_box = (70.0, 530.0, 560.0, 190.0)
    perspective_box = (770.0, 530.0, 500.0, 190.0)
    side = by_id["R1S_SIDE_ROOF"]["landmarks"]
    rear = by_id["R1S_FRONT_REAR_UPPER"]["landmarks"]
    photo = by_id["R1S_PHOTO_THREE_QUARTER"]["landmarks"]

    candidate_height = _candidate_points(stations, "height_ratio")
    candidate_roof = _candidate_points(stations, "roof_width_ratio")

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="820" viewBox="0 0 1400 820">
<style>
  .bg {{ fill:#f6f3ed; }} .panel {{ fill:#fff; stroke:#c8c1b5; stroke-width:2; }}
  .title {{ font:700 28px system-ui,sans-serif; fill:#202728; }}
  .label {{ font:700 17px system-ui,sans-serif; fill:#202728; }}
  .small {{ font:14px system-ui,sans-serif; fill:#4c5859; }}
  .source {{ fill:none; stroke:#8c9694; stroke-width:4; stroke-linecap:round; stroke-linejoin:round; }}
  .candidate {{ fill:none; stroke:#0b6f69; stroke-width:5; stroke-linecap:round; stroke-linejoin:round; }}
  .secondary {{ fill:none; stroke:#d8892b; stroke-width:4; stroke-dasharray:9 7; stroke-linecap:round; }}
  .band {{ fill:#67b8ae; fill-opacity:.28; stroke:#0b6f69; stroke-width:1; }}
  .axis {{ stroke:#d5d0c8; stroke-width:1; }}
</style>
<rect class="bg" width="1400" height="820"/>
<text class="title" x="70" y="54">R1T topper — photo-derived multi-view reconstruction targets</text>
<text class="small" x="70" y="82">Normalized visual evidence only · no source rasters redistributed · no fitment or metric claim</text>

<rect class="panel" x="45" y="105" width="610" height="300" rx="12"/>
<text class="label" x="70" y="137">SIDE · roof continuity and localized rear drop</text>
<line class="axis" x1="70" y1="360" x2="630" y2="360"/>
{_line(side["roof_outer"], side_box, "source")}
{_line(side["upper_shoulder"], side_box, "secondary")}
{_line(candidate_height, side_box, "candidate")}
{_band_rect(0.78, bands["roof_height_ratio_at_x_0_78"], side_box)}
{_band_rect(1.00, bands["rear_roof_height_ratio"], side_box)}
<text class="small" x="70" y="388">gray: unregistered image-space trace · green/bands: fixed ratio scale · amber: shoulder cue</text>

<rect class="panel" x="745" y="105" width="610" height="300" rx="12"/>
<text class="label" x="770" y="137">REAR · broad crown, eased shoulders, continuous corners</text>
{_line(rear["rear_roof_outer"], rear_box, "source")}
{_line(rear["rear_glass_outer"], rear_box, "secondary")}
<path class="candidate" d="M 845 352 Q 805 260 850 190 Q 1020 145 1190 190 Q 1235 260 1195 352"/>
<text class="small" x="770" y="388">rear styling target remains broad; rounded transitions are required, planar chamfers are not</text>

<rect class="panel" x="45" y="485" width="610" height="270" rx="12"/>
<text class="label" x="70" y="517">PLAN · roof-width retention before rear-corner taper</text>
<line class="axis" x1="70" y1="720" x2="630" y2="720"/>
{_line(candidate_roof, plan_box, "candidate")}
{_band_rect(0.78, bands["roof_width_ratio_at_x_0_78"], plan_box)}
{_band_rect(1.00, bands["rear_roof_width_ratio"], plan_box)}
<text class="small" x="70" y="744">target: almost parallel through x=0.78, then controlled narrowing to 0.950–0.975</text>

<rect class="panel" x="745" y="485" width="610" height="270" rx="12"/>
<text class="label" x="770" y="517">THREE-QUARTER · qualitative perspective cross-check</text>
{_line(photo["roof_highlight"], perspective_box, "source")}
{_line(photo["shoulder_highlight"], perspective_box, "secondary")}
{_line(photo["rear_corner"], perspective_box, "candidate")}
<text class="small" x="770" y="744">foreshortening is not calibrated; this panel cannot set width, length, or station position</text>
</svg>
"""

    height_078 = stations[3]["height_ratio"]
    height_rear = stations[-1]["height_ratio"]
    roof_078 = stations[3]["roof_width_ratio"]
    roof_rear = stations[-1]["roof_width_ratio"]
    shoulder_rear = stations[-1]["shoulder_width_ratio"]
    base_values = [station["base_width_ratio"] for station in stations]

    checks = {
        "source_count": len(sources),
        "reproducible_source_count": sum("asset_url" in source for source in sources),
        "view_coverage": sorted(
            {view for source in sources for view in source.get("view", [])}
        ),
        "current_hypothesis": {
            "roof_height_ratio_at_x_0_78": {
                "value": height_078,
                "band": bands["roof_height_ratio_at_x_0_78"],
                "inside": bands["roof_height_ratio_at_x_0_78"][0] <= height_078 <= bands["roof_height_ratio_at_x_0_78"][1]
            },
            "rear_roof_height_ratio": {
                "value": height_rear,
                "band": bands["rear_roof_height_ratio"],
                "inside": bands["rear_roof_height_ratio"][0] <= height_rear <= bands["rear_roof_height_ratio"][1]
            },
            "roof_width_ratio_at_x_0_78": {
                "value": roof_078,
                "band": bands["roof_width_ratio_at_x_0_78"],
                "inside": bands["roof_width_ratio_at_x_0_78"][0] <= roof_078 <= bands["roof_width_ratio_at_x_0_78"][1]
            },
            "rear_roof_width_ratio": {
                "value": roof_rear,
                "band": bands["rear_roof_width_ratio"],
                "inside": bands["rear_roof_width_ratio"][0] <= roof_rear <= bands["rear_roof_width_ratio"][1]
            },
            "rear_shoulder_width_ratio": {
                "value": shoulder_rear,
                "band": bands["rear_shoulder_width_ratio"],
                "inside": bands["rear_shoulder_width_ratio"][0] <= shoulder_rear <= bands["rear_shoulder_width_ratio"][1]
            },
            "base_width_ratio": {
                "value_range": [min(base_values), max(base_values)],
                "band": bands["base_width_ratio"],
                "inside": (
                    bands["base_width_ratio"][0] <= min(base_values)
                    and max(base_values) <= bands["base_width_ratio"][1]
                )
            }
        },
        "all_current_hypothesis_values_inside_targets": True,
        "authority": reconstruction["authority"],
        "warning": "Passing target bands does not accept the aesthetic skin; Step 5 comparison is still required."
    }
    checks["all_current_hypothesis_values_inside_targets"] = all(
        item["inside"] for item in checks["current_hypothesis"].values()
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "multi_view_reconstruction.svg").write_text(svg, encoding="utf-8")
    (output_dir / "target_summary.json").write_text(
        json.dumps(checks, indent=2) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    build(args.output_dir.resolve())
    print(f"PHOTO_RECONSTRUCTION_BUILD_PASS {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
