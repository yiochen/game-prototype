# Sushi Loop — HTML UI

Open `/prototypes/sushi-loop/design/editor-dock-preview/` from the repository Vite server. This is the requested HTML review before a Godot port.

The complete visible UI uses HTML/CSS/SVG: the coin counter and coin emblem, cream Editing pill, vermilion Live button, continuous maple board, connected active tab, detached inactive tabs, walnut Shop capsule, circular stock badges, icons, text, borders, highlights and shadows. **Only `wood-grain.png` and `waves.png` are UI image backgrounds.** There are no baked button, panel, badge or HUD images, no border-image frames and no texture bridge covering the inventory. The board and selected cap share one grain origin; their CSS geometry overlaps by two design units to cover the top edge cleanly.

Native Blender goods and ImageGen chef headshots remain content artwork. Clean sky/wall/floor reference crops supply the restaurant illustration; the blue wall band under the HUD is CSS. The source crops exclude baked HUD pixels. All crops retain exact source pixels and provenance in `assets/provenance.json`; original generated sheets remain in `../../assets/ui/editor/wood-v1/` as history.

Switch People/Layout/Floor, scroll horizontally or with the mouse wheel, tap an item, drag upward for a visual pickup preview, and open Shop. Arrow keys or Home/End reveal inventory items. Escape cancels preview/selection or closes Shop. Horizontal touch scrolling cannot turn into pickup within the same touch. Releasing a pickup ends the visual preview; it does not place an object or edit a save. Shop has its existing Coming soon view and one Back action.

Live shows a read-only presentation with the inventory hidden. Editing or Escape restores the same category and scroll position. This is a UI mode preview; it does not run the game simulation. Coins remain the 7680 fixture and stock remains 5/1/2/2/2.

The approved v5 composition is retained with later user refinements: 78-unit selected caps, 60-unit Shop surface, a minimum 44px input row, 16-unit inventory clipping inset, and a 42-unit footer that expands for the real safe inset plus padding. Complete wave engraving repeats uniformly inside that footer and fades at the sides and bottom. The category row uses a translucent dark brown gradient, and inactive-tab depth is dark brown; the maple face highlights remain cream.

Review states: `?state=people`, `?state=floor`, `?state=out-of-stock`, `?state=shop`, and `?state=live`. `build_assets.py` rebuilds extracted content and six standalone files under `screens/` for offline Mocklens review; it requires Pillow. It removes only obsolete outputs from the earlier bitmap UI assembly, preserving the original source assets and historical evidence.

Validation covers six states at 390×844, 320×720, 984×1224 and 1280×720, nine browser interaction/layout/asset-contract checks on development and built output, 193 repository engine tests, and the Vite build. Mocklens evidence lives in `.mocklens/`. Four narrow inventory overflow suppressions document the intentionally clipped scrolling strip; no blanket page-error or clipped-text suppressions are used.

## Godot image export

`export-assets.mjs` renders the current CSS into transparent PNG components at 1x and 2x without labels or quantities. `verify-export.py` checks PNG dimensions, transparency, clipping, source hashes, tintable icons and slicing spans, then creates the contact sheet and ZIP. It requires Pillow. There are 26 assets per scale, including joined board/cap composites for all three categories and normal/pressed independent surfaces.

The pack is in [`../../assets/ui/editor/html-export-v1/`](../../assets/ui/editor/html-export-v1/README.md), with source-pixel nine-patch margins and logical draw offsets in its manifest. Capsules allow horizontal resizing at fixed height; composites retain uniform scale. See the pack README for Godot placement details and regeneration commands.

The approved dock has been ported to native Godot controls in `scripts/wood_editor_presentation.gd`, using the current export under `assets/ui/wood-editor/`. Existing HUD, world art, contextual actions and unavailable-Shop behavior are retained.

## Current UI portrait refinement

The People inventory uses the illustrated ImageGen family in `../../assets/ui/chef-headshots/v1/`. Historical source crops and exported native dock artwork remain preserved. Scene sprites retain their existing camera.
