# Independent native and capture audit

The frozen project with SHA256
`c02e04d6c90e34afce2b0895328d4a1e26d47817ce9d38fb2b458fa3e766fc1f`
passes the independent native audit: 104 objects, 525 used materials and 2,580
evaluated pose/facing combinations. See [the measured report](independent-native-audit.json)
and [the read-only audit recipe](audit_saved_native.py).

The saved scene has its own 135% sRGB compositor, with Render Layers alpha
bypassing the RGB grade. Every used surface ends in emission or the intentional
transparent 2D image mixture. World strength and all light energies are zero.
Environment cameras retain the 128-pixel ground pitch and 89.6-pixel vertical
unit. Concept decorations remain below three complete projected tiles in every
sampled facing; the largest measured silhouette is approximately 2.585 tiles.

The audit checks every frame of the concept decoration, car clearance and dock
cover animations, plus first/middle/last frames of the other native clips in
all declared facings. The car and folding cover required larger fixed canvases;
the final canvases contain the complete measured motion. Floors intentionally
overrun their opaque panels by less than half a logical pixel to prevent clear
antialiasing seams.

[The image-level audit](audit_capture_pixels.py) independently checks every raw
frame as each object finishes capturing. It verifies fixed dimensions, missing
frames, alpha touching capture edges, and at least six distinct visible RGBA
images for each animated clip/facing. Fully transparent RGB is zeroed for hashing
so invisible color noise cannot count as a distinct animation frame. Floors are
exempt from transparent edge margins. This process never edits a source image.

The final [pixel report](independent-pixel-audit.json) is `state: complete`, with
104 completed assets, **9,390 frames**, zero issues and `passed: true`. Every
native animated clip/facing has at least six distinct visible frames. The
initial 43-object, 260-frame subset is retained separately in
`independent-static-pixel-audit.json`.

These structural and image checks do not substitute for the user's visual asset
approval or close issue 33.
