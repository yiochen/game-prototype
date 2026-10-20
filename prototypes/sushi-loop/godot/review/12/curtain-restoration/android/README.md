# Actual Android APK verification

Version **0.4.4 / code 44 passed all 55 assertions** through actual adb touch, swipe and key input on an isolated read-only Pixel 8 / API 35 clone. The runtime commit is `5190d3034d3f8a1818fd8203178e799ac75caa84`. The complete run finished successfully in [android-touch-qa.log](android-touch-qa.log); [android-editor-verification.json](android-editor-verification.json) records every assertion and [android-verification-summary.json](android-verification-summary.json) records the final identity and audit result.

The signed normal **0.4.3 → 0.4.4** upgrade preserved primary and backup byte for byte before launch, then retained every saved field after rendered startup, including schema 3, paused Edit, camera, inventory and remembered Layout page 1. The fresh review package was installed separately without injected state. Its complete touch and lifecycle run left both normal saves unchanged.

The suite covers pointer-down feedback, held People → Home → rendered same-process resume, cancelled orphan release and working fresh press; rotation, object/inventory drag and invalid-drop rejection; both bare pagers and the narrowed final drawer; beige gutter tap and swipe shielding; People inspection, keyboard focus and Back; collapsed drawers and disabled Floor; paused Home, force-stop and Back reopening; and Live simulation resumption. Cold reopens waited for two rendered game frames before input or captures.

| Exact installed artifact | Package | SHA256 |
| --- | --- | --- |
| [Normal build receipt](../normal-build.json) | `com.yiochen.sushilooptickets` | `f2519c3e25f43e0a1016765a97ebe777c7b08d918cd0e0bdc99507904fc11772` |
| [Review build receipt](../review-build.json) | `com.yiochen.sushilooptickets.review12` | `b059c76d92c0baa0059936d486653d113b2d7a7dbe82cc94013021d594b262bc` |

Both retain signer `9b465ce9e19fc9cfb1a3a34c6fa2e1e452d3bfc9cb6adb5c01918c1fcfc061ed`. All 286 runtime files match the build receipts after QA; fingerprint `47c283518d1acda892838eb263ce9c757ab8062f55dea90b072c74c5193db5a1`.

Eight representative PNGs are retained here from **43 captures produced by the full 55-assertion run**. All raw PNGs remain in `/private/tmp/sushi12-curtain-review`; complete JSON states, assertions, logs and the exact harness are retained here.

| Representative capture | Purpose |
| --- | --- |
| [normal-v44-upgraded-rendered.png](normal-v44-upgraded-rendered.png) | Existing normal save after upgrade |
| [01-edit-paused.png](01-edit-paused.png) | Restored looped curtains, full-width rod, beige backing, four Layout goods |
| [01d-people-background-resumed-before-release.png](01d-people-background-resumed-before-release.png) | Cancelled held press after rendered resume, before original release |
| [08-inventory-next-page.png](08-inventory-next-page.png) | Narrow final drawer and external carets |
| [08c-beige-gutter-tap-blocked.png](08c-beige-gutter-tap-blocked.png) | Beige gutter preserves selection and camera |
| [09a-staff-details-popup.png](09a-staff-details-popup.png) | Staff inspection and native Close focus |
| [10-people-tray-collapsed.png](10-people-tray-collapsed.png) | Restored rail and backing with drawer collapsed |
| [17-live-resumed.png](17-live-resumed.png) | Preserved service resumes in Live |

Visual inspection confirmed the original looped curtain shapes, visible wood rod reaching both portrait edges, continuous beige backing behind the rail/drawer/footer, and the retained v43 control geometry. [runtime-logcat.txt](runtime-logcat.txt) contains **zero Godot script errors or Android runtime crashes**. Two cold reopens emitted `Failed to load cached shader, recompiling.` warnings; rendering recovered and both readiness/lifecycle checks passed.

[sandbox-verification.json](sandbox-verification.json) proves separate app UIDs/private directories and untouched normal primary/backup. [avd-isolation.json](avd-isolation.json) proves the original AVD config, userdata base/overlay and snapshot metadata retain their SHA256, size and mtime. The dedicated clone stopped and its process exited without saving a snapshot. No physical device, other emulator or existing desktop preview was modified. No AVD userdata or credentials are included in this evidence.
