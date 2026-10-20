# Noren optical alignment revision

Only the curtain pair is newly generated. The v6 materials, icons and complete-screen composition are reused with immutable generation receipts and SHA256 pins. The original raw output is retained in `raw/curtains.png`; see `curtains-prompt.txt` and `imagegen.json` for the exact prompt and references.

`face_px` measures a visible surface before its drop shadow. `ink_px` measures the opaque icon drawing. Both use coordinates relative to the atlas entry including its four-pixel gutter. Godot maps the face through the same nine-patch transform used to draw it, and shapes native label glyphs to align their actual ink.

The new loops have transparent apertures; the separate thicker cedar rod is drawn behind them. A 54-logical-pixel dock anchors the compact goods drawer. Category and caret backing surfaces are intentionally absent. Pill minimum height remains100 logical pixels.

Regenerate the deterministic atlas with the bundled Pillow Python and `pack.py`. No crop is repainted, resized or alpha-processed.
