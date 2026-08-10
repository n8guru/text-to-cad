"""Generate the Step 15 operator_visual STEP, native GLB, and review packet."""

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parents[1]
REVIEW_DIR = PROJECT_ROOT / "outputs/review/step15"
STEP_PATH = REVIEW_DIR / "R1T_TOPPER_STEP15_OPERATOR_VISUAL.step"
GLB_PATH = REVIEW_DIR / "R1T_TOPPER_STEP15_OPERATOR_VISUAL.glb"
VERIFIED_STEP11_COMMIT = "6e0229cecefee0043aed9ea607c5241c1fe7f815"
VERIFIED_STEP11_STEP_OID = (
    "c25c9df4213abdb1e87beb4aab052dc1725a4ee8433b6f242ca0dd6c5ade37ad"
)

VIEWS = {
    "front": "left",
    "rear": "right",
    "driver_side": "front",
    "passenger_side": "back",
    "top": "top",
    "three_quarter_rear": "iso",
}


def _copy_snapshot(temp_dir: Path, prefix: str, name: str) -> None:
    generated = sorted(temp_dir.glob(f"{prefix}{name}_*.png"))
    if not generated:
        raise RuntimeError(f"snapshot missing for {name}")
    shutil.copy2(generated[-1], REVIEW_DIR / f"{name}.png")


def run() -> None:
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "skills/cad/scripts/step"),
            f"cad/visual_review_step15.py={STEP_PATH.relative_to(PROJECT_ROOT)}",
            "--glb",
            GLB_PATH.name,
            "--force",
        ],
        cwd=PROJECT_ROOT,
        check=True,
    )
    if not GLB_PATH.exists():
        raise RuntimeError(f"native GLB missing: {GLB_PATH}")

    with tempfile.TemporaryDirectory(prefix="r1t-topper-step15-") as temp:
        temp_dir = Path(temp)
        job = {
            "input": str(STEP_PATH),
            "mode": "view",
            "outputs": [
                {"path": str(temp_dir / f"{name}.png"), "camera": camera}
                for name, camera in VIEWS.items()
            ],
            "display": {"mode": "rendered", "projection": "orthographic"},
            "render": {
                "viewLabels": False,
                "padding": 0.08,
                "sizeProfile": "presentation",
            },
        }
        subprocess.run(
            [sys.executable, str(REPO_ROOT / "skills/cad/scripts/snapshot"), "--job", "-"],
            cwd=PROJECT_ROOT,
            input=json.dumps(job),
            text=True,
            check=True,
        )
        for name in VIEWS:
            _copy_snapshot(temp_dir, "", name)

    manifest = {
        "authority": "PRESENTATION_ONLY_NOT_FITMENT_OR_FABRICATION_RELEASE",
        "source_geometry_commit": VERIFIED_STEP11_COMMIT,
        "source_step_lfs_oid_sha256": VERIFIED_STEP11_STEP_OID,
        "step": {
            "path": STEP_PATH.name,
            "sha256": hashlib.sha256(STEP_PATH.read_bytes()).hexdigest(),
        },
        "glb": {
            "path": GLB_PATH.name,
            "sha256": hashlib.sha256(GLB_PATH.read_bytes()).hexdigest(),
        },
        "views": {
            f"{name}.png": hashlib.sha256((REVIEW_DIR / f"{name}.png").read_bytes()).hexdigest()
            for name in VIEWS
        },
    }
    (REVIEW_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    run()
