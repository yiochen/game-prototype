# Pan rendering optimization — 0.4.14 / version code 54

The Mobile-renderer pan benchmark follows the same horizontal camera sweep in
Edit and Live. It runs in an isolated seed-41 restaurant, warms the visible art,
disables VSync, and records 180 frames per mode. Measurements are from an Apple
M4 using Metal, not an Android device. No Android device was connected.

| Rendering work | Before | After |
| --- | --- | --- |
| Shadow draw calls, median | 50 | 2 |
| Shadow draw calls, p95 | 90 | 2 |
| Reduction passes at 390×844 | 4 | 2 |
| Reduction passes at 1080×2340 | 4 | 0 |

- Conveyor/stool decks, legs, blackboard posts and feet share one unit-box
  MultiMesh. Character capsules share a second MultiMesh. Shapes and light
  direction are unchanged; individual meshes are no longer rebuilt as painter
  order changes. Templates are cached and instance transforms upload in bulk.
- Buffer uploads and camera/receiver geometry updates are skipped when their
  inputs are unchanged. Shadow viewports continue rendering while active, which
  preserves correct first-frame shadows and immediate light/geometry updates.
- The compositor's physical-pixel footprint selects which reduction targets
  need updates. It retains the same full-resolution sprite pass and final
  filtering, and automatically adjusts after viewport changes.
- Shadow collection no longer resolves animation textures or sprite rectangles;
  the native color/shadow passes share one sorted render plan.

The 390×844 Edit captures before/after batching and reduction selection were
compared with Godot Image: **zero changed RGB pixels**, maximum channel
difference 0/255 across 329,160 pixels. The later render-plan/atlas optimization
changes only CPU work. Final 1080×2340, wider portrait and landscape captures
passed the native GPU checks, including blackboard direction, floor clipping,
conveyor visibility, removal of shadow casters, unchanged instance-buffer reuse
and unchanged sprite-picking geometry.

Desktop frame-wall medians remain around 8 ms and do not establish an Android
FPS improvement. GPU timestamp measurements were unavailable on this Metal
setup (zero values in the reports). The verified improvement is fewer rendering
submissions and unnecessary passes; Android smoothness still needs device QA.

Validation: all 13 native suites, GPU regression captures and web build passed.
Repository tests remain 200/202 with the same two missing art-history files.
The 0.4.14 release export passed its original-signer, package/version, nondebuggable
and payload audits; see [release audit](release-audit.json). Package and save
identity are unchanged, with Vulkan on Android and Compatibility fallback disabled.

Evidence: [before at 390 px](before-390.json), [after at 390 px](after-390.json),
[after at 1080 px](after-1080.json), [final scene](02-live-shadows.png),
[landscape](04-edit-1280x720.png). The original shadow source is retained as
`before-ground-shadows.gd.txt` for comparison.

```sh
python3 prototypes/sushi-loop/godot/tools/test_native.py \
  --script tests/profile_pan.gd --visible --size 1080x2340 \
  --output /tmp/sushi-loop-pan-profile
```
