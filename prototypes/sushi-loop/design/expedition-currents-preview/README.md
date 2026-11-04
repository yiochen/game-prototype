# Issue #22 review · currents, shields and the bonus passage

Interactive HTML prototype for approval before the Godot implementation. It runs the issue #21 expedition (same route module, chunks, pieces and HUD) with the #22 features added.

## Behaviour on review

| Feature | Rule (balance in `balance.json`) |
|---|---|
| Lateral current | Field cells push the ship 1.4 columns/s sideways, added to steering (3.3 columns/s). Releasing the arrows eases the player's part to zero; the push continues. Bubbles drift with it. |
| Shield (the ticket's “boost”) | Shield-emblem pickup. ×1.8 forward speed for 3.5 s and no collision damage (rocks bump the shield). No pickup-value multiplier. Ends at the encounter edge (the finish chunk stands in for the creature encounter). |
| Portal | Optional sunken stone ring off the main line. Steering onto it spends it and enters a separate passage. The strong current carries the ship along a gold ribbon with no damage, and it rejoins the main route at the entry of the chunk after next. |
| Passage steering | Open design choice: **Automatic ride** (arrows dimmed, "The current carries you") or **Steerable** (arrows work, walls are soft, still no damage). Pick one in the review panel. |
| Save / pause | Run state includes `boost`, `boosts_taken`, `portals_used` and `passage {portal, y, x, collected}`. Entering a portal commits it before the ride, so reopening never repeats it or its gold. A save mid-transition lands on its far side. |

Rules, balance keys and chunk data keep the ticket's `boost` name; only presentation says Shield.

## Content

- Feature chunks: `godot/content/expedition/chunks/{current-crossing,current-crossing-mirror,portal-basin,boost-run}.json` (kinds `current`, `portal`, `boost`), authored by `author-chunks.mjs` in the map-designer format with two extra layers, `currents` (`current-east` / `current-west` per cell) and `features` (`boost`, `portal-ring`). `route.js` ignores those layers, so the chunks validate and join like any other.
- Plan: feature slots `current`, `portal` and `boost` join the run plan (`balance.json → plan`). Those kinds are offered only by their own slots.
- The bonus passage is generated from the run seed and portal: a winding three-wide channel with gold every other row, dressed by the same `composeScene`.

## Asset map

| Element | Source |
|---|---|
| Portal ring | Blender: `assets/expedition/v3/portal.py` (v2 ruin kit, decor-ruin-fragment round-03 materials, light rig and 35° registered camera); published by `v3/publish.mjs` at the atlas scale. Centre left open. |
| Whirlpool (portal, passage ends, outflow) | Code-drawn: dark core with three turning spiral arms, drawn under the ring. A used portal shows a still, dim pool. |
| Current field | Code-drawn: blurred pale seabed wash plus tapered flow lines moving at the real current speed, some with chevron heads. |
| Passage current | Code-drawn forward flow lines and speed lines; seabed tinted deeper with a stronger vignette. |
| Shield pickup / active shield | Code-drawn shield emblem (navy rim, blue face, white inner rim, sheen) with a cool halo and pulsing ring; the shielded hull wears a shield bubble whose bright rim drains with the time left. |
| Arrows | Same rounded translucent triangles as the native view; pressed brightens, passage ride dims. |
| HUD | Existing family: coin-panel pills (cropped from `assets/ui/editor/skin.png`, nine-slice 64 px source / 22.2 px at 390 wide), round cream Pause. |
