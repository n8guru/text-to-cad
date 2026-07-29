"""R1T topper Step 10 review assembly with electrical integration packaging."""

from cadpy.assembly import AssemblyHelper

from electrical_integration import build_electrical_integration_subassembly
from vehicle_reference import build_reference_subassembly, make_coordinate_reference


def gen_step():
    assembly = AssemblyHelper("R1T_TOPPER_ASSEMBLY")
    assembly.add(build_reference_subassembly(), "00_REFERENCE")
    assembly.add(
        build_electrical_integration_subassembly(),
        "10_TOPPER_ELECTRICAL_INTEGRATION",
    )
    assembly.add(make_coordinate_reference(), "90_REVIEW_COORDINATE_REFERENCE")
    return assembly.build()
