# Android validation · issue #11 customer visits

The primary [Customer Visits review APK](https://drive.google.com/file/d/15QpL-oLuSuFHPoCrid_LyWgLQ8PeUHEj/view?usp=drivesdk) uses an isolated Android package so it opens the fresh demonstration alongside the installed restaurant. Version **0.3.0 / code 30**; title **Sushi Loop · Customer Visits**; package `com.yiochen.sushilooptickets.review11`.

| Build | Bytes | APK SHA-256 |
| --- | ---: | --- |
| Isolated review | 213,564,944 | `a54bd2482e6e2df09dfe2c906eb3ac68da530a1828e4eb45420e772f67452523` |
| Normal update | 213,560,848 | `92a0081c35ad529dd27f97ea9f7e140b0394aaed5e610bb36a68d91781b314fd` |

Both artifacts were rebuilt from final code `0211c6bb4ad5bc6100384aa240c9383df4bc4a9d`. Their exact 257-file source maps match that commit. The normal package remains `com.yiochen.sushilooptickets`; both retain the original release signer and save identity, target SDK 36 with minimum SDK 24, request no permissions, and are nondebuggable. Export audits exclude private, legacy and authoring payloads and verify all four runtime asset manifests.

- [Normal build receipt](normal-build.json), [review build receipt](review-build.json) and [variant parity](variant-parity.json). The only staged differences are `branding.json`, `export_presets.cfg` and `project.godot`; all gameplay code, content and asset files are identical.
- Shared runtime-source fingerprint: `d6e75f9dbcfabb14cb18a690f294a7f76bdf4e30b5361686d473dbcd32db9bfe`. Review staged fingerprint: `a1a50d375a8a8c740609c3d3634b33175ee8e74a9db7432c3d9d8038b7921bd9`. Fingerprints hash the compact sorted JSON file-to-SHA-256 map.
- Asset gates verify 180 byte-identical approved base atlases, 32 native customer-meal atlases, eight native chef-food atlases and four ImageGen 2D smile atlases: 224 atlases / 2,493 frame contexts total. No sprite fitting or resampling is introduced by review isolation.

The [normal version 20→30 update proof](normal-update-verification.json) checks primary and backup save bytes before first launch. The updated app retained the previous restaurant's object layout and camera. Its migrated state then matched uninterrupted final `GameSession` simulation.

The [coinstall proof](coinstall-verification.json) verifies distinct Android application IDs (normal 10211, review 10208). The review package had no prior installation or save. It started at 120 coins, zero sales and elapsed zero with the new three-chef/five-seat layout. Normal primary and backup files remained byte-identical throughout review play and lifecycle testing.

[Actual Android screenshots](review-fresh-scene.png) show the fresh restaurant. A naturally matched salmon preference produced the [smiling feedback](review-happy.png); it was saved at `happy_elapsed=0.9`, then force-stopped and [reopened](review-feedback-reopened.png). [Touch panning](review-touch-panned.png) moved the camera 3.435 tiles, and [Android Back/reopen](review-back-reopened.png) preserved the camera. The [legacy normal restaurant](normal-restored.png) remained intact. Screenshots retain actual device pixels, including transient Android bars during resume.

The [lifecycle report](review-lifecycle.json) confirms four seconds of unchanged Home-background save bytes, force-stop preservation of the active feedback save, Back leaving the activity, two seconds of stable closed save bytes, and camera preservation on reopening. [All three full-state continuation comparisons](continuation-reports.json)—legacy migration, active feedback/force-stop and Android Back—passed at numeric tolerance 1e-7, including complete state/configuration, random state and fractional remainder.

The [runtime report](android-verification.json) and [log](runtime-logcat.txt) contain no script errors or crashes. Three GLES cached-shader entries were automatically recompiled; their recovered warnings remain recorded and post-reopen rendering was inspected. Checks used Pixel 8 / API 35 at 1080 × 2400 in a `-read-only -no-snapshot-save` AVD copy. Original AVD userdata and all physical devices were untouched. Earlier candidate APKs are superseded; these receipts refer only to the final rebuilt hashes above.

The six paired save fixtures are actual synthetic exhibition-game data from that disposable emulator. To reproduce a complete saved-state comparison after importing the native project, run the custom SceneTree below. It reads only the supplied fixtures and never opens the real application's save directory:

```sh
godot --headless --path prototypes/sushi-loop/godot --script res://review/11/android/verify-continuation.gd -- "$PWD/prototypes/sushi-loop/godot/review/11/android/feedback-before-save.json" "$PWD/prototypes/sushi-loop/godot/review/11/android/feedback-after-save.json"
```

Use `legacy-v20-save.json` / `normal-migrated-save.json` for migration, or `back-before-save.json` / `back-after-save.json` for Android Back.
