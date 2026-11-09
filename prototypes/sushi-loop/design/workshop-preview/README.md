# Workshop equipment · issue #28 prototype

## Revision 7 · copy, scene transition, interactables, unified tabs

User, 2026-11-08:
- **Copy.** Power-up cards say what the power-up does and which way the next level moves it ("▲ Lasts longer", "▲ Longer ride", "▲ Unlock"), with no numbers or internal units. Collector shows its reach relative to base (1.0× → 2.5×) instead of tiles.
- **Scene transition** (`transition.js`, one module for every scene switch). An iris closes onto what was tapped, navy with a cream rim like the harpoon strike's focus circle. It holds on a short loading beat (the salvage chunk bobbing over bubbles, at least 0.45 s) while the next scene is built, then reopens on the new scene's focus. Input is blocked throughout, and reduced motion fades through navy instead. It is used for hut → Workshop (reopens on the cradle), doorway or Back → restaurant (reopens on the hut) and submarine → dive (reopens on the ship).
- **Interactable signal in the restaurant.** The submarine and hut carry the approved #61 cyan `#19e3ff` outline with glow (the same SVG filter as the tip piles), so restaurant interactables share one look. The hut overlay is fitted to the capture (1.8 px error). The dive keeps lime for good pickups.
- **Unified tabs.** One tab control (`tabBar`) serves both the Workshop tray and the Edit inventory dock (new review state *Restaurant · Edit inventory tabs*). People, Layout and Floor are maple segments with the selected one in cream; Shop stays a separate walnut action button. This would replace the approved connected-tab wood dock (#12 wood-dock amendment) once approved.

## Revision 6 · power-up glyphs; no attraction ring

User, 2026-11-08: power-up cards use one-colour neon line glyphs on a dark tile, in the style of the user's skill-icon reference; the drawings are original. Each glyph takes its look tier's colour (white → violet → gold):
- **Shield duration**: a shield with a clock.
- **Passage**: a vortex ring under a ride chevron.
- **Shield at start**: a shield over launch chevrons, dimmed while the track is at "None".

The dive no longer draws the Collector's attraction range: a second circle beside the shield bubble was confusing. Attraction still works, and salvage drifts in when the ship is close enough.

## Revision 5 · Power-ups tab and the dive signal

User, 2026-11-08: the tray has two tabs, **Equipment | Power-ups**. Each holds three cards, so the tray keeps its height; a red dot marks the other tab when something there is affordable. Power-ups extend the spec's three Workshop tracks (#7) on purpose:
- **Shield**: duration 3.5 → 6.5 s.
- **Passage**: portal ride 28 → 46 rows, capped because the ride pays salvage.
- **Shield at start**: launch already shielded for 0 → 3.5 s.

Power-up looks are only a colour change of the effect: white (native) → violet → gold. The Shield track's colour also tints the launch shield. Shields still end before the creature encounter. Portal sense was considered and dropped.

**Dive signal.** Things the ship can use (shield pickup, passage entrance) share one signal: a soft lime halo, a steady keylined ring and a pulse. On the real cyan water, pure green turned teal and lost contrast; lime `#b4ff2e` with a dark keyline stays distinct. Red `#ff3b3b` is reserved for future harmful things. The comparison is in Shared components. Colours live in `balance.js` (`tierColors`, `signal`); drawing is in `powerups.js`, an SVG port of the approved #22 shield, bubble and whirlpool.

## Revision 4 · the harpoon is not on the ship

User, 2026-11-08: a launcher mounted on the hull looked too fierce. The ship is now only the hull and the paired collectors; the hull's nose plate reads as a small hatch the harpoon leaves from. The **Harpoon** track changes the fired harpoon instead (`harpoon.js`):
- Tier 1 is the approved native harpoon from `godot/scripts/expedition/harpoon_art.gd`, ported with the same geometry.
- Tier 2 (Lv 3) is longer, with a double barb, brass collar and red braided rope.
- Tier 3 (MAX) has a gold head with three barbs, a teal glowing collar, gold rope and a sparkle trail.

The dive fires it from the nose every few seconds. In the Workshop, tap the ship on its cradle to test-fire, and every Harpoon upgrade test-fires the new one. Harpoon cards and the gallery use the same drawing. The ImageGen launcher sheet is kept in `ship-parts/superseded/` as history.

## Revision 3 · ImageGen submarine parts

The submarine is no longer the Blender sprite (user, 2026-11-08: the game only ever shows one view). It is three ImageGen parts — **hull**, bow **harpoon launcher** and paired side **collectors** — and every part is fitted from the start. Each track has three looks (base, Lv 3, MAX; Collector MAX is Lv 4), and reaching a milestone swaps that part's whole sprite (e.g. starter → reinforced → deep-sea hull). Each part's tiers were generated together on one sheet so they match; the harpoon and collector sheets used the hull sheet as their reference.

`tools/prepare-ship-parts.py` slices the sheets, cleans keyed edges and measures anchors: hull nose plate and side stubs, harpoon base ring, collector bracket. `app.js` composes any tier mix in one shared frame, centred on the hull (the collision centre). The right collector is the left one mirrored. The dock and dive backdrops were recaptured without the 3D ship (`restaurant-dock-empty.png`, `dive-empty.png`), so the layered ship replaces it in the Workshop, on the dock, in the dive and on the card icons. Provenance: `ship-parts/generation.json`.

## Revision 2 · full-screen Workshop room

The Workshop is now its own room instead of a popup (user, 2026-11-08). Tapping the hut crossfades into an ImageGen workshop shed in the restaurant's rendered style: back wall with the red fish noren doorway, a blank sign carrying the live "Workshop" title, tool board, porthole, crates and rope. The submarine rests on a separate ImageGen cradle; the three upgrade cards sit in a maple bottom tray with the beige catalog. Leave through the **Sushi Bar** doorway (its tag is part of the target), Escape or Back.

**Any screen shape.** The room art is anchored to the top and cover-fitted (on screens wider than 0.62 it is capped and sits over a blurred copy of itself). The cradle and ship are not tied to room pixels: `layoutRoom` places them in the free floor between the wall and the tray, sized to fit. The tray never exceeds the space below the wall plus 120 px and scrolls on very short screens; cards compact below 760 px of height. The restaurant and dive captures also cover-fit. The review bar's **Screen** menu previews Fill window, 9:16, 9:19.5, 9:21, 2:3 and 3:4.

ImageGen provenance (prompts, references with hashes, raw outputs, rejected attempts) is in `room/` and `room/generation.json`. Runtime: `assets/workshop-room.webp`, `assets/workshop-cradle.png`.

## Revision 1 (popup) — superseded composition

HTML review of the Workshop before Godot integration. Open `/prototypes/sushi-loop/design/workshop-preview/`.

## What to try

- **Restaurant · dock**: tap the blue-roofed **Workshop hut** on the dock. Live service keeps running (the cash pill rises). Close with the round X, Escape or Back; focus returns to the hut and the camera does not move.
- **Workshop**: each Upgrade pays for exactly one level and stays on the page. The balance rolls down, the stat pops and the level pips advance. Reaching **Lv 3** fits that part on the slip with a NEW tag. After closing, the same part appears on the dock submarine; tap the submarine for the dive.
- **Not enough salvage**: every Upgrade is disabled, with no shortage message.
- **MAX**: the card keeps its final stat and shows a red ink MAX stamp, without a cost or arrow.
- **Dive**: the departing ship has the full upgraded hull (written on the native hull bar), the fitted parts, and a dashed ring for the Collector's attraction range. Salvage inside the ring is drawn to the ship; pickup value stays 2.
- **Shared components**: normal, pressed, disabled, NEW and MAX cards, and the five ship looks in idle (Workshop/dock) and travel (dive).

The side panel on wide windows lists the levels and the equivalent-run comparison: max hull and rock hits survived, eel reel-in time (resistance 100 ÷ (4.5/s × reeling strength)) and attraction range. Encounters do not scale to equipment.

## Composition decisions

- **Shell**: the approved maple popup and beige catalog (`wireframe/recipe-maple.css`) and the shared cream round X, like Shop (#18). The issue's paper return corner is replaced by the X for consistency with the approved Shop, which superseded the curl.
- **Salvage** uses the native expedition gold chunk (`godot/assets/expedition/kit/gold-00.png`), never cash. Cash and salvage never exchange.
- **Upgrade** is the Shop's wood price pill with an "Upgrade" caption; disabled reuses the Shop's disabled pill. **MAX** is a red ink stamp, the same ink family as Assigned/Fired.
- **Slip**: a darker maple inset with plank seams showing the submarine at its designed aspect ratio.
- **Level pips** mark the look level with a teal ring.

## Asset map

All art is existing production or native art; no new raster was generated. `tools/prepare-assets.py` derives everything in `assets/`; `assets/registration.json` records crops, fits and regions.

| Asset | Source | Notes |
| --- | --- | --- |
| `restaurant-dock.webp` | native capture, `tools/capture_workshop_backdrop.gd` (seed 19, dock revealed, camera x 4, HUD hidden) | 780×1688 logical frame; HTML draws the HUD |
| `dive.webp` | native capture, `tools/capture_dive_backdrop.gd` (seed 21, travelling) | native hull/salvage HUD retained |
| `ship-{idle,travel}-base.png` | `assets/production/sprites/submarine-yellow/{clip}-S.png` frame 0 | cropped to the union of base and parts |
| `ship-{clip}-{hull,harpoon,collector}.png` | regions where `upgraded-{clip}-S` differs from `{clip}-S` | one layer per track; same crop, so layers stack exactly |
| `part-*.png` | `sub-hull-panels`, `sub-harpoon-mount`, `sub-collector-inlet` `idle-S` | card icons at their own aspect ratio |
| `salvage.png`, `cash.png` | native UI | |

Ship placement in the captures was found by fitting the baseline frame (mean error 3.4 px restaurant, 5.5 px dive): restaurant scale 0.479 at (339, 759); dive 0.439 at (250, 996). The collision footprint is unchanged (0.3-tile circle); parts are visual only and sit inside the yellow silhouette, except the collector intake below the stern.

## Balance

Review values in `balance.js` (rules in `model.js`):

| Track | Stat | Levels | Costs | Look |
| --- | --- | --- | --- | --- |
| Hull | Maximum hull | 100 / 125 / 150 / 175 / 200 | 60 / 110 / 170 / 240 | Lv 3 armour plates |
| Harpoon | Reeling strength | 1.0× … 1.8× | 70 / 120 / 180 / 260 | Lv 3 launcher rail |
| Collector | Attraction range (tiles) | 0.6 / 0.9 / 1.2 / 1.5 | 50 / 95 / 150 | Lv 3 stern intake |

Each upgrade carries a one-time token; repeated taps, replays and reloads cannot pay twice. Tests: `node --test prototypes/sushi-loop/tests/workshop-preview.test.js`.

## For Godot (after approval)

Render per-track look combinations from the submarine Blender source (the prototype splits the combined `upgraded` clip instead), add the Workshop to `godot/content` as balance, and route the hut through the existing `dock_access` Workshop destination.
