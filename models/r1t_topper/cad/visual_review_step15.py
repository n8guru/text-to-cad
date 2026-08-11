"""Re-embodied Step 15 exterior presentation assembly for operator review.

This is deliberately a fresh visual embodiment, rather than a reduction of the
old six-cartridge presentation.  It starts with the continuous rounded sparse
profile loft, cuts two broad, shell-conformal side lights per side, and closes
the rear with one real two-light hatch.  The presentation model is not a
fitment, sealing, capacity, or fabrication-release claim.
"""

from build123d import Align, Axis, Box, Color, Compound, Edge, Face, Location, Plane, Rectangle, RectangleRounded, Wire, extrude, loft
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


CARBON_COLOR = Color(0.18, 0.21, 0.24, 1.0)
CARBON_EDGE_COLOR = Color(0.08, 0.10, 0.13, 1.0)
GLAZING_COLOR = Color(0.08, 0.38, 0.56, 0.92)
HATCH_CARBON_COLOR = Color(0.14, 0.17, 0.20, 1.0)
INTEGRATED_PORT_COLOR = Color(0.11, 0.13, 0.16, 1.0)

# Source-intent geometry: two broad, rounded lights on each side and two
# rounded lights in one rear hatch.  The side bridge exceeds the 76 mm / 3 in
# minimum; the rear bridge is the specified 140 mm.
SIDE_WINDOW_X_RANGES = ((145.0, 690.0), (800.0, 1345.0))
SIDE_WINDOW_Z_RANGE = (145.0, 660.0)
WINDOW_CORNER_RADIUS = 82.0
REAR_WINDOW_Y_RANGES = ((-605.0, -70.0), (70.0, 605.0))
REAR_WINDOW_Z_RANGE = (185.0, 605.0)
REAR_WINDOW_CORNER_RADIUS = 64.0
STRUCTURAL_CARBON_MINIMUM = 76.0
STRUCTURAL_MULLION_WIDTH = 110.0
REAR_MULLION_WIDTH = 140.0
SIDE_CUT_DEPTH = 360.0


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
            height - inset,
            base_width - 2.0 * inset,
            shoulder_width - 2.0 * inset,
            roof_width - 2.0 * inset,
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
        RectangleRounded(width, height, min(WINDOW_CORNER_RADIUS, width / 2.0 - 1.0, height / 2.0 - 1.0))
        if WINDOW_CORNER_RADIUS > 0.0 else Rectangle(width, height)
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


def make_curved_side_glazing() -> Compound:
    """Shell-conformal lights, intersected from the rounded outer skin."""
    glazing_skin = _rounded_presentation_envelope() - _rounded_presentation_envelope(8.0)
    panes = []
    for side, sign in (("DRIVER", 1.0), ("PASSENGER", -1.0)):
        for index, (x_min, x_max) in enumerate(SIDE_WINDOW_X_RANGES, start=1):
            pane = glazing_skin & _side_window_selector(x_min, x_max, sign)
            pane.label = f"CURVED_SIDE_GLAZING_{side}_{index}_PRESENTATION_ONLY"
            pane.color = GLAZING_COLOR
            panes.append(pane)
    return Compound(label="CURVED_SIDE_GLAZING_PRESENTATION_ONLY", children=panes)


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


def gen_step():
    assembly = AssemblyHelper("R1T_TOPPER_STEP15_OPERATOR_VISUAL")
    assembly.add(make_continuous_carbon_shell(), "CONTINUOUS_ROUNDED_CARBON_SHELL")
    assembly.add(make_curved_side_glazing(), "CURVED_SIDE_GLAZING")
    assembly.add(make_visual_review_hatch_leaf(), "SINGLE_REAR_HATCH_LEAF")
    assembly.add(make_rear_hatch_glazing(), "REAR_HATCH_TWO_PANE_GLAZING")
    assembly.add(make_integrated_crossbar_ports_presentation(), "INTEGRATED_TOPPER_CROSSBAR_PORTS")
    return assembly.build()
