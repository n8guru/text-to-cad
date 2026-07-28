"""Deterministic checks for the provisional authoritative Step 6 shell."""

import json
from math import isclose
from pathlib import Path

from parameters import (
    DESIGN_DECISION,
    ESTIMATED,
    PLACEHOLDER_REQUIRING_SCAN,
    base_interface_keepout_depth,
    topper_base_outer_width,
    topper_overall_length,
    topper_silhouette_stations,
    value,
    wall_nominal_thickness,
)
from topper_envelope import (
    build_topper_engineered_subassembly,
    make_base_flange_references,
    make_engineered_shell,
    make_load_path_references,
    make_master_topper_envelope,
    make_shell_datums,
    make_shell_keepouts,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STYLE_PATH = (
    PROJECT_ROOT
    / "interchange/reference_only/blender_to_cad_style_selected.json"
)


def _close(actual: float, expected: float) -> None:
    assert isclose(actual, expected, abs_tol=1e-6), (actual, expected)


def run() -> None:
    selected = json.loads(STYLE_PATH.read_text(encoding="utf-8"))
    stations = value(topper_silhouette_stations)
    selected_station_tuples = tuple(
        (
            profile["x_mm"] / value(topper_overall_length),
            profile["points_mm"][4][2],
            2.0 * profile["points_mm"][1][1],
            2.0 * profile["points_mm"][2][1],
            2.0 * profile["points_mm"][3][1],
            profile["points_mm"][4][2] - profile["points_mm"][3][2],
        )
        for profile in selected["profiles"]
    )
    for actual, expected in zip(stations, selected_station_tuples):
        for actual_value, expected_value in zip(actual, expected):
            _close(actual_value, expected_value)
    assert topper_silhouette_stations.provenance == ESTIMATED

    envelope = make_master_topper_envelope()
    shell = make_engineered_shell()
    assert 0.0 < shell.volume < envelope.volume
    _close(shell.bounding_box().size.X, value(topper_overall_length))
    _close(shell.bounding_box().size.Y, value(topper_base_outer_width))
    assert wall_nominal_thickness.provenance == DESIGN_DECISION

    flanges = make_base_flange_references().children
    assert len(flanges) == 2
    assert {item.label for item in flanges} == {
        "BASE_FLANGE_DRIVER_PROVISIONAL",
        "BASE_FLANGE_PASSENGER_PROVISIONAL",
    }

    datums = make_shell_datums().children
    assert [datum.label for datum in datums] == [
        "DATUM_A_BED_RAIL_MOUNTING_PLANE_Z0",
        "DATUM_B_VEHICLE_CENTERLINE_Y0",
        "DATUM_C_REAR_CLOSURE_PLANE_MARKER",
    ]

    keepouts = make_shell_keepouts().children
    assert len(keepouts) == 2
    assert base_interface_keepout_depth.provenance == PLACEHOLDER_REQUIRING_SCAN
    assert all("KEEP_OUT" in keepout.label for keepout in keepouts)

    load_paths = make_load_path_references().children
    assert len(load_paths) == 2
    assert all(load_path.volume > 0.0 for load_path in load_paths)
    assert all("PROVISIONAL" in load_path.label for load_path in load_paths)

    labels = {child.label for child in build_topper_engineered_subassembly().children}
    assert labels == {
        "TOPPER_ENGINEERED_SHELL",
        "BASE_FLANGES",
        "SHELL_DATUMS",
        "SHELL_ENGINEERING_KEEP_OUTS",
        "STRUCTURAL_LOAD_PATH_REFERENCES",
    }


if __name__ == "__main__":
    run()
    print("STEP_6_ENGINEERED_SHELL_CHECKS_PASS")
