"""Shared low-poly helpers for the Sushi Loop creature concept models (#66-#80).

Each creature's source/build_model.py runs this file first, inside Blender:
    exec(open(KIT).read())

Axes follow the Storm Eel and Inkfin Cuttlefish: X right, +Y north (the travel
direction, away from the submarine), Z up, 1 unit = 1 grid cell. Geometry is faceted
(flat-shaded), with one flat material per colour and no textures.
"""
import math, os
import bpy, bmesh
from mathutils import Vector, Matrix

def reset():
    for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.armatures, bpy.data.cameras, bpy.data.lights):
        for item in list(coll): coll.remove(item)
    for m in list(bpy.data.materials):
        if not m.users: bpy.data.materials.remove(m)
    PARTS.clear(); MATS.clear()

def srgb(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)

MATS = {}    # key -> material, in slot order
PARTS = []

def palette(prefix, colours):
    """colours: key -> "#hex" or ("#hex", "#emission", strength)."""
    for key, spec in colours.items():
        hexc, emit, strength = (spec, None, 0.0) if isinstance(spec, str) else spec
        name = f"{prefix}_{key}"
        m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        m.use_nodes = True
        p = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        p.inputs["Base Color"].default_value = (*srgb(hexc), 1)
        p.inputs["Roughness"].default_value = 0.9
        p.inputs["Metallic"].default_value = 0.0
        if emit:
            p.inputs["Emission Color"].default_value = (*srgb(emit), 1)
            p.inputs["Emission Strength"].default_value = strength
        m.diffuse_color = (*srgb(hexc), 1)
        MATS[key] = m

def add(bm, material, paint=None, name="part"):
    """Turn a bmesh into a part. paint(polygon) may return another material key."""
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    keys = list(MATS)
    for k in keys: me.materials.append(MATS[k])
    for p in me.polygons:
        p.use_smooth = False
        k = paint(p) if paint else None
        p.material_index = keys.index(k or material)
    PARTS.append(ob)
    return ob

def lerp_tab(s, xs, ys):
    if s <= xs[0]: return ys[0]
    for i in range(len(xs) - 1):
        if xs[i] <= s <= xs[i + 1]:
            return ys[i] + (ys[i + 1] - ys[i]) * (s - xs[i]) / (xs[i + 1] - xs[i])
    return ys[-1]

def ring_loft(bm, rings):
    for i in range(len(rings) - 1):
        a, b = rings[i], rings[i + 1]
        n = max(len(a), len(b))
        if len(a) == 1 and len(b) == 1: continue
        for j in range(n):
            if len(a) == 1: bm.faces.new((a[0], b[(j + 1) % n], b[j]))
            elif len(b) == 1: bm.faces.new((a[j], a[(j + 1) % n], b[0]))
            else: bm.faces.new((a[j], a[(j + 1) % n], b[(j + 1) % n], b[j]))

def loft(stations, material, sides=10, belly=None, paint=None, name="body", offset=0.5):
    """A body lofted along Y. stations: dicts with y, w (half width), h (half height up),
    optional b (half height down, default h), z (centre height), x (centre x).
    A station with w == 0 closes the end in a point."""
    bm = bmesh.new()
    rings = []
    for st in stations:
        y, w, h = st["y"], st["w"], st["h"]
        b, z, x = st.get("b", h), st.get("z", 0.0), st.get("x", 0.0)
        if w <= 1e-6:
            rings.append([bm.verts.new((x, y, z))]); continue
        ring = []
        for j in range(sides):
            a = 2 * math.pi * (j + offset) / sides
            ca, sa = math.cos(a), math.sin(a)
            ring.append(bm.verts.new((x + sa * w, y, z + ca * (h if ca >= 0 else b))))
        rings.append(ring)
    ring_loft(bm, rings)
    for ring in (rings[0], rings[-1]):
        if len(ring) > 1: bm.faces.new(ring)
    def default_paint(p):
        k = paint(p) if paint else None
        if k: return k
        return belly if belly and p.normal.z < -0.35 else None
    return add(bm, material, default_paint, name)

def tube(points, radii, material, sides=4, flat=1.0, paint=None, name="tube", closed_tip=True):
    """A tube along a path. radii: one number or one per point. flat squashes it vertically."""
    pts = [Vector(p) for p in points]
    if not isinstance(radii, (list, tuple)): radii = [radii] * len(pts)
    bm = bmesh.new()
    rings = []
    for i, c in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        up = Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0))
        u = t.cross(up).normalized(); v = u.cross(t).normalized()
        r = radii[i]
        if r <= 1e-6 and closed_tip:
            rings.append([bm.verts.new(c)]); continue
        rings.append([bm.verts.new(c + u * (math.cos(a) * r) + v * (math.sin(a) * r * flat))
                      for a in (math.pi / sides + j * 2 * math.pi / sides for j in range(sides))])
    ring_loft(bm, rings)
    for ring in (rings[0], rings[-1]):
        if len(ring) > 1: bm.faces.new(ring)
    return add(bm, material, paint, name)

def gem(center, size, material, subdiv=1, rot=None, paint=None, name="gem"):
    """A faceted ball (icosphere) scaled per axis; rot is an optional Matrix."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=1.0)
    if isinstance(size, (int, float)): size = (size, size, size)
    m = Matrix.Translation(center) @ (rot or Matrix.Identity(4)) @ Matrix.Diagonal((*size, 1))
    bmesh.ops.transform(bm, verts=bm.verts, matrix=m)
    return add(bm, material, paint, name)

def cone(base, tip, radius, material, sides=5, name="spike"):
    base, tip = Vector(base), Vector(tip)
    t = (tip - base).normalized()
    up = Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0))
    u = t.cross(up).normalized(); v = u.cross(t).normalized()
    bm = bmesh.new()
    ring = [bm.verts.new(base + u * (math.cos(a) * radius) + v * (math.sin(a) * radius))
            for a in (j * 2 * math.pi / sides for j in range(sides))]
    top = bm.verts.new(tip)
    for j in range(sides): bm.faces.new((ring[j], ring[(j + 1) % sides], top))
    bm.faces.new(ring)
    return add(bm, material, None, name)

def plate(outline, thickness, material, paint=None, name="plate"):
    """A thin slab from an outline of (x, y, z) points (a fin, a fluke, a shell lip)."""
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in outline]
    f = bm.faces.new(vs)
    f.normal_update()
    if f.normal.z < -1e-6 or (abs(f.normal.z) <= 1e-6 and f.normal.x < 0): f.normal_flip()   # same slab either side of a mirror
    bmesh.ops.triangulate(bm, faces=[f])
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=thickness)
    return add(bm, material, paint, name)

def strip(inner, outer, thickness, material, paint=None, name="fin"):
    """A thin slab between two point rows of the same length (a long fin or a wing)."""
    bm = bmesh.new()
    a = [bm.verts.new(p) for p in inner]; b = [bm.verts.new(p) for p in outer]
    for i in range(len(a) - 1): bm.faces.new((a[i], a[i + 1], b[i + 1], b[i]))
    bm.normal_update()
    n = sum((f.normal for f in bm.faces), Vector())
    if n.z < -1e-6 or (abs(n.z) <= 1e-6 and n.x < 0): bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=thickness)
    return add(bm, material, paint, name)

def eye(center, r, out, iris="eye", pupil="pupil", slit=(0.45, 0.8, 0.45)):
    """A lidless gold eye with a dark pupil on the side facing `out`."""
    c, out = Vector(center), Vector(out).normalized()
    gem(c, r, iris, name="eye")
    gem(c + out * r * 0.62, (r * slit[0], r * slit[1], r * slit[2]), pupil, name="pupil")

def segments(y0, y1, n, w0, w1, h0, h1, z0, z1, shell, band, belly=None, sides=8, name="segment"):
    """Overlapping shell plates from y0 to y1 (a shrimp's abdomen): each plate is wider at
    its front than the next one's start, and carries a band along its rear edge."""
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        lerp = lambda a, b, t: a + (b - a) * t
        ya, yb = lerp(y0, y1, t0), lerp(y0, y1, t1)
        cut = yb + (ya - yb) * 0.3
        loft([{"y": ya, "w": lerp(w0, w1, t0) * 1.07, "h": lerp(h0, h1, t0) * 1.07, "z": lerp(z0, z1, t0)},
              {"y": cut, "w": lerp(w0, w1, t1 - 0.3 / n) * 1.03, "h": lerp(h0, h1, t1 - 0.3 / n) * 1.03, "z": lerp(z0, z1, t1 - 0.3 / n)},
              {"y": yb, "w": lerp(w0, w1, t1), "h": lerp(h0, h1, t1), "z": lerp(z0, z1, t1)}],
             shell, sides=sides, name=name,
             paint=lambda p, cut=cut: (belly if belly and p.normal.z < -0.35 else (band if p.center.y < cut else None)))

def turn(matrix, parts=None):
    """Apply a matrix to the parts built so far (or to the given ones)."""
    for ob in (parts or PARTS): ob.data.transform(matrix)

def finish(name, folder):
    bpy.ops.object.select_all(action="DESELECT")
    for ob in PARTS: ob.select_set(True)
    bpy.context.view_layer.objects.active = PARTS[0]
    bpy.ops.object.join()
    ob = PARTS[0]
    ob.name = ob.data.name = name
    used = {p.material_index for p in ob.data.polygons}
    os.makedirs(os.path.join(folder, "export"), exist_ok=True)
    os.makedirs(os.path.join(folder, "source"), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(folder, "source", f"{name.replace('_', '-')}.blend"))
    bpy.ops.export_scene.gltf(filepath=os.path.join(folder, "export", f"{name.replace('_', '-')}.glb"),
                              export_format="GLB", use_selection=True, export_apply=True, export_yup=True)
    dims = ob.dimensions
    print(f"{name}: {len(ob.data.vertices)} verts, {len(ob.data.polygons)} faces, {len(used)} colours, "
          f"{dims.x:.2f} x {dims.y:.2f} x {dims.z:.2f} cells")
    return ob

def shoot(path, span=5.6, tilt=38, turn=0, res=(700, 800), sea="#2fb6c4"):
    """Render the scene as the pursuit camera sees it: from above, leaning south."""
    sc = bpy.context.scene
    for ob in list(sc.objects):
        if ob.type in {"CAMERA", "LIGHT"} or ob.name == "seabed": bpy.data.objects.remove(ob)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    sc.collection.objects.link(cam)
    cam.data.type = "ORTHO"; cam.data.ortho_scale = span
    rot = Matrix.Rotation(math.radians(turn), 4, "Z") @ Matrix.Rotation(math.radians(tilt), 4, "X")
    cam.matrix_world = Matrix.Translation(Vector((0, 0, 0.5))) @ rot @ Matrix.Translation((0, 0, 20))
    sc.camera = cam
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sc.collection.objects.link(sun)
    sun.data.energy = 3.2
    sun.rotation_euler = (math.radians(35), math.radians(-25), math.radians(turn))
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=30)
    me = bpy.data.meshes.new("seabed"); bm.to_mesh(me); bm.free()
    floor = bpy.data.objects.new("seabed", me); sc.collection.objects.link(floor)
    m = bpy.data.materials.get("seabed") or bpy.data.materials.new("seabed")
    m.use_nodes = True
    next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (*srgb(sea), 1)
    me.materials.append(m)
    w = sc.world or bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs["Color"].default_value = (1, 1, 1, 1); bg.inputs["Strength"].default_value = 0.75
    for engine in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try: sc.render.engine = engine; break
        except TypeError: pass
    sc.view_settings.view_transform = "Standard"
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = path
    sc.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)
    for ob in (cam, sun, floor): bpy.data.objects.remove(ob)
