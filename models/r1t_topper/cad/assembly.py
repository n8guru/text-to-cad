"""R1T topper Step 9 review assembly with provisional vehicle interfaces."""

from cadpy.assembly import AssemblyHelper

from mount_interfaces import build_mount_interface_subassembly
from vehicle_reference import build_reference_subassembly, make_coordinate_reference


def gen_step():
    assembly = AssemblyHelper("R1T_TOPPER_ASSEMBLY")
    assembly.add(build_reference_subassembly(), "00_REFERENCE")
    assembly.add(
        build_mount_interface_subassembly(),
        "10_TOPPER_MOUNT_AND_INTERFACE_SYSTEM",
    )
    assembly.add(make_coordinate_reference(), "90_REVIEW_COORDINATE_REFERENCE")
    return assembly.build()
