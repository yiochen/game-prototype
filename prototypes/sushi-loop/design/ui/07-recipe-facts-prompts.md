# Recipe reveal information options

Pending UI interview Question 7. Option A uses a built-in image generation edit of [the selected recipe reveal card](./06b-recipe-reveal-card.png). Option B reuses that existing art-and-name card rather than generating an identical copy. All numeric recipe facts are illustrative, not balance decisions.

## A — compact recipe facts

```text
Use case: precise-object-edit, polished commercial mobile game UI.
Image 1 is the selected recipe reveal card screenshot. Preserve the portrait size, commercial 2D doodle ink style, navy/teal ocean-bed background, submarine, headlight, celebration sparkles, top hull badge, salvage "72", pause, paper card, curled corner, coral "NEW RECIPE", dish illustration, exact recipe name "Eel Nigiri", and coral "Continue" button. This is the same accepted reveal card, with recipe facts added.
Change ONLY the card's internal layout to fit a tidy compact row of THREE equal fact columns between the recipe name and Continue. Make the card a little taller if needed, keep it clear of the submarine below, reduce food art modestly, preserve generous spacing and large readable type. Card should remain a polished celebratory reward rather than a spreadsheet.
Three columns, each with a small hand-drawn matching icon, a concise dark label, and larger dark value:
1. restaurant COIN icon, exact label "Price per dish", exact value "18".
2. stopwatch icon, exact label "Base prep", exact value "6s".
3. chef hat icon, exact label "Chef quality", exact value "3+".
Fit labels on two lines if necessary; no tiny type. Coins are restaurant currency, not gear-shaped salvage. Chef quality is a cooking requirement, not a star rating or hiring level. Use exact spelling and numbers. All sample values are illustrative.
No earnings per second/minute, quality stars, chef roster, assignment button, ingredient list, new currency, collection progress, purchase/claim button, extra footer, phone frame or other UI changes. The one action stays "Continue". Keep full food plate and text visible.
```

## B — art and name only

Reuse [the selected reveal card](./06b-recipe-reveal-card.png), with no extra fact row. Its [original generation prompt](./06-recipe-reveal-prompts.md) is preserved.

