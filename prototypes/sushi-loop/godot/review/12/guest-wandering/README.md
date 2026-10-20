# Issue 12 — blocked-route guest wandering

The [behavior correction](contract.md) targets signed Android **0.4.6 / code 46**. Valid layout edits may block a guest route. Unreachable walking/leaving guests keep their destination and visit state while walking around free floor; they resume a goal route when it becomes reachable. Seated guests stay seated, and the existing direct-overlap, busy-seat and entrance guards remain.

Implementation and verification are in progress. This folder will hold native verification and signed-APK evidence after the final source freeze and sequential exports. Planned actual Android coverage uses a fresh isolated review package and real inventory drags to close and reopen a route, observes wandering movement and walk frames, reopens a paused wandering save, restores the route and checks automatic recovery. No app-state injection or runtime test backdoor is used.

The normal 0.4.5 → 0.4.6 upgrade is checked separately: both legacy save files stay byte-identical before launch; first launch adds navigation version 1/defaults and documented seated-path cleanup while preserving all legacy physical, economic, meal, visit, clock and RNG state. The [0.4.5 sprite-selection evidence](../sprite-selection/README.md) remains unchanged history. Package names, save identity, signer and approved v8 UI are unchanged. This stays within issue #12 and PR #36.
