"""Deterministic checks for the Step 15 operator_visual presentation package."""

import hashlib
import json
from pathlib import Path

from exports_step15 import VERIFIED_STEP11_COMMIT, VERIFIED_STEP11_STEP_OID
from rear_hatch import make_closed_hatch_leaf
from visual_review_step15 import (
    REAR_WINDOW_Y_RANGE,
    REAR_WINDOW_Z_RANGE,
    SIDE_WINDOW_X_RANGES,
    SIDE_WINDOW_Z_RANGE,
    STRUCTURAL_MULLION_WIDTH,
    gen_step,
    make_continuous_carbon_shell,
    make_curved_side_glazing,
    make_rear_hatch_glazing,
    make_visual_review_hatch_leaf,
)


def run() -> None:
    labels = {child.label for child in gen_step().children}
    assert labels == {
        "CONTINUOUS_CARBON_SHELL",
        "CURVED_SIDE_GLAZING",
        "SINGLE_REAR_HATCH_FRAME",
        "SINGLE_REAR_HATCH_LEAF",
        "SINGLE_REAR_HATCH_GLAZING",
    }
    assert "00_REFERENCE" not in labels
    assert all(
        not any(token in label for token in ("TOOL", "KEEP_OUT", "DATUM", "LOAD_PATH", "MOTION"))
        for label in labels
    )

    shell = make_continuous_carbon_shell()
    assert shell.volume > 0.0
    assert shell.bounding_box().size.X > 1400.0

    panes = make_curved_side_glazing().children
    assert len(panes) == 6
    assert all(pane.volume > 0.0 for pane in panes)
    assert all(pane.bounding_box().size.Y > 20.0 for pane in panes)
    assert all(pane.bounding_box().max.Z >= SIDE_WINDOW_Z_RANGE[1] - 15.0 for pane in panes)
    assert all(
        right[0] - left[1] >= STRUCTURAL_MULLION_WIDTH
        for left, right in zip(SIDE_WINDOW_X_RANGES, SIDE_WINDOW_X_RANGES[1:])
    )
    assert SIDE_WINDOW_Z_RANGE[1] - SIDE_WINDOW_Z_RANGE[0] >= 450.0

    rear_panes = make_rear_hatch_glazing().children
    assert len(rear_panes) == 1
    assert rear_panes[0].volume > 0.0
    assert rear_panes[0].bounding_box().size.Y == REAR_WINDOW_Y_RANGE[1] - REAR_WINDOW_Y_RANGE[0]
    assert rear_panes[0].bounding_box().size.Z == REAR_WINDOW_Z_RANGE[1] - REAR_WINDOW_Z_RANGE[0]
    assert make_visual_review_hatch_leaf().volume < make_closed_hatch_leaf().volume

    review_dir = Path(__file__).resolve().parents[1] / "outputs/review/step15"
    manifest = json.loads((review_dir / "manifest.json").read_text())
    assert manifest["source_geometry_commit"] == VERIFIED_STEP11_COMMIT
    assert manifest["source_step_lfs_oid_sha256"] == VERIFIED_STEP11_STEP_OID
    assert manifest["authority"] == "PRESENTATION_ONLY_NOT_FITMENT_OR_FABRICATION_RELEASE"
    assert set(manifest["views"]) == {
        "front.png", "rear.png", "driver_side.png", "passenger_side.png", "top.png", "three_quarter_rear.png"
    }
    assert all(
        hashlib.sha256((review_dir / name).read_bytes()).hexdigest() == expected
        for name, expected in manifest["views"].items()
    )
    assert (review_dir / "R1T_TOPPER_STEP15_OPERATOR_VISUAL.glb").stat().st_size > 0
    assert (review_dir / "R1T_TOPPER_STEP15_OPERATOR_VISUAL.step").stat().st_size > 0


if __name__ == "__main__":
    run()
    print("STEP_15_OPERATOR_VISUAL_CHECKS_PASS")
