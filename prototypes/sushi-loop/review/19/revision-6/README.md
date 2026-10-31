# Issue 19 · Covered submarine feedback

[Open the verified preview](https://6ae3e93e612cf3f2ed531b77--game-prototypes-yiochen.netlify.app/prototypes/sushi-loop/design/expansion-preview/?state=covered) and tap the covered submarine.

Tapping the covered submarine now shows **Clear the surrounding trash to uncover the submarine.** The message uses the existing cream People/chef notice material, sits below the HUD, and dismisses after 3.2 seconds. Repeated attempts refresh its duration. It works in Live and Edit with touch, pointer and a named keyboard target, without changing coins, camera, access or layout. Selecting trash dismisses the notice; clearing the existing access car still enables the normal Submarine and Workshop targets.

The covered sprite participates in the same alpha-based depth selection as the trash, preserving selection of trash drawn in front. The notice is a polite status and does not receive focus or block world input. No new model, generation, cost or save schema is required.

The Vite build, 9 model checks and 15 focused browser checks pass. The new checks cover real touch activation, keyboard activation, unchanged state, dismissal, repeated attempts, and normal opening after access is cleared. Existing camera restoration, view bounds, cancellation, single-debit, placement and shared-state checks pass. Captures include Live and Edit toasts at 320×720, 390×844, 844×390 and 1440×1000; `capture-results.json` records no runtime or request errors.

All 15 browser checks also pass against the exact hosted draft. `deployment.json` records HTTP 200, no page/request errors, the exact toast text, unchanged model state after a pointer attempt, automatic dismissal and full restaurant coverage. `deployed-toast-390x844.png` shows the hosted result. `source-before/` preserves the previous app and style. The build retains its existing large-chunk warning. Broader repository failures from missing historical evidence remain documented in revision 2 and were not rerun for this change. Native production sources, approved model art and installed saves remain untouched.
