"""Deterministic contract checks for the re-embodied Step 15 review package."""

import hashlib
import json
from pathlib import Path

from build123d import Align, Box, Location

from exports_step15 import VERIFIED_STEP11_COMMIT, VERIFIED_STEP11_STEP_OID
from mount_interfaces import make_topper_crossbar_ports
from parameters import rear_hatch_opening_width, topper_overall_length, value, wall_nominal_thickness
import visual_review_step15 as visual
from visual_review_step15 import (
    gen_step,
    make_continuous_carbon_shell,
    make_flat_window_inserts,
    make_hatch_b_side_engineering,
    make_integrated_crossbar_ports_presentation,
    make_rear_hatch_glazing,
    make_side_aperture_interfaces,
    make_side_insert_interchangeability_proof,
    make_visual_review_hatch_leaf,
)


def _expected_side_labels(side: str) -> set[str]:
    return {
        f"WINDOW_INSERT_{side}_{index}_SEPARATE_PART"
        for index in range(1, len(visual.SIDE_WINDOW_X_RANGES) + 1)
    }


def _expected_rear_labels() -> set[str]:
    return {
        f"REAR_HATCH_GLAZING_{index}_PRESENTATION_ONLY"
        for index in range(1, len(visual.REAR_WINDOW_Y_RANGES) + 1)
    }


def _presented_port_label(label: str) -> str:
    label = label.replace("_PROVISIONAL", "_INTEGRATED_PRESENTATION_ONLY")
    return label if "INTEGRATED_PRESENTATION_ONLY" in label else label.replace(
        "OEM_ACCESSORY_PORT_PROFILE_", "INTEGRATED_SHELL_PORT_"
    ) + "_INTEGRATED_PRESENTATION_ONLY"


def _rear_corner_selector(side: float):
    return Box(70.0, 110.0, 660.0, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(
        Location(
            (
                value(topper_overall_length),
                side * (value(rear_hatch_opening_width) / 2.0 + value(wall_nominal_thickness) - 55.0),
                20.0,
            )
        )
    )


def _enforce(checks: dict[str, bool]) -> None:
    failed = sorted(name for name, passed in checks.items() if not passed)
    assert not failed, f"STEP15_CONTRACT_FAILED: {', '.join(failed)}"


def _mutation_test() -> None:
    """Prove source dimensions and rounded profiles, not cached check booleans."""
    mutations = {
        "side_mullion_120_mm": ("SIDE_WINDOW_X_RANGES", ((145.0, 690.0), (810.0, 1345.0))),
        "rear_mullion_120_mm": ("REAR_WINDOW_Y_RANGES", ((-605.0, -60.0), (60.0, 605.0))),
        "square_side_profiles": ("SIDE_APERTURE_CORNER_RADIUS", 0.0),
        "square_rear_profiles": ("REAR_WINDOW_CORNER_RADIUS", 0.0),
    }
    survivors = []
    for name, (attribute, replacement) in mutations.items():
        original = getattr(visual, attribute)
        setattr(visual, attribute, replacement)
        try:
            checks = _contract_checks()
        except Exception as error:
            raise AssertionError(f"STEP15_MUTATION_CONSTRUCTION_ERROR: {name}: {error}") from error
        finally:
            setattr(visual, attribute, original)
        try:
            _enforce(checks)
        except AssertionError:
            continue
        survivors.append(name)
    assert not survivors, f"STEP15_MUTATION_SURVIVORS: {', '.join(survivors)}"
    print(f"STEP_15_MUTATION_TEST_PASS mutations={len(mutations)} all_rejected=true")


def _contract_checks() -> dict[str, bool]:
    root_labels = {child.label for child in gen_step().children}
    required_roots = {
        "R1T_VEHICLE_PRESENTATION_CONTEXT",
        "CONTINUOUS_ROUNDED_CARBON_SHELL",
        "SHARED_SIDE_APERTURE_INTERFACES",
        "FLAT_WINDOW_INSERTS_SEPARATE_PARTS",
        "SIDE_INSERT_INTERCHANGEABILITY_PROOF",
        "SINGLE_REAR_HATCH_LEAF",
        "REAR_HATCH_TWO_PANE_GLAZING",
        "INTEGRATED_TOPPER_CROSSBAR_PORTS",
    }
    shell = make_continuous_carbon_shell()
    side_inserts = make_flat_window_inserts().children
    side_panes = [insert.children[0] for insert in side_inserts]
    side_interfaces = make_side_aperture_interfaces().children
    interchangeability = make_side_insert_interchangeability_proof()
    rear_panes = make_rear_hatch_glazing().children
    hatch_leaf = make_visual_review_hatch_leaf()
    b_side = make_hatch_b_side_engineering()
    integrated_ports = make_integrated_crossbar_ports_presentation().children
    source_ports = make_topper_crossbar_ports().children

    checks: dict[str, bool] = {
        "root_set_equality": root_labels == required_roots,
        "no_reference_or_engineering_visibility": all(
            not any(token in label for token in ("00_REFERENCE", "TOOL", "KEEP_OUT", "DATUM", "LOAD_PATH", "MOTION"))
            for label in root_labels
        ),
        "no_top_center_protrusion": all("TOP_CENTER_PROTRUSION" not in label for label in root_labels),
        "no_freestanding_crossbar_reference": all("CROSSBAR_REFERENCE" not in label for label in root_labels),
        "one_positive_volume_shell": shell.volume > 0.0 and len(shell.solids()) == 1,
        "rounded_shell_spans_product_length": shell.bounding_box().size.X > 1400.0,
        "two_side_ranges": len(visual.SIDE_WINDOW_X_RANGES) == 2,
        "driver_insert_set_equality": {insert.label for insert in side_inserts if "_DRIVER_" in insert.label} == _expected_side_labels("DRIVER"),
        "passenger_insert_set_equality": {insert.label for insert in side_inserts if "_PASSENGER_" in insert.label} == _expected_side_labels("PASSENGER"),
        "all_side_panes_positive_and_planar": all(
            pane.volume > 0.0 and abs(pane.bounding_box().size.Y - visual.SIDE_INSERT_PANE_THICKNESS) < 1e-6
            for pane in side_panes
        ),
        "wide_side_lights": all((right - left) >= 500.0 for left, right in visual.SIDE_WINDOW_X_RANGES),
        "side_light_height": visual.SIDE_WINDOW_Z_RANGE[1] - visual.SIDE_WINDOW_Z_RANGE[0] >= 500.0,
        "rounded_side_aperture_profiles": visual.SIDE_APERTURE_CORNER_RADIUS >= 60.0
        and any(edge.geom_type.name != "LINE" for edge in visual._side_window_selector(*visual.SIDE_WINDOW_X_RANGES[0], 1.0).edges()),
        "shared_interface_count": len(side_interfaces) == 4,
        "shared_interface_contract": all(
            len(interface.children) == 3
            and all(child.volume > 0.0 for child in interface.children)
            for interface in side_interfaces
        ),
        "shared_interface_load_path_intersects_shell": all(
            (interface.children[2] & shell).volume > 0.0 for interface in side_interfaces
        ),
        "shared_interface_retention_pattern": all(
            len(interface.children[1].children) == 4 for interface in side_interfaces
        ),
        "interchangeability_root_present": interchangeability.label == "SIDE_INSERT_INTERCHANGEABILITY_PROOF",
        "interchangeability_variant_set": {
            child.label for child in interchangeability.children
        } == {
            "SIDE_INSERT_INTERCHANGEABILITY_COMMON_APERTURE_DATUM_FLANGE_SEAL_RETENTION",
            "SIDE_INSERT_INTERCHANGEABILITY_WINDOW_INSERT_SAME_INTERFACE",
            "SIDE_INSERT_INTERCHANGEABILITY_CAGE_INSERT_SAME_INTERFACE",
            "SIDE_INSERT_INTERCHANGEABILITY_TOOLBOX_INSERT_SAME_INTERFACE",
        },
        "interchangeability_variants_positive": all(
            child.volume > 0.0 for child in interchangeability.children
        ),
        "interchangeability_same_profile": all(
            child.bounding_box().size.X == interchangeability.children[1].bounding_box().size.X
            for child in interchangeability.children[1:]
        ),
        "two_rear_pane_set_equality": {pane.label for pane in rear_panes} == _expected_rear_labels(),
        "all_rear_panes_positive": all(pane.volume > 0.0 for pane in rear_panes),
        "wide_rear_lights": all((right - left) >= 500.0 for left, right in visual.REAR_WINDOW_Y_RANGES),
        "rounded_rear_window_profiles": visual.REAR_WINDOW_CORNER_RADIUS >= 50.0
        and any(edge.geom_type.name != "LINE" for edge in visual._rear_window_selector(*visual.REAR_WINDOW_Y_RANGES[0]).edges()),
        "single_closed_two_pane_hatch": hatch_leaf.label == "SINGLE_REAR_HATCH_LEAF_TWO_PANE_CONTINUOUS_CORNERS_PRESENTATION_ONLY" and len(hatch_leaf.solids()) == 1 and hatch_leaf.volume > 0.0,
        "rear_apertures_cut_through_leaf": all(
            (hatch_leaf & visual._rear_window_selector(y_min, y_max)).volume < 1e-6
            for y_min, y_max in visual.REAR_WINDOW_Y_RANGES
        ),
        "rear_panes_seated_within_leaf_plane": all(
            hatch_leaf.bounding_box().min.X <= pane.bounding_box().min.X
            and pane.bounding_box().max.X <= hatch_leaf.bounding_box().max.X
            for pane in rear_panes
        ),
        "rear_hatch_corners_continuous": all((hatch_leaf & _rear_corner_selector(side)).volume > 0.0 for side in (-1.0, 1.0)),
        "b_side_hatch_system_complete": {child.label for child in b_side.children} == {
            "SINGLE_REAR_HATCH_FRAME_CONTINUOUS_PRESENTATION_ONLY",
            "REAR_HATCH_PANEL_CLOSED_B_SIDE_PRESENTATION_ONLY",
            "REAR_HATCH_PANEL_OPEN_B_SIDE_PRESENTATION_ONLY",
            "REAR_HATCH_HINGE_LATCH_B_SIDE_PRESENTATION_ONLY",
            "REAR_HATCH_CONTINUOUS_SEAL_B_SIDE_PRESENTATION_ONLY",
            "REAR_HATCH_GUTTER_DRAINAGE_B_SIDE_PRESENTATION_ONLY",
        },
        "eight_shell_integrated_ports_set_equality": {
            item.label for item in integrated_ports
        } == {_presented_port_label(item.label) for item in source_ports} and len(integrated_ports) == 8,
        "ports_are_shell_integrated": all((item & shell).volume > 0.0 for item in integrated_ports),
    }

    for side, sign in (("DRIVER", 1.0), ("PASSENGER", -1.0)):
        for left, right in zip(visual.SIDE_WINDOW_X_RANGES, visual.SIDE_WINDOW_X_RANGES[1:]):
            gap = (left[1], right[0])
            checks[f"{side.lower()}_carbon_between_side_lights"] = (
                gap[1] - gap[0] == visual.STRUCTURAL_MULLION_WIDTH
                and gap[1] - gap[0] >= visual.STRUCTURAL_CARBON_MINIMUM
                and (shell & visual._side_window_selector(*gap, sign)).volume > 0.0
            )
    for left, right in zip(visual.REAR_WINDOW_Y_RANGES, visual.REAR_WINDOW_Y_RANGES[1:]):
        gap = (left[1], right[0])
        checks["carbon_between_rear_hatch_lights"] = (
            gap[1] - gap[0] == visual.REAR_MULLION_WIDTH
            and (hatch_leaf & visual._rear_window_selector(*gap, depth=80.0)).volume > 0.0
        )

    review_dir = Path(__file__).resolve().parents[1] / "outputs/review/step15"
    manifest = json.loads((review_dir / "manifest.json").read_text())
    expected_views = {"front.png", "rear.png", "driver_side.png", "passenger_side.png", "top.png", "three_quarter_rear.png", "interchangeability.png"}
    checks.update(
        {
            "manifest_source_commit": manifest["source_geometry_commit"] == VERIFIED_STEP11_COMMIT,
            "manifest_source_lfs_oid": manifest["source_step_lfs_oid_sha256"] == VERIFIED_STEP11_STEP_OID,
            "manifest_presentation_authority": manifest["authority"] == "PRESENTATION_ONLY_NOT_FITMENT_OR_FABRICATION_RELEASE",
            "manifest_view_set_equality": set(manifest["views"]) == expected_views,
            "manifest_view_hashes": all(hashlib.sha256((review_dir / name).read_bytes()).hexdigest() == expected for name, expected in manifest["views"].items()),
            "manifest_interchangeability_asset": (
                manifest["interchangeability"]["view"] == "interchangeability.png"
                and manifest["interchangeability"]["step_path"] == "R1T_TOPPER_STEP15_INSERT_INTERCHANGEABILITY.step"
                and manifest["interchangeability"]["glb_path"] == "R1T_TOPPER_STEP15_INSERT_INTERCHANGEABILITY.glb"
                and hashlib.sha256((review_dir / "interchangeability.png").read_bytes()).hexdigest() == manifest["interchangeability"]["view_sha256"]
            ),
            "manifest_delivery_dimensions": manifest["delivery"] == {"width": 2400, "height": 1600, "aspect": "3:2"},
            "manifest_flat_window_contract": manifest["design_contract"]["window"] == "separate planar insert",
            "manifest_interchangeability_contract": manifest["design_contract"]["interchangeability"] == "same side aperture carries WINDOW/CAGE/TOOLBOX insert variants",
            "step_and_glb_present": (review_dir / "R1T_TOPPER_STEP15_OPERATOR_VISUAL.glb").stat().st_size > 0 and (review_dir / "R1T_TOPPER_STEP15_OPERATOR_VISUAL.step").stat().st_size > 0,
        }
    )
    return checks


def run() -> None:
    checks = _contract_checks()
    _enforce(checks)
    _mutation_test()


if __name__ == "__main__":
    run()
    print("STEP_15_OPERATOR_VISUAL_CHECKS_PASS")
