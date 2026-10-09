# Sushi Loop interactive wireframe

Status: **review draft**. The pages are navigation and component fixtures, not an approved UI or a playable game. They preserve the accepted interview behavior while keeping art, placement and unresolved product choices open for discussion.

Open `/prototypes/sushi-loop/` from the repository development server or a Netlify PR preview. The component menu works like a small Storybook: select a scene, popup, state or shared component; the adjacent notes describe target behavior and proposed motion. A story URL can be shared using its hash, for example `#floor-plan`, `#recipe-picker`, `#results-hull` or `#component-recipe-tile`. The full floor plan remains the default page and the first design to review.

On phones, the story menu and annotations are accessible without shrinking touch targets. Scene content retains a portrait presentation. The full restaurant overview can pan across three portrait-width panels; the panel divisions are camera guides, not walls.

## Run and verify

From the repository root:

```sh
npm install
npm run dev -- --host 0.0.0.0
npm run build
npm test
npm run test:browser
```

The development server’s LAN address can be opened on a phone connected to the same network. The PR’s Netlify preview offers a shareable HTTPS version; no production deployment is required. `npm test` covers existing game engines, while browser checks verify the wireframe’s links, popup controls, story selection and responsive layout.

## Review controls

Reset restores the original fixture, first résumé, roster page and camera position. Clearly outlined targets are tappable. Muted controls are deliberately disabled. Native buttons and links support keyboard navigation; focus treatment is visible. Browser Back restores story navigation, and popup close controls return to the parent view. Scrims block clicks on the scene underneath; outside taps do not dismiss dialogs that require an explicit action.

Scene links connect Restaurant, Shop, Staff, Workshop and expedition preparation. Start opens a travel fixture; review controls advance through encounter, pursuit, catch, award and result states. Pause opens Resume and Return early; early return has its own confirmation. First-discovery flow goes through the recipe award; repeat catch goes directly to results. Results have one Restaurant continuation.

Shopping, hiring, leveling, firing, Prepare and Clear may change a displayed fixture or switch a story so their outcome can be reviewed. All sample prices, quantities, character profiles, durations, recipes and progression values are illustrative. No economy, real-time timers, service simulation, physics, game save, offline earnings calculation or reward persistence is implemented.

Restaurant scene examples now focus on the floor plan: entries, garbage patches, the dock and a finished left wall remain, while belt, chef and customer decoration is omitted. A single neutral selection footprint remains in the selected-object example to demonstrate Rotate and Remove. This drawing scope does not change the accepted future service, placement, character or pause rules. Recipe and staff examples remain directly available through the explorer.

Pan the restaurant by finger drag or swipe at a fixed scale. Numeric panel shortcuts, edge pan carets and panel snapping are absent; Shop and Live/Edit transitions preserve the exact camera position. Edit and Staff sit at the bottom-left in live mode. Live sits at the top-right in edit mode, without a Service paused label. People, Layout and Floor buttons form a vertical right-side stack outside the bottom tray. Only the selected layer shows its name beside the icon; that name remains visible while its tray is collapsed. Tapping the active layer collapses or reopens its tray; selecting a different layer opens that layer content. The Floor tray shows pattern thumbnails only, with style names supplied through accessible labels rather than visible names, Owned captions or instructions.

Clearance confirmation contains the title, patch preview, Cancel and Clear with its coin cost on the button. It omits patch dimensions, expansion/panel numbers, explanatory copy, a separate price row and a redundant close X. When unaffordable, Clear is greyed out with no shortage reason or extra notice; Cancel and system Back preserve the underlying restaurant mode.

Submarine and Workshop share a 3 × 3 floor-cell footprint in the middle panel, with the Workshop to the submarine’s right so taller hut artwork does not cover it. Before access is available, patchwork rags cover both landmarks with small peek openings. Locked targets do not navigate; no Future access instruction is displayed. The standalone dock page and combined floor plans use the same renderer.

Recipe tiles and the fixed recipe-details board use their tier’s material texture rather than visible tier names. Distinct wood grain and metal patterns must remain distinguishable beyond color; tier information stays available in accessible descriptions. The picker header shows the chef’s level without a tier suffix, and the catalog keeps its accepted ordering without visible section headings. Inspection still preserves the chef’s current assignment; Prepare, current and NEW states remain unchanged.

Staff opens a bottom paginated tray over the restaurant rather than a fullscreen roster. Two chef profiles appear per page with accessible Previous/Next controls of at least 44 × 44 px; the shared fixture has four chefs to expose two pages. Tap a profile to open its stats popup; drag it to preview placement affordance. After 8 px of movement the source fades over 120 ms and a portrait ghost follows the pointer directly. A valid drop on the visible cleared starter floor shows a neutral assignment footprint while keeping the tray open; invalid or cancelled previews remove the ghost immediately. A 160 ms snap-back is proposed for the full game. Real adjacency, occupancy and belt-connection validation remain future game logic. Applicant browsing shows one paper resume at a time: left/right swipes or accessible Previous/Next controls browse the remaining pool, while explicit Hire commits the selected candidate. Browsing alone neither hires nor rejects. A resume enters over 180 ms and its track settles over 200 ms; hiring retains the accepted unassigned-roster and no-automatic-replacement rules.

The empty-inventory example uses an open Layout tray and a short nonmodal toast. It has no dialog, forced Shop/Keep editing choice, focus trap or navigation requirement. Proposed feedback fades in over 180 ms, holds for about 2.2 s and fades out over 180 ms, leaving the editor interactive.

The component menu is review chrome. Labels such as advance-to-state are review controls, not proposed gameplay controls. The wireframe should make this distinction visible so a deterministic review action is not mistaken for a new game rule.

## Shared components

The React entry is `app.jsx`. `common.jsx` owns shared primitives such as icons, currency amounts, portraits and tappable targets. `components.jsx` owns shared composite components such as `RestaurantHud`, `EditorControls`, the dock, recipe tile, hull meter, Workshop upgrade card and salvage receipt. `staff-tray.jsx` owns the shared `RosterTray`, and `applicants.jsx` owns the shared `ResumeDeck`. Full scenes in `scenes.jsx`, popups in `overlays.jsx`, and the standalone component pages must render these same React components. Do not make a separate look-alike copy for the gallery. Scene wrappers supply context, state fixtures and navigation; shared components own the reusable element structure and presentation. React and React DOM belong to this prototype’s package rather than the root’s shared game tooling.

The Shared components group has twelve review pages: restaurant HUD, editor controls, roster tray, applicant resume, currency display, character portrait, dock with Workshop hut, recipe catalog tile, hull meter, upgrade card, salvage receipt, and tap target. The shared `RestaurantHud` renders the coin count and floating Shop control in isolation and in combined restaurant views. `EditorControls` similarly renders the right-side layers, selected title, top-right Live action and bottom tray in both its component example and full edit views. Roster and resume components likewise appear in their isolated pages and integrated staff views. Feedback on one of these pages can target the reusable component directly; updating that component must propagate to its integrated scenes. Whole-screen stories remain useful for checking spacing, composition and interaction context after a shared change.

## Feedback on each page

Every story has its own feedback draft through the shared React `feedback.jsx` module. Comments are stored locally in that browser and device; they are review notes, not game saves or synchronized project records. Use **Open GitHub feedback** to hand the selected page’s comment and story context to a prefilled GitHub issue form. Review and submit that form on GitHub to publish the feedback; opening the form alone does not create an issue. The wireframe does not need a Netlify backend, sign-in implementation, access token or secret to perform this handoff.

Use the Markdown export to collect all local story comments for sharing or backup. Local drafts do not automatically reach Codex, GitHub or another phone/browser. After submitting feedback, ask Codex to read the linked issue or PR and apply the requested changes. Codex can then update the concrete shared component or scene, refresh the preview, and show the affected examples for another review. A posted comment is feedback rather than implicit design approval; approved screens are recorded only after explicit approval.

## Coverage and annotation conventions

`stories.js` exports the story groups and story inventory consumed by the shell. Each story identifies its scene, variant and optional popup, with a description and a list of element behaviors and motion annotations. Notes distinguish accepted behavior from unresolved proposals. Animation durations are proposed targets for discussion, not approved tuning. Apply state changes on input rather than waiting for animation completion; reduce motion to short fades or immediate changes, retaining essential state feedback.

Stories cover the full floor plan; starter/expanded/live/edit/floor/selection/charging/reopen restaurant states; recipe eligibility, idle placement, unavailable, undiscovered and NEW states; roster, applicants, full capacity, chef detail, insufficient coins, maximum level and firing; normal/owned/unaffordable Shop; normal/maximum/unaffordable Workshop; preparation, travel, shooting window, pursuit, danger, pause, return confirmation and resume; first/repeat catches, recipe award and three result outcomes; expansion and inventory exhaustion.

The library also isolates twelve shared components using the same code as their integrated appearances. Each component page includes behavior and state-transition motion notes; the overall library has 55 examples across nine groups.

The HUD follows the latest user direction: the styled coin count is at the upper-left of the viewport, with a floating Shop button below it. Both stay anchored while the restaurant pans. Shop has no physical entrance or floor footprint; it opens from live or edit mode, preserves that mode and exact camera position on return, and carries the refreshed-stock sparkle until Shop opens. HUD controls remain transparent without cream/yellow backing containers. A wireframe outline marks targets for review. The Workshop remains a physical hut to the submarine’s right within their shared 3 × 3 floor-cell footprint. Character backgrounds and occupations should be varied; cultural identity is flavor, not a mechanic.

The reference layout uses existing Sushi Loop controls only, as explicitly selected by the user. Its level meter, Settings, Tasks and extra Workshop shortcut are excluded from this wireframe. This scope choice is settled; detailed screen composition remains subject to review.

## Current open decisions

- Exact overall grid dimensions, garbage-patch geometry/costs, dock approach and restaurant expansion pacing. The combined submarine/Workshop footprint is settled at 3 × 3 floor cells.
- Whether later customer entries and submarine access activate when a connected cleared route reaches them. This is a proposal from the floor-plan discussion.
- Final touch insets, material treatment, illustrations, character cast and timing/amplitude of proposed animation.
- Applicant Refresh cooldown duration and whether its disabled button displays a countdown (UI interview Question 206 was deferred).
- Offline earnings behavior when the player closes while in edit mode, and all economy/throughput tuning.
- Fine-grained belt-placement states, trapped-customer rescue and individual customer reaction examples can extend the component library as designs are reviewed.

The three-panel sketch is the current floor-plan reference. Earlier generated restaurant mockups are useful style exploration but do not override this layout. Each screen and popup remains subject to the user’s review before being archived as an approved design.

Accepted source documents: [UI interview](../docs/ui-design-interview.md), [restaurant behavior](../docs/gameplay-and-controls.md), [expedition behavior](../docs/expedition-gameplay-and-controls.md), and [doodle art direction](../docs/art-direction.md).
