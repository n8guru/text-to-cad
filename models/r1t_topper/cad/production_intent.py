"""Step 11 integrated production-intent structure and tooling package.

All loads, allowables, interfaces, and tool envelopes remain provisional until
coupon testing and the Step 13 physical calibration pass.
"""

from build123d import Align, Box, Color, Compound, Location
from cadpy.assembly import AssemblyHelper

from electrical_integration import (
    make_brake_light_provision,
    make_interior_lighting_provision,
    make_low_voltage_harness_packaging,
    make_rear_camera_provision,
    make_vehicle_electrical_ingress_reservation,
)
from mount_interfaces import (
    _roof_edge_z,
    make_quick_release_mount_adapters,
    make_relocated_control_system,
    make_topper_crossbar_ports,
    make_vehicle_and_service_keepouts,
)
from parameters import (
    DESIGN_DECISION,
    ESTIMATED,
    assumed_dynamic_load_factor,
    assumed_vertical_design_load,
    bed_anchor_locations,
    brake_light_center,
    brake_light_recess_dimensions,
    camera_housing_dimensions,
    crossbar_mount_span,
    hatch_hardpoint_plate_size,
    mount_hardpoint_plate_size,
    rear_camera_center,
    screening_bondline_shear_allowable,
    screening_core_shear_allowable,
    screening_skin_allowable,
    screening_skin_modulus,
    section_joint_gap,
    structural_frame_depth,
    structural_frame_skin_thickness,
    structural_frame_width,
    tooling_flange_width,
    tooling_trim_allowance,
    topper_crossbar_station_1,
    topper_crossbar_station_2,
    topper_overall_length,
    value,
)
from rear_hatch import (
    make_closed_hatch_leaf,
    make_drainage_management,
    make_hatch_mechanism_envelopes,
    make_hatch_opening_cutter,
    make_latch_service_access,
    make_open_hatch_motion_envelope,
    make_rear_hatch_frame,
    make_weather_seal,
)
from topper_envelope import (
    _section_joint_stations,
    make_base_flange_references,
    make_load_path_references,
    make_module_cartridges,
    make_module_frames,
    make_section_joint_interfaces,
    make_sectioned_modular_shell,
    make_shell_datums,
    make_shell_keepouts,
)


STRUCTURE_COLOR = Color(0.92, 0.72, 0.08, 0.92)
HARDPOINT_COLOR = Color(0.64, 0.66, 0.70, 0.95)
TOOL_COLOR = Color(0.28, 0.62, 0.92, 0.22)

LAYUP_SCHEDULE = (
    ("GENERAL_SHELL", "1.0 mm quasi-isotropic carbon / 20 mm foam / 1.0 mm carbon"),
    ("TRANSVERSE_FRAMES", "2.0 mm carbon faces / 76 mm core at two load stations"),
    ("SECTION_JOINTS", "4.0 mm internal doubler plus bonded keyed splice"),
    ("MOUNT_HARDPOINTS", "4.0 mm aluminum insert in locally reinforced laminate"),
    ("HATCH_HARDPOINTS", "4.0 mm aluminum insert in locally reinforced laminate"),
)

ASSEMBLY_SEQUENCE = (
    "CNC machine three female tool sections and trim/drill templates",
    "Lay outer skin, core, local frame plies, and hardpoint inserts",
    "Vacuum cure each section; trim and drill from common datums",
    "Bond/index the two section joints and install module frames",
    "Install hatch, seals, drains, mounts, controls, lighting, and harness",
    "Perform dimensional, coupon, leak, electrical, and proof-load acceptance",
)


def make_integrated_sectioned_shell() -> Compound:
    """Apply the verified hatch/camera/brake cuts to the verified Step 7 shell."""
    camera = Box(
        *value(camera_housing_dimensions),
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    ).moved(Location(value(rear_camera_center)))
    brake = Box(
        *value(brake_light_recess_dimensions),
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    ).moved(Location(value(brake_light_center)))
    hatch = make_hatch_opening_cutter()
    segments = []
    for source in make_sectioned_modular_shell().children:
        segment = source - hatch - camera - brake
        segment.label = source.label.replace("PROVISIONAL", "STEP11_PROVISIONAL")
        segments.append(segment)
    return Compound(label="INTEGRATED_SECTIONED_SHELL_STEP11_PROVISIONAL", children=segments)


def make_transverse_structural_frames() -> Compound:
    """Return two local sandwich-frame envelopes tied to the roof hardpoints."""
    frame_width = value(structural_frame_width)
    frame_depth = value(structural_frame_depth)
    span = value(crossbar_mount_span)
    frames = []
    for index, x in enumerate(
        (value(topper_crossbar_station_1), value(topper_crossbar_station_2)),
        start=1,
    ):
        frame = Box(
            frame_width,
            span,
            frame_depth,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
        ).moved(Location((x, 0.0, _roof_edge_z(x) - frame_depth / 2.0)))
        frame.label = f"TRANSVERSE_SANDWICH_FRAME_{index}_PROVISIONAL"
        frame.color = STRUCTURE_COLOR
        frames.append(frame)
    return Compound(label="TRANSVERSE_STRUCTURAL_FRAMES", children=frames)


def make_hardpoint_inserts() -> Compound:
    """Return mount, crossbar, hinge, and strut insert-plate envelopes."""
    children = []
    mount_size = value(mount_hardpoint_plate_size)
    for index, (x, y, _z) in enumerate(value(bed_anchor_locations), start=1):
        plate = Box(*mount_size, align=(Align.CENTER,) * 3).moved(
            Location((x, y, mount_size[2] / 2.0))
        )
        plate.label = f"MOUNT_HARDPOINT_INSERT_{index}_PROVISIONAL"
        plate.color = HARDPOINT_COLOR
        children.append(plate)

    crossbar_size = value(mount_hardpoint_plate_size)
    half_span = value(crossbar_mount_span) / 2.0
    for station, x in enumerate(
        (value(topper_crossbar_station_1), value(topper_crossbar_station_2)),
        start=1,
    ):
        for side, sign in (("DRIVER", 1.0), ("PASSENGER", -1.0)):
            plate = Box(*crossbar_size, align=(Align.CENTER,) * 3).moved(
                Location((x, sign * half_span, _roof_edge_z(x)))
            )
            plate.label = (
                f"CROSSBAR_HARDPOINT_INSERT_{station}_{side}_PROVISIONAL"
            )
            plate.color = HARDPOINT_COLOR
            children.append(plate)

    hatch_size = value(hatch_hardpoint_plate_size)
    for index, service in enumerate(make_hatch_mechanism_envelopes().children, start=1):
        plate = Box(*hatch_size, align=(Align.CENTER,) * 3).moved(
            Location(service.center())
        )
        plate.label = f"HATCH_HARDPOINT_INSERT_{index}_PROVISIONAL"
        plate.color = HARDPOINT_COLOR
        children.append(plate)
    return Compound(label="LOCAL_HARDPOINT_INSERTS", children=children)


def make_tooling_definition() -> Compound:
    """Return three CNC master/fixture envelopes aligned to the section joints."""
    trim = value(tooling_trim_allowance)
    flange = value(tooling_flange_width)
    gap = value(section_joint_gap)
    stations = (0.0, *_section_joint_stations(), value(topper_overall_length))
    tools = []
    for index, (start, end) in enumerate(zip(stations, stations[1:]), start=1):
        adjusted_start = start + (gap / 2.0 if index > 1 else 0.0)
        adjusted_end = end - (gap / 2.0 if index < 3 else 0.0)
        length = adjusted_end - adjusted_start
        tool = Box(
            length + 2.0 * trim,
            value(crossbar_mount_span) + 2.0 * flange,
            20.0,
            align=(Align.CENTER, Align.CENTER, Align.MAX),
        ).moved(Location(((adjusted_start + adjusted_end) / 2.0, 0.0, -70.0)))
        tool.label = f"TOOL_SECTION_{index}_CNC_MASTER_AND_FIXTURE_ENVELOPE"
        tool.color = TOOL_COLOR
        tools.append(tool)
    return Compound(label="SECTIONAL_CNC_TOOLING_DEFINITION", children=tools)


def structural_screening() -> dict[str, float | str]:
    """Return transparent first-order checks; results are not product ratings."""
    load = value(assumed_vertical_design_load) * value(assumed_dynamic_load_factor)
    path_load = load / 4.0
    span = value(crossbar_mount_span) / 1000.0
    width = value(structural_frame_width) / 1000.0
    depth = value(structural_frame_depth) / 1000.0
    skin = value(structural_frame_skin_thickness) / 1000.0
    inertia = width * (depth**3 - (depth - 2.0 * skin) ** 3) / 12.0
    modulus = value(screening_skin_modulus) * 1_000_000.0
    stress_mpa = path_load * span * depth / (8.0 * inertia) / 1_000_000.0
    deflection_mm = path_load * span**3 / (48.0 * modulus * inertia) * 1000.0
    core_shear_mpa = path_load / (width * (depth - 2.0 * skin)) / 1_000_000.0
    plate_x, plate_y, _plate_z = value(mount_hardpoint_plate_size)
    bondline_shear_mpa = path_load / (plate_x * plate_y)
    return {
        "basis": "SCREENING_ONLY_NOT_A_RATING",
        "factored_total_load_n": load,
        "load_per_path_n": path_load,
        "frame_skin_stress_mpa": stress_mpa,
        "frame_deflection_mm": deflection_mm,
        "frame_deflection_limit_mm": value(crossbar_mount_span) / 100.0,
        "core_shear_mpa": core_shear_mpa,
        "bondline_shear_mpa": bondline_shear_mpa,
        "skin_stress_margin": value(screening_skin_allowable) / stress_mpa,
        "core_shear_margin": value(screening_core_shear_allowable) / core_shear_mpa,
        "bondline_shear_margin": (
            value(screening_bondline_shear_allowable) / bondline_shear_mpa
        ),
    }


def validate_production_intent_inputs() -> None:
    assert all(
        parameter.provenance == DESIGN_DECISION
        for parameter in (
            structural_frame_width,
            structural_frame_depth,
            structural_frame_skin_thickness,
            mount_hardpoint_plate_size,
            hatch_hardpoint_plate_size,
            tooling_flange_width,
            tooling_trim_allowance,
        )
    )
    assert all(
        parameter.provenance == ESTIMATED
        for parameter in (
            screening_skin_modulus,
            screening_skin_allowable,
            screening_core_shear_allowable,
            screening_bondline_shear_allowable,
        )
    )


def build_production_intent_subassembly() -> Compound:
    """Build the integrated Step 11 review and manufacturing package."""
    validate_production_intent_inputs()
    assembly = AssemblyHelper("10_TOPPER_STEP11_PRODUCTION_INTENT")
    assembly.add(make_integrated_sectioned_shell(), "INTEGRATED_SECTIONED_SHELL")
    assembly.add(make_section_joint_interfaces(), "SECTION_JOINT_INTERFACES")
    assembly.add(make_module_frames(), "COMMON_MODULE_INTERFACE_FRAMES")
    assembly.add(make_module_cartridges(), "SWAPPABLE_MODULE_CARTRIDGES")
    assembly.add(make_rear_hatch_frame(), "REAR_HATCH_FRAME")
    assembly.add(make_closed_hatch_leaf(), "REAR_HATCH_LEAF_CLOSED")
    assembly.add(make_weather_seal(), "PRIMARY_HATCH_WEATHER_SEAL")
    assembly.add(make_drainage_management(), "REAR_HATCH_DRAINAGE")
    assembly.add(make_hatch_mechanism_envelopes(), "HINGE_AND_STRUT_ENVELOPES")
    assembly.add(make_latch_service_access(), "HATCH_SERVICE_ACCESS")
    assembly.add(make_open_hatch_motion_envelope(), "HATCH_OPEN_MOTION_ENVELOPE")
    assembly.add(make_quick_release_mount_adapters(), "QUICK_RELEASE_MOUNT_ADAPTERS")
    assembly.add(make_relocated_control_system(), "RELOCATED_MECHANICAL_CONTROLS")
    assembly.add(make_topper_crossbar_ports(), "TOPPER_CROSSBAR_PORT_SYSTEM")
    assembly.add(make_vehicle_and_service_keepouts(), "VEHICLE_AND_SERVICE_KEEP_OUTS")
    assembly.add(make_rear_camera_provision(), "REAR_CAMERA_PROVISION")
    assembly.add(make_brake_light_provision(), "HIGH_MOUNT_BRAKE_LIGHT_PROVISION")
    assembly.add(make_interior_lighting_provision(), "INTERIOR_LIGHTING_PROVISION")
    assembly.add(make_low_voltage_harness_packaging(), "LOW_VOLTAGE_HARNESS")
    assembly.add(make_vehicle_electrical_ingress_reservation(), "ELECTRICAL_INGRESS")
    assembly.add(make_transverse_structural_frames(), "TRANSVERSE_STRUCTURAL_FRAMES")
    assembly.add(make_hardpoint_inserts(), "LOCAL_HARDPOINT_INSERTS")
    assembly.add(make_tooling_definition(), "SECTIONAL_CNC_TOOLING_DEFINITION")
    assembly.add(make_base_flange_references(), "BASE_FLANGES")
    assembly.add(make_shell_datums(), "SHELL_DATUMS")
    assembly.add(make_shell_keepouts(), "SHELL_ENGINEERING_KEEP_OUTS")
    assembly.add(make_load_path_references(), "STRUCTURAL_LOAD_PATH_REFERENCES")
    return assembly.build()
