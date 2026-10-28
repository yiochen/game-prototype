# Issue 17 · native Godot implementation · 0.9.0 / 70

The approved tabbed popup, wood-only Manage page, portrait/separator anchor, purchased levels, stored/assigned chef lifecycle and stamped firing application now use production Godot controls. See [contract.md](contract.md) and [verification.json](verification.json).

The same `recipe_picker.gd`, `chef_management.gd` and `chef_dismissal.gd` serve gameplay and `--chef-gallery`. Existing #16 résumé/headshot/physical stamp and patterned plates are reused. Levels/caps/growth remain with the retained chef; reassignment opens idle Recipes until Prepare. Fire saves removal before animation and retains Fired ink until Close, with no toast. Cancel and Back leave staff unchanged. A real storage-failure test confirms that Retry saves the same removal before resuming the Fired receipt.

Versioned migration adds progression baselines and dismissed identities without resetting shipped progress, prices, discoveries, camera, arrangement, meal clocks, RNG or coins. Actual preparation uses upgraded cooking speed. Cost/growth tuning is in `godot/content/chef_development.json`, outside rules and UI. Hired caps/growth remain in the existing staff catalog.

Validation: 52 new rule checks, 595 passing domain regression checks, 369 native hiring/navigation/general UI/recovery checks, and 108 GPU touch checks across 320×720, 390×844, 1440×1000 and 844×390. Mobile/Metal/Apple M4 was observed in real native captures. Node repository tests remain 200 passed / 2 known missing-artifact failures; two older native legacy-fixture assertions also fail identically on unchanged HEAD, as recorded by the baseline logs. Web build passes with its existing chunk warning.

Captures cover Recipes, the next-level preview, a real held press, named firing confirmation, stamp contact, retained Fired ink, insufficient funds, MAX and the shared presentation. They are actual native screens, not web mockups. Normal and wide windows retain the restaurant scene; compact landscape keeps management controls and benefits together.

The normal signed update is `godot/build/sushi-loop-release-v0.9.0.apk`: package `com.yiochen.sushilooptickets`, save identity `SushiLoopTickets`, code 70, original pinned release signer, nondebuggable. All 474 runtime source hashes and the APK bytes/SHA match the audited build. The temporary exporter reused only source-identical Godot image-import cache; normal staging, source hash, art manifest, signer and APK audits still ran. There was no connected Android device, so this run does not claim an Android install or actual Vulkan/GPU verification.

Reproduce production Shared UI with `godot --path prototypes/sushi-loop/godot -- --chef-gallery`. Tests use a disposable staged runtime and the separate `SushiLoopTicketsTest-Issue17` identity; the user's installed save was never opened by verification. The user approved the native build and authorized merging and resolving #17. No subsequent implementation ticket is part of this change.

[Verified signed Android 0.9.0 APK on Google Drive](https://drive.google.com/file/d/1Ffqk9iA2109F7sZL2XiEiU7QkuW6jMJ4/view?usp=drivesdk). The uploaded file size and SHA-256 match the audited local release.
