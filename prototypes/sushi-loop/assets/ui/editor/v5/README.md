# Indigo noren & warm ceramic — production UI family

The user selected [B's complete-screen composition](../v4/raw/b-indigo-ceramic.png). This coordinated family supplies every interactive and passive editor surface: primary/secondary/disabled controls, cloth category rail and tabs, item/profile mats, neutral stock badges, contextual actions, drawer, inspection/recovery panels and rejection feedback.

Two **built-in ImageGen** calls created [the full surface sheet](raw/surfaces.png) and [the full icon sheet](raw/icons.png). Both used the accepted B composition and unchanged Restaurant UI & item catalog. The icon call also received the actual generated surface sheet. The world concept is recorded as context, rather than claimed as a directly supplied generator input. Exact prompts, roles, reference hashes and original full-output dimensions are retained in [imagegen.json](imagegen.json).

## Resizing and geometry

Large surfaces use nine-patch rendering. [authoring.json](authoring.json) separates source-pixel corner slices, logical destination edges and symmetric content insets. Godot's shared `ui_skin.gd` keeps each corner uniformly scaled while extending only documented plain center/straight-edge spans. This avoids treating source image pixels as physical layout padding.

The cloth rail is separate from the cream drawer. Icons retain their aspect ratios. The contextual capsule's pointer is a separate fixed-proportion sprite, and its two action hit areas share one authored background. The stock badge has its own circular registration. Dynamic text, names, counts, active state and accessibility labels stay in Godot.

## Reproduce and verify

Run `pack.py` with a Pillow-enabled Python. It copies the measured source rectangles unchanged into one RGBA atlas, adds four transparent sampling pixels around each item, and writes the runtime manifest plus source/calibration record. It does not repaint, threshold alpha, resize, recolor or synthesize artwork. Fixed crop rectangles exclude neighboring low-opacity sheet fringe; the full originals remain intact.

`godot/tools/verify_editor_ui.py` independently decodes source/atlas PNG pixels with the Python standard library. It verifies the accepted composition and reference hashes, exact source crop pixels, transparent gutters, nonoverlap, all 17 surface/16 icon identities, symmetric insets and uniform corner scale. The source record, complete authoring input and packing script are separately hashed. Native captures remain necessary for visual review.

The runtime atlas and manifest are the only shipped editor image payload. Raw source sheets, prompts, concepts, test fixtures and authoring tools stay outside the APK. Version 1 remains historical; versions 2/3 are rejected studies and are not runtime inputs.
