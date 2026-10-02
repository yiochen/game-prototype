# Dumpling Disco

A one-thumb rhythm kitchen. Open `/prototypes/dumpling-disco/`.

The starting idea is a rhythm arcade. The branch replaces a note highway and multiple lanes with one little pan: closing rings are the score, a tap flips a dumpling, and a sustained press steams the trio. The feedback is a character performance, rather than a wall of accuracy statistics. Visual timing carries the whole game; optional synthesized tones provide a simple accompaniment. This is a prototype rhythm toy with three authored patterns, not a licensed soundtrack player.

## Play

- Tap the large pad when a thin gold ring meets the gold pan rim.
- A thick green ring asks for a hold. Keep pressing until the rim fills; the hold completes automatically.
- Space presses/releases the pad. Enter also works while the pad is focused.
- Missed beats briefly soften the dumplings' expressions and reset the streak; the set continues. Every finished set earns a star rating.
- The first visit offers two actual practice notes. Each waits at the timing line. Releasing the practice hold early rewinds it for another try.
- `?` pauses, reopens practice, or restarts the current mix. A hidden or unfocused tab pauses. An interrupted hold rewinds to its start so resuming needs no phantom finger press.
- Sound is opt-in. Reduced motion stops character bobbing, flips and sparkles while keeping essential ring movement and steam progress.

Tutorial completion and each mix's best score are stored locally when available. Mixes have 20–26 notes at 92, 108 and 122 bpm. Perfect inputs award 100 groove; good inputs award 65. All numbers and authored patterns live in `balance.js`.

## Implementation

`engine.js` owns timing, judgement, holds, scoring and practice gates. `world.js` draws the original vector kitchen, ring cues and dumplings with Phaser. `main.js` owns DOM controls, input lifetimes, pause, tutorials, results and optional Web Audio. The renderer never awards points. Assets and CSS are local to this game. Nunito is bundled under the SIL Open Font License in `assets/OFL.txt`; the cover is original SVG artwork.

```sh
node --test prototypes/dumpling-disco/tests/engine.test.js
npm run build
npx playwright test prototypes/dumpling-disco/tests/game.spec.js
```

Engine checks cover timing windows, lesson gates, duplicate scoring, interrupted holds, complete perfect runs and result ratings. Browser checks exercise keyboard and emulated touch input, cancellation, tutorial persistence, mix transitions, pause, sound and phone/landscape layouts. Screenshots are saved to ignored `artifacts/dumpling-disco/`.

`?test` exposes `window.__dumplingDisco` for snapshots and advancing the same timing engine. Ordinary sessions do not expose fixtures. Visual rings are the authoritative timing cue; the optional accompaniment is scheduled from frames and is not a sample-accurate audio clock.
