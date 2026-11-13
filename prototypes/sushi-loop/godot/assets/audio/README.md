# Original restaurant audio

These five PCM WAV files were synthesized specifically for issue #10 by `generate_audio.py`. No recordings, external samples, speech, existing songs or archived implementation assets were used. The generator uses the Python standard library and a fixed random seed for reproducible quiet brush noise.

- `click.wav`: short warm wooden UI response.
- `cook.wav`: restrained preparation taps.
- `load.wav`: soft ceramic plate placement.
- `coin.wav`: brief three-note sale chime.
- `harbor_cafe.wav`: original 19.2-second, eight-bar instrumental loop at 100 BPM, with soft keys, low bass and a very quiet brushed pulse. Instrument tails wrap across the loop boundary.

Dive cues for the Inkfin Cuttlefish's ink (#70), from the same generator: `ink_warn.wav` (three low glugs, one per warning pulse), `ink_burst.wav` (the ink bursting out: a falling bloop under a muffled whoosh with a few bubbles) and `ink_lift.wav` (a soft rising wash as the ink clears). The expedition presentation requests them through `cue_requested`.

Scene music, from the same generator; each loop wraps its tails like `harbor_cafe`. `RestaurantAudio.set_scene()` crossfades between them (0.9 s), and `Game._music_scene()` picks the scene every frame:

- `harbor_cafe.wav` (`restaurant`): the restaurant, including Edit and Shop.
- `tinker_dock.wav` (`workshop`): 20-second loop at 96 BPM in F; marimba arpeggio, a whistled tune and small hammer taps.
- `deep_current.wav` (`dive`): 24-second loop at 80 BPM in A minor; slow pads, echoing bells and a low swell. Plays in dive preparation, along the route, and on the outro, award and results.
- `portal_ride.wav` (`passage`): 14.5-second loop at 132 BPM in C lydian; racing arpeggios, a bouncing bass and a rising tune. Plays for the ride through the bonus passage behind a portal, from the top each time.
- `storm_chase.wav` (`boss`): 25.6-second loop at 150 BPM in D minor; driving bass, kick and snare, chord stabs and a lead. Plays from the creature's arrival until it is caught or gone, and restarts from the top each encounter; the remaining tracks resume where they left off.

Audio is 22,050 Hz, signed 16-bit PCM. Cues are mono; music is stereo. Peak/RMS values and durations are recorded in `audio-verification.json`. Source headroom and playback attenuation keep the mix quiet.

Create one `RestaurantAudio` node from `res://scripts/audio.gd`; it starts the music automatically. Call `play_cue("click"|"cook"|"load"|"coin")` for presentation events. Aliases `ui`, `prepared`, `loaded` and `sale` accept the current public session event names. Calls never affect game state or timers. Repeated cues are rate-limited and dropped when all six voices are occupied. Application pause/focus loss pauses music and stops one-shot cues; resume continues the music without replaying stale effects. `set_muted(bool)` and `set_backgrounded(bool)` are available for host integration.
