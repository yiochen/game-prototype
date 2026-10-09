# Art and audio provenance

These assets were made for this game. Version **0.1.1** adds V2 painted production art based on the accepted [doodle reference](../../design/art-directions/01-doodle.png). The illustrations contain no game title; the product name belongs in live interface text and can be changed independently.

## V2 painted production art

The built-in image generation tool created original environments, character atlases, props, dishes, creatures and blank interface surfaces using the repository’s doodle study as style guidance. The artwork uses confident irregular ink contours, warm gouache color and restrained paper grain. Game state, dishes on the belt, characters, interface text, selection outlines and animations remain runtime layers.

The original generated PNGs and intermediate atlases are retained under `v2/`. See the [V2 sprite manifest](v2/SPRITES.md) for source images, dimensions, refinements and the mechanical extraction workflow. The [atlas metadata](v2/atlas-metadata.json) records measured crop rectangles and output sizes. Extraction preserves original color and alpha values and adds transparent margins; it does not repaint source images.

Generation records distinguish exact tool prompts from summaries:

- [Initial sprite prompts](v2/sprite-prompts.json): exact generation prompts.
- [Sprite refinement prompts](v2/sprite-refinement-prompts.json): exact edits bringing props and creatures closer to the accepted reference.
- [Customer pose prompt](v2/customer-poses-prompt.json): exact edit prompt for separate walking and chair-sitting guest poses.
- [Ocean art provenance](v2/ocean-art-provenance.json): exact environment and HUD panel prompts.
- [Restaurant, title and UI atlas provenance](v2/restaurant-art-provenance.json): originating-agent-confirmed summaries, explicitly **not verbatim** prompts.
- [Conveyor material provenance](v2/belt-art-provenance.json): exact seamless painted-belt generation prompt.
- [Outcome vignette prompt](v2/results-vignettes-prompt.txt) and [extraction metadata](v2/results-vignettes-metadata.json): exact prompt and measured crops for the distinct complete, early-return and repair illustrations.
- [Launcher icon prompts](v2/icon-prompt.json): exact initial composition and safe-area refinement prompts, input image roles and source paths. The finished opaque painted submarine icon is `v2/icon.png`, copied to `icon.png` for Android launcher/splash export. It has generous cream margins for Android icon masking and no baked-in title.

Source atlases, initial atlas revisions, extraction scripts, sprite documentation, prompt/provenance records and extraction metadata are retained in the repository but excluded from the Android export. The APK uses the separate production sprites and environment textures.

The runtime prefers V2 PNGs when available and retains the SVG assets below as fallbacks and supporting illustrations. No title is baked into either set. The Android app and web introduction read the visible name from `branding.json`.

## Original SVG fallback library

`../tools/generate_assets.py` is the editable, deterministic source for every SVG here. The line art, silhouettes, characters, environment props and compositions are original vector artwork, following the project's accepted doodle direction: warm ivory, coral, mustard, mint and rounded dark ink. No stock illustrations or extracted reference-image pixels are used.

- `chef.svg`, `customer_1.svg`–`customer_4.svg`: 256 × 256 character sprites.
- `cucumber.svg`, `salmon.svg`, `shrimp.svg`, `eel.svg`: 256 × 256 dishes on porcelain plates.
- `submarine.svg`: 160 × 256, nose upward, transparent background.
- `creature_salmon.svg`, `creature_shrimp.svg`, `creature_eel.svg`: 256 × 160 encounter creatures.
- `customer_walk_1.svg`–`customer_walk_4.svg`: 256 × 256 standing guests without chairs or plates, for runtime walking animation.
- `crate.svg`, `rubble.svg`: 256 × 256 warm construction clutter for uncleared restaurant cells.
- `gear.svg`, `rock.svg`, `portal.svg`, `plant.svg`, `lantern.svg`: 256 × 256 props.
- `title_vignette.svg`: 506 × 432 welcome art matched to the title-screen illustration slot.
- `results_complete.svg`, `results_early.svg`, `results_failed.svg`: 720 × 1280 distinct full-screen outcome art; x75–645/y360–960 is reserved for live receipt UI.
- `cover.svg`: 720 × 1050 welcome illustration without any baked-in title.
- `ocean_background.svg`: 720 × 1280 ocean environment with a quiet center.
- `icon.svg` and `icon-prototype.png`: earlier deterministic icon, with a 512px Inkscape render preserved for provenance. The Android app now uses the V2 painted icon described above; `icon.png` is its export copy.
- `contact-sheet.svg` and `contact-sheet.png`: development-only visual review sheet.

SVGs are imported by Godot as native texture assets. Transparent sprite areas remain transparent. All painted outlines are rounded and deliberately restrained to stay readable on a phone.

## Original sound

The V2 art update keeps the existing original audio. All WAV audio is synthesized by `generate_assets.py` using original note sequences and envelopes. There are no sampled recordings, copyrighted songs or downloaded effects. Output is 22,050 Hz, 16-bit stereo PCM.

- `restaurant.wav`: original 16-second toy-jazz loop, warm plucked keyboard, bass and quiet brush percussion.
- `ocean.wav`: original 16-second marimba/bell loop with a soft bass and understated water-like timbre.
- Effects: `click`, `coin`, `build`, `upgrade`, `splash`, `sonar`, `harpoon`, `hit`, `catch`, `win`, `warning`, `boost`.
- Semantically named aliases: `ui` → click, `pickup` → coin, `shot` → harpoon, `hook` → build, `portal` → sonar.

Music files contain exactly 352,800 sample frames (16s). Their trailing note energy is wrapped into the beginning by the generator for a continuous repeat. Set `AudioStreamWAV.loop_mode = AudioStreamWAV.LOOP_FORWARD`, `loop_begin = 0`, `loop_end = 352800` for music. Sound effects should not loop.

## Fonts

Fonts were downloaded directly from the official [Google Fonts repository](https://github.com/google/fonts). Their full SIL Open Font License notices are included beside the font files.

- `fonts/Body.ttf`: **Nunito** variable font, copyright the Nunito Project Authors. Source: https://github.com/google/fonts/blob/main/ofl/nunito/Nunito%5Bwght%5D.ttf — license: `fonts/Body-OFL.txt`.
- `fonts/Display.ttf`: **Delius Regular**, copyright Natalia Raices. Source: https://github.com/google/fonts/blob/main/ofl/delius/Delius-Regular.ttf — license: `fonts/Display-OFL.txt`.

The bundled font binaries are unmodified, and the license permits bundling and commercial use under its stated terms. `fonts/Body.ttf` and `fonts/Display.ttf` are filenames; internal font names have not been changed.
