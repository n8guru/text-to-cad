# Step 30 — bridge capture revision (decision 2154445)

Design study, 2026-10-12, task 147368 attempt 1. **No OEM fitment, strength,
preload, sealing, fabrication or purchase authorization.** This supersedes the
Step29 description of two isolated reference pins and flat slider teeth; all
other previously named OPEN engineering items remain open.

## What changed in the actual attachment

`cad/mounts.py` still supplies the four primary Port Latch Feet in the authoritative
assembly. The slider now has two open-sided **C-jaws**, each with a lower bearing
lip, an inboard web and an upper lip around one continuous reference bridge.
The existing paddle's provisional displacement law withdraws both jaws to free
the bridge. This is not an added padlock accessory or decorative hook. A literal
padlock is not proposed: Nate's inverted-padlock analogy describes capture around
the port bridge. The existing key lock/paddle envelopes remain present.

The foot body's entry channel is now continuous across the reference bridge;
leaving the old two disconnected pin slots would block installation. Its slider
pocket roof follows the new upper lips. The nominal material contact path remains
bridge -> jaw -> slider guide floor -> foot body -> rail screws/shims -> base rail.
That contact statement is geometric only, not a capacity calculation.

The bridge is drawn along the local rail axis for this provisional design. Neither
cited source establishes that axis, dimensions, recess mating profile or latch
internals on Nate's vehicle. The two jaw bearing positions 25 mm apart are retained
design assumptions, not a vendor dimension. The 8 mm bridge diameter, 35 mm bridge
length, 70 x 34 x 30 mm port envelope and 6.5 mm slider travel are **PROVISIONAL**.
Physical calibration can rotate/re-size/reposition this interface later.

## Sources actually inspected

Retrieved 2026-10-12; external imagery is cited, not redistributed in this repo.

* [Weistec accessory-port adapter](https://www.weistec.com/accessory_port_adapter_for_rivian.html):
  billet 6061, clear anodize, five-axis CNC; accessories attach using M10 bolts;
  four adapters for the R1T bed; no permanent port modification. Its
  [three-frame installation animation](https://www.weistec.com/mm5/graphics/00000001/2/access-adapter.gif)
  shows an oval port with a central bridge, inserts on either side and an upper
  bolted plate. This is an **alternative bolted capture adapter**, not proof of an
  OEM threaded stud or of our foot dimensions. Animation SHA256:
  `93adde9b3f4a104763a606b979082e8b9759024416f38895b91fd1e74b1bd495`.
* [TWRAPS crossbar wall mount](https://twraps.com/es/products/cargo-crossbars-wall-mount-for-rivian-r1t-r1s):
  states the same two-stage snap-on behavior; product pictures show a bridge/pin
  between two ears. The purchased object is an ABS **garage storage plate**, not
  vehicle mounting hardware. The pictured 8.85 x 3.15 inch plate dimensions and
  advertised storage loads are NOT used as port dimensions or topper ratings.
  Inspected feature-photo SHA256:
  `9db84e91227476e09ade3717fe9459c7023ef396da8f15a5faf195d14c29eca7`.
* [Rivian cargo crossbars](https://gearshop.rivian.com/products/cargo-crossbars):
  confirms one-handed snap-on installation and a lock that fastens crossbars to
  accessory ports. OEM crossbar capacities do not rate this custom topper.

The sources support the **capture topology and user interaction**, not replication
of proprietary internals. The existing cited Owner's Guide remains the source for
the two-click interaction. Our schematic two-stage motion is not an OEM mechanism
certification.

## Proof and reproducibility

Run in the existing build123d environment:

```
python models/r1t_topper/step27/cad/checks_step30_mount.py
python models/r1t_topper/step27/cad/export_step30_mount.py
```

The first command tests single valid solids, every sampled slider state against
body and bridge, containment inside the provisional recess, actual jaw lips above
and below the bridge, collision under a virtual 0.5 mm upward displacement while
caught/closed, and zero collision while the released foot is lifted 0..40 mm.
It also checks that all four real primary-foot assemblies contain this exact jaw,
not a separate illustration. The second command exports closed/caught/released
STEP/STL geometry and a section through a jaw bearing zone; source and mesh hashes
bind the detail views. The bridge is always reference-only.

## BOM/drawing delta

* Four `PLF_BODY_6061`: revised continuous bridge entry channel and taller slider
  pocket. Same proposed 6061-T6 CNC process and finish; revise DWG-27-012 accordingly.
* Four `PLF_HOOK_SLIDER_17_4PH`: C-jaw section replaces flat teeth. Same proposed
  17-4 PH H1025 / wire-EDM plus ground bearing surfaces; revise DWG-27-013.
* No new purchased hardware or vendor quote. Existing price estimates are not a
  quote for the revised machining. `SEC-30-001_bridge_capture.svg` and the dedicated
  STEP30 mount packet supersede earlier mount-section depictions for this revision.

**Remaining OPEN:** physical port orientation/dimensions and tolerances, paddle-to-
slider drive linkage, lock keeper/interlock, cam/preload/detent forces, pad-set
force, material allowables, fatigue/crash retention and real installation tests.
A collision-free kinematic law alone does not solve those items. No capacity from
an OEM port, OEM crossbar, or TWRAPS wall fixture transfers to this assembly.
