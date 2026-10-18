# B/C native scale comparison — issue 33

Route: #character-scale-study. Two new editable native Blender designs, B Playful and C Chunky, at 100 / 125 / 150%, with all four directions. Front/side pairs share one tile pitch; the 3×3 layout uses the same registered sprites and roots. The existing ImageGen concept board is preserved as reference.

User constraint: full width and physical X/Y footprint inside one tile; head/hat may rise above it. All 24 native captures pass independent evaluated-vertex and actualcamera-matrix checks at ordinary35°. The widest case is C at 150%, 0.977 tile, within ±0.489 of its root. Fixed 192×448 logical canvas, root (96,368), source 4× RGBA, complete unclipped alpha. Root scaling is exactly 1.0 / 1.25 / 1.5. Geometry normalized through the inverse actualroot/facing matrices agrees across all sizes and directions.

Revision 2 follows the user's footwear feedback: bulky boots removed, tiny navy foot ends and minimal leg stubs. Previous bulky-boot source and four representative stills are retained under `iterations/`. No production asset, original source library or existing full scene has been replaced; issue 33staysopen for review. This is a static proportion/size study, not an animation validation.

Validation: 164 engine/helper tests pass; final production build passes in 3.15 seconds. All five existing restaurant/underwater browser checks pass, and three dedicated B/C checks pass on phone 390, landscape 844 and desktop 1440. The dedicated checks cover all 24 export links, native 4× dimensions, common frame/root, all facing pairs, shared display pitch, guides and 3×3 controls. The initial landscape test incorrectly expected offscreen lazy images to mount before scrolling; it was corrected to bring the capture into view, with no application workaround.

Additional actual-touch QA passes: a vertical swipe over the comparison scrolled the document 141 pixels and a horizontal swipe moved the comparison 152 pixels, with no nested vertical scrolling or page overflow. At the default 64-pixel tile pitch all three scale columns fit the 806-pixel desktop stage. Representative complete-table, phone and 3×3 screenshots plus the reproducible browser script are under browser/.

## Revision 3 — selected 125% and fuller hair

125% is selected and is now the default 3×3 layout size and highlighted table column. Both B/C received a rounded crown/back shell, layered overlapping curls, fuller temples/nape and softened native cheek/chin corners. Camera, original head extents, uniform scaling, tiny feet and costume stay fixed. At 125%, C is 1.576 tiles tall including hat and fits a 0.814×0.814 turning envelope.

All 24 revised captures pass the independent mesh/camera/alpha audit. The system Python initially lacked Pillow; the same audit passed with the bundled Python containing Pillow. The 164 engine tests, production build (2.98s), three responsive character browser checks and actual phone swipe checks pass. New screenshots/report/script are under hair-revision-browser. Earlier browser evidence remains versioned. The MCP front, side, back and three-quarter review caught scalp gaps in the first pass; the corrected final model covers them with the rounded back and curls. Original flat-hair and first-pass records remain under iterations/.
