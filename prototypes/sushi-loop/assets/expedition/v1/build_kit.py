"""Procedural Blender source for the issue #21 underwater expedition kit.

Run from the repository root:

    blender -b --factory-startup --python prototypes/sushi-loop/assets/expedition/v1/build_kit.py -- [--only name,...]

Every sprite is modelled at one Blender unit per grid cell and projected with
ART-01's 70% height rule by shearing world Y by 0.7 * Z under a top-down
orthographic camera. Square cells therefore stay square, and the shear keeps Z
for depth ordering. Output PNGs are trimmed; `manifest.json` records the cell
origin inside each trimmed frame so Godot can register sprites exactly.
"""

import bpy
import bmesh
import colorsys
import json
import math
import os
import random
import sys
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "sprites")
MANIFEST = os.path.join(HERE, "manifest.json")
PX = 192            # rendered pixels per cell
HEIGHT_PROJECTION = 0.70
PAD = 0.5           # horizontal canvas padding (cells) on each side
HEADROOM = 2.6      # cells of canvas above the footprint for projected height

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ONLY = set()
if "--only" in ARGS:
    ONLY = set(ARGS[ARGS.index("--only") + 1].split(","))


def hexcol(value, alpha=1.0):
    value = value.lstrip("#")
    srgb = [int(value[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]
    return (*lin, alpha)


# ---------------------------------------------------------------- scene setup

def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _materials.clear()
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0.0
    scene.render.filter_size = 1.2
    eevee = scene.eevee
    eevee.taa_render_samples = 48
    for attr, value in (("use_shadows", True), ("use_raytracing", True), ("shadow_ray_count", 2), ("fast_gi_method", "GLOBAL_ILLUMINATION")):
        if hasattr(eevee, attr):
            try:
                setattr(eevee, attr, value)
            except Exception:
                pass

    # Thin navy ink outline, matching the concept's crisp facet separation.
    scene.render.use_freestyle = True
    scene.render.line_thickness_mode = "ABSOLUTE"
    scene.render.line_thickness = 1.6
    fs = bpy.context.view_layer.freestyle_settings
    fs.crease_angle = math.radians(128)
    lineset = fs.linesets[0] if fs.linesets else fs.linesets.new("Ink")
    lineset.select_by_visibility = True
    lineset.select_silhouette = True
    lineset.select_border = True
    lineset.select_crease = True
    lineset.select_contour = True
    if lineset.linestyle is None:
        lineset.linestyle = bpy.data.linestyles.new("Ink")
    lineset.linestyle.color = hexcol("#0b1748")[:3]
    lineset.linestyle.alpha = 0.75
    lineset.linestyle.thickness = 1.6

    world = bpy.data.worlds.new("Water")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = hexcol("#9fd8ff")
    bg.inputs[1].default_value = 0.42

    sun = bpy.data.lights.new("Key", "SUN")
    sun.energy = 5.2
    sun.angle = math.radians(18)
    sun.color = hexcol("#fff6e8")[:3]
    key = bpy.data.objects.new("Key", sun)
    scene.collection.objects.link(key)
    # From above, slightly behind (north) and to the left: tops read brightest,
    # south fronts mid-tone and east faces darkest, as in the concept.
    key.rotation_euler = Vector((0.42, -0.38, -0.82)).to_track_quat("-Z", "Y").to_euler()

    fill = bpy.data.lights.new("Fill", "SUN")
    fill.energy = 0.7
    fill.color = hexcol("#7fd4ff")[:3]
    fill_obj = bpy.data.objects.new("Fill", fill)
    scene.collection.objects.link(fill_obj)
    fill_obj.rotation_euler = Vector((-0.3, 0.7, -0.4)).to_track_quat("-Z", "Y").to_euler()
    fill.use_shadow = False
    return scene


_materials = {}


def shade(color, factor, toward="#000000"):
    """Blend an sRGB hex colour toward `toward` by `factor` (0 = unchanged)."""
    a = [int(color.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    b = [int(toward.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    return "#" + "".join(f"{round(x + (y - x) * factor):02x}" for x, y in zip(a, b))


def tone(color, value, saturation=1.0, hue=0.0):
    """HSV adjust of an sRGB hex colour, keeping it saturated (no white wash)."""
    r, g, b = [int(color.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    h, sat, v = colorsys.rgb_to_hsv(r, g, b)
    r, g, b = colorsys.hsv_to_rgb((h + hue) % 1.0, min(1.0, sat * saturation), min(1.0, v * value))
    return "#" + "".join(f"{round(c * 255):02x}" for c in (r, g, b))


# Direction-free cel tone: facets are toned by their projected normal against a
# fixed screen-space key (top brightest, south fronts mid, east faces darkest).
TONE_KEY = Vector((-0.38, 0.32, 0.87)).normalized()


def material(name, color, rough=0.55, gradient=None, emission=0.0, metallic=0.0, spec=0.35):
    """Environment pieces use emission cel tone; the submarine and salvage stay physical.

    `gradient` = (dark colour, z_low, z_high) darkens toward the seabed.
    """
    key = (name, color, gradient)
    if key in _materials:
        return _materials[key]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes["Principled BSDF"]
    if not name.startswith(("sub-", "gold")):
        out = nodes["Material Output"]
        geo = nodes.new("ShaderNodeNewGeometry")
        dot = nodes.new("ShaderNodeVectorMath")
        dot.operation = "DOT_PRODUCT"
        dot.inputs[1].default_value = TONE_KEY
        links.new(geo.outputs["Normal"], dot.inputs[0])
        remap = nodes.new("ShaderNodeMapRange")
        # Thin foliage faces sideways; compress its tone toward the lit end.
        remap.inputs["From Min"].default_value = -1.6 if name.startswith(("kelp", "coral", "grass", "moss", "starfish")) else -0.35
        remap.inputs["From Max"].default_value = 1.0
        links.new(dot.outputs["Value"], remap.inputs["Value"])
        ramp = nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.interpolation = "EASE"
        elements = ramp.color_ramp.elements
        elements[0].position = 0.3
        elements[0].color = hexcol(tone(color, 0.5, 1.08, 0.015))
        elements[1].position = 0.86
        elements[1].color = hexcol(tone(color, 1.22, 0.9, -0.01))
        mid = elements.new(0.6)
        mid.color = hexcol(color)
        links.new(remap.outputs["Result"], ramp.inputs["Fac"])
        result = ramp.outputs["Color"]
        if gradient:
            sep = nodes.new("ShaderNodeSeparateXYZ")
            links.new(geo.outputs["Position"], sep.inputs[0])
            height = nodes.new("ShaderNodeMapRange")
            height.inputs["From Min"].default_value = gradient[1]
            height.inputs["From Max"].default_value = gradient[2]
            links.new(sep.outputs["Z"], height.inputs["Value"])
            mix = nodes.new("ShaderNodeMix")
            mix.data_type = "RGBA"
            mix.inputs["A"].default_value = hexcol(gradient[0])
            links.new(height.outputs["Result"], mix.inputs["Factor"])
            links.new(result, mix.inputs["B"])
            result = mix.outputs["Result"]
        emit = nodes.new("ShaderNodeEmission")
        emit.inputs["Strength"].default_value = 1.0
        links.new(result, emit.inputs["Color"])
        links.new(emit.outputs["Emission"], out.inputs["Surface"])
        _materials[key] = mat
        return mat
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = spec
    if gradient:
        geo = nodes.new("ShaderNodeNewGeometry")
        sep = nodes.new("ShaderNodeSeparateXYZ")
        ramp = nodes.new("ShaderNodeMapRange")
        ramp.inputs["From Min"].default_value = gradient[1]
        ramp.inputs["From Max"].default_value = gradient[2]
        mix = nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.inputs["A"].default_value = hexcol(gradient[0])
        mix.inputs["B"].default_value = hexcol(color)
        links.new(geo.outputs["Position"], sep.inputs[0])
        links.new(sep.outputs["Z"], ramp.inputs["Value"])
        links.new(ramp.outputs["Result"], mix.inputs["Factor"])
        links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    else:
        bsdf.inputs["Base Color"].default_value = hexcol(color)
    if emission:
        bsdf.inputs["Emission Color"].default_value = hexcol(color)
        bsdf.inputs["Emission Strength"].default_value = emission
    _materials[key] = mat
    return mat


def mesh_object(name, bm, mat, smooth=False, bevel=0.0, segments=2):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    if isinstance(mat, list):
        for m in mat:
            me.materials.append(m)
    else:
        me.materials.append(mat)
    for poly in me.polygons:
        poly.use_smooth = smooth
    if bevel:
        mod = obj.modifiers.new("Bevel", "BEVEL")
        mod.width = bevel
        mod.segments = segments
        mod.limit_method = "ANGLE"
        mod.angle_limit = math.radians(30)
        mod.harden_normals = False
    return obj


def apply_and_shear():
    """Apply modifiers/transforms and project height at 70% onto screen Y."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for obj in list(bpy.context.scene.objects):
        if obj.type != "MESH":
            continue
        evaluated = obj.evaluated_get(depsgraph)
        me = bpy.data.meshes.new_from_object(evaluated)
        me.transform(obj.matrix_world)
        for v in me.vertices:
            v.co.y += HEIGHT_PROJECTION * v.co.z
        old = obj.data
        obj.modifiers.clear()
        obj.data = me
        obj.matrix_world = Matrix.Identity(4)
        bpy.data.meshes.remove(old)


ORTHO_ELEVATION = 58  # degrees; rounded-prop exception (see README)


def render_ortho(name, extra=None):
    """Ordinary orthographic capture for rounded props (submarine, salvage).

    The oblique environment shear makes spheres egg-shaped, so these follow the
    documented character-style exception: an undistorted orthographic camera
    looking north and down. The ground root (cell centre) is registered.
    """
    from bpy_extras.object_utils import world_to_camera_view
    scene = bpy.context.scene
    size = 1.4
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = size
    cam = bpy.data.objects.new("Cam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    e = math.radians(ORTHO_ELEVATION)
    target = Vector((0.5, -0.5, 0.25))
    cam.location = target + Vector((0, -math.cos(e), math.sin(e))) * 20
    cam.rotation_euler = (math.pi / 2 - e, 0, 0)
    scene.render.resolution_x = scene.render.resolution_y = round(size * PX)
    full = os.path.join(OUT, f"{name}.png")
    scene.render.filepath = full
    bpy.ops.render.render(write_still=True)
    bpy.context.view_layer.update()
    root = world_to_camera_view(scene, cam, Vector((0.5, -0.5, 0.0)))
    rx, ry = root.x * size * PX, (1 - root.y) * size * PX
    bounds = trim(full)
    entry = {
        "image": f"sprites/{name}.png",
        "footprint": [1, 1],
        "origin": [rx - 0.5 * PX - bounds[0], ry - 0.5 * PX - bounds[1]],
        "size": [bounds[2] - bounds[0], bounds[3] - bounds[1]],
        "cell_pixels": PX,
        "camera": f"ortho-{ORTHO_ELEVATION}",
    }
    if extra:
        entry.update(extra)
    record(name, entry)


def render(name, footprint=(1, 1), anchor="cell", extra=None):
    """Render the current scene. Cell (0,0) occupies x 0..w, y -h..0 (north = +y)."""
    if ONLY and name not in ONLY and name.split("-")[0] not in ONLY:
        return
    if extra and extra.get("camera") == "ortho":
        extra = {k: v for k, v in extra.items() if k != "camera"}
        render_ortho(name, extra)
        return
    apply_and_shear()
    scene = bpy.context.scene
    w, h = footprint
    width = w + 2 * PAD
    height = h + HEADROOM + 0.4
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = max(width, height)
    cam = bpy.data.objects.new("Cam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    cx = w / 2
    # Canvas spans y from -h - 0.4 (below footprint, for front faces/shadow) to HEADROOM.
    y0 = -h - 0.4
    cy = y0 + height / 2
    cam.location = (cx, cy, 30)
    cam.rotation_euler = (0, 0, 0)
    scene.render.resolution_x = round(width * PX)
    scene.render.resolution_y = round(height * PX)
    if width < height:
        cam_data.sensor_fit = "VERTICAL"
    else:
        cam_data.sensor_fit = "HORIZONTAL"
    cam_data.clip_end = 100
    os.makedirs(OUT, exist_ok=True)
    full = os.path.join(OUT, f"{name}.png")
    scene.render.filepath = full
    bpy.ops.render.render(write_still=True)
    # Cell top-left (x=0, y=0 world) in canvas pixels.
    origin = (PAD * PX, (HEADROOM - 0) * PX)
    bounds = trim(full)
    entry = {
        "image": f"sprites/{name}.png",
        "footprint": [w, h],
        "origin": [origin[0] - bounds[0], origin[1] - bounds[1]],
        "size": [bounds[2] - bounds[0], bounds[3] - bounds[1]],
        "cell_pixels": PX,
    }
    if extra:
        entry.update(extra)
    record(name, entry)


def trim(path):
    img = bpy.data.images.load(path)
    w, h = img.size
    px = list(img.pixels)
    alpha_rows = []
    minx, miny, maxx, maxy = w, h, -1, -1
    for y in range(h):
        row = y * w * 4
        for x in range(w):
            if px[row + x * 4 + 3] > 0.004:
                if x < minx: minx = x
                if x > maxx: maxx = x
                if y < miny: miny = y
                if y > maxy: maxy = y
    if maxx < 0:
        bpy.data.images.remove(img)
        return (0, 0, w, h)
    minx = max(0, minx - 2); maxx = min(w - 1, maxx + 2)
    miny = max(0, miny - 2); maxy = min(h - 1, maxy + 2)
    cw, ch = maxx - minx + 1, maxy - miny + 1
    out = bpy.data.images.new("trim", cw, ch, alpha=True)
    out.colorspace_settings.name = img.colorspace_settings.name
    data = [0.0] * (cw * ch * 4)
    for y in range(ch):
        src = ((miny + y) * w + minx) * 4
        data[y * cw * 4:(y + 1) * cw * 4] = px[src:src + cw * 4]
    out.pixels = data
    out.filepath_raw = path
    out.file_format = "PNG"
    out.save()
    bpy.data.images.remove(out)
    bpy.data.images.remove(img)
    # Blender pixel rows are bottom-up; convert to top-down image bounds.
    return (minx, h - 1 - maxy, maxx + 1, h - miny)


_manifest = {}


def record(name, entry):
    _manifest[name] = entry


# ------------------------------------------------------------------ geometry

ROCK_SHADES = ["#2c5ee6", "#2855d8", "#3367ec", "#2650cc", "#2a5ade"]
ROCK_DARK = "#081040"


def rock_material(rng):
    return material("rock", rng.choice(ROCK_SHADES), rough=0.62, gradient=(ROCK_DARK, -0.05, 0.6))


def prism(rng, cx, cy, radius, height, sides=None, tilt=0.12, mat=None, base=0.0, squash=1.0, dome=None):
    """Chunky faceted rock: irregular n-gon with chamfered, gently tilted crown."""
    sides = sides or rng.choice([5, 6, 6, 7])
    bm = bmesh.new()
    phase = rng.random() * math.tau
    radii = [radius * rng.uniform(0.82, 1.08) for _ in range(sides)]
    angles = [phase + i * math.tau / sides + rng.uniform(-0.18, 0.18) for i in range(sides)]
    tx, ty = rng.uniform(-tilt, tilt), rng.uniform(-tilt, tilt)
    chamfer = (height * dome) if dome else min(0.16, height * 0.28) * rng.uniform(0.7, 1.1)
    crown = rng.uniform(0.5, 0.62) if dome else rng.uniform(0.6, 0.72)
    rings = []
    for z, scale in ((base, 1.0), (base + height - chamfer, rng.uniform(0.98, 1.04)), (base + height, crown)):
        ring = []
        for a, r in zip(angles, radii):
            x = cx + math.cos(a) * r * scale
            y = cy + math.sin(a) * r * scale * squash
            zz = z + (tx * (x - cx) + ty * (y - cy) if z > base else 0)
            ring.append(bm.verts.new((x, y, zz)))
        rings.append(ring)
    for lower, upper in zip(rings, rings[1:]):
        for i in range(sides):
            j = (i + 1) % sides
            bm.faces.new((lower[i], lower[j], upper[j], upper[i]))
    bm.faces.new(rings[-1])
    bm.faces.new(list(reversed(rings[0])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_object("prism", bm, mat or rock_material(rng), bevel=0.018, segments=2)


def box(x0, y0, z0, x1, y1, z1, mat, bevel=0.02):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x = x0 + (v.co.x + 0.5) * (x1 - x0)
        v.co.y = y0 + (v.co.y + 0.5) * (y1 - y0)
        v.co.z = z0 + (v.co.z + 0.5) * (z1 - z0)
    return mesh_object("box", bm, mat, bevel=bevel, segments=2)


def cylinder(cx, cy, z0, radius, height, mat, inner_mat=None, segments=14, lean=(0, 0), hollow=True, cap_scale=1.0):
    bm = bmesh.new()
    bottom, top = [], []
    for i in range(segments):
        a = i * math.tau / segments
        bottom.append(bm.verts.new((cx + math.cos(a) * radius, cy + math.sin(a) * radius, z0)))
        top.append(bm.verts.new((cx + lean[0] + math.cos(a) * radius * cap_scale, cy + lean[1] + math.sin(a) * radius * cap_scale, z0 + height)))
    for i in range(segments):
        j = (i + 1) % segments
        bm.faces.new((bottom[i], bottom[j], top[j], top[i]))
    cap = bm.faces.new(top)
    bm.faces.new(list(reversed(bottom)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if hollow:
        inset = bmesh.ops.inset_region(bm, faces=[cap], thickness=radius * 0.3, depth=0)
        inner = [f for f in inset["faces"]] if "faces" in inset else []
        cap_face = cap
        cap_face.material_index = 1
        ext = bmesh.ops.extrude_discrete_faces(bm, faces=[cap_face])
        for f in ext["faces"]:
            f.material_index = 1
            for v in f.verts:
                v.co.z -= height * 0.45
    mats = [mat, inner_mat or mat]
    obj = mesh_object("tube", bm, mats, smooth=True, bevel=radius * 0.18, segments=2)
    return obj


def base_slab(mask, mat):
    """Low rock bed under a wall cell. mask = (N, E, S, W) neighbours that are rock."""
    n, e, s, w = mask
    inset = 0.14
    x0 = 0.0 if w else inset
    x1 = 1.0 if e else 1.0 - inset
    y1 = 0.0 if n else -inset          # north edge (cell spans y -1..0)
    y0 = -1.0 if s else -1.0 + inset
    radius = 0.22
    corners = [  # (corner point, open?, centre direction)
        ((x1, y1), not n and not e, (-1, -1)),
        ((x0, y1), not n and not w, (1, -1)),
        ((x0, y0), not s and not w, (1, 1)),
        ((x1, y0), not s and not e, (-1, 1)),
    ]
    outline = []
    start_angles = {(-1, -1): 0, (1, -1): 90, (1, 1): 180, (-1, 1): 270}
    for (px, py), rounded, (dx, dy) in corners:
        if rounded:
            ccx, ccy = px + dx * radius, py + dy * radius
            a0 = start_angles[(dx, dy)]
            for k in range(7):
                a = math.radians(a0 + k * 15)
                outline.append((ccx + math.cos(a) * radius, ccy + math.sin(a) * radius))
        else:
            outline.append((px, py))
    bm = bmesh.new()
    height = 0.08
    lower = [bm.verts.new((x, y, -0.02)) for x, y in outline]
    upper = [bm.verts.new((x, y, height)) for x, y in outline]
    count = len(outline)
    for i in range(count):
        j = (i + 1) % count
        bm.faces.new((lower[i], lower[j], upper[j], upper[i]))
    bm.faces.new(upper)
    bm.faces.new(list(reversed(lower)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_object("slab", bm, mat)


def kelp(rng, cx, cy, z0, height, mat, width=0.09, sway=0.08):
    """Wavy tapered ribbon with thickness."""
    bm = bmesh.new()
    steps = 10
    facing = rng.uniform(-0.6, 0.6)
    fx, fy = math.cos(facing), math.sin(facing) * 0.4
    phase = rng.uniform(0, math.tau)
    left, right = [], []
    for i in range(steps + 1):
        t = i / steps
        off = math.sin(phase + t * 7.0) * sway * (0.3 + t)
        px = cx + off
        py = cy + math.cos(phase + t * 5.0) * sway * 0.4 * t
        wdt = width * (1.0 - 0.75 * t ** 1.5) * (0.85 + 0.25 * math.sin(t * 9 + phase))
        left.append(bm.verts.new((px - fx * wdt, py - fy * wdt, z0 + t * height)))
        right.append(bm.verts.new((px + fx * wdt, py + fy * wdt, z0 + t * height)))
    for i in range(steps):
        bm.faces.new((left[i], right[i], right[i + 1], left[i + 1]))
    obj = mesh_object("kelp", bm, mat, smooth=True)
    sol = obj.modifiers.new("Solid", "SOLIDIFY")
    sol.thickness = 0.035
    sol.offset = 0
    return obj


def starfish(cx, cy, z0, radius, mat, rot=0.0):
    bm = bmesh.new()
    pts = []
    for i in range(10):
        a = rot + i * math.tau / 10
        r = radius if i % 2 == 0 else radius * 0.45
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    lower = [bm.verts.new((x, y, z0)) for x, y in pts]
    upper = [bm.verts.new((x + (cx - x) * 0.18, y + (cy - y) * 0.18, z0 + radius * 0.32)) for x, y in pts]
    for i in range(10):
        j = (i + 1) % 10
        bm.faces.new((lower[i], lower[j], upper[j], upper[i]))
    centre = bm.verts.new((cx, cy, z0 + radius * 0.45))
    for i in range(10):
        bm.faces.new((upper[i], upper[(i + 1) % 10], centre))
    bm.faces.new(list(reversed(lower)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_object("star", bm, mat, smooth=True, bevel=0.012)


CORALS = [("#ef3f5f", "#7a1530"), ("#f2559a", "#7d1648"), ("#8f55e6", "#3d1e7a"), ("#ff8b2b", "#8a3a0a"), ("#ff5a7a", "#801a35")]


def coral_cluster(rng, cx, cy, z0, spread, scale=1.0, palette=None):
    color, inner = palette or rng.choice(CORALS)
    mat = material(f"coral-{color}", color, rough=0.45, gradient=(tone(color, 0.55), z0 - 0.05, z0 + 0.3))
    imat = material(f"coral-in-{inner}", inner, rough=0.8)
    count = rng.randint(6, 8)
    tubes = []
    for i in range(count):
        a = i * math.tau / count + rng.uniform(-0.4, 0.4)
        d = spread * (0.25 if i == 0 else rng.uniform(0.55, 1.0))
        r = rng.uniform(0.07, 0.1) * scale
        hgt = (rng.uniform(0.55, 0.75) if i == 0 else rng.uniform(0.25, 0.55)) * scale
        lean = (math.cos(a) * d * 0.7, math.sin(a) * d * 0.7)
        tubes.append(cylinder(cx + math.cos(a) * d, cy + math.sin(a) * d, z0 - 0.02, r, hgt, mat, imat, lean=lean))
    return tubes


def moss(rng, cx, cy, z, count, spread):
    mat = material("moss", "#52cc3f", rough=0.6)
    dark = material("moss-dark", "#2f9a33", rough=0.6)
    for _ in range(count):
        s = rng.uniform(0.035, 0.06)
        x = cx + rng.uniform(-spread, spread)
        y = cy + rng.uniform(-spread, spread)
        box(x - s, y - s, z - 0.01, x + s, y + s, z + s * rng.uniform(0.9, 1.5), rng.choice([mat, mat, dark]), bevel=0.012)


def stone_block(rng, cx, cy, z0, size, height, pieces=3):
    mat = material("stone", "#d5dde6", rough=0.7, gradient=("#8c9aac", z0, z0 + height))
    objs = []
    split = rng.random() < 0.5
    for i in range(pieces):
        if split:
            px = cx - size / 2 + (i + 0.5) * size / pieces
            w = size / pieces * 0.96
            hh = height * rng.uniform(0.75, 1.0)
            objs.append(box(px - w / 2, cy - size / 2, z0, px + w / 2, cy + size / 2, z0 + hh, mat, bevel=0.025))
        else:
            py = cy - size / 2 + (i + 0.5) * size / pieces
            w = size / pieces * 0.96
            hh = height * rng.uniform(0.75, 1.0)
            objs.append(box(cx - size / 2, py - w / 2, z0, cx + size / 2, py + w / 2, z0 + hh, mat, bevel=0.025))
    moss(rng, cx, cy, z0 + height * 0.92, rng.randint(4, 7), size * 0.4)
    return objs


# -------------------------------------------------------------------- pieces

def rock_pile(seed, low=False):
    """Collidable wall-rock cell: two or three squat domed boulders filling the cell."""
    rng = random.Random(seed)
    layouts = [
        [(0.3, -0.3, 0.3), (0.7, -0.36, 0.3), (0.5, -0.72, 0.34)],
        [(0.32, -0.66, 0.32), (0.7, -0.68, 0.3), (0.52, -0.3, 0.32)],
        [(0.5, -0.5, 0.45)],
        [(0.36, -0.42, 0.38), (0.74, -0.72, 0.26)],
        [(0.62, -0.4, 0.38), (0.28, -0.72, 0.27)],
    ]
    for x, y, radius in rng.choice(layouts):
        radius *= rng.uniform(0.95, 1.08)
        x += rng.uniform(-0.03, 0.03)
        y += rng.uniform(-0.03, 0.03)
        x = min(max(x, radius * 0.85 + 0.02), 0.98 - radius * 0.85)
        y = min(max(y, -0.98 + radius * 0.85), -0.02 - radius * 0.85)
        hgt = rng.uniform(0.32, 0.55) if low else rng.uniform(0.4, 0.82)
        prism(rng, x, y, radius, hgt, sides=rng.choice([6, 7, 7, 8]), tilt=0.1, dome=rng.uniform(0.3, 0.42))


def rock_big(seed):
    """Interior-only boulder that overhangs its neighbours to break the grid."""
    rng = random.Random(seed)
    prism(rng, 0.5 + rng.uniform(-0.08, 0.08), -0.5 + rng.uniform(-0.05, 0.05), rng.uniform(0.62, 0.72), rng.uniform(0.7, 1.0), sides=rng.choice([7, 8]), tilt=0.08, dome=0.36)
    prism(rng, rng.choice([0.15, 0.85]), -0.88, 0.24, rng.uniform(0.3, 0.45), dome=0.4)


def rock_tall(seed):
    """Tall basalt column variant for skyline variety."""
    rng = random.Random(seed)
    prism(rng, 0.5, -0.5, 0.4, rng.uniform(1.0, 1.3), sides=7, tilt=0.06, dome=0.25)
    prism(rng, rng.choice([0.26, 0.74]), -0.76, 0.22, rng.uniform(0.35, 0.55), dome=0.35)


def stone_cell(seed):
    """Pale broken basalt columns with moss caps (concept "Broken Column")."""
    rng = random.Random(seed)
    grey = material("stone", "#d3dbe5", rough=0.7, gradient=("#6f7d92", 0.0, 0.9))
    prism(rng, 0.5, -0.55, 0.42, 0.22, tilt=0.02)
    tall = rng.uniform(0.85, 1.25)
    cx, cy = 0.5 + rng.uniform(-0.06, 0.06), -0.48
    prism(rng, cx, cy, 0.27, tall, sides=6, tilt=0.06, mat=grey)
    prism(rng, cx + rng.choice([-0.2, 0.2]), -0.72, 0.2, tall * rng.uniform(0.4, 0.6), sides=6, tilt=0.05, mat=grey)
    moss(rng, cx, cy, tall - 0.02, rng.randint(4, 6), 0.15)
    moss(rng, 0.5, -0.8, 0.22, 3, 0.25)


def reef_cell(seed):
    rng = random.Random(seed)
    grey = material("stone", "#d3dbe5", rough=0.7, gradient=("#6f7d92", 0.0, 0.9))
    for x, y in ((0.3, -0.3), (0.7, -0.32), (0.3, -0.7), (0.7, -0.7)):
        prism(rng, x, y, 0.24, rng.uniform(0.32, 0.42), sides=6, tilt=0.03, mat=grey)
    moss(rng, 0.5, -0.5, 0.38, 6, 0.3)
    coral_cluster(rng, 0.5, -0.52, 0.36, 0.2, scale=0.95)


def kelp_blade(rng, cx, cy, z0, height, width, mat, sway=0.12, lean=None):
    """Rounded, tapered kelp stalk with real thickness (elliptic cross-section)."""
    bm = bmesh.new()
    steps, ring = 14, 10
    phase = rng.uniform(0, math.tau)
    lean_x, lean_y = lean if lean else (rng.uniform(-0.12, 0.12), rng.uniform(-0.04, 0.08))
    rings = []
    for i in range(steps + 1):
        t = i / steps
        px = cx + math.sin(phase + t * 6.0) * sway * t + lean_x * t
        py = cy + math.cos(phase * 0.7 + t * 4.0) * sway * 0.35 * t + lean_y * t
        pz = z0 + t * height
        w = width * (0.75 + 0.45 * math.sin(math.pi * min(1.0, t * 1.35))) * (1.0 - t ** 3)
        w = max(w, 0.004)
        verts = []
        for k in range(ring):
            a = k * math.tau / ring
            verts.append(bm.verts.new((px + math.cos(a) * w, py + math.sin(a) * w * 0.62, pz)))
        rings.append(verts)
    for lower, upper in zip(rings, rings[1:]):
        for k in range(ring):
            j = (k + 1) % ring
            bm.faces.new((lower[k], lower[j], upper[j], upper[k]))
    tip = bm.verts.new((rings[-1][0].co.x - width * 0.0, rings[-1][0].co.y, z0 + height + width * 0.6))
    centre_tip = Vector((sum(v.co.x for v in rings[-1]) / ring, sum(v.co.y for v in rings[-1]) / ring, z0 + height + width * 0.5))
    tip.co = centre_tip
    for k in range(ring):
        bm.faces.new((rings[-1][k], rings[-1][(k + 1) % ring], tip))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_object("kelp", bm, mat, smooth=True)


KELP_GREENS = [("#3ad63c", "#1c8a30"), ("#72e440", "#2a9a2c"), ("#2cc64a", "#178032")]


def kelp_clump(rng, cx, cy, z0, count=None, tall=1.0):
    count = count or rng.randint(4, 6)
    for i in range(count):
        color, dark = rng.choice(KELP_GREENS)
        mat = material(f"kelp-{color}", color, rough=0.5, gradient=(dark, z0, z0 + 1.0))
        # Fan the stalks: spread across the gap, each leaning away from the centre.
        f = (i + 0.5) / count - 0.5
        a = rng.uniform(0, math.tau)
        d = rng.uniform(0.0, 0.05)
        kelp_blade(rng, cx + f * 0.26 + math.cos(a) * d, cy + math.sin(a) * d * 0.6 + (0.04 if i % 2 else -0.03), z0 - 0.02,
                   rng.uniform(0.7, 1.25) * tall * (1.0 - abs(f) * 0.4), rng.uniform(0.07, 0.095), mat, sway=0.11,
                   lean=(f * 0.55 + rng.uniform(-0.04, 0.04), rng.uniform(-0.02, 0.06)))


def branch_coral(rng, cx, cy, z0, color, scale=1.0):
    """Antler coral: rounded branching limbs (concept's orange/red branch coral)."""
    mat = material(f"coral-{color}", color, rough=0.45, gradient=(tone(color, 0.55), z0 - 0.05, z0 + 0.4))

    def limb(x, y, z, angle, tilt, length, radius, depth):
        dx = math.sin(tilt) * math.cos(angle) * length
        dy = math.sin(tilt) * math.sin(angle) * length
        dz = math.cos(tilt) * length
        cylinder(x, y, z, radius, dz, mat, hollow=False, segments=10, lean=(dx, dy), cap_scale=0.85)
        ex, ey, ez = x + dx, y + dy, z + dz
        if depth == 0:
            bm = bmesh.new()
            bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=radius * 0.9)
            obj = mesh_object("tip", bm, mat, smooth=True)
            obj.location = (ex, ey, ez)
            return
        for da in (-0.9, 0.9):
            limb(ex, ey, ez, angle + da + rng.uniform(-0.3, 0.3), min(1.0, tilt + 0.35), length * 0.7, radius * 0.8, depth - 1)
    for k in range(rng.randint(2, 3)):
        limb(cx + rng.uniform(-0.05, 0.05), cy + rng.uniform(-0.04, 0.04), z0 - 0.02, rng.uniform(0, math.tau), rng.uniform(0.15, 0.35), 0.26 * scale, 0.065 * scale, 2)


def big_coral(rng, cx, cy, z0, scale=1.0):
    """Tube coral cluster with mixed colours, tallest tube near the middle."""
    palettes = rng.sample(CORALS, 2)
    count = rng.randint(6, 8)
    for i in range(count):
        color, inner = palettes[0] if i % 3 else palettes[1]
        mat = material(f"coral-{color}", color, rough=0.45, gradient=(tone(color, 0.5), z0 - 0.05, z0 + 0.5))
        imat = material(f"coral-in-{inner}", inner, rough=0.8)
        a = i * math.tau / count + rng.uniform(-0.35, 0.35)
        d = 0.03 if i == 0 else rng.uniform(0.08, 0.16) * scale
        r = rng.uniform(0.075, 0.105) * scale
        hgt = (rng.uniform(0.85, 1.05) if i == 0 else rng.uniform(0.45, 0.8)) * scale
        lean = (math.cos(a) * (0.08 + d * 0.6), math.sin(a) * (0.05 + d * 0.5))
        cylinder(cx + math.cos(a) * d, cy + math.sin(a) * d * 0.7, z0 - 0.02, r, hgt, mat, imat, lean=lean)


# Rock nests: boulder arrangements that leave a seabed gap where growth roots.
# Each entry: boulders (x, y, radius) and the gap centre (x, y).
NESTS = [
    ([(0.26, -0.27, 0.26), (0.76, -0.3, 0.25), (0.8, -0.8, 0.2), (0.2, -0.84, 0.17)], (0.48, -0.62)),
    ([(0.5, -0.25, 0.3), (0.2, -0.76, 0.21), (0.82, -0.74, 0.19)], (0.52, -0.66)),
    ([(0.7, -0.38, 0.32), (0.28, -0.84, 0.18), (0.86, -0.86, 0.13)], (0.28, -0.42)),
    ([(0.3, -0.38, 0.31), (0.74, -0.84, 0.18), (0.16, -0.86, 0.13)], (0.7, -0.44)),
]


def nest_rocks(layout, seed):
    rng = random.Random(seed * 31 + layout)
    boulders, _gap = NESTS[layout]
    objs = []
    for x, y, radius in boulders:
        objs.append(prism(rng, x, y, radius * rng.uniform(0.95, 1.08), rng.uniform(0.32, 0.62),
                          sides=rng.choice([6, 7, 7, 8]), tilt=0.08, dome=rng.uniform(0.3, 0.42)))
    return objs


def nest_cell(layout, seed):
    nest_rocks(layout, seed)


def nest_growth(layout, seed, kind, variant):
    """Growth rooted on the seabed inside a nest; the nest's rocks are a holdout.

    The rocks occlude the plant's base exactly as in the obstacle sprite drawn
    beneath, yet stay out of this sprite, so decor remains a separate,
    non-collidable layer.
    """
    holdout = bpy.data.collections.new("Holdout")
    bpy.context.scene.collection.children.link(holdout)
    for obj in nest_rocks(layout, seed):
        bpy.context.scene.collection.objects.unlink(obj)
        holdout.objects.link(obj)
        obj.is_holdout = True
    lineset = bpy.context.view_layer.freestyle_settings.linesets[0]
    lineset.select_by_collection = True
    lineset.collection = holdout
    lineset.collection_negation = "EXCLUSIVE"
    rng = random.Random(variant * 977 + layout * 13 + seed)
    gx, gy = NESTS[layout][1]
    floor = 0.06
    if kind == "coral":
        big_coral(rng, gx, gy, floor)
    elif kind == "branch":
        branch_coral(rng, gx, gy, floor, rng.choice(["#ff8b2b", "#ef3f5f", "#ff6a3d"]), scale=1.15)
    elif kind == "kelp":
        kelp_clump(rng, gx, gy, floor)
    elif kind == "garden":
        big_coral(rng, gx - 0.07, gy - 0.03, floor, scale=0.85)
        kelp_clump(rng, gx + 0.14, gy + 0.06, floor, count=2, tall=0.9)
    elif kind == "star":
        # Starfish resting on the top of the nest's largest boulder.
        boulders = NESTS[layout][0]
        bx, by, br = max(boulders, key=lambda b: b[2])
        tops = [o for o in holdout.objects]
        top = max(v.co.z for v in tops[boulders.index((bx, by, br))].data.vertices)
        starfish(bx, by, top - 0.03, 0.15, material("starfish", "#ff7a3d", rough=0.55), rot=rng.uniform(0, 1))


def seabed_decor(kind, seed):
    """Low, darker non-collidable decoration for open water cells."""
    rng = random.Random(seed)
    if kind == "fan":
        mat = material("fan", "#1f5aa6", rough=0.9)
        def branch(x, z, angle, length, width, depth):
            x1, z1 = x + math.sin(angle) * length, z + math.cos(angle) * length
            bm = bmesh.new()
            nx, nz = math.cos(angle) * width, -math.sin(angle) * width
            vs = [bm.verts.new((x - nx, -0.5, z - nz)), bm.verts.new((x + nx, -0.5, z + nz)),
                  bm.verts.new((x1 + nx * 0.6, -0.5, z1 + nz * 0.6)), bm.verts.new((x1 - nx * 0.6, -0.5, z1 - nz * 0.6))]
            bm.faces.new(vs)
            obj = mesh_object("fan", bm, mat)
            sol = obj.modifiers.new("Solid", "SOLIDIFY"); sol.thickness = 0.03
            if depth > 0:
                for da in (-0.45, 0.4):
                    branch(x1, z1, angle + da + rng.uniform(-0.15, 0.15), length * rng.uniform(0.62, 0.78), width * 0.7, depth - 1)
        branch(0.5 + rng.uniform(-0.1, 0.1), 0, rng.uniform(-0.15, 0.15), 0.22, 0.03, 3)
    elif kind == "grass":
        mat = material("grass", "#1f8f75", rough=0.8)
        for i in range(rng.randint(4, 6)):
            kelp(rng, 0.5 + rng.uniform(-0.3, 0.3), -0.5 + rng.uniform(-0.3, 0.3), 0, rng.uniform(0.2, 0.34), mat, width=0.05, sway=0.02)
    elif kind == "star":
        starfish(0.5, -0.5, 0, 0.16, material("starfish", "#ff7a3d", rough=0.55), rot=rng.uniform(0, 1))
    elif kind == "pebbles":
        mat = material("pebble", "#2a5fa8", rough=0.8)
        for i in range(rng.randint(3, 5)):
            prism(rng, 0.5 + rng.uniform(-0.3, 0.3), -0.5 + rng.uniform(-0.3, 0.3), rng.uniform(0.06, 0.1), rng.uniform(0.05, 0.1), mat=mat)


def wreck(seed):
    """2x2 collidable broken hull: crossed beams and planks over a rock bed."""
    rng = random.Random(seed)
    wood = material("wood", "#b47236", rough=0.7, gradient=("#6c3d1a", 0.0, 0.9))
    wood_dark = material("wood-dark", "#8a5326", rough=0.75)
    iron = material("iron", "#7f8fa3", rough=0.4, metallic=0.6)
    for x, y in ((0.5, -0.5), (1.5, -0.5), (0.5, -1.5), (1.5, -1.5)):
        prism(rng, x, y, 0.4, rng.uniform(0.2, 0.4))
    # Hull ribs: long beams on diagonals.
    def beam(x0, y0, x1, y1, z0, z1, thick, mat):
        length = math.hypot(x1 - x0, y1 - y0)
        dz = z1 - z0
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co.x *= math.hypot(length, dz)
            v.co.y *= thick
            v.co.z *= thick * 0.9
        obj = mesh_object("beam", bm, mat, bevel=0.02)
        obj.rotation_euler = (0, -math.atan2(dz, length), math.atan2(y1 - y0, x1 - x0))
        obj.location = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
        return obj
    beam(0.15, -1.7, 1.85, -0.35, 0.35, 1.1, 0.17, wood)
    beam(0.2, -0.35, 1.8, -1.75, 0.95, 0.4, 0.16, wood)
    beam(0.1, -1.0, 1.9, -0.95, 0.75, 0.75, 0.14, wood_dark)
    for i in range(4):
        x = 0.35 + i * 0.42
        beam(x, -1.85, x + rng.uniform(-0.1, 0.1), -0.2, 0.3, 0.3 + rng.uniform(0.0, 0.3), 0.12, rng.choice([wood, wood_dark]))
    for x, y in ((0.95, -1.02), (0.5, -0.62), (1.45, -1.38)):
        cylinder(x, y, 0.95, 0.05, 0.06, iron, hollow=False, segments=8)
    moss(rng, 0.4, -1.5, 0.45, 4, 0.2)
    moss(rng, 1.6, -0.4, 0.5, 3, 0.15)


def gold_nugget(frame, frames):
    rng = random.Random(77)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.19)
    for v in bm.verts:
        v.co *= rng.uniform(0.72, 1.18)
        v.co.x *= 1.12
        v.co.z *= 0.8
    bmesh.ops.convex_hull(bm, input=bm.verts)
    mat = material("gold", "#ffd21f", rough=0.3, metallic=0.15, emission=0.18, spec=0.9, gradient=("#e88a00", -0.2, 0.25))
    obj = mesh_object("gold", bm, mat, bevel=0.01)
    obj.rotation_euler = (0.35, 0.2, frame / frames * math.tau)
    obj.location = (0.5, -0.5, 0.18)


def tube_y(cx, y0, cz, radius, length, mat, inner_mat=None, segments=18, taper=1.0):
    """Closed tube laid along +Y; the far (-Y) end can show a dark nozzle."""
    bm = bmesh.new()
    back, front = [], []
    for i in range(segments):
        a = i * math.tau / segments
        back.append(bm.verts.new((cx + math.cos(a) * radius * taper, y0, cz + math.sin(a) * radius * taper)))
        front.append(bm.verts.new((cx + math.cos(a) * radius, y0 + length, cz + math.sin(a) * radius)))
    for i in range(segments):
        j = (i + 1) % segments
        bm.faces.new((back[i], back[j], front[j], front[i]))
    cap_front = bm.faces.new(front)
    cap_back = bm.faces.new(list(reversed(back)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if inner_mat:
        bmesh.ops.inset_region(bm, faces=[cap_back], thickness=radius * 0.28, depth=0)
        cap_back.material_index = 1
        for v in cap_back.verts:
            v.co.y += length * 0.25
    return mesh_object("tubey", bm, [mat, inner_mat or mat], smooth=True, bevel=radius * 0.2, segments=2)


def submarine(frame, frames):
    yellow = material("sub-yellow", "#ffc91c", rough=0.35, spec=0.6)
    yellow_dark = material("sub-yellow-dark", "#e8a210", rough=0.4)
    red = material("sub-red", "#e8392c", rough=0.4)
    dark = material("sub-dark", "#3a3f4f", rough=0.5)
    glass = material("sub-glass", "#1d7cf2", rough=0.08, spec=1.0, emission=0.15)
    rim = material("sub-rim", "#f2b10e", rough=0.35, metallic=0.4)
    cx, cy, cz = 0.5, -0.5, 0.34
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=0.29)
    for v in bm.verts:
        v.co.y *= 1.12
        v.co.z *= 0.9
        v.co += Vector((cx, cy, cz))
    mesh_object("hull", bm, yellow, smooth=True)

    def disc(px, py, pz, r, mat, depth, tilt):
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=28, radius1=r, radius2=r * 0.9, depth=depth)
        obj = mesh_object("disc", bm, mat, smooth=True)
        obj.location = (px, py, pz)
        obj.rotation_euler = (tilt, 0, 0)
        return obj
    disc(cx, cy + 0.03, cz + 0.25, 0.135, rim, 0.07, math.radians(-14))
    disc(cx, cy + 0.035, cz + 0.285, 0.1, glass, 0.04, math.radians(-14))
    disc(cx - 0.035, cy + 0.07, cz + 0.307, 0.03, material("sub-shine", "#e8f6ff", rough=0.1, emission=0.8), 0.01, math.radians(-14))
    # Side thrusters with dark rear nozzles.
    for side in (-1, 1):
        tube_y(cx + side * 0.355, cy - 0.2, cz - 0.03, 0.09, 0.36, red, dark, taper=0.9)
        box(cx + side * 0.19 - 0.06, cy - 0.06, cz - 0.08, cx + side * 0.19 + 0.06, cy + 0.06, cz + 0.02, yellow_dark, bevel=0.015)
    # Periscope pointing forward (+Y).
    cylinder(cx, cy + 0.13, cz + 0.18, 0.035, 0.18, yellow_dark, hollow=False, segments=12)
    box(cx - 0.045, cy + 0.1, cz + 0.33, cx + 0.045, cy + 0.3, cz + 0.41, yellow, bevel=0.02)
    box(cx - 0.1, cy + 0.17, cz + 0.34, cx + 0.1, cy + 0.24, cz + 0.4, red, bevel=0.015)
    # Rear nozzle and propeller (animated).
    tube_y(cx, cy - 0.42, cz - 0.02, 0.085, 0.14, yellow_dark, dark)
    blade_angle = frame / frames * math.tau / 3
    for k in range(3):
        a = blade_angle + k * math.tau / 3
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co.x *= 0.035
            v.co.y *= 0.02
            v.co.z *= 0.22
            v.co.z += 0.06
        b = mesh_object("blade", bm, dark, bevel=0.006)
        b.rotation_euler = (0, a, 0)
        b.location = (cx, cy - 0.45, cz - 0.02)
    bolt = material("sub-bolt", "#d48f0c", rough=0.4)
    for px, py in ((-0.2, -0.1), (0.2, -0.1), (-0.13, 0.19), (0.13, 0.19)):
        cylinder(cx + px, cy + py, cz + 0.12, 0.02, 0.12, bolt, hollow=False, segments=8)


def fish():
    mat = material("fish", "#1c4f9a", rough=0.9)
    bm = bmesh.new()
    pts = [(0.0, 0.0), (0.12, 0.06), (0.24, 0.035), (0.32, 0.08), (0.3, 0.0), (0.32, -0.08), (0.24, -0.035), (0.12, -0.06)]
    verts = [bm.verts.new((0.5 + x, -0.5 + y, 0)) for x, y in pts]
    bm.faces.new(verts)
    mesh_object("fish", bm, mat)


# ----------------------------------------------------------------- catalogue

def build(name, fn, *args, footprint=(1, 1), extra=None, ink=True):
    if ONLY and name not in ONLY and name.split("-")[0] not in ONLY:
        return
    reset_scene()
    # Beds join edge to edge; outlining them would draw the grid as seams.
    bpy.context.scene.render.use_freestyle = ink
    fn(*args)
    render(name, footprint, extra=extra)


def main():
    global _manifest
    if ONLY and os.path.exists(MANIFEST):
        with open(MANIFEST) as fh:
            _manifest = json.load(fh).get("sprites", {})
    for mask in range(16):
        n, e, s, w = bool(mask & 1), bool(mask & 2), bool(mask & 4), bool(mask & 8)
        build(f"bed-{mask:02d}", lambda m=(n, e, s, w): base_slab(m, material("bed", "#1a3a9c", rough=0.7, gradient=(ROCK_DARK, -0.02, 0.4))), extra={"layer": "bed", "mask": mask}, ink=False)
    for i in range(10):
        build(f"rock-{i:02d}", rock_pile, 100 + i, extra={"layer": "obstacle", "family": "rock"})
    for i in range(3):
        build(f"rocktall-{i:02d}", rock_tall, 200 + i, extra={"layer": "obstacle", "family": "rock"})
    for i in range(4):
        build(f"rockbig-{i:02d}", rock_big, 250 + i, extra={"layer": "obstacle", "family": "rock", "interior_only": True})
    for i in range(4):
        build(f"stone-{i:02d}", stone_cell, 300 + i, extra={"layer": "obstacle", "family": "stone"})
    for i in range(3):
        build(f"reef-{i:02d}", reef_cell, 400 + i, extra={"layer": "obstacle", "family": "reef"})
    build("wreck-00", wreck, 500, footprint=(2, 2), extra={"layer": "obstacle", "family": "wreck"})
    growth = {"coral": 2, "branch": 1, "kelp": 1, "garden": 1, "star": 1}
    for layout in range(len(NESTS)):
        for seed in range(2):
            build(f"nest-{layout}{seed}", nest_cell, layout, seed, extra={"layer": "obstacle", "family": "rock", "nest": True})
            for kind, count in growth.items():
                for variant in range(count):
                    build(f"grow-{kind}-{layout}{seed}{variant}", nest_growth, layout, seed, kind, variant,
                          extra={"layer": "decor", "family": kind, "anchor": "nest", "nest": f"nest-{layout}{seed}"})
    for kind, count in (("fan", 3), ("grass", 3), ("star", 2), ("pebbles", 3)):
        for i in range(count):
            build(f"seabed-{kind}-{i:02d}", seabed_decor, kind, 700 + i * 5 + len(kind), extra={"layer": "decor", "family": kind, "anchor": "seabed"})
    for f in range(12):
        build(f"gold-{f:02d}", gold_nugget, f, 12, extra={"layer": "pickup", "frame": f, "camera": "ortho"})
    for f in range(6):
        build(f"sub-{f:02d}", submarine, f, 6, extra={"layer": "ship", "frame": f, "camera": "ortho"})
    build("fish-00", fish, extra={"layer": "background"})
    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
    with open(MANIFEST, "w") as fh:
        json.dump({
            "format": "sushi-loop-expedition-kit",
            "version": 1,
            "cell_pixels": PX,
            "height_projection": HEIGHT_PROJECTION,
            "source": "assets/expedition/v1/build_kit.py",
            "sprites": dict(sorted(_manifest.items())),
        }, fh, indent=1)


main()
