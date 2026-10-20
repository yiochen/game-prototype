# Issue 12 — previous curtains and continuous backdrop

The [current correction](contract.md) is implemented in signed Android **0.4.4 / code 44**. It restores the exact previous curtain artwork, lowers it three logical units to meet the wooden rod, restores the overall beige background behind the bottom UI, and extends the rod's visible wood to both screen edges. Native text/icon alignment, compact goods, bare carets, stock padding and the thicker dock remain.

[Download APK 0.4.4](https://drive.google.com/file/d/1JH6hkgaE6yCSyWdn1YJLPTc8ZM_inSnf/view?usp=drivesdk). The [verified upload receipt](drive-upload.json) matches the signed local APK by size and MD5. Sharing was unchanged. The review package is `com.yiochen.sushilooptickets.review12`; normal package `com.yiochen.sushilooptickets`, save identity and release signer remain unchanged.

[Phone preview](native/720x1560/02-edit-layout.png). The [capture matrix](native/capture-matrix.json) exercised two full 30-state runs and retains eight representative screenshots across 720×1560 and 320×720: open, pressed, narrowed final page and collapsed. Runtime source hashes match the corrected implementation; test-only metadata/assertion edits after capture do not change its visuals.

[Native verification](checks/native-matrix.json) passes **229 checks at each of 320×720 and 1280×720**. Actual rendered pixels show two original fabric strap bands crossing the rod, wood reaching both edges and continuous beige through seams, beside goods and at the footer. The visible backing also shields scene input while moving. Existing font, card, pager, stock, dock and currency cases pass.

[Actual Android verification](android/android-verification-summary.json) passes **55 assertions** on the signed APK, including the normal 0.4.3→0.4.4 save upgrade, fresh review isolation, pointer-down/cancelled touches across Home/resume, drag/rotate/Return, both pagers, profiles/Back/focus, cold reopen and Live continuation. The new beige gutter blocks both taps and swipes without changing the underlying restaurant. [Eight APK screenshots, reports and logs](android/README.md) are retained. There were zero runtime errors; two cold-start shader-cache warnings recovered by recompilation. The isolated clone was stopped and the original AVD remained unchanged.

The [art-reuse proof](checks/approved-art-reuse.json) confirms the entire runtime UI atlas is byte-identical to the approved v6 atlas. **No artwork was generated for this correction.** The v8 schema-4 registration inherits the three unchanged v6 ImageGen sheets and complete-screen provenance. Source gates verify exact curtain generation/crops/pixels and existing optical bounds, uniform corners and 100-unit pill minima. [All 64 packaging tests pass](checks/packaging-verification.json).

The [normal build receipt](normal-build.json) and [review build receipt](review-build.json) record 286 runtime files, runtime commit `5190d3034d3f8a1818fd8203178e799ac75caa84` and fingerprint `47c283518d1acda892838eb263ce9c757ab8062f55dea90b072c74c5193db5a1`. Review APK SHA256: `b059c76d92c0baa0059936d486653d113b2d7a7dbe82cc94013021d594b262bc`. The [0.4.3 review](../alignment-revision/README.md) remains unchanged history.

Issue #12 and PR #36 remain open for user verification. No next ticket is included.
