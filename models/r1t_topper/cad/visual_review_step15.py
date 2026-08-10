"""Step 15 exterior presentation assembly for operator_visual review.

This is a deliberately presentation-only derivative of the verified Step 11
shell.  It keeps the five sparse silhouette stations visible as one continuous
loft, then adds substantial carbon mullions, shell-conformal glazing, and one
clean rear hatch leaf.  It does not replace the authoritative Step 11 CAD.
"""

from build123d import Align, Box, Color, Compound, Location
from cadpy.assembly import AssemblyHelper

from parameters import (
    rear_hatch_opening_height,
    rear_hatch_opening_width,
    seal_land_width,
    topper_base_outer_width,
    topper_overall_length,
    value,
    wall_nominal_thickness,
)
from rear_hatch import (
    make_closed_hatch_leaf,
    make_hatch_opening_cutter,
    make_rear_hatch_frame,
)
from topper_envelope import (
    _make_inset_envelope,
    make_engineered_shell,
    make_master_topper_envelope,
)


CARBON_COLOR = Color(0.18, 0.21, 0.24, 1.0)
CARBON_EDGE_COLOR = Color(0.08, 0.10, 0.13, 1.0)
GLAZING_COLOR = Color(0.08, 0.38, 0.56, 0.92)
HATCH_CARBON_COLOR = Color(0.14, 0.17, 0.20, 1.0)

# Three windows per side, with 110 mm structural mullions (> 3 in / 76 mm).
SIDE_WINDOW_X_RANGES = ((120.0, 455.0), (565.0, 900.0), (1010.0, 1345.0))
SIDE_WINDOW_Z_RANGE = (160.0, 660.0)
STRUCTURAL_MULLION_WIDTH = 110.0
SIDE_CUT_DEPTH = 320.0

# One rear opening/pane: no center split and no stacked/doubled hatch leaf.
REAR_WINDOW_Y_RANGE = (-560.0, 560.0)
REAR_WINDOW_Z_RANGE = (190.0, 600.0)


def _side_window_selector(x_min: float, x_max: float, sign: float):
    side_y = value(topper_base_outer_width) / 2.0
    return Box(
        x_max - x_min,
        SIDE_CUT_DEPTH,
        SIDE_WINDOW_Z_RANGE[1] - SIDE_WINDOW_Z_RANGE[0],
        align=(Align.MIN, Align.CENTER, Align.MIN),
    ).moved(Location((x_min, sign * side_y, SIDE_WINDOW_Z_RANGE[0])))


def make_side_window_cutters() -> Compound:
    cutters = []
    for side, sign in (("DRIVER", 1.0), ("PASSENGER", -1.0)):
        for index, (x_min, x_max) in enumerate(SIDE_WINDOW_X_RANGES, start=1):
            cutter = _side_window_selector(x_min, x_max, sign)
            cutter.label = f"SIDE_WINDOW_{side}_{index}_CUTTER_PRESENTATION_ONLY"
            cutters.append(cutter)
    return Compound(label="SIDE_WINDOW_CUTTERS_PRESENTATION_ONLY", children=cutters)


def make_continuous_carbon_shell():
    """Return the one-piece continuous loft with presentation window cuts."""
    shell = make_engineered_shell() - make_hatch_opening_cutter()
    for cutter in make_side_window_cutters().children:
        shell = shell - cutter
    shell.label = "CONTINUOUS_R1S_LIKE_CARBON_SHELL_PRESENTATION_ONLY"
    shell.color = CARBON_COLOR
    return shell


def make_curved_side_glazing() -> Compound:
    """Return panes intersected from the curved exterior skin, not flat plates."""
    glazing_skin = make_master_topper_envelope() - _make_inset_envelope(8.0)
    panes = []
    for side, sign in (("DRIVER", 1.0), ("PASSENGER", -1.0)):
        for index, (x_min, x_max) in enumerate(SIDE_WINDOW_X_RANGES, start=1):
            pane = glazing_skin & _side_window_selector(x_min, x_max, sign)
            pane.label = f"CURVED_SIDE_GLAZING_{side}_{index}_PRESENTATION_ONLY"
            pane.color = GLAZING_COLOR
            panes.append(pane)
    return Compound(label="CURVED_SIDE_GLAZING_PRESENTATION_ONLY", children=panes)


def make_rear_hatch_glazing() -> Compound:
    """Return one wide centered pane for the single rear hatch leaf."""
    x = value(topper_overall_length) + value(wall_nominal_thickness) - 6.0
    pane = Box(
        6.0,
        REAR_WINDOW_Y_RANGE[1] - REAR_WINDOW_Y_RANGE[0],
        REAR_WINDOW_Z_RANGE[1] - REAR_WINDOW_Z_RANGE[0],
        align=(Align.MIN, Align.MIN, Align.MIN),
    ).moved(Location((x, REAR_WINDOW_Y_RANGE[0], REAR_WINDOW_Z_RANGE[0])))
    pane.label = "SINGLE_REAR_HATCH_GLAZING_PRESENTATION_ONLY"
    pane.color = GLAZING_COLOR
    return Compound(label="SINGLE_REAR_HATCH_GLAZING_PRESENTATION_ONLY", children=[pane])


def make_visual_review_hatch_leaf():
    """Return one carbon leaf with one opening and one centered pane."""
    leaf = make_closed_hatch_leaf()
    cutter = Box(
        2.0 * value(wall_nominal_thickness),
        REAR_WINDOW_Y_RANGE[1] - REAR_WINDOW_Y_RANGE[0],
        REAR_WINDOW_Z_RANGE[1] - REAR_WINDOW_Z_RANGE[0],
        align=(Align.MIN, Align.MIN, Align.MIN),
    ).moved(
        Location(
            (
                value(topper_overall_length) - value(wall_nominal_thickness) / 2.0,
                REAR_WINDOW_Y_RANGE[0],
                REAR_WINDOW_Z_RANGE[0],
            )
        )
    )
    leaf = leaf - cutter
    leaf.label = "SINGLE_REAR_HATCH_LEAF_WITH_ONE_OPENING_PRESENTATION_ONLY"
    leaf.color = HATCH_CARBON_COLOR
    return leaf


def make_hatch_frame_presentation() -> Compound:
    frame = make_rear_hatch_frame()
    for bar in frame.children:
        bar.color = CARBON_EDGE_COLOR
        bar.label = bar.label.replace("PROVISIONAL", "PRESENTATION_ONLY")
    frame.label = "SINGLE_REAR_HATCH_FRAME_PRESENTATION_ONLY"
    return frame


def gen_step():
    assembly = AssemblyHelper("R1T_TOPPER_STEP15_OPERATOR_VISUAL")
    assembly.add(make_continuous_carbon_shell(), "CONTINUOUS_CARBON_SHELL")
    assembly.add(make_curved_side_glazing(), "CURVED_SIDE_GLAZING")
    assembly.add(make_hatch_frame_presentation(), "SINGLE_REAR_HATCH_FRAME")
    assembly.add(make_visual_review_hatch_leaf(), "SINGLE_REAR_HATCH_LEAF")
    assembly.add(make_rear_hatch_glazing(), "SINGLE_REAR_HATCH_GLAZING")
    return assembly.build()
