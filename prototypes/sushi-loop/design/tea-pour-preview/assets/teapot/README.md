# Teapot (ImageGen) for the #62 pour view

1. `gen1-raw.png` — `sprite-gen gen --provider codex --model gpt-5.6-sol`, prompt `prompt.txt`, style reference
   `../../../cash-preview/assets/restaurant-live.png`. Good teapot, but on black with a glow (`gen1-report.json`).
2. `teapot.png` — edit of `gen1-raw.png` with `prompt-edit.txt` onto flat magenta, chroma keyed (`report.json`;
   raw kept as `teapot.png.raw.png`). 1536x1024, visible bounds x 209–1308, y 185–877.
3. `../teapot-pour.png` — crop of `teapot.png` at (180, 160, 1160x741), resized to 316x202 (2x of 158x101 display).
   Pour pivot (spout lip): source (215, 400) → display (4.8, 32.7).
