# Issue 12 — approved continuous maple inventory dock

The user approved `design/inventory-tray-concepts/v5-connected-tabs/full-screen.png` in this conversation and requested implementation. This supersedes the indigo curtain, ceramic inventory-card and paging-caret composition for this editor revision. Continue issue #12 only.

The user subsequently requested HTML assembly before continuing the port. Review `design/editor-dock-preview/` first. That review is approved; the user now authorizes the native port and Android build. Historical experiments and original sources remain preserved.

The latest user instruction replaces bitmap UI surfaces with HTML/CSS geometry,
using only wood grain and waves as background textures. The HTML reference now
builds the complete HUD, board, category surfaces, Shop, badges and icons in
code; the earlier nine-patch panel/button atlas is historical. The subsequent export request authorizes exact transparent PNG renders of this CSS geometry for native controls. Native merchandise and restaurant illustration remain art.

- Use a continuous maple board through the bottom safe area, with the approved quiet carved waves. Place interactive content above the actual mobile bottom inset.
- Join the active category seamlessly to the board. Inactive categories remain detached. Shop is a separate walnut action capsule, never a category toggle. Preserve the existing unavailable-Shop behavior until its feature ticket is implemented.
- Keep native dynamic category names, item captions and circular quantity badges separate from the coordinated ImageGen surfaces. Reuse existing Blender goods and registered world sprites.
- Replace paging carets with a horizontally clipped inventory strip: four complete Layout entries and a hint of the fifth. Mouse wheel and keyboard focus must reach all items.
- Resolve tray touch intent after a scaled movement threshold: horizontal movement scrolls; clearly upward movement picks up a usable item. Keep that owner through release. A scroll cannot arm, place, select, pan the room, or alter the simulation. Preserve taps, invalid-drop recovery, pause/save contracts and system Back.
- Retain all previous generated sources. The new HTML export family is independently registered and verified alongside the inherited HUD/modal family, including exact source PNG hashes and uniformly calibrated corners.
- Latest HTML review requests compact 78-unit category caps, a 60-unit Shop surface with uniformly smaller corner artwork, at least 44px input targets, inventory clipped inside the board rim, and a 42-unit decorative footer that expands for the actual safe inset. Carry these proportions forward after HTML approval; they supersede the older 100-unit decorative pill minimum for this dock family.
- Verify actual native normal/pressed/selected/disabled states, narrow phone and wider portrait containment, plus the shared editor gallery. Provide rendered captures and the Android build for user verification.

The user now authorizes exporting the CSS geometry as transparent PNGs and porting it to Godot, then building and uploading the Android APK. Shop matches the inactive tab face height and vertical alignment (60 units). Use the current HTML export and retain its dark brown shadows. Dynamic text, gestures and safe areas remain native.
