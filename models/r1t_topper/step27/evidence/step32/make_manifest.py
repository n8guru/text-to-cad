"""Write EVIDENCE_MANIFEST.json for the step-32 renders from a blender-loop run.

usage: python make_manifest.py <run_dir> <task_id> [counterfactual_run_dir]

Copies the matched stills (the ctx_/hero_/access_ views) next to this file, and hashes them and the
sources. Git LFS files are hashed by PAYLOAD: if the working-tree file is still a pointer, the run
fails rather than hashing the 133-byte pointer (verify task 165492). The pointer's own sha256 is
recorded separately, and the payload hash is checked against the pointer oid.
"""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path(subprocess.check_output(["git", "-C", str(HERE), "rev-parse", "--show-toplevel"], text=True).strip())
SOURCES = [
    "models/r1t_topper/blender/s11_truck.py",
    "models/r1t_topper/blender/s12_topper.py",
    "models/r1t_topper/blender/s13_hero.py",
    "models/r1t_topper/blender/s17_access.py",
    "models/r1t_topper/blender/r1t_lib.py",
    "models/r1t_topper/blender/params.json",
    "models/r1t_topper/step27/style/rivian_reference.json",
    "models/r1t_topper/step27/style/r1t_published_specs_32.json",
    "models/r1t_topper/step27/cad/assembly_step27.py",
    "models/r1t_topper/step27/out/R1T_TOPPER_STEP27.step",
    "models/r1t_topper/step27/out/R1T_TOPPER_STEP27_open.step",
]
VIEWS = ("ctx_", "hero_", "access_")


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def source_entry(rel: str) -> dict:
    p = REPO / rel
    head = p.open("rb").read(200)
    if head.startswith(b"version https://git-lfs.github.com/spec/v1"):
        raise SystemExit(f"{rel} is an LFS pointer in the working tree; run `git lfs checkout` first")
    e = {"sha256": sha(p), "bytes": p.stat().st_size}
    attr = subprocess.run(["git", "-C", str(REPO), "check-attr", "filter", "--", rel],
                          capture_output=True, text=True).stdout
    if attr.strip().endswith("lfs"):
        ptr = subprocess.check_output(["git", "-C", str(REPO), "show", f"HEAD:{rel}"])
        oid = next(ln.split(":", 1)[1] for ln in ptr.decode().splitlines() if ln.startswith("oid sha256:"))
        assert oid == e["sha256"], f"{rel}: payload sha256 != LFS pointer oid"
        e["lfs_pointer_sha256"] = hashlib.sha256(ptr).hexdigest()
        e["lfs_oid_matches_payload"] = True
    return e


def main():
    run = Path(sys.argv[1])
    task = int(sys.argv[2])
    cf = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    ledger = json.loads((run / "ledger.json").read_text())
    for old in HERE.glob("*.png"):
        old.unlink()
    images = []
    for st in sorted((run / "stills").glob("*.png")):
        labels = [s["step"] for s in ledger["steps"] if s["step"][:3] in ("S0_", "S2_", "S3_")]
        view = next((st.stem[len(lb) + 1:] for lb in labels if st.stem.startswith(lb + "_")), "")
        if view.startswith(VIEWS):        # skip the runtime's own {side,overhead,front} stills
            dst = HERE / st.name
            shutil.copy2(st, dst)
            images.append({"file": st.name, "sha256": sha(dst)})
    base = subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip()
    man = {
        "task_id": task,
        "project_id": 924515,
        "step": "32",
        "defect": 61514,
        "revises": "8024b24117cfcee762950e153ebb6116fc22ed2f (failed verify task 165492)",
        "built_on_commit": base,
        "cad_identity": "topper geometry unchanged: closed parts regenerated from base-pin "
                        "assembly_step27.step27_assembly(0.0); open-hatch parts = committed out/parts_access; "
                        "params.json / rivian_reference.json / step27/cad unchanged",
        "truck": "render-lane proxy from Rivian line art + published specs; NOT a scan, NOT calibration, "
                 "NO fitment approval",
        "blender_loop_run": run.name,
        "scores": {s["step"]: s["scores"] for s in ledger["steps"]},
        "images": images,
        "sources": {rel: source_entry(rel) for rel in SOURCES},
    }
    if cf:
        cl = json.loads((cf / "ledger.json").read_text())
        man["counterfactual_parent_proxy"] = {
            "run": cf.name,
            "doc": "parent 8024b241 s11_truck.py + style json under the revised s17_access.py checks",
            "scores": {s["step"]: s["scores"] for s in cl["steps"]},
        }
    (HERE / "EVIDENCE_MANIFEST.json").write_text(json.dumps(man, indent=1) + "\n")
    shutil.copy2(run / "ledger.json", HERE / "loop_ledger.json")
    print(f"{len(images)} images, {len(man['sources'])} sources")


if __name__ == "__main__":
    main()
