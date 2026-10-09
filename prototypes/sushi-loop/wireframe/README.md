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

Clearly outlined targets are tappable. Muted controls are deliberately disabled. Native buttons and links support keyboard navigation; focus treatment is visible. Browser Back restores story navigation, and popup close controls return to the parent view. Scrims block clicks on the scene underneath; outside taps do not dismiss dialogs that require an explicit action.

Scene links connect Restaurant, Shop, Staff, Workshop and expedition preparation. Start opens a travel fixture; review controls advance through encounter, pursuit, catch, award and result states. Pause opens Resume and Return early; early return has its own confirmation. First-discovery flow goes through the recipe award; repeat catch goes directly to results. Results have one Restaurant continuation.

Shopping, hiring, leveling, firing, Prepare and Clear may change a displayed fixture or switch a story so their outcome can be reviewed. All sample prices, quantities, character profiles, durations, recipes and progression values are illustrative. No economy, real-time timers, service simulation, physics, game save, offline earnings calculation or reward persistence is implemented.

The component menu is review chrome. Labels such as advance-to-state are review controls, not proposed gameplay controls. The wireframe should make this distinction visible so a deterministic review action is not mistaken for a new game rule.

## Shared components

The React entry is `app.jsx`. `common.jsx` owns shared primitives such as icons, currency amounts, portraits and tappable targets. `components.jsx` owns shared composite components such as the dock, recipe tile, hull meter, Workshop upgrade card and salvage receipt. Full scenes in `scenes.jsx`, popups in `overlays.jsx`, and the standalone component pages must render these same React components. Do not make a separate look-alike copy for the gallery. Scene wrappers supply context, state fixtures and navigation; shared components own the reusable element structure and presentation. React and React DOM belong to this prototype’s package rather than the root’s shared game tooling.

The Shared components group has eight review pages: currency display, character portrait, dock with Workshop hut, recipe catalog tile, hull meter, upgrade card, salvage receipt, and tap target. Feedback on one of these pages can target the reusable component directly; updating that component must propagate to its integrated scenes. Whole-screen stories remain useful for checking spacing, composition and interaction context after a shared change.

## Feedback on each page

Every story has its own feedback draft through the shared React `feedback.jsx` module. Comments are stored locally in that browser and device; they are review notes, not game saves or synchronized project records. Use **Open GitHub feedback** to hand the selected page’s comment and story context to a prefilled GitHub issue form. Review and submit that form on GitHub to publish the feedback; opening the form alone does not create an issue. The wireframe does not need a Netlify backend, sign-in implementation, access token or secret to perform this handoff.

Use the Markdown export to collect all local story comments for sharing or backup. Local drafts do not automatically reach Codex, GitHub or another phone/browser. After submitting feedback, ask Codex to read the linked issue or PR and apply the requested changes. Codex can then update the concrete shared component or scene, refresh the preview, and show the affected examples for another review. A posted comment is feedback rather than implicit design approval; approved screens are recorded only after explicit approval.

## Coverage and annotation conventions

`stories.js` exports the story groups and story inventory consumed by the shell. Each story identifies its scene, variant and optional popup, with a description and a list of element behaviors and motion annotations. Notes distinguish accepted behavior from unresolved proposals. Animation durations are proposed targets for discussion, not approved tuning. Apply state changes on input rather than waiting for animation completion; reduce motion to short fades or immediate changes, retaining essential state feedback.

Stories cover the full floor plan; starter/expanded/live/edit/floor/selection/charging/reopen restaurant states; recipe eligibility, idle placement, unavailable, undiscovered and NEW states; roster, applicants, full capacity, chef detail, insufficient coins, maximum level and firing; normal/owned/unaffordable Shop; normal/maximum/unaffordable Workshop; preparation, travel, shooting window, pursuit, danger, pause, return confirmation and resume; first/repeat catches, recipe award and three result outcomes; expansion and inventory exhaustion.

The library also isolates eight shared components using the same code as their integrated appearances. Each component page includes behavior and state-transition motion notes; the overall library has 51 examples across nine groups.

The HUD follows the latest user direction: styled currency text and transparent scene controls, without cream/yellow UI backing containers. A wireframe outline marks targets for review. Physical scene signage and modal surfaces are distinct from those HUD containers. Character backgrounds and occupations should be varied; cultural identity is flavor, not a mechanic.

## Current open decisions

- Exact grid dimensions, garbage-patch geometry/costs, dock footprint/approach and restaurant expansion pacing.
- Whether later customer entries and submarine access activate when a connected cleared route reaches them. This is a proposal from the floor-plan discussion.
- Final touch insets, material treatment, illustrations, character cast and timing/amplitude of proposed animation.
- Applicant Refresh cooldown duration and whether its disabled button displays a countdown (UI interview Question 206 was deferred).
- Offline earnings behavior when the player closes while in edit mode, and all economy/throughput tuning.
- Fine-grained belt-placement states, trapped-customer rescue and individual customer reaction examples can extend the component library as designs are reviewed.

The three-panel sketch is the current floor-plan reference. Earlier generated restaurant mockups are useful style exploration but do not override this layout. Each screen and popup remains subject to the user’s review before being archived as an approved design.

Accepted source documents: [UI interview](../docs/ui-design-interview.md), [restaurant behavior](../docs/gameplay-and-controls.md), [expedition behavior](../docs/expedition-gameplay-and-controls.md), and [doodle art direction](../docs/art-direction.md).
