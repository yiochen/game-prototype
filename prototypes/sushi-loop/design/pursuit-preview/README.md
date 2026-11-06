# Pursuit, catch & recipe award · issue #24 review

Interactive HTML prototype for approval before Godot work, per the game-ui-prototype workflow. Open `index.html` through the Vite site (`/prototypes/sushi-loop/design/pursuit-preview/`).

## Flow

1. **Chase.** The Storm Eel is already hooked (the #23 handoff). Ship and eel speed up to 1.4× travel speed through ordinary route terrain. The cable stretches freely from the ship's nose to the pinned harpoon, drawn over the world. There is no following strip and no range limit. The steering arrows work as usual. Pale streaks rush past the sides to sell the speed. The Harpoon button stays hidden (one harpoon only).
2. **Resistance is the eel's health.** The wide pill under the HUD row drains steadily and never refills. Below 25% it turns amber and the eel switches to its `struggle` clip.
3. **Hits.** Hits cost hull only, with the #23 round collision, knock-back, wobble, red tint and sparks. Zero hull snaps the cable. The eel escapes ("It got away · Hull depleted"), then the Hull depleted results show, with no recipe and no second try.
4. **Catch.** At zero resistance the catch and the first recipe are committed first. Hazards end, the chase eases to a stop, and a short automatic cutscene plays with no Skip:
   - the exhausted eel is drawn into the upper middle and grows;
   - the harpoon pulls free with a small spark and reels back along the slackening rope into the ship's nose, then is stowed;
   - warm rays turn behind it and the scene dims;
   - bubbles burst, and "Caught! · Storm Eel · first catch" appears as plain outlined text, like "Hooked!".
5. **Recipe award.** The cutscene opens it automatically. It is a maple card titled "New recipe!":
   - an ImageGen underwater stage with a lit sandy spotlight;
   - the #15 Red plate and Eel roll layered separately on top;
   - the name, "From the Storm Eel", and two fact chips: price 48 and base prep 7.5 s;
   - one Continue.

   The plate colour and dashed rim carry the tier. The accessible label names the Red plate and level 5. There is no Chef requirement row.
6. **Results.** The existing native receipt. The ship finishes the route automatically after the catch, so the completion bonus applies. There is no recipe recap.
7. **Restaurant.** The results' Restaurant action returns straight to the restaurant, with no extra screen. Eel roll appears NEW in every chef's picker until inspected; this is the existing #15 picker state, linked from the review panel. Discovery never switches what a chef is preparing.

A repeat catch (review toggle) goes from the cutscene straight to the results.

## Versus HUD revision (2026-11-05)

On short 16:9 screens the eel's head sat under the second HUD row. The user proposed removing the gold count and merging the hull bar, and chose the mirrored "versus" layout used by fighting-game health bars and fishing fights.

- From the encounter onward, the top row holds the hull bar on the left (submarine icon) and the eel's resistance on the right (eel icon, draining toward the middle). Pause stays at the right end.
- The gold count hides during the encounter. Gold picked up during the chase still counts, and the results show it.
- The second row is gone, so the eel's head stays clear on 405×720.
- **Arrival transition** (when the creature arrives; here, 0.6 s after Restart or **Replay HUD transition**):
  - the gold count lifts and fades (250 ms);
  - the empty eel bar slides in from the right into its slot with a small overshoot (380 ms, 180 ms delay);
  - its fill sweeps from empty to full (600 ms), like a boss bar.

  Reduced motion uses plain fades.
- Review controls: **16:9 phone 405×720**, and **Previous HUD (compare)** for a side-by-side.

## Asset map

| Surface | Source |
|---|---|
| Terrain, seabed, gold, submarine | Approved production sprites and route chunks (#21/#22) |
| Storm Eel | Approved live 3D GLB (#23): `hooked`, `struggle`, `exhausted` and `escape` clips |
| Cable, pinned harpoon | #23 code-drawn rope and harpoon |
| HUD pills, pause, arrows | #22/#23 family; the resistance pill reuses the coin-panel nine-slice |
| Cutscene rays, dim, sparkles | CSS/canvas, no baked art |
| Award and results cards | Maple wood grain, ink, rim and vermilion primary of the native PopupSkin family |
| Award backdrop | **New ImageGen** `award-art/v1/backdrop.jpg`, 3:2 and never stretched. Original, prompt, reference hash and provenance in `award-art/v1/` |
| Plate and dish | `design/recipe-picker-preview/raw/plates.png` cell 2 (Red) and `food.png` cell 0 (Eel roll), separate layers at the calibrated food inset |
| Coin | `godot/assets/ui/coin.svg` |

Balance for this review is in `balance.json`. It joins `godot/content/expedition.json` → `encounter` on approval.

## Checks

Captured headlessly at 390×844, 320×720 and the wider portrait-contained window, with no console errors. The captures cover the chase, steering, cutscene, award, results, the restaurant note, the hull-depleted escape and the Screens tab.
