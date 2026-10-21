# Actual Android APK verification

Signed **0.4.5 / code 45 passed 69 assertions** through real adb tap, swipe and key input on an isolated read-only Pixel 8 / API 35 clone. This comprises the 55 existing regressions, 13 visible-sprite/source cases and one explicit context-capsule rejection assertion. [android-verification-summary.json](android-verification-summary.json) is the final audited result; [android-editor-verification.json](android-editor-verification.json) records all 69 assertions.

The normal **0.4.4 → 0.4.5** signed upgrade preserved primary and backup byte for byte before launch, then retained every saved field after rendered startup, including schema 3 and paused Layout page 1. A separate fresh review package started the original 16-object scene. All editing, service and lifecycle checks left both normal save files unchanged. No gameplay state was injected.

New touch checks selected the extruded chef hat, moved its ground root 6,10 → 6,11 → 6,10 without snapping the hat under the finger, selected the chef via its board and recipe image, and selected the conveyor through a carried plate. Opaque guest-over-stool and fixed-room pixels block editable selection. A plant placed by actual inventory drag ignores a transparent frame pixel, selects through a raised opaque leaf, moves to a clear tile while retaining its grab offset, and returns to stock without a refund. Source-point JSON records the atlas path, current frame, source pixel/RGBA, destination rectangle, screen point and root offset. These points were calculated offline from the production manifest/PNG registration and the real saved state, then used for actual Android input; no runtime backdoor was added.

The 55 retained regressions include held People → Home → rendered warm resume → orphan release, fresh press recovery, pause/RNG stability, stool rotation/movement/Return, invalid-drop shielding, both pagers, beige gutter shielding, profiles/focus/Back, collapsed drawers, force-stop/cold reopen and Live resumption. Cold reopens waited for rendered game pixels before input.

Two fixture calibrations are retained honestly:

- [android-touch-qa.log](android-touch-qa.log) preserves the successful prefix and the initial upward leaf-drag wait failure. Its endpoint entered the existing Rotate/Return capsule; the app correctly rejected it with unchanged state. [leaf-drag-coordinate-calibration.json](leaf-drag-coordinate-calibration.json) records the geometry. [android-touch-continuation.log](android-touch-continuation.log) proves that rejection, completes the clear downward move to 6,5 and finishes the remaining regressions with **68 passed assertions**.
- The first paused frame had no carried plate. A real Live → Edit continuation produced one. [android-carried-dish.log](android-carried-dish.log) preserves an overly strict camera-zero preparation wait after adb rounded the pan to `0.0123291015625` tiles. [carried-dish-camera-calibration.json](carried-dish-camera-calibration.json) records that valid actual camera. [android-carried-dish-continuation.log](android-carried-dish-continuation.log) uses it in the atlas transform and passes the plate-owner assertion, yielding the final **69**. Neither calibration required an app/source change.

Eight representative APK PNGs are retained from **58 raw captures** of the full run; all raw PNGs remain in `/private/tmp/sushi12-sprite-review`. Complete assertion/state JSON, source-point proofs, logs and the exact harness/continuations are retained here. Upload files, emulator startup noise, AVD userdata and credentials are excluded.

| Capture | Proof |
| --- | --- |
| [normal-v45-upgraded-rendered.png](normal-v45-upgraded-rendered.png) | Existing normal save after upgrade |
| [S01-chef-hat-selected.png](S01-chef-hat-selected.png) | Raised hat selects chef |
| [S02-chef-hat-moved.png](S02-chef-hat-moved.png) | Chef root moves one tile from a hat grab |
| [S08-guest-blocked.png](S08-guest-blocked.png) | Guest blocks the stool behind it |
| [S10-transparent-plant-gap.png](S10-transparent-plant-gap.png) | Transparent plant frame pixel selects nothing |
| [S11-plant-leaf-selected.png](S11-plant-leaf-selected.png) | Raised leaf selects its plant |
| [S12-plant-leaf-moved.png](S12-plant-leaf-moved.png) | Leaf grab retains the root offset |
| [D02-carried-dish-selected.png](D02-carried-dish-selected.png) | Carried plate selects its conveyor |

Both installed APK hashes match their [normal](../normal-build.json) and [review](../review-build.json) signed build receipts. Runtime commit: `c13ced782fefa6703dfa1814cb0ed679a5eeb799`; all 286 runtime files remained unchanged. Fingerprint: `1d41736c699fd1c93cf8b24285c64208fdd0bd6485179d6ac6782ee58cc88ac8`. Normal SHA256: `fb6c0cf5542fba46708b12ddf4d4bd4bb5f5cf1c494733dcd0657384af476cd7`; review SHA256: `1209e6c9c31460ca5bfe851635417f230604056934288ae9522c546b8cf271da`. Package names and signer remain unchanged.

[runtime-logcat.txt](runtime-logcat.txt) contains zero Godot script errors or Android crashes. Two cold-start cached-shader warnings recovered by recompilation and rendered readiness passed. [sandbox-verification.json](sandbox-verification.json) proves separate UIDs/private directories and intact normal saves. [avd-isolation.json](avd-isolation.json) proves the original config, userdata base/overlay and snapshot metadata retain their SHA256, size and mtime. The dedicated clone stopped and its process exited without saving a snapshot. Physical devices, other emulators and the existing user preview were not modified.
