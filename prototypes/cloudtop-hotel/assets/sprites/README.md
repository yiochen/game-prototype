# Detailed paper sprite sheets

Created with the built-in `image_gen` tool from the user's two Cloudtop Hotel paper-diorama references. [prompts.json](prompts.json) preserves every final generation prompt. The reference photos themselves are not shipped.

| Asset | Grid | Frames in reading order |
| --- | --- | --- |
| [Bunny rooms](rooms-bunny.png) | 4 × 2 | Folded box, open cross, assembling facade, happy guest, blink, book, wave, sleep |
| [Frog rooms](rooms-frog.png) | 4 × 2 | Same eight poses in green |
| [Cat rooms](rooms-cat.png) | 4 × 2 | Same eight poses in orange |
| [Copycat and balloons](actors.png) | 4 × 4 | Row 1: spyglass, stamp, send, celebrate. Rows 2–4: four flight poses each for Bunny, Frog, Cat balloons |
| [Scenery and props](props.png) | 4 × 2 | Cloud, island, construction platform, roof, parcel, bell, coin, heart |
| [Power card illustrations](card-powers.png) | 4 × 2 | Room Choice, Surprise Parcel, Copycat, Master Fold; Lucky Bell, Reserve Delivery, Coupon Book, Neighborhood Streak |
| [Typed card illustrations](card-types.png) | 3 × 2 | Row 1: Bunny, Frog, Cat Room Pattern blueprints. Row 2: Bunny, Frog, Cat Type Locks with three future cards |
| [Moving scenery](scenery.png) | 6 individually bounded frames | Cottage island, windmill island, forest island, three folded cloud shapes |
| [Cardboard tray](cardboard-tray.png) | Single image | Empty textured kraft-cardboard box in perspective, with folded joins, walls and a raised front lip |
| [Balloon Dock banner](dock-paper.png) | Single image | Hand-lettered Balloon Dock title on ivory paper with torn fibrous edges |
| [Clean paper sky](sky-paper.png) | Single image | Uninterrupted azure paper texture behind the moving scenery |
| [Original paper sky](sky.png) | Single reference image, not shipped | Original painted islands/clouds, preserved as the source for the separated layers |

There are seven game/UI sheets plus one scenery atlas, containing 68 frames: 40 character/room animation frames, eight prop frames, 14 card illustrations and six background scenery frames. The tray, Dock banner and sky are separate single images. PNGs retain the generated alpha transparency where applicable. WebP copies retain the same dimensions and alpha and use 90% encoding quality. Only current WebP files enter the Vite build.

The built-in `image_gen` tool also generated the card illustrations, torn-paper label and cardboard tray from the user's September 23 tray reference. [card-ui-prompts.json](card-ui-prompts.json) preserves their final prompts and source/delivery filenames. Each power has a distinct illustration of its function rather than a shared generic room icon. Room Choice offers three doors; Surprise Parcel releases varied rooms; Copycat stamps a duplicate; Master Fold operates a folding press; Lucky Bell rings over a parcel; Reserve Delivery converts a coin chest to rooms; Coupon Book shows three refund tickets; Neighborhood Streak shows increasingly tall matching towers. Room Pattern and Type Lock each have separate Bunny, Frog and Cat variants. One Room uses a room sprite, Prefab Pack composes three matching rooms, Balloon Call pairs a typed balloon and room, and Mosaic displays its exact room sequence with arrows.

The built-in `image_gen` tool separated the original sky into [sky-paper.png](sky-paper.png) and [scenery.png](scenery.png); [scenery-prompts.json](scenery-prompts.json) preserves both final prompts. The atlas's islands have taller bounds than its clouds: `SCENERY.frames` in `assets.js` crops each complete object with alpha padding, keeping the original PNG untouched. `scenery.js` places five island instances and nine cloud instances around the viewport edges and animates transforms independently. Clouds take 43–63 seconds per round trip; islands bob and sway over 21–31 seconds. Reduced motion and hidden tabs pause these loops in place.

Run `node prototypes/cloudtop-hotel/assets/sprites/encode.mjs` from the repository root to reproduce the delivery encodings using the existing Playwright dependency. This is a format conversion; it does not resize, recolor or redraw the original artwork.

`assets.js` divides sheets using their actual image dimensions, including fractional grid boundaries rounded to pixels. It registers tight facade bounds for frames 3–7 so complete rooms meet without transparent gutters. The original files remain intact. DOM thumbnails clip a whole grid cell using the same frame index.

The scene chooses staggered guest poses and balloon frames on its presentation clock. Card flight is a separate DOM animation: 470 ms to the screen center, 220 ms of inflation, then a pop with fragments of the actual selected illustration lasting up to 420 ms. The engine purchase occurs once at that pop. Reset cancels an uncommitted flight; Reveal now or Reduced motion finishes it once. Subsequent Phaser delivery choreography uses the committed purchase result; frame timing cannot change a payout. Reduced motion bypasses the flight and delivery animations and freezes all idle frames. The first prototype's SVG sketches remain in the parent assets folder as unused source art.
