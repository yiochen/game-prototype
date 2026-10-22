# Continuous maple editor — 0.4.12 / code 52

The approved HTML dock is now used by native Godot gameplay and the shared editor gallery. Shop has the same **60-unit face height and alignment as inactive Floor**, with the retained dark brown shadows. The active cap and board use the exact joined export; other categories remain detached. Quantities and labels are native controls over the exported surfaces. Goods fit the same visible alpha bounds as HTML, with transparent authoring padding excluded. Native starting inventory and existing saves retain their actual counts rather than the HTML fixture's sample values.

The horizontal strip clips goods inside the board rim and shows four complete Layout goods plus a continuation hint. Wheel and keyboard focus reach the rest. Touch waits for 10 physical pixels and 1.3× directional dominance: sideways motion owns scrolling; upward motion owns pickup. Ownership stays fixed until release/cancellation. Scroll offsets persist per category through the session/save boundary; legacy paging saves still load. Inspection, placement rejection, Rotate/Return, drawer collapse, pause/resume, save retry and the existing unavailable-Shop feedback remain native. The upper HUD and world artwork retain their existing presentation.

The 42-unit wave footer expands for the real bottom safe inset. The control row grows enough to retain 44px physical hit targets while the compact artwork retains its proportions. Exported corner strips scale uniformly and plain spans tile; the connected board/cap composites preserve their exact grain join.

## Android artifact

[Download the signed APK from Google Drive](https://drive.google.com/file/d/1pb3xaL-LHGNBGcpJLB6o7XuPzQm-WX5W/view?usp=drivesdk).

- Version: **0.4.12 / 52**, normal package `com.yiochen.sushilooptickets`.
- Release signer: `9b465ce9e19fc9cfb1a3a34c6fa2e1e452d3bfc9cb6adb5c01918c1fcfc061ed`, unchanged from earlier releases. The original private key was used directly from its existing signing directory; no key material is included here.
- APK: 235,394,636 bytes; SHA-256 `0e601ff525a202acaf0c1d6ecfe5d0ea76c93836c3ef41db0c631a19a50dd375`.
- The package audit verified arm64/x86_64 libraries, nondebuggable offline release settings, runtime manifest fingerprints and exclusion of authoring/private files.
- Drive metadata was read back and its size and MD5 match the local APK. Sharing permissions were not changed. See [upload verification](apk-drive-verification.json) and [build receipt](normal-build.json).

## Verification

- Full native suite passed, including 148 actual-app checks, 37 dock interaction checks, and inherited session, save, placement, sprite-picking, guest and art regressions. The actual-app suite retains the storage-failure/retry path.
- Rendered dock checks passed at 320×720, 390×844, 984×1224 and 1280×720. The gallery uses the same native presentation. Captures are below; these are desktop Godot renders, not physical Android screenshots.
- 66 Android packaging tests passed, including altered runtime PNG and stale CSS rejection.
- 193 repository engine tests, nine browser checks and the Vite build passed. Browser bounds checks confirm Shop and Floor surfaces share both height and Y position.
- HTML Mocklens delivery readiness: **PASS**, six states × four devices, with current UX and visual proofs.
- The APK's recorded runtime source hashes still match the checkout after export. Complete logs are in [checks/](checks/).

| Capture | Purpose |
| --- | --- |
| [Layout, phone](native/phone/01-layout.png) | Connected maple board, matching Shop, live circular counts and clipped fifth good |
| [People, phone](native/phone/03-people.png) | Three native chef previews and statuses |
| [Floor, phone](native/phone/04-floor.png) | Disabled swatch with complete caption and Current status |
| [Collapsed, phone](native/phone/05-collapsed.png) | Existing collapse behavior with connected cap/footer |
| [Shared editor gallery](native/phone/07-shared-editor-gallery.png) | Same native UI in the shared presentation |
| [Narrow phone](native/narrow/01-layout.png) | Compact artwork with at least 44px native input targets |
| [Wide portrait container](native/review-browser/01-layout.png) | Correct proportional geometry at the review viewport |
| [Landscape](native/landscape/01-layout.png) | Centered portrait containment |

Sources remain editable in the [HTML preview](../../../../design/editor-dock-preview/). The [PNG pack](../../../../assets/ui/editor/html-export-v1/README.md) includes 1x/2x images and slicing metadata. The native runtime stores exact 2x copies in `godot/assets/ui/wood-editor/`, verified by `godot/tools/verify_wood_ui.py`. All earlier generated source sheets, prompts and historical captures remain intact.
