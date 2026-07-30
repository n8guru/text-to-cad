"""Provisional Step 10 visibility, lighting, and low-voltage harness packaging."""

from build123d import Align, Box, Color, Compound, Location
from cadpy.assembly import AssemblyHelper

from parameters import (
    PLACEHOLDER_REQUIRING_SCAN,
    brake_light_center,
    brake_light_recess_dimensions,
    camera_housing_dimensions,
    camera_optical_keepout_dimensions,
    electrical_service_box_dimensions,
    interior_light_bar_centers,
    interior_light_bar_dimensions,
    rear_camera_center,
    value,
    vehicle_electrical_ingress_center,
    vehicle_electrical_ingress_dimensions,
    wiring_channel_dimensions,
)
from topper_envelope import make_engineered_shell


CAMERA_COLOR = Color(0.12, 0.12, 0.16, 0.95)
BRAKE_COLOR = Color(0.92, 0.03, 0.04, 0.90)
INTERIOR_LIGHT_COLOR = Color(1.00, 0.92, 0.55, 0.92)
HARNESS_COLOR = Color(0.95, 0.48, 0.08, 0.88)
SERVICE_COLOR = Color(0.55, 0.22, 0.72, 0.72)
KEEP_OUT_COLOR = Color(0.25, 0.86, 0.96, 0.18)


def _centered_box(dimensions, center, label, color):
    box = Box(*dimensions, align=(Align.CENTER, Align.CENTER, Align.CENTER)).moved(
        Location(center)
    )
    box.label = label
    box.color = color
    return box


def make_camera_brake_ready_shell():
    """Cut real provisional packaging passages without changing Step 6 source."""
    camera_cutter = _centered_box(
        value(camera_housing_dimensions),
        value(rear_camera_center),
        "CAMERA_PASSAGE_CUTTER",
        CAMERA_COLOR,
    )
    brake_cutter = _centered_box(
        value(brake_light_recess_dimensions),
        value(brake_light_center),
        "BRAKE_LIGHT_RECESS_CUTTER",
        BRAKE_COLOR,
    )
    shell = make_engineered_shell() - camera_cutter - brake_cutter
    shell.label = "TOPPER_SHELL_ELECTRICAL_READY_PROVISIONAL"
    return shell


def make_rear_camera_provision() -> Compound:
    housing = _centered_box(
        value(camera_housing_dimensions),
        value(rear_camera_center),
        "REAR_CAMERA_RELOCATED_HOUSING_PROVISIONAL",
        CAMERA_COLOR,
    )
    keepout_size = value(camera_optical_keepout_dimensions)
    camera_center = value(rear_camera_center)
    sight = Box(
        *keepout_size,
        align=(Align.MIN, Align.CENTER, Align.CENTER),
    ).moved(Location(camera_center))
    sight.label = "REAR_CAMERA_OPTICAL_FIELD_KEEP_OUT_REVIEW_ONLY"
    sight.color = KEEP_OUT_COLOR
    return Compound(label="REAR_CAMERA_PROVISION", children=[housing, sight])


def make_brake_light_provision() -> Compound:
    light = _centered_box(
        value(brake_light_recess_dimensions),
        value(brake_light_center),
        "HIGH_MOUNT_BRAKE_LIGHT_BAR_PROVISIONAL_NO_PHOTOMETRY_CLAIM",
        BRAKE_COLOR,
    )
    service_size = value(electrical_service_box_dimensions)
    center = value(brake_light_center)
    service = _centered_box(
        service_size,
        (center[0] - service_size[0] / 2.0, center[1], center[2] - 30.0),
        "BRAKE_LIGHT_DRIVER_SERVICE_ENVELOPE",
        SERVICE_COLOR,
    )
    return Compound(
        label="HIGH_MOUNT_BRAKE_LIGHT_PROVISION",
        children=[light, service],
    )


def make_interior_lighting_provision() -> Compound:
    lights = [
        _centered_box(
            value(interior_light_bar_dimensions),
            center,
            f"INTERIOR_TASK_LIGHT_{side}_PROVISIONAL",
            INTERIOR_LIGHT_COLOR,
        )
        for side, center in zip(
            ("DRIVER", "PASSENGER"),
            value(interior_light_bar_centers),
        )
    ]
    return Compound(label="INTERIOR_LIGHTING_PROVISION", children=lights)


def make_low_voltage_harness_packaging() -> Compound:
    """Reserve connected raceways only; wire gauge and circuits are downstream."""
    channel_size = value(wiring_channel_dimensions)
    ingress = value(vehicle_electrical_ingress_center)
    rear_x = value(rear_camera_center)[0] - 44.0
    rear_z = value(interior_light_bar_centers)[0][2]
    y = ingress[1]

    longitudinal = _centered_box(
        channel_size,
        (ingress[0] + channel_size[0] / 2.0, y, ingress[2]),
        "HARNESS_RACEWAY_DRIVER_BASE_PROVISIONAL",
        HARNESS_COLOR,
    )
    rise_height = rear_z - ingress[2]
    riser = _centered_box(
        (channel_size[1], channel_size[1], rise_height),
        (rear_x, y, ingress[2] + rise_height / 2.0),
        "HARNESS_RISER_REAR_DRIVER_PROVISIONAL",
        HARNESS_COLOR,
    )
    header = _centered_box(
        (channel_size[1], 2.0 * y, channel_size[1]),
        (rear_x, 0.0, rear_z),
        "HARNESS_HEADER_BRANCH_PROVISIONAL",
        HARNESS_COLOR,
    )
    roof_branches = [
        _centered_box(
            (rear_x - center[0], channel_size[1], channel_size[1]),
            ((rear_x + center[0]) / 2.0, center[1], rear_z),
            f"HARNESS_INTERIOR_LIGHT_BRANCH_{side}_PROVISIONAL",
            HARNESS_COLOR,
        )
        for side, center in zip(
            ("DRIVER", "PASSENGER"),
            value(interior_light_bar_centers),
        )
    ]
    camera_z = value(rear_camera_center)[2]
    camera_drop = _centered_box(
        (channel_size[1], channel_size[1], abs(rear_z - camera_z)),
        (rear_x, 0.0, (rear_z + camera_z) / 2.0),
        "HARNESS_CAMERA_DROP_PROVISIONAL",
        HARNESS_COLOR,
    )
    service = _centered_box(
        value(electrical_service_box_dimensions),
        (rear_x, y, rear_z),
        "LOW_VOLTAGE_SERVICE_JUNCTION_PROVISIONAL",
        SERVICE_COLOR,
    )
    return Compound(
        label="LOW_VOLTAGE_HARNESS_PACKAGING",
        children=[
            longitudinal,
            riser,
            header,
            *roof_branches,
            camera_drop,
            service,
        ],
    )


def make_vehicle_electrical_ingress_reservation():
    ingress = _centered_box(
        value(vehicle_electrical_ingress_dimensions),
        value(vehicle_electrical_ingress_center),
        "VEHICLE_ELECTRICAL_INGRESS_PROTOCOL_UNKNOWN_"
        + PLACEHOLDER_REQUIRING_SCAN.replace(" ", "_"),
        KEEP_OUT_COLOR,
    )
    return ingress


def build_electrical_integration_subassembly() -> Compound:
    integration = AssemblyHelper("10_TOPPER_ELECTRICAL_INTEGRATION")
    integration.add(
        make_camera_brake_ready_shell(),
        "TOPPER_SHELL_ELECTRICAL_READY",
    )
    integration.add(make_rear_camera_provision(), "REAR_CAMERA_PROVISION")
    integration.add(
        make_brake_light_provision(),
        "HIGH_MOUNT_BRAKE_LIGHT_PROVISION",
    )
    integration.add(
        make_interior_lighting_provision(),
        "INTERIOR_LIGHTING_PROVISION",
    )
    integration.add(
        make_low_voltage_harness_packaging(),
        "LOW_VOLTAGE_HARNESS_PACKAGING",
    )
    integration.add(
        make_vehicle_electrical_ingress_reservation(),
        "VEHICLE_ELECTRICAL_INGRESS",
    )
    return integration.build()
