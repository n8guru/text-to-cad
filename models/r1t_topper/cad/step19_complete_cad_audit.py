"""Step 19 exact-package audit for the R1T topper complete-CAD claim.

This is a digital-CAD completeness gate.  It deliberately does not assert
vehicle fitment, sealing, ratings, fabrication authorization, or a manufacture
plan.  Use --full to re-run every predecessor contract gate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

AUDITED_PACKAGE_COMMIT = "54ca2381477d7a64a2092365898bbefda39045d1"
STEP11_SOURCE_COMMIT = "6e0229cecefee0043aed9ea607c5241c1fe7f815"
STEP11_SOURCE_STEP_OID = "c25c9df4213abdb1e87beb4aab052dc1725a4ee8433b6f242ca0dd6c5ade37ad"

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "outputs" / "review" / "step15"
MANIFEST = REVIEW / "manifest.json"

REQUIRED_CHECKS = (
    "checkpoint1_checks.py",
    "phase2_checks.py",
    "step6_checks.py",
    "step7_checks.py",
    "step8_checks.py",
    "step9_checks.py",
    "step10_checks.py",
    "step11_checks.py",
    "step15_checks.py",
)
REQUIRED_ROOTS = {
    "R1T_VEHICLE_PRESENTATION_CONTEXT",
    "CONTINUOUS_ROUNDED_CARBON_SHELL",
    "SHARED_SIDE_APERTURE_INTERFACES",
    "FLAT_WINDOW_INSERTS_SEPARATE_PARTS",
    "SIDE_INSERT_INTERCHANGEABILITY_PROOF",
    "SINGLE_REAR_HATCH_LEAF",
    "REAR_HATCH_TWO_PANE_GLAZING",
    "INTEGRATED_TOPPER_CROSSBAR_PORTS",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=ROOT.parents[1], text=True
    ).strip()


def _run_check(name: str) -> None:
    subprocess.run([sys.executable, name], cwd=Path(__file__).parent, check=True)


def _static_checks() -> dict[str, bool]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    views = manifest.get("views", {})
    expected_views = {
        "front.png",
        "rear.png",
        "driver_side.png",
        "passenger_side.png",
        "top.png",
        "three_quarter_rear.png",
        "interchangeability.png",
    }

    # Import only after file integrity is established: it proves the review
    # assembly still exposes every required final visual CAD subsystem.
    import visual_review_step15 as visual

    root_labels = {child.label for child in visual.gen_step().children}
    checks = {
        "audited_commit_is_available": bool(
            _git("rev-parse", "--verify", f"{AUDITED_PACKAGE_COMMIT}^{{commit}}")
        ),
        "audited_commit_is_ancestor_of_checkout": subprocess.run(
            ["git", "merge-base", "--is-ancestor", AUDITED_PACKAGE_COMMIT, "HEAD"],
            cwd=ROOT.parents[1],
            check=False,
        ).returncode == 0,
        "manifest_authority_boundary": (
            manifest.get("authority")
            == "PRESENTATION_ONLY_NOT_FITMENT_OR_FABRICATION_RELEASE"
        ),
        "manifest_step11_provenance": (
            manifest.get("source_geometry_commit") == STEP11_SOURCE_COMMIT
            and manifest.get("source_step_lfs_oid_sha256") == STEP11_SOURCE_STEP_OID
        ),
        "review_view_set": set(views) == expected_views,
        "review_view_hashes": all(
            (REVIEW / name).is_file() and _sha256(REVIEW / name) == digest
            for name, digest in views.items()
        ),
        "review_native_artifact_hashes": all(
            (REVIEW / entry["path"]).is_file()
            and _sha256(REVIEW / entry["path"]) == entry["sha256"]
            for entry in (manifest["step"], manifest["glb"])
        ),
        "interchangeability_artifact_hashes": all(
            (REVIEW / manifest["interchangeability"][key]).is_file()
            and _sha256(REVIEW / manifest["interchangeability"][key])
            == manifest["interchangeability"][hash_key]
            for key, hash_key in (
                ("view", "view_sha256"),
                ("step_path", "step_sha256"),
                ("glb_path", "glb_sha256"),
            )
        ),
        "final_visual_subsystems_present": root_labels == REQUIRED_ROOTS,
        "no_visible_reference_or_bar_story": all(
            "00_REFERENCE" not in label and "CROSSBAR_REFERENCE" not in label
            for label in root_labels
        ),
        "explicit_scope_boundaries_present": all(
            phrase in (ROOT / filename).read_text(encoding="utf-8").lower()
            for filename, phrase in (
                ("README.md", "not calibrated fitment, a structural"),
                ("reports/OPEN_ITEMS.md", "not production fitment"),
            )
        ),
    }
    return checks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--full",
        action="store_true",
        help="also run all predecessor CAD/visual contract checks",
    )
    args = parser.parse_args()
    checks = _static_checks()
    failed = sorted(name for name, passed in checks.items() if not passed)
    if failed:
        raise AssertionError("STEP19_COMPLETE_CAD_AUDIT_FAILED: " + ", ".join(failed))
    if args.full:
        for check in REQUIRED_CHECKS:
            _run_check(check)
    print(
        "STEP19_COMPLETE_CAD_AUDIT_PASS "
        f"audited_commit={AUDITED_PACKAGE_COMMIT} "
        f"full_checks={'true' if args.full else 'false'}"
    )


if __name__ == "__main__":
    main()
