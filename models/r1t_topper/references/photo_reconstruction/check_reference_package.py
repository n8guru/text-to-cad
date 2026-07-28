#!/usr/bin/env python3
"""Deterministic checks for the photo-derived reconstruction package."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUTPUT = HERE.parents[1] / "outputs" / "reference" / "photo_reconstruction"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run() -> None:
    sources = _load(HERE / "sources.json")
    observations = _load(HERE / "observations.json")
    reconstruction = _load(HERE / "reconstruction.json")

    assert sources["schema_version"] == 1
    assert observations["schema_version"] == 1
    assert reconstruction["schema_version"] == 1
    assert sources["policy"]["redistribute_source_rasters"] is False

    source_rows = sources["sources"]
    source_ids = {source["id"] for source in source_rows}
    assert len(source_ids) == len(source_rows)
    reproducible = [source for source in source_rows if "asset_url" in source]
    assert len(reproducible) >= 5
    assert all(len(source["asset_sha256"]) == 64 for source in reproducible)
    assert all(source["redistribution"].startswith("remote reference") for source in reproducible)
    views = {view for source in source_rows for view in source.get("view", [])}
    assert {"front_orthographic", "rear_orthographic", "driver_side_orthographic"} <= views
    assert "front_driver_three_quarter_perspective" in views
    assert "rear_bed_perspective" in views

    observation_rows = observations["observations"]
    assert len(observation_rows) >= 5
    assert all(row["source_id"] in source_ids for row in observation_rows)
    assert {row["view_class"] for row in observation_rows} == {"orthographic", "perspective"}
    for row in observation_rows:
        assert len(row["crop_px"]) == 4
        assert row["uncertainty"]
        for points in row["landmarks"].values():
            assert len(points) >= 2
            assert all(0.0 <= coordinate <= 1.0 for point in points for coordinate in point)
    perspective_text = " ".join(
        phrase
        for row in observation_rows
        if row["view_class"] == "perspective"
        for phrase in row["interpretation"]
    ).lower()
    assert "cannot set rail width" in perspective_text
    assert "prohibits direct length or width ratios" in perspective_text

    bands = reconstruction["target_bands"]
    assert all(0.0 < low <= high <= 1.01 for low, high in bands.values())
    assert bands["roof_height_ratio_at_x_0_78"][0] > bands["rear_roof_height_ratio"][0]
    assert bands["roof_width_ratio_at_x_0_78"][0] > bands["rear_roof_width_ratio"][0]
    assert "CAD remains authoritative" in reconstruction["authority"]

    hypothesis = reconstruction["current_cad_starting_hypothesis"]
    assert "not an accepted aesthetic skin" in hypothesis["status"]
    stations = hypothesis["stations"]
    assert [station["x_fraction"] for station in stations] == [0.0, 0.22, 0.52, 0.78, 1.0]
    assert all(station["base_width_ratio"] == 1.0 for station in stations)
    assert all(
        left["height_ratio"] >= right["height_ratio"]
        and left["roof_width_ratio"] >= right["roof_width_ratio"]
        for left, right in zip(stations, stations[1:])
    )
    assert any("ESTIMATED" in item for item in reconstruction["step_5_acceptance_inputs"])
    assert any("do not alter fitment" in item for item in reconstruction["step_5_acceptance_inputs"])

    required_outputs = [
        OUTPUT / "multi_view_reconstruction.svg",
        OUTPUT / "target_summary.json",
    ]
    assert all(path.is_file() for path in required_outputs)
    summary = _load(required_outputs[1])
    # The package is allowed to expose a mismatch in the starting surrogate;
    # Step 4 records targets and Step 5 resolves them. At this checkpoint the
    # only deliberate mismatch is the too-broad rear shoulder.
    assert summary["all_current_hypothesis_values_inside_targets"] is False
    outside = {
        name
        for name, result in summary["current_hypothesis"].items()
        if not result["inside"]
    }
    assert outside == {"rear_shoulder_width_ratio"}
    assert summary["reproducible_source_count"] >= 5
    assert "does not accept the aesthetic skin" in summary["warning"]

    with tempfile.TemporaryDirectory() as temp_dir:
        subprocess.run(
            [
                sys.executable,
                str(HERE / "build_reference_package.py"),
                "--output-dir",
                temp_dir,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        regenerated = Path(temp_dir)
        for committed in required_outputs:
            rebuilt = regenerated / committed.name
            assert _digest(committed) == _digest(rebuilt), committed.name


if __name__ == "__main__":
    run()
    print("PHOTO_RECONSTRUCTION_REFERENCE_CHECKS_PASS")
