# Issue 12 — visible sprite selection

The [selection correction](contract.md) targets signed Android **0.4.5 / code 45**. Scene taps use the current visible sprite pixels and reverse painter order, including raised chef hats, plant leaves and owner attachments. Selected-object drags retain the original pointer-to-ground-root offset. Grid placement rules and the approved v8 UI remain unchanged.

Implementation and verification are in progress. Native and signed-APK evidence will be recorded here after the final source is frozen and sequential Android exports finish. The planned actual Android run upgrades normal 0.4.4 to 0.4.5, installs a fresh isolated review package, preserves the 55 existing regressions, and adds visible-pixel and raised-part drag cases using offline registered atlas coordinates followed by real touch input. No runtime test backdoor or app-state injection is used.

The [0.4.4 curtain restoration](../curtain-restoration/README.md) remains unchanged history. Android package names, save identity and signer are unchanged. Issue #12 and PR #36 remain open for user verification; this follow-up does not start a later ticket.
