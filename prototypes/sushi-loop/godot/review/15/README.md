# #15 native recipe picker and People photos

## Approved composition

The native picker implements the approved maple HTML review in `wireframe/recipe-maple.jsx` and its CSS. Catalog sections **5, 8 and 13**, the restaurant concept, the historical B composition and the current continuous wood dock were inspected. The maple amendment and the user's later popup/headshot refinements govern this iteration.

| Surface | Native implementation and states |
| --- | --- |
| Full-screen scrim | Blocks the complete viewport; outside touches do not close or reach the restaurant |
| Maple popup | Existing calibrated wood export, fixed corners, tiled plain spans |
| Header | Dynamic chef name/level, ImageGen chest crop ending at the separator and overflowing the top border, Close |
| Catalog | Independently scrolling two-column cream cards, bright inspected background, walnut current marker, NEW, muted ineligible food, five accessible patterned plates |
| Details | Full popup width with rounded top corners, independent plate/food layers, fixed price, actual chef time and level requirement |
| Action | Vermilion Prepare, disabled Prepare for unknown/ineligible/no selection, noninteractive Preparing for current recipe; at least 44 physical pixels |
| People | Three uniformly scaled ivory instant photos on the existing wood dock; shared generated headshots, native names and Placed/Ready text |
| World | Shared plated dishes on belts/blackboards, small board shake after Prepare; native character identity and projection retained |

The current native staff entry points are **tap a chef in Live** or **Edit → People → tap a photo**. Close and system Back return to the same camera/mode/tray context. Existing horizontal inventory browsing and upward placement remain on the original editor path. `recipe_picker.gd` is reused for the restaurant and shared-component captures.

## Production and saves

`recipe_book.gd` owns inspection, Prepare, eligibility and restaurant-wide discovered/NEW state. `recipe_catalog.json` owns tier thresholds, rim descriptions and content. Existing starter/save prices and preparation times remain authoritative: this release does not import the HTML fixture economy. Existing discovered recipes and chosen production are retained when adding metadata; legacy material-tier names map by rank. Chef level/cap/speed, assignments, unfinished preparation, held food, belt dishes, service clocks and RNG survive loading.

Inspection clears NEW without changing preparation or held food. Preparing another eligible recipe restarts unfinished preparation or immediately replaces an already completed held dish, and leaves dishes on the belt unchanged. Stored chefs use the same command path. An idle chef opens without inspection. New recipe discoveries do not change chosen production.

The starter still has its two discovered recipes. Higher recipes remain undiscovered until the later discovery feature supplies them; the review captures explicitly seed discovery/level fixtures in an isolated session to show all approved UI states. This slice does not implement hiring, level-up purchases or expeditions.

## Artwork and packaging

The runtime headshots and separate plate/food sheets are exact copies of the approved ImageGen originals. The new instant-photo original, exact prompt and reference/output hashes are in `assets/ui/people-photos/v1/`. `assets/ui/recipes/manifest.json` documents native calibration. Headshots, photo paper and dish layers retain their aspect ratios; dynamic text stays native.

The original wood atlas and its export manifest remain unchanged. `assets/ui/editor/html-export-v1/source/app.js` retains the exact original template source whose hash was recorded in that export. The native wood manifest explicitly binds this historical source snapshot, since the current HTML app now uses the new chef illustrations. The release gate checks the snapshot against the original recorded hash and checks every native wood PNG against its original export; it does not bless altered surface pixels.

## Review evidence

`native/phone/`, `native/narrow/` and `native/wide/` contain native Mobile/Metal renders at 390×844, 320×720 and 1280×720. Each contains People, current/inspected, NEW/eligible, unknown, ineligible, idle and the shared picker. Additional phone captures show the changed blackboard and a prepared/loaded cucumber dish. Captures use the isolated `SushiLoopRecipePreview15` save identity, with simulation disabled except for the explicit service captures.

Godot imports and the release APK export are the build checks for this delivery. No automated test suite was run. No Android device was connected; these Mac captures do not verify the Android Vulkan driver or device touch behavior. Final acceptance remains with the APK review.

## Android delivery

[Release APK 0.7.0 (code 61)](https://drive.google.com/file/d/1tIdF4mi23zv01cTTWXl8VXdVdTgO54aV/view?usp=drivesdk). Release signer, nondebuggable flag, package/save identity and Drive SHA-256/size readback are verified; see `release.json`. No sharing permissions were changed.
