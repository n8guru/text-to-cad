"""Deterministic checks for the integrated Step 11 production-intent package."""

from assembly import gen_step
from parameters import (
    assumed_dynamic_load_factor,
    assumed_vertical_design_load,
    section_segment_max_length,
    tooling_trim_allowance,
    value,
)
from production_intent import (
    ASSEMBLY_SEQUENCE,
    LAYUP_SCHEDULE,
    build_production_intent_subassembly,
    make_hardpoint_inserts,
    make_integrated_sectioned_shell,
    make_tooling_definition,
    make_transverse_structural_frames,
    structural_screening,
)
from topper_envelope import make_sectioned_modular_shell


def run() -> None:
    source_segments = make_sectioned_modular_shell().children
    integrated_segments = make_integrated_sectioned_shell().children
    assert len(source_segments) == len(integrated_segments) == 3
    assert sum(item.volume for item in integrated_segments) < sum(
        item.volume for item in source_segments
    )
    assert all(item.volume > 0.0 for item in integrated_segments)
    assert all("STEP11_PROVISIONAL" in item.label for item in integrated_segments)

    frames = make_transverse_structural_frames().children
    assert len(frames) == 2
    assert all(frame.volume > 0.0 for frame in frames)
    assert all(
        sum((frame & segment).volume for segment in integrated_segments) > 0.0
        for frame in frames
    )

    hardpoints = make_hardpoint_inserts().children
    assert len(hardpoints) == 13
    assert sum("MOUNT_HARDPOINT" in item.label for item in hardpoints) == 4
    assert sum("CROSSBAR_HARDPOINT" in item.label for item in hardpoints) == 4
    assert sum("HATCH_HARDPOINT" in item.label for item in hardpoints) == 5
    assert all(item.volume > 0.0 for item in hardpoints)

    tools = make_tooling_definition().children
    assert len(tools) == 3
    assert all(item.volume > 0.0 for item in tools)
    assert all(
        item.bounding_box().size.X
        <= value(section_segment_max_length) + 2.0 * value(tooling_trim_allowance)
        for item in tools
    )

    results = structural_screening()
    assert results["basis"] == "SCREENING_ONLY_NOT_A_RATING"
    assert results["factored_total_load_n"] == (
        value(assumed_vertical_design_load) * value(assumed_dynamic_load_factor)
    )
    assert results["frame_deflection_mm"] < results["frame_deflection_limit_mm"]
    assert results["skin_stress_margin"] > 1.0
    assert results["core_shear_margin"] > 1.0
    assert results["bondline_shear_margin"] > 1.0
    assert len(LAYUP_SCHEDULE) == 5
    assert len(ASSEMBLY_SEQUENCE) == 6

    labels = {child.label for child in build_production_intent_subassembly().children}
    assert {
        "INTEGRATED_SECTIONED_SHELL",
        "SECTION_JOINT_INTERFACES",
        "COMMON_MODULE_INTERFACE_FRAMES",
        "SWAPPABLE_MODULE_CARTRIDGES",
        "REAR_HATCH_FRAME",
        "QUICK_RELEASE_MOUNT_ADAPTERS",
        "TOPPER_CROSSBAR_PORT_SYSTEM",
        "REAR_CAMERA_PROVISION",
        "LOW_VOLTAGE_HARNESS",
        "TRANSVERSE_STRUCTURAL_FRAMES",
        "LOCAL_HARDPOINT_INSERTS",
        "SECTIONAL_CNC_TOOLING_DEFINITION",
    } <= labels
    assert {child.label for child in gen_step().children} == {
        "00_REFERENCE",
        "10_TOPPER_STEP11_PRODUCTION_INTENT",
        "90_REVIEW_COORDINATE_REFERENCE",
    }


if __name__ == "__main__":
    run()
    print("STEP_11_PRODUCTION_INTENT_CHECKS_PASS")
