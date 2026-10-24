# Front-facing chef UI portraits

Eight transparent front views rendered in Blender from the existing native chef models: Lena, Omar, Ama, Mateo, Noor, Dalia, Ellis and Rowan.

## Capture contract

- Eye-level ordinary orthographic front camera, **0° elevation**, equal pixel aspect and one fixed scale/frame for every chef.
- Full 512×640 PNGs retain the complete native character, fixed authored camera and clear frame margins. No per-character alpha fitting.
- Existing idle pose, frame 1, South/front facing; food and utensils hidden for UI portraits. Existing meshes, materials and Faceted lighting/color grade retained.
- Full front views supply non-scene chef UI: inventory/roster, applications, profile and confirmation surfaces.
- Recipe headers use a fixed **[64,24,384,512]** chest-up rectangle from that same full render, clipped in CSS without image distortion. The same crop applies to every chef.
- In-scene characters retain their established scene camera/sprites. This dedicated UI capture does not alter them.

`render_portraits.py` is the reproducible Blender capture recipe. `chef-ui-front-views.blend` retains the separate editable capture scene, imported native chef models and shared lighting/camera. `camera-and-provenance.json` records the original source project hash, rig hashes, camera matrices, fixed crop and all eight PNG hashes. The canonical Blender project and the user's existing scene were not saved over.

`wireframe/chef-portrait.jsx` is the shared HTML portrait component. It is used by the roster/inventory, applications, profiles and recipe header. The original standalone wood dock's People inventory uses these same front renders. Open `#chef-ui-portraits` in the wireframe studio to compare all eight full and chest-up views.

These captures are ready for native UI reuse after prototype review. They do not constitute a Godot UI port or Android build.
