"""R1T topper Step 8 review assembly with the provisional rear hatch system."""

from cadpy.assembly import AssemblyHelper

from rear_hatch import build_rear_hatch_subassembly
from vehicle_reference import build_reference_subassembly, make_coordinate_reference


def gen_step():
    assembly = AssemblyHelper("R1T_TOPPER_ASSEMBLY")
    assembly.add(build_reference_subassembly(), "00_REFERENCE")
    assembly.add(build_rear_hatch_subassembly(), "10_TOPPER_REAR_HATCH_SYSTEM")
    assembly.add(make_coordinate_reference(), "90_REVIEW_COORDINATE_REFERENCE")
    return assembly.build()
