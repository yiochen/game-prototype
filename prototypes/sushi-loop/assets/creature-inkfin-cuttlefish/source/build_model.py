"""Inkfin Cuttlefish (issue #70, low-poly) — procedural model + rig.

Run inside Blender on an empty file (wm.read_homefile(use_empty=True) first):
exec(open(path).read()).

Axes: X right, +Y north (the travel direction, away from the submarine), Z up.
1 Blender unit = 1 grid cell. Like a real cuttlefish fleeing, it jets mantle-first:
the pointed mantle tip leads north and the head and arms trail south, towards the
ship, so the camera sees its patterned back, eyes and arms, and the funnel (the ink
source) points back at the ship. Faceted (flat-shaded) low-poly geometry, as the
Storm Eel.

Every bone points +Y with roll 0, so bone-local axes equal world axes:
X pitch (+ = north end up), Y roll, Z yaw (+ = counter-clockwise from above).
"""
import math
import bpy, bmesh
from mathutils import Vector, Matrix

for me in list(bpy.data.meshes): bpy.data.meshes.remove(me)
for a in list(bpy.data.armatures): bpy.data.armatures.remove(a)
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob)

# ---------------------------------------------------------------- dimensions
ZC = 0.80                # body centre height above the seabed
Y_TIP = 1.50             # mantle tip (north)
MANTLE = 2.60            # tip -> collar
Y_COLLAR = Y_TIP - MANTLE
Y_HEAD_END = Y_COLLAR - 0.62
SIDES = 10
RINGS = 15
FIN_BONES = 5
ARM_BONES = 3
ARM_LEN = 1.15

def lerp_tab(s, xs, ys):
    for i in range(len(xs) - 1):
        if xs[i] <= s <= xs[i + 1]:
            k = (s - xs[i]) / (xs[i + 1] - xs[i])
            return ys[i] + (ys[i + 1] - ys[i]) * k
    return ys[-1] if s > xs[-1] else ys[0]

# s runs 0 at the mantle tip to 1 at the collar.
S_TAB = [0.0, 0.05, 0.16, 0.36, 0.58, 0.80, 1.0]
W_TAB = [0.0, 0.26, 0.50, 0.68, 0.72, 0.66, 0.50]   # half width
H_TAB = [0.0, 0.11, 0.21, 0.30, 0.32, 0.29, 0.23]   # half height (top); the underside is flatter
BELLY = 0.62

def y_at(s): return Y_TIP - MANTLE * s
def s_at(y): return (Y_TIP - y) / MANTLE
def half_w(s): return lerp_tab(s, S_TAB, W_TAB)
def half_h(s): return lerp_tab(s, S_TAB, H_TAB)

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
    "body": mat("inkfin_body", "#43246e"),      # deep violet: reads against the turquoise seabed
    "stripe": mat("inkfin_stripe", "#7a4bb5"),  # zebra bands across the back
    "belly": mat("inkfin_belly", "#9a78c8"),
    "fin": mat("inkfin_fin", "#a783e0"),
    "arm": mat("inkfin_arm", "#5a318a"),
    "spot": mat("inkfin_spot", "#ffc4f6", "#ff7cf0", 2.5),   # glow strength is driven at runtime
    "eye": mat("inkfin_eye", "#f0d68c"),
    "pupil": mat("inkfin_pupil", "#0b0612"),
    "funnel": mat("inkfin_funnel", "#2a1445"),
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

TIP_Y = y_at(0.30)       # the front third of the mantle flexes on mantle_tip

def mantle_weights(co):
    k = max(0.0, min(1.0, (co.y - (TIP_Y - 0.25)) / 0.5))
    return {"mantle_tip": k, "mantle": 1 - k} if k > 0 else {"mantle": 1.0}

def ring_loft(bm, rings):
    for i in range(len(rings) - 1):
        n = len(rings[i])
        for j in range(n):
            bm.faces.new((rings[i][j], rings[i][(j + 1) % n], rings[i + 1][(j + 1) % n], rings[i + 1][j]))

# ---------------------------------------------------------------- mantle
def build_mantle():
    bm = bmesh.new()
    rings = []
    for i in range(1, RINGS + 1):
        s = (i / RINGS) ** 1.15
        w, h = half_w(s), half_h(s)
        ring = []
        for j in range(SIDES):
            a = 2 * math.pi * (j + 0.5) / SIDES          # flat facet along the back's midline
            ca, sa = math.cos(a), math.sin(a)
            ring.append(bm.verts.new((sa * w, y_at(s), ZC + ca * (h if ca >= 0 else h * BELLY))))
        rings.append(ring)
    ring_loft(bm, rings)
    tip = bm.verts.new((0, Y_TIP, ZC))
    for j in range(SIDES):
        bm.faces.new((rings[0][(j + 1) % SIDES], rings[0][j], tip))
    bm.faces.new(rings[-1])                              # collar cap, hidden by the head
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    ob = new_obj("inkfin_mantle", bm, "body", mantle_weights)
    ring_of = lambda y: round(RINGS * s_at(y) ** (1 / 1.15) - 0.5)
    for p in ob.data.polygons:
        if p.normal.z < -0.35:
            p.material_index = MAT_ORDER.index("belly")
        elif p.normal.z > 0.45 and 0.12 < s_at(p.center.y) < 0.93 and ring_of(p.center.y) % 3 == 0:   # straight bands; offsetting them per facet read as a chessboard
            p.material_index = MAT_ORDER.index("stripe")
    return ob

# ---------------------------------------------------------------- skirt fins
FIN_S0, FIN_S1 = 0.07, 0.97
FIN_Y = [y_at(FIN_S0 + (FIN_S1 - FIN_S0) * (i + 0.5) / FIN_BONES) for i in range(FIN_BONES)]

def fin_blend(y):
    if y >= FIN_Y[0]: return {0: 1.0}
    for i in range(FIN_BONES - 1):
        if FIN_Y[i] >= y >= FIN_Y[i + 1]:
            k = (FIN_Y[i] - y) / (FIN_Y[i] - FIN_Y[i + 1])
            return {i: 1 - k, i + 1: k}
    return {FIN_BONES - 1: 1.0}

def build_fins():
    n = 20
    for side, name in ((-1, "L"), (1, "R")):
        bm = bmesh.new()
        base, edge = [], []
        for i in range(n + 1):
            s = FIN_S0 + (FIN_S1 - FIN_S0) * i / n
            w = half_w(s)
            rise = min(1.0, (s - FIN_S0) / 0.10) ** 0.7 * min(1.0, (FIN_S1 - s) / 0.10) ** 0.7
            fw = (0.20 + 0.14 * math.sin(math.pi * (i / n) ** 0.8)) * rise * (1.0 if i % 2 else 0.84) + 0.02
            base.append(bm.verts.new((side * w * 0.93, y_at(s), ZC + 0.01)))
            edge.append(bm.verts.new((side * (w + fw), y_at(s), ZC - 0.02)))
        for i in range(n):
            f = (base[i], base[i + 1], edge[i + 1], edge[i])
            bm.faces.new(f if side < 0 else tuple(reversed(f)))
        def weights(co, side=side, name=name):
            # the base rides the mantle; the free edge follows the fin bones
            edge_k = min(1.0, max(0.0, (abs(co.x) - half_w(s_at(co.y)) * 0.93) / 0.12))
            out = {}
            for b, k in fin_blend(co.y).items():
                out[f"fin.{name}_{b}"] = k * edge_k
            if edge_k < 1: out.update({g: v * (1 - edge_k) for g, v in mantle_weights(co).items()})
            return out
        ob = new_obj(f"inkfin_fin_{name}", bm, "fin", weights)
        solidify(ob, 0.03)

# ---------------------------------------------------------------- head, eyes, funnel
HEAD_S = [0.0, 0.22, 0.50, 0.78, 1.0]            # collar -> arm crown
HEAD_W = [0.44, 0.47, 0.46, 0.38, 0.27]
HEAD_H = [0.21, 0.22, 0.21, 0.18, 0.13]

def head_y(t): return Y_COLLAR + 0.06 - (Y_COLLAR + 0.06 - Y_HEAD_END) * t

def build_head():
    H = {"head": 1.0}
    bm = bmesh.new()
    rings = []
    for t in HEAD_S:
        w, h = lerp_tab(t, HEAD_S, HEAD_W), lerp_tab(t, HEAD_S, HEAD_H)
        ring = []
        for j in range(8):
            a = 2 * math.pi * (j + 0.5) / 8
            ca, sa = math.cos(a), math.sin(a)
            ring.append(bm.verts.new((sa * w, head_y(t), ZC - 0.02 + ca * (h if ca >= 0 else h * 0.75))))
        rings.append(ring)
    ring_loft(bm, rings)
    bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    ob = new_obj("inkfin_head", bm, "body", H)
    for p in ob.data.polygons:
        if p.normal.z < -0.35: p.material_index = MAT_ORDER.index("belly")
    for side, name in ((-1, "L"), (1, "R")):
        # a cuttlefish eye: bulging gold iris with a dark slit pupil, no lids
        c = Vector((side * 0.43, head_y(0.42), ZC + 0.07))
        gem(f"inkfin_eye_{name}", c, (0.11, 0.15, 0.12), "eye", H)
        gem(f"inkfin_pupil_{name}", c + Vector((side * 0.075, -0.01, 0.03)), (0.05, 0.11, 0.045), "pupil", H)
    # the funnel under the head points back at the ship: the ink leaves here
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.10, radius2=0.055, depth=0.34)
    bmesh.ops.transform(bm, verts=bm.verts, matrix=Matrix.Translation((0, head_y(0.55), ZC - 0.20)) @ Matrix.Rotation(math.radians(100), 4, "X"))
    new_obj("inkfin_funnel", bm, "funnel", H)

# ---------------------------------------------------------------- arms
# Eight arms in two layers, four per side, trailing south and fanning a little.
ARMS = [  # (x at the crown, z offset, length scale, tip fan)
    (0.07, 0.05, 1.00, 0.16), (0.19, 0.03, 0.92, 0.42), (0.11, -0.07, 0.80, 0.30), (0.23, -0.06, 0.70, 0.62),
]
ARM_Y = [Y_HEAD_END + 0.04 - ARM_LEN * i / ARM_BONES for i in range(ARM_BONES + 1)]

def arm_weights(name):
    def weights(co):
        if co.y >= ARM_Y[0] - 0.04: return {f"arms.{name}_0": 1.0}
        for i in range(ARM_BONES - 1):
            mid0, mid1 = (ARM_Y[i] + ARM_Y[i + 1]) / 2, (ARM_Y[i + 1] + ARM_Y[i + 2]) / 2
            if co.y >= mid0: return {f"arms.{name}_{i}": 1.0}
            if co.y >= mid1:
                k = (mid0 - co.y) / (mid0 - mid1)
                return {f"arms.{name}_{i}": 1 - k, f"arms.{name}_{i + 1}": k}
        return {f"arms.{name}_{ARM_BONES - 1}": 1.0}
    return weights

def build_arms():
    segs = 5
    for side, name in ((-1, "L"), (1, "R")):
        for k, (x0, dz, ls, fan) in enumerate(ARMS):
            bm = bmesh.new()
            rings = []
            for i in range(segs + 1):
                t = i / segs
                r = 0.085 * (1 - t) ** 0.8 + 0.012
                c = Vector((side * (x0 + fan * t * t), Y_HEAD_END + 0.10 - ARM_LEN * ls * t, ZC - 0.03 + dz * (1 - 0.4 * t)))
                rings.append([bm.verts.new(c + Vector((math.sin(a) * r, 0, math.cos(a) * r * 0.8)))
                              for a in (math.pi / 4 + j * math.pi / 2 for j in range(4))])
            ring_loft(bm, rings)
            bm.faces.new(rings[-1]); bm.faces.new(list(reversed(rings[0])))
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            bm.normal_update()
            ob = new_obj(f"inkfin_arm_{name}_{k}", bm, "arm", arm_weights(name))
            for p in ob.data.polygons:
                if p.normal.z < -0.3: p.material_index = MAT_ORDER.index("belly")

# ---------------------------------------------------------------- glow spots
def build_spots():
    # a row along each fin base, and one between the eyes; the engine drives their glow
    count = 7
    for side in (-1, 1):
        for k in range(count):
            s = 0.16 + (0.90 - 0.16) * k / (count - 1)
            w, h = half_w(s), half_h(s)
            c = Vector((side * w * 0.70, y_at(s), ZC + h * 0.72))
            size = 0.035 + 0.035 * (h / 0.32)
            gem(f"inkfin_spot_{side}_{k}", c, (size, size * 1.25, 0.022), "spot", mantle_weights)
    gem("inkfin_spot_head", Vector((0, head_y(0.42), ZC + 0.19)), (0.06, 0.08, 0.022), "spot", {"head": 1.0})

# ---------------------------------------------------------------- armature
def build_rig():
    arm = bpy.data.armatures.new("inkfin_rig")
    rig = bpy.data.objects.new("inkfin_rig", arm)
    bpy.context.scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm.edit_bones
    def bone(name, head, parent=None, deform=True, length=0.3):
        b = eb.new(name); b.head = head; b.tail = (head[0], head[1] + length, head[2]); b.roll = 0
        b.use_deform = deform
        if parent: b.parent = eb[parent]
        return b
    bone("root", (0, 0, 0), deform=False, length=0.6)
    mid = y_at(0.58)
    bone("body", (0, mid, ZC), "root", deform=False, length=0.5)   # whole-animal pitch, yaw and roll
    bone("mantle", (0, mid, ZC), "body", length=0.4)               # scaled for the jet pulse
    bone("mantle_tip", (0, TIP_Y, ZC), "mantle", length=0.5)
    bone("head", (0, Y_COLLAR, ZC), "body")
    for side, name in ((-1, "L"), (1, "R")):
        prev = "head"
        for i in range(ARM_BONES):
            bone(f"arms.{name}_{i}", (side * 0.15, ARM_Y[i], ZC - 0.03), prev, length=0.2)
            prev = f"arms.{name}_{i}"
        for i in range(FIN_BONES):
            x = side * half_w(s_at(FIN_Y[i])) * 0.93
            bone(f"fin.{name}_{i}", (x, FIN_Y[i] - 0.1, ZC), "mantle", length=0.2)
    bpy.ops.object.mode_set(mode="OBJECT")
    return rig

# ---------------------------------------------------------------- assemble
def build():
    build_mantle(); build_fins(); build_head(); build_arms(); build_spots()
    for ob, weights in PARTS:
        for v in ob.data.vertices:
            w = weights(ob.matrix_world @ v.co) if callable(weights) else weights
            for g, val in w.items():
                if val <= 0: continue
                vg = ob.vertex_groups.get(g) or ob.vertex_groups.new(name=g)
                vg.add([v.index], val, "REPLACE")
    bpy.ops.object.select_all(action="DESELECT")
    body = PARTS[0][0]
    for ob, _ in PARTS:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()
    body.name = body.data.name = "inkfin_cuttlefish"
    rig = build_rig()
    body.parent = rig
    mod = body.modifiers.new("rig", "ARMATURE"); mod.object = rig
    return body, rig

body, rig = build()
print("built", len(body.data.vertices), "verts", len(body.data.polygons), "faces", len(rig.data.bones), "bones")
