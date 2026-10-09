# Workshop upgrade purchase — UI question 23

Built-in image-generation edits of the previously inspected `22b-workshop-stat-preview.png`. A shows a one-tap Hull purchase after it has applied; B shows a pending confirmation before it applies. Numbers, future prices and visual feedback are illustrative and do not establish balance or animation rules.

## A — one-tap purchase

```text
Use case: precise-object-edit.
Asset type: finished commercial portrait 2D mobile-game Workshop UI screenshot.
Input image: the supplied current-to-next-stat Workshop screen is the EDIT TARGET. Preserve exact portrait dimensions and polished 2D doodle ink art, warm timber/stone maintenance room, recognizable yellow submarine on its cradle, Sushi Bar scene doorway, Workshop sign, and the accepted three-card layout. All money icons represent gear/scrap salvage, never restaurant coins. Preserve Harpoon and Collector cards exactly, including Lv. 2, their stat previews, and gear costs 160 and 90. Levels, values and costs are illustrative.
Primary request — OPTION A, INSTANT PURCHASE RESULT: show the Workshop immediately AFTER one tap has purchased the Hull upgrade, with no popup or confirmation.
Change top-right salvage balance from "320" to "200" because the illustrated Hull purchase cost 120. On ONLY the Hull card, change current-level tag from "Lv. 2" to "Lv. 3"; change its Max hull current-to-next stat preview from "100 → 120" to exact "120 → 140"; change its Upgrade gear cost from "120" to "180", the illustrative next cost. Retain the coral Upgrade button in the same location. Add a restrained thin mint highlight to the Hull card's perimeter and tint its Lv. 3 tag mint as brief success feedback. No floating texts, extra card, confetti or major glow. The level and balance updates should be easy to notice but maintain a calm clear commercial UI.
Constraints: do not alter the ship appearance, room layout, other card values or salvage icons. No popup, Buy again button, auto-upgrade, maxed label, new currency, gold coins, earning rate, reward preview, repair charge, Start, nav arrow, footer, phone frame or option label. Keep all three current-to-next preview cards readable, unclipped and touch-friendly. Complete crisp polished 2D game UI, not concept art.
```

## B — confirm purchase

```text
Use case: precise-object-edit.
Asset type: finished commercial portrait 2D mobile-game Workshop UI screenshot.
Input image: the supplied current-to-next-stat Workshop screen is the EDIT TARGET. Preserve exact portrait dimensions and polished 2D doodle ink art, warm timber/stone maintenance room, recognizable yellow submarine on its cradle, Sushi Bar scene doorway, Workshop sign, and the accepted three-card layout. All money icons represent gear/scrap salvage, never restaurant coins. Preserve Harpoon and Collector cards exactly, including Lv. 2, their stat previews, and gear costs 160 and 90. Levels, values and costs are illustrative.
Primary request — OPTION B, PURCHASE CONFIRMATION: show the Workshop immediately AFTER tapping its Hull Upgrade button, BEFORE any purchase. Keep the top-right salvage balance exactly "320", and preserve all three underlying cards with their original levels, stats and costs, including Hull Lv. 2, "100 → 120" and gear cost "120".
Add a restrained translucent navy scrim over the room and underlying UI. Center one ivory paper confirmation card with rounded navy ink outline and slight shadow, about 76% screen width and 34% screen height. Exact large title "Upgrade Hull?". Below it, a compact shield icon with exact level change "Lv. 2 → Lv. 3", then stat label "Max hull" and exact values "100 → 120", then an easy-to-read gear salvage cost "120" next to exact word "Cost". Deliberate spacing with large rounded hand-ink text.
At the card bottom, two separate generous stacked actions: coral primary button with cream text exactly "Upgrade", then ivory outlined secondary button with navy text exactly "Cancel". This dialog shows a still-pending upgrade; no success feedback or balance deduction yet.
Constraints: no nested second popup, extra stats, new currency, gold coins, earning rate, reward preview, repair charge, Start, maxed label, nav arrow, footer, phone frame or option label. Do not alter the ship, room or underlying card values. The confirmation is readable and thumb-friendly. Complete crisp polished commercial 2D game UI, not concept art.
```

## B correction — remove duplicated background card

The initial confirmation edit added an extra card behind the modal. The final option restores the three original cards, preserving the confirmation contents. References: initial B output `exec-6d50542f-b531-4f98-9da3-54e535266f79.png` as edit target, and `22b-workshop-stat-preview.png` as the correct background.

```text
Use case: compositing, precise-object-edit.
Image 1 is the EDIT TARGET: a polished Workshop purchase-confirmation screen. Image 2 is the correct ORIGINAL WORKSHOP BACKGROUND. Correct a background duplication error only.
Preserve the entire opaque foreground confirmation panel from Image 1 unchanged: its exact dimensions, position, ivory paper, navy outline, title "Upgrade Hull?", shield icon, "Lv. 2 → Lv. 3", "Max hull", "100 → 120", cost gear "120", coral "Upgrade" and ivory "Cancel" buttons.
Replace all visible background pixels around this panel with Image 2's Workshop screen at exactly its original scale and positions, covered by the existing restrained navy scrim. The correct background has exactly THREE upgrade cards: Hull at the top, Harpoon in the middle, Collector at the bottom. They must stay at their Image 2 positions and be naturally occluded by the confirmation panel. Do NOT move any of these cards downward to reveal them. Do NOT invent any extra row behind or below the popup. In particular, remove the extra ghost upgrade-card row in Image 1; there must be only ONE Harpoon row and ONE Collector row. Keep the top-right balance "320", Workshop sign, doorway, yellow submarine and cradle as in Image 2. No purchase has happened.
Do not change card prices, stat previews, level tags, typography or illustration style. Same portrait dimensions, crisp polished commercial 2D doodle game UI. No fourth card, no added elements, no phone frame.
```

## B final correction — isolated review over room scenery

The first correction still duplicated the background list. The final correction edits the original `22b-workshop-stat-preview.png` and hides the list during review, using uninterrupted Workshop floor behind the single confirmation panel. This background treatment is illustrative; Cancel restores the three-card Workshop.

```text
Use case: precise-object-edit.
Asset type: polished commercial portrait 2D mobile-game Workshop purchase-review screenshot.
Input image: supplied Workshop stat-preview screen is the EDIT TARGET. Preserve exact portrait dimensions, polished doodle ink style, timber/stone room, Sushi Bar doorway, Workshop sign, yellow submarine on its maintenance cradle, and top-right salvage balance "320". This is BEFORE any Hull upgrade is bought.
First REMOVE ALL THREE existing bottom upgrade cards, their icons, texts, borders, and buttons from the scene. Restore uninterrupted matching warm ivory workshop FLOOR where they were. The room behind the forthcoming modal has NO upgrade rows, cards or buttons visible anywhere. No ghost outlines, no copied rows. This is an isolated purchase-review state; the three-card list returns after Cancel.
Then add EXACTLY ONE centered opaque ivory confirmation panel, about 76% screen width, with rounded navy ink outline and shadow. Position it in the middle of the screen, its whole perimeter visible. Add a restrained translucent navy scrim across the room behind it. The background remains recognizable but contains ONLY room scenery, the submarine and header, not a list of cards.
Panel contents, carefully spaced and highly legible:
Exact title "Upgrade Hull?".
Shield icon beside exact level change "Lv. 2 → Lv. 3".
Exact stat label "Max hull", then exact values "100 → 120".
Exact cost label "Cost" beside a gear-shaped salvage icon and exact value "120".
At bottom, TWO stacked generous buttons: coral primary button "Upgrade" in cream text, and ivory outlined secondary button "Cancel" in navy text.
Keep balance "320"; do not buy the upgrade or animate success yet. Level/stat/cost values are illustrative. No other popup or paper card on the entire screen. No Hull/Harpoon/Collector upgrade rows around or behind the panel, no extra action, gold coin, earning rate, recipe preview, Start, repair, footer, phone frame or option label. Finished crisp commercial 2D mobile-game UI, not concept art.
```
