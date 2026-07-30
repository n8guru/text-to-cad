"""Authoritative provisional shell and sectional modular system."""

from build123d import Align, Box, Color, Compound, Edge, Face, Location, Wire, loft
from cadpy.assembly import AssemblyHelper

from parameters import (
    PLACEHOLDER_REQUIRING_SCAN,
    base_interface_keepout_depth,
    base_rail_height,
    base_rail_width,
    cab_to_topper_nominal_gap,
    datum_display_thickness,
    module_bay_center_z,
    module_bay_count_per_side,
    module_frame_depth,
    module_frame_land_width,
    module_opening_height,
    module_opening_width,
    module_panel_thickness,
    module_spacing,
    module_variant_types,
    rear_hatch_opening_height,
    rear_hatch_opening_width,
    section_joint_alignment_key_size,
    section_joint_doubler_thickness,
    section_joint_doubler_width,
    section_joint_gap,
    topper_base_outer_width,
    topper_crossbar_station_1,
    topper_crossbar_station_2,
    topper_front_height,
    topper_overall_length,
    topper_silhouette_stations,
    transverse_load_path_band_width,
    value,
    wall_nominal_thickness,
)


CONCEPT_BLUE = Color(0.10, 0.36, 0.72, 0.42)
SHELL_BLUE = Color(0.08, 0.30, 0.64, 0.78)
FLANGE_BLUE = Color(0.04, 0.18, 0.42, 0.92)
DATUM_COLOR = Color(0.12, 0.84, 0.76, 0.22)
KEEP_OUT_COLOR = Color(1.00, 0.58, 0.05, 0.24)
LOAD_PATH_COLOR = Color(0.96, 0.82, 0.12, 0.82)
SECTION_COLOR = Color(0.08, 0.30, 0.64, 0.82)
JOINT_COLOR = Color(0.78, 0.20, 0.78, 0.86)
MODULE_FRAME_COLOR = Color(0.08, 0.62, 0.50, 0.92)
MODULE_SOLID_COLOR = Color(0.12, 0.24, 0.48, 0.90)
MODULE_WINDOW_COLOR = Color(0.35, 0.75, 0.94, 0.38)
MODULE_MESH_COLOR = Color(0.18, 0.18, 0.20, 0.92)
MODULE_RECOVERY_COLOR = Color(0.90, 0.42, 0.08, 0.92)
MODULE_UTILITY_COLOR = Color(0.55, 0.60, 0.66, 0.92)


def _section(
    x: float,
    height: float,
    base_width: float,
    shoulder_width: float,
    roof_width: float,
    crown: float,
) -> Face:
    """Create one symmetric scan-replaceable YZ silhouette section."""
    half_base = base_width / 2.0
    half_shoulder = shoulder_width / 2.0
    half_roof = roof_width / 2.0
    shoulder_z = height * 0.72
    roof_edge_z = height - crown

    left_base = (x, -half_base, 0.0)
    right_base = (x, half_base, 0.0)
    right_shoulder = (x, half_shoulder, shoulder_z)
    right_roof = (x, half_roof, roof_edge_z)
    left_roof = (x, -half_roof, roof_edge_z)
    left_shoulder = (x, -half_shoulder, shoulder_z)

    edges = [
        Edge.make_line(left_base, right_base),
        Edge.make_line(right_base, right_shoulder),
        Edge.make_three_point_arc(
            right_shoulder,
            (x, (half_shoulder + half_roof) / 2.0, (shoulder_z + roof_edge_z) / 2.0 + 8.0),
            right_roof,
        ),
        Edge.make_three_point_arc(
            right_roof,
            (x, 0.0, height),
            left_roof,
        ),
        Edge.make_three_point_arc(
            left_roof,
            (x, -(half_shoulder + half_roof) / 2.0, (shoulder_z + roof_edge_z) / 2.0 + 8.0),
            left_shoulder,
        ),
        Edge.make_line(left_shoulder, left_base),
    ]
    return Face.make_surface(Wire(edges))


def make_master_topper_envelope():
    """Return the selected Step 5 exterior design volume."""
    x_front = value(cab_to_topper_nominal_gap)
    sections = [
        _section(
            x_front + fraction * value(topper_overall_length),
            height,
            base_width,
            shoulder_width,
            roof_width,
            crown,
        )
        for fraction, height, base_width, shoulder_width, roof_width, crown
        in value(topper_silhouette_stations)
    ]
    envelope = loft(
        sections,
        ruled=False,
    )
    envelope.label = "TOPPER_MASTER_ENVELOPE_CONCEPT_ONLY"
    envelope.color = CONCEPT_BLUE
    return envelope


def make_engineered_shell():
    """Return the provisional sandwich shell, open along its mounting plane."""
    thickness = value(wall_nominal_thickness)
    outer = make_master_topper_envelope()
    inner_sections = [
        _section(
            value(cab_to_topper_nominal_gap) + fraction * value(topper_overall_length),
            height - thickness,
            base_width - 2.0 * thickness,
            shoulder_width - 2.0 * thickness,
            roof_width - 2.0 * thickness,
            crown,
        )
        for fraction, height, base_width, shoulder_width, roof_width, crown
        in value(topper_silhouette_stations)
    ]
    shell = outer - loft(inner_sections, ruled=False)
    shell.label = "TOPPER_ENGINEERED_SANDWICH_SHELL_PROVISIONAL"
    shell.color = SHELL_BLUE
    return shell


def _make_inset_envelope(inset: float):
    """Return a closed envelope inset from the selected exterior profiles."""
    sections = [
        _section(
            value(cab_to_topper_nominal_gap) + fraction * value(topper_overall_length),
            height - inset,
            base_width - 2.0 * inset,
            shoulder_width - 2.0 * inset,
            roof_width - 2.0 * inset,
            crown,
        )
        for fraction, height, base_width, shoulder_width, roof_width, crown
        in value(topper_silhouette_stations)
    ]
    return loft(sections, ruled=False)


def _module_bay_centers() -> tuple[float, ...]:
    count = value(module_bay_count_per_side)
    opening = value(module_opening_width)
    spacing = value(module_spacing)
    occupied = count * opening + (count - 1) * spacing
    first = (
        value(cab_to_topper_nominal_gap)
        + (value(topper_overall_length) - occupied) / 2.0
        + opening / 2.0
    )
    return tuple(first + index * (opening + spacing) for index in range(count))


def _section_joint_stations() -> tuple[float, ...]:
    """Place the two joints midway between the three module openings."""
    centers = _module_bay_centers()
    return tuple((left + right) / 2.0 for left, right in zip(centers, centers[1:]))


def make_module_opening_cutters() -> Compound:
    """Return six through-cutters for the common modular side opening."""
    cutters = []
    cut_depth = value(module_frame_depth) + 2.0 * value(wall_nominal_thickness)
    side_y = value(topper_base_outer_width) / 2.0
    for side, sign in (("DRIVER", 1.0), ("PASSENGER", -1.0)):
        for index, center_x in enumerate(_module_bay_centers(), start=1):
            cutter = Box(
                value(module_opening_width),
                cut_depth,
                value(module_opening_height),
                align=(Align.CENTER, Align.CENTER, Align.CENTER),
            ).moved(
                Location(
                    (
                        center_x,
                        sign * side_y,
                        value(module_bay_center_z),
                    )
                )
            )
            cutter.label = f"MODULE_OPENING_{side}_{index}_CUTTER"
            cutters.append(cutter)
    return Compound(label="MODULE_OPENING_CUTTERS", children=cutters)


def make_sectioned_modular_shell() -> Compound:
    """Cut the Step 6 shell into three flat-pack segments with six side bays."""
    shell = make_engineered_shell()
    for cutter in make_module_opening_cutters().children:
        shell = shell - cutter

    gap = value(section_joint_gap)
    x_front = value(cab_to_topper_nominal_gap)
    x_rear = x_front + value(topper_overall_length)
    stations = _section_joint_stations()
    bounds = (
        (x_front, stations[0] - gap / 2.0),
        (stations[0] + gap / 2.0, stations[1] - gap / 2.0),
        (stations[1] + gap / 2.0, x_rear),
    )
    segments = []
    for index, (start, end) in enumerate(bounds, start=1):
        selector = Box(
            end - start,
            value(topper_base_outer_width) + 200.0,
            value(topper_front_height) + 100.0,
            align=(Align.MIN, Align.CENTER, Align.MIN),
        ).moved(Location((start, 0.0, 0.0)))
        segment = shell & selector
        segment.label = f"SHELL_SEGMENT_{index}_PROVISIONAL"
        segment.color = SECTION_COLOR
        segments.append(segment)
    return Compound(label="SECTIONED_MODULAR_SHELL", children=segments)


def make_section_joint_interfaces() -> Compound:
    """Return internal splice doublers and indexing keys for both section joints."""
    inner = _make_inset_envelope(value(wall_nominal_thickness))
    deeper = _make_inset_envelope(
        value(wall_nominal_thickness) + value(section_joint_doubler_thickness)
    )
    doubler_shell = inner - deeper
    key_x, key_y, key_z = value(section_joint_alignment_key_size)
    joint_groups = []
    for index, station in enumerate(_section_joint_stations(), start=1):
        band_selector = Box(
            value(section_joint_doubler_width),
            value(topper_base_outer_width),
            value(topper_front_height),
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        ).moved(Location((station, 0.0, 0.0)))
        doubler = doubler_shell & band_selector
        doubler.label = f"SECTION_JOINT_{index}_INTERNAL_DOUBLER_PROVISIONAL"
        doubler.color = JOINT_COLOR

        keys = []
        for side, sign in (("DRIVER", 1.0), ("PASSENGER", -1.0)):
            key = Box(
                key_x,
                key_y,
                key_z,
                align=(Align.CENTER, Align.CENTER, Align.MAX),
            ).moved(
                Location(
                    (
                        station,
                        sign * (value(topper_silhouette_stations)[2][4] / 10.0),
                        value(topper_silhouette_stations)[2][1]
                        - value(wall_nominal_thickness),
                    )
                )
            )
            key.label = f"SECTION_JOINT_{index}_{side}_ALIGNMENT_KEY_PROVISIONAL"
            key.color = JOINT_COLOR
            keys.append(key)
        joint_groups.append(
            Compound(
                label=f"SECTION_JOINT_{index}_INTERFACE_PROVISIONAL",
                children=[doubler, *keys],
            )
        )
    return Compound(label="SECTION_JOINT_INTERFACES", children=joint_groups)


def _frame_rails(center_x: float, side: str, sign: float, index: int) -> Compound:
    opening_x = value(module_opening_width)
    opening_z = value(module_opening_height)
    land = value(module_frame_land_width)
    depth = value(module_frame_depth)
    center_y = sign * (
        value(topper_base_outer_width) / 2.0 - depth / 2.0
    )
    center_z = value(module_bay_center_z)
    rails = [
        Box(opening_x + 2.0 * land, depth, land, align=(Align.CENTER,) * 3).moved(
            Location((center_x, center_y, center_z - opening_z / 2.0 - land / 2.0))
        ),
        Box(opening_x + 2.0 * land, depth, land, align=(Align.CENTER,) * 3).moved(
            Location((center_x, center_y, center_z + opening_z / 2.0 + land / 2.0))
        ),
        Box(land, depth, opening_z, align=(Align.CENTER,) * 3).moved(
            Location((center_x - opening_x / 2.0 - land / 2.0, center_y, center_z))
        ),
        Box(land, depth, opening_z, align=(Align.CENTER,) * 3).moved(
            Location((center_x + opening_x / 2.0 + land / 2.0, center_y, center_z))
        ),
    ]
    for rail_index, rail in enumerate(rails, start=1):
        rail.label = f"MODULE_FRAME_{side}_{index}_LAND_{rail_index}"
        rail.color = MODULE_FRAME_COLOR
    return Compound(
        label=f"MODULE_FRAME_{side}_{index}_COMMON_INTERFACE",
        children=rails,
    )


def make_module_frames() -> Compound:
    """Return six identical common-interface perimeter frames."""
    frames = []
    for side, sign in (("DRIVER", 1.0), ("PASSENGER", -1.0)):
        for index, center_x in enumerate(_module_bay_centers(), start=1):
            frames.append(_frame_rails(center_x, side, sign, index))
    return Compound(label="COMMON_MODULE_INTERFACE_FRAMES", children=frames)


def _panel_box(
    size_x: float,
    size_z: float,
    center_x: float,
    center_y: float,
    center_z: float,
    thickness: float | None = None,
):
    return Box(
        size_x,
        thickness if thickness is not None else value(module_panel_thickness),
        size_z,
        align=(Align.CENTER,) * 3,
    ).moved(Location((center_x, center_y, center_z)))


def _make_module_panel(
    variant: str,
    center_x: float,
    side: str,
    sign: float,
    index: int,
) -> Compound:
    """Build one cartridge inside the shared opening envelope."""
    width = value(module_opening_width)
    height = value(module_opening_height)
    thickness = value(module_panel_thickness)
    center_z = value(module_bay_center_z)
    center_y = sign * (value(topper_base_outer_width) / 2.0 + thickness / 2.0)
    children = []

    if variant == "SOLID":
        children.append(_panel_box(width, height, center_x, center_y, center_z))
        color = MODULE_SOLID_COLOR
    elif variant == "WINDOW":
        border = value(module_frame_land_width)
        children.extend(
            [
                _panel_box(width, border, center_x, center_y, center_z - height / 2.0 + border / 2.0),
                _panel_box(width, border, center_x, center_y, center_z + height / 2.0 - border / 2.0),
                _panel_box(border, height - 2.0 * border, center_x - width / 2.0 + border / 2.0, center_y, center_z),
                _panel_box(border, height - 2.0 * border, center_x + width / 2.0 - border / 2.0, center_y, center_z),
                _panel_box(width - 2.0 * border, height - 2.0 * border, center_x, center_y, center_z, thickness / 2.0),
            ]
        )
        color = MODULE_WINDOW_COLOR
    elif variant == "MESH":
        border = value(module_frame_land_width)
        children.extend(
            [
                _panel_box(width, border, center_x, center_y, center_z - height / 2.0 + border / 2.0),
                _panel_box(width, border, center_x, center_y, center_z + height / 2.0 - border / 2.0),
                _panel_box(border, height, center_x - width / 2.0 + border / 2.0, center_y, center_z),
                _panel_box(border, height, center_x + width / 2.0 - border / 2.0, center_y, center_z),
            ]
        )
        for offset_x in (-width / 4.0, 0.0, width / 4.0):
            children.append(_panel_box(8.0, height - 2.0 * border, center_x + offset_x, center_y, center_z))
        for offset_z in (-height / 3.0, 0.0, height / 3.0):
            children.append(_panel_box(width - 2.0 * border, 8.0, center_x, center_y, center_z + offset_z))
        color = MODULE_MESH_COLOR
    elif variant == "RECOVERY_BOARD":
        children.append(_panel_box(width, height, center_x, center_y, center_z))
        for offset_x in (-width / 4.0, width / 4.0):
            children.append(
                _panel_box(26.0, height - 50.0, center_x + offset_x, center_y + sign * 10.0, center_z, 12.0)
            )
        color = MODULE_RECOVERY_COLOR
    elif variant == "UTILITY":
        children.append(_panel_box(width, height, center_x, center_y, center_z))
        for offset_x in (-width / 4.0, width / 4.0):
            for offset_z in (-height / 4.0, height / 4.0):
                children.append(
                    _panel_box(24.0, 24.0, center_x + offset_x, center_y + sign * 8.0, center_z + offset_z, 8.0)
                )
        color = MODULE_UTILITY_COLOR
    else:
        raise ValueError(f"unsupported module variant: {variant}")

    for child_index, child in enumerate(children, start=1):
        child.label = f"MODULE_{side}_{index}_{variant}_PART_{child_index}"
        child.color = color
    return Compound(
        label=f"MODULE_{side}_{index}_{variant}_CARTRIDGE_PROVISIONAL",
        children=children,
    )


def make_module_cartridges() -> Compound:
    """Install all five required variants across the six common side bays."""
    allowed = set(value(module_variant_types))
    assignments = {
        "DRIVER": ("SOLID", "WINDOW", "MESH"),
        "PASSENGER": ("RECOVERY_BOARD", "UTILITY", "SOLID"),
    }
    assert set(variant for variants in assignments.values() for variant in variants) == allowed
    cartridges = []
    for side, sign in (("DRIVER", 1.0), ("PASSENGER", -1.0)):
        for index, (center_x, variant) in enumerate(
            zip(_module_bay_centers(), assignments[side]),
            start=1,
        ):
            cartridges.append(_make_module_panel(variant, center_x, side, sign, index))
    return Compound(label="SWAPPABLE_MODULE_CARTRIDGES", children=cartridges)


def make_base_flange_references() -> Compound:
    """Return two provisional longitudinal mounting flanges."""
    length = value(topper_overall_length)
    width = value(base_rail_width)
    height = value(base_rail_height)
    center = value(topper_base_outer_width) / 2.0 - width / 2.0
    flanges = []
    for side, sign in (("DRIVER", 1.0), ("PASSENGER", -1.0)):
        flange = Box(
            length,
            width,
            height,
            align=(Align.MIN, Align.CENTER, Align.MIN),
        ).moved(Location((value(cab_to_topper_nominal_gap), sign * center, 0.0)))
        flange.label = f"BASE_FLANGE_{side}_PROVISIONAL"
        flange.color = FLANGE_BLUE
        flanges.append(flange)
    return Compound(label="BASE_FLANGES_PROVISIONAL", children=flanges)


def make_shell_datums() -> Compound:
    """Return visible review artifacts for the three controlling shell datums."""
    thickness = value(datum_display_thickness)
    length = value(topper_overall_length)
    width = value(topper_base_outer_width)
    height = value(topper_front_height)
    x_front = value(cab_to_topper_nominal_gap)

    mounting = Box(
        length,
        width,
        thickness,
        align=(Align.MIN, Align.CENTER, Align.MAX),
    ).moved(Location((x_front, 0.0, 0.0)))
    mounting.label = "DATUM_A_BED_RAIL_MOUNTING_PLANE_Z0"

    centerline = Box(
        length,
        thickness,
        height,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    ).moved(Location((x_front, 0.0, 0.0)))
    centerline.label = "DATUM_B_VEHICLE_CENTERLINE_Y0"

    rear = Box(
        thickness,
        width,
        thickness,
        align=(Align.MAX, Align.CENTER, Align.CENTER),
    ).moved(Location((x_front + length, 0.0, 0.0)))
    rear.label = "DATUM_C_REAR_CLOSURE_PLANE_MARKER"

    for datum in (mounting, centerline, rear):
        datum.color = DATUM_COLOR
    return Compound(label="SHELL_DATUMS", children=[mounting, centerline, rear])


def make_shell_keepouts() -> Compound:
    """Reserve calibration and rear-hatch volumes without claiming fitment."""
    x_front = value(cab_to_topper_nominal_gap)
    length = value(topper_overall_length)
    width = value(topper_base_outer_width)
    depth = value(base_interface_keepout_depth)
    base = Box(
        length,
        width,
        depth,
        align=(Align.MIN, Align.CENTER, Align.MAX),
    ).moved(Location((x_front, 0.0, 0.0)))
    base.label = (
        "KEEP_OUT_BASE_INTERFACE_LATE_CALIBRATION_"
        + PLACEHOLDER_REQUIRING_SCAN.replace(" ", "_")
    )

    hatch_depth = value(datum_display_thickness)
    hatch_width = value(rear_hatch_opening_width)
    hatch_height = value(rear_hatch_opening_height)
    hatch_border = value(base_rail_width) / 2.0
    hatch_x = x_front + length
    hatch_z = value(base_rail_height)
    hatch_parts = [
        Box(
            hatch_depth,
            hatch_width,
            hatch_border,
            align=(Align.MAX, Align.CENTER, Align.MIN),
        ).moved(Location((hatch_x, 0.0, hatch_z))),
        Box(
            hatch_depth,
            hatch_width,
            hatch_border,
            align=(Align.MAX, Align.CENTER, Align.MAX),
        ).moved(Location((hatch_x, 0.0, hatch_z + hatch_height))),
    ]
    for sign in (-1.0, 1.0):
        hatch_parts.append(
            Box(
                hatch_depth,
                hatch_border,
                hatch_height,
                align=(Align.MAX, Align.CENTER, Align.MIN),
            ).moved(
                Location(
                    (
                        hatch_x,
                        sign * (hatch_width / 2.0 - hatch_border / 2.0),
                        hatch_z,
                    )
                )
            )
        )
    hatch = Compound(children=hatch_parts)
    hatch.label = "KEEP_OUT_REAR_HATCH_STEP_8_PROVISIONAL"

    base.color = KEEP_OUT_COLOR
    for part in hatch_parts:
        part.color = KEEP_OUT_COLOR
    return Compound(label="SHELL_ENGINEERING_KEEP_OUTS", children=[base, hatch])


def make_load_path_references() -> Compound:
    """Mark provisional transverse shell bands; these are not capacity claims."""
    shell = make_engineered_shell()
    band_width = value(transverse_load_path_band_width)
    width = value(topper_base_outer_width)
    height = value(topper_front_height)
    bands = []
    for index, station in enumerate(
        (value(topper_crossbar_station_1), value(topper_crossbar_station_2)),
        start=1,
    ):
        cutter = Box(
            band_width,
            width,
            height,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        ).moved(Location((station, 0.0, 0.0)))
        band = shell & cutter
        band.label = f"LOAD_PATH_{index}_TRANSVERSE_SHELL_BAND_PROVISIONAL"
        band.color = LOAD_PATH_COLOR
        bands.append(band)
    return Compound(label="STRUCTURAL_LOAD_PATH_REFERENCES", children=bands)


def build_topper_engineered_subassembly() -> Compound:
    engineered = AssemblyHelper("10_TOPPER_ENGINEERED_SHELL")
    engineered.add(make_engineered_shell(), "TOPPER_ENGINEERED_SHELL")
    engineered.add(make_base_flange_references(), "BASE_FLANGES")
    engineered.add(make_shell_datums(), "SHELL_DATUMS")
    engineered.add(make_shell_keepouts(), "SHELL_ENGINEERING_KEEP_OUTS")
    engineered.add(make_load_path_references(), "STRUCTURAL_LOAD_PATH_REFERENCES")
    return engineered.build()


def build_topper_step7_subassembly() -> Compound:
    """Return the Step 7 shell, joints, and common-interface module system."""
    modular = AssemblyHelper("10_TOPPER_SECTIONED_MODULAR_SYSTEM")
    modular.add(make_sectioned_modular_shell(), "SECTIONED_MODULAR_SHELL")
    modular.add(make_section_joint_interfaces(), "SECTION_JOINT_INTERFACES")
    modular.add(make_module_frames(), "COMMON_MODULE_INTERFACE_FRAMES")
    modular.add(make_module_cartridges(), "SWAPPABLE_MODULE_CARTRIDGES")
    modular.add(make_base_flange_references(), "BASE_FLANGES")
    modular.add(make_shell_datums(), "SHELL_DATUMS")
    modular.add(make_shell_keepouts(), "SHELL_ENGINEERING_KEEP_OUTS")
    modular.add(make_load_path_references(), "STRUCTURAL_LOAD_PATH_REFERENCES")
    return modular.build()
