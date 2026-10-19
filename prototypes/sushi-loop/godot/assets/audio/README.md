# Original restaurant audio

These five PCM WAV files were synthesized specifically for issue #10 by `generate_audio.py`. No recordings, external samples, speech, existing songs or archived implementation assets were used. The generator uses the Python standard library and a fixed random seed for reproducible quiet brush noise.

- `click.wav`: short warm wooden UI response.
- `cook.wav`: restrained preparation taps.
- `load.wav`: soft ceramic plate placement.
- `coin.wav`: brief three-note sale chime.
- `harbor_cafe.wav`: original 19.2-second, eight-bar instrumental loop at 100 BPM, with soft keys, low bass and a very quiet brushed pulse. Instrument tails wrap across the loop boundary.

Audio is 22,050 Hz, signed 16-bit PCM. Cues are mono; music is stereo. Peak/RMS values and durations are recorded in `audio-verification.json`. Source headroom and playback attenuation keep the mix quiet.

Create one `RestaurantAudio` node from `res://scripts/audio.gd`; it starts the music automatically. Call `play_cue("click"|"cook"|"load"|"coin")` for presentation events. Aliases `ui`, `prepared`, `loaded` and `sale` accept the current public session event names. Calls never affect game state or timers. Repeated cues are rate-limited and dropped when all six voices are occupied. Application pause/focus loss pauses music and stops one-shot cues; resume continues the music without replaying stale effects. `set_muted(bool)` and `set_backgrounded(bool)` are available for host integration.
