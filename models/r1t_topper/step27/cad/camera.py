"""Step 31: R1T camera sight lines through the topper -- measured on the authoritative solids.

Decision 2154445 (Nate): "We also need a rear camera OR optics (maybe fiberoptic?) extension to feed
the rear camera, that is on the back of cab." This module measures what the topper actually hides
from the OEM cameras, before (pre-Step-31 shell) and after (the Step 31 camera tab), with every
camera position, target set and occluder traceable to a source or a CAD solid.

Vehicle frame (geom.py): X rearward, Y driver(+), Z up, origin = bed inside front wall centreline at
the bed-rail top. Millimetres.

SOURCES (Rivian PDFs, SHA-256 pinned in ../STEP31_CAMERA.md):
  UPFIT  R1T Upfitting Guide 2025-09-24 (847d036f...552a)
         p.49 rear exterior view: item 10 "Truck bed camera" at the top centre of the cab back, just
              under the roof edge between the two CHMSL lamps; item 11 "Rear surround view camera"
              at the centre of the rear bumper fascia above the hitch.
         p.107 the truck bed camera view is shown automatically "When in R (Reverse) and the
              tailgate is down".
         p.108 "Do not block the exterior camera field of view", "Keep the camera in its current
              position", "Do not modify the camera harness, including connectors", "Avoid placing
              any light sources within the camera's field of view".
  OG     R1T Owner's Guide 2024-05-27 (e6c54434...75b6) p.307 Gear Guard: "A camera monitors the
         truck bed".
  FMVSS  49 CFR 571.111 S6.2 (trucks/MPVs <= 4,536 kg GVWR) and S14.1.4 test-object layout: seven
         0.8 m x 0.3 m cylinders, F/G 0.3 m, D/E 3.05 m, A/B/C 6.1 m behind the rear bumper plane;
         A/D/F 1.52 m left, C/E/G 1.52 m right, B on the centreline.

The camera POSITIONS are scaled off the p.49 line drawing (no Rivian dimension exists for them): two
independent scale anchors (roof-to-tailgate-top and roof-to-tyre-contact) disagree by ~10 %, so
every camera carries an explicit +/- band and the checks re-run the measurement at its corners.
Camera aim and field of view are NOT published; the measurement is therefore TARGET-based (can a
straight line from the lens reach the thing the camera exists to show?) and claims nothing about
image quality, FOV coverage, calibration or Rivian software behaviour.
"""
from __future__ import annotations

import itertools
from functools import lru_cache

import geom as G

T = G.T

# ------------------------------------------------------------------------------ cameras (sourced)
CAMERAS = {
    "TRUCK_BED_CAMERA": {
        "source": "UPFIT p.49 item 10 / p.105 item 5 (top centre of cab back, under roof edge)",
        # p.49 rear view: lens 10 px below the roof line at 400 dpi; 1.78-1.96 mm/px -> z 443-446.
        # The params.json cab back (side-photo derived) tops out at the spoiler tip z 427, so the
        # drawing reading would float the lens above the modelled cab. Nominal = the point ON the
        # modelled cab-back face (glass top (-180, 355) -> spoiler tip (-132, 427)) at z 420, the
        # CHMSL strip; the band spans the cab model up to the drawing reading.
        "xyz": (-136.7, 0.0, 420.0),
        "band": {"x": (-155.0, -130.0), "z": (405.0, 450.0)},
        "role": "bed view (OG p.307) and reverse view with the tailgate DOWN (UPFIT p.107)",
    },
    "REAR_SURROUND_VIEW_CAMERA": {
        "source": "UPFIT p.49 item 11 (rear bumper fascia centre, above the hitch)",
        # 613 px below the roof line at 400 dpi -> z -631 (1.78 mm/px) .. -741 (1.96 mm/px)
        "xyz": (T["rear_end_x"] - 10.0, 0.0, -690.0),
        "band": {"x": (T["rear_end_x"] - 30.0, T["rear_end_x"]), "z": (-750.0, -630.0)},
        "role": "reverse view with the tailgate up (the topper never sits below the rail plane "
                "behind the bed)",
    },
}

GROUND_Z = T["ground_z"]
BED_FLOOR_Z = -T["bed_depth"]


# ------------------------------------------------------------------------------ targets
def bed_floor_targets():
    """121 points 5 mm above the bed floor: x 100..1350, y -550..550 (inside the 1299 bed)."""
    xs = [100.0 + 125.0 * i for i in range(11)]
    ys = [-550.0 + 110.0 * j for j in range(11)]
    return [(x, y, BED_FLOOR_Z + 5.0) for x in xs for y in ys]


FMVSS_OBJECTS = {  # S14.1.4: (metres behind the rear bumper plane, metres left(+) of centreline)
    "A": (6.10, 1.52), "B": (6.10, 0.0), "C": (6.10, -1.52),
    "D": (3.05, 1.52), "E": (3.05, -1.52), "F": (0.30, 1.52), "G": (0.30, -1.52),
}


def fmvss_targets():
    """Centre-axis points of each S14.1.4 test object: base+50, mid-height, top band (-75 mm).

    The axis point, not the surface: this is a line-of-sight screen, not the S14.1 photometric
    test (no image, no visual-angle measurement)."""
    out = []
    for name, (back_m, left_m) in FMVSS_OBJECTS.items():
        x = T["rear_end_x"] + back_m * 1000.0
        y = left_m * 1000.0
        for tag, dz in (("base", 50.0), ("mid", 400.0), ("top_band", 725.0)):
            out.append((f"{name}_{tag}", (x, y, GROUND_Z + dz)))
    return out


# ------------------------------------------------------------------------------ occluders
def _is_glazing(label: str) -> bool:
    return "PANE" in label.upper()


@lru_cache(maxsize=4)
def occluders(camera_tab: bool = True, hatch_deg: float = 0.0):
    """(label, shape) for every leaf of the CLOSED Step 27 assembly, in vehicle coordinates, with
    the shell (and front pane) swapped for the pre-Step-31 versions when ``camera_tab`` is False.
    The OEM truck itself (cab, body, tailgate) is NOT an occluder here: it hides what it hides with
    or without a topper, and its envelopes are keep-outs, not surfaces."""
    import copy

    import assembly_step27 as A
    import shell as SH
    a = A.step27_assembly(hatch_deg, with_shell=False)
    out = [(lab, shp) for lab, shp in A._flatten(a)]
    if not camera_tab:
        out = [(lab, shp) for lab, shp in out if "FRONT_PASS_THROUGH_PANE" not in lab]
        out.append(("FRONT_PASS_THROUGH_PANE_PC", SH.front_pane(camera_tab=False)))
    sh = copy.copy(SH.shell(camera_tab))
    out.append(("SHELL_CARBON_SANDWICH", sh))
    return tuple(out)


class SightLines:
    """Segment-vs-solid classifier on OCC's face intersector (exact B-rep, not a mesh)."""

    def __init__(self, parts):
        from OCP.IntCurvesFace import IntCurvesFace_ShapeIntersector
        self.items = []
        for label, shp in parts:
            ix = IntCurvesFace_ShapeIntersector()
            ix.Load(shp.wrapped, 1e-4)
            bb = shp.bounding_box()
            self.items.append((label, ix, (bb.min.X, bb.min.Y, bb.min.Z, bb.max.X, bb.max.Y,
                                          bb.max.Z)))

    @staticmethod
    def _slab(p, d, length, box):
        t0, t1 = 0.0, length
        for k in range(3):
            lo, hi = box[k] - 1.0, box[k + 3] + 1.0
            if abs(d[k]) < 1e-12:
                if not lo <= p[k] <= hi:
                    return False
                continue
            a, b = (lo - p[k]) / d[k], (hi - p[k]) / d[k]
            a, b = min(a, b), max(a, b)
            t0, t1 = max(t0, a), min(t1, b)
            if t0 > t1:
                return False
        return True

    def trace(self, p, q, skip_start=1.0, skip_end=1.0):
        """Labels crossed by the open segment p->q (first ``skip_start`` mm ignored: the lens)."""
        from OCP.gp import gp_Dir, gp_Lin, gp_Pnt
        d = [q[i] - p[i] for i in range(3)]
        length = sum(v * v for v in d) ** 0.5
        u = [v / length for v in d]
        line = gp_Lin(gp_Pnt(*p), gp_Dir(*u))
        hits = []
        for label, ix, box in self.items:
            if not self._slab(p, u, length, box):
                continue
            ix.Perform(line, skip_start, length - skip_end)
            if ix.IsDone() and ix.NbPnt() > 0:
                hits.append(label)
        return hits


def classify(sl: SightLines, cam_xyz, target):
    hits = sl.trace(cam_xyz, target)
    opaque = [h for h in hits if not _is_glazing(h)]
    if opaque:
        return "BLOCKED", opaque
    return ("THROUGH_GLAZING" if hits else "CLEAR"), hits


def measure(camera: str, targets, camera_tab: bool, xyz=None, sl=None):
    """Counts of CLEAR / THROUGH_GLAZING / BLOCKED sight lines and the opaque parts responsible."""
    sl = sl or SightLines(occluders(camera_tab))
    cam = xyz or CAMERAS[camera]["xyz"]
    counts = {"CLEAR": 0, "THROUGH_GLAZING": 0, "BLOCKED": 0}
    blockers: dict[str, int] = {}
    for t in targets:
        state, parts = classify(sl, cam, t)
        counts[state] += 1
        if state == "BLOCKED":
            for p in set(parts):
                key = p.split("__")[-1]
                blockers[key] = blockers.get(key, 0) + 1
    n = len(targets)
    seen = counts["CLEAR"] + counts["THROUGH_GLAZING"]
    return {"camera": camera, "xyz": list(cam), "camera_tab": camera_tab, "n": n, **counts,
            "visible_fraction": round(seen / n, 4), "blocked_by": dict(sorted(blockers.items()))}


def band_corners(camera: str):
    b = CAMERAS[camera]["band"]
    y = CAMERAS[camera]["xyz"][1]
    return [(x, y, z) for x, z in itertools.product(b["x"], b["z"])]


# ------------------------------------------------------------------------------ drawing reference
def sight_wedge(x_near: float = 100.0, x_far: float = 1350.0, half_t: float = 2.0):
    """00_REFERENCE body for SEC-31-001: the centreline fan from the nominal bed-camera lens to the
    bed floor between ``x_near`` and ``x_far`` (the farthest bed-floor row the provision measures
    visible at the nominal lens). A drawing aid, not product geometry and not an FOV claim."""
    from build123d import Plane, Polygon, Pos, Sphere, extrude
    cx, _, cz = CAMERAS["TRUCK_BED_CAMERA"]["xyz"]
    tri = Polygon((cx, cz), (x_near, BED_FLOOR_Z), (x_far, BED_FLOOR_Z), align=None)
    wedge = extrude(Plane.XZ * tri, amount=half_t, both=True)
    out = wedge + Pos(cx, 0, cz) * Sphere(8.0)          # the lens point, R8 marker
    out.label = "00_REFERENCE_TRUCK_BED_CAMERA_SIGHT_FAN"
    return out
