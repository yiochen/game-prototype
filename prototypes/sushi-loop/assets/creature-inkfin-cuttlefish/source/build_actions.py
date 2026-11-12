"""Inkfin Cuttlefish action set. Run after build_model.py, inside Blender.

It jets north in place (the game scrolls the world under it and the submarine), so
clips carry no forward root motion except `escape`. Clip names match the Storm Eel's,
so the runtime drives both creatures the same way.

Every bone's local axes equal the world's (see build_model.py):
X pitch (+ = north end up, so trailing arms droop with +X), Y roll, Z yaw.
- body: whole-animal location and rotation.
- mantle: scale (x, z) is the jet pulse; the ink sac swells it before a burst.
- fin.L/R_i: roll flaps the skirt fin; a phase step along the row makes a travelling wave.
- arms.L/R_i: yaw spreads or closes each side's four arms; pitch lifts or droops them.

Every action keys every bone, so switching clips never inherits a stale pose.
30 fps; loops close exactly.
"""
import math
import bpy

FPS = 30
TAU = 2 * math.pi
rig = bpy.data.objects["inkfin_rig"]
scene = bpy.context.scene
scene.render.fps = FPS
FINS = 5
ARMS = 3

for pb in rig.pose.bones:
    pb.rotation_mode = "XYZ"

def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)

def lerp(a, b, k): return a + (b - a) * k

def pose(loc=(0, 0, 0), pitch=0.0, roll=0.0, yaw=0.0, swell=1.0, stretch=1.0, tip=(0.0, 0.0),
         head=(0.0, 0.0), fin=None, spread=0.0, lift=0.0, sway=None, root=(0, 0, 0)):
    """Full bone pose.
    fin(side, i) -> upward flap in radians. spread: arms fan out (+) or close (-).
    lift: arms rise (+) or droop (-). sway(i) -> extra yaw for arm joint i, both sides."""
    out = {"root": {"l": root}, "body": {"l": loc, "r": (pitch, roll, yaw)},
           "mantle": {"s": (swell, stretch, swell)}, "mantle_tip": {"r": (tip[0], 0, tip[1])},
           "head": {"r": (head[0], 0, head[1])}}
    for side, name in ((-1, "L"), (1, "R")):
        for i in range(FINS):
            out[f"fin.{name}_{i}"] = {"r": (0, -side * (fin(side, i) if fin else 0.0), 0)}
        for i in range(ARMS):
            k = (0.5, 0.3, 0.2)[i]
            out[f"arms.{name}_{i}"] = {"r": (-lift * k, 0, side * spread * k + (sway(i) if sway else 0.0))}
    return out

def fin_wave(t, period, amp, base=0.0, step=1.05, mirror=True):
    """Travelling wave from the tip back to the collar; both sides in step unless mirror is off."""
    return lambda side, i: base + amp * math.sin(TAU * t / period - step * i + (0 if mirror or side < 0 else math.pi))

def make(name, frames, pose_at, loop):
    act = bpy.data.actions.get(name)
    if act:
        bpy.data.actions.remove(act)
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    rig.animation_data_create()
    rig.animation_data.action = act
    for f in range(frames + 1):
        p = pose_at(f)   # loops are periodic, so frame `frames` == frame 0
        for pb in rig.pose.bones:
            d = p.get(pb.name, {})
            pb.rotation_euler = d.get("r", (0, 0, 0))
            pb.location = d.get("l", (0, 0, 0))
            pb.scale = d.get("s", (1, 1, 1))
            for path in ("rotation_euler", "location", "scale"):
                pb.keyframe_insert(path, frame=f)
    act.frame_range = (0, frames)
    act.use_frame_range = True
    act["loop"] = loop
    return act

# ------------------------------------------------------------------ swim (loop 2 s)
SWIM_P = 60

def swim(f):
    a = TAU * f / SWIM_P
    pulse = math.sin(2 * a)                         # two gentle jet pulses per loop
    return pose(loc=(0.05 * math.sin(a), 0.03 * pulse, 0.03 * math.sin(a + 0.6)), yaw=0.03 * math.sin(a),
                swell=1 + 0.035 * pulse, stretch=1 - 0.02 * pulse, tip=(0.0, 0.04 * math.sin(a + 0.8)),
                fin=fin_wave(f, 30, 0.42), spread=-0.10 + 0.08 * pulse, lift=0.03 * pulse,
                sway=lambda i: 0.07 * math.sin(a - 0.7 * i))

# ------------------------------------------------------------------ restless (loop 1 s)
def restless(f, P=30):
    a = TAU * f / P
    return pose(loc=(0.04 * math.sin(a), 0.02 * math.sin(2 * a), 0.05 * math.sin(2 * a)), roll=0.07 * math.sin(a),
                swell=1 + 0.07 * math.sin(2 * a), stretch=1 - 0.03 * math.sin(2 * a),
                fin=fin_wave(f, 15, 0.6), spread=0.22 + 0.14 * math.sin(2 * a), lift=0.10,
                sway=lambda i: 0.12 * math.sin(2 * a - 0.9 * i))

# ------------------------------------------------------------------ hit (0.6 s)
def hit(f, D=18):
    t = f / D
    k = math.exp(-5 * t) * math.sin(TAU * 1.6 * t + 0.5)     # the jolt rings down
    burst = math.exp(-6 * t)
    back = swim(0)["body"]
    return pose(loc=(0.10 * k, 0.28 * burst * (1 - smooth(t * 3) * 0.6), 0.05 * k + 0.03 * math.sin(0.6)),
                pitch=0.28 * burst, roll=0.20 * k, swell=1 - 0.13 * burst, stretch=1 + 0.06 * burst,
                fin=lambda side, i: lerp(fin_wave(0, 30, 0.42)(side, i), 0.75, burst),
                spread=lerp(-0.10, 0.85, burst), lift=0.35 * burst,
                sway=lambda i: 0.25 * k * (i + 1) / 3)

# ------------------------------------------------------------------ hooked (loop 2/3 s)
def hooked(f, P=20):
    a = TAU * f / P
    jet = math.sin(a)
    return pose(loc=(0.07 * math.sin(a / 1 + 1.0), 0.07 * max(0.0, jet), 0.02 * jet), yaw=0.09 * math.sin(a + 0.4),
                pitch=0.06, swell=1 - 0.09 * jet, stretch=1 + 0.05 * jet, tip=(0.0, -0.06 * math.sin(a)),
                fin=fin_wave(f, 10, 0.7, base=-0.1), spread=-0.22 - 0.08 * jet, lift=-0.04,
                sway=lambda i: 0.10 * math.sin(a - 0.9 * i))

# ------------------------------------------------------------------ struggle (loop 0.8 s)
def struggle(f, P=24):
    a = TAU * f / P
    return pose(loc=(0.16 * math.sin(a), 0.04 * math.sin(2 * a), 0.05 * math.sin(2 * a + 1)),
                yaw=0.30 * math.sin(a + 0.5), roll=0.26 * math.sin(a), pitch=0.08 * math.sin(2 * a),
                swell=1 + 0.08 * math.sin(2 * a), tip=(0.0, -0.14 * math.sin(a + 0.5)),
                head=(0.0, -0.18 * math.sin(a + 0.2)),
                fin=fin_wave(f, 12, 0.8, mirror=False), spread=0.30 + 0.25 * math.sin(2 * a), lift=0.12,
                sway=lambda i: 0.42 * math.sin(a - 1.0 * i - 0.6))

# ------------------------------------------------------------------ ink burst: windup, attack, recover
SWELL = 1.24

def windup(f, D=30):
    # The ink sac fills: the mantle swells and trembles, the arms pull together, the fins tuck down.
    k = smooth(f / (D * 0.8))
    tremble = 0.018 * k * math.sin(TAU * f / 4)
    s0 = swim(0)
    return pose(loc=(0.0, lerp(s0["body"]["l"][1], -0.06, k), 0.03 + 0.05 * k), pitch=0.10 * k,
                swell=lerp(1.0, SWELL, k) + tremble, stretch=lerp(1.0, 0.94, k),
                fin=lambda side, i: lerp(fin_wave(0, 30, 0.42)(side, i), -0.38 + 0.05 * math.sin(TAU * f / 5 - i), k),
                spread=lerp(-0.10, -0.38, k), lift=lerp(0.0, -0.10, k),
                sway=lambda i: 0.03 * (1 - k) * math.sin(-0.7 * i))

def attack(f, D=18):
    # The burst: the mantle clamps down hard, the animal kicks north and the arms flare.
    t = f / D
    squeeze = smooth(t / 0.12)                       # clamped by 0.07 s
    hold = 1 - smooth((t - 0.70) / 0.30)             # locked until 0.42 s, then easing
    swell = lerp(SWELL, 0.80, squeeze)
    kick = math.sin(math.pi * min(1.0, t / 0.55)) * 0.34
    return pose(loc=(0.0, -0.06 + kick, 0.08 - 0.04 * squeeze), pitch=lerp(0.10, 0.16, squeeze) * hold + 0.02,
                swell=lerp(0.92, swell, hold), stretch=lerp(1.0, lerp(0.94, 1.10, squeeze), hold),
                fin=lambda side, i: lerp(-0.38, 0.55, squeeze) * hold,
                spread=lerp(-0.38, 0.95, squeeze) * hold, lift=lerp(-0.10, 0.30, squeeze) * hold,
                sway=lambda i: 0.05 * math.sin(TAU * f / 6 - i) * hold)

def recover(f, D=27):
    k = smooth(f / D)
    a, b = attack(18), swim(0)
    out = {}
    for name in a:
        out[name] = {}
        for key, default in (("l", (0, 0, 0)), ("r", (0, 0, 0)), ("s", (1, 1, 1))):
            va, vb = a[name].get(key, default), b[name].get(key, default)
            out[name][key] = tuple(lerp(x, y, k) for x, y in zip(va, vb))
    return out

# ------------------------------------------------------------------ escape (1.2 s, root motion north)
def escape(f, D=36):
    t = f / D
    jet = math.sin(TAU * f / 9)
    return pose(root=(0, 9.0 * t * t, 0), loc=(0.0, 0.05 * jet, 0.04 * t), pitch=0.08,
                swell=1 - 0.12 * max(0.0, jet), stretch=1 + 0.08 * max(0.0, jet),
                fin=lambda side, i: -0.45 + 0.12 * math.sin(TAU * f / 6 - i),
                spread=-0.40, lift=-0.05, sway=lambda i: 0.06 * math.sin(TAU * f / 9 - i))

# ------------------------------------------------------------------ exhausted (loop 2 s)
def exhausted(f, P=60):
    a = TAU * f / P
    b = math.sin(a)
    return pose(loc=(0.03 * b, 0.0, -0.22 + 0.03 * b), roll=1.05 + 0.05 * b, yaw=0.05 * b, pitch=-0.06,
                swell=1 + 0.02 * b, fin=lambda side, i: -0.25 + 0.10 * math.sin(a - 0.8 * i),
                spread=0.38, lift=-0.30, head=(-0.12, 0.10),
                sway=lambda i: 0.10 * math.sin(a - 0.6 * i) + 0.08 * (i + 1))

CLIPS = [
    ("swim", SWIM_P, swim, True),
    ("restless", 30, restless, True),
    ("hit", 18, hit, False),
    ("hooked", 20, hooked, True),
    ("struggle", 24, struggle, True),
    ("windup", 30, windup, False),
    ("attack", 18, attack, False),
    ("recover", 27, recover, False),
    ("escape", 36, escape, False),
    ("exhausted", 60, exhausted, True),
]
for name, frames, fn, loop in CLIPS:
    make(name, frames, fn, loop)
rig.animation_data.action = bpy.data.actions["swim"]
scene.frame_start, scene.frame_end = 0, SWIM_P
print("actions:", [c[0] for c in CLIPS])
