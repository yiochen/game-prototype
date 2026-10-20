# Issue 12 — alignment and spacing refinement

The [latest B amendment](contract.md) is implemented in signed Android **0.4.3 / code 43**. It removes the category backing and caret surfaces, tightens the goods drawer, adds stock padding, thickens the rod and dock, and aligns native text/icons to measured visible faces. The curtains now have real transparent loop openings. Rounded controls retain their 100-unit minimum height.

[Download the verified review APK](https://drive.google.com/file/d/1Fp0xLQ7IXv0uYZb3-dgqMIIJrtX4n5zX/view?usp=drivesdk). It uses the separate `com.yiochen.sushilooptickets.review12` package. [Drive verification](drive-upload.json) confirms the uploaded size and MD5 match the signed local APK; sharing was unchanged. The [0.4.2 review](../noren-revision/README.md) remains historical evidence.

[Open the main phone view](native/720x1560/02-edit-layout.png). The [native capture matrix](native/capture-matrix.json) contains **120 screenshots**: thirty states at each of 720×1560, 320×720, 1440×1000 and 1280×720. It covers Live/Edit, held/cancelled controls, context actions, paging, profiles, recovery and the shared gallery.

[Native verification](checks/native-matrix.json) passes **222 checks at each of three phone/landscape sizes**, using rendered foreground/background differences to measure actual text and icon ink. Other checks pass: 182 headless app, 83 rendered nine-patch, 94 session and 26 save checks. The unchanged gameplay/art subset also passes [engine checks](checks/engine-subset-verification.json): 185 editor, 76 customer, 12 demonstration and 1,501 art checks. [Packaging verification](checks/packaging-verification.json) passes **63 tests**.

[Actual Android verification](android/android-verification-summary.json) passes **53 assertions** with real touch, swipe and Back inputs on an isolated read-only Pixel 8/API 35 clone. It verifies normal 0.4.2→0.4.3 save preservation, fresh review package isolation, held/cancelled touches through Home/resume and orphan release, both bare pagers on the narrowing final page, context actions, profiles/focus, editing, immediate saves, cold reopen and Live continuation. [Screenshots and logs](android/README.md) show the installed APK. There were zero runtime errors; the clone was stopped and the original AVD remained unchanged.

The v7 family uses manifest/provenance schema 4. Unchanged sheets and the complete-screen composition inherit exact v6 prompt/reference receipts through a pinned parent record; only the curtain pair is newly generated. Every style records visible-face bounds and every icon records tight ink bounds, separate from transparent padding and shadow. The packaging gate checks provenance, exact RGBA crops, gutters, uniform corners and transparent openings.

The [normal build receipt](normal-build.json) and [review build receipt](review-build.json) contain 286 runtime files with fingerprint `880b26f49879a1be883e98121794c6bafbabb91f67e4f269d0e627d3b0bc09db`, built from runtime commit `bcec29f3`. The normal package `com.yiochen.sushilooptickets`, save identity and signer remain unchanged. Review APK SHA256: `c1bc546466b70726f1189dbab2bf1c542a53bbfb296d07a13ec303eb14dca97e`.

Issue #12 and PR #36 remain open for user verification. No next implementation ticket is included.
