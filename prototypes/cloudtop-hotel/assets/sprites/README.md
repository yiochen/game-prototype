# Detailed paper sprite sheets

Created with the built-in `image_gen` tool from the user's two Cloudtop Hotel paper-diorama references. [prompts.json](prompts.json) preserves every final generation prompt. The reference photos themselves are not shipped.

| Asset | Grid | Frames in reading order |
| --- | --- | --- |
| [Bunny rooms](rooms-bunny.png) | 4 × 2 | Folded box, open cross, assembling facade, happy guest, blink, book, wave, sleep |
| [Frog rooms](rooms-frog.png) | 4 × 2 | Same eight poses in green |
| [Cat rooms](rooms-cat.png) | 4 × 2 | Same eight poses in orange |
| [Copycat and balloons](actors.png) | 4 × 4 | Row 1: spyglass, stamp, send, celebrate. Rows 2–4: four flight poses each for Bunny, Frog, Cat balloons |
| [Scenery and props](props.png) | 4 × 2 | Cloud, island, construction platform, roof, parcel, bell, coin, heart |
| [Moving scenery](scenery.png) | 6 individually bounded frames | Cottage island, windmill island, forest island, three folded cloud shapes |
| [Clean paper sky](sky-paper.png) | Single image | Uninterrupted azure paper texture behind the moving scenery |
| [Original paper sky](sky.png) | Single reference image, not shipped | Original painted islands/clouds, preserved as the source for the separated layers |

There are 40 character/room animation frames, eight prop frames and six background scenery frames. PNGs retain the generated alpha transparency. WebP copies retain the same dimensions and alpha, use 90% encoding quality and total about 2.3 MB. Only current WebP files enter the Vite build.

The built-in `image_gen` tool separated the original sky into [sky-paper.png](sky-paper.png) and [scenery.png](scenery.png); [scenery-prompts.json](scenery-prompts.json) preserves both final prompts. The atlas's islands have taller bounds than its clouds: `SCENERY.frames` in `assets.js` crops each complete object with alpha padding, keeping the original PNG untouched. `scenery.js` places five island instances and nine cloud instances around the viewport edges and animates transforms independently. Clouds take 43–63 seconds per round trip; islands bob and sway over 21–31 seconds. Reduced motion and hidden tabs pause these loops in place.

Run `node prototypes/cloudtop-hotel/assets/sprites/encode.mjs` from the repository root to reproduce the delivery encodings using the existing Playwright dependency. This is a format conversion; it does not resize, recolor or redraw the original artwork.

`assets.js` divides sheets using their actual image dimensions, including fractional grid boundaries rounded to pixels. It registers tight facade bounds for frames 3–7 so complete rooms meet without transparent gutters. The original files remain intact. DOM thumbnails clip a whole grid cell using the same frame index.

The scene chooses staggered guest poses and balloon frames on its presentation clock. Delivery choreography uses the already-committed purchase result; frame timing cannot change a payout. Reduced motion bypasses delivery animation and freezes all idle frames. The first prototype's SVG sketches remain in the parent assets folder as unused source art.
