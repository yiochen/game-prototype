# Issue #33 production object review

The concept sheet remains at `#art-catalog`. The production index is `#object-library`, and every manifest object has its own stable `#object-<id>` page and Comments context.

`assets/production/library.json` is the only object inventory. Vite imports its actual PNG exports with fingerprinted URLs; missing exports render a labeled pending cell, never a concept crop. `status: ready` means ready for review, not user-approved or issue-complete. Keep queued inventory entries visible as production continues.

```json
{
  "version": 1,
  "cellSize": 128,
  "objects": [{
    "id": "chef-lena",
    "name": "Lena Brooks",
    "family": "W05",
    "status": "working",
    "kind": "character",
    "footprint": [1, 1],
    "frameSize": [192, 320],
    "root": [96, 248],
    "sourceScale": 4,
    "projection": "character-orthographic",
    "clips": [{
      "id": "work",
      "name": "Preparing sushi",
      "frames": 12,
      "fps": 12,
      "loop": true,
      "directions": {
        "N": {"image": "sprites/chef-lena/work-N.png", "columns": 6, "rows": 2},
        "E": {"image": "sprites/chef-lena/work-E.png", "columns": 6, "rows": 2},
        "S": {"image": "sprites/chef-lena/work-S.png", "columns": 6, "rows": 2},
        "W": {"image": "sprites/chef-lena/work-W.png", "columns": 6, "rows": 2}
      }
    }],
    "interactions": [{
      "name": "Chef at the facing belt",
      "gridSize": [3, 3],
      "placements": [
        {"object": "chef-lena", "x": 1, "y": 2, "direction": "N", "clip": "work"},
        {"object": "belt-straight-n", "x": 1, "y": 1, "direction": "N", "clip": "running"}
      ]
    }]
  }]
}
```

`frameSize` and `root` are logical pixels. Native source frame dimensions are `frameSize × sourceScale`. The renderer crops complete authored panels into their unchanged logical rectangle; it never measures alpha or fits poses. A direction entry may override `frameSize`, `root`, `sourceScale`, `frames`, and `atlasSize`. Use `offset` to address a panel in a shared static atlas. For a nonuniform atlas, `rects` records every native `[x,y,width,height]` rectangle and `atlasSize` records the actual whole image dimensions.

Optional `sockets: {seat: [dx,dy]}` and `ports: [{name: "in",position: [dx,dy]}]` contain logical projected offsets relative to the ground root. Direction-specific `sockets`/`ports` on the direction entry override the object records. These points appear in the overlay.

Rectangular assets can declare `directionFootprints: {N: [3,1], E: [1,3], S: [3,1], W: [1,3]}`. Grid footprints, ground centers and repeated-copy spacing follow the selected direction; four-facing panels reserve the maximum extent. Frame/root pixel coordinates stay fixed. An irregular `directionRootCells` entry can override the ground anchor within that facing’s footprint.

Direction entries must represent separately captured facings. The viewer never rotates a bitmap as a substitute. Clips use 12 fps. Static entries have `frames: 1`; animated entries should contain at least six unique native renders. Missing directional exports stay visibly Pending.

A placement's x/y are the zero-based top-left cell indices of its declared footprint. Its projected root is `((x+footprintWidth/2)*cellSize, (y+footprintHeight/2)*cellSize)` (so a single-cell root remains at its cell center). An optional object `rootCell: [cellX,cellY]` records an irregular anchor relative to that top-left cell, plus an optional `offset: [logicalX, logicalY]` for an authored support attachment. Declare floor `kind: floor` and deck `kind: belt`. Floor/background renders first. World belts, people, props, and dishes sort by registered ground-center depth, then numeric `layer` at equal depth, then stable insertion order. Keep a belt's local layer below its attached dish. Objects or placements may explicitly declare `renderPass: background`, `foreground`, or `overhead` for separate scenery/depth pieces. Support-height projection offsets do not change that ground-depth sort, so a seated character can layer above its supporting stool.

For a manually staged moving plate, put `motion: {path: [[cellX,cellY],...],duration: 4,loop: true}` on its separate placement. The review clock interpolates the path by distance and controls its play/pause/scrub together with belt slats. This is presentation only; there is no belt occupancy, service or pathfinding simulation. Include the last point again for a closed loop; use `loop: false` for a one-shot path.

Every page shows four facings, a footprint-spaced 3×3 repetition, the object's manifest interaction scenes, and a list of every exported clip. One animation disclosure is open at a time and shows all four facings; closed disclosures unmount their SVGs and images to avoid decoding every atlas together. Opening a state also selects it for the isolated/repeated scenes, allowing the browser to share the same four atlas images. All scenes preserve one logical cell size. Scene zoom uniformly enlarges the whole scene with horizontal panning; vertical gestures continue to the browser page. Root/footprint overlays can be hidden. Actual `floor-cream`/`floor-plain` or `floor-underwater` exports are used behind the grid as they arrive; otherwise the square calibration surface is explicit. Reduced motion starts paused, and hiding the tab pauses playback.

The shared clock closes the common period of all clips and presentation paths, preventing a short loop from jumping when a longer state restarts. One-shot sprites hold their final pose until the review cycle restarts.

Validation: `npm test`, `npm run build`, and `npx playwright test prototypes/sushi-loop/tests/object-review.spec.js` (after at least the queued production manifest exists). The browser suite checks stable object deep links, contained responsive scenes, exact four-way/3×3 placement counts, pause/scrub, honest queued states and object-specific Comments handoff. `sprite-layout.test.js` checks native atlas registration, one-shot/loop timing, repeated multi-cell footprints, upward bounds, depth ordering and separate plate path travel.


Library cards show the first actual pose on its unchanged full authored canvas and keep tile rectangles square. An IntersectionObserver rooted in the browser viewport mounts the sprite only within a 96 px viewport margin, then unmounts its SVG/image when it leaves. Card and thumbnail dimensions remain fixed during that change; queued cards contain no image. A scroll/resize measurement fallback preserves this bounded behavior without IntersectionObserver. These thumbnail poses stay static, including under reduced motion.


The studio has one document-level vertical scroller. Object reviews and libraries, concept sheets, component galleries, paper pages and dialogs grow to their full content height. Desktop sidebars flow with the page, and mobile Examples expands inline without locking the body. New route selections reveal the destination heading; browser Back restores the prior route’s page position. In-page playback and filter changes do not request a navigation scroll. `single-scroll.spec.js` exercises these rules, including touch swipes over sprites and wide maps.


Direction-independent effects can declare `facingPolicy: "camera-facing"`. The four separately captured world-facing contexts then retain readable artwork toward the fixed camera. The review header and first-scene subtitle explain this policy; the renderer still uses each native directional atlas without rotating or substituting it. Physical objects retain their ordinary four-direction wording.


The editable-source reference follows each object’s immutable `source.blend` revision for the exact captured model. The Download .blend action follows `production.editableProject` to the current complete native library, falling back to the object revision when no canonical project is declared. Both paths require safe relative paths.
