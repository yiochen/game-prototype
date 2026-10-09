# Expedition result backgrounds: generation record

User instruction: accept outcome-specific titles and give each outcome a different image-generated background. This request is an explicit exception to the text-only interview preference; future questions remain text-only unless requested.

Mode: built-in image_gen. Deliverables: three static, polished portrait result-screen mockups demonstrating distinct backgrounds behind a consistent salvage receipt. These are UI proof-of-concept images, not animation assets or implemented game screens. Numeric amounts are illustrative. Recipe-summary treatment was unresolved at generation time and omitted for this comparison; Question 42 subsequently accepts receipt-only results.

## Expedition complete

Target: `41a-results-complete.png`.

Style references: `08a-results-restaurant.png` and `../art-directions/01-doodle.png`.

Exact prompt:

```text
Use case: ui-mockup
Asset type: polished commercial mobile-game result screen, single portrait 9:16 composition, edge-to-edge game screen without a phone frame.
Primary request: create the EXPEDITION COMPLETE result screen for Sushi Loop, using a distinct completed-route background behind the accepted salvage receipt.
Input images: Image 1 is a reference for the cream receipt card, coral Restaurant button, salvage gear icon and mobile UI polish; it is NOT an edit target. Image 2 is the selected 2D doodle art direction and yellow submarine identity. Use only the reference style and identity, not their provisional gameplay HUD or recipe-summary content.
Scene/backdrop: an overhead underwater canyon opening into a broad sunlit teal basin. Clean coral silhouettes frame the sides, pale sunbeams brighten the upper water, sparse small fish silhouettes and quiet sand ripples add life. This is a finished-route scene with an intact warm-yellow submarine visible below the receipt near the lower center, gentle bubbles behind it and a steady soft headlight. Keep the scene welcoming and readable.
Style/medium: production-quality 2D doodle game art, confident slightly irregular dark ink outlines, flat controlled color fills, rounded modular silhouettes, restrained paper grain, sparse hatching. Match the selected doodle reference. Crisp sprite-like submarine construction and clean commercial typography. Preserve the rounded yellow hull and blue circular porthole.
Composition/framing: one complete portrait screen. A single centered warm-ivory receipt panel fills roughly x=13–87%, y=25–72%. Keep ample visible background above, below and along both sides; the whole submarine is visible below the card. Dark navy rounded lettering is crisp and legible at phone size. Deliberate padding, aligned labels and amounts, clear hierarchy. A single large coral Restaurant button sits inside the panel at its bottom. No footer outside the panel.
Text (verbatim): the panel title is "Expedition complete". Two receipt rows read "Salvage pickups" with "72" and "Completion bonus" with "+18". Below the rows, a prominent total reads "Total earned" and "90", with a small amber salvage gear icon. The only action reads "Restaurant".
Constraints: render exactly these UI elements and numbers. These are illustrative amounts, not gameplay tuning. Do not add a repeat-catch bonus line because this comparison does not depict a repeat catch. Do not reproduce the old New recipe/Eel Nigiri row from the reference; recipe-summary treatment is outside this background comparison. The scene is a static results background, not active gameplay. No pause button, hull meter, creature bar, harpoon button, coins, rate, stars, ratings, repair costs, retry, Skip, phone chrome or watermark. The result must look like a complete polished released 2D game screen, not a prototype, rough sketch, 3D render or painted concept-art plate.
```

## Returned early

Target: `41b-results-returned-early.png`.

Edit reference: the completed-route result generated above, saved as `41a-results-complete.png`.

Exact prompt:

```text
Use case: ui-mockup
Asset type: polished commercial mobile-game result screen, single portrait 9:16 composition.
Primary request: derive the RETURNED EARLY result screen from the provided completed-route result screen. Give it a genuinely different illustrated background, not a simple recolor.
Input image: Image 1 is the edit target. Preserve its exact cream receipt panel shape, position, padding, typography, salvage gear icon, coral Restaurant button, portrait framing, 2D doodle line treatment and recognizable submarine body.
Change only the outcome background/ship pose and the specified receipt text and numbers.
Scene/backdrop: replace the open sunlit basin with a quieter sheltered underwater return corridor. Sweeping coral-covered rock walls form a broad curved sandy route around the sides, with calm muted teal water, gentle pale light and sparse bubbles. The intact yellow submarine below the panel is turning toward the returning route, in the same overhead view; show a calm voluntary departure, not damage or distress. The terrain composition must be clearly different from the completed-route image.
Text (verbatim): change the title to "Returned early". Keep "Salvage pickups" and "72". Change "Completion bonus" amount to "0". Add a short legible explanation beneath the bonus rows: "No completion bonus: returned early." Change the prominent "Total earned" amount to "72". Keep the sole button label "Restaurant".
Constraints: preserve the same commercial 2D doodle style and matching panel geometry; keep the whole submarine visible below the panel. All amounts are illustrative. This is a static results scene, not a new controllable return sequence. No new gameplay mechanics, navigation arrows, portals, reward multipliers, extra recipe row, repair fees, currency loss, repeated bonus line, active-play HUD, new buttons, phone frame or watermark. Keep color fills flat, outlines clean, texture restrained and all text crisp. Do not add an additional modal, duplicate card or multiple screens.
```

## Hull depleted

Target: `41c-results-hull-depleted.png`.

Edit reference: the same completed-route result, saved as `41a-results-complete.png`.

Exact prompt:

```text
Use case: ui-mockup
Asset type: polished commercial mobile-game result screen, single portrait 9:16 composition.
Primary request: derive the HULL DEPLETED result screen from the provided completed-route result screen. Give it a genuinely different illustrated background and visibly damaged submarine, not a simple recolor.
Input image: Image 1 is the edit target. Preserve its exact cream receipt panel shape, position, padding, typography, salvage gear icon, coral Restaurant button, portrait framing, 2D doodle line treatment and recognizable submarine body.
Change only the outcome background/ship state and the specified receipt text and numbers.
Scene/backdrop: replace the open sunlit basin with a darker rocky seabed alcove. Cool blue water, uneven stone silhouettes, sparse sea plants, settled sand and a narrow soft shaft of light frame the receipt. Below the panel, the same warm-yellow submarine rests on the sandy bottom at a slight angle. Its hull has readable cartoon dents and a loose small panel, a few tiny escaping bubbles and a dim headlight; keep the blue porthole intact and the submarine recognizable. Use gentle humorous game wear rather than a grim destroyed wreck. The terrain composition must be clearly different from both open completion water and a curved return corridor.
Text (verbatim): change the title to "Hull depleted". Keep "Salvage pickups" and "72". Change "Completion bonus" amount to "0". Add a short legible explanation beneath the bonus rows: "No completion bonus: hull depleted." Change the prominent "Total earned" amount to "72". Keep the sole button label "Restaurant".
Constraints: preserve the same commercial 2D doodle style and matching panel geometry; keep the whole submarine visible below the panel. All amounts are illustrative. The damage illustration is an outcome background, not a repair-cost, rescue, lost-reward or permanent-damage mechanic. No towing characters or extra ships, fire, gore, red screen-edge vignette, currency deductions, repair fees, reward multipliers, extra recipe row, repeated bonus line, active-play HUD, new buttons, phone frame or watermark. Keep color fills flat, outlines clean, texture restrained and all text crisp. Do not add an additional modal, duplicate card or multiple screens.
```

## Output record

Generated and visually inspected using built-in image_gen. Each selected image is 941 × 1672 pixels, in portrait orientation.

| Outcome | Workspace mockup | Original generated output |
| --- | --- | --- |
| Expedition complete | [41a-results-complete.png](./41a-results-complete.png) | `/Users/yiouchen/.codex/generated_images/01a103d4-0163-7062-9c99-10fa48df2e09/exec-7a952089-8b03-44fd-a283-fdd4a5de9acd.png` |
| Returned early | [41b-results-returned-early.png](./41b-results-returned-early.png) | `/Users/yiouchen/.codex/generated_images/01a103d4-0163-7062-9c99-10fa48df2e09/exec-ff3caae0-83c3-4578-b494-71c685451b56.png` |
| Hull depleted | [41c-results-hull-depleted.png](./41c-results-hull-depleted.png) | `/Users/yiouchen/.codex/generated_images/01a103d4-0163-7062-9c99-10fa48df2e09/exec-c563f313-eb9b-4296-8888-ee090a9062f6.png` |

The completed-route screen uses bright open water; early return uses a separate coral archway and curved corridor; depleted hull uses a darker rocky alcove and visibly damaged submarine. Titles, receipt amounts, and the sole Restaurant action are legible. The examples preserve their arithmetic: 72 + 18 = 90 on completion, and 72 + 0 = 72 on early return or hull depletion.

These are static full-screen UI mockups with illustrated backgrounds and baked-in receipt text, not isolated runtime background layers or cutscene animation assets. Exact compositions are proposals; the accepted requirements are distinct backgrounds, selected doodle style, outcome titles, reward retention, receipt fields, and Restaurant continuation. The absent recipe recap now matches the receipt-only results accepted in Question 42. Exact generation prompts remain preserved above, along with the original generated files.
