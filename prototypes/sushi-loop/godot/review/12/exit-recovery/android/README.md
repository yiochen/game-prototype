# Actual Android exit-recovery verification

Signed **0.4.8 / code 48 passed 27 focused actual Android assertions** on an isolated read-only Pixel 8 / API 35 clone: **5 normal upgrade, 5 legacy47 fixture and 17 exit-recovery checks**. The [summary](android-verification-summary.json), [complete report](android-editor-verification.json), [legacy fixture](legacy47-fixture.json) and [focused behavior proof](exit-recovery-verification.json) record the result. All gameplay changes used real adb taps, swipes and keys; no save-state injection or runtime backdoor was used. The previously passing [0.4.7 Android regression suite](../../entrance-wait/android/README.md), including its 55 editor controls/lifecycle cases, is linked as history and was not repeated for this behavior correction.

The normal **0.4.7 → 0.4.8** installation kept both save files **byte-identical before first launch**. Its [post-launch parsed payload](normal-no-schema-upgrade.json) was **exactly equal**, including every schema marker, guest, object, inventory, route, clock, RNG and simulation elapsed; no numeric differences were observed and no fields were added or removed.

The separate real review47 APK reproduced the bug. Six owned conveyors filled row 3 columns 0–5, leaving a right-side gap at 6,3. An already seated guest remained below. A new assigned walker, `customer-2`, was paused in the upper corridor; the plant gate closed the gap through actual inventory-card/world taps, blocking its assigned `seat-3` below while leaving the entrance at 3,2 reachable above. The old app entered **walking / wander** with visible scared idle feedback. At save time the guest was at `(2,0)`, with scared clock 2.05 seconds. The wall consumed only owned stock, with no coin or paused seated-state change.

Both review save files also remained **byte-identical before first48 launch**. The initial Python strict post-launch comparison stopped on two known JSON number parsing roundtrips, retained honestly in [the original raw log](android-exit-recovery-qa.log) and [exact-difference receipt](review-upgrade-exact-differences.json):

| Exact field | Before → after | Difference |
| --- | --- | --- |
| `remainder` | `0.027066666666666475` → `0.02706666666666647` | `3.469446951953614e-18` |
| `state.customers[1].appetite_target` (`customer-2`) | `1.6605734825134277` → `1.6605734825134275` | `2.220446049250313e-16` |

[The successful continuation](android-exit-recovery-continuation.log) permits **one ULP only at those two enumerated fields**, without a broad numeric state tolerance. [The upgrade receipt](review-no-schema-upgrade.json) proves every other value and key is exact: navigation, phase, pose, position, visit, schema, simulation elapsed and RNG. The paused48 payload stayed byte-stable afterward. No installation or successful prefix was repeated, and no source or application data was modified to continue. This numeric comparison calibration is separate from the passing behavior assertions and pre-launch save-byte preservation.

On Live, the old walker changed to **leaving / goal**, reason **`seat_unreachable`**, cleared its scared and retry clocks, retained the walk pose and original guest/meal/seat history, and reached the available entrance. The first changed saved frame was at simulation 8.9, on the direct path `(3,0) → (3,1) → (3,2)`; subsequent proof confirms departure. Paused48 restore and idle Edit applied no fallback before Live.

The older lower-room `customer-1` completed its meal and retained reason **`satisfied`** while its exit was genuinely blocked. It continued moving on free floor in leaving/wander with scared feedback and the original visit. Returning the real plant gate restored stock and access without changing paused coins or visit state; that same guest resumed its original goal departure, cleared scared feedback and exited. A later reachable-seat walker, **`customer-11`**, prioritized **`seat-2`** despite an available entrance and reached that seat without rerolling its visit or taking the new fallback.

Eight representative APK PNGs are retained from **16 raw captures**. The complete raw set remains at `/private/tmp/sushi12-exit-recovery`; all selected JSON states, reports, exact executed helpers and raw/continuation logs are retained here. [The manifest](evidence-manifest.json) hashes each retained evidence file. No upload files, emulator startup noise, AVD userdata or credentials are included.

| Capture | Proof |
| --- | --- |
| [normal-v48-upgraded-rendered.png](normal-v48-upgraded-rendered.png) | Existing normal save after exact no-schema upgrade |
| [R03-legacy47-walking-wander-paused.png](R03-legacy47-walking-wander-paused.png) | Real47 blocked-seat bug with reachable entrance and scared bubble |
| [R04-legacy48-restored-paused.png](R04-legacy48-restored-paused.png) | Same legacy guest restored paused in48 before fallback |
| [R05-seat-unreachable-direct-exit.png](R05-seat-unreachable-direct-exit.png) | Direct entrance route, walking pose and cleared scared feedback |
| [R07-true-trap-still-wanders.png](R07-true-trap-still-wanders.png) | Satisfied guest genuinely trapped below the wall keeps scared wandering |
| [R09-trapped-exit-route-restored.png](R09-trapped-exit-route-restored.png) | Gate returned, original leaving guest follows the exit without scared feedback |
| [R10-reachable-seat-first.png](R10-reachable-seat-first.png) | New walker follows its reachable assigned seat |
| [R11-seat-first-arrived.png](R11-seat-first-arrived.png) | Same walker reaches seat-2 and starts its meal |

Runtime commit: `13b769a3f43651655a7d1c6e7d77bf63637c3fcf`; all **292 runtime files** remained unchanged. Fingerprint: `513f315cc7cc631dc7fea1a9fc74e54b7a3494290b694cde1dfe2a95cab1698f`. Normal APK SHA256: `f0ab7ad93bf22ed5ba24bab35b8549560182c426d5965719627eafe8dc8b2917`; review APK SHA256: `ad4e155b8b8c54052b47491f35b1b631271ce401a4c03250a54e8892007a9798`. Package names, `SushiLoopTickets` save identity and pinned signer are unchanged; navigation/admission versions remain 1.

[runtime-logcat.txt](runtime-logcat.txt) contains **zero app script errors or Android crashes**; one cached-shader warning recovered by recompilation. [Sandbox verification](sandbox-verification.json) proves separate UIDs/private directories and untouched normal primary/backup. [Historical helper audit](historical-helper-isolation.json) proves all eleven v47 helpers remain unchanged. [AVD isolation](avd-isolation.json) proves all four original AVD files retain SHA256, size and mtime; the clone stopped and its process exited without saving a snapshot. No physical device, other emulator or existing user preview was modified.
