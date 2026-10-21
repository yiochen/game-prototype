# Approved restaurant backdrop integration

[Published catalog](https://6ad83979c722d341e3175395--game-prototypes-yiochen.netlify.app/prototypes/sushi-loop/?ntl-drawer-state=hidden#object-library). The blank wall and entrance have individual catalog
pages with their actual sprites and downloadable editable Blender source.

Layout: blank wall at columns 0,1,2; four-tile entrance at 3–6; blank wall at every
remaining column 7–20. The entrance opening covers two whole columns, 4 and 5.
Rows 0–2 are reserved and are excluded from object placement and guest routing.
The approved uniform lighting, honey wood, baseboard and flat roof are unchanged.

The old entrance sprite exports, active native capture records and builder are
removed. Its 88 objects are removed from the current editable master, which now
includes the approved backdrop scene. Unrelated assets retain their immutable
source/capture snapshots. Character and feedback variants retain their exact
source objects, captures and PNGs; a compatibility receipt binds their unchanged
base records to the revised catalog.

Legacy shipped saves preserve furniture, inventory, coins, clocks and visits.
If an edited layout used the reserved rows, it moves down together and gains
three floor rows. Old doorway visitors move onto free floor and replan. Thirty-three
seeded legacy save points verify valid reopening with no rewards replayed.

Validation: 193 engine/tooling tests; 12 native suites / 2,435 checks; 19 browser
checks passed (one inapplicable queued-object test skipped); 64 packaging tests;
Vite build and actual Android runtime preflight passed. Native rendered phone and
landscape captures are in `godot/review/33/backdrop/`. The isolated runners never
load the installed game's save data. This task updates the source project; it
does not install a device build.

See `model-retirement.json`, `variant-compatibility.json`, `published-check.json`,
`checks.json` and the saved logs for evidence.
