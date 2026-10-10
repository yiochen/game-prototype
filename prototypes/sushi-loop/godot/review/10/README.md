# Ticket #10: operating starter restaurant

This review covers [issue #10](https://github.com/yiochen/game-prototype/issues/10) only, adapted to the user-confirmed Godot Android target. Later tickets have not been implemented. Shop, Edit and Staff remain visible but disabled until their own tickets are approved.

## Try the Android build

1. Install the [signed release APK in My Drive](https://drive.google.com/file/d/11Xc_wS-RMYopaDi8S4Qji_9n_w__Jy0H/view?usp=drivesdk). The Android package is `com.yiochen.sushilooptickets`.
2. Watch Mina prepare salmon nigiri, load the conveyor and begin her next dish. Customers arrive, walk to the three seats, eat and leave automatically.
3. Watch a completed meal add 14 coins once. Its local cue contains a coin icon without an amount label.
4. Drag the room horizontally. The HUD stays fixed and the square cells retain their scale.
5. Background the app, close it and reopen it. Coins, dishes, chef progress, customer positions and meals resume from the saved state. Time spent away does not generate income in this ticket.

The displayed title and version come from `branding.json`; the artwork contains no game title. Android uses the full portrait surface. Wide desktop windows contain the same portrait room at its original scale.

## Evidence

These are captures of the actual Godot renderer, with observable snapshots stored in each directory's `manifest.json`:

| Behavior | Narrow phone, 320 × 720 | Wide window, 1440 × 1000 |
| --- | --- | --- |
| Starter layout | [Starter](phone/01-starter.png) | [Starter](wide/01-starter.png) |
| Walking customers | [Walking](phone/02-walking.png) | [Walking](wide/02-walking.png) |
| Meals in progress | [Eating](phone/03-eating.png) | [Eating](wide/03-eating.png) |
| Automatic service | [Service](phone/04-live-service.png) | [Service](wide/04-live-service.png) |
| Retained open endpoint and one held dish | [Backpressure](phone/05-full-open-belt-held-food.png) | [Backpressure](wide/05-full-open-belt-held-food.png) |
| Horizontal camera continuity | [Panned room](phone/06-continuous-room.png) | [Panned room](wide/06-continuous-room.png) |
| Shared art and native normal/pressed/disabled controls | [Gallery](phone/07-shared-components.png) | [Gallery](wide/07-shared-components.png) |

The backpressure capture uses the public entrance command to stop arrivals, so the initial open belt fills without silently discarding dishes. The gallery shares gameplay textures, font construction, anchor math and native controls.

## Validation

- 51 deterministic public-session checks: production, pathing, capacity, fixed-price sales, elapsed time and exact save continuation.
- 24 persistence checks: atomic saves, checksums, valid backups, domain validation and preservation of unrecoverable files.
- 56 native application checks: physical touch, fixed HUD, clipping, configured camera extent, real control states, save/reopen and recovery Retry.
- The native application suite also passes in visible 320 × 720 and 1440 × 1000 windows.
- Existing repository engine suite: 129 checks passed. Vite build passed. Existing Sushi Loop studio: 35 Playwright checks passed, including phone, wide and landscape pages.
- [Independent Standards and Spec reviews](code-review.md): all four findings resolved and independently verified after the fixes.

Final Android emulator checks at 1080 × 2400 passed real touch panning, unchanged background save bytes, update preservation, force-stop and reopen. Reopened state matched uninterrupted public-session simulation after 6.7 active seconds: coins 246 → 274 from exactly two 14-coin sales, with matching chef, customer, belt and random state. No runtime errors were observed. The exact signed release was installed and launched; it serves customers and is non-debuggable.

- [Android service](android/android-final-service.png), [touch pan](android/android-panned.png), [reopened room](android/android-reopened.png) and [signed release](android/android-release-service.png).
- [Lifecycle/continuation results](android/android-verification.json), [release results](android/android-release-verification.json) and [build fingerprints](android/release-build.json).

The release APK is 68,963,674 bytes. SHA-256: `2127003d9845567ac9aa39b0cef08b77b037a5e01d4d634aaf17ca16e7dbcae5`. All 52 recorded source/media fingerprints match this implementation. Drive readback confirmed the file size and MD5 `722505275ca2dc32d40305db62616819`; sharing permissions were unchanged.
