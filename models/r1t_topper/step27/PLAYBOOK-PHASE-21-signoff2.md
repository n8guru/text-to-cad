## Phase 10: Nate-only design sign-off, second round (Step 21 re-open, mesh task 144775, 2026-10-10 ~11:00-11:40 UTC, ~40 min)

Producer of the card: claude-sonnet-5-5 headless mesh worker. Package under review: Step 29 pin
`79935a1933381268592c8a1b6d80b61b6b40ef37` (branch `agents/claude/task-139737-r1t-revision`), verified PASS
by task 139827. Card: Studio decision 2154445 (operator_visual, open, no agent answers for Nate).
Round 1 (card 2081357, Step 27 pin) ended Request-changes on 2026-10-06; Step 29 answered it.

- **What worked**
  - *Re-open by re-staging, not by new code.* Step 21 goes back to `done_unverified` + `operator_visual` with new
    `verification_images`, `evidence_ref` (pin + six-still manifest sha256) and `operator_visual_readiness`; the shared
    mint raises the card. The bound answered-card URL must be cleared (`operator_decision_url: null`) or the mint
    treats the step as already ruled.
  * *Dry-run the mint gate locally.* `studio.require_visual_readiness(...)` on the payload names the missing field
    in one call; the first live POST failed silently (no card, `raised_decisions: []`) because `ready`, `reviewer`
    and `purpose` were absent. Check `raised_decisions` in the POST response, not just `status: ok`.
  * *Pick stills by looking at them.* Of nine r29 renders one (`mount_service`) is near-black and was dropped;
    captions say 'stylised' for the blocky foot close-up rather than overselling it.
  * *Judge on the exact published bytes.* Publish first (`publish_operator_visual.py`), re-download the URLs, confirm
    sha256 equals the local file, then run `tools/qc_gate/run_gate.py` per still with a checklist written from the
    requested change (Nate's two points), not from the render.
- **What failed / dead ends**
  - First POST minted nothing (see above). `find / -name` for the playbook file timed out the 60 s sandbox: use
    `git ls-tree` on the pinned repo instead.
  - `tools/r1t-opus-pass/PLAYBOOK-NOTES.md` named in the step acceptance does not exist in forage or text-to-cad;
    phase notes live in `models/r1t_topper/step27/PLAYBOOK-PHASE-*.md`. Folding them into a skill is Step 28.
- **Tools:** forage-api (steps POST, decision GET), publish_operator_visual.py, tools/qc_gate/run_gate.py
  (qwen3.8-27b-uncensored on forge llama-swap), forage worktree python for the dry-run.
- **Costs:** $0; one Sonnet session; 6 judge calls x ~1-4 items on a local model.
- **Times:** ground 10 min, still review + publish 10 min, gate 5 min, first/second mint 10 min, notes 5 min.
- **Reuse:** (1) answer a Request-changes with a revision step whose acceptance quotes the operator's words, then
  re-open the sign-off with captions keyed to each of his points ('YOUR POINT 1'); (2) always state what the render
  is and is not (proxy truck, not photoreal); (3) list known-open checks on the card itself.
- **Needs Nate:** answer card 2154445 (Approve visual / Request changes). Approval does not release fabrication;
  Step 22 (real-truck calibration) follows.
