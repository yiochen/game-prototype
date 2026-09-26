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
| [Celestial ornaments](celestial.png) | 4 individually bounded frames | Ivory star, gold star, ivory crescent moon, folded blue ribbon |
| [Cardboard tray](cardboard-tray.png) | Single image | Empty textured kraft-cardboard box in perspective, with folded joins, walls and a raised front lip |
| [Original Balloon Dock banner](dock-paper.png) | Unused source image, not shipped | Hand-lettered Balloon Dock title on ivory paper with torn fibrous edges |
| [Paper card faces](card-paper.png) | 3 × 2 | Blank portrait faces: pink, green, orange; lavender, gold, teal. Folded colored borders surround fibrous ivory centers |
| [HUD paper tab](hud-tab.png) | Single image | Blank warm ivory plaque with hand-cut corners for coin, balloon and hotel-height counters |
| [Clean paper sky](sky-paper.png) | Single image | Uninterrupted azure paper texture behind the moving scenery |
| [Original paper sky](sky.png) | Single reference image, not shipped | Original painted islands/clouds, preserved as the source for the separated layers |

There are seven game/UI sprite sheets plus two scenery atlases, containing 72 sprite frames: 40 character/room animation frames, eight prop frames, 14 card illustrations, six background scenery frames and four celestial ornaments. A separate surface atlas contains six blank card faces. The tray, HUD tab and sky are separate single images. The removed Dock banner is preserved as unused source art. PNGs retain the generated alpha transparency where applicable. WebP copies retain the same dimensions and alpha and use 90% encoding quality (88% for the celestial atlas). Only current WebP files enter the Vite build.

The built-in `image_gen` tool also generated the card illustrations, torn-paper label and cardboard tray from the user's September 23 tray reference. [card-ui-prompts.json](card-ui-prompts.json) preserves their final prompts and source/delivery filenames. Each power has a distinct illustration of its function rather than a shared generic room icon. Room Choice offers three doors; Surprise Parcel releases varied rooms; Copycat stamps a duplicate; Master Fold operates a folding press; Lucky Bell rings over a parcel; Reserve Delivery converts a coin chest to rooms; Coupon Book shows three refund tickets; Neighborhood Streak shows increasingly tall matching towers. Room Pattern and Type Lock each have separate Bunny, Frog and Cat variants. One Room uses a room sprite, Prefab Pack composes three matching rooms, Balloon Call pairs a typed balloon and room, and Mosaic displays its exact room sequence with arrows.

The later paper-surface pass uses the same built-in tool and the full-screen September 23 mock. [paper-surfaces-prompts.json](paper-surfaces-prompts.json) records the final prompts for `card-paper` and `hud-tab`. Each paper-card cell is a flat, portrait 3:4 surface with no baked-in illustration, label or perspective. `card-table.css` selects its color with a 300% × 200% background and places all three cards on the box floor's shared perspective plane. Existing DOM artwork, cost, title, result and help controls sit over the generated paper. The cardboard box remains stationary, with its foreground rim drawn over the lower card edges. `paper-hud.css` reuses the blank tab behind live counters, with balloon sprites overlapping the tabs and the existing heart prop marking hotel height; the heart does not add a lives system.

The built-in `image_gen` tool separated the original sky into [sky-paper.png](sky-paper.png) and [scenery.png](scenery.png); [scenery-prompts.json](scenery-prompts.json) preserves both final prompts. The atlas's islands have taller bounds than its clouds: `SCENERY.frames` in `assets.js` crops each complete object with alpha padding, keeping the original PNG untouched. `scenery.js` places five island instances and nine cloud instances around the viewport edges and animates transforms independently. Clouds take 43–63 seconds per round trip; islands bob and sway over 21–31 seconds. Reduced motion and hidden tabs pause these loops in place.

Run `node prototypes/cloudtop-hotel/assets/sprites/encode.mjs` from the repository root to reproduce the delivery encodings using the existing Playwright dependency. This is a format conversion; it does not resize, recolor or redraw the original artwork.

The built-in `image_gen` tool generated `celestial.png` for the seven altitude skies. [celestial-prompts.json](celestial-prompts.json) preserves the final prompt and delivery settings. The 1254 × 1254 source has uneven object bounds, explicitly cropped by DOM background coordinates in `scenery.js`; the PNG itself stays untouched. Its WebP copy was encoded with `ffmpeg -i celestial.png -c:v libwebp -quality 88 celestial.webp`. Precise constellation paths are native SVG with small four-point star nodes, drawn behind the hotel. Existing paper texture is blended over each altitude color, preserving tactile material without shipping seven full-screen images.

`assets.js` divides sheets using their actual image dimensions, including fractional grid boundaries rounded to pixels. It registers tight facade bounds for frames 3–7 so complete rooms meet without transparent gutters. The original files remain intact. DOM thumbnails clip a whole grid cell using the same frame index.

The scene chooses staggered guest poses and balloon frames on its presentation clock. Card flight is a separate DOM animation: the card's four projected corners establish its starting pose, followed by 470 ms to the screen center, 220 ms of inflation, then a pop with fragments of the actual selected illustration lasting up to 420 ms. The engine purchase occurs once at that pop. Reset cancels an uncommitted flight; Reveal now or Reduced motion finishes it once. Subsequent Phaser delivery choreography uses the committed purchase result; frame timing cannot change a payout. Reduced motion bypasses the flight and delivery animations and freezes all idle frames. The first prototype's SVG sketches remain in the parent assets folder as unused source art.

The offer stacks reuse the blank paper faces with a parcel placeholder; they are decorative and reveal no future cards. The final free Roof card reuses the roof prop (frame 3), which also lands on the hotel after the card is selected.
