# Game prototype

A collection of independent browser-game prototypes. Each game gets its own directory; shared tooling builds a single site with a prototype index.

## Run locally

Use Node 22 or newer:

```sh
npm ci
npm run dev
```

Open the local URL printed by Vite. The homepage lists all registered prototypes.

- [One More Card](prototypes/one-more-card/README.md) — `/prototypes/one-more-card/`
- [Its balance table](prototypes/one-more-card/balance.js)
- [Cloudtop Hotel](prototypes/cloudtop-hotel/README.md) — `/prototypes/cloudtop-hotel/`
- [Cloudtop Hotel design](prototypes/cloudtop-hotel/CLOUDTOP_HOTEL_DESIGN.md)

## Layout

```text
prototypes.json                 # Shared list of games and routes
prototypes/
  one-more-card/
    index.html
    main.js                     # UI
    engine.js                   # Rules and state
    balance.js                  # Prices, probabilities, effect strengths
    style.css
    README.md
    tests/
      engine.test.js
      game.spec.js
index.html / catalog.js         # Prototype index
vite.config.js                  # Builds every registered game
playwright.config.js
netlify.toml
```

## Add a prototype

1. Create `prototypes/<slug>/` with an `index.html` entry and its own game files. Use lowercase hyphenated slugs.
2. Add `{ "slug": "your-slug", "title": "Your Game", "description": "What you play" }` to `prototypes.json`.
3. Add engine tests as `tests/*.test.js` and browser tests as `tests/*.spec.js` inside that game's directory.
4. Run `npm run check`. The homepage and production build include the new entry automatically.

Cloudtop Hotel declares its Phaser dependency in its own package manifest, installed through npm workspaces.

Games can use different implementations. Keep their rules and balance independent; share tooling rather than game state.

## Verify

```sh
npm test
npm run build
npx playwright install chromium  # First browser setup, if needed
npm run test:browser
```

`npm run check` runs tests, build, and browser checks in order. Browser tests launch a fresh production preview at port 4175 so they cannot accidentally hit the old project. Set `TEST_URL` to test a deployed copy of this site.

## Host

The build produces `dist/`, containing the index and all registered games. Netlify builds from the repository root using `npm run build` and publishes `dist/`; `netlify.toml` also pins Node 22.

Production: https://game-prototypes-yiochen.netlify.app/ — Netlify site `game-prototypes-yiochen` (`a05448cf-3d0c-4100-9b1a-6d8a0d28c886`), connected to https://github.com/yiochen/game-prototype.

- Pushes to `main` automatically deploy production.
- Pull requests targeting `main` automatically build a Deploy Preview. The Netlify check on each PR links to the preview; new commits update the same preview URL after a successful build.
- Each preview contains every registered game. Open `/prototypes/cloudtop-hotel/` to review Cloudtop Hotel. Add `@netlify /prototypes/cloudtop-hotel/` to a PR description to make its Netlify preview comment link directly to the game.
- Manage builds and previews at https://app.netlify.com/projects/game-prototypes-yiochen/deploys.

For a manual draft after verification and building, run `npx netlify-cli deploy --dir dist --no-build --site a05448cf-3d0c-4100-9b1a-6d8a0d28c886`. Add `--prod` only when intentionally publishing to production. The older Midnight Noodle deployment remains separate. Do not deploy this repo over that site because it also hosts the original restaurant game.

## Import

One More Card was imported from `~/dev/life-sim/experiment/` at v23, including its balance configuration and tests. Its gameplay code is preserved; links, test paths, and documentation were adapted to this repository. The old copy remains in place to preserve the existing deployment. Continue prototype development here.
