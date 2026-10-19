# Surface lighting review

The existing `#character-lighting-study` route now compares four subjects:
Noor, Conveyor belt, Wood crate and the three-module Connected conveyor.
Noor retains the original character captures and 35° camera. The environment
subjects use their native 70% square-grid camera and their own fixed frame/root.
Single objects sit on one square tile; the connected L occupies a 2×2 floor.
The original restaurant concept remains unchanged.

The same four preset cards display each subject. Full views and surface crops
reuse native PNGs directly, with no browser image filters or silhouette fitting.
The crate note explicitly records that the stronger presets lose some color
detail in its pale top boards; the comparison has not been retuned to hide this.
No treatment is selected and production assets are unchanged.

The connected South view includes 24 actual native frames at 12 fps. It starts
paused even without a reduced-motion preference. Play/Pause and one scrubber
control all four cards together. There is no eager decoding of the 96 animation
images; only the current native URLs are displayed by the full/detail views.

Subject selection is stored in the validated `lightingSubject` query parameter.
Reload keeps the selected subject, and changing it preserves other query fields
and the route hash. Unknown IDs fall back to Noor. Conveyor, crate, corner and
Noor object pages link directly to their matching subject.

Validation:

- 183 engine tests passed.
- Production build passed.
- Eight browser cases passed: the three original responsive Noor cases, three
  responsive environment cases, one complete 24-frame playback/closure case,
  and one deep-link/reload/object-navigation case.
- Tested 390×844, 844×390 and 1440×1000 layouts with one document scrollbar.
- Every native facing retains its subject's declared 4× dimensions, frame, root,
  square floor and common scale within each comparison.
- All 24 connected frame paths scrub in sync; playback wraps from 23 back to the
  start and freezes after Pause.
- `git diff --check` passed.

`engine.log`, `build.log` and `browser.log` preserve the final results.
The nine `environment-lighting-<subject>-<width>.png` screenshots preserve all
three environment subjects at phone, landscape and desktop widths. The three
desktop comparisons and the connected phone comparison were visually inspected.
