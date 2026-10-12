"""Export unmodified primary-foot solids and a visibly labelled PROVISIONAL bridge.
All geometry comes from mounts.py; this is a detail packet, not a separate mount.
"""
import hashlib
import json
from pathlib import Path
from build123d import Compound, Plane, export_step, export_stl
import mounts as M
import assembly_step27 as A

OUT = Path(__file__).resolve().parents[1] / "out"

def main():
    manifest = {"scope": "provisional_mount_detail_not_fitment", "states": {}, "sources": {}}
    for src in (Path(M.__file__), Path(__file__)):
        manifest["sources"][src.name] = hashlib.sha256(src.read_bytes()).hexdigest()
    x, y = max(M.stations(), key=lambda p: (p[1] > 0, p[0]))
    for state, angle in (("closed", 0), ("caught", M.STAGE1_DEG), ("released", M.OPEN_DEG)):
        parts = M.port_station(x, y, angle)
        parts += M.port_reference(x, y)[1]
        folder = OUT / f"parts_step30_mount_{state}"
        folder.mkdir(parents=True, exist_ok=True)
        for old in folder.glob("*.stl"):
            old.unlink()
        rows = []
        for i, p in enumerate(parts):
            dest = folder / f"{p.label}_{i:02d}.stl"
            export_stl(p, str(dest), tolerance=0.03, angular_tolerance=0.12)
            rows.append({"name": p.label, "stl": dest.name,
                         "sha256": hashlib.sha256(dest.read_bytes()).hexdigest()})
        packet = OUT / f"STEP30_MOUNT_{state.upper()}_PROVISIONAL.step"
        export_step(Compound(children=parts), str(packet))
        manifest["states"][state] = {"angle_deg": angle, "parts": rows,
            "step": packet.name, "step_sha256": hashlib.sha256(packet.read_bytes()).hexdigest()}
    # Section through the jaw bearing zone, not the gap between the two jaws.
    station = M.station_loc(x, y)
    section_plane = Plane(origin=station.position + (M.PIN_XS[1], 0, 0),
                          x_dir=(0, 1, 0), z_dir=(1, 0, 0))
    A._svg("SEC-30-001_bridge_capture", M.port_station(x, y) + M.port_reference(x, y)[1],
           section_plane,
           "STEP30 C-jaw wraps PROVISIONAL bridge; OPEN linkage/preload; design only, mm")
    (OUT / "step30_mount_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("STEP30_MOUNT_DETAIL_EXPORTED closed/caught/released with source and STL hashes")

if __name__ == "__main__":
    main()
