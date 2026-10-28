# Issue 18 · maple popup revision

The user requested the existing wood grain popup family and a beige rounded scroll view matching the recipe picker. Shop directly reuses `.wr-panel` and `.wr-catalog` from `wireframe/recipe-maple.css`: grain, maple rim and shadow, beige fill, and inset shadow. Four rounded corners clip the scrolling catalog independently of the header/footer. The same shared close X, Edit-only tray entry, pause, saved inventory, hidden/restored tray, and independent purchase-to-bag flights remain.

The original paper asset is no longer used; its source and generation records remain as historical evidence. No replacement raster artwork was generated. The approved grain tiles at its original shared size instead of stretching a full popup image.

Evidence covers 320×720, 390×844, 844×390 and 1440×1000: Shop, purchase flights/arrival, disabled and sold-out goods, Shared pressed, Edit entry, Live without Shop and selected placement. Visual inspection checked rounded list clipping, cost contrast, equal insets, stable header/close, bag clearance and matching materials against the current recipe picker. Browser capture errors: zero.

Build, five model tests and fifteen feature browser checks passed. Native gameplay integration still awaits approval of the deployed prototype.
