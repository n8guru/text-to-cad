"""Tie the generated outputs to the exact sources that produced them.

    python cad/provenance.py            write out/PROVENANCE.json (run last, after every generator)
    python cad/provenance.py --check    exit 1 unless every recorded input AND output still matches

A commit cannot contain its own hash, so the previous out/COMMIT.txt always named the parent and
went stale on the next commit. Source hashes do not: if any input changes, --check fails until the
outputs are regenerated.
"""
from __future__ import annotations

import hashlib
import json
import platform
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEP27 = HERE.parent
MODEL = STEP27.parent                     # models/r1t_topper
OUT = STEP27 / "out" / "PROVENANCE.json"

INPUTS = ["blender/params.json", "step27/hardware.json", "step27/style/rivian_reference.json",
          "step27/style/rivian_reference.py", "step27/bom_prices.json",
          "step27/research/pricing_2026-10.json"] + \
         sorted(f"step27/cad/{p.name}" for p in HERE.glob("*.py"))
OUTPUT_GLOBS = ["step27/out/*.step", "step27/out/parts_manifest.json", "step27/out/kinematics.json",
                "step27/out/checks.json", "step27/out/mounting_analysis.json", "step27/out/BOM27.csv",
                "step27/drawings/*.svg", "step27/BOM27.md"]
COMMANDS = ["python step27/style/rivian_reference.py", "python step27/cad/assembly_step27.py",
            "python step27/cad/make_drawings.py", "python step27/cad/make_bom.py",
            "python step27/cad/checks_step27.py", "python step27/cad/provenance.py"]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def outputs():
    out = []
    for g in OUTPUT_GLOBS:
        out += sorted(MODEL.glob(g))
    return out


def write():
    import build123d
    rec = {
        "_doc": __doc__.strip().splitlines()[0],
        "commands_in_order": COMMANDS,
        "tools": {"python": platform.python_version(), "build123d": build123d.__version__},
        "inputs": {k: sha(MODEL / k) for k in INPUTS},
        "outputs": {str(p.relative_to(MODEL)): sha(p) for p in outputs()},
    }
    OUT.write_text(json.dumps(rec, indent=1) + "\n")
    print(f"PROVENANCE_WRITTEN {len(rec['inputs'])} inputs, {len(rec['outputs'])} outputs")


def check() -> int:
    if not OUT.exists():
        print("PROVENANCE_MISSING")
        return 1
    rec = json.loads(OUT.read_text())
    bad = [k for k, v in {**rec["inputs"], **rec["outputs"]}.items()
           if not (MODEL / k).exists() or sha(MODEL / k) != v]
    new_inputs = sorted(set(INPUTS) - set(rec["inputs"]))
    if bad or new_inputs:
        print(f"PROVENANCE_STALE changed={bad[:10]} unrecorded_inputs={new_inputs}")
        return 1
    print(f"PROVENANCE_OK {len(rec['inputs'])} inputs, {len(rec['outputs'])} outputs unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(check() if "--check" in sys.argv else (write() or 0))
