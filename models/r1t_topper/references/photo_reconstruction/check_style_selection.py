#!/usr/bin/env python3
"""Deterministic acceptance checks for the Step 5 sparse styling selection."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from build_style_comparison import _metric_summary, _selected_ratios


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
OUTPUT = PROJECT / "outputs" / "reference" / "photo_reconstruction"
SELECTED = (
    PROJECT
    / "interchange"
    / "reference_only"
    / "blender_to_cad_style_selected.json"
)
BASELINE = (
    PROJECT / "interchange" / "reference_only" / "cad_to_blender_stations.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run() -> None:
    reconstruction = _load(HERE / "reconstruction.json")
    selected = _load(SELECTED)
    baseline = _load(BASELINE)

    assert selected["schema"] == baseline["schema"] == "r1t-topper-sparse-sections-v1"
    assert selected["status"] == "ESTIMATED_PHOTO_DERIVED_STYLE"
    assert selected["provenance"] == "ESTIMATED"
    assert selected["units"] == baseline["units"] == "mm"
    assert selected["axes"] == baseline["axes"]
    assert selected["origin"] == baseline["origin"]
    assert selected["visual_target_source_commit"] == (
        "6bdffc9d243200e25a148173e72062b86763219f"
    )
    assert selected["selection"]["deliberate_target_exceptions"] == []

    profiles = selected["profiles"]
    baseline_profiles = baseline["profiles"]
    assert len(profiles) == len(baseline_profiles) == 5
    assert [row["x_mm"] for row in profiles] == [0.0, 321.64, 760.24, 1140.36, 1462.0]
    assert all(row["closed"] for row in profiles)
    assert all(len(row["points_mm"]) == 7 for row in profiles)
    for profile in profiles:
        assert profile["name"].startswith("STYLE_STATION_")
        assert all(point[0] == profile["x_mm"] for point in profile["points_mm"])
        points = profile["points_mm"]
        assert points[0][1] == -points[1][1] and points[0][2] == points[1][2] == 0.0
        assert points[2][1] == -points[6][1] and points[2][2] == points[6][2]
        assert points[3][1] == -points[5][1] and points[3][2] == points[5][2]
        assert points[4][1] == 0.0

    # The proposal is deliberately minimal: all 34 other sparse profile
    # coordinates remain byte-equivalent numerically; only the symmetric rear
    # shoulder Y pair changes from +/-815 mm to +/-800 mm.
    changed = []
    for profile_index, (before, after) in enumerate(zip(baseline_profiles, profiles)):
        for point_index, (old_point, new_point) in enumerate(
            zip(before["points_mm"], after["points_mm"])
        ):
            for axis, (old, new) in enumerate(zip(old_point, new_point)):
                if old != new:
                    changed.append((profile_index, point_index, axis, old, new))
    assert changed == [
        (4, 2, 1, 815.0, 800.0),
        (4, 6, 1, -815.0, -800.0),
    ]

    character_lines = selected["longitudinal_character_lines"]
    assert {row["name"] for row in character_lines} == {
        "STYLE_CROWN",
        "STYLE_ROOF_EDGE_DRIVER",
        "STYLE_ROOF_EDGE_PASSENGER",
        "STYLE_SHOULDER_DRIVER",
        "STYLE_SHOULDER_PASSENGER",
    }
    assert all(len(row["points_mm"]) == 5 for row in character_lines)

    ratios = _selected_ratios(selected)
    summary = _metric_summary(ratios, reconstruction["target_bands"])
    assert all(row["inside"] for row in summary.values())
    assert summary["rear_shoulder_width_ratio"]["value"] == 0.946746
    assert ratios[3]["shoulder_width_ratio"] > ratios[4]["shoulder_width_ratio"]

    boundary = " ".join(selected["authority_boundary"]).lower()
    assert "aesthetic exterior silhouette only" in boundary
    assert "step 6" in boundary
    assert "dense mesh-to-step conversion is prohibited" in boundary
    assert "does not imply rail contact" in boundary
    encoded = json.dumps(selected).lower()
    assert '"mesh"' not in encoded

    required = [
        OUTPUT / "step5_style_comparison.svg",
        OUTPUT / "step5_target_summary.json",
    ]
    assert all(path.is_file() for path in required)
    committed_summary = _load(required[1])
    assert committed_summary["status"] == "PASS"
    assert committed_summary["provenance"] == "ESTIMATED"
    assert committed_summary["all_selected_values_inside_targets"] is True
    assert committed_summary["deliberate_target_exceptions"] == []
    assert committed_summary["target_results"] == summary

    with tempfile.TemporaryDirectory() as temp_dir:
        subprocess.run(
            [
                sys.executable,
                str(HERE / "build_style_comparison.py"),
                "--output-dir",
                temp_dir,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        for committed in required:
            rebuilt = Path(temp_dir) / committed.name
            assert _digest(committed) == _digest(rebuilt), committed.name


if __name__ == "__main__":
    run()
    print("STEP5_STYLE_SELECTION_CHECKS_PASS")
