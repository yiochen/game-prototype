# Native B/C character proportion and scale study

This independent Blender study compares B Playful and C Chunky at actual uniform native scales 100%, 125%, 150%, in four cardinal directions. It does not replace any of the125production assets. No animation is included.

The saved ImageGen board under design/art-directions/character-proportions-v1.png establishes identity and proportion directions. Both new models retain Lena’s skin, curls, cream chef toque/jacket, red scarf and blue apron. C has a wider, deeper head, fuller belly/back and shorter legs. The user rejected the original boots: revision 2 introduced tiny navy toe ends 0.043 cells high, no boot shafts/cuffs/stacked soles, and native leg stubs. The upper body is lowered0.15cells with no scaling of its component proportions. The superseded source and representative stills are retained in review/33/character-scale-study/iterations/.

All 24 RGBA PNGs are direct 4× Blender captures (768×1792). The ordinary 35° camera uses square pixels and horizontal pitch 128 logical pixels/cell, fixed 192×448 frame and root (96,368), across both models/scales/facings. The model root supplies actual 1.0 / 1.25 / 1.5 uniform scaling. No finished sprite is squashed, fitted to alpha or cropped. Full horizontal silhouette and all native X/Y vertices stay inside the root-centered 1×1 cell in every case; height is allowed above the tile as confirmed by the user. The manifest’s footprint is a conservative envelope across all four facings, not the exact shape of a single facing.

The highest facing-dependent displayed silhouette, including hat, is B 1.334 / 1.668 / 2.001 tiles and C 1.261 / 1.576 / 1.891 tiles at 100 / 125 / 150. This is a calibrated native comparison; the earlier AI board’s approximate 1.6-tile C estimate was unregistered. At 150%, maximum full width is B 0.944 and C 0.977 tiles. C head-core depth is 14.3% greater and torso depth 17.7% greater than B.

`character-scale-study.blend` is an isolated editable native library with two models, materials, independent part meshes, root controls, lights and camera. It is a static anatomy study with no armature or action claims; the source is ready for later rigging after size/design approval. The file was written independently using libraries.write, preserving the unrelated live user project. Runtime production object/pose snapshots match before/after.

`study.json` declares each native capture. `geometry/` retains evaluated vertices, faces, matrices, dimensions and hashes for every scale/facing. `cameras/` retains actual 35° camera/projection matrices, root calibration, native project identity and PNG hash/dimension receipts. Audit source independently checks actual mesh vertices and matrices, normalized geometry under uniform scaling, square pixels, all 24 native PNG dimensions/hashes, and unclipped alpha margins. These checks establish registration/bounds, not final art approval.

Re-render/audit from this folder (Blender 5.2.2; audit uses Pillow):

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background character-scale-study.blend --python source/capture_character_scale_study.py -- --capture --manifest study.json
python3 source/audit_character_scale_study.py study.json --report native-audit.json
```

The reusable recipe can also create a new isolated editable scene via create_study(None, output_dir=NEW_FOLDER) in Blender. Never overwrite the existing study or the user's live project.

## Selected size and hair revision 3

The user selected 125% on 2026-10-18. The page highlights that column and defaults the 3×3 layout to 125%. B/C remain alternatives; no global character replacement has been approved.

Revision 3 replaces the box hair cap with a rounded crown and occiput, layered smooth curls, fuller temples and a covered nape. Asymmetric fringe groups and subtle brown variation add readable volume. Cheek/chin corners use a larger native bevel with weighted normals. Head dimensions, camera, root, costume, minimal feet and actual scale factors are unchanged. C at 125% is still 1.576 tiles high including the hat and has a conservative 0.814×0.814 tile turning envelope. All 24 native captures were regenerated and audited.

Earlier flat-hair captures are retained under review/33/character-scale-study/iterations/flat-hair-v2; the complete earlier native source is available at commit 4ba88fb.
