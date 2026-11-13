"""Reef cues for the #76 review: original deterministic synthesis, no samples.

Same approach and sample rate as godot/assets/audio/generate_audio.py; on approval these move there.
  reef_breach  the parrotfish's first ram into a reef wall: a double boom, a long rumble, rubble rain
  reef_smash   each row it breaks after that: a short thump and crunch with a few pebbles
  reef_crash   the submarine ramming reef: a metal clank on top of the crunch
"""
from pathlib import Path
import math, random, struct, wave

RATE = 22050
OUT = Path(__file__).parent
TAU = math.tau


def write(name, samples, peak):
    scale = peak / (max(abs(v) for v in samples) or 1)
    with wave.open(str(OUT / (name + '.wav')), 'wb') as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(RATE)
        f.writeframes(struct.pack('<' + 'h' * len(samples), *[round(v * scale * 32767) for v in samples]))


def sweep(buffer, start, duration, f0, f1, gain, decay=4.0, attack=.004):
    """Falling sine: the body of an impact."""
    onset = round(start * RATE); length = round(duration * RATE); phase = 0.0
    for i in range(length):
        k = i / length
        phase += TAU * (f1 + (f0 - f1) * (1 - k) ** 3) / RATE
        env = min(1.0, i / (RATE * attack)) * math.exp(-decay * k) * min(1.0, (length - i) / (RATE * .02))
        if onset + i < len(buffer): buffer[onset + i] += math.sin(phase) * gain * env


def crunch(buffer, start, duration, gain, rng, low=.0, high=.0, decay=8.0):
    """Band-limited noise: `low` smooths away the hiss, `high` removes the rumble (0 keeps all)."""
    onset = round(start * RATE); length = round(duration * RATE); lp = hp = 0.0
    for i in range(length):
        lp = low * lp + (1 - low) * rng.uniform(-1, 1)
        hp = high * hp + (1 - high) * lp
        k = i / length
        env = min(1.0, i / (RATE * .002)) * math.exp(-decay * k)
        if onset + i < len(buffer): buffer[onset + i] += (lp - hp) * gain * env


def ring(buffer, start, duration, frequency, gain, decay=9.0):
    """A struck metal partial."""
    onset = round(start * RATE); length = round(duration * RATE)
    for i in range(length):
        t = i / RATE
        if onset + i < len(buffer): buffer[onset + i] += math.sin(TAU * frequency * t) * gain * min(1.0, t / .001) * math.exp(-decay * t)


def pebbles(buffer, start, span, count, gain, rng):
    """Small fragments landing: short bright ticks thinning out."""
    for n in range(count):
        at = start + span * (n / count) ** 1.4 + rng.uniform(0, span / count)
        crunch(buffer, at, .025 + rng.uniform(0, .02), gain * (1 - .6 * n / count) * rng.uniform(.6, 1), rng, .1, .75, 6)


def bubbles(buffer, start, count, gain, rng):
    for n in range(count):
        f = rng.uniform(420, 760)
        sweep(buffer, start + n * rng.uniform(.04, .09), .06, f, f * 1.7, gain, 3, .006)


rng = random.Random(762026)

smash = [0.0] * round(.55 * RATE)
sweep(smash, 0, .32, 170, 46, .9, 3.2)
crunch(smash, 0, .2, 1.2, rng, .2, 0, 10)
crunch(smash, .01, .32, .7, rng, .6, 0, 7)
pebbles(smash, .08, .38, 7, .5, rng)
bubbles(smash, .12, 3, .05, rng)
write('reef_smash', smash, .42)

breach = [0.0] * round(1.3 * RATE)
sweep(breach, 0, .5, 150, 38, 1.0, 2.6)
sweep(breach, .1, .45, 120, 34, .8, 2.8)
crunch(breach, 0, .3, 1.4, rng, .15, 0, 9)
crunch(breach, .02, 1.2, .9, rng, .96, 0, 3.2)
crunch(breach, .1, .35, .8, rng, .5, 0, 6)
pebbles(breach, .15, 1.0, 16, .55, rng)
bubbles(breach, .25, 6, .05, rng)
write('reef_breach', breach, .5)

crash = [0.0] * round(.5 * RATE)
for f, g, d in [(312, .5, 11), (497, .35, 13), (781, .25, 16), (1163, .15, 20)]:
    ring(crash, 0, .45, f, g, d)
sweep(crash, 0, .22, 120, 52, .8, 3.5)
crunch(crash, 0, .18, 1.1, rng, .25, 0, 10)
pebbles(crash, .05, .3, 6, .5, rng)
write('reef_crash', crash, .48)
print('wrote reef_smash, reef_breach, reef_crash')
