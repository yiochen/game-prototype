# Ika nigiri dish art · issue #70

The Inkfin Cuttlefish's recipe picture. **Approved** by the user on 2026-11-11.

- `ika-nigiri-v1.txt`: the exact prompt. Style reference: `godot/assets/ui/recipes/food.png` (the existing dish sheet).
- `ika-nigiri-v1.png.raw.png`: the full original ImageGen output (native alpha). `ika-nigiri-v1-candidate.png` is the same image.
- `ika-nigiri-v1.report.json`: provider, model (`gpt-5.6-sol`) and session. Its chroma-key step is not used: the output came back with real transparency rather than the requested green, and keying erased it.
- `food-v2.png`: the dish sheet with the Ika nigiri in its sixth cell, scaled uniformly to the salmon nigiri's width. The other five cells are the pixels of `design/recipe-picker-preview/raw/food.png`, which stays unchanged. This is the source of `godot/assets/ui/recipes/food.png` (see its manifest).
