"""Authoritative provisional shell rebuilt from the selected sparse styling profiles."""

from build123d import Align, Box, Color, Compound, Edge, Face, Location, Wire, loft
from cadpy.assembly import AssemblyHelper

from parameters import (
    PLACEHOLDER_REQUIRING_SCAN,
    base_interface_keepout_depth,
    base_rail_height,
    base_rail_width,
    cab_to_topper_nominal_gap,
    datum_display_thickness,
    rear_hatch_opening_height,
    rear_hatch_opening_width,
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
