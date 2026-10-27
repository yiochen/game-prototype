# Issue 16 — native implementation review

Approved design: [interactive prototype](https://6adfa8edd2cc138ad8c62b1f--game-prototypes-yiochen.netlify.app/prototypes/sushi-loop/design/staff-hiring-preview/). The user's subsequent approval authorizes this Godot implementation. Catalog sections 5 and 8–9, the current continuous maple dock and independent People photo family remain the references. The prototype's composition, exact paper/stamp artwork, illustrated identities and source slicing are reused. User amendments supersede the original issue's strength/reachable-tier/start-state captions and timed replacement wording.

The native session owns persistent offers, one-time payment, capacity, absolute Refresh deadline, six applicant identities and unread flags. The custom fan provides horizontal touch ownership, velocity-assisted sticky settling, tilted neighboring papers, edge resistance, wheel and keyboard browsing. It has no page indicator, caret, instructions, scrollbar or vertical scrolling. No toast appears after Hire. Confirmation is expand → physical stamp impact → red live Hired imprint → fly-out; reduced motion retains the ink with a short fade.

The native photo roster and separate profile are shared by Staff (Live), People (Edit) and the component review mode. Modal dismissal preserves mode/editor/camera. Live roster browsing does not edit Edit's scroll state. Chef placement uses the existing atomic floor/belt rules, opens the same idle recipe picker and preserves explicit Prepare behavior.

## Evidence

`320x720/`, `390x844/`, `1440x1000/` and `844x390/` contain full-scene captures from the real Godot Mobile renderer, Metal on Apple M4. Each includes applicants, middle-card neighbors, expansion, stamp contact, imprint, capacity, unread roster, details, unaffordable cost and the same presentation over Shared. `renderer.json` records the actual driver and device. Tween captures pause and advance the real production tweens, without substituting a painted confirmation.

Tests use a separate runtime project and `SushiLoopTicketsTest-*` save identity; installed restaurant data is never used. The public-rule and integrated viewport tests cover payment, retained offers, cooldown/reopen, identity/assignment saves, offscreen/covered/interrupted visibility and native placement. Desktop OS window focus is an external condition; visibility timing is additionally checked against the real rendered card bounds through the extracted foreground predicate.

The complete regression run is recorded in `verification.json`. Historical failures are compared against the same tests and runtime scripts at HEAD in a second isolated project. No missing historical art evidence was fabricated to satisfy old provenance tests. The web build succeeds; two pre-existing Node provenance tests reference absent historical files.

## Release APK and Android smoke

Normal release 0.8.0 / code 67 is nondebuggable and retains `com.yiochen.sushilooptickets`, `SushiLoopTickets` and the pinned original signer. The APK SHA-256 is `12f2c5be5c5431465362383772b13b2bf8a8c69f560856d59eb16f8f5ec68e8f`. The exact approved staff manifest and content JSON were additionally read back from the signed ZIP and matched to source.

The temporary read-only Android 15 ARM64 emulator installs version 67 and starts Godot's actual Forward Mobile renderer with Vulkan 1.3.0. Its SwiftShader backend fails presentation with VkResult error 5 and a black surface, so this is not an Android visual pass. Logs and black captures are retained in `android/`; no physical device is connected. No Compatibility fallback, app identity change or uninstall workaround is used. Native Metal captures and feature touch checks are the completed visual evidence.

A second check used a fresh temporary userdata image and the host Apple M4/MoltenVK bridge, preserving the existing AVD's old app/data. It installed the exact signed 0.8.0 / code 67 APK, verified all 470 current runtime source hashes against its build receipt, and started Forward Mobile/Vulkan 1.3.0. Presentation still failed with VkResult error 5, including after resume. Both attempts therefore remain explicitly unverified visually on Android. The temporary emulator was closed after the check.

The connected Drive upload was rejected before invocation because its 100 MiB file-reference limit is below the 351,918,517-byte APK. The CLI's OAuth grant had expired; a fresh limited `drive.file` sign-in was opened. No Drive file URL is claimed until the upload and metadata readback complete.

## APK size investigation and physical-phone install

The signed APK is 351,918,517 bytes (335.62 MiB). ZIP-accounted payload: chef animation textures 111.24 MiB; customer animation textures 88.35 MiB; customer/chef food variants 29.50 MiB; UI/portraits 28.64 MiB; arm64 libraries 23.34 MiB; x86_64 libraries 24.64 MiB; world props/floors/effects 13.86 MiB; conveyors 7.45 MiB; remaining feedback/audio/fonts/other files about 8.4 MiB. The six new chefs add 82.57 MiB across 96 four-facing animation atlases (1,152 frames). The payload excludes source Blender projects and historical review evidence.

Godot's imported 2D textures currently use lossless compression (`compress/mode=0`) with mipmaps. Enabling the project ETC2/ASTC import support alone does not select VRAM compression for these 2D imports (`vram_texture=false`). An isolated import probe retains the exact source images, dimensions and mipmaps, measuring lossy quality 0.8 and 0.9 and a lossless-without-mipmaps control. Quality 0.9 reduces the two sampled animation atlases by about 73% and the sampled paper by about 93%. These are sample resource results, not an exported APK size prediction or visual acceptance. The installed 0.8.0 APK and production import settings are unchanged. `apk-size.json` contains per-source and per-object accounting plus probe results.

Godot documentation: https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/importing_images.html#compress-mode — Lossy is intended for large 2D assets and reduces disk size while retaining the same VRAM usage; GPU compression has different quality/memory tradeoffs. A phone-only arm64 export would independently remove roughly 24.64 MiB of unused x86_64 native libraries. Review texture quality at actual phone scale before applying compression; retain mipmaps where needed for stable downsampling.

Installed the exact signed release successfully on the connected Pixel 10 Pro with `adb --no-incremental -r`. Package readback confirms version 0.8.0 / code 67. No uninstall, data reset or signing change was performed.

Drive authentication was renewed for the same account and limited scope. The release upload completed, and an independent metadata readback verified name, byte count and SHA-256 against the local signed APK. Verified link: https://drive.google.com/file/d/1z5VZxpwZXqhxKtjGhN3xPZeKlb1wB0-T/view?usp=drivesdk . `drive-release.json` records the observed metadata; no sharing or permission changes were made.
