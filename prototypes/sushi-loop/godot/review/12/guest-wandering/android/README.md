# Actual Android APK verification

Signed **0.4.6 / code 46 passed 69 assertions** on an isolated read-only Pixel 8 / API 35 clone: **55 existing regressions plus 14 focused wandering checks**. The final [summary](android-verification-summary.json), [complete assertion report](android-editor-verification.json) and [focused proof](guest-wandering-verification.json) record the result. All input used real adb taps, swipes and keys; no app-state injection or runtime backdoor was used.

The normal **0.4.5 → 0.4.6** upgrade kept both save files byte-identical before first launch. The [navigation migration comparison](normal-navigation-migration.json) allows only navigation version 1, neutral mode/origin/retry/cursor fields, missing wander tuning defaults and seated path/index cleanup. All legacy coins, objects, inventory, positions, meals, visits, service progress, clocks and RNG remained intact. The separate fresh review package started navigation version 1 with the original 16-object scene.

The actual fixture placed six spare conveyors across row 3 and closed its final gap with a plant at **4,3**. This empty-tile edit was accepted even though the exit route became unreachable; stock decreased by only the seven owned supplies and coins did not change. The complete seated dictionaries of `customer-1` and `customer-2` stayed unchanged during the Edit layout changes.

On Live, `customer-1` finished its meal and entered **leaving / wander** mode with the existing walk animation. Its root moved from `(2, 4.1062479)` to `(4.1687517, 4)` on free floor while its identity, seat assignment and meal/visit state stayed intact. Edit/Home/force-stop preserved the save, and cold reopen restored the entire paused payload, including fractional route bookkeeping, origin, retry clock and cursor. Live resumed that guest's wandering. Returning the plant restored its stock and the same guest automatically returned to **goal** navigation.

The [main touch log](android-touch-qa.log) passes all 55 regressions, including interrupted press cancellation, sprite-aware editing, invalid-drop shielding, paging, profile focus/Back, cold reopening and Live service. One focused fixture calibration is retained: the sixth long conveyor swipe landed at `6,4` instead of `6,3`, caught before route closure in [android-wander-qa.log](android-wander-qa.log). [The calibration record](wall-placement-coordinate-calibration.json) preserves the exact target and saved camera. The misplaced piece was Returned and replaced through normal card/world taps; [android-wander-continuation.log](android-wander-continuation.log) then passes all 14 focused checks without repeating the 55-check prefix or changing source.

Eight representative APK PNGs are retained from **54 raw captures**; the full raw set remains in `/private/tmp/sushi12-wander-review`. JSON states, assertions, exact harness and logs are retained here. Upload files, emulator startup noise, AVD userdata and credentials are excluded.

| Capture | Proof |
| --- | --- |
| [normal-v46-upgraded-rendered.png](normal-v46-upgraded-rendered.png) | Existing normal save after migration |
| [W01-route-closed.png](W01-route-closed.png) | Full row-3 barrier, plant gate and unchanged seated guests |
| [W02-guest-wandering.png](W02-guest-wandering.png) | Leaving guest walks below the blocked route |
| [W03-wander-moved.png](W03-wander-moved.png) | Same guest changes position while still wandering |
| [W05-wander-cold-reopened.png](W05-wander-cold-reopened.png) | Exact paused wandering save after force-stop/reopen |
| [W06-wander-resumed.png](W06-wander-resumed.png) | Live movement resumes after reopening |
| [W07-route-reopened.png](W07-route-reopened.png) | Plant Returned, gap and stock restored |
| [W08-goal-route-restored.png](W08-goal-route-restored.png) | Same guest returns to goal navigation |

Installed hashes match the [normal](../normal-build.json) and [review](../review-build.json) signed build receipts. Runtime commit: `588a8f880556ecabf7bf5008e43ad775ac2028f3`; all **286 runtime files** remained unchanged. Fingerprint: `445135add7bd66a61b5dc57f05af525083849fb0298fc3df90238606e3ea7c7c`. Normal APK SHA256: `b14fcd0f434e4a985bb3540d5e4c2fbc798ae11873ca2379d07c7c452c8edbfb`; review APK SHA256: `381c890e3e3ebc0f224c25d686409df87f6578eeb6e3147ebea2fec148882cf4`. Packages and pinned signer are unchanged.

[runtime-logcat.txt](runtime-logcat.txt) contains **zero Godot script errors or Android crashes**; three cold-start shader-cache warnings recovered by recompilation. [sandbox-verification.json](sandbox-verification.json) proves separate UIDs/private directories and untouched normal primary/backup. [avd-isolation.json](avd-isolation.json) proves all four original AVD files retain their SHA256, size and mtime; the clone stopped and its process exited without saving a snapshot. No physical device, other emulator or existing user preview was modified.
