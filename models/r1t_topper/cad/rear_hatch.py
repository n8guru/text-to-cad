"""Step 8 provisional swing-up rear hatch, sealing, drainage, and service CAD."""

from build123d import Align, Axis, Box, Color, Compound, Location
from cadpy.assembly import AssemblyHelper

from parameters import (
    DESIGN_DECISION,
    PLACEHOLDER_REQUIRING_SCAN,
    base_rail_height,
    gas_strut_mount_points,
    hatch_drain_outlet_size,
    hatch_frame_depth,
    hatch_gutter_depth,
    hatch_gutter_width,
    hatch_open_angle,
    hatch_seal_compression,
    hatch_service_keepout_size,
    hinge_axis,
    rear_hatch_opening_height,
    rear_hatch_opening_width,
    seal_land_width,
    topper_overall_length,
    value,
    wall_nominal_thickness,
)
from topper_envelope import make_engineered_shell


HATCH_BLUE = Color(0.04, 0.22, 0.52, 0.92)
FRAME_BLUE = Color(0.03, 0.14, 0.34, 0.96)
SEAL_COLOR = Color(0.10, 0.10, 0.12, 0.96)
DRAIN_COLOR = Color(0.18, 0.72, 0.90, 0.88)
HARDWARE_COLOR = Color(0.88, 0.72, 0.18, 0.90)
KEEP_OUT_COLOR = Color(1.00, 0.58, 0.05, 0.22)


def _rear_plane() -> float:
    return value(topper_overall_length)


def _opening_bottom() -> float:
    return value(base_rail_height)


def make_hatch_opening_cutter():
    """Return the real rear-wall opening used only by the Step 8 derived shell."""
    cutter = Box(
        2.0 * value(wall_nominal_thickness),
        value(rear_hatch_opening_width),
        value(rear_hatch_opening_height),
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).moved(Location((_rear_plane(), 0.0, _opening_bottom())))
    cutter.label = "REAR_HATCH_OPENING_CUTTER_PROVISIONAL"
    return cutter


def make_hatch_ready_shell():
    """Cut the Step 8 opening from the unchanged verified Step 6 shell."""
    shell = make_engineered_shell() - make_hatch_opening_cutter()
    shell.label = "TOPPER_SHELL_WITH_REAR_HATCH_OPENING_PROVISIONAL"
    return shell


def _perimeter_bars(
    depth: float,
    width: float,
    height: float,
    border: float,
    x: float,
    z: float,
) -> list:
    bars = [
        Box(
            depth,
            width,
            border,
            align=(Align.MAX, Align.CENTER, Align.MIN),
        ).moved(Location((x, 0.0, z))),
        Box(
            depth,
            width,
            border,
            align=(Align.MAX, Align.CENTER, Align.MAX),
        ).moved(Location((x, 0.0, z + height))),
    ]
    for sign in (-1.0, 1.0):
        bars.append(
            Box(
                depth,
                border,
                height,
                align=(Align.MAX, Align.CENTER, Align.MIN),
            ).moved(
                Location((x, sign * (width / 2.0 - border / 2.0), z))
            )
        )
    return bars


def make_rear_hatch_frame() -> Compound:
    """Return a four-sided structural packaging frame around the opening."""
    bars = _perimeter_bars(
        value(hatch_frame_depth),
        value(rear_hatch_opening_width) + 2.0 * value(seal_land_width),
        value(rear_hatch_opening_height) + 2.0 * value(seal_land_width),
        value(seal_land_width),
        _rear_plane(),
        _opening_bottom() - value(seal_land_width),
    )
    for index, bar in enumerate(bars, start=1):
        bar.label = f"REAR_HATCH_FRAME_BAR_{index}_PROVISIONAL"
        bar.color = FRAME_BLUE
    return Compound(label="REAR_HATCH_FRAME_PROVISIONAL", children=bars)


def make_closed_hatch_leaf():
    """Return the closed outer hatch leaf overlapping the seal land."""
    land = value(seal_land_width)
    thickness = value(wall_nominal_thickness)
    leaf = Box(
        thickness,
        value(rear_hatch_opening_width) + 2.0 * land,
        value(rear_hatch_opening_height) + 2.0 * land,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    ).moved(
        Location(
            (
                _rear_plane(),
                0.0,
                _opening_bottom() - land,
            )
        )
    )
    leaf.label = "REAR_HATCH_LEAF_CLOSED_PROVISIONAL"
    leaf.color = HATCH_BLUE
    return leaf


def make_weather_seal() -> Compound:
    """Return the primary continuous compression-seal packaging envelope."""
    bars = _perimeter_bars(
        value(hatch_seal_compression),
        value(rear_hatch_opening_width),
        value(rear_hatch_opening_height),
        value(seal_land_width),
        _rear_plane() + value(hatch_seal_compression),
        _opening_bottom(),
    )
    for index, bar in enumerate(bars, start=1):
        bar.label = f"PRIMARY_HATCH_SEAL_SEGMENT_{index}_PROVISIONAL"
        bar.color = SEAL_COLOR
    return Compound(label="PRIMARY_HATCH_WEATHER_SEAL_PROVISIONAL", children=bars)


def make_drainage_management() -> Compound:
    """Return a header/side gutter path feeding two low-point outlets."""
    gutter_width = value(hatch_gutter_width)
    gutter_depth = value(hatch_gutter_depth)
    opening_width = value(rear_hatch_opening_width)
    opening_height = value(rear_hatch_opening_height)
    bottom = _opening_bottom()
    x = _rear_plane() + gutter_depth

    header = Box(
        gutter_depth,
        opening_width,
        gutter_width,
        align=(Align.MAX, Align.CENTER, Align.MAX),
    ).moved(Location((x, 0.0, bottom + opening_height)))
    header.label = "HATCH_HEADER_DRIP_GUTTER_PROVISIONAL"

    sides = []
    side_y = opening_width / 2.0 + gutter_width / 2.0
    for side, sign in (("DRIVER", 1.0), ("PASSENGER", -1.0)):
        gutter = Box(
            gutter_depth,
            gutter_width,
            opening_height,
            align=(Align.MAX, Align.CENTER, Align.MIN),
        ).moved(Location((x, sign * side_y, bottom)))
        gutter.label = f"HATCH_SIDE_GUTTER_{side}_PROVISIONAL"
        sides.append(gutter)

    outlet_x, outlet_y, outlet_z = value(hatch_drain_outlet_size)
    outlets = []
    for side, sign in (("DRIVER", 1.0), ("PASSENGER", -1.0)):
        outlet = Box(
            outlet_x,
            outlet_y,
            outlet_z,
            align=(Align.MAX, Align.CENTER, Align.MAX),
        ).moved(
            Location(
                (
                    _rear_plane(),
                    sign * side_y,
                    bottom,
                )
            )
        )
        outlet.label = f"HATCH_DRAIN_OUTLET_{side}_PROVISIONAL"
        outlets.append(outlet)

    for item in (header, *sides, *outlets):
        item.color = DRAIN_COLOR
    return Compound(
        label="REAR_HATCH_DRAINAGE_MANAGEMENT_PROVISIONAL",
        children=[header, *sides, *outlets],
    )


def make_hatch_mechanism_envelopes() -> Compound:
    """Package the hinge and symmetric strut mounts without force claims."""
    axis_start, axis_end = value(hinge_axis)
    axis_box = Box(
        18.0,
        axis_end[1] - axis_start[1],
        18.0,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    ).moved(
        Location(
            (
                axis_start[0],
                (axis_start[1] + axis_end[1]) / 2.0,
                axis_start[2],
            )
        )
    )
    axis_box.label = "REAR_HATCH_HINGE_AXIS_ENVELOPE_PROVISIONAL"

    mount_x, mount_y, mount_z = value(hatch_service_keepout_size)
    mounts = []
    for side_index, pair in enumerate(value(gas_strut_mount_points), start=1):
        for mount_index, point in enumerate(pair, start=1):
            mount = Box(
                mount_x,
                mount_y,
                mount_z,
                align=(Align.CENTER, Align.CENTER, Align.CENTER),
            ).moved(Location(point))
            mount.label = (
                f"GAS_STRUT_SERVICE_ENVELOPE_SIDE_{side_index}_"
                f"MOUNT_{mount_index}_{PLACEHOLDER_REQUIRING_SCAN.replace(' ', '_')}"
            )
            mounts.append(mount)
    for item in (axis_box, *mounts):
        item.color = HARDWARE_COLOR
    return Compound(
        label="REAR_HATCH_MECHANISM_ENVELOPES_PROVISIONAL",
        children=[axis_box, *mounts],
    )


def make_latch_service_access() -> Compound:
    """Reserve removable access at the lower-center latch packaging zone."""
    size_x, size_y, size_z = value(hatch_service_keepout_size)
    access = Box(
        size_x,
        2.0 * size_y,
        size_z,
        align=(Align.MAX, Align.CENTER, Align.MIN),
    ).moved(
        Location(
            (
                _rear_plane(),
                0.0,
                _opening_bottom() - value(seal_land_width),
            )
        )
    )
    access.label = "HATCH_LATCH_SERVICE_ACCESS_KEEP_OUT_PROVISIONAL"
    access.color = KEEP_OUT_COLOR
    return Compound(label="REAR_HATCH_SERVICE_ACCESS", children=[access])


def make_open_hatch_motion_envelope():
    """Return the leaf at the provisional open angle as a review keep-out."""
    open_leaf = make_closed_hatch_leaf().rotate(
        Axis(value(hinge_axis)[0], (0.0, 1.0, 0.0)),
        -value(hatch_open_angle),
    )
    open_leaf.label = "REAR_HATCH_OPEN_POSITION_MOTION_ENVELOPE_PROVISIONAL"
    open_leaf.color = KEEP_OUT_COLOR
    return open_leaf


def build_rear_hatch_subassembly() -> Compound:
    """Build the Step 8 derived shell and closure-system review assembly."""
    assert hatch_frame_depth.provenance == DESIGN_DECISION
    assembly = AssemblyHelper("10_TOPPER_REAR_HATCH_SYSTEM")
    assembly.add(make_hatch_ready_shell(), "TOPPER_SHELL_WITH_HATCH_OPENING")
    assembly.add(make_rear_hatch_frame(), "REAR_HATCH_FRAME")
    assembly.add(make_closed_hatch_leaf(), "REAR_HATCH_LEAF_CLOSED")
    assembly.add(make_weather_seal(), "PRIMARY_HATCH_WEATHER_SEAL")
    assembly.add(make_drainage_management(), "REAR_HATCH_DRAINAGE")
    assembly.add(make_hatch_mechanism_envelopes(), "HINGE_AND_STRUT_ENVELOPES")
    assembly.add(make_latch_service_access(), "SERVICE_ACCESS")
    assembly.add(make_open_hatch_motion_envelope(), "OPEN_POSITION_MOTION_ENVELOPE")
    return assembly.build()
