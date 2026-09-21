# Game prototype workspace

- Each game lives in `prototypes/<slug>/` and owns its engine, UI, balance config, assets, and tests.
- `prototypes.json` is the shared catalog for the homepage and Vite build entries. Register new games there.
- Keep balance tables separate from gameplay rules. For One More Card, edit `balance.js` to tune costs, odds, and strengths.
- Keep games independent: no imports from sibling games or from the old life-sim repository.
- The root shares only development, build, hosting, and test tooling. Add game-specific dependencies only when needed.
- Run engine tests, the build, and relevant browser checks for behavior changes. Preserve phone and landscape layouts.
- This repository is linked to the Netlify site `game-prototypes-yiochen` (`a05448cf-3d0c-4100-9b1a-6d8a0d28c886`). Do not deploy it to the old Midnight Noodle site.
