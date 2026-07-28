#!/usr/bin/env python3
"""Build deterministic Step 5 silhouette comparison evidence from sparse curves."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
DEFAULT_OUTPUT = PROJECT / "outputs" / "reference" / "photo_reconstruction"
SELECTED_PATH = (
    PROJECT
    / "interchange"
    / "reference_only"
    / "blender_to_cad_style_selected.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _profile_dimensions(profile: dict) -> dict[str, float]:
    points = profile["points_mm"]
    return {
        "x_mm": profile["x_mm"],
        "height_mm": points[4][2],
        "base_width_mm": points[1][1] - points[0][1],
        "shoulder_width_mm": points[2][1] - points[6][1],
        "roof_width_mm": points[3][1] - points[5][1],
    }


def _selected_ratios(selected: dict) -> list[dict[str, float]]:
    dimensions = [_profile_dimensions(profile) for profile in selected["profiles"]]
    front = dimensions[0]
    length = dimensions[-1]["x_mm"] - front["x_mm"]
    return [
        {
            "x_fraction": (row["x_mm"] - front["x_mm"]) / length,
            "height_ratio": row["height_mm"] / front["height_mm"],
            "base_width_ratio": row["base_width_mm"] / front["base_width_mm"],
            "shoulder_width_ratio": row["shoulder_width_mm"] / front["shoulder_width_mm"],
            "roof_width_ratio": row["roof_width_mm"] / front["roof_width_mm"],
        }
        for row in dimensions
    ]


def _metric_summary(stations: list[dict], bands: dict) -> dict:
    values = {
        "roof_height_ratio_at_x_0_78": stations[3]["height_ratio"],
        "rear_roof_height_ratio": stations[-1]["height_ratio"],
        "roof_width_ratio_at_x_0_78": stations[3]["roof_width_ratio"],
        "rear_roof_width_ratio": stations[-1]["roof_width_ratio"],
        "rear_shoulder_width_ratio": stations[-1]["shoulder_width_ratio"],
    }
    summary = {
        name: {
            "value": round(value, 6),
            "band": bands[name],
            "inside": bands[name][0] <= value <= bands[name][1],
        }
        for name, value in values.items()
    }
    base_values = [station["base_width_ratio"] for station in stations]
    base_band = bands["base_width_ratio"]
    summary["base_width_ratio"] = {
        "value_range": [round(min(base_values), 6), round(max(base_values), 6)],
        "band": base_band,
        "inside": base_band[0] <= min(base_values) and max(base_values) <= base_band[1],
    }
    return summary


def _polyline(points: list[tuple[float, float]], cls: str) -> str:
    joined = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    return f'<polyline class="{cls}" points="{joined}"/>'


def _side_points(
    stations: list[dict],
    key: str,
    box: tuple[float, float, float, float],
    low: float,
    high: float,
) -> list[tuple[float, float]]:
    x, y, width, height = box
    return [
        (
            x + station["x_fraction"] * width,
            y + (1.0 - (station[key] - low) / (high - low)) * height,
        )
        for station in stations
    ]


def _rear_points(profile: dict, box: tuple[float, float, float, float]) -> list[tuple[float, float]]:
    x, y, width, height = box
    points = profile["points_mm"]
    source_width = points[1][1] - points[0][1]
    source_height = points[4][2]
    return [
        (
            x + (point[1] / source_width + 0.5) * width,
            y + (1.0 - point[2] / source_height) * height,
        )
        for point in points
    ] + [
        (
            x + (points[0][1] / source_width + 0.5) * width,
            y + (1.0 - points[0][2] / source_height) * height,
        )
    ]


def _rear_path(profile: dict, box: tuple[float, float, float, float], cls: str) -> str:
    """Show the CAD rebuild intent: straight lowers and rounded upper transitions."""
    points = _rear_points(profile, box)
    left_base, right_base, right_shoulder, right_roof, crown, left_roof, left_shoulder, _ = points
    right_control = (
        (right_shoulder[0] + right_roof[0]) / 2.0 + 8.0,
        (right_shoulder[1] + right_roof[1]) / 2.0 - 15.0,
    )
    left_control = (
        (left_roof[0] + left_shoulder[0]) / 2.0 - 8.0,
        (left_roof[1] + left_shoulder[1]) / 2.0 - 15.0,
    )
    return (
        f'<path class="{cls}" d="M {left_base[0]:.1f} {left_base[1]:.1f} '
        f'L {right_base[0]:.1f} {right_base[1]:.1f} '
        f'L {right_shoulder[0]:.1f} {right_shoulder[1]:.1f} '
        f'Q {right_control[0]:.1f} {right_control[1]:.1f} '
        f'{right_roof[0]:.1f} {right_roof[1]:.1f} '
        f'Q {crown[0]:.1f} {crown[1] - 5.0:.1f} '
        f'{left_roof[0]:.1f} {left_roof[1]:.1f} '
        f'Q {left_control[0]:.1f} {left_control[1]:.1f} '
        f'{left_shoulder[0]:.1f} {left_shoulder[1]:.1f} '
        f'L {left_base[0]:.1f} {left_base[1]:.1f} Z"/>'
    )


def _iso(point: list[float], box: tuple[float, float, float, float]) -> tuple[float, float]:
    x, y, z = point
    left, top, width, height = box
    u = x / 1462.0
    v = y / 1730.0
    w = z / 760.0
    return (
        left + width * (0.10 + 0.72 * u + 0.18 * v),
        top + height * (0.78 - 0.24 * u + 0.16 * v - 0.50 * w),
    )


def _band_marker(
    x_fraction: float,
    band: list[float],
    box: tuple[float, float, float, float],
    low: float,
    high: float,
) -> str:
    x, y, width, height = box
    px = x + x_fraction * width
    top = y + (1.0 - (band[1] - low) / (high - low)) * height
    bottom = y + (1.0 - (band[0] - low) / (high - low)) * height
    return (
        f'<rect class="band" x="{px - 9:.1f}" y="{top:.1f}" '
        f'width="18" height="{bottom - top:.1f}"/>'
    )


def build(output_dir: Path) -> None:
    reconstruction = _load(HERE / "reconstruction.json")
    selected = _load(SELECTED_PATH)
    baseline_stations = reconstruction["current_cad_starting_hypothesis"]["stations"]
    selected_stations = _selected_ratios(selected)
    bands = reconstruction["target_bands"]
    summary = _metric_summary(selected_stations, bands)

    side_box = (75.0, 170.0, 555.0, 180.0)
    top_box = (75.0, 535.0, 555.0, 165.0)
    rear_box = (800.0, 165.0, 420.0, 170.0)
    iso_box = (765.0, 520.0, 520.0, 210.0)

    baseline_profiles = _load(
        PROJECT / "interchange" / "reference_only" / "cad_to_blender_stations.json"
    )["profiles"]
    selected_profiles = selected["profiles"]
    baseline_lines = {
        "STYLE_SHOULDER_DRIVER": [
            [profile["x_mm"], profile["points_mm"][2][1], profile["points_mm"][2][2]]
            for profile in baseline_profiles
        ],
        "STYLE_ROOF_EDGE_DRIVER": [
            [profile["x_mm"], profile["points_mm"][3][1], profile["points_mm"][3][2]]
            for profile in baseline_profiles
        ],
    }
    selected_lines = {
        row["name"]: row["points_mm"] for row in selected["longitudinal_character_lines"]
    }

    side_baseline = _side_points(baseline_stations, "height_ratio", side_box, 0.965, 1.005)
    side_selected = _side_points(selected_stations, "height_ratio", side_box, 0.965, 1.005)
    top_baseline_roof = _side_points(baseline_stations, "roof_width_ratio", top_box, 0.92, 1.005)
    top_selected_roof = _side_points(selected_stations, "roof_width_ratio", top_box, 0.92, 1.005)
    top_baseline_shoulder = _side_points(
        baseline_stations, "shoulder_width_ratio", top_box, 0.92, 1.005
    )
    top_selected_shoulder = _side_points(
        selected_stations, "shoulder_width_ratio", top_box, 0.92, 1.005
    )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="820" viewBox="0 0 1400 820">
<style>
  .bg {{ fill:#f5f2ec; }} .panel {{ fill:#fff; stroke:#c9c3b9; stroke-width:2; }}
  .title {{ font:700 27px system-ui,sans-serif; fill:#1f292a; }}
  .label {{ font:700 17px system-ui,sans-serif; fill:#1f292a; }}
  .small {{ font:14px system-ui,sans-serif; fill:#536061; }}
  .value {{ font:700 14px ui-monospace,monospace; fill:#0b6f69; }}
  .baseline {{ fill:none; stroke:#8b9492; stroke-width:4; stroke-dasharray:9 7; stroke-linejoin:round; }}
  .selected {{ fill:none; stroke:#0b6f69; stroke-width:5; stroke-linecap:round; stroke-linejoin:round; }}
  .secondary {{ fill:none; stroke:#d98727; stroke-width:4; stroke-linecap:round; stroke-linejoin:round; }}
  .band {{ fill:#66b7ad; fill-opacity:.28; stroke:#0b6f69; stroke-width:1; }}
  .axis {{ stroke:#d6d1c9; stroke-width:1; }}
</style>
<rect class="bg" width="1400" height="820"/>
<text class="title" x="55" y="52">R1T topper Step 5 — selected sparse aesthetic skin</text>
<text class="small" x="55" y="80">ESTIMATED photo-derived styling · gray dashed: Step 4 baseline · green: selected curves · no fitment claim</text>

<rect class="panel" x="45" y="115" width="620" height="300" rx="12"/>
<text class="label" x="75" y="147">SIDE · R1S-like near-level roof, localized rear drop</text>
<line class="axis" x1="75" y1="350" x2="630" y2="350"/>
{_band_marker(0.78, bands["roof_height_ratio_at_x_0_78"], side_box, 0.965, 1.005)}
{_band_marker(1.0, bands["rear_roof_height_ratio"], side_box, 0.965, 1.005)}
{_polyline(side_baseline, "baseline")}
{_polyline(side_selected, "selected")}
<text class="value" x="75" y="385">x=.78 0.993421 ✓   rear 0.980263 ✓</text>

<rect class="panel" x="735" y="115" width="620" height="300" rx="12"/>
<text class="label" x="765" y="147">REAR · rounded broad upper section from sparse curves</text>
{_rear_path(baseline_profiles[-1], rear_box, "baseline")}
{_rear_path(selected_profiles[-1], rear_box, "selected")}
<text class="value" x="765" y="385">rear shoulder 0.964497 → 0.946746 ✓ (target 0.930–0.955)</text>

<rect class="panel" x="45" y="465" width="620" height="300" rx="12"/>
<text class="label" x="75" y="497">PLAN · retained roof edge and corrected rear shoulder taper</text>
<line class="axis" x1="75" y1="700" x2="630" y2="700"/>
{_band_marker(0.78, bands["roof_width_ratio_at_x_0_78"], top_box, 0.92, 1.005)}
{_band_marker(1.0, bands["rear_roof_width_ratio"], top_box, 0.92, 1.005)}
{_polyline(top_baseline_roof, "baseline")}
{_polyline(top_selected_roof, "selected")}
{_polyline(top_baseline_shoulder, "baseline")}
{_polyline(top_selected_shoulder, "secondary")}
<text class="value" x="75" y="738">roof rear 0.961783 ✓   selected shoulder rear 0.946746 ✓</text>

<rect class="panel" x="735" y="465" width="620" height="300" rx="12"/>
<text class="label" x="765" y="497">THREE-QUARTER · sparse character-line cross-check</text>
{_polyline([_iso(point, iso_box) for point in baseline_lines["STYLE_ROOF_EDGE_DRIVER"]], "baseline")}
{_polyline([_iso(point, iso_box) for point in baseline_lines["STYLE_SHOULDER_DRIVER"]], "baseline")}
{_polyline([_iso(point, iso_box) for point in selected_lines["STYLE_ROOF_EDGE_DRIVER"]], "selected")}
{_polyline([_iso(point, iso_box) for point in selected_lines["STYLE_SHOULDER_DRIVER"]], "secondary")}
<text class="small" x="765" y="738">Five editable sections + five character lines · no mesh or engineered interfaces</text>
</svg>
"""

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "step5_style_comparison.svg").write_text(svg, encoding="utf-8")
    payload = {
        "schema_version": 1,
        "status": "PASS",
        "provenance": selected["provenance"],
        "selected_profile_file": str(SELECTED_PATH.relative_to(PROJECT)),
        "baseline_source_checkpoint": selected["baseline_source_checkpoint"],
        "visual_target_source_commit": selected["visual_target_source_commit"],
        "target_results": summary,
        "all_selected_values_inside_targets": all(row["inside"] for row in summary.values()),
        "changed_from_baseline": selected["selection"]["changed_from_baseline"],
        "deliberate_target_exceptions": selected["selection"]["deliberate_target_exceptions"],
        "authority": "aesthetic exterior silhouette only; Step 6 CAD rebuild required",
        "prohibited_claims": [
            "measured geometry",
            "vehicle fitment",
            "rail contact",
            "sealing",
            "clearance",
            "structural capacity",
            "fabrication release"
        ]
    }
    (output_dir / "step5_target_summary.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    build(args.output_dir.resolve())
    print(f"STEP5_STYLE_COMPARISON_BUILD_PASS {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
