#!/usr/bin/env python3
"""Read-only audit of issue 33 section-03 connections.

Reads the library and its native source records. No image or repository writes.
Optional --report writes JSON only to the explicitly supplied report path.
Port geometry comes from native records; published port metadata is checked too.
Loft cross-sections are independently read from the native builder's AST, without
importing bpy or executing the builder. This catches reversed asymmetric pieces.
"""
import argparse
import ast
import importlib.util
import json
import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True

DIRECTIONS = ('N', 'E', 'S', 'W')
ANGLES = {'S': 0., 'E': math.pi / 2, 'N': math.pi, 'W': -math.pi / 2}
NORMALS = {'N': (0., 1.), 'E': (1., 0.), 'S': (0., -1.), 'W': (-1., 0.)}
SCREEN_VECTORS = {'N': (0., -1.), 'E': (1., 0.), 'S': (0., 1.), 'W': (-1., 0.)}
# Native path tangent -> transverse normal, before capture-facing rotation.
TRANSVERSE = {'W': (0., 1.), 'E': (0., 1.), 'N': (-1., 0.), 'S': (1., 0.)}
DEFAULT_LIBRARY = Path('/Users/yiouchen/.codex/worktrees/sushi-loop-33-art-catalog/game-prototype/prototypes/sushi-loop/assets/production/library.json')
BASE = Path(__file__).resolve().parent


def read_json(path):
    return json.loads(Path(path).read_text())


def distance(a, b):
    return math.dist(a, b)


def rotate(point, direction):
    c, s = math.cos(ANGLES[direction]), math.sin(ANGLES[direction])
    return [c * point[0] - s * point[1], s * point[0] + c * point[1]]


def project(point, direction, camera):
    x, y = rotate(point, direction)
    z = point[2] if len(point) > 2 else 0.
    scale = camera.get('captureScale', 4)
    calibration = camera.get('calibration', {})
    X = calibration.get('unitX', [128 * scale, 0])
    D = calibration.get('unitDepth', [0, 128 * scale])
    H = calibration.get('unitHeight', [0, -128 * scale])
    return [(X[i] * x - D[i] * y + H[i] * z) / scale for i in range(2)]


def placement_root(placement, asset, cell_size=128):
    direction = placement.get('direction', 'S')
    footprint = asset.get('directionFootprints', {}).get(direction, asset['footprint'])
    root_cell = asset.get('directionRootCells', {}).get(direction, asset.get('rootCell', [v / 2 for v in footprint]))
    offset = placement.get('offset', [0, 0])
    return [(placement[axis] + root_cell[i]) * cell_size + offset[i] for i, axis in enumerate(('x', 'y'))]


def raw_ports(asset_id, info):
    if asset_id.startswith('belt-'):
        flow = info.get('flow')
        if not flow:
            raise ValueError('Belt has no authoritative native flow record: ' + asset_id)
        result = []
        for role in ('incoming', 'outgoing'):
            side = flow.get(role)
            if side:
                nx, ny = NORMALS[side]
                result.append({'name': role, 'direction': side,
                               'position': [nx * .5, ny * .5, flow.get('deckHeight', .64)],
                               'normal': [nx, ny, 0], 'profile': 'belt-deck-v1', 'role': role})
        return result
    return [dict(port, name=port.get('name', port['direction'])) for port in info.get('ports', [])]


def _source_value(node, values):
    """Resolve only native recipe literals/arithmetic, never execute source."""
    if isinstance(node, ast.Name) and node.id in values:
        return values[node.id]
    if isinstance(node, (ast.Tuple, ast.List)):
        return [_source_value(value, values) for value in node.elts]
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = _source_value(node.operand, values)
        return value if isinstance(node.op, ast.UAdd) else -value
    if isinstance(node, ast.BinOp):
        left, right = _source_value(node.left, values), _source_value(node.right, values)
        operations = {ast.Add: lambda: left + right, ast.Sub: lambda: left - right,
                      ast.Mult: lambda: left * right, ast.Div: lambda: left / right}
        operation = operations.get(type(node.op))
        if operation is not None:
            return operation()
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError) as error:
        raise ValueError('Native cross-section must use resolvable source literals: ' + ast.unparse(node)) from error


def _bind_source_target(target, value, values):
    if isinstance(target, ast.Name):
        values[target.id] = value
    elif isinstance(target, (ast.Tuple, ast.List)) and len(target.elts) == len(value):
        for child, item in zip(target.elts, value):
            _bind_source_target(child, item, values)
    else:
        raise ValueError('Unsupported native recipe loop target: ' + ast.unparse(target))


def _source_calls(statements, values=None):
    """Yield recipe calls with constant assignments and finite loops expanded."""
    values = dict(values or {})
    for statement in statements:
        if isinstance(statement, ast.Assign):
            try:
                value = _source_value(statement.value, values)
            except ValueError:
                pass  # Builder/scene objects are not needed for source geometry.
            else:
                for target in statement.targets:
                    if isinstance(target, (ast.Name, ast.Tuple, ast.List)):
                        _bind_source_target(target, value, values)
        if isinstance(statement, (ast.Expr, ast.Assign)) and isinstance(statement.value, ast.Call):
            yield statement.value, dict(values)
        elif isinstance(statement, ast.For):
            expression = statement.iter
            enumerated = isinstance(expression, ast.Call) and isinstance(expression.func, ast.Name) and expression.func.id == 'enumerate'
            if enumerated and len(expression.args) == 1 and not expression.keywords:
                items = enumerate(_source_value(expression.args[0], values))
            else:
                try:
                    items = _source_value(expression, values)
                except ValueError:
                    # Ignore detail-generation loops only when they cannot
                    # contain a seam-defining _tier or _loft call.
                    if any(isinstance(node, ast.Call) and _source_call_name(node) in ('_tier', '_loft') for node in ast.walk(statement)):
                        raise
                    continue
            for item in items:
                child_values = dict(values)
                _bind_source_target(statement.target, item, child_values)
                yield from _source_calls(statement.body, child_values)
        elif isinstance(statement, ast.If):
            # Current seam geometry is independent of end/corner dressing.
            # Read both branches so a future conditional seam cannot disappear
            # silently from the audit.
            yield from _source_calls(statement.body, values)
            yield from _source_calls(statement.orelse, values)


def _source_call_name(call):
    return call.func.id if isinstance(call.func, ast.Name) else call.func.attr if isinstance(call.func, ast.Attribute) else None


def _tier_section(width_z):
    """Cross-section of native square-miter _tier at an endpoint plane."""
    if len(width_z) < 2 or any(len(item) != 2 or item[0] <= 0 for item in width_z):
        raise ValueError('Native tier requires at least two positive-width height rings')
    first, *remaining = width_z
    return [(-first[0], first[1]), (first[0], first[1])] + [(width, z) for width, z in remaining] + [(-width, z) for width, z in reversed(remaining)]


def _contained_in_convex_section(inner, outer):
    """Prove a detail tier cannot change the outer native endpoint section."""
    edges = [(outer[i], outer[(i + 1) % len(outer)]) for i in range(len(outer))]
    def cross(a, b, point):
        return (b[0] - a[0]) * (point[1] - a[1]) - (b[1] - a[1]) * (point[0] - a[0])
    turns = [cross(a, b, outer[(i + 2) % len(outer)]) for i, (a, b) in enumerate(edges)]
    signs = {1 if value > 0 else -1 for value in turns if abs(value) > 1e-9}
    if len(signs) != 1:
        raise ValueError('Native outer loft must be convex to prove a detail tier is contained')
    winding = next(iter(signs))
    return all(winding * cross(a, b, point) >= -1e-9 for point in inner for a, b in edges)


def _revision_sections(revision_source):
    """Read approved V2 seams from their native modeling recipe, using stdlib."""
    tree = ast.parse(Path(revision_source).read_text())
    result = {}
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    for name in ('_wall', '_rock_wall'):
        if name not in functions:
            raise ValueError('Missing native revision seam builder: ' + name)
        function = functions[name]
        profile_ids = {_source_value(node.args[1], {}) for node in ast.walk(function)
                       if isinstance(node, ast.Call) and _source_call_name(node) == 'port' and len(node.args) >= 2}
        if len(profile_ids) != 1:
            raise ValueError('Native seam builder must declare one profile ID: ' + name)
        rings, contained_tiers = [], []
        for call, values in _source_calls(function.body):
            kind = _source_call_name(call)
            if name == '_wall' and kind == '_tier':
                rings.append(_tier_section(_source_value(call.args[3], values)))
            elif name == '_rock_wall' and kind == '_loft':
                rings.append(_source_value(call.args[3], values))
            elif name == '_rock_wall' and kind == '_tier':
                contained_tiers.append(_tier_section(_source_value(call.args[3], values)))
        if not rings:
            raise ValueError('No native endpoint geometry found in ' + name)
        if contained_tiers and (len(rings) != 1 or any(not _contained_in_convex_section(tier, rings[0]) for tier in contained_tiers)):
            raise ValueError('Native detail tier extends outside the audited loft section: ' + name)
        result[next(iter(profile_ids))] = rings
    return result


def cross_sections(world_source, revision_source=None):
    """Read V1/V2 endpoint rings from native source AST, without loading bpy.

    V2 rock-wall contact shoulders are inside the main loft's lower full-width
    section, so the loft supplies the outer seam. Its broad silhouette is read
    directly from _rock_wall's profile; it is not a copied V1 approximation.
    """
    world_source = Path(world_source)
    tree = ast.parse(Path(world_source).read_text())
    profiles = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'PROFILES' for t in node.targets):
            profiles.update({name + '-section-v1': [value] for name, value in ast.literal_eval(node.value).items()})
    for function in (n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ('build_wall', 'build_wreck')):
        rings = []
        for node in ast.walk(function):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name) or node.func.id != '_loft':
                continue
            section = node.args[3]
            if isinstance(section, ast.Call) and isinstance(section.func, ast.Name) and section.func.id == '_rect_profile':
                width, z, height = [ast.literal_eval(arg) for arg in section.args]
                ring = [(-width / 2, z), (width / 2, z), (width / 2, z + height), (-width / 2, z + height)]
            else:
                ring = ast.literal_eval(section)
            centers = node.args[2]
            base_z = 0.
            if isinstance(centers, ast.ListComp):
                z_node = centers.elt.elts[2]
                if isinstance(z_node, ast.Constant):
                    base_z = ast.literal_eval(z_node)
                elif isinstance(z_node, ast.Name) and z_node.id == 'z':
                    # Four decorative horizontal board rings in build_wall.
                    bases = []
                    for parent in ast.walk(function):
                        if isinstance(parent, ast.For) and isinstance(parent.target, ast.Tuple) and any(isinstance(t, ast.Name) and t.id == 'z' for t in parent.target.elts):
                            bases = ast.literal_eval(parent.iter.args[0])
                    rings.extend([[(w, z + base) for w, z in ring] for base in bases])
                    continue
            rings.append([(w, z + base_z) for w, z in ring])
        profiles['restaurant-wall-wood-blue-v1' if function.name == 'build_wall' else 'wreck-frame-section-v1'] = rings
    revision_source = Path(revision_source) if revision_source is not None else world_source.with_name('catalog_art_revision.py')
    if revision_source.is_file():
        profiles.update(_revision_sections(revision_source))
    return profiles


class Audit:
    def __init__(self, manifest, native_root, profiles, tolerance=.2):
        self.manifest = manifest
        self.by_id = {obj['id']: obj for obj in manifest['objects']}
        self.native_root = Path(native_root) if native_root else None
        self.profiles = profiles
        self.tolerance = tolerance
        self.info = {}
        self.camera = {}
        self.errors = []
        self.checked = []

    def error(self, asset_id, message, scene=None):
        self.errors.append({'object': asset_id, 'scene': scene, 'message': message})

    def load(self, asset_id):
        if asset_id in self.info:
            return self.info[asset_id]
        asset = self.by_id[asset_id]
        if self.native_root:
            record = self.native_root / asset_id / 'asset.json'
            camera = self.native_root / asset_id / 'camera.json'
        else:
            record = self.manifest_root / asset['source']['assetRecord']
            camera = self.manifest_root / asset['source']['camera']
        self.info[asset_id] = read_json(record)
        self.camera[asset_id] = read_json(camera)
        return self.info[asset_id]

    def ports_at(self, placement):
        asset_id = placement['object']
        asset = self.by_id[asset_id]
        info = self.load(asset_id)
        direction = placement.get('direction', 'S')
        ground = placement_root(placement, asset, self.manifest.get('cellSize', 128))
        result = []
        for port in raw_ports(asset_id, info):
            relative = project(port['position'], direction, self.camera[asset_id])
            point = [ground[i] + relative[i] for i in range(2)]
            normal = rotate(port['normal'], direction)
            rings = []
            for ring in self.profiles.get(port['profile'], []):
                transverse = TRANSVERSE[port['direction']]
                sampled = []
                for width, z in ring:
                    native_point = [port['position'][0] + transverse[0] * width,
                                    port['position'][1] + transverse[1] * width,
                                    port['position'][2] + z]
                    logical = project(native_point, direction, self.camera[asset_id])
                    sampled.append([ground[i] + logical[i] for i in range(2)])
                rings.append(sampled)
            result.append(dict(port, point=point, projectedNormal=normal, rings=rings))
        return result

    def compatible(self, first, second):
        if first['profile'] != second['profile']:
            return False, 'profile mismatch'
        if distance(first['point'], second['point']) > self.tolerance:
            return False, 'projected endpoints differ'
        if distance(first['projectedNormal'], [-v for v in second['projectedNormal']]) > 1e-6:
            return False, 'port normals do not oppose'
        if first.get('role') and first.get('role') == second.get('role'):
            return False, 'both belt ports have the same role'
        if len(first['rings']) != len(second['rings']):
            return False, 'endpoint ring counts differ'
        for a_ring, b_ring in zip(first['rings'], second['rings']):
            # Hausdorff comparison ignores ring winding but not asymmetric lips.
            if any(min(distance(a, b) for b in b_ring) > self.tolerance for a in a_ring) or any(min(distance(a, b) for a in a_ring) > self.tolerance for b in b_ring):
                return False, 'authored endpoint cross-section is flipped or different'
        return True, None

    def validate_registration(self, asset_id):
        asset = self.by_id[asset_id]
        ports = raw_ports(asset_id, self.load(asset_id))
        if asset_id.startswith('belt-'):
            expected = {p['name']: p['direction'] for p in ports}
            if asset.get('portDefinition') != expected:
                self.error(asset_id, 'portDefinition does not match native flow: expected ' + str(expected))
        else:
            expected = {p['name']: p['profile'] for p in ports}
            if asset.get('portProfiles') != expected:
                self.error(asset_id, 'portProfiles do not match native profiles: expected ' + str(expected))
        for direction in DIRECTIONS:
            published = asset.get('ports', {}).get(direction, {})
            for port in ports:
                actual = published.get(port['name'])
                expected = project(port['position'], direction, self.camera[asset_id])
                if not isinstance(actual, list) or distance(actual[:2], expected) > self.tolerance:
                    self.error(asset_id, 'Published projected port is missing/wrong: ' + direction + '/' + port['name'])

    def validate_port_scene(self, asset_id, scene):
        placements = scene.get('placements', [])
        all_ports = [self.ports_at(p) if p['object'] in self.by_id else [] for p in placements]
        failures = []
        for index, target in enumerate(placements):
            if target['object'] != asset_id:
                continue
            misses = []
            for port in all_ports[index]:
                neighbors = [(j, other) for j, candidates in enumerate(all_ports) if j != index for other in candidates]
                if not any(self.compatible(port, other)[0] for _, other in neighbors):
                    nearby = [(placements[j]['object'], self.compatible(port, other)[1]) for j, other in neighbors if distance(port['point'], other['point']) <= self.tolerance]
                    misses.append({'port': port['name'], 'point': port['point'], 'nearbyRejected': nearby})
            if not misses:
                return True, None
            failures.append({'placement': index, 'missing': misses})
        return False, failures or 'Reviewed object is absent'

    def validate_belt_motion(self, asset_id, scenes):
        found = False
        for scene in scenes:
            for placement in scene.get('placements', []):
                motion = placement.get('motion')
                if not placement['object'].startswith('dish-') or not motion:
                    continue
                found = True
                path = motion.get('path', [])
                if len(path) < 2 or motion.get('duration', 0) <= 0:
                    self.error(asset_id, 'Conveyed dish lacks a valid staged motion path', scene['name'])
                    continue
                belt_placements = [p for p in scene['placements'] if p['object'].startswith('belt-')]
                deck_height = self.load(asset_id)['flow']['deckHeight']
                expected_offset = [0, -128 * deck_height]
                if distance(placement.get('offset', [0, 0]), expected_offset) > self.tolerance:
                    self.error(asset_id, 'Conveyed dish is not raised to the native deck socket', scene['name'])
                # Every sampled centerline point must lie on one actual deck.
                for point in path:
                    on_deck = False
                    for belt in belt_placements:
                        info = self.load(belt['object'])
                        flow = info['flow']
                        local = [point[0] - belt['x'], point[1] - belt['y']]
                        # S preserves each module's authored suffix orientation.
                        if belt.get('direction', 'S') != 'S':
                            continue
                        if belt['object'].startswith('belt-corner-'):
                            vi, vo = SCREEN_VECTORS[flow['incoming']], SCREEN_VECTORS[flow['outgoing']]
                            center = [sum(v) * .5 for v in zip(vi, vo)]
                            delta = [local[i] - center[i] for i in range(2)]
                            # Correct quarter, radius .5; tolerance allows sampled endpoints.
                            within_quarter = all(abs(center[i]) < 1e-9 or delta[i] * center[i] <= 1e-8 for i in range(2))
                            on_deck = within_quarter and abs(math.hypot(*delta) - .5) <= 1e-5
                        else:
                            side = flow.get('outgoing') or {'N':'S', 'E':'W', 'S':'N', 'W':'E'}[flow['incoming']]
                            axis = SCREEN_VECTORS[side]
                            on_deck = abs(local[0] * axis[1] - local[1] * axis[0]) <= 1e-5 and abs(local[0] * axis[0] + local[1] * axis[1]) <= .50001
                        if on_deck:
                            break
                    if not on_deck:
                        self.error(asset_id, 'Dish path leaves the authored deck centerline at ' + str(point), scene['name'])
                        break
                if asset_id.startswith('belt-corner-'):
                    targets = [p for p in belt_placements if p['object'] == asset_id]
                    if not targets or len(path) < 10:
                        self.error(asset_id, 'Corner demonstration lacks a sampled curved path', scene['name'])
        if not found:
            self.error(asset_id, 'No connected scene conveys an independent dish')

    def run(self):
        port_ids = []
        for asset_id in self.by_id:
            if raw_ports(asset_id, self.load(asset_id)):
                port_ids.append(asset_id)
        if len(port_ids) != 42:
            self.error('library', 'Expected exactly 42 port modules, found ' + str(len(port_ids)))
        for asset_id in port_ids:
            self.validate_registration(asset_id)
            expected_kind = 'directed-belt' if asset_id.startswith('belt-') else 'profile-join'
            scenes = [scene for scene in self.by_id[asset_id].get('interactions', []) if scene.get('connectionReview', {}).get('kind') == expected_kind and scene['connectionReview'].get('object') == asset_id]
            if not scenes:
                self.error(asset_id, 'No tagged connected interaction fixture')
            for scene in scenes:
                passed, reason = self.validate_port_scene(asset_id, scene)
                if not passed:
                    self.error(asset_id, 'Reviewed ports are not all genuinely joined: ' + json.dumps(reason), scene['name'])
            if asset_id.startswith('belt-'):
                self.validate_belt_motion(asset_id, scenes)
            self.checked.append(asset_id)
        for asset_id in ('floor-cream', 'floor-blue-wave', 'floor-checker', 'floor-underwater'):
            scenes = [scene for scene in self.by_id[asset_id].get('interactions', []) if scene.get('connectionReview', {}).get('kind') == 'floor-patch' and scene['connectionReview'].get('object') == asset_id]
            expected = {(x, y, 'S') for x in range(3) for y in range(3)}
            if not any({(p['x'], p['y'], p.get('direction', 'S')) for p in scene.get('placements', []) if p['object'] == asset_id} == expected for scene in scenes):
                self.error(asset_id, 'No complete contiguous 3x3 floor patch')
        dock_roots = {'dock-floor': (1.5, 1.5, 0), 'dock-entry': (1.5, 3., 0), 'workshop-hut': (2.28, 1.15, .23), 'submarine-yellow': (.8, 1.92, .23), 'dock-cover': (1.5, 1.5, .23)}
        for asset_id in ('dock-floor', 'dock-entry', 'workshop-hut', 'dock-cover'):
            scenes = [scene for scene in self.by_id[asset_id].get('interactions', []) if scene.get('connectionReview', {}).get('kind') == 'dock-assembly' and scene['connectionReview'].get('object') == asset_id]
            if not scenes:
                self.error(asset_id, 'No tagged dock assembly')
            for scene in scenes:
                required = set(dock_roots) - ({'dock-cover'} if asset_id != 'dock-cover' else set())
                seen = set()
                for p in scene.get('placements', []):
                    if p['object'] not in required:
                        continue
                    seen.add(p['object'])
                    x, y, z = dock_roots[p['object']]
                    expected = [128 * x, 128 * (y - z)]
                    if p.get('direction', 'S') != 'S' or distance(placement_root(p, self.by_id[p['object']]), expected) > self.tolerance:
                        self.error(asset_id, 'Dock support/composition offset differs from native record for ' + p['object'], scene['name'])
                if seen != required:
                    self.error(asset_id, 'Dock assembly lacks: ' + ', '.join(sorted(required - seen)), scene['name'])
        return {'ok': not self.errors, 'portModules': len(port_ids), 'floorPatches': 4, 'dockAssemblies': 4, 'errors': self.errors}


def support_footprint_report(path):
    spec = importlib.util.spec_from_file_location('s33_support_read_only', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    recipe = module.geometry()
    result = []
    for leg in recipe['legs']:
        angle = leg['rotationZ']
        c, s = math.cos(angle), math.sin(angle)
        cx, cy = leg['center'][:2]
        sx, sy = leg['size'][:2]
        vertices = [(cx + c*x - s*y - .5, cy + s*x + c*y - .5) for x,y in [(-sx/2,-sy/2),(sx/2,-sy/2),(sx/2,sy/2),(-sx/2,sy/2)]]
        def edge_distance(a, b):
            dx, dy = b[0]-a[0], b[1]-a[1]
            t = max(0, min(1, -(a[0]*dx+a[1]*dy)/(dx*dx+dy*dy)))
            return math.hypot(a[0]+t*dx, a[1]+t*dy)
        minimum = min(edge_distance(vertices[i], vertices[(i+1)%4]) for i in range(4))
        maximum = max(math.hypot(*point) for point in vertices)
        angles = [math.degrees(math.atan2(y,x) % math.tau) for x,y in vertices]
        within_angle = min(angles) >= 180 and max(angles) <= 270
        result.append({'part': leg['part'], 'radiusRange': [minimum, maximum], 'angleRangeDegrees': [min(angles), max(angles)], 'insideDeckAnnulus': within_angle and minimum >= .15 and maximum <= .85, 'insideSupportSlab': within_angle and minimum >= .13 and maximum <= .87})
    return {'ok': all(x['insideDeckAnnulus'] and x['insideSupportSlab'] for x in result), 'legs': result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library', type=Path, default=DEFAULT_LIBRARY)
    parser.add_argument('--native-source-root', type=Path, help='Optional authoritative export/source; otherwise read published source records')
    parser.add_argument('--world-source', type=Path, default=BASE / 'world_components.py')
    parser.add_argument('--revision-source', type=Path, help='Native V2 recipe; defaults to catalog_art_revision.py beside world source')
    parser.add_argument('--support-source', type=Path, default=BASE / 'catalog_corner_supports.py')
    parser.add_argument('--plan', type=Path, default=BASE / 'coverage-plan.json')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    manifest = read_json(args.library)
    audit = Audit(manifest, args.native_source_root, cross_sections(args.world_source, args.revision_source))
    audit.manifest_root = args.library.parent
    expected = {item['id'] for item in read_json(args.plan)['objects']}
    if set(audit.by_id) != expected:
        audit.error('library', '117-ID inventory mismatch: missing=' + str(sorted(expected-set(audit.by_id))) + ', extra=' + str(sorted(set(audit.by_id)-expected)))
    report = audit.run()
    report['supportFootprints'] = support_footprint_report(args.support_source)
    report['ok'] = report['ok'] and report['supportFootprints']['ok']
    if args.report:
        args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
