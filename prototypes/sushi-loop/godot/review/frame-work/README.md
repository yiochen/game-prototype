# Frame work — 0.4.16 (56)

Reported device: Pixel 10 Pro; overlay reading CPU 135 ms, draws 70, FPS 28. No Android device is connected to this workspace, so the desktop benchmark below is not a claim about Android FPS.

Final changes: one detached session snapshot and one UI refresh per Live frame; selection reuses the prepared snapshot; inventory presentation relayout follows visual state/geometry changes, including hidden controls on safe-area changes; unchanged hidden/visible selection does not relayout the dock; sprite hit records resolve on demand through the existing input/picking pass. Explicit advance_time callers still refresh immediately. The overlay's CPU value is now a rolling one-second mean rather than a last-frame sample.

The complete CPU microbenchmark invokes the main scene's _process 120 times with a controlled clock. On Apple M4 / Mobile / Metal at 1080×2340, median main-loop work fell from 2341 µs to 124 µs (94.7%). This excludes render-thread and GPU work and must not be extrapolated to whole-game or Android FPS. Pan frame wall time remains about 8–9 ms on this 120 Hz desktop. See before.json / after.json for p95 and allocation details. GPU timestamps are unavailable on this host.

A cull-before-atlas-load experiment, including a bounded spare cache, increased Live pan p95 from about 9 ms to 24–27 ms due to texture churn. Both changes were removed before shipping. The original atlas lifetime, sprite frames, native 256 px cell, area filter and live native shadow pass remain. The current native render target is 1824×3920 at this display size, about 7.2 million pixels; render-resolution scaling is a possible future GPU experiment, not part of this release.

Verification includes a counted-session test proving one snapshot per main frame and immediate explicit advancement, all native suites, existing raised-sprite/transparent-pixel picking tests, safe-area/UI tests, actual Mobile/Metal pan rendering and phone/wide/landscape overlay captures. The native tests use disposable projects and unique save identities.

Pixel comparison: the complete restaurant below the diagnostic strip was byte-for-byte identical in both Edit and Live before/after 1080×2340 captures.

User verification on Pixel 10 Pro after installing 0.4.16: “Much better. Frame rate stays at 80,90.” This is user-reported device feedback, not a local instrumented benchmark. The user approved committing and merging this change.
