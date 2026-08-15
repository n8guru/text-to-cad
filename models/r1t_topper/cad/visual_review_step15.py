"""Re-embodied Step 15 exterior presentation assembly for operator review.

The side openings are now a shared, removable-module interface.  The window
insert is a separate flat pane; cage and toolbox inserts use the same aperture
datum, flange/seal land, retention pattern, and shell bridge.  This package is
still presentation-only and does not claim calibrated fitment, sealing,
capacity, or fabrication release.
"""

from build123d import Align, Axis, Box, Color, Compound, Cylinder, Edge, Face, Location, Plane, Rectangle, RectangleRounded, Wire, extrude, loft
from cadpy.assembly import AssemblyHelper

from parameters import (
    hatch_open_angle,
    hinge_axis,
    cab_to_topper_nominal_gap,
    rear_hatch_opening_height,
    rear_hatch_opening_width,
    topper_base_outer_width,
    topper_overall_length,
    topper_silhouette_stations,
    value,
    wall_nominal_thickness,
)
from rear_hatch import (
    make_drainage_management,
    make_hatch_mechanism_envelopes,
    make_hatch_opening_cutter,
    make_rear_hatch_frame,
    make_weather_seal,
)
from mount_interfaces import make_topper_crossbar_ports


CARBON_COLOR = Color(0.30, 0.34, 0.38, 1.0)
CARBON_EDGE_COLOR = Color(0.16, 0.19, 0.23, 1.0)
GLAZING_COLOR = Color(0.08, 0.38, 0.56, 0.92)
HATCH_CARBON_COLOR = Color(0.26, 0.30, 0.34, 1.0)
INTEGRATED_PORT_COLOR = Color(0.20, 0.24, 0.28, 1.0)

# Source-intent geometry: two broad side apertures on each side and two rounded
# lights in one rear hatch.  Each side aperture is a shared removable-module
# interface.  The shell bridge exceeds the 76 mm / 3 in minimum; the rear
# bridge is the specified 140 mm.
SIDE_WINDOW_X_RANGES = ((145.0, 690.0), (800.0, 1345.0))
SIDE_WINDOW_Z_RANGE = (145.0, 660.0)
SIDE_APERTURE_CORNER_RADIUS = 82.0
REAR_WINDOW_Y_RANGES = ((-605.0, -70.0), (70.0, 605.0))
REAR_WINDOW_Z_RANGE = (185.0, 605.0)
REAR_WINDOW_CORNER_RADIUS = 64.0
STRUCTURAL_CARBON_MINIMUM = 76.0
STRUCTURAL_MULLION_WIDTH = 110.0
REAR_MULLION_WIDTH = 140.0
SIDE_CUT_DEPTH = 360.0

# Shared side-insert contract.  These are provisional visual-design controls,
# not calibrated fitment dimensions.
SIDE_INTERFACE_SEAL_LAND = 22.0
SIDE_INTERFACE_RETENTION_DEPTH = 18.0
SIDE_INTERFACE_FASTENER_RADIUS = 7.0
SIDE_INTERFACE_FASTENER_EDGE_OFFSET = 34.0
SIDE_INSERT_PANE_THICKNESS = 8.0
SIDE_INSERT_NORMAL_EXPLODE = 115.0
SIDE_INSERT_MATING_CONTRACT = {
    "datum": "side-aperture X/Z rounded profile; constant side-Y datum plane",
    "flange_seal_land_mm": SIDE_INTERFACE_SEAL_LAND,
    "retention": "four M-sized provisional fastener envelopes on insert flange",
    "load_path": "perimeter land into continuous shell; 110 mm carbon bridge remains between bays",
    "insert_contract": "same outer profile, flange depth, seal land, and fastener centers for WINDOW/CAGE/TOOLBOX",
}

# Presentation-only A-surface adjustment.  The authoritative Step 11 shell is
# unchanged; this derivative deliberately carries a tighter crown and softer
# shoulder break so the operator can judge the R1S-like roof language in a
# vehicle context rather than against an isolated rectangular envelope.
ROOF_WIDTH_SCALE = 0.88
SHOULDER_WIDTH_REDUCTION = 18.0
CROWN_LIFT = 18.0


def _rounded_section(x: float, height: float, base_width: float, shoulder_width: float, roof_width: float) -> Face:
    """A visibly radiused R1S-like YZ section, intentionally unlike the old box profile."""
    half_base, half_shoulder, half_roof = base_width / 2.0, shoulder_width / 2.0, roof_width / 2.0
    shoulder_z = height * 0.54
    roof_edge_z = height * 0.87
    left_base, right_base = (x, -half_base, 0.0), (x, half_base, 0.0)
    right_shoulder, right_roof = (x, half_shoulder, shoulder_z), (x, half_roof, roof_edge_z)
    left_roof, left_shoulder = (x, -half_roof, roof_edge_z), (x, -half_shoulder, shoulder_z)
    return Face.make_surface(Wire([
        Edge.make_line(left_base, right_base),
        Edge.make_three_point_arc(right_base, (x, half_base + 28.0, height * 0.28), right_shoulder),
        Edge.make_three_point_arc(right_shoulder, (x, half_shoulder + 22.0, height * 0.72), right_roof),
        Edge.make_three_point_arc(right_roof, (x, 0.0, height), left_roof),
        Edge.make_three_point_arc(left_roof, (x, -(half_shoulder + 22.0), height * 0.72), left_shoulder),
        Edge.make_three_point_arc(left_shoulder, (x, -(half_base + 28.0), height * 0.28), left_base),
    ]))


def _rounded_presentation_envelope(inset: float = 0.0):
    sections = [
        _rounded_section(
            value(cab_to_topper_nominal_gap) + fraction * value(topper_overall_length),
            height + _crown * CROWN_LIFT / 35.0 - inset,
            base_width - 2.0 * inset,
            shoulder_width - SHOULDER_WIDTH_REDUCTION - 2.0 * inset,
            roof_width * ROOF_WIDTH_SCALE - 2.0 * inset,
        )
        for fraction, height, base_width, shoulder_width, roof_width, _crown in value(topper_silhouette_stations)
    ]
    return loft(sections, ruled=False)


def _rounded_presentation_shell():
    return _rounded_presentation_envelope() - _rounded_presentation_envelope(value(wall_nominal_thickness))


def _side_window_selector(x_min: float, x_max: float, sign: float):
    side_y = value(topper_base_outer_width) / 2.0
    width, height = x_max - x_min, SIDE_WINDOW_Z_RANGE[1] - SIDE_WINDOW_Z_RANGE[0]
    profile = Plane.XZ * (
        RectangleRounded(width, height, min(SIDE_APERTURE_CORNER_RADIUS, width / 2.0 - 1.0, height / 2.0 - 1.0))
        if SIDE_APERTURE_CORNER_RADIUS > 0.0 else Rectangle(width, height)
    )
    return extrude(profile, amount=SIDE_CUT_DEPTH / 2.0, both=True).moved(
        Location(((x_min + x_max) / 2.0, sign * side_y, sum(SIDE_WINDOW_Z_RANGE) / 2.0))
    )


def _rear_window_selector(y_min: float, y_max: float, depth: float = 2.0 * value(wall_nominal_thickness)):
    width, height = y_max - y_min, REAR_WINDOW_Z_RANGE[1] - REAR_WINDOW_Z_RANGE[0]
    profile = Plane.YZ * (
        RectangleRounded(width, height, REAR_WINDOW_CORNER_RADIUS)
        if REAR_WINDOW_CORNER_RADIUS > 0.0 else Rectangle(width, height)
    )
    return extrude(profile, amount=depth / 2.0, both=True).moved(
        Location(
            (
                value(topper_overall_length) + value(wall_nominal_thickness) / 2.0,
                (y_min + y_max) / 2.0,
                sum(REAR_WINDOW_Z_RANGE) / 2.0,
            )
        )
    )


def make_side_window_cutters() -> Compound:
    cutters = []
    for side, sign in (("DRIVER", 1.0), ("PASSENGER", -1.0)):
        for index, (x_min, x_max) in enumerate(SIDE_WINDOW_X_RANGES, start=1):
            cutter = _side_window_selector(x_min, x_max, sign)
            cutter.label = f"SIDE_WINDOW_{side}_{index}_CUTTER_PRESENTATION_ONLY"
            cutters.append(cutter)
    return Compound(label="SIDE_WINDOW_CUTTERS_PRESENTATION_ONLY", children=cutters)


def make_continuous_carbon_shell():
    """One rounded shell, with positive carbon rails around every opening."""
    shell = _rounded_presentation_shell() - make_hatch_opening_cutter()
    for cutter in make_side_window_cutters().children:
        shell = shell - cutter
    shell.label = "CONTINUOUS_ROUNDED_R1S_LIKE_CARBON_SHELL_PRESENTATION_ONLY"
    shell.color = CARBON_COLOR
    return shell


def _side_aperture_profile(x_min: float, x_max: float):
    width, height = x_max - x_min, SIDE_WINDOW_Z_RANGE[1] - SIDE_WINDOW_Z_RANGE[0]
    radius = min(SIDE_APERTURE_CORNER_RADIUS, width / 2.0 - 1.0, height / 2.0 - 1.0)
    return Plane.XZ * (RectangleRounded(width, height, radius) if radius > 0.0 else Rectangle(width, height))


def _side_aperture_y(sign: float) -> float:
    return sign * value(topper_base_outer_width) / 2.0


def _side_insert_panel(x_min: float, x_max: float, sign: float, depth: float, normal_offset: float = 0.0):
    """Flat constant-Y insert envelope for every module variant."""
    panel = extrude(_side_aperture_profile(x_min, x_max), amount=depth / 2.0, both=True)
    return panel.moved(
        Location(
            (
                (x_min + x_max) / 2.0,
                _side_aperture_y(sign + 0.0) + sign * normal_offset,
                sum(SIDE_WINDOW_Z_RANGE) / 2.0,
            )
        )
    )


def _insert_frame(x_min: float, x_max: float, sign: float, normal_offset: float = 0.0) -> Compound:
    """Perimeter mating flange carried by every insert type."""
    depth = SIDE_INTERFACE_RETENTION_DEPTH
    y = _side_aperture_y(sign) + sign * normal_offset
    z_min, z_max = SIDE_WINDOW_Z_RANGE
    land = SIDE_INTERFACE_SEAL_LAND
    children = []
    for label, x, z, sx, sz in (
        ("LEFT", x_min - land / 2.0, (z_min + z_max) / 2.0, land, z_max - z_min + 2.0 * land),
        ("RIGHT", x_max + land / 2.0, (z_min + z_max) / 2.0, land, z_max - z_min + 2.0 * land),
        ("LOW", (x_min + x_max) / 2.0, z_min - land / 2.0, x_max - x_min, land),
        ("HIGH", (x_min + x_max) / 2.0, z_max + land / 2.0, x_max - x_min, land),
    ):
        bar = Box(sx, depth, sz, align=(Align.CENTER, Align.CENTER, Align.CENTER)).moved(Location((x, y, z)))
        bar.label = f"SIDE_INSERT_FLANGE_{label}_MATING_CONTRACT"
        children.append(bar)
    return Compound(label="SIDE_INSERT_PERIMETER_FLANGE_MATING_CONTRACT", children=children)


def _insert_fasteners(x_min: float, x_max: float, sign: float, normal_offset: float = 0.0) -> Compound:
    y = _side_aperture_y(sign) + sign * normal_offset
    z_min, z_max = SIDE_WINDOW_Z_RANGE
    offset = SIDE_INTERFACE_FASTENER_EDGE_OFFSET
    children = []
    for index, (x, z) in enumerate(
        ((x_min + offset, z_min + offset), (x_max - offset, z_min + offset),
         (x_min + offset, z_max - offset), (x_max - offset, z_max - offset)),
        start=1,
    ):
        fastener = Cylinder(
            SIDE_INTERFACE_FASTENER_RADIUS,
            SIDE_INTERFACE_RETENTION_DEPTH + 8.0,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
            rotation=(90.0, 0.0, 0.0),
        ).moved(Location((x, y, z)))
        fastener.label = f"SIDE_INSERT_RETENTION_FASTENER_{index}_MATING_CONTRACT"
        children.append(fastener)
    return Compound(label="SIDE_INSERT_RETENTION_PATTERN_MATING_CONTRACT", children=children)


def make_side_aperture_interface(side: str, index: int, x_min: float, x_max: float, sign: float) -> Compound:
    """Common shell-side datum, seal land, retention and load-path package."""
    frame = _insert_frame(x_min, x_max, sign)
    frame.label = f"SHARED_SIDE_APERTURE_INTERFACE_{side}_{index}"
    fasteners = _insert_fasteners(x_min, x_max, sign)
    fasteners.label = f"SHARED_SIDE_APERTURE_RETENTION_{side}_{index}"
    # The positive shell land is the load path around the cut.  It intentionally
    # shares material with the continuous carbon shell instead of floating as a
    # separate ornamental surround.
    bridge = Box(
        x_max - x_min,
        60.0,
        30.0,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    ).moved(Location(((x_min + x_max) / 2.0, _side_aperture_y(sign) - sign * 20.0, SIDE_WINDOW_Z_RANGE[0] - 35.0)))
    bridge.label = f"SIDE_APERTURE_LOAD_PATH_INTO_SHELL_{side}_{index}"
    bridge.color = CARBON_EDGE_COLOR
    return Compound(label=f"SIDE_APERTURE_INTERFACE_{side}_{index}", children=[frame, fasteners, bridge])


def make_side_aperture_interfaces() -> Compound:
    children = []
    for side, sign in (("DRIVER", 1.0), ("PASSENGER", -1.0)):
        for index, (x_min, x_max) in enumerate(SIDE_WINDOW_X_RANGES, start=1):
            children.append(make_side_aperture_interface(side, index, x_min, x_max, sign))
    return Compound(label="SHARED_SIDE_APERTURE_INTERFACES", children=children)


def make_flat_window_insert(side: str, index: int, x_min: float, x_max: float, sign: float, normal_offset: float = 0.0) -> Compound:
    """Separate planar glazing part with the common insert-side mating contract."""
    pane = _side_insert_panel(x_min, x_max, sign, SIDE_INSERT_PANE_THICKNESS, normal_offset)
    pane.label = f"FLAT_WINDOW_INSERT_{side}_{index}_PLANAR_MATING_CONTRACT"
    pane.color = GLAZING_COLOR
    frame = _insert_frame(x_min, x_max, sign, normal_offset)
    frame.label = f"FLAT_WINDOW_INSERT_FLANGE_{side}_{index}"
    fasteners = _insert_fasteners(x_min, x_max, sign, normal_offset)
    fasteners.label = f"FLAT_WINDOW_INSERT_RETENTION_{side}_{index}"
    return Compound(label=f"WINDOW_INSERT_{side}_{index}_SEPARATE_PART", children=[pane, frame, fasteners])


def make_cage_insert(side: str, index: int, x_min: float, x_max: float, sign: float, normal_offset: float = 0.0) -> Compound:
    """Open cage cartridge using the same perimeter, datum and retention pattern."""
    x_mid, z_mid = (x_min + x_max) / 2.0, sum(SIDE_WINDOW_Z_RANGE) / 2.0
    y = _side_aperture_y(sign) + sign * normal_offset
    width, height = x_max - x_min, SIDE_WINDOW_Z_RANGE[1] - SIDE_WINDOW_Z_RANGE[0]
    bars = list(_insert_frame(x_min, x_max, sign, normal_offset).children)
    for n, x in enumerate((x_min + width * 0.33, x_min + width * 0.66), start=1):
        bar = Box(18.0, 12.0, height, align=(Align.CENTER, Align.CENTER, Align.CENTER)).moved(Location((x, y, z_mid)))
        bar.label = f"CAGE_INSERT_VERTICAL_BAR_{n}"
        bars.append(bar)
    for n, z in enumerate((SIDE_WINDOW_Z_RANGE[0] + height * 0.33, SIDE_WINDOW_Z_RANGE[0] + height * 0.66), start=1):
        bar = Box(width, 12.0, 18.0, align=(Align.CENTER, Align.CENTER, Align.CENTER)).moved(Location((x_mid, y, z)))
        bar.label = f"CAGE_INSERT_HORIZONTAL_BAR_{n}"
        bars.append(bar)
    fasteners = _insert_fasteners(x_min, x_max, sign, normal_offset)
    return Compound(
        label=f"CAGE_INSERT_{side}_{index}_SEPARATE_PART",
        children=[*bars, *fasteners.children],
    )


def make_toolbox_insert(side: str, index: int, x_min: float, x_max: float, sign: float, normal_offset: float = 0.0) -> Compound:
    """Opaque service/toolbox cartridge using the common mating contract."""
    width, height = x_max - x_min, SIDE_WINDOW_Z_RANGE[1] - SIDE_WINDOW_Z_RANGE[0]
    panel = _side_insert_panel(x_min, x_max, sign, 42.0, normal_offset)
    panel.label = f"TOOLBOX_INSERT_PANEL_{side}_{index}"
    panel.color = Color(0.18, 0.20, 0.22, 1.0)
    frame = _insert_frame(x_min, x_max, sign, normal_offset)
    frame.label = f"TOOLBOX_INSERT_FLANGE_{side}_{index}"
    handle = Box(160.0, 18.0, 18.0, align=(Align.CENTER, Align.CENTER, Align.CENTER)).moved(
        Location(((x_min + x_max) / 2.0, _side_aperture_y(sign) + sign * (normal_offset + 25.0), SIDE_WINDOW_Z_RANGE[1] - 64.0))
    )
    handle.label = f"TOOLBOX_INSERT_SERVICE_HANDLE_{side}_{index}"
    fasteners = _insert_fasteners(x_min, x_max, sign, normal_offset)
    return Compound(label=f"TOOLBOX_INSERT_{side}_{index}_SEPARATE_PART", children=[panel, frame, handle, fasteners])


def make_flat_window_inserts() -> Compound:
    children = []
    for side, sign in (("DRIVER", 1.0), ("PASSENGER", -1.0)):
        for index, (x_min, x_max) in enumerate(SIDE_WINDOW_X_RANGES, start=1):
            children.append(make_flat_window_insert(side, index, x_min, x_max, sign))
    return Compound(label="FLAT_WINDOW_INSERTS_SEPARATE_PARTS", children=children)


def make_side_insert_interchangeability_proof() -> Compound:
    """Exploded proof: one aperture datum, three interchangeable inserts."""
    side, sign, index = "DRIVER", 1.0, 1
    x_min, x_max = SIDE_WINDOW_X_RANGES[0]
    interface = make_side_aperture_interface(side, index, x_min, x_max, sign)
    window = make_flat_window_insert(side, index, x_min, x_max, sign, SIDE_INSERT_NORMAL_EXPLODE * 0.28)
    cage = make_cage_insert(side, index, x_min, x_max, sign, SIDE_INSERT_NORMAL_EXPLODE * 0.62)
    toolbox = make_toolbox_insert(side, index, x_min, x_max, sign, SIDE_INSERT_NORMAL_EXPLODE)
    for item, name in ((interface, "COMMON_APERTURE_DATUM_FLANGE_SEAL_RETENTION"), (window, "WINDOW_INSERT_SAME_INTERFACE"), (cage, "CAGE_INSERT_SAME_INTERFACE"), (toolbox, "TOOLBOX_INSERT_SAME_INTERFACE")):
        item.label = f"SIDE_INSERT_INTERCHANGEABILITY_{name}"
    return Compound(label="SIDE_INSERT_INTERCHANGEABILITY_PROOF", children=[interface, window, cage, toolbox])


def make_rear_hatch_glazing() -> Compound:
    """Two broad panes separated by a substantial vertical carbon bridge."""
    panes = []
    for index, (y_min, y_max) in enumerate(REAR_WINDOW_Y_RANGES, start=1):
        pane = _rear_window_selector(y_min, y_max, depth=6.0)
        pane.label = f"REAR_HATCH_GLAZING_{index}_PRESENTATION_ONLY"
        pane.color = GLAZING_COLOR
        panes.append(pane)
    return Compound(label="REAR_HATCH_TWO_PANE_GLAZING_PRESENTATION_ONLY", children=panes)


def make_visual_review_hatch_leaf():
    """One closed carbon hatch leaf with continuous corners and two lights."""
    x = value(topper_overall_length)
    leaf = Box(
        value(wall_nominal_thickness),
        value(rear_hatch_opening_width) + 2.0 * value(wall_nominal_thickness),
        value(rear_hatch_opening_height) + 2.0 * value(wall_nominal_thickness),
        align=(Align.MIN, Align.CENTER, Align.MIN),
    ).moved(Location((x, 0.0, 18.0)))
    for y_min, y_max in REAR_WINDOW_Y_RANGES:
        leaf = leaf - _rear_window_selector(y_min, y_max)
    leaf.label = "SINGLE_REAR_HATCH_LEAF_TWO_PANE_CONTINUOUS_CORNERS_PRESENTATION_ONLY"
    leaf.color = HATCH_CARBON_COLOR
    return leaf


def make_hatch_frame_presentation() -> Compound:
    frame = make_rear_hatch_frame()
    for bar in frame.children:
        bar.color = CARBON_EDGE_COLOR
        bar.label = bar.label.replace("PROVISIONAL", "PRESENTATION_ONLY")
    frame.label = "SINGLE_REAR_HATCH_FRAME_CONTINUOUS_PRESENTATION_ONLY"
    return frame


def make_hatch_b_side_engineering() -> Compound:
    """Resolved B-side package: frame/panel, hinge, latch, seal, gutter/drain and open leaf.

    It is retained as an inspectable engineering derivative rather than added to
    the clean exterior render, where an open leaf or service envelopes would
    obscure the requested closed-product silhouette.
    """
    closed_leaf = make_visual_review_hatch_leaf()
    closed_leaf.label = "REAR_HATCH_PANEL_CLOSED_B_SIDE_PRESENTATION_ONLY"
    open_leaf = make_visual_review_hatch_leaf().rotate(
        Axis(value(hinge_axis)[0], (0.0, 1.0, 0.0)), -value(hatch_open_angle)
    )
    open_leaf.label = "REAR_HATCH_PANEL_OPEN_B_SIDE_PRESENTATION_ONLY"
    mechanism = make_hatch_mechanism_envelopes()
    mechanism.label = "REAR_HATCH_HINGE_LATCH_B_SIDE_PRESENTATION_ONLY"
    seal = make_weather_seal()
    seal.label = "REAR_HATCH_CONTINUOUS_SEAL_B_SIDE_PRESENTATION_ONLY"
    drainage = make_drainage_management()
    drainage.label = "REAR_HATCH_GUTTER_DRAINAGE_B_SIDE_PRESENTATION_ONLY"
    return Compound(
        label="REAR_HATCH_B_SIDE_ENGINEERING_PRESENTATION_ONLY",
        children=[make_hatch_frame_presentation(), closed_leaf, open_leaf, mechanism, seal, drainage],
    )


def make_integrated_crossbar_ports_presentation() -> Compound:
    """Topper-owned shell ports only; never a freestanding crossbar."""
    # The source hardpoint datum follows the earlier, flatter roof.  Re-seat the
    # eight interface envelopes into this re-embodied curved crown so each is a
    # shell feature rather than a bar floating over it.
    children = [item.moved(Location((0.0, 0.0, -60.0))) for item in make_topper_crossbar_ports().children]
    for item in children:
        item.label = item.label.replace("_PROVISIONAL", "_INTEGRATED_PRESENTATION_ONLY")
        if "INTEGRATED_PRESENTATION_ONLY" not in item.label:
            item.label = item.label.replace("OEM_ACCESSORY_PORT_PROFILE_", "INTEGRATED_SHELL_PORT_") + "_INTEGRATED_PRESENTATION_ONLY"
        item.color = INTEGRATED_PORT_COLOR
    return Compound(label="INTEGRATED_TOPPER_CROSSBAR_PORTS", children=children)


def make_r1t_presentation_context() -> Compound:
    """A restrained vehicle envelope so the operator can judge silhouette and scale.

    This is not a fitment model and intentionally omits the engineering
    keep-outs, datums, anchors, and service geometry from the reference package.
    The pickup cues are enough to make the topper read as an R1T product rather
    than an isolated box: cab mass, bed deck, tailgate, rails, and four wheels.
    """
    context_color = Color(0.40, 0.44, 0.48, 1.0)
    glass_color = Color(0.06, 0.12, 0.16, 0.9)
    tire_color = Color(0.035, 0.04, 0.045, 1.0)
    wheel_color = Color(0.22, 0.25, 0.28, 1.0)

    bed = Box(
        value(topper_overall_length),
        value(topper_base_outer_width) - 150.0,
        120.0,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    ).moved(Location((0.0, 0.0, -120.0)))
    bed.label = "R1T_BED_CONTEXT"
    bed.color = context_color

    rail_children = []
    for side, sign in (("DRIVER", 1.0), ("PASSENGER", -1.0)):
        rail = Box(
            value(topper_overall_length),
            90.0,
            90.0,
            align=(Align.MIN, Align.CENTER, Align.MIN),
        ).moved(Location((0.0, sign * (value(topper_base_outer_width) / 2.0 - 45.0), -10.0)))
        rail.label = f"R1T_{side}_BED_RAIL_CONTEXT"
        rail.color = wheel_color
        rail_children.append(rail)

    tailgate = Box(
        85.0,
        value(topper_base_outer_width) - 150.0,
        500.0,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    ).moved(Location((value(topper_overall_length) - 85.0, 0.0, -620.0)))
    tailgate.label = "R1T_TAILGATE_CONTEXT"
    tailgate.color = context_color

    cab = Box(
        520.0,
        1650.0,
        760.0,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    ).moved(Location((-520.0, 0.0, -120.0)))
    cab.label = "R1T_CAB_CONTEXT"
    cab.color = context_color
    cab_roof = Box(
        520.0,
        1540.0,
        70.0,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    ).moved(Location((-520.0, 0.0, 640.0)))
    cab_roof.label = "R1T_CAB_ROOF_CONTEXT"
    cab_roof.color = wheel_color

    side_glass = []
    for side, sign in (("DRIVER", 1.0), ("PASSENGER", -1.0)):
        window = Box(
            340.0,
            12.0,
            280.0,
            align=(Align.MIN, Align.CENTER, Align.MIN),
        ).moved(Location((-410.0, sign * 826.0, 280.0)))
        window.label = f"R1T_{side}_CAB_GLASS_CONTEXT"
        window.color = glass_color
        side_glass.append(window)

    wheels = []
    for axle_x in (170.0, 1110.0):
        for side, sign in (("DRIVER", 1.0), ("PASSENGER", -1.0)):
            tire = Cylinder(
                245.0,
                180.0,
                align=(Align.CENTER, Align.CENTER, Align.CENTER),
                rotation=(90.0, 0.0, 0.0),
            ).moved(Location((axle_x, sign * 875.0, -270.0)))
            tire.label = f"R1T_{side}_{int(axle_x)}_WHEEL_CONTEXT"
            tire.color = tire_color
            wheels.append(tire)
            hub = Cylinder(
                105.0,
                186.0,
                align=(Align.CENTER, Align.CENTER, Align.CENTER),
                rotation=(90.0, 0.0, 0.0),
            ).moved(Location((axle_x, sign * 878.0, -270.0)))
            hub.label = f"R1T_{side}_{int(axle_x)}_HUB_CONTEXT"
            hub.color = wheel_color
            wheels.append(hub)

    return Compound(
        label="R1T_VEHICLE_PRESENTATION_CONTEXT",
        children=[bed, *rail_children, tailgate, cab, cab_roof, *side_glass, *wheels],
    )


def gen_step():
    assembly = AssemblyHelper("R1T_TOPPER_STEP15_OPERATOR_VISUAL")
    assembly.add(make_r1t_presentation_context(), "R1T_VEHICLE_PRESENTATION_CONTEXT")
    assembly.add(make_continuous_carbon_shell(), "CONTINUOUS_ROUNDED_CARBON_SHELL")
    assembly.add(make_side_aperture_interfaces(), "SHARED_SIDE_APERTURE_INTERFACES")
    assembly.add(make_flat_window_inserts(), "FLAT_WINDOW_INSERTS_SEPARATE_PARTS")
    assembly.add(make_side_insert_interchangeability_proof(), "SIDE_INSERT_INTERCHANGEABILITY_PROOF")
    assembly.add(make_visual_review_hatch_leaf(), "SINGLE_REAR_HATCH_LEAF")
    assembly.add(make_rear_hatch_glazing(), "REAR_HATCH_TWO_PANE_GLAZING")
    assembly.add(make_integrated_crossbar_ports_presentation(), "INTEGRATED_TOPPER_CROSSBAR_PORTS")
    return assembly.build()
