"""Write EVIDENCE_MANIFEST.json for the step-32 renders from a blender-loop run.

usage: python make_manifest.py <run_dir> <task_id> [counterfactual_run_dir]

Copies the matched stills (the ctx_/hero_/access_ views) next to this file, and hashes them and the
sources. Git LFS files are hashed by PAYLOAD: if the working-tree file is still a pointer, the run
fails rather than hashing the 133-byte pointer (verify task 165492). The pointer's own sha256 is
recorded separately, and the payload hash is checked against the pointer oid.

Verify task 165502 found the reference record out of step with the pinned geometry. So this script
also refuses to write a manifest when (a) a "Proxy now" figure in STEP32_REFERENCE_ASSETS.md section 2
differs from the run's measured score, or (b) an imported part STL differs from the sha256 the base
pin recorded in out/PROVENANCE.json. It hashes the reference record files too.
"""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path(subprocess.check_output(["git", "-C", str(HERE), "rev-parse", "--show-toplevel"], text=True).strip())
BASE_PIN = "0bb4c68121eb6974c6f739c8db10159f3394a967"      # step 30a: the CAD these renders show
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
MODEL = "models/r1t_topper/"
RECORD = [
    MODEL + "step27/STEP32_REFERENCE_ASSETS.md",
    MODEL + "step27/evidence/step32/source_observations.json",
    MODEL + "references/visual_reference_sources.md",
]


def doc_consistency(s0: dict) -> dict:
    """Section 2 of the reference record against the S0 scores: {quantity: [expected, cell]}."""
    doc = (REPO / RECORD[0]).read_text()
    sec = doc[doc.index("## 2. Dimensions"):doc.index("## 3. ")]
    rows = {c[1].strip(): [x.strip() for x in c[2:]] for c in
            (ln.split("|") for ln in sec.splitlines() if ln.startswith("| ")) if len(c) > 6}
    mm = lambda k: str(round(s0[k] * 1000))                                   # noqa: E731
    want = {   # row label -> (column index after the label, text the cell must contain)
        "Overall length": [(3, mm("length_m"))],
        "Front overhang": [(3, mm("front_overhang_m"))],
        "Rear overhang": [(3, mm("rear_overhang_m")),
                          # full phrases: the cell also quotes the superseded first-pin value
                          (4, f"The bumper top is unsourced: z {s0['rear_bumper_top_z']:.3f} m"),
                          (4, f"underside (z {s0['lowered_gate_underside_z']:.3f} m)"),
                          (4, f"traced rear face (x {s0['tailgate_face_x']:.3f} m)")],
        "Approach angle (standard)": [(3, f"{s0['approach_angle_deg']:.2f} deg")],
        "Departure angle (standard)": [(3, f"{s0['departure_angle_deg']:.2f} deg")],
        "Width without mirrors": [(3, mm("width_m"))],
        "Width with mirrors": [(3, mm("width_with_mirrors_m"))],
        "Roof height, no antenna": [(3, mm("roof_no_fin_above_ground_m"))],
        "Rail height above ground": [(3, mm("rail_above_ground_m"))],
    }
    out, bad = {}, []
    for label, checks in want.items():
        for col, text in checks:
            cell = rows[label][col]
            out.setdefault(label, []).append(text)
            if text not in cell:
                bad.append(f"{label}: expected {text!r} in {cell[:80]!r}")
    if bad:
        raise SystemExit("reference record disagrees with the measured proxy:\n  " + "\n  ".join(bad))
    return out


def parts_identity() -> dict:
    """Every STL the render lane imports, against the sha256 in the committed out/PROVENANCE.json."""
    base = MODEL + "step27/out/PROVENANCE.json"
    same = subprocess.run(["git", "-C", str(REPO), "diff", "--quiet", BASE_PIN, "HEAD", "--", base]).returncode == 0
    assert same, "out/PROVENANCE.json differs from the base pin"
    prov = json.loads((REPO / base).read_text())["outputs"]
    res = {"provenance_file": base, "provenance_sha256": sha(REPO / base), "identical_to_base_pin": BASE_PIN}
    for sub in ("parts", "parts_access"):
        files = sorted((REPO / MODEL / "step27" / "out" / sub).glob("*.stl"))
        want = {k: v for k, v in prov.items() if k.startswith(f"step27/out/{sub}/")}
        got = {f"step27/out/{sub}/{f.name}": sha(f) for f in files}
        assert got == want, f"out/{sub}: STLs differ from PROVENANCE.json"
        res[sub] = {"stl_files": len(files), "sha256_match_provenance": len(got)}
    return res


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
        "revises": "2a282d696952bf9cceb18619daa7728fea8e0537 (failed verify task 165502: reference record); "
                   "before it 8024b24117cfcee762950e153ebb6116fc22ed2f (failed verify task 165492: tailgate)",
        "built_on_commit": base,
        "cad_identity": "topper geometry unchanged: closed parts = out/parts as exported by base-pin "
                        "assembly_step27.step27_assembly(0.0) (gitignored); open-hatch parts = committed "
                        "out/parts_access; both sha256-checked against out/PROVENANCE.json (parts_identity); "
                        "params.json / rivian_reference.json / step27/cad unchanged",
        "parts_identity": parts_identity(),
        "reference_record": {rel: {"sha256": sha(REPO / rel), "bytes": (REPO / rel).stat().st_size}
                             for rel in RECORD},
        "reference_record_matches_scores": doc_consistency(
            next(s["scores"] for s in ledger["steps"] if s["step"].startswith("S0_"))),
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
            "doc": "parent 8024b241 s11_truck.py + style json under the revised s17_access.py checks; run "
                   "under task 165497 and carried over (s17_access.py is unchanged since)",
            "scores": {s["step"]: s["scores"] for s in cl["steps"]},
        }
    (HERE / "EVIDENCE_MANIFEST.json").write_text(json.dumps(man, indent=1) + "\n")
    shutil.copy2(run / "ledger.json", HERE / "loop_ledger.json")
    print(f"{len(images)} images, {len(man['sources'])} sources")


if __name__ == "__main__":
    main()
