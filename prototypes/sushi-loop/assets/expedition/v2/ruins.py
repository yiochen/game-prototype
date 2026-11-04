"""Issue #21 pale statues and multi-tile arches in the approved ruin style.

Run from the repository root:

    blender -b --factory-startup --python prototypes/sushi-loop/assets/expedition/v2/ruins.py [-- id,id]

Materials, helpers, Cycles settings, light rig, 35° orthographic camera and
capture-only square footing follow the approved decor-ruin-fragment round-03
build/capture (assets/production/source/blender/refinement/decor-ruin-fragment/
source/round-03). That build runs on import, so its helpers are reproduced here
verbatim in behaviour. Each piece registers its ground root at the footprint
centre; arches span W cells with collidable legs only at the two end cells.
"""
import bpy, bmesh, json, math, random, sys
from pathlib import Path
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view

HERE = Path(__file__).resolve().parent
OUT = HERE / 'native' / 'ruins'
CELL, NATIVE = 128, 4


def linear(v): return v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4
def rgba(h): return tuple(linear(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4)) + (1,)


class Kit:
    """Ruin round-03 vocabulary bound to one collection/root."""

    def __init__(self, asset):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        self.sc = bpy.context.scene; self.sc.name = asset
        self.col = bpy.data.collections.new(asset); self.sc.collection.children.link(self.col)
        self.root = bpy.data.objects.new(asset + '__ground_root', None); self.col.objects.link(self.root)
        m = self.material
        self.stone = m('Warm ivory stone', 'D6D3BF', .88, .035); self.side = m('Stone worn edges', 'CBCAB8', .9, .035)
        self.chip = m('Fresh pale chipped stone', 'DCD8C5', .9, .025); self.recess = m('Blue gray carved recess', '3E6470', .94, .015)
        self.crack = m('Subtle weathered fracture', '6E8581', .96, .01)
        self.blue = [m('Cobalt reef facet ' + str(i), h, .9, .025) for i, h in enumerate(['125692', '1B689D', '154879', '237AA6', '164F84', '1B5B8C'])]
        self.moss = m('Fresh olive green moss', '698D25', .76, .045); self.leaf = m('Thick reef sprouts', '3E7944', .7, .025)

    def material(self, name, h, rough=.82, noise=.02):
        mat = bpy.data.materials.new(name); mat.use_nodes = True; t = mat.node_tree; n = t.nodes; l = t.links; n.clear()
        out = n.new('ShaderNodeOutputMaterial'); p = n.new('ShaderNodeBsdfPrincipled'); p.inputs['Roughness'].default_value = rough
        p.inputs['Specular IOR Level'].default_value = .16; l.new(p.outputs['BSDF'], out.inputs['Surface'])
        tex = n.new('ShaderNodeTexNoise'); tex.inputs['Scale'].default_value = 15; tex.inputs['Detail'].default_value = 2
        geo = n.new('ShaderNodeNewGeometry'); sep = n.new('ShaderNodeSeparateXYZ'); l.new(geo.outputs['Position'], sep.inputs[0]); l.new(geo.outputs['Position'], tex.inputs['Vector'])
        ramp = n.new('ShaderNodeMapRange'); ramp.inputs['From Min'].default_value = 0; ramp.inputs['From Max'].default_value = 1.8
        ramp.inputs['To Min'].default_value = .71; ramp.inputs['To Max'].default_value = 1.0; ramp.clamp = True; l.new(sep.outputs['Z'], ramp.inputs[0])
        base = n.new('ShaderNodeRGB'); base.outputs[0].default_value = rgba(h)
        mul = n.new('ShaderNodeMixRGB'); mul.blend_type = 'MULTIPLY'; mul.inputs[0].default_value = 1; l.new(base.outputs[0], mul.inputs[1]); l.new(ramp.outputs[0], mul.inputs[2])
        var = n.new('ShaderNodeMapRange'); var.inputs['To Min'].default_value = 1 - noise; var.inputs['To Max'].default_value = 1 + noise; l.new(tex.outputs['Fac'], var.inputs[0])
        grain = n.new('ShaderNodeMixRGB'); grain.blend_type = 'MULTIPLY'; grain.inputs[0].default_value = 1; l.new(mul.outputs[0], grain.inputs[1]); l.new(var.outputs[0], grain.inputs[2]); l.new(grain.outputs[0], p.inputs['Base Color'])
        if noise:
            bump = n.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = .14; bump.inputs['Distance'].default_value = .006
            l.new(tex.outputs['Fac'], bump.inputs['Height']); l.new(bump.outputs[0], p.inputs['Normal'])
        return mat

    def adopt(self, o, name, mat):
        o.name = name
        for c in list(o.users_collection): c.objects.unlink(o)
        self.col.objects.link(o); o.parent = self.root; o.data.materials.append(mat); return o

    def block(self, name, loc, size, mat, bevel=.025, rot=(0, 0, 0)):
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = self.adopt(bpy.context.object, name, mat)
        o.dimensions = size; bpy.ops.object.transform_apply(location=False, rotation=False, scale=True); o.rotation_euler = rot
        if bevel:
            b = o.modifiers.new('Worn rounded stone edges', 'BEVEL'); b.width = bevel; b.segments = 1; b.affect = 'EDGES'; b.profile = .58
            b = o.modifiers.new('Weighted broad stone planes', 'WEIGHTED_NORMAL'); b.keep_sharp = True; b.weight = 40
        return o

    def ellipsoid(self, name, loc, scale, mat, seg=14, rings=8):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, radius=1, location=loc); o = self.adopt(bpy.context.object, name, mat)
        o.scale = scale; bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        for p in o.data.polygons: p.use_smooth = True
        return o

    def mesh(self, name, verts, faces, mat):
        me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update(); o = bpy.data.objects.new(name, me)
        self.col.objects.link(o); o.parent = self.root; me.materials.append(mat); return o

    def wornstone(self, name, loc, size, mat, rows=None, top=None, cuts=(.12, .16, .15, .12), bevel=.012, sides=8):
        """Irregular broad cross-section prism with chipped shoulders (ruin round-03)."""
        x, y, z = loc; w, d, h = size; rows = rows or [(0, 1, 0), (1, 1, 0)]
        outline = [(-.5 + cuts[0], -.5), (.5 - cuts[1], -.5), (.5, -.5 + cuts[1]), (.5, .5 - cuts[2]), (.5 - cuts[2], .5), (-.5 + cuts[3], .5), (-.5, .5 - cuts[3]), (-.5, -.5 + cuts[0])]
        verts = []
        for j, (v, wide, shift) in enumerate(rows):
            for i, (xx, yy) in enumerate(outline):
                zz = z + h * (v - .5) + (top[i] if top and j == len(rows) - 1 else 0)
                verts.append((x + xx * w * wide + shift, y + yy * d * (1 - .018 * math.sin(j * 2 + i)), zz))
        faces = [tuple(reversed(range(8)))]
        for j in range(len(rows) - 1):
            for i in range(8): faces.append((j * 8 + i, j * 8 + (i + 1) % 8, (j + 1) * 8 + (i + 1) % 8, (j + 1) * 8 + i))
        faces.append(tuple((len(rows) - 1) * 8 + i for i in range(8)))
        o = self.mesh(name, verts, faces, mat)
        if bevel:
            md = o.modifiers.new('Soft chipped stone transitions', 'BEVEL'); md.width = bevel; md.segments = 2; md.limit_method = 'ANGLE'; md.angle_limit = .45
            md = o.modifiers.new('Broad worn stone normals', 'WEIGHTED_NORMAL'); md.keep_sharp = True; md.weight = 40
        return o

    def moss_cluster(self, label, bulbs):
        parts = [self.ellipsoid(label + ' growth volume', c, s, self.moss, 20, 12) for c, s in bulbs]
        bpy.ops.object.select_all(action='DESELECT')
        for o in parts: o.select_set(True)
        bpy.context.view_layer.objects.active = parts[0]; bpy.ops.object.join(); o = parts[0]; o.name = label
        md = o.modifiers.new('Native continuous moss union', 'REMESH'); md.mode = 'VOXEL'; md.voxel_size = .006; md.use_smooth_shade = True
        bpy.ops.object.modifier_apply(modifier=md.name)
        md = o.modifiers.new('Soft living moss transitions', 'SMOOTH'); md.factor = .8; md.iterations = 4; bpy.ops.object.modifier_apply(modifier=md.name)
        for p in o.data.polygons: p.use_smooth = True
        return o

    def moss_cap(self, label, x, y, z, w, d, rng):
        """Puffy cap with a lobe hanging over the front edge, like the approved head."""
        bulbs = [((x + rng.uniform(-w, w) * .35, y + rng.uniform(-d, d) * .35, z + .01), (w * rng.uniform(.32, .46), d * rng.uniform(.32, .46), rng.uniform(.06, .085))) for _ in range(5)]
        fx = x + rng.uniform(-w, w) * .3
        bulbs += [((fx, y - d * .5, z - .03), (w * .22, .07, .085)), ((fx + .02, y - d * .56, z - .1), (w * .16, .05, .08))]
        return self.moss_cluster(label, bulbs)

    def sprouts(self, x, y, z, rng, count=3):
        """Thick rooted reef sprouts with a moss root, as around the approved head's footing."""
        for j in range(count):
            h = rng.uniform(.18, .34)
            o = self.ellipsoid('Rooted reef sprout', (x + (j - count / 2) * .045, y, z + h * .4), (.03, .052, h * .48), self.leaf)
            o.rotation_euler = (.16 * (j - 1), (-.18 if x < 0 else .18) + j * .06, (j - 1) * .3)
        self.moss_cluster('Sprout root moss', [((x, y, z), (.06, .07, .035)), ((x + .03, y - .02, z + .01), (.04, .05, .03))])

    def footing(self, name, cx, cy, w, d, h=.3, seed=0):
        """Cobalt faceted reef footing, as under the approved statue head."""
        rng = random.Random(seed)
        n = 12; out = []
        for i in range(n):
            a = i * math.tau / n; r = 1 + rng.uniform(-.06, .04)
            out.append((cx + math.cos(a) * w * .5 * r, cy + math.sin(a) * d * .5 * r))
        verts = [(x, y, 0) for x, y in out] + [(cx + (x - cx) * .97, cy + (y - cy) * .97, h * rng.uniform(.4, .6)) for x, y in out]
        verts += [(cx + (x - cx) * .88, cy + (y - cy) * .88, h * rng.uniform(.85, 1.05)) for x, y in out] + [(cx, cy, h)]
        faces = [tuple(reversed(range(n)))]
        for j in range(2):
            for i in range(n):
                a = j * n + i; b = j * n + (i + 1) % n; c = (j + 1) * n + (i + 1) % n; dd = j * n + n + i
                faces.extend([(a, b, c), (a, c, dd)] if (i + j) % 4 == 1 else [(a, b, c, dd)])
        for i in range(n): faces.append((2 * n + i, 2 * n + (i + 1) % n, 3 * n))
        o = self.mesh(name, verts, faces, self.blue[0])
        for m in self.blue[1:]: o.data.materials.append(m)
        for p in o.data.polygons: p.material_index = 1 if p.normal.z > .45 else (2 if p.normal.z < -.08 else (3 + p.index % 3))
        md = o.modifiers.new('Worn natural reef edges', 'BEVEL'); md.width = .010; md.segments = 1; md.limit_method = 'ANGLE'; md.angle_limit = .8
        md = o.modifiers.new('Broad reef plane normals', 'WEIGHTED_NORMAL'); md.keep_sharp = True; md.weight = 30
        return o

    def carved_head(self, label, pivot, scale, rot):
        """The approved head silhouette (body, eye niches, brow, nose, mouth, ears, crown), posed."""
        holder = bpy.data.objects.new(label, None); self.col.objects.link(holder); holder.parent = self.root
        start = set(self.col.objects)
        body = self.wornstone(label + ' carved mass', (0, .015, .94), (.69, .58, 1.33), self.stone,
                              rows=[(0, .90, -.004), (.24, 1, -.008), (.66, .98, .004), (1, .965, 0)],
                              top=[-.025, -.005, .012, -.012, -.024, .005, -.01, -.025], cuts=(.13, .18, .14, .13), bevel=.018)
        bpy.context.view_layer.objects.active = body
        for mod in list(body.modifiers): bpy.ops.object.modifier_apply(modifier=mod.name)
        for x in (-.185, .185):
            cut = self.block('Eye cutter', (x, -.285, 1.17), (.195, .15, .22), self.stone, .027)
            bpy.context.view_layer.objects.active = cut
            for mod in list(cut.modifiers): bpy.ops.object.modifier_apply(modifier=mod.name)
            mod = body.modifiers.new('Carved eye niche', 'BOOLEAN'); mod.operation = 'DIFFERENCE'; mod.object = cut
            bpy.context.view_layer.objects.active = body; bpy.ops.object.modifier_apply(modifier=mod.name); bpy.data.objects.remove(cut, do_unlink=True)
            self.block(label + ' inset eye', (x, -.223, 1.17), (.160, .018, .183), self.recess, .020)
        self.wornstone(label + ' forehead', (0, .025, 1.735), (.755, .61, .405), self.stone, rows=[(0, .965, 0), (.56, 1, -.004), (1, .965, .006)],
                       top=[-.015, .008, -.015, -.025, .012, -.008, -.027, -.004], cuts=(.17, .11, .18, .14), bevel=.014)
        self.wornstone(label + ' brow', (0, -.327, 1.420), (.835, .202, .190), self.chip, rows=[(0, .94, .006), (.38, 1, 0), (1, .965, -.004)],
                       top=[-.020, .004, -.006, -.014, -.008, -.002, -.016, -.023], cuts=(.075, .14, .11, .08), bevel=.013)
        self.block(label + ' nose bridge', (0, -.323, 1.055), (.170, .245, .480), self.stone, .029)
        self.block(label + ' nose end', (0, -.363, .824), (.242, .249, .137), self.side, .028)
        self.block(label + ' mouth', (0, -.284, .667), (.318, .022, .035), self.recess, .009)
        self.block(label + ' lip', (0, -.311, .617), (.348, .108, .097), self.chip, .023)
        for x in (-.383, .383): self.block(label + ' ear', (x, .028, 1.382), (.134, .26, .375), self.side, .044)
        for i, (x, y, z, sz) in enumerate([(-.205, .045, 1.985, (.217, .245, .20)), (.125, .070, 2.010, (.250, .265, .235))]):
            self.wornstone(label + ' crown ' + str(i), (x, y, z), sz, self.chip, rows=[(0, 1, 0), (.60, 1.02, -.004), (1, .92, .004)], cuts=(.16, .20, .12, .17), bevel=.012)
        for o in set(self.col.objects) - start - {holder}:
            o.parent = holder
        holder.location = pivot; holder.scale = (scale,) * 3; holder.rotation_euler = rot
        return holder


# ------------------------------------------------------------------ pieces
# Each returns (frame width cells, frame height logical px, root logical px, footprint, solid cells).

def statue_tilted(k):
    rng = random.Random(11)
    k.footing('Reef footing', 0, 0, .98, .96, .3, 1)
    k.sprouts(-.36, -.24, .29, rng); k.sprouts(.38, .22, .29, rng, 2)
    k.carved_head('Tilted head', (0, .02, .1), .92, (0, math.radians(14), math.radians(-8)))
    k.moss_cap('Crown moss', .36, .05, 1.94, .3, .26, rng)
    k.moss_cap('Footing moss', .3, -.25, .3, .14, .12, rng)


def statue_fallen(k):
    rng = random.Random(12)
    k.footing('Reef footing', 0, 0, .98, .96, .22, 2)
    # Lying on its side: rotating about Y lays the head's height along +X, so pivot left of centre.
    k.carved_head('Fallen head', (-.5, .06, .3), .5, (math.radians(-6), math.radians(84), math.radians(8)))
    k.wornstone('Broken crown drum', (.33, .28, .25), (.3, .28, .2), k.chip, cuts=(.2, .16, .18, .2))
    k.moss_cap('Side moss', -.05, .12, .52, .3, .2, rng)


def statue_guardian(k):
    rng = random.Random(13)
    k.footing('Reef footing', 0, 0, .98, .96, .26, 3)
    k.sprouts(-.38, -.26, .25, rng)
    k.wornstone('Plinth', (0, .02, .48), (.8, .72, .44), k.side, rows=[(0, 1, 0), (1, .95, 0)], cuts=(.1, .1, .1, .1))
    k.carved_head('Guardian head', (0, .05, .66), .7, (0, 0, math.radians(4)))
    k.wornstone('Headdress', (0, .1, 2.18), (.62, .5, .3), k.chip, rows=[(0, .9, 0), (1, 1.05, 0)], cuts=(.06, .06, .06, .06))
    k.moss_cap('Headdress moss', .08, .1, 2.34, .26, .2, rng)


def pillar_capital(k):
    rng = random.Random(14)
    k.footing('Reef footing', 0, 0, .96, .94, .26, 4)
    k.sprouts(.34, -.28, .25, rng)
    k.wornstone('Column base', (0, 0, .36), (.74, .74, .2), k.side, cuts=(.1, .1, .1, .1))
    k.wornstone('Column shaft', (0, 0, 1.12), (.52, .52, 1.36), k.stone, rows=[(0, 1, 0), (.5, .96, 0), (1, .98, 0)], cuts=(.15, .15, .15, .15), bevel=.02)
    for i in range(8):
        a = i * math.tau / 8 + math.pi / 8
        k.block('Flute groove', (math.cos(a) * .255, math.sin(a) * .255, 1.12), (.03, .03, 1.2), k.recess, 0, (0, 0, a))
    k.wornstone('Capital', (0, 0, 1.9), (.78, .78, .2), k.chip, cuts=(.08, .08, .08, .08))
    k.moss_cap('Capital moss', 0, 0, 2.02, .34, .32, rng)


def pillar_stump(k):
    rng = random.Random(15)
    k.footing('Reef footing', 0, 0, .98, .96, .24, 5)
    k.sprouts(-.36, -.3, .23, rng, 2)
    k.wornstone('Broken column', (-.08, .12, .62), (.5, .5, .8), k.stone, top=[.1, -.05, .14, -.02, .08, -.1, .05, .12], cuts=(.15, .15, .15, .15))
    k.wornstone('Fallen drum', (.22, -.22, .38), (.44, .4, .26), k.chip, cuts=(.14, .14, .14, .14))
    k.moss_cap('Stump moss', -.08, .12, 1.05, .22, .2, rng)


def stele(k):
    rng = random.Random(16)
    k.footing('Reef footing', 0, 0, .98, .96, .26, 6)
    k.sprouts(.36, -.25, .25, rng)
    k.wornstone('Stele slab', (0, .05, 1.1), (.72, .26, 1.6), k.stone, top=[0, .04, -.03, .1, .12, -.02, .03, 0], cuts=(.08, .08, .08, .08), bevel=.02)
    for i, (x, z, w) in enumerate([(0, 1.5, .4), (-.1, 1.2, .26), (.08, .95, .32), (0, .7, .22)]):
        k.block('Glyph ' + str(i), (x, -.085, z), (w, .02, .07), k.recess, .008)
    k.moss_cap('Stele moss', .1, .05, 1.9, .26, .14, rng)


def ruined_leg(k, x, side, leg_h, rng, seed):
    """Weathered pier: chipped uneven top, a displaced course and reef footing."""
    k.footing('Leg footing', x, 0, .98, .96, .26, seed)
    k.sprouts(x + .34 * side, -.26, .25, rng)
    lower = leg_h * rng.uniform(.5, .6)
    k.wornstone('Leg lower course', (x, 0, .26 + lower / 2), (.7, .62, lower), k.stone, rows=[(0, 1, 0), (1, .98, 0)], cuts=(.14, .16, .12, .15), bevel=.02)
    upper = leg_h - lower
    k.wornstone('Leg upper course', (x + rng.uniform(-.04, .04), rng.uniform(-.03, .03), .26 + lower + upper / 2 + .01), (.66, .6, upper),
                k.side, rows=[(0, .97, 0), (1, 1, 0)], cuts=(.18, .12, .2, .1), bevel=.02)
    k.block('Chipped pier corner', (x + .26 * side, -.22, .26 + lower + .05), (.16, .14, .12), k.chip, .02, (0, 0, rng.uniform(-.4, .4)))
    top = .26 + leg_h + .07
    k.wornstone('Impost', (x, 0, top), (.84, .7, .14), k.chip, top=[rng.uniform(-.04, .03) for _ in range(8)], cuts=(.14, .06, .16, .1))
    return top + .07


def rubble(k, x, side, rng, count=3):
    """Fallen voussoirs lying on the leg's own footing (never in the open span)."""
    for i in range(count):
        s = rng.uniform(.14, .24)
        k.block('Fallen voussoir', (x + side * rng.uniform(.18, .36), rng.uniform(-.34, -.16), .26 + s * .3),
                (s * 1.3, s, s * .8), rng.choice([k.chip, k.side, k.stone]), .025, (rng.uniform(-.3, .3), rng.uniform(-.4, .4), rng.uniform(0, math.pi)))


def voussoirs(k, rng, half, spring, rz, count, profile, skip=()):
    """Jittered, chipped voussoir ring; `skip` indices have fallen out."""
    rx = half - .02
    placed = []
    for i in range(count):
        if i in skip:
            continue
        t0, t1 = math.pi * i / count, math.pi * (i + 1) / count
        tm = (t0 + t1) / 2
        x, z = profile(tm, rx, rz)
        x0, z0 = profile(t0, rx, rz); x1, z1 = profile(t1, rx, rz)
        length = math.hypot(x1 - x0, z1 - z0)
        angle = math.atan2(z1 - z0, x1 - x0)
        mat = k.chip if i == count // 2 else rng.choice([k.stone, k.side, k.stone, k.chip])
        depth = .6 * rng.uniform(.82, 1.0)
        # Settled, weathered stones: uneven lengths open small joints, slight twists.
        k.block('Voussoir ' + str(i), (x + rng.uniform(-.03, .03), rng.uniform(-.07, .07), spring + z + rng.uniform(-.05, .02)),
                (length * rng.uniform(.82, .98), depth, rng.uniform(.25, .36)), mat, .035,
                (rng.uniform(-.1, .1), -angle + rng.uniform(-.13, .13), rng.uniform(-.1, .1)))
        placed.append((x, spring + z))
        if rng.random() < .3:
            k.block('Chipped corner', (x + rng.uniform(-.06, .06), -depth / 2 - .02, spring + z + .12), (.1, .08, .08), k.chip, .015, (0, 0, rng.uniform(0, 1)))
    return placed


def segmental(t, rx, rz): return -math.cos(t) * rx, math.sin(t) * rz
def pointed(t, rx, rz):
    # Two curved flanks meeting at a raised apex (lancet).
    u = abs(math.cos(t)); return -math.cos(t) * rx, (1 - u) ** .62 * rz


def arch(k, span, style):
    """Ruined pale stone arch over `span` open cells; legs occupy the two end cells."""
    rng = random.Random(sum(map(ord, style)) * 10 + span)
    half = (span + 1) / 2
    leg_h = {'ruin': 1.3, 'broken': 1.35, 'pointed': 1.2}[style] + rng.uniform(-.05, .05)
    tops = [ruined_leg(k, side * half, side, leg_h + (rng.uniform(-.12, 0) if side > 0 else 0), rng, 30 + side) for side in (-1, 1)]
    spring = min(tops)
    count = 7 + 2 * span
    if style == 'ruin':
        lost = {rng.choice([count // 2 - 2, count // 2 + 2])}
        placed = voussoirs(k, rng, half, spring, .55, count, segmental, lost)
    elif style == 'broken':
        mid = count // 2
        placed = voussoirs(k, rng, half, spring, .55, count, segmental, set(range(mid - 1, mid + 2 + (span > 2))))
    else:
        placed = voussoirs(k, rng, half, spring, 1.0, count + 2, pointed, {rng.randrange(2, count - 1)})
    for side in (-1, 1):
        rubble(k, side * half, side, rng, 2 + (style == 'broken'))
    # Moss and sprouts only on stones that are actually there.
    for x, z in rng.sample(placed, min(len(placed), 3 + span)):
        k.moss_cap('Voussoir moss', x, 0, z + .19, .2, .24, rng)
    for x, z in rng.sample(placed, 2):
        k.sprouts(x, -.05, z + .17, rng, 2)
    for side in (-1, 1):
        k.moss_cap('Leg moss', side * half + .2 * side, -.25, .3, .14, .12, rng)


def bridge(k, span):
    """Collapsed slab bridge: cracked deck slabs between piers, one sagging."""
    rng = random.Random(70 + span)
    half = (span + 1) / 2
    tops = [ruined_leg(k, side * half, side, 1.05 + rng.uniform(-.08, .04), rng, 40 + side) for side in (-1, 1)]
    deck = min(tops)
    slabs = span + 2
    width = (2 * half + .6) / slabs
    for i in range(slabs):
        x = -half - .3 + width * (i + .5)
        inner = 0 < i < slabs - 1
        # Inner slabs settle into a shallow V where the deck cracked; end slabs rest on piers.
        drop = rng.uniform(.06, .14) if inner else 0
        tilt = (rng.uniform(.06, .12) if inner else rng.uniform(-.02, .02)) * (1 if x < 0 else -1)
        slab = k.wornstone('Deck slab ' + str(i), (x, rng.uniform(-.03, .03), deck + .1 - drop), (width * .96, .66, .2),
                           rng.choice([k.stone, k.side]), top=[rng.uniform(-.02, .02) for _ in range(8)], cuts=(.06, .1, .08, .06), bevel=.02)
        # Tilt about the slab's own centre (mesh vertices are authored in root space).
        slab.data.transform(Matrix.Translation((x, 0, deck)) @ Matrix.Rotation(tilt, 4, 'Y') @ Matrix.Translation((-x, 0, -deck)))
    for side in (-1, 1):
        for j in range(2):
            x = side * (half - .05 - j * .45)
            h = rng.uniform(.22, .45)
            k.wornstone('Broken parapet', (x, -.27, deck + .2 + h / 2), (.3, .12, h), k.side, top=[rng.uniform(-.08, .04) for _ in range(8)], cuts=(.2, .2, .2, .2))
        rubble(k, side * half, side, rng, 2)
        k.sprouts(side * (half - .3), .1, deck + .2, rng, 2)
    k.moss_cap('Deck moss', rng.uniform(-.4, .4) * half, .05, deck + .24, .32, .24, rng)
    k.moss_cap('Deck moss 2', rng.uniform(-.4, .4) * half, -.05, deck + .24, .24, .2, rng)


PIECES = {
    'statue-tilted': (statue_tilted, 1), 'statue-fallen': (statue_fallen, 1), 'statue-guardian': (statue_guardian, 1),
    'pillar-capital': (pillar_capital, 1), 'pillar-stump': (pillar_stump, 1), 'stele': (stele, 1),
    **{f'arch-{style}-{span}': ((lambda style, span: lambda k: arch(k, span, style))(style, span), span + 2)
       for style, spans in (('ruin', (1, 2, 3)), ('broken', (2, 3)), ('pointed', (1, 2))) for span in spans},
    **{f'bridge-{span}': ((lambda span: lambda k: bridge(k, span))(span), span + 2) for span in (1, 2, 3)},
}


def setup_capture(k, width_cells, frame_h=512, root_y=416):
    sc = k.sc
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 32; sc.cycles.use_denoising = True; sc.cycles.seed = 0
    frame_w = int((width_cells + .5) * CELL)
    sc.render.resolution_x = frame_w * NATIVE; sc.render.resolution_y = frame_h * NATIVE; sc.render.resolution_percentage = 100
    sc.render.pixel_aspect_x = sc.render.pixel_aspect_y = 1; sc.render.film_transparent = True
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'; sc.render.image_settings.color_depth = '8'
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'; sc.view_settings.exposure = 0; sc.view_settings.gamma = 1
    cam = bpy.data.objects.new('Registered ruin camera 35deg', bpy.data.cameras.new('Registered ruin camera 35deg')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.sensor_fit = 'HORIZONTAL'; cam.data.ortho_scale = frame_w / CELL
    ang = math.radians(35); cam.location = (0, -10 * math.cos(ang), 10 * math.sin(ang)); cam.rotation_euler = (-cam.location).to_track_quat('-Z', 'Y').to_euler()
    # Calibrate vertical shift so the ground root lands at the registered pixel.
    cam.data.shift_y = 0; bpy.context.view_layer.update(); base = (1 - world_to_camera_view(sc, cam, Vector((0, 0, 0))).y) * sc.render.resolution_y
    cam.data.shift_y = 1; bpy.context.view_layer.update(); one = (1 - world_to_camera_view(sc, cam, Vector((0, 0, 0))).y) * sc.render.resolution_y
    cam.data.shift_y = (root_y * NATIVE - base) / (one - base); bpy.context.view_layer.update()
    world = bpy.data.worlds.new('Balanced neutral ambient'); world.use_nodes = True; sc.world = world
    bg = world.node_tree.nodes.get('Background'); bg.inputs['Color'].default_value = (.7, .78, .85, 1); bg.inputs['Strength'].default_value = .16
    def light(name, loc, power, size, color):
        d = bpy.data.lights.new(name, 'AREA'); d.energy = power; d.shape = 'DISK'; d.size = size; d.color = color
        o = bpy.data.objects.new(name, d); sc.collection.objects.link(o); o.location = loc; o.rotation_euler = (Vector((0, 0, 1)) - o.location).to_track_quat('-Z', 'Y').to_euler()
    light('Soft centered overhead', (0, 0, 4.5), 110 * max(1, width_cells / 1.5), 3.5 * max(1, width_cells / 2), (1, .94, .83))
    for a in (0, 90, 180, 270):
        t = math.radians(a); light('Equal cardinal fill ' + str(a), ((3 + width_cells / 2) * math.cos(t), 3 * math.sin(t), 2.0), 72, 4, (1, .98, .94))
    return frame_w


def capture(k, out, directions):
    meshes = [o for o in k.col.all_objects if o.type == 'MESH']
    for direction, degrees in directions:
        k.root.rotation_euler.z = math.radians(degrees); bpy.context.view_layer.update()
        saved = []
        try:
            dg = bpy.context.evaluated_depsgraph_get()
            for o in meshes:
                # Bake modifiers so the footing deformation acts on final geometry.
                ev = o.evaluated_get(dg); me = bpy.data.meshes.new_from_object(ev)
                saved.append((o, o.data, list(o.modifiers)))
                old_mods = [(m.name) for m in o.modifiers]
                o.modifiers.clear(); o.data = me
                inv = o.matrix_world.inverted()
                for v in me.vertices:
                    w = o.matrix_world @ v.co; blend = max(0, 1 - max(0, w.z) / .42) ** 2
                    w.y *= 1 + (1 / math.sin(math.radians(35)) - 1) * blend; v.co = inv @ w
                me.update()
            bpy.context.view_layer.update()
            k.sc.render.filepath = str(out / f'static-{direction}.png'); bpy.ops.render.render(write_still=True)
        finally:
            for o, data, _mods in saved:
                o.data = data
        # Modifiers were consumed by the capture copy; rebuild the scene per direction.
        return


def main():
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    only = set(args[0].split(',')) if args else None
    manifest = OUT / 'pieces.json'
    records = json.loads(manifest.read_text())['pieces'] if manifest.exists() else {}
    for old in [p for p in records if p.startswith('arch-') and p.count('-') == 1]:
        records.pop(old)  # superseded first-pass arches
    for pid, (fn, width) in PIECES.items():
        if only and pid not in only:
            continue
        directions = [('S', 0)] if pid.startswith(('arch', 'bridge')) else [('N', 180), ('E', 90), ('S', 0), ('W', -90)]
        out = OUT / pid; out.mkdir(parents=True, exist_ok=True)
        for direction in directions:
            k = Kit(pid); fn(k); frame_w = setup_capture(k, width)
            if direction == directions[0]:
                bpy.ops.wm.save_as_mainfile(filepath=str(out / 'project.blend'), compress=True)
            capture(k, out, [direction])
        records[pid] = {'footprint': [width, 1], 'frame': [frame_w, 512], 'root': [frame_w / 2, 416], 'directions': [d for d, _ in directions],
                        'solidCells': [[0, 0], [width - 1, 0]] if pid.startswith(('arch', 'bridge')) else [[0, 0]]}
    (OUT / 'pieces.json').write_text(json.dumps({'style': 'decor-ruin-fragment round-03', 'nativeScale': NATIVE, 'pieces': records}, indent=1) + '\n')


if __name__ == '__main__':
    main()
