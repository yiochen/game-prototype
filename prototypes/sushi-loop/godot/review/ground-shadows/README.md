# Sprite silhouette ground-shadow trial — 2026-10-22

## Performance update: 0.4.14 (54)

The current release batches shadow casters into two MultiMesh draws and skips
unused compositor reduction passes. The same pan path dropped from 50–90 shadow
draw calls to 2; a 1080×2340 viewport skips all four unused reduction passes.
The 390 px before/after scene comparison is pixel-identical. See
[pan profiling, limitations and validation](pan-performance/README.md).

## Install correction: release update 0.4.13 (53)

The first shared Vulkan APK was debug-signed under the normal package ID. Its
certificate differed from the installed app's pinned release signer, making it
incompatible as an update. Do not uninstall the existing app to resolve this.

The replacement is a nondebuggable release APK, version 0.4.13 / code 53, signed
with the original pinned certificate. Its package and save identity are unchanged,
and Mobile / Vulkan remains enabled. The complete release export, certificate,
package/version and payload audits passed. Android build mode now defaults to
release, and AGENTS.md records the requirement for delivered updates.

## Current renderer: Mobile / Vulkan on Android

The project now uses Godot's Mobile RenderingDevice renderer, with the Android
driver explicitly set to Vulkan and automatic OpenGL/Compatibility fallback
disabled. macOS uses Metal. GPU capture checks assert the actual renderer is
Mobile and require Vulkan when running on Android.

[Current scene](mobile-vulkan/02-live-shadows.png),
[landscape](mobile-vulkan/04-edit-1280x720.png) and
[renderer report](mobile-vulkan/renderer.json) were captured with Mobile / Metal
on macOS. Native blackboard/light-direction/floor-clipping checks passed, and
806 visible conveyor shadow pixels were measured. No Android device was
connected, so this verifies desktop rendering and Android configuration rather
than an Android GPU run. Earlier Compatibility captures remain historical.

The Android debug APK was exported and independently re-audited after updating
the packaging audit from legacy aapt1 to aapt2. aapt1 rejects Godot's generated
Vulkan feature declarations; aapt2 reads them successfully. Package/version,
signature, permissions, excluded files and all seven runtime manifest hashes
were checked. The compiled APK settings also confirm Mobile / Vulkan with no
OpenGL fallback; see [APK audit](mobile-vulkan/android-apk-audit.json).
The aapt2 regression test preserves release/debug and package-identity rejection.
All 13 native suites and the web build passed; repository tests are 200/202,
with the same two missing-art-history failures described below.

## Current: native Godot lighting

The current renderer replaces the flattened sprite shadows with actual
`DirectionalLight3D` shadow maps. Hidden meshes supply approximate heights and
footprints: conveyor/stool decks and legs, a blackboard panel with posts/feet in
its measured front-of-cell band, character capsules and basic prop volumes.
The light direction is (0.55,-1,-0.35), giving finite top-right shadows.

The shadow-only meshes are invisible to the color camera. A top-down orthographic
camera renders a white floor receiver, and native light attenuation becomes a
transparent warm-brown layer at 18% maximum opacity. The receiver is clipped to
the restaurant floor, so shadows do not paint the back wall. Color sprites,
animation, sprite picking and UI remain unchanged. Two quarter-native-resolution
targets are used; Android frame cost has not been measured.

Native 2D directional lights were considered, but their shadows are infinitely
long and their Height does not supply geometry heights. See
[Godot's 2D lighting documentation](https://docs.godotengine.org/en/stable/tutorials/2d/2d_lights_and_shadows.html).
The current approach instead uses Godot's native 3D shadow mapping in the
initial Compatibility renderer (now replaced by Mobile, as recorded above).
The presentation shader only extracts/tints
the native shadow mask; it does not project sprite silhouettes.

Current evidence is in `native-lighting/`: [full scene](native-lighting/02-live-shadows.png),
[conveyors](native-lighting/06-conveyors-top-right.png) and
[blackboard's native shadow receiver](native-lighting/07-blackboard-native-shadow-map.png).
The GPU regression checks the blackboard has no shadow pixels left of its
physical footprint, shadows respond to changes in the actual light direction,
the receiver respects the wall/floor edge, and conveyor shadows remain visible.
These proxies do not reproduce every detail of the source meshes or limb animation.

Validation: all 13 native suites passed. The Compatibility GPU check found 432
blackboard shadow pixels with no left extrusion, verified actual-light response
and floor clipping, and found 806 visible upper-right conveyor shadow pixels.
Phone, wider portrait and landscape captures were visually checked. The web
build passed; repository tests remain 199/201 with the same two missing art-history
files documented in the initial trial below.

Both sprite-shadow experiments below are superseded, with sources/captures
retained as historical comparisons.

## Earlier top-right sprite revision

The current projection is X=(1,0), Y=(-0.55,0.35): sprite height projects to
the top right. Its increased reach lets conveyor shadows extend beyond their
raised color sprites; the first trial's shorter projection hid most of them.
Opacity, blur, sprite registration and draw order are unchanged.

Current captures live in `top-right/`: [full scene](top-right/02-live-shadows.png),
[conveyors without shadows](top-right/05-conveyors-before.png) and
[conveyors with shadows](top-right/06-conveyors-top-right.png). The GPU capture
check also measures darkened floor pixels above and right of the conveyor's
end module, so a completely covered belt shadow fails verification.
The 390×844 check found 320 visibly darkened pixels in that floor region.
All 13 native suites and the build passed again; repository tests retain the
same two missing-art-history failures documented below. Phone, wider portrait
and landscape captures were visually checked.

The original images and calibration below are retained for comparison.

## Initial trial

Requested trial: reuse the existing object sprite, tilt/squash its silhouette,
recolor it and blur it beneath the object. This is a runtime rendering change;
approved color sprites, registration, gameplay and UI artwork are unchanged.

- [Before](01-live-before.png) and [after](02-live-shadows.png) use the same
  frozen seed-41 session, ten seconds into service, at 390×844.
- [Phone editor](03-edit-shadows.png), [wider portrait](04-edit-768x1024.png)
  and [landscape](04-edit-1280x720.png) show the current native UI and renderer.
- Furniture, chefs, customers, plants, crates and barrels reuse the current
  facing/action/frame. Dishes, thought bubbles and walls are excluded.
- The shadow uses the sprite's alpha, a warm brown at 22% opacity, and the
  registered ground root. Projection basis: X=(1,0), Y=(-0.22,-0.20).
- A nine-sample weighted alpha blur stays inside the current atlas frame;
  transparent padding allows the softened edge to extend beyond the frame.
- One quarter-native-resolution GPU target is composited after floor/backdrop
  and before objects, selection overlays and UI. Pooled sprite nodes release
  unused atlas references. No runtime image readbacks or shadow-frame cache.
- `ground_shadows_enabled` on RestaurantView switches the native A/B comparison.

Reproduce with isolated save data:

```sh
python3 prototypes/sushi-loop/godot/tools/test_native.py \
  --script tests/capture_ground_shadows.gd --visible --size 390x844 \
  --output /tmp/sushi-loop-shadows
```

The capture checks assert visible GPU output changes, frozen simulation and
unchanged sprite-picking rectangles/ownership. Actual Compatibility-renderer
captures were visually inspected at all three window sizes. Android-device
frame cost has not been measured.

Validation: all 13 native test suites passed, as did the GPU A/B capture and
`npm run build`. `npm test` passed 199/201 tests; the two failures reference
missing historical art files: the belt-straight-n round-09 consumer's
`.godot/.gdignore` and coin-pop's `final/original-catalog-object.json`.
