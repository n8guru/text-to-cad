"""R1T topper review assembly with vehicle references and engineered shell."""

from cadpy.assembly import AssemblyHelper

from topper_envelope import build_topper_engineered_subassembly
from vehicle_reference import build_reference_subassembly, make_coordinate_reference


def gen_step():
    assembly = AssemblyHelper("R1T_TOPPER_ASSEMBLY")
    assembly.add(build_reference_subassembly(), "00_REFERENCE")
    assembly.add(build_topper_engineered_subassembly(), "10_TOPPER_ENGINEERED_SHELL")
    assembly.add(make_coordinate_reference(), "90_REVIEW_COORDINATE_REFERENCE")
    return assembly.build()
