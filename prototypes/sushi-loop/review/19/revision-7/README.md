# Issue 19 · Keep the view still while clearing

[Open the verified preview](https://6ae3ea9652f7d3727343942c--game-prototypes-yiochen.netlify.app/prototypes/sushi-loop/design/expansion-preview/?state=bare).

The latest user instruction supersedes the earlier centering and restoration behavior: opening the garbage confirmation, Cancel/Back and successful Clear now keep the camera at its current position throughout. The automatic centering helper and stored inspection camera are removed, including in preselected clearance review states. Manual panning, restaurant bounds, focus-safe clipping and the submarine cleanup toast remain.

The Vite build, 9 model checks and 15 browser checks validate this revision. Browser assertions compare both saved coordinates and actual rendered room positions before inspection, while the confirmation is open, after clearing and after reload, across Live/Edit and 320×720, 390×844, 844×390 and 1440×1000 layouts. Touch selection and cancellation also assert no camera movement. Other focused checks cover the toast, single debit, placement, dock and shared components.

Current captures and `capture-results.json` are saved here with no runtime or request errors. All 15 browser checks also pass against the exact hosted draft. `deployment.json` records HTTP 200, no page/request errors, and identical camera coordinates and rendered room rectangles before selection, with the confirmation open, after Cancel and after Clear. Hosted screenshots use the `deployed-*` prefix. `source-before/` preserves the previous app and test. The existing build-size warning and previously documented missing historical-evidence failures remain outside this change. No native production source, model art, pricing or installed saves changed.
