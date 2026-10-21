"""Native, reusable dense garden clusters.

Root alone executes this module through Blender MCP. No rendering, publishing,
camera fitting, external I/O or user-scene deletion occurs here. Geometry comes
from the existing native component builders, with independent object/mesh IDs.
All positions are relative to a fixed ground center; depth is -Y, height is Z.
"""

import importlib.util
import json
import math
from pathlib import Path
import sys


CLUSTER_IDS = (
    'restaurant-border-garden-a', 'restaurant-border-garden-b',
    'restaurant-corner-garden-a', 'restaurant-corner-garden-b',
    'underwater-reef-garden-a', 'underwater-reef-garden-b',
    'underwater-coral-garden-a', 'underwater-coral-garden-b',
)
ASSET_IDS = CLUSTER_IDS
CLIPS = {
    'ambient': {'frames': 12, 'fps': 12, 'loop': True},
    'static': {'frames': 1, 'fps': 12, 'loop': False, 'static': True},
}
SOURCES = {
    'plant': ('P', 'potted_plant'), 'slate': ('W', 'slate-rock'),
    'rubble': ('P', 'rubble'), 'boulder': ('W', 'boulder-underwater'),
    'kelp': ('P', 'kelp_group'), 'branch': ('P', 'coral_branch'),
    'tubes': ('P', 'coral_tubes'), 'column': ('P', 'ruin_column'),
    'lantern': ('P', 'lantern'), 'crate': ('P', 'crate'),
    'barrel': ('P', 'barrel'), 'star': ('P', 'starfish'),
    'reef': ('P', 'reef_rock'),
}

# Source, X, Y, uniform native scale, yaw radians. The short rows of ground
# foliage are not a tile lattice: unequal overlaps and varied heights connect
# the larger masses, and lower stones finish the irregular outline.
LAYOUTS = {
 'restaurant-border-garden-a': [
    ('plant',-.40,1.48,.84,.18), ('plant',.43,-1.25,.64,-.35),
    ('lantern',.42,.62,.77,-.10), ('crate',-.40,-.69,.56,.24),
    ('shoot',.28,1.30,.82,-.40), ('shoot',-.43,.90,.92,.33),
    ('shoot',.08,.57,.79,.81), ('shoot',-.47,.21,.86,-.26),
    ('shoot',.47,.02,.77,.56), ('shoot',-.14,-.30,.92,-.63),
    ('shoot',.40,-.61,.74,.26), ('shoot',-.48,-1.10,.88,.67),
    ('shoot',-.16,-1.57,.65,-.22), ('shoot',.55,1.67,.53,.46),
    ('slate',-.49,1.72,.51,.15), ('slate',.55,.97,.55,-.23),
    ('rubble',-.54,.48,.51,.82), ('slate',.56,-.28,.55,.25),
    ('rubble',-.48,-1.60,.48,-.14), ('slate',.47,-1.68,.52,.39),
    ('slate',-.58,-.24,.47,.11), ('rubble',.12,-.99,.44,.71),
 ],
 'restaurant-border-garden-b': [
    ('plant',.36,1.42,.91,-.30), ('plant',-.41,-.97,.69,.26),
    ('barrel',-.43,.71,.59,.12), ('lantern',.42,-.52,.73,.19),
    ('shoot',-.42,1.43,.83,.40), ('shoot',.08,.97,.88,-.70),
    ('shoot',.49,.48,.78,.25), ('shoot',-.40,.21,.86,.77),
    ('shoot',.11,-.05,.90,-.41), ('shoot',-.48,-.45,.80,-.33),
    ('shoot',.45,-1.12,.91,.59), ('shoot',-.10,-1.56,.76,.11),
    ('shoot',-.57,1.75,.45,-.12), ('shoot',.53,-1.70,.50,.71),
    ('slate',.52,1.73,.54,.68), ('rubble',-.55,1.08,.56,-.15),
    ('slate',.56,.08,.55,-.40), ('rubble',-.49,-.06,.52,.46),
    ('slate',-.55,-1.56,.53,-.27), ('slate',.38,-1.76,.47,.24),
    ('rubble',.08,-1.03,.48,.51), ('slate',-.10,.47,.44,-.81),
 ],
 'restaurant-corner-garden-a': [
    ('plant',-.77,.80,.95,.25), ('plant',.62,.90,.78,-.31),
    ('lantern',.81,.16,.83,-.10), ('crate',-.86,-.58,.67,.19),
    ('shoot',-.11,1.03,.88,.52), ('shoot',-.79,.26,.97,-.45),
    ('shoot',-.22,.49,.99,.15), ('shoot',.44,.40,.93,-.66),
    ('shoot',1.00,.68,.64,.48), ('shoot',-.20,-.12,.94,.83),
    ('shoot',.43,-.34,.90,-.20), ('shoot',-.74,-1.03,.71,.64),
    ('shoot',-.12,-.87,.86,-.34), ('shoot',.60,-.97,.72,.15),
    ('shoot',1.10,-.48,.56,.77),
    ('slate',-1.13,.97,.52,.12), ('slate',.98,1.08,.61,-.31),
    ('rubble',-.99,-.04,.59,.75), ('slate',1.07,-.07,.55,.28),
    ('rubble',-.40,-1.08,.58,-.22), ('slate',.99,-1.02,.60,.46),
    ('slate',-1.12,-.95,.54,-.40), ('rubble',.14,-.55,.50,.82),
    ('slate',.23,1.15,.49,.31),
 ],
 'restaurant-corner-garden-b': [
    ('plant',.81,.75,.96,-.25), ('plant',-.66,.92,.82,.43),
    ('lantern',-.83,.17,.80,.15), ('barrel',.84,-.49,.62,-.16),
    ('crate',.24,.18,.51,.30),
    ('shoot',.10,.99,.91,-.35), ('shoot',.79,.17,.91,.63),
    ('shoot',-.40,.45,.99,-.26), ('shoot',-.96,.74,.64,.47),
    ('shoot',-.26,-.13,.91,.81), ('shoot',.39,-.42,.92,-.57),
    ('shoot',-.72,-.75,.88,.19), ('shoot',.03,-.93,.90,-.30),
    ('shoot',.75,-1.05,.64,.41), ('shoot',-1.08,-.37,.58,.66),
    ('slate',1.10,1.04,.56,-.22), ('rubble',-1.09,1.09,.52,.40),
    ('slate',1.08,-.08,.53,.73), ('slate',-1.07,-.91,.58,-.38),
    ('rubble',.38,-1.12,.59,.30), ('slate',1.09,-.99,.54,-.54),
    ('rubble',-.35,-1.10,.51,.62), ('slate',-.07,.58,.46,.23),
    ('slate',-.22,1.17,.45,-.66),
 ],
 'underwater-reef-garden-a': [
    ('kelp',-.31,1.42,1.00,.22), ('column',.39,.80,.70,-.16),
    ('boulder',-.34,.33,.90,.23), ('reef',.34,-.52,.81,-.26),
    ('kelp',.46,1.48,.73,-.43), ('kelp',-.43,-.49,.83,.48),
    ('kelp',-.27,-1.32,.73,.18), ('kelp',.48,.13,.65,-.24),
    ('branch',.41,-1.21,.83,.37), ('tubes',-.48,.99,.67,-.29),
    ('tubes',-.38,-1.66,.58,.67), ('branch',.46,1.76,.49,-.15),
    ('branch',-.56,-.97,.57,.31), ('tubes',.10,-.07,.62,-.49),
    ('rubble',-.52,1.71,.55,.21), ('slate',.55,1.10,.51,.54),
    ('rubble',-.55,.62,.53,-.25), ('slate',.57,-.13,.51,.43),
    ('rubble',-.51,-1.42,.57,-.17), ('slate',.44,-1.73,.48,.62),
    ('star',.08,-1.70,.44,-.39), ('star',.51,-.83,.38,.19),
    ('slate',-.09,-.89,.47,.70), ('rubble',.14,1.02,.45,-.46),
 ],
 'underwater-reef-garden-b': [
    ('column',-.36,1.29,.78,.28), ('kelp',.39,.92,1.04,-.26),
    ('boulder',.30,-.03,.94,-.34), ('reef',-.36,-.95,.86,.37),
    ('kelp',.48,-1.22,.85,-.52), ('kelp',-.48,.36,.80,.24),
    ('kelp',.20,1.62,.68,.61), ('branch',-.52,1.76,.52,-.22),
    ('branch',-.43,-1.60,.63,.41), ('tubes',.45,.32,.73,-.38),
    ('tubes',-.44,-.32,.70,.15), ('branch',.41,-.73,.76,.53),
    ('tubes',.48,-1.72,.47,-.69), ('kelp',-.57,-.73,.52,.44),
    ('rubble',.51,1.71,.53,.11), ('slate',-.55,.87,.53,-.32),
    ('slate',.55,-.45,.50,.63), ('rubble',-.53,-1.35,.55,.25),
    ('slate',.04,-1.63,.51,-.49), ('rubble',-.08,.54,.47,.32),
    ('star',-.36,-1.78,.39,.45), ('star',.44,.73,.39,-.18),
    ('slate',-.56,1.59,.47,.71), ('rubble',.28,-1.08,.43,.38),
 ],
 'underwater-coral-garden-a': [
    ('kelp',-.84,.80,1.02,.21), ('column',.64,.84,.81,-.20),
    ('boulder',-.36,.31,.99,.31), ('reef',.62,-.26,.92,-.26),
    ('kelp',.05,.96,1.00,-.52), ('kelp',1.00,.38,.76,.43),
    ('kelp',-.89,-.36,.85,-.21), ('kelp',.28,-.85,.77,.68),
    ('branch',-.27,-.55,1.03,.31), ('tubes',.62,.25,.85,-.30),
    ('tubes',-.78,.16,.76,.64), ('branch',-.70,-1.02,.71,-.23),
    ('tubes',.73,-.98,.68,.35), ('branch',1.10,-.37,.55,.17),
    ('branch',-.08,1.12,.53,-.67), ('tubes',-.99,.97,.53,.42),
    ('slate',-1.09,.59,.62,-.22), ('rubble',1.06,.96,.58,.73),
    ('rubble',-.95,-.79,.64,.19), ('slate',1.05,-.77,.62,-.38),
    ('slate',-.22,-1.09,.63,.47), ('rubble',.20,.03,.53,.17),
    ('star',.22,-1.19,.50,-.35), ('star',1.13,.06,.43,.61),
    ('slate',.13,1.17,.48,-.29), ('rubble',-.97,-1.13,.43,.33),
 ],
 'underwater-coral-garden-b': [
    ('column',-.66,.88,.87,.26), ('kelp',.77,.81,1.04,-.21),
    ('reef',-.65,-.21,.98,.32), ('boulder',.37,.12,1.02,-.27),
    ('kelp',-.04,1.02,.91,.54), ('kelp',.88,-.34,.87,-.48),
    ('kelp',-.36,-.92,.79,.18), ('kelp',-1.03,.30,.74,-.32),
    ('tubes',.03,-.35,1.00,.61), ('branch',.67,-.91,.96,-.26),
    ('branch',-.82,.35,.80,.35), ('tubes',-.78,-.98,.70,-.52),
    ('branch',1.06,.91,.59,.26), ('tubes',.65,.62,.71,.47),
    ('branch',-1.09,-.38,.58,-.19), ('tubes',-.02,1.16,.52,.63),
    ('rubble',-1.08,.98,.59,.23), ('slate',1.08,.26,.57,-.39),
    ('slate',.97,-1.06,.61,.54), ('rubble',-.28,-1.12,.58,-.23),
    ('slate',-1.07,-.87,.60,.31), ('rubble',.17,.60,.54,-.66),
    ('star',.22,-1.18,.49,.16), ('star',-.91,-.59,.43,-.45),
    ('slate',.28,1.17,.47,.29), ('rubble',.99,.94,.45,-.38),
 ],
}


def layout(asset_id):
    """Pure-data layout for review/auditing before Blender execution."""
    if asset_id not in CLUSTER_IDS:
        raise ValueError('Unknown native cluster ' + asset_id)
    footprint = [2, 4] if '-border-' in asset_id or '-reef-' in asset_id else [3, 3]
    components = []
    for index, (source, x, y, scale, yaw) in enumerate(LAYOUTS[asset_id]):
        components.append({
            'id': 'component-%02d' % index,
            'source': 'plant' if source == 'shoot' else source,
            'position': [x, y, 0.], 'uniformScale': scale,
            'yaw': yaw, 'phase': (index * .38196601125 + .13) % 1.,
            'groundFoliageOnly': source == 'shoot',
        })
    return {'id': asset_id, 'footprint': footprint, 'components': components,
            'family': 'W12' if asset_id.startswith('underwater-') else 'W02',
            'height': 1.70, 'nativeSource': 'catalog_clusters.py'}


def _module(name, filename):
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(name, str(Path(__file__).with_name(filename)))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _builders():
    return (_module('prop_builders', 'prop_builders.py'),
            _module('s33cluster_world', 'world_components.py'))


def _merge(host, child, namespace):
    import bpy
    target, source = host['collection'], child['collection']
    for obj in list(source.objects):
        obj.name = host['root'].name + '__' + namespace + '__' + obj.name
        source.objects.unlink(obj)
        target.objects.link(obj)
    bpy.data.collections.remove(source)
    child['root'].parent = host['root']
    host['parts'] = dict(host['parts'])
    host['parts'].update({namespace + '__' + name: obj for name, obj in child['parts'].items()})
    host['parts'][namespace + '__root'] = child['root']
    return child


def _organic_base(builder, footprint, underwater, variant):
    """A low irregular soil/stone island, never a rectangular table or tile."""
    width, depth = footprint
    count, vertices = 24, []
    for z in (.004, .035):
        for index in range(count):
            angle = index / count * math.tau
            c, s = math.cos(angle), math.sin(angle)
            wave = .93 + .035 * math.sin(3 * angle + variant) + .020 * math.cos(5 * angle - variant)
            vertices.append(((width / 2 - .10) * math.copysign(abs(c) ** .66, c) * wave,
                             (depth / 2 - .10) * math.copysign(abs(s) ** .66, s) * wave, z))
    faces = [tuple(reversed(range(count))), tuple(range(count, count * 2))]
    faces += [(i, (i + 1) % count, (i + 1) % count + count, i + count) for i in range(count)]
    builder.mesh('irregular_ground_island', vertices, faces, 'rock_dark' if underwater else 'wood_dark')


def _apply_component(child, spec, clip, t):
    animated = next((key for key, recipe in child['clips'].items()
                     if recipe.get('frames', 1) > 1 and not recipe.get('static')), None)
    source_clip = animated or next(iter(child['clips']))
    phase = (float(t) + spec['phase']) % 1. if clip == 'ambient' else spec['phase']
    child['pose'](source_clip, phase)
    root, scale = child['root'], spec['uniformScale']
    root.location = spec['position']
    root.rotation_euler = (0., 0., spec['yaw'])
    root.scale = (scale, scale, scale)
    if spec['groundFoliageOnly']:
        # Existing native stems start at Z=.40 above their pot. Move their stem
        # bases onto the island while keeping the source leaf animation intact.
        for name, obj in child['parts'].items():
            if name.endswith(('_pot', '_rim', '_soil')):
                obj.hide_render = True
                obj.hide_viewport = True
    # Authored once from actual source mesh geometry, independent of playback
    # frame and capture facing. This replaces the former nominal -.40 foliage
    # shift and also lifts native rocks whose source bases cross below Z=0.
    root.location.z += spec.get('groundLift', .035 - .40 * scale
                               if spec['groundFoliageOnly'] else 0.)


def _source_min_z(root):
    """Actual visible evaluated vertices in this component's native root frame."""
    import bpy
    bpy.context.view_layer.update()
    inverse = root.matrix_world.inverted()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    minimum = float('inf')
    count = 0
    for obj in root.children_recursive:
        if obj.type != 'MESH' or obj.hide_render:
            continue
        evaluated = obj.evaluated_get(depsgraph)
        transform = inverse @ evaluated.matrix_world
        mesh = evaluated.to_mesh()
        try:
            for vertex in mesh.vertices:
                minimum = min(minimum, (transform @ vertex.co).z)
                count += 1
        finally:
            evaluated.to_mesh_clear()
    if not count:
        raise ValueError('No visible native geometry to ground: ' + root.name)
    return minimum


def _set_ground_lift(spec, root):
    minimum = _source_min_z(root)
    spec['sourceGroundMinZ'] = minimum
    spec['groundPlaneZ'] = .035
    spec['groundLift'] = .035 - minimum * spec['uniformScale']
    spec['groundingPolicy'] = 'Fixed offset from evaluated native source geometry; never frame fitting.'
    root['source_ground_min_z'] = minimum
    root['fixed_ground_lift'] = spec['groundLift']
    root['cluster_ground_plane_z'] = .035


def ground_existing(asset):
    """Ground already-built cluster children by updating their shared specs.

    For existing pose closures, reload this same module object in place before
    calling this helper: their global _apply_component will then read groundLift.
    No geometry, object identities, capture frames or root transforms are fitted.
    """
    import bpy
    # Match create_asset's canonical static source phase before measuring, so a
    # later rebuild produces the same offset regardless of the last viewed frame.
    asset['reset']()
    specs = asset['composition_context']['components']
    for spec in specs:
        root = bpy.data.objects.get(spec['nativeRoot'])
        if root is None:
            raise KeyError('Missing native cluster component ' + spec['nativeRoot'])
        _set_ground_lift(spec, root)
    asset['root']['composition_context'] = json.dumps(asset['composition_context'])
    asset['root']['support_layout'] = json.dumps(asset['supportLayout'])
    asset['reset']()
    return asset


def create_asset(asset_id):
    """Build one independent dense multi-cell native cluster; return pipeline API."""
    import bpy
    plan = layout(asset_id)
    P, W = _builders()
    builder = P.Builder(asset_id)
    builder.footprint, builder.height = tuple(plan['footprint']), plan['height']
    _organic_base(builder, plan['footprint'], plan['family'] == 'W12', asset_id.endswith('-b'))
    # Finish before extending outward parts: its reset closes over builder.parts.
    asset = builder.finish({key: dict(value) for key, value in CLIPS.items()})
    base_pose = asset['pose']
    children = []
    for spec in plan['components']:
        module, ident = SOURCES[spec['source']]
        child = _merge(asset, (P if module == 'P' else W).create_asset(ident), spec['id'])
        role = ('ground-foliage' if spec['groundFoliageOnly'] else
                'foliage' if spec['source'] in ('plant', 'kelp') else
                'coral' if spec['source'] in ('branch', 'tubes', 'reef') else
                'lighting' if spec['source'] == 'lantern' else
                'stone' if spec['source'] in ('slate', 'rubble', 'boulder') else
                'detail' if spec['source'] == 'star' else 'structure')
        child['root']['source_component'] = ident
        child['root']['ground_foliage_only'] = spec['groundFoliageOnly']
        spec['role'] = role
        for name, obj in child['parts'].items():
            obj['cluster_component_id'] = spec['id']
            obj['cluster_component_role'] = role
            obj['cluster_source_asset'] = ident
            obj['cluster_source_part'] = name
        spec['nativeRoot'] = child['root'].name
        spec['nativeSourceAsset'] = ident
        spec['sourceFootprint'] = list(child['footprint'])
        # Hide optional pot meshes before evaluating the actual foliage base.
        _apply_component(child, spec, 'static', 0.)
        _set_ground_lift(spec, child['root'])
        children.append((child, spec))
    def pose(clip='ambient', t=0.):
        if clip not in asset['clips']:
            raise KeyError('Unknown cluster clip ' + clip)
        base_pose(clip, 0.)
        for child, spec in children:
            _apply_component(child, spec, clip, t)
        bpy.context.view_layer.update()
    asset['pose'] = pose
    asset['reset'] = lambda: pose('static', 0.)
    asset['ports'] = []
    asset['nonblocking'] = True
    asset['family'] = plan['family']
    asset['depth_layer'] = 'world'
    asset['source_script'] = 'catalog_clusters.py'
    asset['composition_context'] = {
        'kind': 'dense-organic-native-cluster', 'components': plan['components'],
        'componentCount': len(children), 'family': plan['family'],
        'footprintCells': plan['footprint'], 'groundRoot': [0., 0., 0.],
        'coordinateConvention': 'X right; depth -Y; Z height',
        'motion': 'Independent phase-offset native foliage/coral/lantern ambient cycles.',
        'collision': 'Decorative composition only; no occupancy or collision mechanic.',
    }
    asset['supportLayout'] = {
        'kind': 'native-cluster-support-envelope', 'footprintCells': plan['footprint'],
        'supportCells': [[x, y] for y in range(plan['footprint'][1]) for x in range(plan['footprint'][0])],
        'blockingCells': [], 'components': plan['components'],
        'groundRoot': [0., 0., 0.], 'maxVisualHeight': plan['height'],
    }
    root = asset['root']
    root['production_id'] = asset_id
    root['catalog_family'] = plan['family']
    root['source'] = 'catalog_clusters.py'
    root['ports'] = '[]'
    root['nonblocking'] = True
    root['depth_layer'] = 'world'
    root['support_cells'] = json.dumps(asset['supportLayout']['supportCells'])
    root['composition_context'] = json.dumps(asset['composition_context'])
    root['support_layout'] = json.dumps(asset['supportLayout'])
    asset['notes'].extend([
        'Dense native multi-cell scenery; irregular fractional arrangement, not a bitmap or a repeated tile lattice.',
        'Ground root remains centered in the declared footprint for every facing and frame.',
        'All component objects and mesh datablocks were independently authored by the existing native builders.',
    ])
    pose('static', 0.)
    return asset


def validate_bounds(asset, samples=12, tolerance=.025):
    """Read-only geometry audit across one complete cycle; never fit/reposition.

    Returns visible evaluated bounds in the fixed ground-root coordinate frame.
    Hidden pots and the retained old entry are excluded. Root controls execution.
    """
    import bpy
    from mathutils import Vector
    bounds = [[float('inf')] * 3, [float('-inf')] * 3]
    inverse = asset['root'].matrix_world.inverted()
    clip = 'ambient' if 'ambient' in asset['clips'] else next(iter(asset['clips']))
    for frame in range(samples):
        asset['pose'](clip, frame / samples)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        for obj in asset['root'].children_recursive:
            if obj.type != 'MESH' or obj.hide_render:
                continue
            evaluated = obj.evaluated_get(depsgraph)
            for corner in evaluated.bound_box:
                point = inverse @ evaluated.matrix_world @ Vector(corner)
                for axis in range(3):
                    bounds[0][axis] = min(bounds[0][axis], point[axis])
                    bounds[1][axis] = max(bounds[1][axis], point[axis])
    width, depth = asset['footprint']
    failures = []
    for axis, extent in enumerate((width, depth)):
        if bounds[0][axis] < -extent / 2 - tolerance or bounds[1][axis] > extent / 2 + tolerance:
            failures.append({'axis': 'XY'[axis], 'declared': [-extent / 2, extent / 2],
                             'actual': [bounds[0][axis], bounds[1][axis]]})
    if bounds[1][2] > asset['height'] + tolerance:
        failures.append({'axis': 'Z', 'declaredMax': asset['height'], 'actualMax': bounds[1][2]})
    return {'passed': not failures, 'bounds': bounds, 'failures': failures,
            'samples': samples, 'coordinateFrame': 'fixed native ground root'}
