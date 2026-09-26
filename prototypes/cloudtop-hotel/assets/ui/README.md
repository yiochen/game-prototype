# Origami UI material

`origami-paper.png` is the original generated transparent cardstock surface.
`origami-paper.webp` is the browser delivery version, encoded at quality 0.9
with the original dimensions and transparency. Only the WebP ships in the game.

The surface is a square with quiet paper in the middle and folded geometry at
the corners. `paper-ui.css` draws it with `border-image-slice: 25% fill`:

- Four corner regions retain their on-screen dimensions.
- The four edge regions stretch along one axis.
- The center region fills the remaining rectangle.

`--paper-corner` controls the visible corner size in CSS pixels, independently
of panel width and height. Large panels use 25–43px corners; controls and HUD
actions use 13–19px corners. `--paper-tone` tints only the paper artwork,
never the text or portraits. The title, guestbook sheet, score form, prominent
buttons, six dialogs, purchase receipt and completed-hotel panel use this material.

Cards and their layered backs retain the original six-frame `card-paper.webp`
atlas, including its distinct colored frames. HUD labels use `hud-tab.webp`.
Guestbook rows are printed directly on the sheet, portraits and the coin seal
are circular, and utility controls stay simple. The explicit surface allowlist
in `paper-ui.js` keeps this variation from being overwritten by shared styling.

For an opening surface, `paper-ui.js` temporarily renders two clipped leaves,
each containing the same full nine-slice skin. Each leaf pivots at the center
crease on its own 3D hinge. A vertical crease opens the guestbook and buttons;
a horizontal crease opens the title, dialogs and form. Content
fades in after the fold begins; its typography is not scaled or skewed.

Closing, navigation, reduced motion, hidden tabs, detached elements and hot
reload settle and remove the temporary leaves. They are inert and hidden from
assistive technology, and cannot commit a purchase. Cards use their original
quick deal-and-settle animation, preserving the illustrated card material.

## Generation

Generated with the built-in image tool using the existing `hud-tab.webp` as a
material reference. Prompt:

> Production nine-slice UI background for Cloudtop Hotel. One square blank
> warm ivory origami cardstock panel, orthographic, almost flush to the canvas.
> Four angular triangular folded corners with lighter reverses, geometric crease
> facets, thin layered beige edges and subtle shadows from the top left. Quiet
> opaque fibrous paper in the center, straight stretchable edge middles, true
> transparency outside the clipped silhouette. Keep folds in the corner regions.
> No text, icons, nails, ornate frames, checkerboard, grid or sample UI.

The original generator output is retained unchanged. Encoding changes only the
delivery format; coloration and nine-slice composition happen in CSS.
