# Issue 12 — previous curtains and continuous backdrop

The [current correction](contract.md) restores the exact v6 curtain artwork, moves its straps slightly lower against an edge-to-edge wooden rod, and places an overall beige backdrop behind the category rail and goods down to the footer. It preserves native text/icon alignment, the tighter goods cards, bare carets, bottom padding and 100-unit pill minimum.

Verification is in progress. Native captures and the signed 0.4.4 / code 44 Android review APK will be recorded here after verification. The [0.4.3 review](../alignment-revision/README.md) remains unchanged historical evidence.

The v8 schema-4 registration inherits exactly the three unchanged v6 ImageGen sheets and complete-screen provenance. The source gate verifies both curtains' precise source generation, source crop and original pixels, plus the existing face/ink, corner, pill-height and runtime packaging contracts. No new curtain generation is authorized for this correction.

[Packaging verification](checks/packaging-verification.json) passes **64 tests** against the actual v8 family. The [test log](checks/packaging-tests.log) includes rejection of alternate curtain crops, any new generation claim, rewritten parent provenance, altered source/atlas pixels, face/ink registration drift and invalid pill minima. [Android preflight](checks/android-preflight.json) passes for **286 runtime files**, normal package `com.yiochen.sushilooptickets`, **0.4.4 / code 44**. The [UI source receipt](checks/editor-ui-verification.json) records three inherited sheets, 19 styles, 16 icons and all eight pill minima at 100 logical units. Packages, save identity and pinned signer remain unchanged.

Issue #12 and PR #36 remain open for user verification.
