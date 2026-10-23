# Android diagnostic overlay — 0.4.15 (55)

The user requested on-screen framerate diagnostics to investigate persistent panning slowdown. This is temporary developer instrumentation rendered as native text over the existing quiet sky strip, separate from the authored game UI family. No product controls or artwork were added. The overlay ignores touches and focus, and updates its text four times a second.

- FPS: frames divided by elapsed wall-clock time in the rolling one-second sample window.
- ms: average wall-clock frame interval; max: slowest interval in that window. Includes presentation waits and stalls, not only CPU work.
- CPU: Godot TIME_PROCESS monitor in milliseconds (not GPU time).
- draws: Godot total frame draw-call monitor. Version identifies the installed build.

Suspension clears the sample history. Samples use 64-bit monotonic timestamps and are bounded to 512 intervals. Startup and resizing can appear as legitimate spikes and age out after a second. Diagnostics do not change simulation/save state, frame cap, renderer or VSync. Android stays Mobile/Vulkan with Compatibility fallback disabled.

Validation: deterministic 60 FPS / 100 ms hitch / window expiry / resume checks; isolated native suites; actual Mobile/Metal captures at 390×844, 720×1280 and 844×390, plus safe-area placement and noninteractive control assertions. Desktop captures verify rendering/layout, not Android performance. No Android device is attached locally.
