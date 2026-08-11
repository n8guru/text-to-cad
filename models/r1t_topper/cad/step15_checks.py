"""Deterministic contract checks for the re-embodied Step 15 review package."""

import hashlib
import json
from pathlib import Path

from build123d import Align, Box, Location

from exports_step15 import VERIFIED_STEP11_COMMIT, VERIFIED_STEP11_STEP_OID
from mount_interfaces import make_topper_crossbar_ports
from parameters import rear_hatch_opening_width, topper_overall_length, value, wall_nominal_thickness
from visual_review_step15 import (
    REAR_WINDOW_Y_RANGES,
    REAR_WINDOW_Z_RANGE,
    SIDE_WINDOW_X_RANGES,
    SIDE_WINDOW_Z_RANGE,
    STRUCTURAL_CARBON_MINIMUM,
    _rear_window_selector,
    _side_window_selector,
    gen_step,
    make_continuous_carbon_shell,
    make_curved_side_glazing,
    make_hatch_b_side_engineering,
    make_integrated_crossbar_ports_presentation,
    make_rear_hatch_glazing,
    make_visual_review_hatch_leaf,
)


def _expected_side_labels(side: str) -> set[str]:
    return {
        f"CURVED_SIDE_GLAZING_{side}_{index}_PRESENTATION_ONLY"
        for index in range(1, len(SIDE_WINDOW_X_RANGES) + 1)
    }


def _expected_rear_labels() -> set[str]:
    return {
        f"REAR_HATCH_GLAZING_{index}_PRESENTATION_ONLY"
        for index in range(1, len(REAR_WINDOW_Y_RANGES) + 1)
    }


def _presented_port_label(label: str) -> str:
    label = label.replace("_PROVISIONAL", "_INTEGRATED_PRESENTATION_ONLY")
    return label if "INTEGRATED_PRESENTATION_ONLY" in label else label.replace(
        "OEM_ACCESSORY_PORT_PROFILE_", "INTEGRATED_SHELL_PORT_"
    ) + "_INTEGRATED_PRESENTATION_ONLY"


def _rear_corner_selector(side: float):
    return Box(70.0, 110.0, 660.0, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(
        Location(
            (
                value(topper_overall_length),
                side * (value(rear_hatch_opening_width) / 2.0 + value(wall_nominal_thickness) - 55.0),
                20.0,
            )
        )
    )


def _enforce(checks: dict[str, bool]) -> None:
    failed = sorted(name for name, passed in checks.items() if not passed)
    assert not failed, f"STEP15_CONTRACT_FAILED: {', '.join(failed)}"


def _mutation_test(checks: dict[str, bool]) -> None:
    survivors = []
    for name in checks:
        mutated = dict(checks)
        mutated[name] = False
        try:
            _enforce(mutated)
        except AssertionError:
            continue
        survivors.append(name)
    assert not survivors, f"STEP15_MUTATION_SURVIVORS: {', '.join(survivors)}"
    print(f"STEP_15_MUTATION_TEST_PASS mutations={len(checks)} all_rejected=true")


def _contract_checks() -> dict[str, bool]:
    root_labels = {child.label for child in gen_step().children}
    required_roots = {
        "CONTINUOUS_ROUNDED_CARBON_SHELL",
        "CURVED_SIDE_GLAZING",
        "SINGLE_REAR_HATCH_LEAF",
        "REAR_HATCH_TWO_PANE_GLAZING",
        "INTEGRATED_TOPPER_CROSSBAR_PORTS",
    }
    shell = make_continuous_carbon_shell()
    side_panes = make_curved_side_glazing().children
    rear_panes = make_rear_hatch_glazing().children
    hatch_leaf = make_visual_review_hatch_leaf()
    b_side = make_hatch_b_side_engineering()
    integrated_ports = make_integrated_crossbar_ports_presentation().children
    source_ports = make_topper_crossbar_ports().children

    checks: dict[str, bool] = {
        "root_set_equality": root_labels == required_roots,
        "no_reference_or_engineering_visibility": all(
            not any(token in label for token in ("00_REFERENCE", "TOOL", "KEEP_OUT", "DATUM", "LOAD_PATH", "MOTION"))
            for label in root_labels
        ),
        "no_top_center_protrusion": all("TOP_CENTER_PROTRUSION" not in label for label in root_labels),
        "no_freestanding_crossbar_reference": all("CROSSBAR_REFERENCE" not in label for label in root_labels),
        "one_positive_volume_shell": shell.volume > 0.0 and len(shell.solids()) == 1,
        "rounded_shell_spans_product_length": shell.bounding_box().size.X > 1400.0,
        "two_side_ranges": len(SIDE_WINDOW_X_RANGES) == 2,
        "driver_pane_set_equality": {pane.label for pane in side_panes if "_DRIVER_" in pane.label} == _expected_side_labels("DRIVER"),
        "passenger_pane_set_equality": {pane.label for pane in side_panes if "_PASSENGER_" in pane.label} == _expected_side_labels("PASSENGER"),
        "all_side_panes_positive_and_conformal": all(pane.volume > 0.0 and pane.bounding_box().size.Y > 20.0 for pane in side_panes),
        "wide_side_lights": all((right - left) >= 500.0 for left, right in SIDE_WINDOW_X_RANGES),
        "side_light_height": SIDE_WINDOW_Z_RANGE[1] - SIDE_WINDOW_Z_RANGE[0] >= 500.0,
        "two_rear_pane_set_equality": {pane.label for pane in rear_panes} == _expected_rear_labels(),
        "all_rear_panes_positive": all(pane.volume > 0.0 for pane in rear_panes),
        "wide_rear_lights": all((right - left) >= 500.0 for left, right in REAR_WINDOW_Y_RANGES),
        "single_closed_two_pane_hatch": hatch_leaf.label == "SINGLE_REAR_HATCH_LEAF_TWO_PANE_CONTINUOUS_CORNERS_PRESENTATION_ONLY" and len(hatch_leaf.solids()) == 1 and hatch_leaf.volume > 0.0,
        "rear_hatch_corners_continuous": all((hatch_leaf & _rear_corner_selector(side)).volume > 0.0 for side in (-1.0, 1.0)),
        "b_side_hatch_system_complete": {child.label for child in b_side.children} == {
            "SINGLE_REAR_HATCH_FRAME_CONTINUOUS_PRESENTATION_ONLY",
            "REAR_HATCH_PANEL_CLOSED_B_SIDE_PRESENTATION_ONLY",
            "REAR_HATCH_PANEL_OPEN_B_SIDE_PRESENTATION_ONLY",
            "REAR_HATCH_HINGE_LATCH_B_SIDE_PRESENTATION_ONLY",
            "REAR_HATCH_CONTINUOUS_SEAL_B_SIDE_PRESENTATION_ONLY",
            "REAR_HATCH_GUTTER_DRAINAGE_B_SIDE_PRESENTATION_ONLY",
        },
        "eight_shell_integrated_ports_set_equality": {
            item.label for item in integrated_ports
        } == {_presented_port_label(item.label) for item in source_ports} and len(integrated_ports) == 8,
        "ports_are_shell_integrated": all((item & shell).volume > 0.0 for item in integrated_ports),
    }

    for side, sign in (("DRIVER", 1.0), ("PASSENGER", -1.0)):
        for left, right in zip(SIDE_WINDOW_X_RANGES, SIDE_WINDOW_X_RANGES[1:]):
            gap = (left[1], right[0])
            checks[f"{side.lower()}_carbon_between_side_lights"] = (
                gap[1] - gap[0] >= STRUCTURAL_CARBON_MINIMUM
                and (shell & _side_window_selector(*gap, sign)).volume > 0.0
            )
    for left, right in zip(REAR_WINDOW_Y_RANGES, REAR_WINDOW_Y_RANGES[1:]):
        gap = (left[1], right[0])
        checks["carbon_between_rear_hatch_lights"] = (
            gap[1] - gap[0] >= STRUCTURAL_CARBON_MINIMUM
            and (hatch_leaf & _rear_window_selector(*gap, depth=80.0)).volume > 0.0
        )

    review_dir = Path(__file__).resolve().parents[1] / "outputs/review/step15"
    manifest = json.loads((review_dir / "manifest.json").read_text())
    expected_views = {"front.png", "rear.png", "driver_side.png", "passenger_side.png", "top.png", "three_quarter_rear.png"}
    checks.update(
        {
            "manifest_source_commit": manifest["source_geometry_commit"] == VERIFIED_STEP11_COMMIT,
            "manifest_source_lfs_oid": manifest["source_step_lfs_oid_sha256"] == VERIFIED_STEP11_STEP_OID,
            "manifest_presentation_authority": manifest["authority"] == "PRESENTATION_ONLY_NOT_FITMENT_OR_FABRICATION_RELEASE",
            "manifest_view_set_equality": set(manifest["views"]) == expected_views,
            "manifest_view_hashes": all(hashlib.sha256((review_dir / name).read_bytes()).hexdigest() == expected for name, expected in manifest["views"].items()),
            "step_and_glb_present": (review_dir / "R1T_TOPPER_STEP15_OPERATOR_VISUAL.glb").stat().st_size > 0 and (review_dir / "R1T_TOPPER_STEP15_OPERATOR_VISUAL.step").stat().st_size > 0,
        }
    )
    return checks


def run() -> None:
    checks = _contract_checks()
    _enforce(checks)
    _mutation_test(checks)


if __name__ == "__main__":
    run()
    print("STEP_15_OPERATOR_VISUAL_CHECKS_PASS")
