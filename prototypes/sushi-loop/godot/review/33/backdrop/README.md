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

## Android test release 0.4.9

[Download the signed APK](https://drive.google.com/file/d/1qGSvfEaqb3sSNqQ5Rcov9OPaTcYNx7aI/view?usp=drivesdk). Uploaded to the same My Drive root as the previous test releases; Drive readback matches the local APK size and MD5. Sharing permissions were unchanged.

Version 0.4.9 / code 49 retains `com.yiochen.sushilooptickets.review12`, the Restaurant Editor title and original release signer, so it updates the 0.4.8 review app. It includes the approved backdrop and preserves the released reachable-exit recovery fix.

All 13 native suites pass: 2,514 checks, including the expanded 48-check backdrop suite. The export is nondebuggable and passes package, signer, runtime catalog and excluded-file audits. Every runtime source hash still matches the signed build receipt. Nonsecret evidence is in `release-0.4.9/`. No device installation was performed.
