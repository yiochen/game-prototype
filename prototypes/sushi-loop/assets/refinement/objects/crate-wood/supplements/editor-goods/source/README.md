Crate inventory goods supplement, round 01.

The standalone round-01.blend is the approved world crate with only the locked UI camera, frame/aspect and output path changed. It preserves eight meshes, modifiers, UVs, parenting, all four native material graphs, the symmetric light rig and the existing Cycles64 Standard/None color pipeline.

For native replay, from the supplement root use:

    blender --background source/round-01.blend --python source/reopen_goods.py -- --output-dir /new/empty/replay-folder

The original build recipe is source/build_goods.py and requires a fresh output directory to retain immutable rounds. It reads the bound approved-world-model.blend backup and camera contract from inputs/. Native pixels are never painted, fitted, recentered, recolored or post-graded. Reopening may change PNG metadata; decoded RGBA pixels reproduce exactly.

For the actual copied current card consumer, use Python3 with Pillow and Godot4.7.2 Compatibility:

    python3 source/prepare_consumer.py
    godot --headless --editor --path source/consumer --import
    GOODS_OUTPUT=/new/empty/evidence-folder godot --path source/consumer --script res://bench.gd --resolution 64x64

The consumer replay reads only the bound current-consumer snapshot, original accepted goods PNG and new native goods PNG. The four production consumer scripts are verbatim; fixture inventory is the exact current content/editor.json. Only the crate region changes in the copied atlas. All six goods remain across layout page0/page1/floor. Floor source bytes and crop pixels remain exact. Complete 540x960, 786x1398 and 1280x720 screenshots back the footer overview; the solid room background is a placeholder, with no room/world rendering claim.

source/verify_portable.py tested native replay and all42 consumer/background outputs in a fresh temporary folder populated only from the declared resources. candidates/round-01/portable-proof.json records exact decoded-pixel equality.

No world source, sealed world packet, production sprites, current Godot files, UI files or floor art were modified. Independent supplement visual approval remains the judge's decision.
