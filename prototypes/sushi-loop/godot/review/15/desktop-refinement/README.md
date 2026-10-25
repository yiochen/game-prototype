# Desktop review refinements

These changes follow the delivered 0.7.2 / code 63 APK and are available in the desktop preview. That APK does not contain this follow-up yet.

- The recipe catalog has 24 logical units of top padding inside its scroll content; the padding scrolls away. Its scrollbar is hidden, while scrolling, focus following and rounded clipping remain available.
- Details extend to the popup's bottom edge. Carved waves sit inside the single outer border.
- People photos have no pressed/focus rectangle. Keyboard focus uses the caption's red ink color. Category buttons and Shop share the connected tab's visible top edge, and all category labels align.
- A dish taken from a belt flies to its guest along a 340 ms arc, easing into the held size/position. The guest's baked held food is hidden until landing, avoiding a duplicate plate. The simulation still owns the meal immediately; timing, payment, fullness and saves are unchanged.
- Flights use the take event's exact source belt position and simulation timestamp. Old events from a large advance, removed/repositioned meals and reduced motion produce no lingering transfer. Flights are temporary presentation data and are not replayed after restore.
- The two native eating clips use frame-specific projected food positions from retained production capture proofs. `tools/export_meal_attachments.py` exports those measurements and source hashes to `content/meal_attachments.json`. Higher recipes land at their existing composed hand socket.

## Render review

Godot 4.7.2 import passed. Native Mobile/Metal captures were inspected at 390×844 and 1280×720, plus the 450×800 dish transfer sequence. Render captures use an isolated preview identity and do not modify the player's save. No automated test suite or new APK export was run for this desktop iteration.

- [Recipe top padding and single footer](phone/02-current-recipe.png)
- [Scrolled catalog with hidden scrollbar](phone/02a-scrolled-no-scrollbar.png)
- [People photos and aligned tabs](phone/01-people-instant-photos.png)
- [Transfer source](flight/01-source.png) · [In flight](flight/02-midpoint.png) · [Landing](flight/03-landing.png) · [Held pose](flight/04-held.png)

The desktop preview retains the existing `SushiLoopRecipePreview15` save identity. The original Android package/save identity is unchanged. Concurrent doorway work in the shared workspace is excluded from these review captures and this commit.
