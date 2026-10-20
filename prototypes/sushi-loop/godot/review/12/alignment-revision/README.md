# Issue 12 — alignment and spacing refinement

The [latest B amendment](contract.md) records the requested rail backing removal, bare paging carets, tighter goods cards, bottom padding, thicker dock/rod and measured icon/text alignment. The 100-unit minimum height for rounded controls remains in force.

This revision is in progress. Native captures and the signed 0.4.3 / code 43 Android review APK will be recorded here after verification. The [0.4.2 review and APK](../noren-revision/README.md) remain unchanged historical evidence.

The v7 source registration uses manifest/provenance schema 4. Reused source sheets and the full-screen composition inherit their exact v6 prompt, reference hashes and original pixels through a pinned parent record. Any new curtain sheet must retain its own full ImageGen output and catalog/composition provenance. Every style records measured visible-face bounds and every icon records ink bounds, separate from texture padding and shadow extents. The packaging gate checks those registrations, exact source crops, transparent gutters and uniform corner calibration before and after staging.

[Packaging verification](checks/packaging-verification.json) passes **63 tests** against the actual v7 family. The [test log](checks/packaging-tests.log) includes rejection of altered parent provenance, source/atlas pixels, face/ink registrations, pill minima and curtain aperture calibration. Both curtains have two registered transparent openings inside their fixed corner pieces. [Android preflight](checks/android-preflight.json) passes for **286 runtime files**, normal package `com.yiochen.sushilooptickets`, **0.4.3 / code 43**. The packages, save identity and pinned signer remain unchanged.

Issue #12 and PR #36 remain open for user verification. This amendment does not establish visual acceptance or authorize the next implementation ticket.
