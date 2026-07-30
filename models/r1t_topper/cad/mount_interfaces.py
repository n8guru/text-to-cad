"""Step 9 provisional vehicle mounts, controls, crossbar ports, and keep-outs.

The geometry in this module is packaging authority only. Factory mating
profiles, loads, clearances, and actuation travel remain calibration inputs.
"""

from build123d import Align, Box, Color, Compound, Location
from cadpy.assembly import AssemblyHelper

from parameters import (
    PLACEHOLDER_REQUIRING_SCAN,
    bed_anchor_locations,
    bed_control_button_locations,
    bed_control_functions,
    cab_relative_motion_keepout_depth,
    control_route_section,
    control_source_coupler_size,
    crossbar_hardpoint_size,
    crossbar_interface_depth,
    crossbar_interface_width,
    crossbar_latch_service_keepout_size,
    crossbar_mount_span,
    factory_crossbar_mount_interface_dimensions,
    mount_adapter_pad_size,
    mount_adapter_web_size,
    mount_receiver_size,
    mount_release_service_keepout_size,
    relocated_control_pod_center_y,
    relocated_control_pod_height,
    relocated_control_pod_size,
    tailgate_height,
    tailgate_sweep_keepout_margin,
    tailgate_thickness,
    tailgate_width,
    tonneau_service_keepout_size,
    topper_base_outer_width,
    topper_crossbar_station_1,
    topper_crossbar_station_2,
    topper_front_height,
    topper_overall_length,
    topper_silhouette_stations,
    value,
)
from topper_envelope import build_topper_engineered_subassembly


MOUNT_COLOR = Color(0.95, 0.66, 0.08, 0.95)
RECEIVER_COLOR = Color(0.85, 0.30, 0.08, 0.88)
CONTROL_COLOR = Color(0.82, 0.12, 0.62, 0.92)
CONTROL_ROUTE_COLOR = Color(0.96, 0.46, 0.82, 0.78)
CROSSBAR_PORT_COLOR = Color(0.05, 0.76, 0.92, 0.95)
HARDPOINT_COLOR = Color(0.96, 0.82, 0.12, 0.90)
KEEP_OUT_COLOR = Color(1.00, 0.35, 0.04, 0.20)


def _box_centered(
    size: tuple[float, float, float],
    center: tuple[float, float, float],
):
    return Box(*size, align=(Align.CENTER, Align.CENTER, Align.CENTER)).moved(
        Location(center)
    )


def _roof_edge_z(x: float) -> float:
    """Linearly interpolate the sparse roof-edge control at a station."""
    fraction = x / value(topper_overall_length)
    rows = value(topper_silhouette_stations)
    for left, right in zip(rows, rows[1:]):
        if left[0] <= fraction <= right[0]:
            blend = (fraction - left[0]) / (right[0] - left[0])
            left_z = left[1] - left[5]
            right_z = right[1] - right[5]
            return left_z + blend * (right_z - left_z)
    raise ValueError(f"crossbar station outside topper: {x}")


def make_quick_release_mount_adapters() -> Compound:
    """Bridge the four provisional factory anchors into the base flanges."""
    children = []
    pad_size = value(mount_adapter_pad_size)
    web_size = value(mount_adapter_web_size)
    receiver_size = value(mount_receiver_size)
    for index, (x, y, z) in enumerate(value(bed_anchor_locations), start=1):
        pad = _box_centered(pad_size, (x, y, pad_size[2] / 2.0))
        pad.label = f"MOUNT_{index}_FLANGE_LOAD_SPREADER_PROVISIONAL"
        pad.color = MOUNT_COLOR

        web_center_z = (z + receiver_size[2] / 2.0 + pad_size[2]) / 2.0
        web = _box_centered(web_size, (x, y, web_center_z))
        web.label = f"MOUNT_{index}_REMOVABLE_BRIDGE_PROVISIONAL"
        web.color = MOUNT_COLOR

        receiver = _box_centered(receiver_size, (x, y, z))
        receiver.label = (
            f"MOUNT_{index}_FACTORY_ANCHOR_RECEIVER_"
            + PLACEHOLDER_REQUIRING_SCAN.replace(" ", "_")
        )
        receiver.color = RECEIVER_COLOR
        children.extend((pad, web, receiver))
    return Compound(label="QUICK_RELEASE_MOUNT_ADAPTERS", children=children)


def make_relocated_control_system() -> Compound:
    """Package non-electronic mechanical extensions to driver-side pods."""
    children = []
    functions = value(bed_control_functions)
    locations = value(bed_control_button_locations)
    source_size = value(control_source_coupler_size)
    pod_size = value(relocated_control_pod_size)
    route_width, route_depth = value(control_route_section)
    pod_y = value(relocated_control_pod_center_y)
    pod_z = value(relocated_control_pod_height)
    for function, (x, y, _z) in zip(functions, locations):
        source = _box_centered(source_size, (x, y, 0.0))
        source.label = (
            f"{function}_SOURCE_COUPLER_"
            + PLACEHOLDER_REQUIRING_SCAN.replace(" ", "_")
        )
        source.color = CONTROL_COLOR

        vertical = Box(
            route_width,
            route_depth,
            pod_z,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        ).moved(Location((x, y, 0.0)))
        vertical.label = f"{function}_MECHANICAL_ROUTE_VERTICAL_PROVISIONAL"
        vertical.color = CONTROL_ROUTE_COLOR

        lateral_length = pod_y - y + pod_size[1] / 2.0
        lateral = Box(
            route_width,
            lateral_length,
            route_depth,
            align=(Align.CENTER, Align.MIN, Align.CENTER),
        ).moved(Location((x, y, pod_z)))
        lateral.label = f"{function}_MECHANICAL_ROUTE_OUTBOARD_PROVISIONAL"
        lateral.color = CONTROL_ROUTE_COLOR

        pod = _box_centered(pod_size, (x, pod_y, pod_z))
        pod.label = f"{function}_RELOCATED_DRIVER_SIDE_CONTROL_POD_PROVISIONAL"
        pod.color = CONTROL_COLOR
        children.extend((source, vertical, lateral, pod))
    return Compound(label="RELOCATED_MECHANICAL_CONTROLS", children=children)


def make_topper_crossbar_ports() -> Compound:
    """Package four topper-roof port/hardpoint envelopes at two stations."""
    children = []
    port_x = value(crossbar_interface_width)
    port_y = value(crossbar_interface_depth)
    port_z = value(factory_crossbar_mount_interface_dimensions)[2]
    hardpoint_size = value(crossbar_hardpoint_size)
    half_span = value(crossbar_mount_span) / 2.0
    for station_index, x in enumerate(
        (value(topper_crossbar_station_1), value(topper_crossbar_station_2)),
        start=1,
    ):
        roof_z = _roof_edge_z(x)
        for side, sign in (("DRIVER", 1.0), ("PASSENGER", -1.0)):
            y = sign * half_span
            hardpoint = _box_centered(
                hardpoint_size,
                (x, y, roof_z - hardpoint_size[2] / 2.0 + 2.0),
            )
            hardpoint.label = (
                f"CROSSBAR_{station_index}_{side}_SHELL_HARDPOINT_PROVISIONAL"
            )
            hardpoint.color = HARDPOINT_COLOR

            port = _box_centered(
                (port_x, port_y, port_z),
                (x, y, roof_z + port_z / 2.0 - 2.0),
            )
            port.label = (
                f"CROSSBAR_{station_index}_{side}_OEM_ACCESSORY_PORT_PROFILE_"
                + PLACEHOLDER_REQUIRING_SCAN.replace(" ", "_")
            )
            port.color = CROSSBAR_PORT_COLOR
            children.extend((hardpoint, port))
    return Compound(label="TOPPER_CROSSBAR_PORT_SYSTEM", children=children)


def make_vehicle_and_service_keepouts() -> Compound:
    """Reserve vehicle motion and human/tool access around Step 9 interfaces."""
    children = []

    cab_depth = value(cab_relative_motion_keepout_depth)
    cab = Box(
        2.0 * cab_depth,
        value(topper_base_outer_width),
        value(topper_front_height) + 30.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    cab.label = (
        "KEEP_OUT_CAB_RELATIVE_MOTION_"
        + PLACEHOLDER_REQUIRING_SCAN.replace(" ", "_")
    )
    cab.color = KEEP_OUT_COLOR
    children.append(cab)

    margin = value(tailgate_sweep_keepout_margin)
    tailgate = Box(
        value(tailgate_height) + value(tailgate_thickness) + 2.0 * margin,
        value(tailgate_width) + 2.0 * margin,
        value(tailgate_height) + 2.0 * margin,
        align=(Align.MIN, Align.CENTER, Align.MAX),
    ).moved(
        Location(
            (
                value(topper_overall_length) - value(tailgate_thickness) - margin,
                0.0,
                margin,
            )
        )
    )
    tailgate.label = (
        "KEEP_OUT_TAILGATE_CLOSED_TO_OPEN_SWEEP_"
        + PLACEHOLDER_REQUIRING_SCAN.replace(" ", "_")
    )
    tailgate.color = KEEP_OUT_COLOR
    children.append(tailgate)

    tonneau_size = value(tonneau_service_keepout_size)
    tonneau = Box(
        *tonneau_size,
        align=(Align.MIN, Align.CENTER, Align.MAX),
    )
    tonneau.label = (
        "KEEP_OUT_TONNEAU_CASSETTE_SERVICE_"
        + PLACEHOLDER_REQUIRING_SCAN.replace(" ", "_")
    )
    tonneau.color = KEEP_OUT_COLOR
    children.append(tonneau)

    release_size = value(mount_release_service_keepout_size)
    for index, (x, y, z) in enumerate(value(bed_anchor_locations), start=1):
        release = _box_centered(release_size, (x, y, z))
        release.label = (
            f"KEEP_OUT_MOUNT_{index}_RELEASE_ACCESS_"
            + PLACEHOLDER_REQUIRING_SCAN.replace(" ", "_")
        )
        release.color = KEEP_OUT_COLOR
        children.append(release)

    latch_size = value(crossbar_latch_service_keepout_size)
    half_span = value(crossbar_mount_span) / 2.0
    for station_index, x in enumerate(
        (value(topper_crossbar_station_1), value(topper_crossbar_station_2)),
        start=1,
    ):
        roof_z = _roof_edge_z(x)
        for side, sign in (("DRIVER", 1.0), ("PASSENGER", -1.0)):
            latch = _box_centered(
                latch_size,
                (x, sign * half_span, roof_z + latch_size[2] / 2.0),
            )
            latch.label = (
                f"KEEP_OUT_CROSSBAR_{station_index}_{side}_LATCH_SERVICE_"
                + PLACEHOLDER_REQUIRING_SCAN.replace(" ", "_")
            )
            latch.color = KEEP_OUT_COLOR
            children.append(latch)

    return Compound(label="VEHICLE_AND_SERVICE_KEEP_OUTS", children=children)


def build_mount_interface_subassembly() -> Compound:
    """Return Step 6 shell plus the independently composable Step 9 systems."""
    assembly = AssemblyHelper("10_TOPPER_MOUNT_AND_INTERFACE_SYSTEM")
    assembly.add(
        build_topper_engineered_subassembly(),
        "TOPPER_ENGINEERED_SHELL_BASELINE",
    )
    assembly.add(make_quick_release_mount_adapters(), "QUICK_RELEASE_MOUNT_ADAPTERS")
    assembly.add(make_relocated_control_system(), "RELOCATED_MECHANICAL_CONTROLS")
    assembly.add(make_topper_crossbar_ports(), "TOPPER_CROSSBAR_PORT_SYSTEM")
    assembly.add(make_vehicle_and_service_keepouts(), "VEHICLE_AND_SERVICE_KEEP_OUTS")
    return assembly.build()
