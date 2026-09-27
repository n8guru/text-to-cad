# Raw research log — Gen-1 R1T tailgate / bed controls (2026-09-27)

Method: SearXNG-backed scout + direct WebFetch of Rivian's own PDFs, which were downloaded and
text/image-extracted locally. **No X/Twitter search.** Source tiers: **A** = Rivian-published
primary, **B** = owner forum / aftermarket, **C** = could not determine.

## Primary documents

| Doc | URL |
|---|---|
| R1T Owner's Guide MY22–24, rev 2025-06-30 (the Gen-1 branch) | <https://assets.ctfassets.net/2md5qhoeajym/530xs9hu11xOKefT2JrvA5/9806f4c37762c217a108b1a07ea3c37f/r1t-my22-24-og-en-us-20250630.pdf> |
| R1T Owner's Guide, 2022-05-23 launch edition | <https://assets.rivian.com/2md5qhoeajym/530xs9hu11xOKefT2JrvA5/feb81551d04b8c9517dc722f5d4da00e/r1t-owners-guide-en-us-20220523.pdf> |
| R1T Upfitting Guide, 2025-09-24 | <https://assets.ctfassets.net/2md5qhoeajym/5ysf6K5UtGtHedY1fMeClC/3ab05048ce5c4f7e3195607919f3def3/r1t-upfitting-guide-en-us-20250924.pdf> |

The tailgate text is identical between the 2022 launch guide and the 2025 MY22–24 revision, so the
arrangement is stable across the whole Gen-1 production run. (A / high)

## Verbatim quotes used

**Owner's Guide p.283, "Use the Tailgate"** (A / high) — the exhaustive open list:
> Open the tailgate with one of the following:
> - Key fob
> - Button on the exterior bed rail
> - Center display
> - Rivian app
> - Entrapment button inside the truck bed

**Owner's Guide p.283** (A / high) — manual, gravity, electric release:
> The only way to close the tailgate is to manually close it.
> Since the tailgate uses gravity to open, it won't open if the car points downhill. In this case,
> you'll need to open the tailgate manually after you press the button.
> Press the tailgate button on the exterior bed rail to open the tailgate. The tailgate unlatches
> and slowly opens.

**Owner's Guide p.283 / p.284** (A / high) — two button variants:
> If you have a power tonneau cover, use this button.  [squared, two-icon]
> If you don't have a power tonneau cover, use this button.  [plain rounded blank]

**Owner's Guide p.284** (A / high) — entrapment button:
> The entrapment button in the truck bed glows in the dark for visibility. If the vehicle is
> parked and someone is trapped inside the truck bed, they can press the entrapment button to open
> the tailgate.
> The entrapment button won't release the tailgate if the vehicle is in Drive, Neutral, or Reverse.

**Owner's Guide p.16, "Truck Bed Exterior View"** (A / high for the item list; side assignment
derived from the diagram being a rear view, so vehicle-left appears image-left) — callouts:
1 Gear Tunnel release buttons (both rails, forward, rail top) · 2 Tonneau cover button (driver,
rear, rail top) · 3 **Tailgate release button** (driver, rear, rail top) · 4 Air compressor and
Gear Guard cable latches (driver, inner wall) · 5 Spare tire compartment lever (driver, floor) ·
6 Power outlets (passenger, inner wall).

**Upfitting / Owner's Guide pp.56–57, "Truck Bed Lights"** (A / high) — there is no bed-light
switch; the rail-top tailgate button doubles as the manual bed-light toggle:
> Automatic Options: Open the tailgate, or open or close the powered tonneau cover, if equipped.
> Manual Options: Choose Vehicle from the status bar on the center display, or press the tailgate
> button on the exterior bed rail while the tailgate is open and unlocked.

Auto-on 2 min timeout; manual-on 10 min; 30 s re-trigger window while locked.

**Upfitting Guide p.65, Truck Bed** (A / high):
> Do not cut, splice, or modify in any way the high-voltage wires and outlet in the truck bed.
> Relocation may be permitted if the wires and outlet itself are not modified.
> When upfitting equipment into the truck bed, do not block any of the required lighting, such as
> the CHMSL. If an upfit blocks required lighting, the upfitter is responsible for installing
> secondary lighting that meets relevant FMVSS 108 requirements.
> All exterior lights are DOT certified. Do not modify or relocate any lights.

**Upfitting Guide pp.100–102, 12 V auxiliary port** (A / high):
> Connect to the vehicle's harness using the Aptiv #13897598 mating connector with #12034047
> terminals.

Port designator **J019**, in the **Gear Tunnel**; **13.5 V** nominal / **14.1 V** in LVM;
**15 A continuous**, **20 A max**; wire **14 AWG PVC** or **16 AWG XLPE** minimum; ground at
**Module Zone Controller South** (LC 782246010); port service ref LC 781013010; available with the
vehicle off via **Camp Mode**. DANGER note: *"To prevent a circuit overload, it is recommended to
block off the 12 V port."*

**Upfitting Guide pp.29–30, dimensions** (A / high): bed length at rail tailgate up 1,381 mm
(1,377 mm with tonneau); bed length at floor tailgate down 2,130 mm; bed width 1,299 mm; **bed
height tonneau open 465 mm**; max cargo height tonneau closed 432 mm; max load on open tailgate
1,000 lb (453 kg). **p.59**: accessory ports along the top of the truck bed, **2,500 N / 551 lb
per port**. Gear Tunnel door static load 250 lb each; *"Do not modify the Gear Tunnel latches."*

**Key fob** (A / high): tailgate is fob button 2, **double press**.
**Centre display** (A / high): Access and Security → tailgate button.
**Rivian app** (A / high): tailgate button → Confirm.
**Voice** (A / high): "Alexa, open the tailgate."
**Driver door panel** (A / high, negative): exhaustive grep of the Gen-1 guide returns only window
switches, the key-card reader and the tyre/loading label. **No tailgate control.**

**12 V dead** (A / high, negative): the guide has "Manually Open the Hood" (p.391) and "Manually
Release the Charge Plug" (p.393) but **no manual tailgate release procedure anywhere**. The
jump-start section credits a 12 V jump with opening doors, frunk and charge-port door and does
**not** name the tailgate.

## Tier B (forum / aftermarket) — corroboration only, never designed against

* Rail button location + lock behaviour — *"The 'normal' tailgate release button on the top of the
  driver bed rail is disabled when the vehicle is locked"*; entrapment button is not disabled.
  <https://www.rivianforums.com/forum/threads/fyi-the-tailgate-can-be-opened-by-a-stranger-even-if-the-vehicle-is-locked.8031/>
* Two electronic latch actuators, one per side; gas-charged dampers; and an **unverified** claim of
  *"a separate manual release string for L & R"* behind the inner bed-wall plastic.
  <https://www.rivianforums.com/forum/threads/tailgate-wont-drop.57654/>
* No tailgate-mounted handle or button: <https://www.go-parts.com/garage/tailgate-lift-motor-rivian-r1t-2022-2025>
  — note this page is titled "tailgate lift motor" but its own body describes latch actuators and
  struts. **Do not order against that label; Gen 1 has no lift motor.**
* Bed lights have no switch: <https://www.rivianforums.com/forum/threads/turn-on-bed-lights-never-mind%E2%80%A6.8610/>
* Bed 120 V outlets: <https://www.rivianownersforum.com/threads/rivian-110v-power-outlets.741/>

## Tier C — could not determine (do NOT invent)

1. J019 **pin count and pinout** — Rivian gives connector + terminal PNs only.
2. Tailgate latch actuator PNs, connector, voltage/current.
3. Bed-light circuit PN / draw.
4. Whether the rail button is a discrete pigtail switch or part of a rail module assembly.
5. Whether the rail button is hard-wired discrete or LIN/CAN signalled.
6. Existence/location of the L/R manual latch release strings (Tier B, single thread).
7. Whether the bed has one or two entrapment buttons.
8. **Any dimensioned button position** — X from the bed rear face, Y from the rail edge, footprint,
   recess depth, actuation force/travel. Rivian publishes none. Tape required.
9. Bed-rail cap width / cross-section.
10. Rivian lock-state behaviour of the rail button from a Rivian source (Tier B only).

## Derived (arithmetic, not cited)

Bed-rail top face ≈ **465 mm above the bed floor**, from the cited "bed height, tonneau open =
18.3 in (465 mm)". That is a bed-height figure and may not be the exact rail-cap top plane the
button occupies — **medium** confidence, confirm by tape (gap T5).
