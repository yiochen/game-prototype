# Issue 19 · Edge-to-edge alternative

[Open the verified no-decor preview](https://6ae3e3176e676901e97241a9--game-prototypes-yiochen.netlify.app/prototypes/sushi-loop/design/expansion-preview/?state=bare).

The user requested a view without perimeter decor, with the restaurant extending edge to edge. Choose **Edge to edge · no decor** in the review selector, or use `?state=bare`. **Decor comparison** retains the previous treatment.

This option removes perimeter props and their ground bed. The existing room covers the view at uniform scale, with square tiles and panning bounded to its actual edges. The existing entrance backdrop remains. It adds no floor cells or capacity and requires no new artwork or native model changes. Native integration remains pending review approval.

The Vite build, 9 model checks and 12 focused browser checks pass. All 12 browser checks also pass against the exact hosted draft. The added browser check covers narrow phone, phone, landscape and wide review windows, extreme pan limits, fixed tile scale and switching back to the decorated view. Full scene captures and empty error lists are saved here; hosted proof is in `deployment.json`. The build retains its existing large-chunk warning. Broader repository failures from missing historical evidence remain recorded in revision 2 and were not rerun for this alternative.

`source-before/` preserves the prior app, style and model sources. The complete native acceptance audit remains in [revision 2](../revision-2/issue-audit.md); perimeter styling remains under user review through revisions 3–4. No native production sources or installed saves changed.
