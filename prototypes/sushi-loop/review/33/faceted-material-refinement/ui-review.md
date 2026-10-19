# Faceted material refinement — UI review

The review keeps **Faceted** selected and shows original versus tuned materials
side by side for the straight conveyor, wood crate and connected conveyor.
Noor retains the original four-preset comparison with Faceted marked as chosen.
The production library is unchanged. Source links distinguish the new two-variant
Blender project from the preserved historical lighting project.

The environment panels read the new native manifest and PNGs directly. Only the
manifest's two review variants are displayed; counts are derived from the active
variants and four facings. Both cards share the declared frame, root, crop,
projection and floor footprint. No browser image filters are applied.

## Verification

- `npm test`: **183 passed**, no failures or skips (`engine.log`).
- `npm run build`: **passed** (`build.log`).
- `npx playwright test prototypes/sushi-loop/tests/character-lighting-study.spec.js`:
  **8 passed** (`browser.log`). The three responsive environment cases also
  passed after the final per-object caption update (`caption-refresh.log`);
  their screenshot proofs were refreshed against the final build.
- Phone 390 × 844, landscape 844 × 390 and desktop 1440 × 1000: all subjects and
  four facings decode at native 4× dimensions, retain equal registration, fit
  within the viewport and use one document scroller. No JavaScript page errors.
- Connected conveyor: starts paused even without reduced-motion preference;
  both variants scrub through all **24 native frames** in sync, play at 12 fps,
  wrap frame 23 to 0, and pause without frame drift. N/E/W retain native stills.
- Subject deep links survive reload, preserve other query fields and match
  crosslinks from the crate, straight belt, corner belt and Noor object pages.

Comparison crops are named `environment-lighting-<subject>-<width>.png`.
The full phone page is `faceted-materials-phone-full-page.png`; Noor proofs are
`character-lighting-<width>.png`. Desktop belt/crate crops and the full phone page
were visually inspected: the muted rail top remains distinct from its side, the
crate top retains warm wood color and the two-card mobile controls/text fit.

Lighting selection is approved; material treatment and final game-scene asset
approval remain pending user review. Issue 33 is kept open.
