# Rivian crossbar / accessory-port attachment — research notes (2026-10-06, task 139737)

Nate's change request (card 2081357): "it appears you do not understand the rivian custom attach points that
the topper needs to connect to. the topper is meant to connect to the truck bed the same way that the rivian
crossbars attach. there is a clever hardware gizmo."

Sourced facts (all fetched 2026-10-06):
1. R1T Owner's Guide 2022-10-17, p.152-154 (https://assets.rivian.com/2md5qhoeajym/530xs9hu11xOKefT2JrvA5/76d493c33659e9ceac1d72175ec54f26/r1t-owners-guide-en-us-20221017.pdf):
   - Cargo crossbars set: 2 crossbars + 2 locking keys. Vehicle has accessory ports on the roof; trucks have
     additional accessory ports on the truck bed rails.
   - Each crossbar END is a clamp/foot with a hinged PADDLE. Install: "lift up the crossbar paddle while setting the
     crossbar into the accessory port. You should hear one click." Then "Center the crossbar in the accessory port,
     then push the paddle down until you hear a second click. You may need additional downward force to fully latch."
     "If you don't hear two clicks, the crossbar may not be latched."  => TWO-STAGE latch: stage 1 = foot seated/caught,
     stage 2 = paddle closed = clamped.
   - Lock: a key lock cylinder is on the foot UNDER the paddle (p.154 drawings); "Lock the crossbars with the key
     by turning clockwise. Push the crossbar paddle all the way down to cover the lock cylinder."
   - Remove: "Push up the crossbar paddle halfway to access the lock. Unlock with key. Lift the paddle while you raise
     the crossbar to disengage it from the accessory port."
   - "CROSSBAR LATCH TUNING: Over time, the crossbar latching mechanism may need adjustment." (a tunable latch)
   - Drawing p.153-154: the port is a rounded-rectangular recess in the rail-cap top; the foot is a pedestal with the
     paddle on its inboard/up face.
2. Rivian Upfitting Guide 2025-09-24 p.59 (local copy ~/forge-agent-os/tools/r1t-opus-pass/r1t-upfitting-guide-20250924.pdf):
   accessory ports: 2,500 N (250 kg) per port, "Do not modify the existing accessory ports unless approved by
   Rivian", "Use Rivian-approved cargo crossbars to attach to the accessory ports". Plan view shows each bed port
   location as a PAIR of orange marks (two anchor points per port).
3. trailrivian.com "Cross Bar Unboxing and Install on my R1T": "You need to have the latching 'tang' on the cross bar
   clamps open so they will fit over the CLEATS on the R1T bed rails ... When the cross bar clamps click down onto the
   bed rail cleat, you should hear two clicks and be able to fully close the latch on both sides. The latch handles
   can then be closed down over the locks." (https://trailrivian.com/threads/cross-bar-unboxing-and-install-on-my-r1t.846/)
4. Team 1EV crossbar storage mount (evsportline.com): "Patented 'dual-barrel' mounting link ... emulate the factory
   Rivian latch pin to ensure a proper and full 'click-in'" => the port/cleat presents a dual-barrel latch pin pair.
5. Mars Adventure Gear Accessory Port Adapter (Rivian) https://marsag.co/products/accessory-port-adapter-rivian
   $59/2: converts the port into TWO M8 threaded points, hole distance 25 mm, "slides into place".
6. Weistec 09-111-00078-7 (previous rev-10 choice): bolt-on M10 adapter, $100 ea, "R1T needs 4 for the bed".
   It converts the port to a bolt interface: it is NOT the crossbar mechanism Nate is describing.
7. Rivian Cargo Crossbars gear shop page: telescoping, 68-82 in spread, 28 lb, "snaps into accessory ports",
   "Compatible with a range of Yakima and Kuat mounts"; roof 250 lb dynamic per pair.
NOT PUBLISHED: the port's internal geometry (cleat/latch-pin dimensions, recess size, depth), the crossbar foot
drawing. These stay PROVISIONAL until measured off a real port / a purchased Rivian crossbar (calibration item).

---
## Added by the implementation pass (task 139737, 2026-10-06) - what else was fetched and what it was used for

8. Rivian Gear Shop, R1 Cargo Crossbars page, fetched 2026-10-06 (curl): https://gearshop.rivian.com/products/cargo-crossbars
   Bright $700 / Dark $800; "Telescoping fit for roof and bed rail"; "One-handed snap-on design"; "The included lock system
   securely fastens the crossbars to your accessory ports"; "Equipped with Rivian Adventure Key Set"; spread 68-82 in; 28 lb;
   height 4.25 in; capacity while driving 250 lb. => the REFERENCE ARTICLE for calibration item P-CAL-01b.
9. CompX National C8053 cam lock, Amazon listing fetched 2026-10-06 (browser): https://www.amazon.com/dp/B0FPPSF66D
   "CompX National Cam Lock w/ 2 Keys - Keyed Alike to C346A  C8053-C346A-14A", $13.77; 90 deg cam turn; key removable in both
   locked and unlocked positions; supplied with two keys, trim washer, spur washer, mounting nut, two cams; cylinder length family
   1-3/16 in. compx.com itself returned HTTP 403 to scripted access, so no manufacturer drawing was retrieved: the lock's body /
   flange / cam dimensions in hardware.json are ESTIMATED.
10. McMaster-Carr 85015A51 ball-nose spring plunger (detent): same part as the module-plug plunger, spec from hardware.json
    ball_plunger (Elesa GN 615 datasheet); McMaster pages need a login, so it stays unpriced.

## Researched vs verified (what this package may and may not claim)

| Fact | Researched (sourced above) | Physically verified |
|---|---|---|
| Crossbar end = foot with hinged paddle, two clicks, key lock under the paddle, latch tuning | Owner's Guide p.152-154 (text) | **No** - no crossbar handled or measured |
| Port = rounded recess + cleat / dual-barrel latch pin pair | trailrivian.com, Team 1EV (descriptions) | **No** - no port measured |
| Two anchor points per port, 25 mm apart | Upfit p.59 plan view (pairs of marks); Mars Adventure Gear (two M8, 25 mm) | **No** |
| 2,500 N per port; do not modify the port | Upfit p.59 | Rivian's stated value; not tested here |
| Port recess size, depth, pin diameter / position, hook geometry of the Rivian foot | **NOT PUBLISHED** | **No** - PROVISIONAL, calibration P-CAL-01b |
