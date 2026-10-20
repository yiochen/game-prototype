"""Pack the complete native RGBA render canvases; no fitting or raster edits.

Run with a Python environment containing Pillow. The output paths are resolved
from this script, so neither a local Blender install nor a working directory is
needed for packing. Blender modeling and rendering use capture_goods.py via MCP.
"""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw

SOURCE = Path(__file__).resolve().parents[1]
PROTOTYPE = SOURCE.parents[3]
OUTPUT = PROTOTYPE / 'godot/assets/ui/editor-goods'
SIZE = 384
PADDING = 4
CELL = SIZE + 2 * PADDING
IDS = ['belt-straight-e', 'stool-wood', 'plant-angular',
       'crate-wood', 'barrel-wood', 'floor-cream']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def pack():
    records_path = SOURCE / 'records/captures.json'
    capture = json.loads(records_path.read_text())
    assert capture['main_file_preserved'] is True
    assert capture['original_scene_restored'] is True
    assert sha(SOURCE / capture['blend']) == capture['blend_sha256']
    assert sha(SOURCE / capture['recipe']) == capture['recipe_sha256']
    assert sha(PROTOTYPE / capture['production_blend']) == capture['production_blend_sha256']
    atlas = Image.new('RGBA', (CELL * 3, CELL * 2))
    sprites = {}
    review = Image.new('RGB', (CELL * 3, (CELL + 28) * 2), '#f7ecd5')
    draw = ImageDraw.Draw(review)
    for index, art_id in enumerate(IDS):
        record = capture['sprites'][art_id]
        path = SOURCE / record['source_render']
        assert sha(path) == record['source_sha256']
        with Image.open(path) as native:
            assert native.mode == 'RGBA' and native.size == (SIZE, SIZE)
            native.load()
            bounds = native.getchannel('A').getbbox()
            assert bounds and min(bounds[:2]) > 3 and max(bounds[2:]) < SIZE - 3
            x = (index % 3) * CELL + PADDING
            y = (index // 3) * CELL + PADDING
            atlas.paste(native, (x, y))
            rx, ry = x, (index // 3) * (CELL + 28) + PADDING
            review.paste(native, (rx, ry), native)
            draw.text((rx + 12, ry + SIZE + 8), art_id, fill='#192e48')
            assert atlas.crop((x, y, x + SIZE, y + SIZE)).tobytes() == native.tobytes()
        sprite = {
            'region': [x, y, SIZE, SIZE],
            'source_render': record['source_render'],
            'source_sha256': record['source_sha256'],
            'source_collection': record['source_collection'],
            'native_collection': record['native_collection'],
            'geometry_sha256': record['geometry_sha256'],
            'camera_id': record['camera']['id'],
            'camera': record['camera'],
            'alpha_bounds': list(bounds),
        }
        if 'floor_thickness' in record:
            sprite['floor_thickness'] = record['floor_thickness']
            sprite['floor_bevel'] = record['floor_bevel']
        sprites[art_id] = sprite
    OUTPUT.mkdir(parents=True, exist_ok=True)
    target = OUTPUT / 'atlas.png'
    atlas.save(target, compress_level=9)
    review.save(SOURCE / 'records/contact-sheet.png', compress_level=9)
    manifest = {
        'schema_version': 1, 'atlas': 'atlas.png',
        'atlas_size': list(atlas.size), 'atlas_sha256': sha(target),
        'atlas_bytes': target.stat().st_size,
        'padding': PADDING, 'native_render_size': [SIZE, SIZE],
        'camera': {
            'id': 'goods-three-quarter-35',
            'projection': 'ordinary-orthographic-three-quarter',
            'elevation_degrees': 35, 'azimuth_degrees': 35,
            'pixel_aspect': [1, 1],
            'exception_scope': 'UI merchandise presentation only',
        },
        'provenance': {
            'method': 'Blender MCP native render',
            'source_root': 'assets/ui/editor/goods-v1',
            'blend': capture['blend'], 'blend_sha256': capture['blend_sha256'],
            'recipe': capture['recipe'], 'recipe_sha256': capture['recipe_sha256'],
            'packing_recipe': 'source/pack_goods.py',
            'packing_recipe_sha256': sha(__file__),
            'production_blend': capture['production_blend'],
            'production_blend_sha256': capture['production_blend_sha256'],
            'records': 'records/captures.json', 'records_sha256': sha(records_path),
            'native_renders_unresized': True,
            'world_assets_unchanged': True,
        },
        'sprites': sprites,
    }
    write(OUTPUT / 'manifest.json', manifest)
    print(json.dumps({'atlas': str(target), 'size': list(atlas.size),
                      'bytes': target.stat().st_size, 'sprites': list(sprites)}))


if __name__ == '__main__':
    pack()
