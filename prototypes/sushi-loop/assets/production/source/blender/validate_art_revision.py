"""No-render native geometry smoke check for the approved issue33 prop revision.

Run in an isolated Blender process, for example:
  Blender --background --factory-startup --python validate_art_revision.py -- \
    --output /absolute/review/native-prop-geometry.json

The check builds native geometry, measures complete idle supports, executes all
pose callbacks, checks wall end sections and verifies that revision helpers do
not edit conveyor decks or their authored UVs. It does not claim visual approval.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import bpy

BASE = Path(__file__).parent


def _module(name, filename):
    spec = importlib.util.spec_from_file_location(name, str(BASE / filename))
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def _deck_hash(obj):
    return hashlib.sha256(json.dumps({
        'vertices': [list(vertex.co) for vertex in obj.data.vertices],
        'uv': [[list(value.uv) for value in layer.data] for layer in obj.data.uv_layers],
    }, sort_keys=True).encode()).hexdigest()


def _bounds(asset):
    bpy.context.view_layer.update()
    points = [obj.matrix_world @ vertex.co
              for obj in asset['collection'].all_objects
              if obj.type == 'MESH' and not obj.hide_render
              for vertex in obj.data.vertices]
    return [[min(p[axis] for p in points), max(p[axis] for p in points)] for axis in range(3)]


def _section(asset, side):
    """Return normalized wall section coordinates at an exact native port."""
    axis, plane = {'W': (0, -.5), 'E': (0, .5), 'N': (1, .5), 'S': (1, -.5)}[side]
    result = {}
    for name, obj in asset['parts'].items():
        if name not in ('wall_panel', 'wood_cap', 'blue_coping') and not name.startswith('horizontal_board_'):
            continue
        points = [obj.matrix_basis @ vertex.co for vertex in obj.data.vertices]
        result[name] = sorted({(round(p[1 - axis], 6), round(p.z, 6))
                               for p in points if abs(p[axis] - plane) < 1e-6})
    return result


def validate(output):
    revision = _module('s33_revision_validation', 'catalog_art_revision.py')
    library = _module('s33_revision_validation_library', 'production_library.py')
    manifest = json.loads((BASE.parents[1] / 'library.json').read_text())
    belts = sorted(obj['id'] for obj in manifest['objects'] if obj['id'].startswith('belt-'))
    ids = list(revision.REPLACEMENT_IDS) + belts
    report = {'revision': revision.REVISION, 'blenderVersion': bpy.app.version_string,
              'assets': {}, 'errors': [], 'visualApproval': 'pending-user-review'}
    sections = {}
    for aid in ids:
        asset = None
        try:
            asset = library.build(aid)
            deck = next((obj for name, obj in asset['parts'].items()
                         if name in ('connected_turn_deck', 'connected_straight_deck')), None)
            deck_hash = _deck_hash(deck) if deck else None
            asset = revision.augment(asset, aid)
            asset = revision.repair_existing_rollout(asset, aid)
            bounds = _bounds(asset)
            size = [upper - lower for lower, upper in bounds]
            entry = {'bounds': bounds, 'size': size, 'footprint': asset['footprint'],
                     'directions': asset['directions'], 'objects': len(asset['collection'].all_objects),
                     'clips': list(asset['clips']), 'ports': asset.get('ports', [])}
            report['assets'][aid] = entry
            if deck:
                entry['unchangedDeckAndUVSHA256'] = deck_hash
                if _deck_hash(deck) != deck_hash:
                    report['errors'].append(aid + ': moving deck or UV changed')
            if aid in revision.SINGLE_FACING and asset['directions'] != ['S']:
                report['errors'].append(aid + ': expected single player-facing direction')
            if aid == 'chef-blackboard' and any(name.startswith(('token_', 'chalk_dash', 'board_salmon', 'board_cucumber', 'board_eel')) for name in asset['parts']):
                report['errors'].append(aid + ': baked recipe/chalk content present')
            for axis in (0, 1):
                # Tiny bevel/strata overhangs are declared native detail; the
                # primary body must remain at the authored integer cell pitch.
                if size[axis] > asset['footprint'][axis] + .04:
                    report['errors'].append(aid + ': idle support overflows declared cell width/depth')
            if aid.startswith('wall-'):
                sections[aid] = {port['direction']: _section(asset, port['direction']) for port in asset.get('ports', [])}
            for clip in asset['clips']:
                for time in (0, .25, .50, .75, 1):
                    asset['pose'](clip, time)
            if deck and _deck_hash(deck) != deck_hash:
                report['errors'].append(aid + ': pose mutated moving deck geometry/UV')
        except Exception as error:
            report['errors'].append(aid + ': ' + repr(error))
        finally:
            if asset is not None:
                revision._remove_owned(asset)
    expected = sections['wall-middle']['W']
    for aid, ports in sections.items():
        for side, section in ports.items():
            if section != expected:
                report['errors'].append(aid + ': ' + side + ' wall section differs from straight module')
    report['wallSectionsMatch'] = not any('wall section' in error for error in report['errors'])
    report['passed'] = not report['errors']
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'nativePropGeometry': report['passed'], 'assets': len(report['assets']),
                      'errors': report['errors'], 'output': str(output)}))
    if report['errors']:
        raise RuntimeError('Native prop geometry validation failed')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    validate(args.output)
