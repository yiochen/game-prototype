# Android performance investigation — 2026-10-30

Installed and launched the normal signed **0.11.7 / code 79** release on the connected Pixel 10 Pro. The installed APK hash matches the audited build:

`16189c24e3c46e96a2fb400069f2dfe2498beedb23b92725ec4055b4f8a84c4d`

Package, save identity and pinned release certificate remain unchanged. The APK is nondebuggable. The phone reported Godot Mobile / Vulkan 1.4.317 on its ImgTec PowerVR D-Series GPU. Every packaged artwork resource has the same hash as 0.11.4.

## Findings and changes

- Capacity and arrival queries repeatedly scanned the full expanded floor and built complete trash presentations. Cache immutable floor geometry, use direct capacity helpers, and cache each session's clearance presentation until its floor, cleared objects or revealed state changes. Returned snapshots remain independently owned; a mutex protects the shared geometry cache during save validation.
- Atomic save rotation restored the same verified payload repeatedly. Retain a bounded cache of successfully domain-validated payload hashes. Incoming dictionaries still receive domain validation, and every disk read still parses the envelope, checks its size and verifies its SHA-256. New or damaged bytes receive the complete validation path.
- Live simulation events synchronously serialized, validated, flushed and rotated saves on the rendering thread. A single low-priority worker now performs routine autosaves. It owns its snapshot and retains at most one newer queued snapshot. Explicit player actions, loading, reset, suspension and exit join the writer; a newer acknowledged action cannot be overwritten by older work. Checksum, backup and atomic promotion rules remain active.

## Measurements

Game-only Perfetto Swappy frame-marker cadence, each capture approximately 12 seconds:

| Release/state | Average FPS | Median frame | P95 frame |
| --- | ---: | ---: | ---: |
| 0.11.4 Live, warm | 35.7 | 27.5 ms | 29.3 ms |
| 0.11.6 Live, before async saves | 43.0 | 15.6 ms | 93.0 ms |
| 0.11.7 Live, first sample | 76.3 | 10.5 ms | 18.8 ms |
| 0.11.7 Live, later warm sample | 58.0 | 14.0 ms | 23.0 ms |

Occasional long frames remain: the final warm sample includes six intervals above 100 ms, with a maximum of 208 ms. This is an improvement, not a claim of locked frame pacing. The one-second on-screen FPS counter varies with those stalls. Its CPU monitor is sampled separately and was not used as an average frame CPU measurement.

The older 0.11.4 save and post-install room differ, so the phone results are not an identical-save A/B test. A controlled local benchmark of the same starter restaurant reduced main refresh work from **2.916 ms** to **0.365 ms**. The intermediate 0.11.6 and final 0.11.7 retain the current room's layout.

Android HWUI statistics and FrameTimeline do not measure this Godot SurfaceView. Filtered game slices and summaries are retained here; raw system traces stay outside the repository. Temporary traces and configuration files created on the phone were removed.

## Save-state clarification

The user confirmed on 2026-10-30 that they were playing or resetting the restaurant during profiling. The balance change from 6,298 to 148 is therefore no longer an unresolved save-recovery concern.

The initial incremental `adb install -r` reported success, followed by an unavailable package lookup. Subsequent updates used `adb install --no-incremental -r --user 0`, and their installed version and APK hashes were verified. No uninstall or data-clear command was issued.

The code 77 → 78 update preserved exactly 1,234 coins, Edit mode and the visible room. Before code 79, Edit showed 2,858 coins; the final release showed the same room running Live at 2,910 coins. The final cold-restart check was stopped when the phone switched to another app, and no further touch input was issued.

## Verification

- **15 native suites / 1,590 checks passed**, covering capacity equivalence across legacy floors, snapshot mutation isolation, clear/reveal invalidation, bounded save validation, atomic recovery, worker handoff/coalescing, stale-write prevention, pause/resume, editor, customers, staff, shop, cover animation and exhibition UI.
- **25 relevant browser checks passed** and the Vite production build passed.
- **87 of 89 JavaScript tests passed.** Two historical refinement checks lack archived fixture files: the belt-straight-n round-09 consumer `.godot/.gdignore` and coin-pop `final/original-catalog-object.json`. These failures do not touch the runtime changes.
- Full release import, production catalog/artwork gates, certificate/nondebuggable audit and all 512 packaged source hashes passed. The installed APK bytes match that release.

See `measurements.json`, `checks/results.json`, `android-release-final.build.json`, `installed-final.txt`, `installed-final-sha256.txt`, and the retained game captures for evidence.
