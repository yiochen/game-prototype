# Reopening an unfinished expedition — UI question 20

Built-in image-generation workflow. A reuses the existing, previously inspected `17a-centered-pause.png`; its accepted pause card already represents the proposed app-reopen state and is not regenerated. B edits the previously inspected `16a-hull-meter.png`. Both keep the restored journey frozen until Resume, followed by the accepted countdown. No new launch or recharge is implied.

## A — existing pause card

Reused image: `17a-centered-pause.png`. Original exact prompt: `17-pause-menu-prompts.md`, option A. No new generation for this option.

## B — frozen scene with Resume

```text
Use case: precise-object-edit.
Asset type: finished commercial portrait mobile-game UI screenshot.
Input image: supplied active-pursuit screenshot is the EDIT TARGET. Preserve exact portrait dimensions, polished 2D doodle ink style, navy/teal canyon and reefs, wreck, upward-facing yellow submarine, spotted eel, attached slack ivory cable, full-height mint following strip with no vertical ends, amber hatched attack strip and lightning icon, and all existing HUD. Keep submarine safely left of the amber band. Keep top-left submarine-icon hull badge with continuous coral meter, top-right salvage "72" and pause control, exact "SPOTTED EEL" name and cyan resistance bar.
Scene state: the player has just REOPENED the app during an unfinished expedition. All gameplay is restored at the same saved frame and FROZEN until they explicitly press Resume. There is no automatic travel, electricity discharge or resistance loss. Add a restrained light translucent navy scrim so this waiting state reads clearly while world geometry stays easy to inspect.
Primary request: show a minimal app-reopen UI instead of a pause card. Add a small cream label exactly "Paused" centered at approximately 49% screen height directly on the water, with a restrained dark ink outline and no background panel. Add ONE generous coral rounded button near 86% screen height, centered horizontally, about 68% screen width, with dark ink outline, slight shadow and large cream text exactly "Resume". It overlays the continuous water, without a footer or panel behind it. Keep the submarine clearly visible above the button and the eel well above the Paused label. The preexisting top-right pause icon remains visible for opening the full pause menu.
Constraints: only add the Paused label, Resume overlay and light waiting scrim. No countdown yet, centered card, Return early button, Start, back arrow, restaurant entrance, repair, upgrade, recipe preview, new charge meter, new resources, tutorial gestures, steering arrows, joystick, close X, phone frame or option label. No movement of scene objects or change to hull, salvage, creature resistance, following/attack geometry. Render a complete crisp polished commercial 2D mobile-game UI screenshot, not concept art.
```
