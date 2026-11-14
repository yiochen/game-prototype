# Draft-01 feasibility probe: torus-mapped (period-1 cell) 4D noise on a pre-footing 'rest' attribute,
# per-slab tone attribute, z strata on sides, voronoi hairline cracks. Not a candidate.
import bpy, math, sys, random
from pathlib import Path
HERE = Path(__file__).resolve().parent
src = (HERE/'base.py').read_text().split("args = sys.argv")[0]
g = {'__file__': str(HERE/'base.py'), '__name__': 'base'}; exec(compile(src, 'base.py', 'exec'), g)
R = g['R']
TAU = math.tau
def lin(h): return g['R'].lin(h)
def build_mat(name, kind):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; n = nt.nodes; l = nt.links; n.clear()
    out = n.new('ShaderNodeOutputMaterial'); bs = n.new('ShaderNodeBsdfPrincipled')
    bs.inputs['Roughness'].default_value = .82; bs.inputs['Specular IOR Level'].default_value = .12
    rest = n.new('ShaderNodeAttribute'); rest.attribute_type = 'GEOMETRY'; rest.attribute_name = 'rest'
    tone = n.new('ShaderNodeAttribute'); tone.attribute_type = 'OBJECT'; tone.attribute_name = 'tone'
    sep = n.new('ShaderNodeSeparateXYZ'); l.new(rest.outputs['Vector'], sep.inputs[0])
    def mathop(op, a, b=None, c=None):
        k = n.new('ShaderNodeMath'); k.operation = op
        for i, v in enumerate((a, b, c)):
            if v is None: continue
            if isinstance(v, (int, float)): k.inputs[i].default_value = v
            else: l.new(v, k.inputs[i])
        return k.outputs[0]
    ax = mathop('MULTIPLY', sep.outputs['X'], TAU); ay = mathop('MULTIPLY', sep.outputs['Y'], TAU)
    def torus(rad, zk=0.0):
        cx = mathop('MULTIPLY', mathop('COSINE', ax), rad); sx = mathop('MULTIPLY', mathop('SINE', ax), rad)
        cy = mathop('MULTIPLY', mathop('COSINE', ay), rad); sy = mathop('MULTIPLY', mathop('SINE', ay), rad)
        if zk: cy = mathop('ADD', cy, mathop('MULTIPLY', sep.outputs['Z'], zk))
        comb = n.new('ShaderNodeCombineXYZ'); l.new(cx, comb.inputs[0]); l.new(sx, comb.inputs[1]); l.new(cy, comb.inputs[2])
        return comb.outputs[0], sy
    def noise4(rad, scale, detail=2, zk=0.0):
        v, w = torus(rad, zk); t = n.new('ShaderNodeTexNoise'); t.noise_dimensions = '4D'
        t.inputs['Scale'].default_value = scale; t.inputs['Detail'].default_value = detail
        l.new(v, t.inputs['Vector']); l.new(w, t.inputs['W']); return t.outputs['Fac']
    # Base colour: top vs side palette, broad periodic tone + per-slab tone
    base = lin('E6CA9E') if kind == 'top' else lin('C08E5A')
    broad = noise4(.35, 1.0, 2)
    var = mathop('ADD', mathop('MULTIPLY', mathop('SUBTRACT', broad, .5), .22), mathop('MULTIPLY', mathop('SUBTRACT', tone.outputs['Fac'], .5), .14))
    bright = mathop('ADD', 1.0, var)
    if kind == 'side':
        z = sep.outputs['Z']
        grad = mathop('ADD', .62, mathop('MULTIPLY', mathop('MINIMUM', mathop('DIVIDE', z, .30), 1.0), .42))
        wav = noise4(.5, 1.5, 1)
        strata = mathop('SINE', mathop('ADD', mathop('MULTIPLY', z, 95.0), mathop('MULTIPLY', wav, 4.0)))
        bright = mathop('MULTIPLY', bright, mathop('MULTIPLY', grad, mathop('ADD', 1.0, mathop('MULTIPLY', strata, .06))))
    rgb = n.new('ShaderNodeRGB'); rgb.outputs[0].default_value = base + (1,)
    mul = n.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1
    l.new(rgb.outputs[0], mul.inputs['A']); l.new(bright, mul.inputs['B'])
    col = mul.outputs['Result']
    if kind == 'top':
        # hairline cracks: per-slab-offset voronoi edges, masked to a few runs
        vor = n.new('ShaderNodeTexVoronoi'); vor.voronoi_dimensions = '4D'; vor.feature = 'DISTANCE_TO_EDGE'; vor.inputs['Scale'].default_value = 1.6
        v, w = torus(1.0); l.new(v, vor.inputs['Vector']); l.new(mathop('ADD', w, mathop('MULTIPLY', tone.outputs['Fac'], 9.0)), vor.inputs['W'])
        crack = mathop('LESS_THAN', vor.outputs['Distance'], .018)
        mask = mathop('GREATER_THAN', noise4(.8, 2.0, 1), .56)
        crack = mathop('MULTIPLY', crack, mask)
        dark = n.new('ShaderNodeMix'); dark.data_type = 'RGBA'; l.new(crack, dark.inputs['Factor']); l.new(col, dark.inputs['A']); dark.inputs['B'].default_value = lin('9C7A55') + (1,)
        col = dark.outputs['Result']
        pores = mathop('GREATER_THAN', noise4(2.0, 9.0, 0), .74)
        pd = n.new('ShaderNodeMix'); pd.data_type = 'RGBA'; l.new(pores, pd.inputs['Factor']); l.new(col, pd.inputs['A']); pd.inputs['B'].default_value = lin('B39270') + (1,)
        col = pd.outputs['Result']
    l.new(col, bs.inputs['Base Color']); l.new(col, bs.inputs['Emission Color']); bs.inputs['Emission Strength'].default_value = .10
    l.new(bs.outputs[0], out.inputs['Surface']); return m

ids = sys.argv[sys.argv.index('--') + 1].split(',')
sc, col, root, mats = g['scene']()
newm = [build_mat('Limestone top v', 'top'), build_mat('Limestone side v', 'side'), build_mat('Limestone side v2', 'side')]
for pid in ids:
    g['clear'](col, root)
    mask, p = int(pid.split('-')[1]), pid.split('-')[2]
    g['cell'](col, root, mask, p, sum(map(ord, pid)), mats)
    for i, ob in enumerate(sorted(col.objects, key=lambda o: o.name)):
        if ob.type != 'MESH': continue
        me = ob.data
        for k, mm in enumerate(newm): me.materials[k] = mm
        a = me.attributes.new('rest', 'FLOAT_VECTOR', 'POINT')
        for v in me.vertices: a.data[v.index].vector = ob.matrix_world @ v.co
        ob['tone'] = random.Random(f'{p}-{i}').random()
    g['capture'](sc, col, HERE / 'native' / pid)
