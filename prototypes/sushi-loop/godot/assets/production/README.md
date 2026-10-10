# Starter restaurant production artwork

Fresh original artwork for issue #10, generated with the built-in image generation tool. The supplied `design/art-directions/doodle.png` catalog informed the style; no artwork was extracted from it, and no archived implementation assets were accessed or reused. No game title is baked into these assets.

## Integration

Load `manifest.json` by semantic key. Each entry names a `res://` PNG, a measured `[x, y, width, height]` region, and an anchor. Equivalent native Godot `AtlasTexture` resources live in `atlas/`. The original PNG pixels, sizes, color channels and transparency are preserved. Regions remove transparent atlas padding; do not assume fixed cell dimensions from the requested generation size.

Character and prop anchors are bottom-center. Scale proportionally, position the base at the occupied floor cell, and allow tall art to extend upward. Belt anchors are center-center. Direction keys describe the direction the figure actually faces, verified visually; the chef sheet's two profile columns were returned in the opposite order from the prompt and are mapped correctly.

- `chef_down/up/left/right` are preparation poses. `chef_work_*` and `chef_hold_*` expose each directional state. `chef_work` and `chef_hold` alias front/down poses.
- `guest_a_*` is the yellow-shirt/bun customer; `guest_b_*` is the coral-jacket/red-curls customer. Plain direction keys are walking poses. `guest_*_seated_down/up/left/right` are seated eating poses. The short `guest_*_seated` alias faces up, appropriate for seats below the starter belt. Draw the independent stool behind the person.
- `guest_*_waiting_down/up/left/right` are separate empty-handed seated poses, with calm open eyes and hands on knees. Use these while waiting for food. `guest_*_eating_down/up/left/right` explicitly alias the original food-holding seated poses; switch only when a meal exists. Both families retain the same identities and use bottom-center anchors.
- `stool`, `salmon_nigiri`, `blackboard`, `plant`, `plant_tall`, `barrel`, `crate` and `lantern` are separate prop regions. The blackboard is blank so the game can place the current recipe in it.
- `belt_horizontal`, `belt_vertical`, and four `belt_end_*` keys are empty modules. `belt_endpoint` aliases the right/east end. Stretch neither characters nor sushi; connect belt joins carefully and keep their lower support edge visually aligned.
- `pile_sofa`, `pile_shelf`, `pile_cart` and `covered_dock` are complete multi-cell compositions. Use each composition once per obstruction cluster. Their source sheet was revised for generous independent extraction regions.
- `floor_wood` is a quiet opaque square wood material; draw the square-cell grid independently. Repeating it over several cells keeps the grain subordinate to service objects. It has been inspected as a 2×2 repetition.
- `app_icon.png` is the opaque square Android launcher illustration, with no title.
- `entrance` is a finished narrow honeywood open doorway with an intentionally dark interior. It uses true alpha around the frame and a bottom-center threshold anchor; scale it to one floor cell wide and allow its height to extend upward. No title or sign is baked into it. Its exact generation prompt is in `../provenance/entrance.json`.

## Provenance and inspection

Exact prompts and generated source paths are recorded in `../provenance/sources.json` and `refinements.json`. `image-verification.json` records dimensions, alpha ranges and SHA-256 hashes. `contact-sheet.png` and `floor-repeat-inspection.png` are inspection previews, not runtime sprites. `build_metadata.py` rebuilds regions and AtlasTexture resources without changing production PNG pixels; it requires Pillow and NumPy. A rejected clutter layout is retained only in provenance, never referenced by the manifest.

These are pose atlases. Runtime movement, bobbing, preparation timing, held-food waiting, plate movement, eating and coin feedback remain controlled by the game rather than baked into sprite images.
