# Map designer only — artwork rollback

The user requested reverting the artwork and retaining only the map designer.
Removed the underwater art study, earlier expedition preview, their tests,
generated asset packs and artwork review folders from the workspace/build.
These uncommitted sources remain recoverable outside the repository at:

`/Users/yiouchen/.codex/archives/game-prototype/issue21-artwork-20261102T170313Z`

The designer owns its original example geometry in `example-layout.js`. The
example export retains SHA-256
`4a4872420a856f54d5f9a2e8a036a3421c792ab4b8b4f8adb7c58ca2f19c6785`.
The Organic 80 JSON retains SHA-256
`1b999c79f6a2bffee13f81bfdbb6a0c8428da1b74dd1b06907ecde7f205f01c1`,
including all 25 user-painted opening rows. Local-storage key, export schema,
paint tools, generic two-color palette, bottom start and one-row navigation
are retained. The shared wireframe entry opens the designer. Former artwork
and expedition URLs redirect to it on the same draft origin.

Validation: 12 model/map tests and Vite build pass. `local-editor/` and
`local-organic/` record actual authoring/import/preset workflows at 1440×1000,
390×844, 320×720 and 844×390. Live checks are recorded in `live-editor/`,
`live-organic/` and `redirect-verification.json` after deployment.
