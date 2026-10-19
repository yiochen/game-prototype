# C125 production character revision

All eight chefs and four customers now share the approved C / Chunky revision 3 anatomy at actual uniform 125% native root scale. Identity-specific skin, hair color/style, facial hair/glasses, costume, accent and hat remain independent. The broad head has an eight-segment native bevel and rounded cheeks/chin. Rounded crown/occiput plus overlapping locks replace box caps. Trouser stubs and tiny navy toe ends replace boots/cuffs/soles.

Native armatures, weighted continuous sleeves/legs, world-root-local goals and analytic two-bone motion remain editable. The shorter legs use a matching .225-cell world travel per complete walk cycle; panic runs two cycles. Ground stance moves rearward relative to canonical front (−Y), preserving the previous moonwalk correction. Production orchestration exports twelve distinct poses at 12 fps for each animated clip. The builder's historical standalone clip durations are retained; this audit samples the twelve production phases explicitly.

Seating uses the 70% environment height rule: the unscaled character contact plane is `environmentZ × .70 / (1.25 × cos35°)`. Ground roots stay fixed. The customer pelvis offset is .080 native cells above that contact plane.

Every held dish is now the actual ImageGen transparent sushi cutout, including its plate. It is a fixed 2D image plane, not modeled sushi. The original alpha rectangle is registered once, with a .35-world-cell width and the lowest plate pixel attached to the evaluated palm midpoint. A native yaw-cancellation driver keeps the image facing the player in every character direction. A .60-cell camera-ray depth offset resolves body occlusion without moving any projected pixel. This flat render plane has no physical ground footprint; the audit separately checks its complete projected width and the physical body/knife ground bounds. Cooking knives remain native props.

`character-audit.json` records evaluated geometry across all twelve identities, every clip, twelve production sample phases and all four directions, along with source hashes. The maximum complete silhouette is **1.592526 projected tiles**. Maximum turning width/depth is **.901955 tiles**. Native body and knife remain inside root-centered ±.5 X/Y; flat plates also remain inside the one-tile projected width. Planted ankle goal error is below .00000014 cells; walking/panic ground-stance goal error is below .00000025 cells. The gait pelvis stays at .141±.001 native cells, preserving short-leg reach throughout the step. These checks establish geometry/registration, not final visual approval.

The sixteen direct Blender preview PNGs show Lena holding a salmon plate, Ellis cooking with a knife, Rosa walking and June eating cucumber rolls, each in all four directions. They use the shared native135 compositor and height-based lower tones, with zero world/directional lighting. Their 192×320 logical frame, root (96,248), 128-pixel cell and ordinary35° square-pixel camera are fixed; PNGs are rendered at2×. The revision3 held-plate width is .35 cells: the direct .40/.35 native comparison showed that .40 still touched the eye line during peak loading, while .35 leaves both eyes readable. Eating continues to reach the mouth. Core C125 anatomy, rig, gait and the exact palm midpoint support remain unchanged.

Reproduce from the repository root without touching the active Blender project:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup \
  --python prototypes/sushi-loop/assets/production/source/blender/catalog_character_revision.py \
  -- --out /private/tmp/s33-c125-review --with-props --render-previews
```

The editable production project and full baked captures are managed by the main asset rollout. Issue #33 remains open for the user's review.
