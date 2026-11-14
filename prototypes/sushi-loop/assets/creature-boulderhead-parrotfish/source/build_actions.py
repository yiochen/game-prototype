"""Boulderhead Parrotfish action set. Run after build_model.py, inside Blender.

It swims north in place (the game scrolls the world under it), so no clip carries
forward root motion; the game moves it for the escape and adds the ram lunge and the
turn along its line in code. Clip names match the Storm Eel's.

Every bone's local axes equal the world's (see build_model.py):
X pitch (+ = north end up), Y roll, Z yaw.
- body: whole-animal location and rotation.
- spine_0..tail: yaw bends the body; the joints are chained, so a phase step from
  the head back makes a travelling wave that grows towards the tail.
- head: yaw against the trunk keeps the boulder steady while the tail sweeps.
- pec.L/R: roll flaps each pectoral fin (parrotfish row with them), yaw sweeps it.

Every action keys every bone, so switching clips never inherits a stale pose.
30 fps; loops close exactly.
"""
import math
import bpy

FPS = 30
TAU = 2 * math.pi
rig = bpy.data.objects["parrot_rig"]
scene = bpy.context.scene
scene.render.fps = FPS
CHAIN = ["spine_1", "spine_2", "tail"]
GROW = (0.55, 0.8, 1.0)       # share of the wave each joint takes, head to tail

for pb in rig.pose.bones:
    pb.rotation_mode = "XYZ"

def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)

def lerp(a, b, k): return a + (b - a) * k

def pose(loc=(0, 0, 0), pitch=0.0, roll=0.0, yaw=0.0, phase=0.0, wave=0.0, step=0.9, bend=0.0,
         head=0.0, flap=0.0, sweep=0.0, curl=0.0):
    """Full bone pose. The body wave: each chain joint yaws wave * GROW[i] * sin(phase - step * i),
    plus a steady `bend` (a curve to one side). curl lifts the tail (pitch). flap rolls the
    pectorals up (+) or down (-); sweep folds them back (+) against the body."""
    out = {"root": {}, "body": {"l": loc, "r": (pitch, roll, yaw)},
           "spine_0": {"r": (0, 0, wave * 0.25 * math.sin(phase + step) + bend * 0.3)},
           "head": {"r": (0, 0, head - wave * 0.3 * math.sin(phase + step))}}
    for i, name in enumerate(CHAIN):
        out[name] = {"r": (-curl * GROW[i], 0, wave * GROW[i] * math.sin(phase - step * i) + bend * GROW[i])}
    for side, name in ((-1, "L"), (1, "R")):
        out[f"pec.{name}"] = {"r": (0, -side * flap, side * sweep)}
    return out

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

def blend(a, b, k):
    out = {}
    for name in set(a) | set(b):
        out[name] = {}
        for key, default in (("l", (0, 0, 0)), ("r", (0, 0, 0)), ("s", (1, 1, 1))):
            va, vb = a.get(name, {}).get(key, default), b.get(name, {}).get(key, default)
            out[name][key] = tuple(lerp(x, y, k) for x, y in zip(va, vb))
    return out

# ------------------------------------------------------------------ swim (loop 2 s)
# A lazy tail beat (1 s) and pectorals rowing three times per loop.
SWIM_P = 60

def swim(f):
    a = TAU * f / 30
    r = TAU * f / 20
    return pose(loc=(0.03 * math.sin(a), 0.03 * math.sin(r), 0.04 * math.sin(r + 0.8)), roll=0.03 * math.sin(a),
                phase=a, wave=0.2, flap=0.18 + 0.42 * math.sin(r), sweep=0.25 + 0.2 * math.sin(r + 1.3))

# ------------------------------------------------------------------ restless (loop 1 s)
def restless(f, P=30):
    a = TAU * f / 15
    r = TAU * f / 10
    return pose(loc=(0.05 * math.sin(TAU * f / P), 0.03 * math.sin(a), 0.05 * math.sin(r)), roll=0.06 * math.sin(a),
                phase=a, wave=0.24, flap=0.2 + 0.55 * math.sin(r), sweep=0.15 + 0.25 * math.sin(r + 1.3))

# ------------------------------------------------------------------ hit (0.6 s)
def hit(f, D=18):
    t = f / D
    ring = math.exp(-5 * t) * math.sin(TAU * 1.8 * t + 0.4)   # the jolt rings down
    burst = math.exp(-6 * t)
    return blend(pose(loc=(0.08 * ring, 0.2 * burst, 0.06 * ring), pitch=0.22 * burst, roll=0.25 * ring,
                      phase=TAU * 2.2 * t, wave=0.1 + 0.3 * burst, bend=0.35 * ring, curl=0.25 * burst,
                      flap=0.9 * burst, sweep=-0.3 * burst), swim(0), smooth((t - 0.6) / 0.4))

# ------------------------------------------------------------------ hooked (loop 2/3 s)
# Straining north: hard, fast tail strokes, pectorals pulled back.
def hooked(f, P=20):
    a = TAU * f / P
    return pose(loc=(0.06 * math.sin(a), 0.06 * max(0.0, math.sin(2 * a)), 0.02 * math.sin(2 * a)), pitch=0.05,
                roll=0.05 * math.sin(a), phase=a, wave=0.3, flap=0.1 + 0.3 * math.sin(2 * a), sweep=0.55)

# ------------------------------------------------------------------ struggle (loop 0.8 s)
# Thrashing: the whole body whips side to side and rolls, fins flailing.
def struggle(f, P=24):
    a = TAU * f / P
    return pose(loc=(0.14 * math.sin(a), 0.04 * math.sin(2 * a), 0.05 * math.sin(2 * a + 1)),
                yaw=0.22 * math.sin(a + 0.5), roll=0.22 * math.sin(a), pitch=0.06 * math.sin(2 * a),
                phase=a, wave=0.42, step=1.1, bend=0.12 * math.sin(a + 1.2), curl=0.08 * math.sin(2 * a),
                flap=0.3 + 0.6 * math.sin(2 * a), sweep=0.1 * math.sin(a))

# ------------------------------------------------------------------ escape (1.2 s)
# A burst of full-power strokes, fins tucked flat; the game carries it off north.
def escape(f, D=36):
    a = TAU * f / 9
    k = smooth(f / 6)
    return blend(swim(0), pose(loc=(0.03 * math.sin(a), 0.0, 0.03), pitch=0.04, phase=a, wave=0.36,
                               flap=-0.1, sweep=0.85), k)

# ------------------------------------------------------------------ exhausted (loop 2 s)
# Caught: rolled on its side, the body curled and the tail barely moving.
def exhausted(f, P=60):
    a = TAU * f / P
    b = math.sin(a)
    return pose(loc=(0.03 * b, 0.0, -0.3 + 0.03 * b), roll=1.0 + 0.05 * b, pitch=-0.05, yaw=0.04 * b,
                phase=a, wave=0.06, bend=0.18, curl=0.1, flap=-0.35 + 0.12 * math.sin(a * 2), sweep=0.6)

CLIPS = [
    ("swim", SWIM_P, swim, True),
    ("restless", 30, restless, True),
    ("hit", 18, hit, False),
    ("hooked", 20, hooked, True),
    ("struggle", 24, struggle, True),
    ("escape", 36, escape, False),
    ("exhausted", 60, exhausted, True),
]
for name, frames, fn, loop in CLIPS:
    make(name, frames, fn, loop)
rig.animation_data.action = bpy.data.actions["swim"]
scene.frame_start, scene.frame_end = 0, SWIM_P
print("actions:", [c[0] for c in CLIPS])
