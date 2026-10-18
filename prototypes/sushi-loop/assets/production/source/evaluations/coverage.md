# Issue 33 production coverage contract

Prepared 2026-10-17 against branch head `989c51c7306147b89f4af4c40ed664fd98cff97a`; cached origin/main `c7160c598d97023b7503339771fe7e1e8e48d45f`. Concept is approved; finished assets are not yet approved. This is a prospective checklist, not a passing art review.

117 stable review entries across 17 families. Entries may expose cosmetic variants without multiplying separate pages. A static asset still gets N/E/S/W model views; rotational symmetry may make views visually equal and must be disclosed.

Every animated state and every direction uses exactly 12 fps and at least six unique sampled frames, normally 12–24 for loops. Duplicate closing keys are excluded. No per-pose alpha fitting. Static/frozen presentations are explicit.

Four required sections per object: isolated four directions; a 3×3 repeated/joined placement; interaction/scale composition; complete animation and variant browser. Use actual reusable sprites throughout. Publish honest partial coverage batches; never call planned cards complete.

## Inventory

| Family | Stable object ID | States | Variants | Interaction comparison |
| --- | --- | --- | --- | --- |
| W01 | floor-cream | static | default | chef-lena, belt-straight-e |
| W01 | floor-blue-wave | static | default | chef-lena, belt-straight-e |
| W01 | floor-checker | static | default | chef-lena, belt-straight-e |
| W02 | entry-finished | static | default | floor-cream, chef-lena |
| W02 | wall-middle | static | default | floor-cream, chef-lena |
| W02 | wall-inner-corner | static | default | floor-cream, chef-lena |
| W02 | wall-outer-corner | static | default | floor-cream, chef-lena |
| W02 | wall-end | static | default | floor-cream, chef-lena |
| W02 | plant-angular | static | default | floor-cream, chef-lena |
| W02 | barrel-wood | static | default | floor-cream, chef-lena |
| W02 | crate-wood | static | default | floor-cream, chef-lena |
| W02 | lantern-gold | ambient | default | floor-cream, chef-lena |
| W02 | sign-blank | static | default | floor-cream, chef-lena |
| W02 | slate-rock | static | default | floor-cream, chef-lena |
| W02 | dock-post-rope | static | default | floor-cream, chef-lena |
| W03 | stool-wood | static | default | customer-rosa, belt-straight-e |
| W03 | stool-blue | static | default | customer-rosa, belt-straight-e |
| W04 | belt-straight-n | running | default | dish-salmon, chef-lena |
| W04 | belt-straight-e | running | default | dish-salmon, chef-lena |
| W04 | belt-straight-s | running | default | dish-salmon, chef-lena |
| W04 | belt-straight-w | running | default | dish-salmon, chef-lena |
| W04 | belt-corner-n-e | running | default | dish-cucumber, chef-lena |
| W04 | belt-corner-e-n | running | default | dish-cucumber, chef-lena |
| W04 | belt-corner-n-w | running | default | dish-cucumber, chef-lena |
| W04 | belt-corner-w-n | running | default | dish-cucumber, chef-lena |
| W04 | belt-corner-s-e | running | default | dish-cucumber, chef-lena |
| W04 | belt-corner-e-s | running | default | dish-cucumber, chef-lena |
| W04 | belt-corner-s-w | running | default | dish-cucumber, chef-lena |
| W04 | belt-corner-w-s | running | default | dish-cucumber, chef-lena |
| W04 | belt-start-n | running | default | dish-eel, chef-lena |
| W04 | belt-start-e | running | default | dish-eel, chef-lena |
| W04 | belt-start-s | running | default | dish-eel, chef-lena |
| W04 | belt-start-w | running | default | dish-eel, chef-lena |
| W04 | belt-end-n | running | default | dish-eel, chef-lena |
| W04 | belt-end-e | running | default | dish-eel, chef-lena |
| W04 | belt-end-s | running | default | dish-eel, chef-lena |
| W04 | belt-end-w | running | default | dish-eel, chef-lena |
| W05 | chef-lena | idle, work, hold, load | default | belt-straight-e, chef-blackboard, dish-salmon |
| W05 | chef-omar | idle, work, hold, load | default | belt-straight-e, chef-blackboard, dish-salmon |
| W05 | chef-ama | idle, work, hold, load | default | belt-straight-e, chef-blackboard, dish-salmon |
| W05 | chef-mateo | idle, work, hold, load | default | belt-straight-e, chef-blackboard, dish-salmon |
| W05 | chef-noor | idle, work, hold, load | default | belt-straight-e, chef-blackboard, dish-salmon |
| W05 | chef-dalia | idle, work, hold, load | default | belt-straight-e, chef-blackboard, dish-salmon |
| W05 | chef-ellis | idle, work, hold, load | default | belt-straight-e, chef-blackboard, dish-salmon |
| W05 | chef-rowan | idle, work, hold, load | default | belt-straight-e, chef-blackboard, dish-salmon |
| W06 | chef-blackboard | idle, recipe-change | salmon-nigiri, cucumber-maki, eel-roll | chef-lena |
| W07 | customer-rosa | walk, stand, seated-wait, eat, sit-down, stand-up, happy, restless, puzzled, panic | default | stool-wood, belt-straight-e, dish-salmon |
| W07 | customer-ellis | walk, stand, seated-wait, eat, sit-down, stand-up, happy, restless, puzzled, panic | default | stool-wood, belt-straight-e, dish-salmon |
| W07 | customer-samir | walk, stand, seated-wait, eat, sit-down, stand-up, happy, restless, puzzled, panic | default | stool-wood, belt-straight-e, dish-salmon |
| W07 | customer-june | walk, stand, seated-wait, eat, sit-down, stand-up, happy, restless, puzzled, panic | default | stool-wood, belt-straight-e, dish-salmon |
| W08 | dish-salmon | static | default | chef-lena, belt-corner-n-e, customer-rosa |
| W08 | dish-cucumber | static | default | chef-lena, belt-corner-n-e, customer-rosa |
| W08 | dish-eel | static | default | chef-lena, belt-corner-n-e, customer-rosa |
| W08 | bubble-preference | appear, fade | salmon-nigiri, cucumber-maki, eel-roll | customer-rosa |
| W08 | bubble-happy | appear, happy-transition, fade | default | customer-rosa |
| W08 | bubble-puzzled | appear, fade | default | customer-rosa |
| W08 | bubble-panic | appear, fade | default | customer-rosa |
| W08 | coin-pop | pop | default | customer-rosa |
| W09 | garbage-sofa | clearance | normal, highlighted | floor-cream, chef-lena |
| W09 | garbage-car | clearance | normal, highlighted | floor-cream, chef-lena |
| W09 | garbage-shelving | clearance | normal, highlighted | floor-cream, chef-lena |
| W10 | dock-floor | static | default | submarine-yellow, dock-post-rope, workshop-hut |
| W10 | dock-entry | static | default | submarine-yellow, dock-post-rope, workshop-hut |
| W10 | workshop-hut | static | default | submarine-yellow, dock-floor |
| W10 | dock-cover | covered, uncover | default | submarine-yellow, dock-post-rope, workshop-hut |
| W11 | floor-underwater | scroll | default | submarine-yellow, rock-wall-middle |
| W11 | rock-wall-middle | static | default | submarine-yellow, rock-wall-middle |
| W11 | rock-wall-edge | static | default | submarine-yellow, rock-wall-middle |
| W11 | rock-wall-corner | static | default | submarine-yellow, rock-wall-middle |
| W11 | rock-wall-end | static | default | submarine-yellow, rock-wall-middle |
| W11 | rock-shelf-middle | static | default | submarine-yellow, rock-shelf-middle |
| W11 | rock-shelf-edge | static | default | submarine-yellow, rock-shelf-middle |
| W11 | rock-shelf-corner | static | default | submarine-yellow, rock-shelf-middle |
| W11 | rock-shelf-end | static | default | submarine-yellow, rock-shelf-middle |
| W11 | reef-middle | static | default | submarine-yellow, reef-middle |
| W11 | reef-edge | static | default | submarine-yellow, reef-middle |
| W11 | reef-corner | static | default | submarine-yellow, reef-middle |
| W11 | reef-end | static | default | submarine-yellow, reef-middle |
| W11 | wreck-middle | static | default | submarine-yellow, wreck-middle |
| W11 | wreck-edge | static | default | submarine-yellow, wreck-middle |
| W11 | wreck-corner | static | default | submarine-yellow, wreck-middle |
| W11 | wreck-end | static | default | submarine-yellow, wreck-middle |
| W11 | rock-half-width | static | default | submarine-yellow, rock-wall-middle |
| W11 | boulder-underwater | static | default | submarine-yellow, floor-underwater |
| W11 | column-broken | static | default | submarine-yellow, floor-underwater |
| W12 | decor-foreground-rock | static | default | submarine-yellow, creature-eel |
| W12 | decor-foreground-coral | static | default | submarine-yellow, creature-eel |
| W12 | decor-starfish | static | default | submarine-yellow, creature-eel |
| W12 | decor-midground-coral | ambient | default | submarine-yellow, creature-eel |
| W12 | decor-kelp | sway | default | submarine-yellow, creature-eel |
| W12 | decor-ruin-fragment | static | default | submarine-yellow, creature-eel |
| W12 | decor-background-rock | static | default | submarine-yellow, creature-eel |
| W12 | decor-background-wreck | static | default | submarine-yellow, creature-eel |
| W12 | decor-background-fish | swim | default | submarine-yellow, creature-eel |
| W12 | decor-bubbles | rise | default | submarine-yellow, creature-eel |
| W12 | decor-light-shafts | ambient | default | submarine-yellow, creature-eel |
| W13 | submarine-yellow | idle, travel, impact, protection, dock-charging, dock-ready | baseline, upgraded | workshop-hut, creature-eel, salvage-metal |
| W13 | sub-hull-panels | idle, active | baseline, upgraded | submarine-yellow |
| W13 | sub-harpoon-mount | idle, active | baseline, upgraded | submarine-yellow |
| W13 | sub-collector-inlet | idle, active | baseline, upgraded | submarine-yellow |
| W14 | salvage-metal | shimmer, attract, collect | plate, bent | submarine-yellow, floor-underwater |
| W14 | route-current | flow | default | submarine-yellow, floor-underwater |
| W14 | boost-trail | boost | default | submarine-yellow, floor-underwater |
| W14 | portal-rim | idle | default | submarine-yellow, floor-underwater |
| W14 | portal-entry | enter | default | submarine-yellow, floor-underwater |
| W14 | safe-passage | ambient | default | submarine-yellow, floor-underwater |
| W15 | creature-eel | swim, aim, restless, hook, pursuit, caught, escape, weave, dash, pause | default | submarine-yellow, harpoon-projectile, harpoon-cable, eel-warning-strip |
| W15 | creature-fish | swim, aim, restless, hook, pursuit, caught, escape, weave, dash, pause | default | submarine-yellow, harpoon-projectile, harpoon-cable, attack-swirl |
| W16 | harpoon-projectile | launch, flight, hook | default | submarine-yellow, creature-eel |
| W16 | harpoon-cable | normal, taut, fraying, break | default | submarine-yellow, creature-eel |
| W16 | following-strip | flow | default | submarine-yellow, creature-eel |
| W17 | attack-reef-fragments | windup, active, recovery | default | creature-eel, submarine-yellow, following-strip |
| W17 | attack-swirl | windup, active, recovery | default | creature-eel, submarine-yellow, following-strip |
| W17 | attack-lateral-current | windup, active, recovery | default | creature-eel, submarine-yellow, following-strip |
| W17 | eel-warning-strip | windup, active, recovery | default | creature-eel, submarine-yellow, following-strip |
| W17 | eel-lightning-symbol | windup, active, recovery | default | creature-eel, submarine-yellow, following-strip |
| W17 | eel-discharge | windup, active, recovery | default | creature-eel, submarine-yellow, following-strip |

## Registration and provenance

Environment: 128 px cells, fixed square top/front oblique projection. Blender x=X, depth=-Y, height=Z. Capture uses 45° orthographic plus √2 vertical projection stretch before rendering; no bitmap stretching. Default full frame 192×320/root (96,248), 4× native captures. Explicitly enlarge complete frames for larger objects rather than fitting silhouettes. People and rounded actors use ordinary orthographic art cameras with square pixels and actual matrices, sharing the same logical root/cell pitch.

Keep integer footprint/support/overhead occupancy, collision and art bounds distinct. Sitting characters retain an explicit seat socket/elevation and separate stool capture. All references, source model scripts, editable `.blend`, actual camera matrices, rig/animation records, native raw frames, registration guide and hashes must be retained. Blender source saving is not visual proof. Multiview and posed validation must show real scene geometry.

The approved skills require Blender MCP authorship for models, and complex tiles need a retained imagegen surface-refinement result after native capture. The user requests every object in Blender MCP, including conveyors; sparse SVG floor geometry may still calibrate the exact capture. A native control and an AI-refined output are labeled separately. Never claim a failed refinement or an untouched control is a passing refined asset.

## Belt acceptance

Exactly 20 directed modules: 4 straights, 8 ordered corner flows, 4 starts and 4 ends. All share port width, support height, phase and slat spacing. Build one connected system, then export registered independent modules. Fixed rails, moving deck. Show valid complete straight/corner/cap assemblies, a loop, separate routes, all join phases and offset-phase neighbors. Demonstrate a separate dish carried along a manually driven path and stationary dishes over running deck/corners/endpoints. Frozen uses a paused running frame. No T/cross/split/merge.

## Prospective skill suites

Prepared before this agent performed any generation: `evals-characters/run.json` (3 cases), `evals-tiles/run.json` (11 cases). Each freezes the installed full skill snapshot and suite/request hashes. Status is `prepared-not-run`; no unrelated fixture art was generated and no historic grades were changed. Actual project acceptance requires structural audits plus independent visual inspection of source/captures and phone-scale clips, not file presence alone.

## Audit usage

`python source-audit.py /absolute/path/to/manifest.json --report /absolute/path/to/report.json` reads source and PNG data only. `--strict` exits nonzero for incomplete production claims or missing required coverage. A schema adapter can be specified by keeping objects and clips in the canonical fields documented in the script; it must not invent absent evidence.

## Scope boundaries

Review presentation does not implement service, pathfinding, cooking, occupancy, prices, upgrades, damage, progression, rewards, capture/charge timers or save games. Exclude full HUD/dialogs, material pages, paper shops, results backdrops and full-screen cutscenes. No new creature species or belt junction mechanics. Issue 33 stays open until the user approves full scene assets on the live site.
