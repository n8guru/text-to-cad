"""Deterministic checks for the provisional Step 8 rear-hatch system."""

from math import isclose

from parameters import (
    DESIGN_DECISION,
    ESTIMATED,
    PLACEHOLDER_REQUIRING_SCAN,
    base_rail_height,
    gas_strut_mount_points,
    hatch_drain_outlet_size,
    hatch_frame_depth,
    hatch_mass_estimate,
    hatch_open_angle,
    hatch_seal_compression,
    hinge_axis,
    rear_hatch_opening_height,
    rear_hatch_opening_width,
    seal_land_width,
    topper_overall_length,
    value,
)
from rear_hatch import (
    build_rear_hatch_subassembly,
    make_closed_hatch_leaf,
    make_drainage_management,
    make_hatch_mechanism_envelopes,
    make_hatch_opening_cutter,
    make_hatch_ready_shell,
    make_latch_service_access,
    make_open_hatch_motion_envelope,
    make_rear_hatch_frame,
    make_weather_seal,
)
from topper_envelope import make_engineered_shell


def _close(actual: float, expected: float) -> None:
    assert isclose(actual, expected, abs_tol=1e-6), (actual, expected)


def run() -> None:
    original_shell = make_engineered_shell()
    cutter = make_hatch_opening_cutter()
    hatch_shell = make_hatch_ready_shell()
    assert (original_shell & cutter).volume > 0.0
    assert 0.0 < hatch_shell.volume < original_shell.volume
    _close(hatch_shell.bounding_box().max.X, value(topper_overall_length))

    frame = make_rear_hatch_frame().children
    assert len(frame) == 4
    assert all(item.volume > 0.0 for item in frame)
    assert all("PROVISIONAL" in item.label for item in frame)

    leaf = make_closed_hatch_leaf()
    land = value(seal_land_width)
    _close(
        leaf.bounding_box().size.Y,
        value(rear_hatch_opening_width) + 2.0 * land,
    )
    _close(
        leaf.bounding_box().size.Z,
        value(rear_hatch_opening_height) + 2.0 * land,
    )
    assert leaf.volume > 0.0

    seal = make_weather_seal().children
    assert len(seal) == 4
    assert all(item.volume > 0.0 for item in seal)
    assert hatch_seal_compression.provenance == DESIGN_DECISION

    drainage = make_drainage_management().children
    assert len(drainage) == 5
    outlets = [item for item in drainage if "OUTLET" in item.label]
    assert len(outlets) == 2
    outlet_z = value(hatch_drain_outlet_size)[2]
    assert all(item.bounding_box().max.Z <= value(base_rail_height) for item in outlets)
    assert outlet_z > 0.0

    mechanism = make_hatch_mechanism_envelopes().children
    assert len(mechanism) == 5
    axis_start, axis_end = value(hinge_axis)
    _close(axis_start[0], axis_end[0])
    _close(axis_start[2], axis_end[2])
    _close(axis_start[1], -axis_end[1])
    assert len(value(gas_strut_mount_points)) == 2
    assert all(pair[0][1] == pair[1][1] for pair in value(gas_strut_mount_points))
    assert value(gas_strut_mount_points)[0][0][1] == -value(
        gas_strut_mount_points
    )[1][0][1]

    service = make_latch_service_access().children
    assert len(service) == 1
    assert "SERVICE_ACCESS" in service[0].label

    open_leaf = make_open_hatch_motion_envelope()
    assert open_leaf.volume > 0.0
    assert open_leaf.bounding_box().max.X > leaf.bounding_box().max.X
    assert value(hatch_open_angle) == 75.0
    assert hatch_mass_estimate.provenance == ESTIMATED
    assert hatch_frame_depth.provenance == DESIGN_DECISION
    assert PLACEHOLDER_REQUIRING_SCAN.replace(" ", "_") in mechanism[1].label

    labels = {child.label for child in build_rear_hatch_subassembly().children}
    assert labels == {
        "TOPPER_SHELL_WITH_HATCH_OPENING",
        "REAR_HATCH_FRAME",
        "REAR_HATCH_LEAF_CLOSED",
        "PRIMARY_HATCH_WEATHER_SEAL",
        "REAR_HATCH_DRAINAGE",
        "HINGE_AND_STRUT_ENVELOPES",
        "SERVICE_ACCESS",
        "OPEN_POSITION_MOTION_ENVELOPE",
    }
if __name__ == "__main__":
    run()
    print("STEP_8_REAR_HATCH_CHECKS_PASS")
