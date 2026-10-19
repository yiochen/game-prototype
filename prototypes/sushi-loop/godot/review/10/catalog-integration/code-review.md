# Independent review record

Fixed base: `fbcfef76c3fb4032cfdeee19d8ca1a16160b6354` (merged art catalog PR #34). Initial head: `ac96d18d824ac379c1ed2c2d7e847ca908dff5d5`. Re-reviewed head: `d07856aa6c46c7dba5f020179595326b10862b14`.

Two independent read-only reviewers followed the code-review skill: Standards checked applicable AGENTS.md instructions and the full smell baseline; Spec checked GitHub issue #10 and the approved art integration. Reviewers did not author fixes.

| Axis | Initial finding | Resolution | Re-review |
| --- | --- | --- | --- |
| Standards · P2 | Packaging had a weaker duplicate catalog check and accepted an empty registration manifest. | Shared `catalog_contract.verify_catalog` now checks exact selection, provenance, roots, frame regions, references and source bytes in synchronization, preflight and staging. Recipe variants have a separate shared native provenance gate. Sixteen packaging regressions pass. | Clear |
| Spec · P2 | Customer eating/waiting poses baked in maki although the starter served salmon. | Native Blender variants use the approved salmon image while eating and no food while waiting. All 384 pose/facing samples have native structural receipts; the original 139 atlases are unchanged. | Clear |
| Spec · P2 | Old saves kept the previous nine-column presentation. | Restore migrates only the presentation width to seven, preserving saved layout/economics/state. A real 0.1.1 snapshot fixture covers it. | Clear |
| Spec · P2 | Blocked dishes accumulated progress and teleported when a vacancy opened. | Blocked movement stops charging; genuine partial crossings remain visible. A versioned migration clears only previously hidden charged progress. Tests cover queues, partial blockage and exactly-once transfers/sales. | Clear |

Standards re-review independently ran all 16 packaging checks, the 28-object/139-atlas exact base check and the four-customer/32-atlas/384-frame variant verifier. Spec re-review inspected the final phone meal capture and the 1,021 art / 94 session / 26 save / 64 UI results. No remaining actionable findings were reported on either axis.
