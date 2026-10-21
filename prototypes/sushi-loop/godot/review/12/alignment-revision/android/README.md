# Actual Android APK verification

Version0.4.3/code43 passed53 assertions through real adb touch/swipe/key inputs on an isolated read-only Pixel8/API35 AVD clone. No gameplay state was injected. The normal0.4.2→0.4.3 upgrade preserved every saved field and both files byte for byte before launch; the separate fresh review package did not modify the normal package's save.

The run verifies pointer-down feedback, held/cancelled curtains across Home and warm resume, orphan release, context actions, inventory drag, invalid drop shielding, both bare pagers on the narrow final page, profiles/focus/Back, disabled floor, camera pan, exact pause preservation, force-stop/cold reopen and Live service continuation. The installed APK hashes match the signed build receipts. See `android-editor-verification.json`, `android-verification-summary.json`, `sandbox-verification.json`, screenshots and `runtime-logcat.txt`.

`avd-isolation.json` proves the original user's AVD config, userdata and snapshot metadata are unchanged by size, mtime and SHA256. The clone was stopped without saving a snapshot. No physical device was used and no AVD userdata or credentials are included here. The existing desktop mobile preview was preserved separately.
