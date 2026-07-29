"""Deterministic checks for the provisional Step 7 sectional module system."""

from math import isclose

from parameters import (
    DESIGN_DECISION,
    module_bay_count_per_side,
    module_frame_land_width,
    module_opening_height,
    module_opening_width,
    module_variant_types,
    section_joint_doubler_width,
    section_joint_gap,
    section_segment_max_length,
    value,
)
from topper_envelope import (
    _module_bay_centers,
    _section_joint_stations,
    build_topper_step7_subassembly,
    make_engineered_shell,
    make_module_cartridges,
    make_module_frames,
    make_module_opening_cutters,
    make_section_joint_interfaces,
    make_sectioned_modular_shell,
)


def run() -> None:
    centers = _module_bay_centers()
    stations = _section_joint_stations()
    assert len(centers) == value(module_bay_count_per_side) == 3
    assert len(stations) == 2
    assert centers[0] < stations[0] < centers[1] < stations[1] < centers[2]
    assert all(
        abs(station - center)
        > value(module_opening_width) / 2.0 + value(section_joint_gap) / 2.0
        for station in stations
        for center in centers
    )
    assert value(section_joint_gap) < value(section_joint_doubler_width)
    assert section_joint_gap.provenance == DESIGN_DECISION
    assert section_joint_doubler_width.provenance == DESIGN_DECISION

    cutters = make_module_opening_cutters().children
    assert len(cutters) == 6
    assert all(
        isclose(cutter.bounding_box().size.X, value(module_opening_width), abs_tol=1e-6)
        for cutter in cutters
    )
    assert all(
        isclose(cutter.bounding_box().size.Z, value(module_opening_height), abs_tol=1e-6)
        for cutter in cutters
    )

    source_shell = make_engineered_shell()
    segments = make_sectioned_modular_shell().children
    assert len(segments) == 3
    assert all(segment.volume > 0.0 for segment in segments)
    assert sum(segment.volume for segment in segments) < source_shell.volume
    assert all(
        segment.bounding_box().size.X <= value(section_segment_max_length)
        for segment in segments
    )
    assert [segment.label for segment in segments] == [
        "SHELL_SEGMENT_1_PROVISIONAL",
        "SHELL_SEGMENT_2_PROVISIONAL",
        "SHELL_SEGMENT_3_PROVISIONAL",
    ]

    joints = make_section_joint_interfaces().children
    assert len(joints) == 2
    assert all(len(joint.children) == 3 for joint in joints)
    assert all(joint.children[0].volume > 0.0 for joint in joints)
    assert all(
        (key & joint.children[0]).volume > 0.0
        for joint in joints
        for key in joint.children[1:]
    )
    assert all("PROVISIONAL" in joint.label for joint in joints)

    frames = make_module_frames().children
    assert len(frames) == 6
    assert all(len(frame.children) == 4 for frame in frames)
    assert all("COMMON_INTERFACE" in frame.label for frame in frames)
    assert all(
        sum((rail & source_shell).volume for rail in frame.children) > 0.0
        for frame in frames
    )
    assert module_frame_land_width.provenance == DESIGN_DECISION

    cartridges = make_module_cartridges().children
    assert len(cartridges) == 6
    labels = {cartridge.label for cartridge in cartridges}
    for variant in value(module_variant_types):
        assert any(f"_{variant}_CARTRIDGE_" in label for label in labels)
    assert all(cartridge.volume > 0.0 for cartridge in cartridges)
    assert all(
        isclose(
            cartridge.bounding_box().size.X,
            value(module_opening_width),
            abs_tol=1e-6,
        )
        for cartridge in cartridges
    )
    assert all(
        isclose(
            cartridge.bounding_box().size.Z,
            value(module_opening_height),
            abs_tol=1e-6,
        )
        for cartridge in cartridges
    )
    assert all(
        sum((segment & cutter).volume for segment in segments) < 1e-6
        for cutter in cutters
    )

    assembly_labels = {child.label for child in build_topper_step7_subassembly().children}
    assert assembly_labels == {
        "SECTIONED_MODULAR_SHELL",
        "SECTION_JOINT_INTERFACES",
        "COMMON_MODULE_INTERFACE_FRAMES",
        "SWAPPABLE_MODULE_CARTRIDGES",
        "BASE_FLANGES",
        "SHELL_DATUMS",
        "SHELL_ENGINEERING_KEEP_OUTS",
        "STRUCTURAL_LOAD_PATH_REFERENCES",
    }
    assert not any(
        forbidden in label
        for label in assembly_labels
        for forbidden in ("HATCH_MECHANISM", "VEHICLE_MOUNT", "WIRING", "LAYUP")
    )


if __name__ == "__main__":
    run()
    print("STEP_7_SECTIONAL_MODULE_CHECKS_PASS")
