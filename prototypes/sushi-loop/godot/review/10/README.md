# Ticket #10: operating starter restaurant

This review covers [issue #10](https://github.com/yiochen/game-prototype/issues/10) only, adapted to the user-confirmed Godot Android target. Later tickets have not been implemented. Shop, Edit and Staff remain visible but disabled until their own tickets are approved.

The visual revision follows the supplied [doodle catalog](../../../design/art-directions/doodle.png): elevated front/top artwork on a square grid, feet at tile centers, broad connected conveyors and a quiet drawn floor. Fifteen character clips contain six different drawings each, at least 445 native pixels tall. Smooth sampling preserves their detail at phone size. Sushi is drawn above the complete belt pass.

The conveyor starts as one connected strip. Each of its six surface phases is cut into the same four 502 × 460 regions: left cap, two center modules and right cap. The rails and supports stay fixed while the deck slats scroll. All tiles share phase and speed, so adjoining pieces stay connected during motion.

## Try the Android build

1. Install the [revised signed release APK in My Drive](https://drive.google.com/file/d/1esvJwG5976m8Mp_2psX4EKNtXk3n9IkG/view?usp=drivesdk), version **0.1.1**, code **11**. The Android package is `com.yiochen.sushilooptickets`; this APK can update the previous build.
2. Watch Mina prepare salmon nigiri, load the conveyor and begin her next dish. Customers arrive, walk to the three seats, eat and leave automatically.
3. Watch a completed meal add 14 coins once. Its local cue contains a coin icon without an amount label.
4. Drag the room horizontally. The HUD stays fixed and the square cells retain their scale.
5. Background the app, close it and reopen it. Coins, dishes, chef progress, customer positions and meals resume from the saved state. Time spent away does not generate income in this ticket.

The displayed title and version come from `branding.json`; the artwork contains no game title. Android uses the full portrait surface. Wide desktop windows contain the same portrait room at its original scale.

## Evidence

Watch the actual production renderer in [the motion preview GIF](animation/live-service.gif) or [the 24 fps recording](animation/live-service.mp4). [The six-frame registration sheet](animation/six-frame-registration.png) shows every character and belt clip, including foot crosses at tile centers. [The pixel audit](animation/art-audit.json) verifies unique drawings, unchanged structural belt pixels, and exact reconstruction of every strip from its cuts.

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
- 57 native application checks: physical touch, fixed HUD, clipping, configured camera extent, real control states, tile-center anchoring, save/reopen and recovery Retry.
- 296 artwork checks: six distinct drawings per clip, native resolution, fixed character scale, connected conveyor topology, exact joins, synchronized phases, mipmapped textures and sushi layering. **428 native checks passed in total.**
- The native application suite also passes in visible 320 × 720 and 1440 × 1000 windows.
- Existing repository engine suite: 129 checks passed. Vite build passed. Existing Sushi Loop studio: 35 Playwright checks passed, including phone, wide and landscape pages.
- [Independent Standards and Spec reviews](code-review.md): **0 remaining findings on either axis** for the doodle revision. The four original implementation findings were resolved and independently verified before this revision.

Final Android emulator checks at 1080 × 2400 passed real touch panning, unchanged background save bytes, update preservation, force-stop and reopen. Reopened state matched uninterrupted public-session simulation, including chef, customer, belt, camera and random state. The final package update preserved all 3,440 paused save bytes exactly. No runtime errors were observed. The installed package's SHA-256 matches the uploaded release; it serves customers and is non-debuggable.

- [Signed Android release serving customers](android/android-release-service.png), [touch pan](android/android-panned.png) and [reopened room](android/android-reopened.png).
- [Lifecycle/continuation results](android/android-verification.json), [release results](android/android-release-verification.json) and [build fingerprints](android/release-build.json).

The release APK is **86,054,904 bytes**. SHA-256: `794a88ed0fc95cb9553b1840b38fd40c81c757e12cfd8fdbcd63223671385fc3`. All **55** recorded source/media fingerprints match this implementation. [Drive readback](android/drive-verification.json) confirmed the file size and MD5 `53a51917f07f30d286cb373c1d3ec3fe`; sharing permissions were unchanged.
