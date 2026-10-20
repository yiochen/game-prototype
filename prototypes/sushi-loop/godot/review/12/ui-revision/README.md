# Issue 12 — approved B UI revision

The user selected the [indigo noren and warm ceramic composition](../../../../assets/ui/editor/v4/raw/b-indigo-ceramic.png), after authorizing a redesign beyond the original wireframe placements. This revision implements that UI in **Godot Android**. The generated concept's world arrangement remains illustrative; registered native sprites, projection and gameplay are retained.

## What changed

- A horizontal indigo People/Layout/Floor rail integrates the quieter cream Shop shortcut above one cream drawer. Three inventory items are visible per page, with neutral stock badges, readable native previews and square paging controls.
- One cream contextual capsule groups labeled Rotate and Return actions. Its separate pointer and all icons retain their proportions. Return stores owned furniture without deleting it or refunding coins.
- Vermilion Live is the primary action. A small Editing cue, sage selection footprint and navy corner brackets make editing readable without adding Save/Done/Undo steps.
- Inspection, recovery, item/profile mats, drawer and feedback surfaces share the same generated family. Focus colors remain legible on cream; every touch target is checked at native phone scale.
- A strict version-1-to-2 editor migration preserves the first visible inventory item's page as Layout grows from two to three slots. Other restaurant state, mode, stock, camera, selection and paused simulation are retained.

The native Shared editor gallery reuses the exact gameplay presentation. Shop remains the existing unavailable feature, and Floor remains the disabled current-floor swatch; their purchasing/painting tickets are not implemented here.

## Artwork and nine-patch calibration

[Two complete ImageGen source sheets](../../../../assets/ui/editor/v5/README.md) provide 17 surfaces and 16 icons. The packer preserves exact source crop pixels, four transparent sampling pixels, uniform fixed-corner scale and separately measured symmetric content margins. Source sheets, exact prompts, accepted composition/reference hashes, source rectangles, authoring input and packer hashes are retained. A strict independent PNG-pixel proof runs at staging and APK validation boundaries.

Nine-patch applies to plain resizable panel/control spans. The cloth rail is separate from the drawer, and the contextual pointer/icons are separate fixed-proportion sprites. No entire decorated button or icon is stretched into a different aspect ratio.

## Validation and actual captures

The final native matrix passes **138 UI checks each** at 320×720, 1440×1000 and 1280×720. It covers real viewport touches, invalid overlay drops, input exclusion, 44px targets, stock/save continuity, focused text contrast, and reaching the complete final floor row above the open drawer in a tall centered viewport. The phone suite also passes 117 editor, 94 session, 76 customer, 26 save-store, 12 scene, 39 skin and 1,501 approved-art checks. The calibrated skin includes actual rendered pixel tests, rather than only arithmetic assertions.

The Android packaging/provenance suite passes **38 checks**. Repository JavaScript engine tests and the production Vite build pass; no browser UI behavior changed in this native revision.

The [phone](phone/manifest.json), [wide](wide/manifest.json) and [landscape](landscape/manifest.json) sets each contain 24 actual native states. Original 0.4.0 evidence is retained in the parent directory. Logs are in [checks/](checks/).

- [Selected stool and attached actions](phone/03-selected-stool.png).
- [Three-item Layout drawer](phone/02-edit-layout.png), [quiet Shop feedback](phone/02b-editor-shop-unavailable.png), [next page](phone/13-inventory-next-page.png).
- [People](phone/14-people-profiles.png), [focused profile Close](phone/14b-profile-inspection.png), [collapsed drawer](phone/15-collapsed-tray.png), [disabled Floor](phone/16-floor-current-disabled.png).
- [Save recovery](phone/17b-pending-save-retry.png), [resumed Live](phone/18-live-resumed.png), [shared gallery](phone/19-shared-editor-normal.png).

Independent Standards and Spec reviews identified the centered-floor camera limit and focused Close contrast; both were corrected and are protected by native regressions. No other actionable findings remained in those reviews. Native Android installation/touch evidence and the signed 0.4.1 review APK are recorded separately after final export.

## Signed Android review build

[Install the B UI review APK](https://drive.google.com/file/d/1li7i0eEnouPfGZ9w_L_GTzfME_jGanGY/view?usp=drivesdk) — **0.4.1 / code 41**, package `com.yiochen.sushilooptickets.review12`. It uses the original release signer and a separate Android save sandbox. [Drive metadata readback](apk-drive-verification.json) matches the uploaded file's size and MD5; no sharing permissions changed.

The review APK is **226,640,808 bytes**, SHA-256 `de51b9bc8195ea03a94c5b100941812b9e7d4cefeb093200983dbe758e28de3f`. The normal save-compatible release is **226,636,712 bytes**, SHA-256 `1ca268271fcce80fd0565d0d9bc2d76c0fbf978602a843c97ff40479d4ff2b09`. Both are offline/nondebuggable and share all **284 runtime source files** from commit `7c64d6fc483a561c2f6a78dff7f7c85ae32dc949`. [The source/commit proof](checks/commit-runtime-verification.json) and [normal](checks/normal-build.json)/[review](checks/review-build.json) build receipts retain exact fingerprints. Verified exports ran sequentially: concurrent Godot Android exports collided in shared temporary APK files and were discarded.

[Actual Android validation](android/README.md) passes **49 assertions**: 38 main touch/platform checks and 11 independent lifecycle rechecks gated on a fully rendered game. The signed 0.4.0→0.4.1 normal update preserves both save files byte-for-byte before launch; paused Layout page 1 migrates to the three-slot page 0 with all other saved fields unchanged. Actual input verifies move/rotate/return/place, occupied/tray/rail rejection, stock conservation, paging, quiet Shop feedback, disabled Floor, profile focus and system Back, Home/force-stop/Back restoration and Live resume.

The review app receives no injected state and leaves the normal app's primary and backup saves untouched. Original AVD SHA256/size/mtime are unchanged, and the disposable read-only clone is stopped without saving snapshots. No app crash or Godot script error occurred. Five GLES shader-cache recompilation warnings across cold starts recovered; the final Edit/Live captures show a fully rendered game. The issue and PR remain open for user verification.
