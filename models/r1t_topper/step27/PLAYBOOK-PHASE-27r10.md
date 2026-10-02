## Phase 8: Attaching hardware + costed BOM (Step 27 rev 10, mesh task 136191, 2026-10-02 ~08:12–09:40 UTC, ~90 min)

Producer: Claude Opus 5.5 headless mesh worker. Worktree `~/text-to-cad-worktrees/task-136191`,
branch `agents/claude/task-136191-r1t-hardware-bom` off `df01d411` (descendant of `57634ea0`).
Evidence: `models/r1t_topper/step27/MOUNTING27.md`, `BOM27.md`, `out/BOM27.csv`,
`out/mounting_analysis.json`, `out/checks.json`, `drawings/SEC-27-008*`, `DWG-27-010, 012–020`.

- **What worked**
  - *Find the OEM-sanctioned interface first.* The Upfitting Guide (p.59) says the bed accessory
    ports are THE structural interface (2,500 N each, do not modify). One web search then found a
    purchased, non-modifying adapter (Weistec 09-111-00078-7, $100, M10). Designing around a
    buyable adapter beat reverse-engineering an unpublished proprietary port.
  - *Re-measure carried numbers.* The bed-port positions had no provenance. The same SHA-pinned
    plan view draws the ports as orange symbols; a 20-line colour-blob measurement in
    `rivian_reference.py` found the rear ports 21 mm inboard of the carried value — larger than
    the slot float. Lesson: every carried dimension gets a source or gets measured.
  - *Metal-to-metal stop.* Keeping the composite out of the bolt clamp path and letting a
    machined spacer set the pad compression turned "how tight?" into a checked dimension.
  - *Checks that fail on purpose.* The tool-access check failed the first (socket-head-from-above)
    station: the socket frames' lips sit 15 mm over the heads. Moving to stud + nut in a wrench
    pocket open to the bed side passed. A clearance check on the tool, not just the part, is cheap
    and found a real serviceability defect.
  - *Quantities from geometry, prices from a pinned research file.* `make_bom.py` refuses to run if
    a selected price is not in `research/pricing_2026-10.json`; counts come from the manifest and
    the joint schedule, so BOM/RESULT count disagreements (a prior verifier FAIL) cannot recur.
  - *Parallel pricing subagent.* One background subagent (5 internal parallel agents) priced 23
    item groups in ~45 min while the CAD was built; 121 entries with URLs + verbatim evidence.
- **What failed / dead ends**
  - DeepSeek web_search had no API key; SearXNG `webx` worked (several engines unresponsive).
  - McMaster (login), MISUMI (client-rendered, office-hours price API), Mouser/Digi-Key (403),
    Bolt Depot/Fastenal/Zoro/MSC blocked scripted reads. Bisco Industries (Southco), jwwinco.com,
    boltsandnuts.com Shopify `search/suggest.json`, Ellsworth and Hinscha worked.
  - Exact-PN gaps remain: DD6139 seal (rep part), MISUMI pins/bushing, McMaster plunger, Aptiv
    13897598 housing, VHB 5952 — kept as NONE/EQUIV with the reason, never a guessed price.
  - An `Edit` after a background regen raced the file; re-read before every edit.
- **Tools:** build123d 0.11.1 (CAD, booleans, sections), numpy/scipy/PIL (drawing measurement),
  webx/SearXNG + curl, headless Chrome (SVG to PNG to read a section), one `subagent` (role mid).
- **Costs:** $0 spent, no purchases/quotes/accounts. Compute: one Opus session + one mid-tier
  subagent. The BOM rolls up to ~$2.3k purchased hardware, ~$0.5k fasteners/consumables (dated
  2026-10-02 list prices), ~$19k fabricated-part ROM (class 5, tooling excluded), with 6 unpriced lines.
- **Times:** ground + ledger/insights 10 min; port research 15 min; mount CAD + checks 35 min
  (including the tool-access redesign); BOM/pricing integration 20 min; drawings 10 min; port
  re-measurement 10 min; docs 10 min. Each full CAD regen ~3 min, full check suite ~10 min.
- **Reuse for the next product:** (1) find the OEM upfitter interface + its rating; (2) search
  for a purchased adapter before designing one; (3) metal stop sets gasket compression; (4) give
  the TOOL a clearance check; (5) slot float sized to the measurement uncertainty, with a named
  calibration item when it isn't; (6) price file + curated selection + generator that verifies it.
- **Needs Nate / later steps:** P-CAL-01 (measure a received adapter), P-CAL-02 (tape the four
  port centres), crash-tether decision if wanted, ordering (spend), Step 21 sign-off.
- **Attempt 2 resume (same task, attempt 2, 2026-10-02 ~09:16–09:50 UTC, ~35 min).** Attempt 1
  was aborted mid-run (its last pipeline run was racing a stale `NameError`). What worked: read
  the aborted session's tail, confirm no live writer, kill its orphan pipeline, re-run the whole
  regen from a clean state (assembly → drawings → BOM → checks, 13 m 50 s: 87 PASS / 0 FAIL /
  10 OPEN), fill the one placeholder left in `MOUNTING27.md` from the generated
  `out/mounting_analysis.json`, then `provenance.py` + `--check`. Lesson: a resumed attempt must
  treat the predecessor's uncommitted tree as unverified until one clean full regen passes.
- **Port-station evidence (attempt 2).** blender-loop run `r1t-step27-r10-mount`: S11 truck (31 s),
  S12 CAD import (49 s), S16 mount close-ups (Cycles CPU, 64 spp, 3 views, ~70 s on 24 threads;
  GPU held by another tenant). First S16 "failed" only because an assert named a score the script
  did not emit — assert on keys you actually report. Cameras aimed from the imported nut
  positions, so the views track the CAD. Stills read: cutaway shows nut/Nord-Lock/slot washer in
  the wrench pocket; the service view is dark (inside the shell) but legible.
- **Tools that failed in attempt 2:** DSH `web_search` (no DeepSeek key) and SearXNG `webx`
  (read timeout) — so the 6 unpriced BOM lines stayed unpriced rather than guessed.
