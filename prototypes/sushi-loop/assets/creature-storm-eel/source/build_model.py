"""Storm Eel boss (v2, low-poly fish) — procedural model + rig.

Run inside Blender on an empty file (wm.read_homefile(use_empty=True) first):
exec(open(path).read()).

Axes: X right, +Y north (the eel's swim direction, away from the submarine),
Z up. 1 Blender unit = 1 grid cell. The eel swims north ahead of the ship, so
the camera sees its back and tail; it curls its head round to face south only
to attack. Faceted (flat-shaded) low-poly geometry, no smoothing.
"""
import math
import bpy, bmesh
from mathutils import Vector, Matrix

for me in list(bpy.data.meshes): bpy.data.meshes.remove(me)
for a in list(bpy.data.armatures): bpy.data.armatures.remove(a)
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob)

# ---------------------------------------------------------------- dimensions
Y_SNOUT = 3.2            # snout tip
LENGTH = 7.0             # snout -> tail tip
SIDES = 8                # octagonal cross-section (vertex on top and bottom)
RINGS = 34
SPINE_BONES = 14
NECK_S = 0.115           # head/body joint, as a fraction of LENGTH
JAW_S = 0.095            # back of the mouth

def lerp_tab(s, xs, ys):
    for i in range(len(xs) - 1):
        if xs[i] <= s <= xs[i + 1]:
            k = (s - xs[i]) / (xs[i + 1] - xs[i])
            return ys[i] + (ys[i + 1] - ys[i]) * k
    return ys[-1] if s > xs[-1] else ys[0]

S_TAB = [0.0, 0.025, 0.06, 0.10, 0.14, 0.25, 0.40, 0.55, 0.70, 0.85, 0.95, 1.0]
W_TAB = [0.05, 0.14, 0.23, 0.29, 0.30, 0.31, 0.29, 0.24, 0.17, 0.10, 0.055, 0.02]   # half width
H_TAB = [0.06, 0.16, 0.27, 0.35, 0.38, 0.42, 0.42, 0.38, 0.31, 0.22, 0.13, 0.05]   # half height
Z_TAB = [0.70, 0.73, 0.76, 0.78, 0.78, 0.78, 0.78, 0.78, 0.78, 0.78, 0.78, 0.78]   # spine height

def y_at(s): return Y_SNOUT - LENGTH * s
def s_at(y): return (Y_SNOUT - y) / LENGTH
def half_w(s): return lerp_tab(s, S_TAB, W_TAB) * 1.2
def half_h(s): return lerp_tab(s, S_TAB, H_TAB)
def spine_z(s): return lerp_tab(s, S_TAB, Z_TAB)

def mouth_k(s):
    """Fraction of the lower half kept by the upper head; the jaw supplies the rest."""
    return 0.32 if s <= JAW_S - 0.01 else min(1.0, 0.32 + (s - JAW_S + 0.01) / 0.05 * 0.68)

def mouth_z(s): return spine_z(s) - half_h(s) * mouth_k(s)

NECK_Y = y_at(NECK_S)
SPINE_Z = 0.78

# ---------------------------------------------------------------- materials
def srgb(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)

def mat(name, hexc, emit=None, strength=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    p = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    p.inputs["Base Color"].default_value = (*srgb(hexc), 1)
    p.inputs["Roughness"].default_value = 0.9
    p.inputs["Metallic"].default_value = 0.0
    if emit:
        p.inputs["Emission Color"].default_value = (*srgb(emit), 1)
        p.inputs["Emission Strength"].default_value = strength
    return m

M = {
    "body": mat("eel_body", "#1d2e66"),     # dark navy: reads against the turquoise seabed
    "belly": mat("eel_belly", "#34508e"),
    "fin": mat("eel_fin", "#2a4184"),
    "spot": mat("eel_spot", "#7ff4ff", "#5cf2ff", 2.5),   # glow strength is driven at runtime
    "eye": mat("eel_eye", "#9fe3ee"),
    "pupil": mat("eel_pupil", "#05070d"),
    "mouth": mat("eel_mouth", "#3b1630"),
}
MAT_ORDER = list(M)

# ---------------------------------------------------------------- helpers
PARTS = []   # (object, weights: dict or callable(co) -> dict)

def new_obj(name, bm, material, weights):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    for k in MAT_ORDER:
        ob.data.materials.append(M[k])
    idx = MAT_ORDER.index(material)
    for p in ob.data.polygons:
        p.material_index = idx
        p.use_smooth = False
    PARTS.append((ob, weights))
    return ob

def solidify(ob, thickness):
    mod = ob.modifiers.new("solid", "SOLIDIFY")
    mod.thickness = thickness; mod.offset = 0
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    ob.select_set(False)

def gem(name, center, size, material, weights, subdiv=1):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=1.0)
    bmesh.ops.transform(bm, verts=bm.verts, matrix=Matrix.Translation(center) @ Matrix.Diagonal((*size, 1)))
    return new_obj(name, bm, material, weights)

BONE_EDGES = [NECK_Y - (NECK_Y - y_at(1.0)) * i / SPINE_BONES for i in range(SPINE_BONES + 1)]
CENTERS = [(BONE_EDGES[i] + BONE_EDGES[i + 1]) / 2 for i in range(SPINE_BONES)]

def spine_weights(co):
    """Linear blend between neighbouring spine bones by rest Y; head in front of the neck."""
    y = co.y
    head_full = NECK_Y + 0.22
    if y >= CENTERS[0]:
        k = min(1.0, (y - CENTERS[0]) / (head_full - CENTERS[0]))
        return {"head": k, "spine_00": 1 - k} if k > 0 else {"spine_00": 1.0}
    for i in range(SPINE_BONES - 1):
        if CENTERS[i] >= y >= CENTERS[i + 1]:
            k = (CENTERS[i] - y) / (CENTERS[i] - CENTERS[i + 1])
            return {f"spine_{i:02d}": 1 - k, f"spine_{i + 1:02d}": k}
    return {f"spine_{SPINE_BONES - 1:02d}": 1.0}

def ring_s(i):
    return (i / RINGS) ** 1.18   # denser rings at the head

# ---------------------------------------------------------------- body + upper head
def build_body():
    bm = bmesh.new()
    rings = []
    for i in range(1, RINGS):
        s = ring_s(i)
        w, h, zc, mk = half_w(s), half_h(s), spine_z(s), mouth_k(s)
        ring = []
        for j in range(SIDES):
            a = 2 * math.pi * j / SIDES
            ca, sa = math.cos(a), math.sin(a)
            z = zc + ca * (h if ca >= 0 else h * mk)
            ring.append(bm.verts.new((sa * w, y_at(s), z)))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for j in range(SIDES):
            bm.faces.new((rings[i][j], rings[i][(j + 1) % SIDES], rings[i + 1][(j + 1) % SIDES], rings[i + 1][j]))
    nose = bm.verts.new((0, Y_SNOUT, spine_z(0) - 0.02))
    tail = bm.verts.new((0, y_at(1.0), spine_z(1.0)))
    for j in range(SIDES):
        bm.faces.new((rings[0][(j + 1) % SIDES], rings[0][j], nose))
        bm.faces.new((rings[-1][j], rings[-1][(j + 1) % SIDES], tail))
    bm.normal_update()
    ob = new_obj("eel_body", bm, "body", spine_weights)
    for p in ob.data.polygons:
        s = s_at(p.center.y)
        if p.normal.z < -0.55:
            # the flat underside of the upper head is the roof of the mouth
            p.material_index = MAT_ORDER.index("mouth" if s < JAW_S - 0.005 else "belly")
    return ob

# ---------------------------------------------------------------- lower jaw
def build_jaw():
    bm = bmesh.new()
    n = 7
    s_end = JAW_S + 0.045          # the wedge thins out where the belly is whole again
    rings = []
    for i in range(n + 1):
        s = 0.012 + (s_end - 0.012) * i / n
        w, zm = half_w(s) * 0.95, mouth_z(s)
        d = max(0.004, zm - (spine_z(s) - half_h(s)))   # flush with the belly line
        rings.append([
            bm.verts.new((-w, y_at(s), zm)),
            bm.verts.new((-w * 0.72, y_at(s), zm - d * 0.62)),
            bm.verts.new((0, y_at(s), zm - d)),
            bm.verts.new((w * 0.72, y_at(s), zm - d * 0.62)),
            bm.verts.new((w, y_at(s), zm)),
        ])
    for i in range(n):
        a, b = rings[i], rings[i + 1]
        for j in range(4):
            bm.faces.new((a[j], a[j + 1], b[j + 1], b[j]))
        bm.faces.new((a[4], a[0], b[0], b[4]))     # top: floor of the mouth
    tip = bm.verts.new((0, Y_SNOUT - 0.04, mouth_z(0.0) - 0.03))
    for j in range(4):
        bm.faces.new((rings[0][j + 1], rings[0][j], tip))
    bm.faces.new((rings[0][0], rings[0][4], tip))
    bm.faces.new(list(reversed(rings[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = new_obj("eel_jaw", bm, "belly", {"jaw": 1.0})
    for p in ob.data.polygons:
        if p.normal.z > 0.6:
            p.material_index = MAT_ORDER.index("mouth")
        elif p.normal.z > -0.2:
            p.material_index = MAT_ORDER.index("body")
    return ob

# ---------------------------------------------------------------- fins
def fin_strip(name, s0, s1, top, height, n, jag):
    bm = bmesh.new()
    base, edge = [], []
    for i in range(n + 1):
        s = s0 + (s1 - s0) * i / n
        zc, h = spine_z(s), half_h(s)
        rise = min(1.0, (s - s0) / 0.07) * min(1.0, (1.0 - s) / 0.09) ** 0.6
        fh = height(s) * rise * (1 + (jag if i % 2 else 0))
        if top:
            b, e = zc + h * 0.96, zc + h + fh
        else:
            b, e = zc - h * 0.96, zc - h - fh
        base.append(bm.verts.new((0, y_at(s), b)))
        edge.append(bm.verts.new((0, y_at(s) - 0.05 * fh, e)))
    for i in range(n):
        bm.faces.new((base[i], base[i + 1], edge[i + 1], edge[i]))
    ob = new_obj(name, bm, "fin", spine_weights)
    solidify(ob, 0.035)

def build_fins():
    # long moray dorsal fin from behind the head into the tail paddle
    fin_strip("eel_dorsal", 0.15, 0.995, True,
              lambda s: 0.12 + 0.12 * min(1.0, max(0.0, (s - 0.5) / 0.4)), 40, 0.12)
    # anal fin from mid-body; together with the dorsal it forms the pointed tail
    fin_strip("eel_anal", 0.50, 0.995, False,
              lambda s: 0.07 + 0.13 * min(1.0, max(0.0, (s - 0.6) / 0.35)), 24, 0.12)
    # small pectoral fins just behind the gill opening
    s = NECK_S + 0.03
    for side, name in ((-1, "L"), (1, "R")):
        root = Vector((side * half_w(s) * 0.92, y_at(s), spine_z(s) - half_h(s) * 0.25))
        bm = bmesh.new()
        vs = [bm.verts.new(root + Vector(o)) for o in (
            (0, 0.06, 0.05), (side * 0.16, -0.02, 0.06), (side * 0.27, -0.14, 0.02),
            (side * 0.28, -0.27, -0.06), (side * 0.15, -0.30, -0.11), (0, -0.10, -0.06))]
        bm.faces.new(vs if side > 0 else list(reversed(vs)))
        ob = new_obj(f"eel_pectoral_{name}", bm, "fin", {f"fin.{name}": 1.0})
        solidify(ob, 0.03)

# ---------------------------------------------------------------- face details
def build_face():
    H = {"head": 1.0}
    s = 0.05
    for side, name in ((-1, "L"), (1, "R")):
        # a fish eye: silvery iris with a big dark pupil, no lids
        c = Vector((side * half_w(s) * 0.86, y_at(s), spine_z(s) + half_h(s) * 0.36))
        gem(f"eel_eye_{name}", c, (0.05, 0.075, 0.075), "eye", H)
        gem(f"eel_pupil_{name}", c + Vector((side * 0.03, 0.004, 0.0)), (0.035, 0.052, 0.052), "pupil", H)
        # tubular front nostrils
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=5, radius1=0.028, radius2=0.018, depth=0.09)
        tip = Vector((side * 0.06, Y_SNOUT - 0.09, spine_z(0.013) + half_h(0.013) * 0.9 + 0.03))
        bmesh.ops.transform(bm, verts=bm.verts, matrix=Matrix.Translation(tip) @ Matrix.Rotation(-0.7, 4, "X"))
        new_obj(f"eel_nostril_{name}", bm, "body", H)
        # small round gill opening
        g = NECK_S + 0.005
        gc = Vector((side * half_w(g) * 0.97, y_at(g), spine_z(g) - half_h(g) * 0.05))
        gem(f"eel_gill_{name}", gc, (0.015, 0.035, 0.05), "pupil", spine_weights)

# ---------------------------------------------------------------- lateral glow organs
def build_spots():
    count = 15
    for side in (-1, 1):
        for k in range(count):
            s = 0.16 + (0.86 - 0.16) * k / (count - 1)
            w, h, zc = half_w(s), half_h(s), spine_z(s)
            size = 0.045 + 0.03 * (h / 0.42)
            c = Vector((side * (w * 0.93 + 0.012), y_at(s), zc + h * 0.18))
            gem(f"eel_spot_{side}_{k}", c, (0.025, size * 1.3, size), "spot", spine_weights, subdiv=1)

# ---------------------------------------------------------------- armature
def build_rig():
    arm = bpy.data.armatures.new("storm_eel_rig")
    rig = bpy.data.objects.new("storm_eel_rig", arm)
    bpy.context.scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm.edit_bones
    def bone(name, head, tail, parent=None, deform=True, connect=False):
        b = eb.new(name); b.head = head; b.tail = tail; b.roll = 0
        b.use_deform = deform
        if parent:
            b.parent = eb[parent]; b.use_connect = connect
        return b
    bone("root", (0, 0, 0), (0, 0.6, 0), deform=False)
    prev = "root"
    for i in range(SPINE_BONES):
        name = f"spine_{i:02d}"
        bone(name, (0, BONE_EDGES[i], SPINE_Z), (0, BONE_EDGES[i + 1], SPINE_Z), prev, connect=i > 0)
        prev = name
    bone("head", (0, NECK_Y, SPINE_Z), (0, Y_SNOUT, SPINE_Z), "spine_00")
    bone("jaw", (0, y_at(JAW_S + 0.03), mouth_z(JAW_S + 0.03)), (0, Y_SNOUT, mouth_z(0.0) - 0.03), "head")
    s = NECK_S + 0.03
    for side, name in ((-1, "L"), (1, "R")):
        x = side * half_w(s) * 0.92
        z = spine_z(s) - half_h(s) * 0.25
        bone(f"fin.{name}", (x, y_at(s), z), (x, y_at(s) - 0.3, z), "spine_00")
    bpy.ops.object.mode_set(mode="OBJECT")
    return rig

# ---------------------------------------------------------------- assemble
def build():
    build_body(); build_jaw(); build_fins(); build_face(); build_spots()
    for ob, weights in PARTS:
        for v in ob.data.vertices:
            w = weights(ob.matrix_world @ v.co) if callable(weights) else weights
            for g, val in w.items():
                vg = ob.vertex_groups.get(g) or ob.vertex_groups.new(name=g)
                vg.add([v.index], val, "REPLACE")
    bpy.ops.object.select_all(action="DESELECT")
    body = PARTS[0][0]
    for ob, _ in PARTS:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()
    body.name = body.data.name = "storm_eel"
    rig = build_rig()
    body.parent = rig
    mod = body.modifiers.new("rig", "ARMATURE"); mod.object = rig
    return body, rig

body, rig = build()
print("built", len(body.data.vertices), "verts", len(body.data.polygons), "faces")
