# Issue 12 — select the visible sprite

Signed Android **0.4.5 / code 45** implements the [sprite selection contract](contract.md). Tap the visible character, furniture or plant pixels, including raised parts above its ground tile. Transparent padding falls through in reverse painter order; opaque guests and fixed room props block hidden editable objects. A chef's board and recipe select the chef, while a carried dish selects its conveyor.

A selected-object drag retains the original pointer-to-ground-root offset, so grabbing a hat or leaf does not snap its feet to the pointer's tile. The first drag on an unselected object still pans; a short tap selects. Grid placement rules, protected native controls and the approved v8 curtain/beige UI remain unchanged. The running 450×800 native mobile preview was refreshed with its existing save unchanged.

- [Review APK 0.4.5](https://drive.google.com/file/d/1U14LE_SdRrZWBASCZo0eYce9wxw3WwgE/view?usp=drivesdk) — uploaded to the authorized My Drive root; size and MD5 match the local signed APK. Sharing was not changed.
- [Phone hat selection](native/320x720/02-hat-selected.png) and [ground-root drag preview](native/320x720/03-hat-drag-preview.png).
- [Native matrix](native/matrix.json): 41 sprite-picking and 234 native app checks pass at both 320×720 and 1280×720; 185 editor, 94 session and 26 save checks pass. Eight rendered captures are retained.
- [Packaging validation](packaging-validation.json): 64 checks pass. [Normal](normal-build.json) and [isolated review](review-build.json) build receipts pin the same 286 runtime files, signer and source fingerprint.
- [Actual Android evidence](android/README.md): 69 assertions against the actual APK pass, including raised hat/leaf selection and movement, transparent padding, composite ownership, guest/fixed blockers, protected overlay rejection, upgrade44→45 preservation, lifecycle, paging and normal/review save isolation. No script errors or runtime crashes; the disposable emulator was stopped and the tracked original AVD files were unchanged. Raw coordinate calibration attempts are retained and explained in the Android report.

Runtime source: `c13ced782fefa6703dfa1814cb0ed679a5eeb799`. APK SHA-256: `1209e6c9c31460ca5bfe851635417f230604056934288ae9522c546b8cf271da`. Full upload verification is in [drive-upload.json](drive-upload.json).

Issue #12 and PR #36 remain open for user verification. The [0.4.4 curtain restoration](../curtain-restoration/README.md) remains unchanged history; no later ticket is included.
