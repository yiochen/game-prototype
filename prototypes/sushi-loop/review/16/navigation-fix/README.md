# Issue 16 — People tray and Edit navigation correction (0.8.1 / 68)

User feedback supersedes the 0.8.0 Live Staff flow: People in Edit is the only roster entry, Applicants belongs inside the existing tray, and the main screen has no Staff button or separate roster panel. The approved maple materials, independent photos, applicant fan, stamp animation and details remain unchanged.

The reported navigation failure was reproduced before the fix: after visiting and closing Live Staff, the category rail parent and Live button retained one-way hidden state. The content cache also could treat Live Staff and Edit People as identical despite their different view roles. The reproducing native touch run failed two visibility checks; its actual broken screen is retained under `before/`.

The redundant view is removed, including its state, parent panel, main button and input shield. Edit now owns the usual category rail and Live visibility. Applicants and the dynamic count are children of the People tray, above the clipped photo rail on its continuous maple backing. Their bounds do not overlap the photo strip; Applicants retains a 44px physical target. Existing People scrolling, placement and unread acknowledgements use the same saved Edit state.

Native touch validation passes 35 navigation checks on both 320×720 and 1440×1000 Mobile/Metal windows, covering repeated tab changes, collapse/reopen, modal dismissal, return to Live and clock resumption. The integrated hiring suite passes 35 checks, the wood inventory suite passes 37, and the general native app suite passes 145. Full-scene hiring/Shared captures under each size's `hiring/` directory show the final roster entry, absence of Staff on Live, and retained confirmation/disabled/unread states.

The signed release uses version 0.8.1 / code 68 and the original package/save identity/signer. Texture quality and architecture selection are unchanged from 0.8.0; this update addresses navigation and the requested roster composition.

Release delivery: the signed 0.8.1 / 68 APK was installed with `adb --no-incremental -r` on Pixel 10 Pro, preserving data. Package readback confirms the version. A separate native desktop demo was opened in a 450×800 Godot window using its own demo save identity. The Drive upload's name, byte count and SHA-256 were independently verified; observed metadata is in `drive-release.json`.
