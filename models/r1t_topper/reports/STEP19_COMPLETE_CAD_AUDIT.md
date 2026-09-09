# Step 19 complete-CAD audit

## Audit target and result

The audited canonical package is commit
`54ca2381477d7a64a2092365898bbefda39045d1`
(`agents/codex/task-86209-r2`).  This audit adds no CAD geometry and does not
revise the approved exterior direction.  Its result is a **complete digital CAD
package claim only**: the checked source, native artifacts, visual-review
artifacts, and reproducible contract gates together cover the project's
declared CAD scope.

The claim expressly excludes fabrication authorization, calibrated vehicle
fitment, sealing or waterproofing performance, electrical/legal compliance,
structural capacity or ratings, and any manufacture plan.  Those remain
late-calibration/proof work recorded in `OPEN_ITEMS.md`.

## Exact evidence

- Authoritative integrated CAD: Step 11 source commit
  `6e0229cecefee0043aed9ea607c5241c1fe7f815`; source STEP LFS SHA-256
  `c25c9df4213abdb1e87beb4aab052dc1725a4ee8433b6f242ca0dd6c5ade37ad`.
- Final visual derivative provenance is bound by
  `outputs/review/step15/manifest.json` to that Step 11 source and declares
  `PRESENTATION_ONLY_NOT_FITMENT_OR_FABRICATION_RELEASE`.
- The manifest binds its native visual STEP SHA-256
  `8fc059cfff217321f55606ff6605da78fe6934ce796721d3dabe9f31f4b3b265`,
  visual GLB SHA-256
  `58475b66ccbdbec0bdc7e21511443ce64de749fdf6f93aba9cad0bfab877febc`,
  dedicated interchangeability STEP SHA-256
  `633bf11e46bfaff092f18c70966b4fe7dae3781dcb3f89af41a5b3d602571cc9`,
  dedicated interchangeability GLB SHA-256
  `7fafca41c8de654e986d0156942b4225943931ba562dc1e720cd3246f9960773`,
  and all seven rendered-review view hashes.
- The visible review assembly is required to contain exactly: a continuous
  rounded carbon shell; two-side shared aperture interfaces; separate planar
  window inserts; a WINDOW/CAGE/TOOLBOX interchangeability proof; one
  single-leaf two-pane rear hatch; and topper-owned integrated crossbar ports.
  It prohibits `00_REFERENCE` and `CROSSBAR_REFERENCE` from that visible
  product story.

## Runnable verification

From `models/r1t_topper/cad`:

```bash
/home/n8/text-to-cad/.venv/bin/python step19_complete_cad_audit.py --full
```

The gate first verifies commit ancestry, provenance, authority boundaries,
artifact/view hashes, review subsystem equality, and the absence of the
disallowed reference/bar story.  With `--full`, it then reruns all
predecessor CAD contracts: checkpoint 1, phase 2, Steps 6--11, and Step 15
including its adversarial mutations.  It is intentionally a verification
warrant, not a release or manufacturing instruction.
