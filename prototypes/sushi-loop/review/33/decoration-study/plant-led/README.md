# Vegetation as the main subject — review study

User request: “I think the coral and kelp should be larger. Instead of just as decors of rock. They should sometimes be the main thing”.

The native Blender study now alternates plant-led and rock-led compositions. Coral is a five-colony/five-sponge thicket in pink, amber and purple; kelp is a seven-clump grove with 21 staggered, volumetric fronds. The shared rock footprint stays broad, but its native support height is only 0.18 tiles for these two pieces. Plants are constructed at their own widths and heights; no rendered image is stretched or fitted. Native rock-led plant accents are enlarged by 1.18× in height and width, with roots sampled on their actual support surfaces.

| Piece | Composition | Native rock height | Mixed view vertical rise | Maximum rise across profiles |
| --- | --- | --- | --- | --- |
| Blue coral shelf | rock-led | 0.93 | 0.94 | 1.09 |
| Coral thicket | coral-led | 0.18 | 0.83 | 0.97 |
| Kelp grove | kelp-led | 0.18 | 1.58 | 1.58 |
| Decorated cobalt crag | rock-led | 2.81 | 2.91 | 2.91 |
| Ruin garden | rock-led | 1.74 | 2.00 | 2.00 |

All 41 high-resolution registered captures pass the independent native audit. Besides footprint/camera/height/front-edge checks, plant-led pieces must have low supports (<0.35), vegetation extending over 0.7 tiles in both ground axes, plants over three times the support height, and >60% visible vegetation color in every capture. Observed: coral 61–70%, kelp 63–72%. This last measure uses the known study palette to distinguish plants from blue rock; it is a visible color-area check, not a claim about gameplay collision or botanical realism.

The saved scene has 44 emission materials, zero lights and zero world illumination. Rock color uses Z-based shading; no world azimuth enters the capture. Material inspection is bound to the project and recipe hashes. The experimental 35° upper view/square footing remains available, with 70% oblique floors and a selectable all-70% alternative. The short coral thicket selects 70% in Mixed mode; kelp, crags and ruins select 35° upper views. Camera choice is based on the whole reference silhouette, while card labels report vertical rise only.

Evidence: phone/landscape/desktop mixed patches, all-70% patches and shoreline screenshots; 164 engine tests; production build; three responsive browser tests. Existing concept art and historical studies remain accessible. The editable `assets/decoration-study/decoration-study.blend`, recipe, logical meshes, actual capture geometry and receipts are committed with this study. Existing production sprites/full scene assets are not rolled out. Issue 33 remains open for visual approval.
