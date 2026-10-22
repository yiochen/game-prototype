# Sushi Loop HTML UI — Godot image export

Rendered directly from the approved HTML/CSS with transparent backgrounds, including the dark brown tab shadows. No image generation or whole-surface stretching is involved. The native Godot dock uses this export with native controls and dynamic text. The PNGs contain presentation only.

## Contents

- `png/1x/` and `png/2x/`: 26 assets at each resolution, with normal/pressed surfaces, selected cap, maple board/panel, walnut Shop, cream/red HUD pills, empty quantity badge, coin, brown row backdrop, fading waves and eight white icons.
- `connected-people`, `connected-layout`, `connected-floor`: blank board plus the selected cap, preserving the exact continuous grain and join. Other tabs, Shop and labels are separate overlays.
- `textures/`: original wood-grain and wave textures. `footer-waves.png` additionally includes the current CSS fade and uniform repeat.
- `svg/`: editable monochrome glyphs. Set their tint when importing, or modulate the white PNGs.
- `fonts/`: Nunito and its OFL license.
- `manifest.json`: exact PNG dimensions, SHA-256 hashes, face/control bounds, source hashes and renderer version, draw offsets, expansion and slicing margins.
- `preview.png` and `validation.json`: asset contact sheet and pixel-level export checks.

Labels, stock counts, the coin balance, item/chef artwork, hit targets and focus feedback are intentionally separate. Render text in Godot so values, localization and accessibility remain dynamic. The coin star is part of the coin emblem.

## Godot placement and sizing

The design canvas is **720 × 1280 logical units**. The 1x set maps one pixel to one design unit. Use a single uniform canvas scale, or use 2x with every layout coordinate, slice and text size scaled by two. Do not apply independent X/Y scaling.

Each image includes a **16-unit transparent gutter** around the normal face (32 px at 2x). This retains shadows and the baked two-unit press displacement. `face_rect` is `[x, y, width, height]` inside the PNG; it is the normal alignment reference even for pressed variants. Do not trim these files on import.

For a fixed-size `TextureRect` child, use the asset's `logical_size` and `draw_offset` relative to its native control. Set the artwork's mouse filter to Ignore. The control owns input, labels and icons. For example, `tab-normal` has a 208 × 78 control, a 208 × 60 face 14 units down, a 240 × 92 PNG, and a draw offset of `(-16, -2)`.

For a resizable `StyleBoxTexture` or `NinePatchRect`:

1. Read `nine_patch_margins_ltrb` from the chosen PNG variant; values are in **source texture pixels**, in left/top/right/bottom order.
2. Use `AXIS_STRETCH_MODE_TILE` horizontally for the center grain. For a two-axis panel, tile vertically too. Preserve the fixed corner strips. Use the manifest's `stylebox_expand_margins_ltrb` for decorative overflow beyond the logical control bounds, scaled with the entire UI. Set native content margins separately for its text/icon layout.
3. Capsule assets marked `horizontal_only_tile_center` retain their exported height. Their zero top/bottom slicing margins preserve the complete rounded end caps while allowing width changes; keep the vertical axis at the source height. Do not resize their height independently.
4. Assets marked `uniform_only` retain their aspect ratio. In particular, the three `connected-*` composites give the exact approved seam at the 720-unit board width. Use these for the simplest faithful implementation. Arbitrary board resizing with separately tiled caps requires matching the wood texture phase, as the HTML does.

Use the `*-pressed` texture at the **same bounds** as its normal texture. Its displacement and darkening are already baked; do not offset it a second time. The selected cap keeps the same surface on press; move only its native icon/label down two design units. For unavailable goods, the HTML dims the item art to 40% and badge to 70%; counts remain dynamic.

Keep Godot touch targets at least 44 screen pixels when adapting the compact artwork to a phone. The standalone images are decorative surfaces and do not encode safe-area handling, scrolling, gesture ownership or game behavior. Use lossless import; enable linear filtering for this smooth illustrated UI.

Reference: [Godot StyleBoxTexture documentation](https://docs.godotengine.org/en/stable/classes/class_styleboxtexture.html).

## Reproduce

From the repository root, with the project's Playwright Chromium installed:

```sh
node prototypes/sushi-loop/design/editor-dock-preview/export-assets.mjs
python3 prototypes/sushi-loop/design/editor-dock-preview/verify-export.py
```

The second command requires Pillow, verifies all PNGs, writes the contact sheet/report and creates the ZIP next to this folder. The exporter uses the current shared CSS and offline Layout HTML. If markup or glyphs in `app.js` change, regenerate the standalone screens with `build_assets.py` first. Original generated artwork remains untouched in `wood-v1`.
