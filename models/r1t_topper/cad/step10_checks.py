"""Deterministic checks for provisional Step 10 electrical integration."""

from math import isclose

from assembly import gen_step
from electrical_integration import (
    build_electrical_integration_subassembly,
    make_brake_light_provision,
    make_camera_brake_ready_shell,
    make_interior_lighting_provision,
    make_low_voltage_harness_packaging,
    make_rear_camera_provision,
    make_vehicle_electrical_ingress_reservation,
)
from parameters import (
    DESIGN_DECISION,
    PLACEHOLDER_REQUIRING_SCAN,
    brake_light_center,
    camera_housing_dimensions,
    interior_light_bar_centers,
    rear_camera_center,
    value,
    vehicle_electrical_ingress_center,
)
from topper_envelope import make_engineered_shell


def _close(actual: float, expected: float) -> None:
    assert isclose(actual, expected, abs_tol=1e-6), (actual, expected)


def run() -> None:
    base_shell = make_engineered_shell()
    ready_shell = make_camera_brake_ready_shell()
    assert 0.0 < ready_shell.volume < base_shell.volume

    camera = make_rear_camera_provision().children
    assert len(camera) == 2
    assert camera[0].volume > 0.0
    assert camera[1].bounding_box().min.X == value(rear_camera_center)[0]
    assert value(camera_housing_dimensions)[1] > 0.0

    brake = make_brake_light_provision().children
    assert len(brake) == 2
    assert brake[0].volume > 0.0
    _close(brake[0].center().Y, 0.0)
    assert brake_light_center.provenance == DESIGN_DECISION

    interior = make_interior_lighting_provision().children
    assert len(interior) == 2
    _close(interior[0].center().Y, -interior[1].center().Y)
    assert value(interior_light_bar_centers)[0][0] == value(
        interior_light_bar_centers
    )[1][0]

    harness = make_low_voltage_harness_packaging().children
    assert len(harness) == 7
    assert all(item.volume > 0.0 for item in harness)
    assert {item.label for item in harness} == {
        "HARNESS_RACEWAY_DRIVER_BASE_PROVISIONAL",
        "HARNESS_RISER_REAR_DRIVER_PROVISIONAL",
        "HARNESS_HEADER_BRANCH_PROVISIONAL",
        "HARNESS_INTERIOR_LIGHT_BRANCH_DRIVER_PROVISIONAL",
        "HARNESS_INTERIOR_LIGHT_BRANCH_PASSENGER_PROVISIONAL",
        "HARNESS_CAMERA_DROP_PROVISIONAL",
        "LOW_VOLTAGE_SERVICE_JUNCTION_PROVISIONAL",
    }
    for first, second in zip(harness, harness[1:3]):
        assert (first & second).volume > 0.0
    assert all((harness[2] & branch).volume > 0.0 for branch in harness[3:5])
    assert (harness[2] & harness[5]).volume > 0.0
    assert (harness[5] & camera[0]).volume > 0.0
    assert all(
        (branch & light).volume > 0.0
        for branch, light in zip(harness[3:5], interior)
    )

    ingress = make_vehicle_electrical_ingress_reservation()
    assert vehicle_electrical_ingress_center.provenance == PLACEHOLDER_REQUIRING_SCAN
    assert "PROTOCOL_UNKNOWN" in ingress.label
    assert PLACEHOLDER_REQUIRING_SCAN.replace(" ", "_") in ingress.label

    labels = {
        child.label for child in build_electrical_integration_subassembly().children
    }
    assert labels == {
        "TOPPER_SHELL_ELECTRICAL_READY",
        "REAR_CAMERA_PROVISION",
        "HIGH_MOUNT_BRAKE_LIGHT_PROVISION",
        "INTERIOR_LIGHTING_PROVISION",
        "LOW_VOLTAGE_HARNESS_PACKAGING",
        "VEHICLE_ELECTRICAL_INGRESS",
    }
    assert {child.label for child in gen_step().children} == {
        "00_REFERENCE",
        "10_TOPPER_ELECTRICAL_INTEGRATION",
        "90_REVIEW_COORDINATE_REFERENCE",
    }


if __name__ == "__main__":
    run()
    print("STEP_10_ELECTRICAL_INTEGRATION_CHECKS_PASS")
