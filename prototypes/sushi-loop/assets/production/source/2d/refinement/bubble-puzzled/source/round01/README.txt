Bubble-puzzled existing native2D round01

Editable source: bubble-puzzled.png (624x561 RGBA); exact frozen raw input:
resources/target.png. PNG is an editable raster source, not a Blender model.
The raw original source and original publisher/atlases are preserved under
resources/original-source, original-2d-pipeline, original-atlases. All original
resource hashes are in provenance.json. The sole prepared crop is declared in
crop.json; full raw source and target bytes remain unchanged.

Portable reproduction requires Python3 with Pillow (tested Python3.12.14,
Pillow12.3.0). From any location preserving object-relative source/round01/:
  python3 source/round01/prepare_sources.py
  python3 source/round01/publish.py
Publisher reads only its own declared source/round01 closure. It regenerates
36 RGBA captures,3 atlases, manifest and previews. Run verify.py after original
publication to copy this closure into an unrelated temporary folder and compare
all generated frame/atlas/metadata/preview/delivery bytes exactly. Verification
requires no inputs/, reviews/, production/ or sibling object.

Actual Godot evidence: resources/native-capture/. Captured using current copied
RestaurantView _customer_at/_feedback_at and ArtBook methods, original customer
stand atlas and candidate atlases, attachment(0,-172) with nonzero(.06,-.02)cell
pose offset. Native playback is48frames at12fps /4seconds. Isolated harness
project is generated under candidates/round01/native-context/. To recapture on
a Godot-enabled window renderer: run publish.py then capture_native.py, then
publish.py and verify.py again before sealing. Source-closed saved native PNG
and APNG evidence is copied verbatim on portable publisher replay.

This is an isolated consumer capture, not a production-game screenshot. The
legacy-catalog-90 image separately shows historical seated-wait/stool placement.
No production scripts/gameplay or other objects were edited by this publisher.

Alpha inspection: threshold>8 selects one crop rectangle only. All RGBA inside
it is untouched.378 outside nonzero pixels(maxalpha7, alpha-weight861) are
omitted by the original bounds policy; raw target is retained. This is not a
claim that every raw alpha>0 pixel enters the packed cutout. Normalized source
has one connected support at alpha>0 and>8. Standard original LANCZOS/opacity
rounding creates tiny alpha1-2 detached support samples in some animated
frames; these are measured in alpha-support-audit.json and not repaired. All
frames have one alpha>8 component and zero frame-border alpha. The independent
judge determines visible outcomes and approval; this delivery makes no rating.
