"""R1T topper integrated Step 11 production-intent review assembly."""

from cadpy.assembly import AssemblyHelper

from production_intent import build_production_intent_subassembly
from vehicle_reference import build_reference_subassembly, make_coordinate_reference


def gen_step():
    assembly = AssemblyHelper("R1T_TOPPER_ASSEMBLY")
    assembly.add(build_reference_subassembly(), "00_REFERENCE")
    assembly.add(build_production_intent_subassembly(), "10_TOPPER_STEP11_PRODUCTION_INTENT")
    assembly.add(make_coordinate_reference(), "90_REVIEW_COORDINATE_REFERENCE")
    return assembly.build()
