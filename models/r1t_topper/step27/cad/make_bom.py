"""Generate BOM27.md + out/BOM27.csv (Step 27 rev 10). One source of truth per fact, no retyping:

    quantities  <- out/parts_manifest.json (geometry) and cad/fasteners.py (joint schedule)
    vendor/PN   <- hardware.json
    prices      <- bom_prices.json, each row verified against research/pricing_2026-10.json
    custom cost <- ROM model below (stated assumptions, NOT quotes)

    python cad/make_bom.py
"""
from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fasteners as FS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
HW = json.loads((ROOT / "hardware.json").read_text())
MAN = json.loads((ROOT / "out" / "parts_manifest.json").read_text())
PRICES = json.loads((ROOT / "bom_prices.json").read_text())
RESEARCH = json.loads((ROOT / "research" / "pricing_2026-10.json").read_text())
C = FS.manifest_counts(MAN)


def _research(pn, vendor):
    for it in RESEARCH["items"]:
        if it.get("part_number") == pn and it.get("vendor") == vendor:
            return it
    return None


def price(key):
    """(unit, basis, vendor, url, date, note) for a BOM line, verified against the research file."""
    p = PRICES["lines"][key]
    if p["basis"] == "NONE":
        it = _research(p["pn"], p["vendor"]) if p.get("pn") else None
        return None, "NONE", p.get("vendor"), (it or {}).get("product_url"), None, p.get("why", "")
    it = _research(p["pn"], p["vendor"])
    if it is None:
        raise SystemExit(f"bom_prices.json {key}: ({p['pn']}, {p['vendor']}) not in the research file")
    listed = [it.get("unit_price_usd"), it.get("per_piece_usd")]
    tiers = (it.get("notes") or "") + " " + (it.get("evidence") or "") + " " + str(it.get("qty_break"))
    if not any(v is not None and abs(v - p["unit"]) < 0.006 for v in listed) and f"{p['unit']:.2f}" not in tiers:
        raise SystemExit(f"bom_prices.json {key}: unit {p['unit']} not found in the research entry")
    note = "; ".join(x for x in (p.get("break"), p.get("why"), p.get("note")) if x)
    return p["unit"], p["basis"], p["vendor"], it.get("product_url"), it.get("date_retrieved"), note


def n(*pat):
    return FS.count_of(C, *pat)


def seal_length_m() -> float:
    import hatch as HA
    import side_socket as SS
    return round((4 * SS.seal_land_path().length + HA.seal_land_path().length) / 1000 * 1.10, 1)


def pad_length_m() -> float:
    import mounts
    return round(sum(p.bounding_box().size.X for p in mounts.foot_pads()) / 1000 * 1.05, 2)


def purchased_lines():
    """(key, function, manufacturer, pn, qty, unit, material, qty basis)."""
    h = HW
    sock_latches = n("LATCH_latch_housing") - n("HATCH_LATCH_latch_housing")
    return [
        ("plf_lock", "Key lock cylinder under each PLF paddle, keyed alike (one key, four stations)",
         h["plf_lock"]["manufacturer"], h["plf_lock"]["pn"], n("PLF_LOCK"), "ea",
         "zinc-alloy cam lock, nickel", "manifest PLF_LOCK"),
        ("plf_detent", "PLF paddle detent plunger (closed / stage 1 clicks), M8 ball-nose",
         h["plf_detent"]["manufacturer"], h["plf_detent"]["pn"], n("PLF_DETENT"), "ea",
         "18-8 SS body, 440C nose", "manifest PLF_DETENT"),
        ("foot_pad", "Foot-to-rail-cap pad, 33 % set by the PLF seat-flange stop (ASTM D1056 2B2, 1/4 in, PSA)",
         "Pres-On (spec match) / any 2B2 EPDM", "P9200 1/4 in x 4 in", pad_length_m(), "m",
         "closed-cell EPDM", "modelled pad strips + 5 %"),
        ("rotary_latch", "Two-stage rotary latch, 4 sockets x 2 + hatch x 2", "Southco",
         h["rotary_latch"]["pn"], n("latch_housing_R4"), "ea", "316 SS, passivated", "manifest latch_housing"),
        ("support_plate", "Fork-bolt support plate (R4-30 ultimate 14,230 N)", "Southco",
         h["rotary_latch"]["support_plate_pn"], n("latch_housing_R4"), "ea", "steel, zinc", "1 per latch"),
        ("striker", "Striker bolt (the bar the rotor grabs)", "Southco", h["striker"]["pn"],
         n("STRIKER_BOLT"), "ea", "316 SS", "manifest STRIKER_BOLT"),
        ("release_handle", "Interior release paddle, 1 per socket", "Southco", h["release_handle"]["pn"],
         n("handle_pan"), "ea", "Al, black powder coat", "manifest handle (hatch release G8: not counted)"),
        ("cable_splitter", "One pull -> two latches, 1 per socket", "Southco",
         h["release_handle"]["splitter_pn"], n("CABLE_SPLITTER"), "ea", "per Southco", "manifest CABLE_SPLITTER"),
        ("release_cable", "Push-pull cable splitter -> latch, 450 mm (SERIES_ONLY)", "Southco",
         h["release_cable"]["pn"], n("RELEASE_CABLE"), "ea", "SS cable, acetal liner, PP jacket",
         "manifest RELEASE_CABLE (2 per socket)"),
        ("clip_trigger", "Cable retainer clip at the R4 bottom trigger", "Southco",
         h["release_cable"]["retainer_clip_trigger"], sock_latches, "ea", "steel", "1 per cabled latch"),
        ("cable_bracket", "Panel cable bracket at each cabled latch (9 mm door)", "Southco", "R4-0-50253-1",
         sock_latches, "ea", "steel", "1 per cabled latch"),
        ("t_handle", "Keyed T-handle on the hatch (GRIP MISMATCH open, G8)", "Southco", h["t_handle"]["pn"],
         n("T_HANDLE"), "ea", "zinc / steel", "manifest T_HANDLE"),
        ("t_gasket", "E3 flange gasket (IP65 needs it)", "Southco", h["t_handle"]["gasket_pn"], n("T_HANDLE"),
         "ea", "neoprene", "1 per T-handle"),
        ("t_spur_washer", "E3 spur washer (round hole in composite)", "Southco", h["t_handle"]["spur_washer_pn"],
         n("T_HANDLE"), "ea", "steel", "1 per T-handle"),
        ("t_keys", "Spare CH751 keys", "Southco", h["t_handle"]["spare_keys_pn"], 1, "set", "-", "1 set"),
        ("hinge_L", "Concealed multi-joint hatch hinge, LH", "JW Winco / Ganter", "GN 7233-NI-50-L-MT",
         1, "ea", "AISI 304", "1 L per pair"),
        ("hinge_R", "Concealed multi-joint hatch hinge, RH", "JW Winco / Ganter", "GN 7233-NI-50-R-MT",
         1, "ea", "AISI 304", "1 R per pair"),
        ("gas_strut", "Hatch lift support 50 N", "Stabilus", h["gas_strut"]["pn"], n("GAS_STRUT_BODY"), "ea",
         "steel, black", "manifest GAS_STRUT_BODY"),
        ("ball_stud", "Strut ball stud Dia 10 / M8", "Stabilus", h["gas_strut"]["ball_stud"]["pn"],
         n("BALL_STUD"), "ea", "steel, zinc", "manifest BALL_STUD"),
        ("bulb_seal", "EPDM bulb seal, 4 socket lands + hatch", "Trim-Lok", h["bulb_seal"]["pn"],
         seal_length_m(), "m", "EPDM sponge on dense EPDM", "modelled seal paths + 10 %"),
        ("locating_pin_round", "Module locator, round", "MISUMI", h["locating_pin_round"]["pn"],
         n("LOCATING_PIN_ROUND"), "ea", "per MISUMI", "manifest"),
        ("locating_pin_diamond", "Module locator, diamond", "MISUMI", h["locating_pin_diamond"]["pn"],
         n("LOCATING_PIN_DIAMOND"), "ea", "per MISUMI", "manifest"),
        ("bushing", "Flanged bushing for the pins", "MISUMI", h["bushing"]["pn"], n("BUSHING"), "ea",
         "per MISUMI", "manifest"),
        ("ball_plunger", "Anti-rattle ball plunger M8", "McMaster-Carr", h["ball_plunger"]["pn"],
         n("BALL_PLUNGER"), "ea", "18-8 SS / 440C", "manifest"),
        ("chmsl", "Secondary CHMSL (FMVSS 108, Upfit p.65)", "Maxxima", h["chmsl"]["pn"], n("CHMSL"), "ea",
         "PC lens", "manifest"),
        ("harness_connector", "12 V upfitter mating connector, J019", "Aptiv", h["harness_tap"]["pn"], 1, "ea",
         "PA", "1 harness"),
        ("harness_terminal", "Metri-Pack 280 terminals", "Aptiv", h["harness_tap"]["terminal_pn"], 3, "ea",
         "tin-plated", "3-position connector"),
    ]


def fastener_lines():
    rows, totals, _ = FS.schedule(MAN)
    out = []
    for key, q in totals.items():
        f = HW["fasteners"][key]
        out.append((key, f["role"], f.get("manufacturer"), f"{f['standard']} {f['size']}", q, "ea",
                    f["material"], "fasteners.py joint schedule"))
    area, ml, carts = FS.adhesive_cartridges()
    k = HW["consumables"]
    out += [
        ("structural_adhesive", f"Structural bonds, {area} m^2 at 0.25 mm + 60 % waste = {ml} mL", "3M",
         k["structural_adhesive"]["pn"], carts, "cartridge", "toughened epoxy", "fasteners.bond_area_m2"),
        ("mix_nozzle", "Mixing nozzles, 2 per cartridge", "3M", "01003 EPX square nozzle", 2 * carts, "ea",
         "-", "2 per cartridge"),
        ("threadlocker", "Strikers, ball studs, plungers, hinge/latch screws, PLF tuning screw", "Henkel Loctite",
         k["threadlocker"]["pn"], 1, "bottle", "-", "1 bottle covers the build"),
        ("anti_seize", "A4 into 6061 threads (PLF rail + tuning screws, cage screws)", "Tef-Gel", k["anti_seize"]["pn"], 1,
         "tube", "PTFE", "1 tube covers the build"),
        ("glazing_tape", "WINDOW panes + front pane to their flanges", "3M", k["glazing_tape"]["pn"],
         round(FS.window_tape_m(MAN) + 3.4, 1), "m", "acrylic foam", "pane perimeters + 10 %"),
    ]
    return out, rows


# ------------------------------------------------------------------------------ custom ROM
# ROM (rough order of magnitude) cost model for parts WE control. NOT a quote. Assumptions stated:
RATES = {"cnc_h": 95.0, "fab_h": 75.0, "composite_h": 65.0}
STOCK = {"6061": 9.0, "316": 14.0, "17-4PH": 45.0, "PC": 35.0, "UHMW": 12.0, "ABS": 10.0, "carbon": 90.0, "EPDM": 0.0}
# family -> (drawing, stock key, buy-to-fly, cycle h per part, setup h per lot, critical tolerances)
CUSTOM = {
    "SHELL_CARBON_SANDWICH": ("DWG-27-000", "carbon", 1.6, 60.0, 0.0,
                              "profile 1.0 to A-surface; foot underside flatness 1.0 (pad band)"),
    "SOCKET_FRAME_6061": ("DWG-27-001", "6061", 6.0, 4.5, 3.0, "bushing true position 0.05; land flatness 0.3"),
    "MODULE_PLUG_FRAME_6061": ("DWG-27-003", "6061", 6.0, 4.0, 3.0, "module profile 0.3; pin bores to MISUMI fit"),
    "STRIKER_BRACKET_custom": ("DWG-27-004", "316", 2.0, 0.4, 1.0, "slot +/-3 mm travel; hole 10.6"),
    "COMPRESSION_LIMITER_custom_UHMW": ("DWG-27-006", "UHMW", 2.0, 0.15, 0.5, "thickness 7.40 +0/-0.05"),
    "J_HOOK_316": ("DWG-27-007", "316", 1.8, 0.4, 1.0, "fin seat height 0.1"),
    "HATCH_SURROUND_6061": ("DWG-27-008", "6061", 5.0, 6.0, 3.0, "land flatness 0.3; latch pattern 0.2"),
    "BASE_RAIL_6061": ("DWG-27-010", "6061", 1.5, 2.5, 2.0, "slot position 0.2; pocket floor flatness 0.05"),
    "HATCH_LEAF_CARBON": ("DWG-27-011", "carbon", 1.6, 18.0, 0.0, "edge profile 0.5 to the surround (4 mm shut line)"),
    "PLF_BODY_6061": ("DWG-27-012", "6061", 5.0, 4.0, 3.0,
                      "seat flange top 4.00 +0/-0.05; slot floor/roof parallel 0.03; hinge bores 5.00 H7 coaxial 0.03; lock bore 19.2 H11"),
    "PLF_PADDLE_6061": ("DWG-27-013", "6061", 3.5, 1.0, 1.0, "hinge bore 5.2 H8; plate flat 0.1; dimples r 2.3 +/-0.05 at 7.5 from the axis"),
    "PLF_HOOK_SLIDER_17_4PH": ("DWG-27-013", "17-4PH", 3.0, 0.8, 1.0, "tooth top faces ground flat 0.02, pin-bottom datum -18.00 +/-0.05; slider-to-slot fit 0.2"),
    "PLF_SHIM_316": ("DWG-27-013", "316", 1.5, 0.05, 0.3, "thickness 1.00 +/-0.02 (kit 0.5 / 1.0)"),
    "GLAZING_PANE": ("DWG-27-014", "PC", 1.3, 0.5, 0.5, "profile +/-0.5"),
    "GLAZING_RETAINER": ("DWG-27-014", "6061", 4.0, 0.8, 1.0, "profile +/-0.3"),
    "CAGE_BAR_316": ("DWG-27-015", "316", 1.1, 0.15, 0.5, "length +/-0.3"),
    "CAGE_RAIL_316": ("DWG-27-015", "316", 1.3, 0.5, 0.5, "welded-cage flatness 1.0"),
    "TOOLBOX_DOOR_CARBON": ("DWG-27-016", "carbon", 1.6, 4.0, 0.0, "profile 0.3 to the module flange"),
    "TOOLBOX_TUB_ABS": ("DWG-27-016", "ABS", 1.8, 1.5, 2.0, "profile +/-1.0"),
    "WINDOW_PANE_PC": ("DWG-27-017", "PC", 1.3, 0.5, 0.5, "flatness 1.0; profile +/-0.5"),
    "ROOF_HARDPOINT": ("DWG-27-018", "6061", 1.8, 0.3, 0.5, "top flush 0/-0.3"),
    "LEAF_STRIKER_ARM_6061": ("DWG-27-019", "6061", 3.0, 0.6, 1.0, "position 0.5 to hinge datum"),
    "LEAF_STRUT_BOSS_6061": ("DWG-27-019", "6061", 3.0, 0.3, 0.5, "position 0.5 to hinge datum"),
    "FRONT_PASS_THROUGH_PANE_PC": ("DWG-27-020", "PC", 1.3, 0.5, 0.5, "profile +/-0.5"),
    "HATCH_DRAIN_TUBE": ("SEC-27-003 (cut length)", "EPDM", 1.0, 0.05, 0.0, "length +/-2; PA12 8x5 tube stock"),
}
EXTRA_CUSTOM = [("POTTED_INSERT_M4_6061", "DWG-27-018", "6061-T6", "CNC turn + knurl", "clear anodise Type II",
                 0.003, "6061", 2.0, 0.08, 0.5, "M4-6H; flange flush to inner skin")]


def _fam_key(fam):
    for k in sorted(CUSTOM, key=len, reverse=True):
        if k in fam:
            return k
    return None


def _rate(stock):
    if stock == "carbon":
        return RATES["composite_h"]
    return RATES["cnc_h"] if stock in ("6061", "UHMW", "PC") else RATES["fab_h"]


def custom_lines():
    fams = {}
    for m in MAN:
        if m["status"] != "CUSTOM":
            continue
        k = _fam_key(FS.family(m["part"]))
        if k is None:
            raise SystemExit(f"custom part with no drawing/ROM row: {m['part']}")
        f = fams.setdefault(k, {"m": m, "kg": 0.0, "n": 0})
        f["kg"] += m["mass_kg"]
        f["n"] += 1
    out = []
    for k, f in sorted(fams.items()):
        dwg, stock, b2f, cyc, setup, tol = CUSTOM[k]
        kg = f["kg"] / f["n"]
        unit = kg * b2f * STOCK[stock] + cyc * _rate(stock) + setup * RATES["cnc_h"] / f["n"]
        m = f["m"]
        out.append((k, m["material"], m["process"], m["finish"], dwg, tol, f["n"], round(kg, 3), round(unit, 2)))
    _, _, sched_custom = FS.schedule(MAN)
    for (k, dwg, mat, proc, fin, kg, stock, b2f, cyc, setup, tol) in EXTRA_CUSTOM:
        q = sched_custom.get(k, 0)
        unit = kg * b2f * STOCK[stock] + cyc * RATES["cnc_h"] + setup * RATES["cnc_h"] / max(q, 1)
        out.append((k, mat, proc, fin, dwg, tol, q, kg, round(unit, 2)))
    return out


# ------------------------------------------------------------------------------ output
def esc(x):
    return "—" if x is None or x == "" else str(x).replace("|", "\\|")


def money(x):
    return "—" if x is None else f"${x:,.2f}"


def main():
    rows_csv = []
    a = []
    A = a.append
    A("# Step 27 — sourced BOM (rev 11: Rivian-crossbar-style Port Latch Foot + dated costs)\n")
    A("Generated by `cad/make_bom.py`. Quantities come from the geometry (`out/parts_manifest.json`) "
      "and the joint schedule (`cad/fasteners.py`); vendor/PN from `hardware.json`; prices from "
      "`bom_prices.json`, each verified against `research/pricing_2026-10.json` (public list prices "
      f"retrieved **{PRICES['retrieved']}**; the rev-11 PLF lock and the crossbar reference article **2026-10-06**; USD, excl. tax/freight). Do not hand-edit.\n")
    A("**Nothing has been purchased, quoted or ordered.** Price basis: EXACT = same manufacturer PN; "
      "EQUIV = cost proxy for a stated equivalent (reason given) - order the specified PN; NONE = no "
      "public price could be read (reason given). Custom-part costs are a ROM model, not quotes.\n")

    def section(title, lines, cat):
        A(f"\n## {title}\n")
        A("| # | Function | Manufacturer | Part number | Qty | Unit cost | Ext. cost | Basis | Vendor / URL | Note |")
        A("|---|---|---|---|---|---|---|---|---|---|")
        tot, unpriced, minbuy = 0.0, [], 0.0
        for i, (key, fn, mfr, pn, qty, unit, mat, basis) in enumerate(lines, 1):
            up, b, vendor, url, date, note = price(key)
            p = PRICES["lines"][key]
            if key == "bulb_seal" and up is not None:
                ext, ucell = math.ceil(qty / p["per_roll_m"]) * up, f"{money(up)}/roll"
            elif key == "foot_pad" and up is not None:
                ext, ucell = up, f"{money(up)}/sheet"
            else:
                ext = None if up is None else up * qty
                ucell = money(up)
            if ext is not None:
                tot += ext
                minbuy += max(ext, (p.get("moq") or 0) * up)
            else:
                unpriced.append(key)
            v = f"[{esc(vendor)}]({url})" if url else esc(vendor)
            A(f"| {i} | {esc(fn)} | {esc(mfr)} | {esc(pn)} | {qty:g} {unit} | {ucell} | {money(ext)} | "
              f"{b} | {v} | {esc(note)[:170]} |")
            rows_csv.append([cat, key, fn, mfr, pn, qty, unit, mat, up, ext, b, vendor, url, date, basis, note])
        A(f"\n**Subtotal (priced lines): {money(tot)}**; buying at vendor minimum-order quantities: "
          f"{money(minbuy)}. Unpriced lines: {len(unpriced)} ({', '.join(unpriced) or 'none'}).\n")
        return tot, minbuy, unpriced

    t1, m1, u1 = section("1. Purchased hardware (counted from the geometry)", purchased_lines(), "purchased")
    fl, joints = fastener_lines()
    t2, m2, u2 = section("2. Fasteners and consumables (from the joint schedule)", fl, "fastener")

    ref_lines = [("crossbar_reference", "REFERENCE ARTICLE for calibration P-CAL-01b (measure the crossbar foot + a real port); "
                  "NOT a product part", HW["crossbar_reference"]["manufacturer"], HW["crossbar_reference"]["pn"], 1,
                  "set", "—", "1 set (2 crossbars, 2 keys)")]
    t2b, m2b, u2b = section("2b. Calibration reference article (not in the roll-up)", ref_lines, "reference")
    fb_lines = [("port_adapter", "DOCUMENTED FALLBACK ONLY (rev-10 bolt-on adapter); would also need the rev-10 M10 stud / "
                 "nut / Nord-Lock / slot-washer / spacer / shim stack. NOT in any total", HW["port_adapter"]["manufacturer"],
                 HW["port_adapter"]["pn"], HW["port_adapter"]["qty"], "ea", "billet 6061, clear anodise",
                 "4 stations if the PLF is abandoned")]
    t2c, m2c, u2c = section("2c. Documented fallback (not in the roll-up)", fb_lines, "fallback")

    A("\n## 3. Joint schedule — every attachment in the product\n")
    A("| Joint | What it joins | Count | Fasteners per joint | Custom parts per joint | Torque / treatment | Grip / note |")
    A("|---|---|---|---|---|---|---|")
    for j in joints:
        per = ", ".join(f"{q} x {k}" for k, q in j.get("per", [])) or "—"
        cus = ", ".join(f"{q} x {k}" for k, q in j.get("custom_per", [])) or "—"
        A(f"| {j['id']} | {esc(j['joint'])} | {j['n']} | {per} | {cus} | {esc(j['torque'])} | {esc(j['grip'])} |")

    A("\n## 4. Machined / fabricated parts (controlled by our drawings)\n")
    A("ROM unit cost = mass x buy-to-fly x stock $/kg + cycle h x shop rate + setup h x $95 / lot qty. "
      f"Assumed rates: CNC ${RATES['cnc_h']:.0f}/h, fabrication ${RATES['fab_h']:.0f}/h, composite "
      f"lay-up ${RATES['composite_h']:.0f}/h; stock $/kg {STOCK}. Excludes composite TOOLING (moulds), "
      "anodise/passivate lot charges, freight and margin: a class-5 estimate (-50 / +100 %), for "
      "budgeting only. Step 23 (vendor quote path) replaces it.\n")
    A("| Part family | Material | Process | Finish | Drawing | Critical tolerances | Qty | Mass ea (kg) | ROM unit | ROM ext. |")
    A("|---|---|---|---|---|---|---|---|---|---|")
    t3 = 0.0
    for (k, mat, proc, fin, dwg, tol, q, kg, unit) in custom_lines():
        t3 += unit * q
        A(f"| {k} | {esc(mat)} | {esc(proc)} | {esc(fin)} | {dwg} | {esc(tol)} | {q} | {kg} | "
          f"{money(unit)} | {money(unit * q)} |")
        rows_csv.append(["custom", k, k, "custom", dwg, q, "ea", mat, unit, unit * q, "ROM", None, None,
                         None, proc, tol])
    A(f"\n**ROM subtotal, fabricated parts (tooling excluded): {money(t3)}**\n")

    A("\n## 5. Roll-up\n")
    A("| Block | Priced total | At vendor MOQ | Unpriced lines |")
    A("|---|---|---|---|")
    A(f"| Purchased hardware | {money(t1)} | {money(m1)} | {len(u1)} |")
    A(f"| Fasteners + consumables | {money(t2)} | {money(m2)} | {len(u2)} |")
    A(f"| Fabricated parts (ROM) | {money(t3)} | — | 0 |")
    A(f"| **Total (known)** | **{money(t1 + t2 + t3)}** | | **{len(u1) + len(u2)}** |")
    A("\nThe total is a floor, not a price: unpriced lines, composite tooling, freight, tax, finishing "
      "lot charges and assembly labour are outside it.\n")

    A("\n## 6. What is NOT resolved — named, not hidden\n")
    for key in sorted(HW):
        h = HW[key]
        if key.startswith("_") or not isinstance(h, dict):
            continue
        if h.get("open"):
            A(f"- **{key}** ({h.get('status')}) — {h['open']}")
        if h.get("CRITICAL"):
            A(f"- **{key}** — {h['CRITICAL']}")
    A("- **Port Latch Foot (PLF) — port internals and the Rivian foot are NOT published** (OPEN check "
      "`plf_port_internals_P-CAL-01b`): the port recess, the latch-pin pair, the hook / paddle / lock geometry, the drive "
      "link between paddle cam and hook slider and the lock-to-paddle interlock are PROVISIONAL until one Rivian Cargo "
      "Crossbars set is measured (P-CAL-01b). The foot absorbs +/-3 mm along the rail, 0 - 4 mm across (shims) and "
      "+/-3 mm in height (slotted screws) at fit-up.")
    A("- **plf_lock** — CompX C8053 body/flange/cam dimensions ESTIMATED (compx.com blocked scripted access); price is a "
      "third-party Amazon listing.")
    A("- **unpriced lines** — " + ", ".join(u1 + u2) + ": PNs are exact; the price was not readable "
      "without a login, an office-hours API or a distributor that blocks scripted access, or the size "
      "was not in the research request.")
    A("- **hatch exterior release (G8)** — the hatch's release handle, splitter and cables are NOT in "
      "these quantities; they follow the hatch access decision.")
    A("- **toolbox door lock** — E3-108-015 (key-alike) not modelled, not counted.")

    A("\n## 7. Mounting-interface provenance (rev 11) — what the attachment is built on\n")
    A("Operator card 2081357 rejected the rev-10 stud-and-nut interface: the topper must connect to the bed **the same "
      "way the Rivian crossbars attach** (a latching foot with a paddle). Full source list with fetch dates: "
      "`research/PORT_MECHANISM_SOURCES.md`.\n")
    A("| Fact used | Source (URL, date) | Status |")
    A("|---|---|---|")
    A("| Crossbar end = foot with a hinged paddle; install = lift paddle, set foot in the port (click 1), push paddle down "
      "(click 2); key lock cylinder under the paddle; remove = paddle up halfway, unlock, lift paddle while raising the bar; "
      "'crossbar latch tuning' | R1T Owner's Guide 2022-10-17 p.152-154, "
      "[PDF](https://assets.rivian.com/2md5qhoeajym/530xs9hu11xOKefT2JrvA5/76d493c33659e9ceac1d72175ec54f26/r1t-owners-guide-en-us-20221017.pdf), fetched 2026-10-06 | researched, not verified on hardware |")
    A("| Latching 'tang' on the clamp opens over the CLEATS on the bed rails; two clicks | "
      "[trailrivian.com crossbar install](https://trailrivian.com/threads/cross-bar-unboxing-and-install-on-my-r1t.846/), 2026-10-06 | researched |")
    A("| Port presents a 'dual-barrel' latch-pin pair | Team 1EV crossbar storage mount (evsportline.com), 2026-10-06 | researched |")
    A("| Two anchor points per port, 25 mm apart (two M8 points) | [Mars Adventure Gear port adapter](https://marsag.co/products/accessory-port-adapter-rivian), 2026-10-06; Upfit Guide p.59 plan view shows each port as a pair of marks | researched |")
    A("| 2,500 N (250 kg) per port; do not modify the ports; use Rivian-approved crossbars | R1T Upfitting Guide 2025-09-24 p.59 | Rivian's stated value, not tested here |")
    A("| Reference article: R1 Cargo Crossbars, Bright $700 / Dark $800, snap-on, lock + key set | "
      "[Rivian Gear Shop](https://gearshop.rivian.com/products/cargo-crossbars), 2026-10-06 | researched; **not purchased** |")
    A("| Port recess, depth, pin diameter / position, the Rivian foot's hook, paddle and lock geometry | **NOT PUBLISHED** | "
      "**PROVISIONAL** - calibration P-CAL-01b |")
    A("\nThe Weistec 09-111-00078-7 adapter (rev 10) is a bolt-on M10 interface and is **not** the crossbar mechanism: it "
      "is retained only as the documented fallback (section 2c).\n")

    A("\n## 8. Standing caveat\n")
    A("No purchase order, no supplier contact, no quote. FEA, prototype fit, real-truck calibration "
      "(P-CAL-01b crossbar + port, tape session), fabrication release and Nate-only design approval remain later gates.")

    (ROOT / "BOM27.md").write_text("\n".join(a) + "\n")
    with open(ROOT / "out" / "BOM27.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["category", "key", "function", "manufacturer", "part_number", "qty", "unit",
                    "material", "unit_cost_usd", "ext_cost_usd", "basis", "vendor", "url", "date",
                    "qty_basis_or_process", "note_or_tolerance"])
        w.writerows(rows_csv)
    print(f"BOM27.md + out/BOM27.csv: purchased {money(t1)} ({len(u1)} unpriced), fasteners+consumables "
          f"{money(t2)} ({len(u2)} unpriced), fabricated ROM {money(t3)}")
    print("BOM27_OK")


if __name__ == "__main__":
    main()
