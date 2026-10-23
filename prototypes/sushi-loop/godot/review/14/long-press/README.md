# Long-press pickup — issue 14 amendment

The user's feedback supersedes the original standing/trapped-only restriction. This update extends the existing customer-recovery branch and keeps issue 14 open for Android verification. The [interaction contract](contract.md) records the accepted composition and state inventory. The previous 0.6.0 evidence remains historical.

## Try it

- In **Edit**, hold a guest's visible body for **400 ms**, then drag. This works from People, Layout or Floor, including an ordinary walking guest, an eating guest on a stool and a visitor waiting at the entrance. Dropping a seated guest on clear floor leaves their stool behind. Their appearance, preference, fullness and unfinished meal remain with the same visit.
- Hold an unselected **stool, chef, conveyor or decorative object** to pick it up directly. An occupied stool carries its guest; a loaded conveyor carries its exact plate and unfinished transfer clock.
- **Single tap** still selects an object for **Rotate / Return**. A Layout tap on an occupied stool's guest selects the stool; a hold on the guest picks up the guest. Bare stool pixels remain a separate hold target.
- The lifted production sprite follows the finger continuously with its grab offset and a small fixed lift. A snapped green/red floor footprint shows drop validity. Its original silhouette is hidden during pickup. Context menus and conveyor path targets hide during the lift.
- **After dropping an object, it stays selected and its context menu returns immediately.** Guests have no Rotate/Return menu. Existing tap-then-drag movement remains available.
- Movement beyond **10 physical pixels before pickup** owns panning. A pan cannot become a late hold. Invalid/canceled drops, interrupted touches, backgrounding and focus loss retain the prior arrangement. A stationary hold/release selects without moving the object or detaching conveyor connections.

All service clocks and RNG stay paused in Edit. A manually admitted door visitor chooses their first preference after seating in Live; moving them does not invent an arrival, meal or sale. The extended customer-layout save format accepts earlier saves and preserves pending manual admissions, including departure before their first seating.

## Native captures

Actual Mobile/Metal rendering and production viewport touch dispatch pass at **320×720**, **390×844**, **984×1224** and **1280×720**. Each directory contains 13 full-scene captures and a `verification.json` with the actual renderer/driver and failures. Existing B/maple controls and registered sprites are reused without new artwork. Shared presentation and reduced motion use the same pickup path.

| State | Narrow phone | Wider portrait containment |
| --- | --- | --- |
| Pending hold | [Before pickup](320x720/01-pending-guest-hold.png) | [Before pickup](984x1224/01-pending-guest-hold.png) |
| Eating guest lifted off stool | [Picked up](320x720/02-seated-guest-picked-up.png) | [Picked up](984x1224/02-seated-guest-picked-up.png) |
| Continuous tracking | [Dragging](320x720/03-continuous-guest-drag.png) | [Dragging](984x1224/03-continuous-guest-drag.png) |
| Invalid guest drop | [Invalid](320x720/05-invalid-guest-drop.png) | [Invalid](984x1224/05-invalid-guest-drop.png) |
| Occupied stool picked up | [Carried guest](320x720/06-occupied-stool-picked-up.png) | [Carried guest](984x1224/06-occupied-stool-picked-up.png) |
| Dropped object stays selected | [Rotate / Return](320x720/07-dropped-stool-context-menu.png) | [Rotate / Return](984x1224/07-dropped-stool-context-menu.png) |
| Chef pickup | [Chef](320x720/08-chef-picked-up.png) | [Chef](984x1224/08-chef-picked-up.png) |
| Ordinary walking guest | [Walking guest](320x720/09-ordinary-walking-guest-picked-up.png) | [Walking guest](984x1224/09-ordinary-walking-guest-picked-up.png) |
| Shared / reduced motion | [Shared](320x720/10-shared-reduced-motion-pickup.png) | [Shared](984x1224/10-shared-reduced-motion-pickup.png) |
| Loaded conveyor pickup | [Same dish](320x720/11-loaded-belt-picked-up.png) | [Same dish](984x1224/11-loaded-belt-picked-up.png) |
| Dropped conveyor menu | [Selected belt](320x720/12-dropped-belt-context-menu.png) | [Selected belt](984x1224/12-dropped-belt-context-menu.png) |
| Decorative object pickup | [Plant](320x720/13-plant-picked-up.png) | [Plant](984x1224/13-plant-picked-up.png) |

Full-scene inspection confirmed readable shared controls, retained portrait containment in landscape, the same carried dish, continuous lifted poses and restored object menus. Diagnostic timing includes scripted captures and concurrent build work; it does not measure Android performance.

## Validation

- **21 native suites pass**, including **121 customer-layout/save checks**, **42 long-press touch checks**, the existing 31 customer-recovery touch checks, 185 editor checks and 148 actual-app checks. The hold suite covers the exact threshold, pre-hold pan, actual frame-loop timing, opaque sprite ownership, valid/invalid/canceled/interrupted drops, carried food, saved selection, Live exclusion and reduced motion.
- All **42 hold checks pass visibly at each of four capture sizes**, producing 52 captures.
- **66 Android packaging checks**, **41 relevant browser checks** and the **Vite production build** pass.
- The complete JavaScript run has **200 passes / two existing missing art-archive failures**. See the unchanged [baseline failure record](../baseline-test-failures.json).
- [Verification audit](verification.json) and [logs](checks/) record this run. All tests use an isolated save identity; the normal app's saved data is not accessed.

## Android update

Release **0.6.1 / code 59** keeps the original pinned release signer, normal package/save identity, nondebuggable offline settings and Mobile/Vulkan configuration with OpenGL fallback disabled. See the [build receipt](normal-build.json) and [source/signing verification](runtime-verification.json).

[Download the signed 0.6.1 APK](https://drive.google.com/file/d/151QBbpBjPe_oX9QCPAeHqirYYLahHebz/view?usp=drivesdk) (246,571,576 bytes). SHA-256: `6e87781b28e60112741ce4360b0758095a001fb5707bf7faa9d4d48d32f1db47`. [Drive readback verification](drive-upload.json).

**Android phone verification remains pending:** no device is attached. Native Mobile/Metal captures do not establish Android Vulkan graphics behavior. The previous separate 0.6.0 review APK remains historical; this amendment delivers the normal signed update.
