"""Dedicated CAD evidence assembly for the Step 15 insert interchange contract.

The explanatory evidence uses three identical datum stations side-by-side so
the operator can see each insert choice installed against the same contract;
the product STEP also contains the normal-direction exploded proof.
"""

from build123d import Color, Location
from cadpy.assembly import AssemblyHelper

from visual_review_step15 import (
    SIDE_WINDOW_X_RANGES,
    make_cage_insert,
    make_flat_window_insert,
    make_side_aperture_interface,
    make_toolbox_insert,
)


def gen_step():
    assembly = AssemblyHelper("R1T_TOPPER_STEP15_INSERT_INTERCHANGEABILITY")
    x_min, x_max = SIDE_WINDOW_X_RANGES[0]
    station_center = (x_min + x_max) / 2.0
    stations = (
        ("WINDOW", -700.0, make_flat_window_insert("DRIVER", 1, x_min, x_max, 1.0)),
        ("CAGE", 0.0, make_cage_insert("DRIVER", 1, x_min, x_max, 1.0)),
        ("TOOLBOX", 700.0, make_toolbox_insert("DRIVER", 1, x_min, x_max, 1.0)),
    )
    for name, offset, variant in stations:
        interface = make_side_aperture_interface("DRIVER", 1, x_min, x_max, 1.0)
        interface.label = f"COMMON_APERTURE_INTERFACE_{name}_STATION"
        interface = interface.moved(Location((offset, 0.0, 0.0)))
        variant.label = f"{name}_INSERT_INSTALLED_ON_SAME_INTERFACE"
        variant = variant.moved(Location((offset, 0.0, 0.0)))
        if name == "WINDOW":
            variant.children[0].color = Color(0.05, 0.20, 0.70, 0.95)
        elif name == "CAGE":
            for bar in variant.children:
                bar.color = Color(0.85, 0.55, 0.08, 1.0)
        else:
            variant.children[0].color = Color(0.12, 0.15, 0.18, 1.0)
        assembly.add(interface, f"{name}_COMMON_APERTURE_INTERFACE")
        assembly.add(variant, f"{name}_INSERT_INSTALLED")
    return assembly.build()
