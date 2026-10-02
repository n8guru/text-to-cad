"""Measure the Gen-1 R1T and R1S from Rivian's own orthographic line art.

    python style/rivian_reference.py [--cache DIR]      -> style/rivian_reference.json

Sources (downloaded to a cache OUTSIDE the repo, SHA-256 verified, never redistributed):
  * R1T Owner's Guide 2022-2024 v2024.19  p.14 (front/rear), p.17 (driver side)
  * R1S Owner's Guide 2022-2024 v2024.27  p.14 (front/rear), p.16 (driver side)
  * R1T Upfitting Guide 2025-09-24         p.59 (plan view, vector line art)

Only derived numbers are written. Scale anchors are PUBLISHED Rivian dimensions:
  side views  -> wheelbase (R1T 3,450 mm Upfit p.28; R1S 121.1 in = 3,076 mm, rivian.com support)
  plan view   -> overall length 5,514 mm (Upfit p.28)
  rear views  -> outer tyre edges = track 1,730 + section 275 mm (Upfit p.28-29)
Every anchor is cross-checked against a second published dimension and the disagreement is
recorded, because these are illustrations, not dimensioned drawings. Heights come from the side
view, whose wheelbase scale reproduces Rivian's published 1,834 mm roof height to <0.1 %.

Output frame = the topper frame used by params.json: metres, X rearward, Z up, origin on the
centreline at the bed's inside front wall, z = 0 on the bed-rail top. The rear axle sits at
x = published tailgate-to-axle geometry (see ``rear_axle_x`` below).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = Path(__file__).resolve().parent
OUT = HERE / "rivian_reference.json"

SOURCES = {
    "R1T_OG": ("https://assets.rivian.com/2md5qhoeajym/530xs9hu11xOKefT2JrvA5/"
               "46f6cb5d5756b8320d3eb494a902e66c/r1t-og-en-us-20240527.pdf",
               "e6c544346ef87548d956934a46c2a656c24d3196ed271ff929ec213e59b775b6"),
    "R1S_OG": ("https://assets.rivian.com/2md5qhoeajym/7Ao7NIFkLxOZtvdc7Fqh70/"
               "c8c4a585ae141effce63b41ead2b8ce0/r1s-og-en-us-20240722.pdf",
               "27eda35d31ee2d38baae97d336d2fb38e128f1fdc04ab9f9334c21e8e8977061"),
    "R1T_UPFIT": ("https://assets.ctfassets.net/2md5qhoeajym/5ysf6K5UtGtHedY1fMeClC/"
                  "b83307f7e8f03838a1906bff88707f95/r1t-upfitting-guide-en-us-20250924.pdf",
                  "847d036f3977764d151689442ea54e4141bf70113b9d8380d46d796c3982552a"),
}
PUBLISHED = {  # value_mm, where
    "r1t_wheelbase": (3450.0, "R1T Upfitting Guide p.28"),
    "r1t_length": (5514.0, "R1T Upfitting Guide p.28"),
    "r1t_height_no_antenna": (1834.0, "R1T Upfitting Guide p.28 (34 in tyres, standard)"),
    "r1t_track": (1730.0, "R1T Upfitting Guide p.28"),
    "r1t_tyre_section": (275.0, "275/65R20, R1T Upfitting Guide p.29"),
    "r1t_tyre_r": (432.3, "275/65R20: (20 x 25.4 + 2 x 0.65 x 275) / 2"),
    "r1t_width_body": (2014.0, "R1T Upfitting Guide p.28, not including mirrors"),
    "r1t_bed_len_rail": (1381.0, "R1T Upfitting Guide p.30, tailgate up, no tonneau"),
    "r1t_bed_width": (1299.0, "R1T Upfitting Guide p.28"),
    "r1t_rear_overhang": (1155.0, "R1T Upfitting Guide p.28"),
    "r1s_wheelbase": (3075.9, "121.1 in, rivian.com/support/article/what-is-the-wheelbase-length"),
    "r1s_length": (5100.3, "200.8 in, stories.rivian.com/sizing-up-the-r1s"),
}
# The params.json frame puts the rear axle 405 mm behind the bed's inside front wall. It is
# re-derived here from the side view (tailgate face) + published bed length, and reported.
TAILGATE_T = 0.060          # tailgate shell thickness assumed for the bed-front derivation


# ------------------------------------------------------------------------------ plumbing
def fetch(cache: Path) -> dict:
    cache.mkdir(parents=True, exist_ok=True)
    got = {}
    for key, (url, sha) in SOURCES.items():
        p = cache / (key + ".pdf")
        if not p.exists():
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            p.write_bytes(urllib.request.urlopen(req, timeout=120).read())
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        if h != sha:
            raise SystemExit(f"{key}: sha256 {h} != recorded {sha}; refuse to measure a changed "
                             "source silently (update the manifest deliberately)")
        got[key] = p
    return got


def render(pdf: Path, page: int, dpi: int, cache: Path, crop=None) -> Path:
    stem = cache / f"{pdf.stem}_p{page}_{dpi}"
    args = ["pdftoppm", "-r", str(dpi), "-f", str(page), "-l", str(page), "-png"]
    if crop:
        x, y, w, h = crop
        args += ["-x", str(x), "-y", str(y), "-W", str(w), "-H", str(h)]
    out = Path(f"{stem}-{page:03d}.png")
    if not out.exists():
        subprocess.run(args + [str(pdf), str(stem)], check=True)
    return out


def line_mask(png: Path, y0=0, y1=None, x0=0, x1=None):
    """Rivian line art is mid-grey (170); callouts are black. Keep grey, drop callouts."""
    a = np.asarray(Image.open(png).convert("L")).astype(int)
    m = (a >= 140) & (a <= 225) & ~ndi.binary_dilation(a < 60, iterations=10)
    m[:y0] = False
    if y1:
        m[y1:] = False
    m[:, :x0] = False
    if x1:
        m[:, x1:] = False
    return m


def fit_circle(x, y):
    A = np.c_[2 * x, 2 * y, np.ones_like(x)]
    c, *_ = np.linalg.lstsq(A, x ** 2 + y ** 2, rcond=None)
    r = float(np.sqrt(c[2] + c[0] ** 2 + c[1] ** 2))
    return float(c[0]), float(c[1]), r, float(np.abs(np.hypot(x - c[0], y - c[1]) - r).max())


def wheels(m):
    """Two tyre circles fitted to the bottom arc of each tyre outline."""
    ys, xs = np.nonzero(m)
    g = int(ys.max())
    low = np.full(m.shape[1], -1)
    for x in range(xs.min(), xs.max() + 1):
        c = np.nonzero(m[:, x])[0]
        if len(c):
            low[x] = c.max()
    near = np.nonzero(low >= g - 3)[0]
    fits = []
    for grp in np.split(near, np.nonzero(np.diff(near) > 60)[0] + 1):
        X = np.arange(int(grp.mean() - 170), int(grp.mean() + 170))
        Y = low[X].astype(float)
        k = Y > g - 90
        fits.append(fit_circle(X[k].astype(float), Y[k]))
    return g, int(xs.min()), int(xs.max()), fits, low


def top_profile(m, xa, xb, step=4, y0=0, y1=None):
    out = []
    for X in range(xa, xb, step):
        c = np.nonzero(m[y0:y1, X])[0]
        if len(c):
            out.append((X, y0 + int(c.min())))
    return out


def rightmost(m, Y, xa, xb):
    c = np.nonzero(m[Y, xa:xb])[0]
    return xa + int(c.max()) if len(c) else None


def smooth(vals, k=5):
    v = np.asarray(vals, float)
    return ndi.median_filter(v, size=k, mode="nearest")


def rnd(v, n=4):
    return round(float(v), n)


# ------------------------------------------------------------------------------ R1T side
def r1t_side(png: Path) -> dict:
    m = line_mask(png, 540, 1750)
    g, xmin, xmax, fits, low = wheels(m)
    (fx, fy, fr, fres), (rx, ry, rr, rres) = fits
    s = PUBLISHED["r1t_wheelbase"][0] / (rx - fx)                  # mm / px
    zr = lambda Y: (g - Y) * s                                        # mm above ground
    xr = lambda X: (X - rx) * s                                       # mm, rear-axle origin
    # bed-rail top: the flat thick line between cab back and tailgate
    rail = [c for c in (np.nonzero(m[760:960, X])[0] for X in range(2320, 2940, 5)) if len(c)]
    railY = float(np.median([760 + c.min() for c in rail]))
    rail_mm = zr(railY)
    # cab back silhouette (right-most thick line under the spoiler) and spoiler tip
    cab = [(zr(Y), xr(rightmost(m, Y, 2150, 2300))) for Y in range(662, int(railY) - 25, 4)
           if rightmost(m, Y, 2150, 2300) is not None]
    spoiler = max(((xr(X), zr(Y)) for X, Y in top_profile(m, 2150, 2300, 1, 560, 700)),
                  key=lambda p: p[0])
    # tailgate outer face
    tail = [xr(rightmost(m, Y, 2800, 3060)) for Y in range(int(railY) + 60, int(railY) + 260, 4)
            if rightmost(m, Y, 2800, 3060) is not None]
    top = top_profile(m, xmin, xmax + 1, 6, 540, 1750)
    # callout leaders crossing the outline leave narrow VALLEYS in the traced top (the topmost
    # surviving pixel is a lower line). A grey closing removes valleys up to ~100 mm wide and
    # keeps the real steps (cab back) and peaks (antenna fin, spoiler).
    tz = ndi.grey_closing(smooth([zr(Y) for _, Y in top], 3), size=9)
    # sill: lowest body line between the wheels, away from the tyres
    sill = [zr(low[X]) for X in range(int(fx + 330), int(rx - 330), 6) if low[X] > 0]
    # rear-axle position in the topper frame, from tailgate face + published bed length
    tail_face = float(np.median(tail))
    bed_front = tail_face - (TAILGATE_T * 1000 + PUBLISHED["r1t_bed_len_rail"][0])
    ax = -bed_front / 1000.0                                          # rear axle x, m
    X = lambda mm: rnd(mm / 1000.0 + ax)                              # rear-axle mm -> frame m
    Z = lambda mm: rnd((mm - rail_mm) / 1000.0)                       # ground mm -> frame m
    cab_rail = min(cab, key=lambda p: abs(p[0] - (rail_mm + 45)))
    cab_top = min(cab, key=lambda p: abs(p[0] - (rail_mm + 360)))
    return {
        "scale_mm_per_px": rnd(s, 5),
        "anchor": "wheelbase 3450 mm",
        "cross_checks": {
            "roof_height_mm": [rnd(zr(min(Y for _, Y in top if True)), 1), 1834.0,
                               "includes antenna fin; see roof_max below"],
            "roof_max_no_fin_mm": [rnd(max(v for (Xp, _), v in zip(top, tz)
                                           if not (-900 < xr(Xp) < -760)), 1),
                                   PUBLISHED["r1t_height_no_antenna"][0]],
            "overall_length_mm": [rnd((xmax - xmin) * s, 1), PUBLISHED["r1t_length"][0]],
            "tyre_r_mm": [rnd(rr * s, 1), PUBLISHED["r1t_tyre_r"][0]],
            "circle_fit_residual_px": [rnd(max(fres, rres), 2), 0.0],
        },
        "rail_height_above_ground_mm": rnd(rail_mm, 1),
        "rear_axle_x": rnd(ax),
        "front_axle_x": rnd(ax - PUBLISHED["r1t_wheelbase"][0] / 1000.0),
        "tailgate_face_x": X(tail_face),
        "cab_back": {"x_at_rail+45": X(cab_rail[1]), "x_at_rail+360": X(cab_top[1]),
                     "rake_deg_top_forward": rnd(np.degrees(np.arctan2(
                         cab_rail[1] - cab_top[1], cab_top[0] - cab_rail[0])), 2),
                     "points_x_z": [[X(x), Z(z)] for z, x in cab[::4]]},
        "spoiler_tip": {"x": X(spoiler[0]), "z": Z(spoiler[1])},
        "sill_z": Z(float(np.median(sill))),
        "front_bumper_x": X(xr(xmin)),
        "rear_extreme_x": X(xr(xmax)),
        "top_profile_x_z": [[X(xr(Xp)), Z(v)] for (Xp, _), v in zip(top, tz)],
        "wheel_r_drawn_mm": rnd(rr * s, 1),
    }


# ------------------------------------------------------------------------------ R1S side
def r1s_side(png: Path) -> dict:
    m = line_mask(png, 540, 1750)
    g, xmin, xmax, fits, low = wheels(m)
    (fx, _, _, _), (rx, _, rr, _) = fits
    s = PUBLISHED["r1s_wheelbase"][0] / (rx - fx)
    zr = lambda Y: (g - Y) * s
    xr = lambda X: (X - rx) * s
    roof = top_profile(m, 1150, 2900, 5, 560, 760)
    # liftgate silhouette: right-most line per row between the roof and the lamp line
    lg = [(zr(Y), xr(rightmost(m, Y, 2800, 3100))) for Y in range(600, 1000, 4)
          if rightmost(m, Y, 2800, 3100) is not None]
    # straight raked portion: fit a line to the rows between 55 % and 95 % of the greenhouse
    col = 2550                                             # through the rear quarter glass
    rows = np.nonzero(m[600:1000, col])[0] + 600
    grp = [(int(g_.min()), int(g_.max())) for g_ in np.split(rows, np.nonzero(np.diff(rows) > 2)[0] + 1)]
    roof_top = zr(grp[0][0])
    dlo_top = zr(sum(grp[1]) / 2)
    belt = zr(sum(grp[2]) / 2)
    gh = roof_top - belt
    straight = [(z, x) for z, x in lg if belt + 0.05 * gh < z < roof_top - 0.22 * gh]
    zz, xx = np.array(straight).T
    k = np.polyfit(zz, xx, 1)[0]                           # dx/dz, mm/mm
    rake = float(np.degrees(np.arctan(-k)))
    corner = [(x, z) for z, x in lg if z > roof_top - 0.22 * gh]
    roof_pts = [(xr(X_), zr(Y_)) for X_, Y_ in roof if -1500 < xr(X_) < 520]
    rx_, rz_ = np.array(roof_pts).T
    slope = float(np.polyfit(rx_, rz_, 1)[0])
    return {
        "scale_mm_per_px": rnd(s, 5), "anchor": "wheelbase 121.1 in",
        "cross_checks": {"overall_length_mm": [rnd((xmax - xmin) * s, 1), PUBLISHED["r1s_length"][0]],
                         "tyre_r_mm": [rnd(rr * s, 1), 432.3]},
        "greenhouse_mm": rnd(gh, 1), "dlo_height_mm": rnd(dlo_top - belt, 1),
        "dlo_fraction_of_greenhouse": rnd((dlo_top - belt) / gh, 3),
        "roof_band_above_dlo_mm": rnd(roof_top - dlo_top, 1),
        "roof_slope_rear_half_pct": rnd(slope * 100, 3),
        "liftgate_rake_deg": rnd(rake, 2),
        "rear_corner_drop_fraction": rnd((roof_top - min(z for _, z in corner)) / gh, 3)
        if corner else None,
        "rear_corner_run_fraction": rnd((max(x for x, _ in corner) - min(x for x, _ in corner)) / gh, 3)
        if corner else None,
    }


# ------------------------------------------------------------------------------ rear views
def rear_view(png: Path, name: str) -> dict:
    m = line_mask(png, 700, 2100, 1700, 3100)
    ys, xs = np.nonzero(m)
    g = int(ys.max())
    band = np.nonzero(m[g - 40:g + 1].any(0))[0]
    L, R = int(band.min()), int(band.max())
    s = (PUBLISHED["r1t_track"][0] + PUBLISHED["r1t_tyre_section"][0]) / (R - L)
    cx = (L + R) / 2
    prof = []
    for Y in range(int(ys.min()), g, 3):
        row = np.nonzero(m[Y])[0]
        if len(row):
            prof.append(((g - Y) * s, (cx - row.min()) * s, (row.max() - cx) * s))
    z, hl, hr = (np.array(v) for v in zip(*prof))
    half = np.minimum(hl, hr)                      # symmetric silhouette, ignores one-sided marks
    body_half = PUBLISHED["r1t_width_body"][0] / 2 / s * s   # published, mm (checked below)
    meas_body_half = float(np.percentile(half, 99))
    # roof: first row whose half-width exceeds 300 mm (the antenna fin is narrower)
    i_roof = int(np.nonzero(half > 300)[0][0])
    z_roof = z[i_roof]
    # tailgate top: the first row below the roof that is a full-width horizontal line. The
    # mirrors stick out above it, so a "half-width jump" test finds the mirrors, not the rail.
    lim = int(0.80 * meas_body_half / s)
    i_rail = None
    for i in range(i_roof + 10, len(z)):
        Y = g - int(round(z[i] / s))
        seg = m[Y - 1:Y + 2, int(cx) - lim:int(cx) + lim].any(0)
        if seg.mean() > 0.97:
            i_rail = i
            break
    z_rail = z[i_rail]
    gh = z_roof - z_rail
    # greenhouse (C/D-pillar) silhouette: outermost pixel inside 0.85 x body half, i.e. without
    # the mirrors
    cap = int(0.85 * meas_body_half / s)
    gz, gw = [], []
    for i in range(i_roof, i_rail):
        Y = g - int(round(z[i] / s))
        row = np.nonzero(m[Y, int(cx) - cap:int(cx) + cap])[0]
        if len(row):
            gz.append(z[i])
            gw.append(min(cap - row.min(), row.max() - cap) * s)
    gz, gw = np.array(gz), np.array(gw)
    # a callout leader crossing one side leaves a one-sided row; drop anything implausible
    ok = (gw > 0.30 * meas_body_half) & (gw < 0.83 * meas_body_half)
    ok[0] = True                                   # the roof-top row is legitimately narrow
    gz, gw = gz[ok], gw[ok]
    gh_rows = [(rnd((zz - z_rail) / gh, 3), rnd(hh / meas_body_half, 4)) for zz, hh in zip(gz, gw)]
    sel = (gz > z_rail + 0.15 * gh) & (gz < z_rail + 0.80 * gh)
    # Theil-Sen (median of pairwise slopes): the liftgate/C-pillar trim lines leave a few rows
    # that are plausible in width but wrong in shape, and a least-squares fit follows them
    zs, ws = gz[sel], gw[sel]
    pair = [(ws[j] - ws[i]) / (zs[j] - zs[i]) for i in range(len(zs)) for j in range(i + 1, len(zs))
            if abs(zs[j] - zs[i]) > 20.0]
    k = float(np.median(pair))
    half = np.interp(z, gz[::-1], gw[::-1]) if len(gz) else half
    i_rail_g = len(gw) - 1
    return {
        "anchor": "outer tyre edges = 1730 + 275 mm",
        "scale_mm_per_px": rnd(s, 5),
        "cross_checks": {"roof_height_mm": [rnd(z_roof, 1), PUBLISHED["r1t_height_no_antenna"][0]],
                         "body_width_mm": [rnd(2 * meas_body_half, 1), PUBLISHED["r1t_width_body"][0]]},
        "rail_to_roof_ratio": rnd(z_rail / z_roof, 4),
        "greenhouse_over_roof_height": rnd(gh / z_roof, 4),
        "greenhouse_tumblehome_deg": rnd(np.degrees(np.arctan(-k)), 2),
        "greenhouse_half_width_at_rail_over_body_half": rnd(gw[i_rail_g] / meas_body_half, 4),
        "roof_edge_half_width_over_body_half": rnd(gw[0] / meas_body_half, 4),
        "greenhouse_section_zfrac_halfwfrac": gh_rows[::3],
        "name": name,
    }


# ------------------------------------------------------------------------------ plan view
def plan_view(png: Path) -> dict:
    a = np.asarray(Image.open(png).convert("L")).astype(int)
    m = (a >= 140) & (a <= 215)
    ys, xs = np.nonzero(m)
    x0, x1 = int(xs.min()), int(xs.max())
    s = PUBLISHED["r1t_length"][0] / (x1 - x0)
    cy = (ys.min() + ys.max()) / 2
    # the bed's inside front and rear walls are the two long vertical lines in the bed region
    counts = m[:, 2000:3050].sum(0)
    cols = np.nonzero(counts > 600)[0] + 2000
    walls = [int(g_.mean()) for g_ in np.split(cols, np.nonzero(np.diff(cols) > 5)[0] + 1)]
    bf, br = walls[0], walls[-1]
    X = lambda px: rnd((px - bf) * s / 1000.0)
    Yw = lambda py: rnd((cy - py) * s / 1000.0)

    def clusters(Xp):
        c = np.nonzero(m[:, Xp])[0]
        parts = np.split(c, np.nonzero(np.diff(c) > 2)[0] + 1) if len(c) else []
        return sorted({Yw((p.min() + p.max()) / 2) for p in parts if (p.min() + p.max()) / 2 < cy})

    outline = []
    for Xp in range(x0, x1 + 1, 12):
        c = np.nonzero(m[:, Xp])[0]
        if len(c):
            outline.append([X(Xp), Yw(c.min())])
    mid = (bf + br) // 2
    # bed accessory ports: the page draws every port as a pair of ORANGE half-pills (Upfit p.59,
    # "Accessory ports are also located along the top of the truck bed"). Centre = mean of a pair.
    rgb = np.asarray(Image.open(png).convert("RGB")).astype(int)
    org = (rgb[..., 0] > 200) & (rgb[..., 1] > 130) & (rgb[..., 1] < 200) & (rgb[..., 2] < 80)
    lab, n_ = ndi.label(org)
    cen = [c for c, k in zip(ndi.center_of_mass(org, lab, range(1, n_ + 1)),
                             ndi.sum(org, lab, range(1, n_ + 1))) if k > 50]
    bed = sorted((c[1], c[0]) for c in cen if bf - 20 < c[1] < br + 20)      # (x_px, y_px)
    ports = {}
    # group by x into the front and rear port rows (the two pill halves are ~30 px apart)
    groups, cur = [], [bed[0]]
    for c in bed[1:]:
        if c[0] - cur[-1][0] > 100:
            groups.append(cur)
            cur = []
        cur.append(c)
    groups.append(cur)
    ports = [[X(float(np.mean([c[0] for c in g]))),
              rnd(float(np.mean([abs(cy - c[1]) for c in g])) * s / 1000.0)] for g in groups]
    return {
        "bed_accessory_ports_x_halfy": ports,
        "bed_accessory_ports_note": "Upfit p.59 plan view, orange port symbols; x from the bed's inside "
                                    "front wall, half-width from the drawing centreline; both sides averaged",
        "anchor": "overall length 5514 mm", "scale_mm_per_px": rnd(s, 5),
        "cross_checks": {"bed_inside_length_mm": [rnd((br - bf) * s, 1), PUBLISHED["r1t_bed_len_rail"][0]]},
        "bed_inside_front_x": 0.0, "bed_inside_rear_x": X(br),
        "lines_half_width_mid_bed": clusters(mid),
        "lines_half_width_at_spoiler": clusters(bf - int(0.127 / s * 1000)),
        "body_half_width_outline_x_y": outline,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=str(Path.home() / ".cache" / "r1t_topper_refs"))
    a = ap.parse_args()
    cache = Path(a.cache)
    pdf = fetch(cache)
    side_t = render(pdf["R1T_OG"], 17, 400, cache)
    side_s = render(pdf["R1S_OG"], 16, 400, cache)
    rear_t = render(pdf["R1T_OG"], 14, 400, cache)
    rear_s = render(pdf["R1S_OG"], 14, 400, cache)
    plan = render(pdf["R1T_UPFIT"], 59, 900, cache, crop=(2250, 5300, 3150, 1400))
    out = {
        "_doc": __doc__.strip().splitlines()[0],
        "_sources": {k: {"url": u, "sha256": h} for k, (u, h) in SOURCES.items()},
        "_published_anchors_mm": {k: {"value": v, "where": w} for k, (v, w) in PUBLISHED.items()},
        "r1t_side": r1t_side(side_t),
        "r1s_side": r1s_side(side_s),
        "r1t_rear": rear_view(rear_t, "R1T"),
        "r1s_rear": rear_view(rear_s, "R1S"),
        "r1t_plan": plan_view(plan),
    }
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    t = out["r1t_side"]
    print(f"R1T rail {t['rail_height_above_ground_mm']} mm above ground; cab back "
          f"{t['cab_back']['x_at_rail+45']} m; spoiler tip {t['spoiler_tip']}; "
          f"rear axle x {t['rear_axle_x']}")
    print(f"R1S liftgate rake {out['r1s_side']['liftgate_rake_deg']} deg; DLO fraction "
          f"{out['r1s_side']['dlo_fraction_of_greenhouse']}")
    print(f"tumblehome R1T {out['r1t_rear']['greenhouse_tumblehome_deg']} deg, R1S "
          f"{out['r1s_rear']['greenhouse_tumblehome_deg']} deg")
    print("RIVIAN_REFERENCE_OK", OUT)


if __name__ == "__main__":
    main()
