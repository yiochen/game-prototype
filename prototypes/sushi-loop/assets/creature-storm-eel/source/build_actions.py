"""Storm Eel (v2) action set. Run after build_model.py, inside Blender.

The eel swims north in place (the game scrolls the world under both the eel and
the submarine), so clips carry no forward root motion except `escape`.

Every bone is rotated only about its local Z (yaw: positive = counter-clockwise
seen from above) apart from head pitch (+X = snout up), jaw (-X = open) and the
root's roll. Body poses are given as per-joint yaw curvatures; `solve` places the
root so one chosen body joint stays put with a chosen heading, which lets the
front curl back on itself while the rest of the eel holds its line.

Every action keys every bone, so switching clips never inherits a stale pose.
30 fps; loops close exactly.
"""
import math
import bpy

FPS = 30
TAU = 2 * math.pi
rig = bpy.data.objects["storm_eel_rig"]
scene = bpy.context.scene
scene.render.fps = FPS
SPINE = sorted(b.name for b in rig.pose.bones if b.name.startswith("spine_"))
N = len(SPINE)
REST = [rig.data.bones[b].head_local.y for b in SPINE] + [rig.data.bones[SPINE[-1]].tail_local.y]
SEG = [REST[i] - REST[i + 1] for i in range(N)]
SPINE_Z = rig.data.bones[SPINE[0]].head_local.z
HALF_PI = math.pi / 2

for pb in rig.pose.bones:
    pb.rotation_mode = "XYZ"

def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)

# ------------------------------------------------------------------ body solver
def solve(c, anchor=3, heading=0.0, offset=(0.0, 0.0)):
    """Root yaw/location so joint `anchor` stays at rest (+offset) with bone
    `anchor` turned by `heading`. Returns (yaw, (x, y), head_dir) where head_dir
    is the world heading change of the head before its own yaw."""
    cum, total = [], 0.0
    for v in c:
        total += v; cum.append(total)
    yaw = heading - cum[anchor]
    # posed joints with the root at the origin
    p = (-math.sin(yaw) * REST[0], math.cos(yaw) * REST[0])
    joints = [p]
    for i in range(N):
        h = -HALF_PI + yaw + cum[i]
        p = (p[0] + SEG[i] * math.cos(h), p[1] + SEG[i] * math.sin(h))
        joints.append(p)
    tx, ty = offset[0], REST[anchor] + offset[1]
    loc = (tx - joints[anchor][0], ty - joints[anchor][1])
    return yaw, loc, yaw + cum[0]

def pose(c, anchor=3, heading=0.0, offset=(0.0, 0.0), z=0.0, roll=0.0,
         head_dir=0.0, head_free=None, pitch=0.0, jaw=0.0, fins=(0.0, 0.0)):
    """Build a full bone pose. The head is kept pointing `head_dir` from north
    unless `head_free` gives its yaw relative to the neck directly."""
    yaw, (x, y), neck = solve(c, anchor, heading, offset)
    head_yaw = head_free if head_free is not None else head_dir - neck
    # roll pivots about the spine line, not the seabed
    rx = -SPINE_Z * math.sin(roll)
    rz = SPINE_Z * (1 - math.cos(roll))
    out = {"root": {"r": (0, roll, yaw), "l": (x + rx * math.cos(yaw), y + rx * math.sin(yaw), z + rz)}}
    for i, b in enumerate(SPINE):
        out[b] = {"r": (0, 0, c[i])}
    out["head"] = {"r": (pitch, 0, head_yaw)}
    out["jaw"] = {"r": (-jaw, 0, 0)}
    out["fin.L"] = {"r": (0, 0, -fins[0])}
    out["fin.R"] = {"r": (0, 0, fins[1])}
    return out

def wave(t, period, amp0, grow, k=0.62, start=1):
    """Travelling curvature wave from head to tail; t in frames."""
    return [0.0 if i < start else (amp0 + grow * i) * math.sin(TAU * t / period - k * i) for i in range(N)]

def add(*cs):
    return [sum(v) for v in zip(*cs)]

def scale(c, k):
    return [v * k for v in c]

def fin_beat(t, period, amp=0.35, base=0.25):
    a = base + amp * (0.5 + 0.5 * math.sin(TAU * t / period))
    b = base + amp * (0.5 + 0.5 * math.sin(TAU * t / period + 1.3))
    return (a, b)

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

def swim_c(t, k=1.0):
    return scale(wave(t, SWIM_P, 0.05, 0.011), k)

def swim(f):
    return pose(swim_c(f), heading=0.03 * math.sin(TAU * f / SWIM_P),
                z=0.04 * math.sin(TAU * f / SWIM_P * 2),
                head_dir=0.05 * math.sin(TAU * f / SWIM_P - 0.6),
                pitch=0.03 * math.sin(TAU * f / SWIM_P * 2),
                jaw=0.04 + 0.03 * math.sin(TAU * f / SWIM_P * 2),
                fins=fin_beat(f, SWIM_P / 2))

# ------------------------------------- restless (loop 1 s, same hit silhouette)
def restless(f, P=30):
    jerk = math.tanh(3 * math.sin(TAU * f / P)) * 0.2
    return pose(wave(f, P, 0.055, 0.012), heading=0.04 * math.sin(TAU * f / P),
                head_dir=jerk, jaw=0.06 + 0.08 * max(0.0, math.sin(TAU * f / P * 3)),
                pitch=0.04 * math.sin(TAU * f / P * 2), fins=fin_beat(f, P / 3, 0.5))

# ------------------------------------------------------ hit (one shot 0.6 s)
def hit(f, D=18):
    k = f / D
    jolt = math.sin(math.pi * smooth(k / 0.3)) if k < 0.3 else 0.0
    rec = smooth(k / 0.12) * (1 - smooth((k - 0.2) / 0.8))
    kink = [0.0] * N
    for i in range(N):
        kink[i] = 0.22 * rec * math.sin(i * 1.1) * (1 if 3 <= i <= 11 else 0.3)
    c = add(swim_c(f, 1 - rec), kink)
    return pose(c, anchor=6, offset=(0.0, 0.25 * rec), z=0.08 * jolt,
                head_dir=-0.15 * jolt, pitch=0.25 * rec, jaw=0.4 * rec, fins=(0.8 * rec, 0.8 * rec))

# ---------------------------------------- hooked (loop): straining against the line
def hooked(f, P=20):
    pull = math.sin(TAU * f / P)
    return pose(wave(f, P, 0.075, 0.016), heading=0.06 * pull, offset=(0.0, -0.15 + 0.08 * pull),
                head_dir=0.22 * math.sin(TAU * f / P * 2), pitch=0.08,
                jaw=0.15 + 0.08 * math.sin(TAU * f / P * 2), fins=fin_beat(f, P / 2, 0.6, 0.3))

# ----------------------------------------------- struggle (loop): side-to-side thrash
def struggle(f, P=24):
    w = math.sin(TAU * f / P)
    c = [0.0] + [0.2 * w * math.sin(math.pi * i / 7.5) + 0.03 * math.sin(TAU * f / P * 2 - 0.7 * i) for i in range(1, N)]
    return pose(c, anchor=6, heading=0.10 * w, offset=(0.15 * math.sin(TAU * f / P + 1.0), -0.1),
                head_dir=-0.45 * w, pitch=0.1 + 0.08 * math.sin(TAU * f / P * 2),
                jaw=0.3 + 0.1 * math.sin(TAU * f / P * 2), fins=(0.9, 0.9))

# ------------------------------------- attack: turn the head back toward the ship
CURL_BONES = range(1, 6)
CURL_HEAD = 0.45
TURN_ANCHOR = 7

def curl_c(amount):
    per = (math.pi - CURL_HEAD) / len(CURL_BONES)
    return [per * amount if i in CURL_BONES else 0.0 for i in range(N)]

def turned(f, amount, jaw, pitch=-0.06, tremble=0.0):
    back = wave(f, SWIM_P, 0.0, 0.012, start=TURN_ANCHOR + 1)
    shake = [tremble * math.sin(TAU * f / 4 + i) for i in range(N)]
    c = add(curl_c(amount), scale(swim_c(f), 1 - amount), back if amount > 0 else [0] * N, shake)
    return pose(c, anchor=TURN_ANCHOR, head_free=-CURL_HEAD * amount, pitch=pitch * amount, jaw=jaw,
                fins=fin_beat(f, SWIM_P / 2, 0.3 + 0.3 * amount))

def windup(f, D=30):
    """Curl round (0.8 s), then hold facing the ship while the organs charge."""
    a = smooth(f / (D * 0.8))
    return turned(f, a, jaw=0.05 + 0.12 * a, tremble=0.02 * smooth((f / D - 0.6) / 0.4))

def attack(f, D=18):
    """Discharge: the jaw gapes and the body locks rigid while lightning fires
    (frames 3-12, ~0.1-0.4 s); the game spawns the bolt from the jaw tip."""
    k = f / D
    gape = smooth(k / 0.15) * (1 - smooth((k - 0.65) / 0.35))
    return turned(30 + f, 1.0, jaw=0.17 + 0.45 * gape, pitch=-0.06 + 0.15 * gape, tremble=0.035 * gape)

def recover(f, D=27):
    """Uncurl back into the forward swim."""
    a = 1 - smooth(f / D)
    return turned(48 + f, a, jaw=0.17 * a + 0.04)

# --------------------------------------- escape (one shot 1.2 s, root motion north)
def escape(f, D=36):
    k = f / D
    dash = smooth(k / 1.0) ** 1.7
    p = pose(wave(f * 2.2, SWIM_P, 0.06, 0.014), head_dir=0.0,
             offset=(0.0, 9.0 * dash), z=0.25 * dash, fins=(0.0, 0.0))
    return p

# ------------------------------------------------------- exhausted (loop 2 s)
def exhausted(f, P=60):
    b = math.sin(TAU * f / P)
    c = [0.0] + [0.05 * math.sin(i * 0.7) + 0.015 * math.sin(TAU * f / P - 0.5 * i) for i in range(1, N)]
    return pose(c, anchor=6, heading=0.02 * b, z=-0.28 + 0.03 * b, roll=1.15 + 0.04 * b,
                head_dir=0.08, pitch=-0.12, jaw=0.32 + 0.04 * b, fins=(-0.1, -0.1))

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
