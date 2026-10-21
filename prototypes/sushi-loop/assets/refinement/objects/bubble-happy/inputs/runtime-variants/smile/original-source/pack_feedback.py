#!/usr/bin/env python3
"""Pack an isolated ImageGen smiling balloon using the approved fixed 2D contract."""
from pathlib import Path
import hashlib
import json
import math
from PIL import Image

HERE = Path(__file__).resolve().parent
PROTOTYPE = HERE.parents[4]
DESTINATION = PROTOTYPE / 'godot/assets/feedback-variants'
CLIPS = ['happy-smile-appear', 'happy-smile-idle', 'happy-smile-fade', 'happy-smile-transition']
FRAME = [192, 320]
ROOT = [96, 248]
SCALE = 2


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n')


def make_frame(cutout, clip, index):
    # One source-only alpha rectangle is selected before animation. Every pose
    # retains the complete same384x640 canvas and192/496 source-pixel root.
    image = cutout.copy()
    phase = index / 12 * math.tau
    opacity = 1.0
    scale = 1.0
    if clip.endswith('-appear'):
        scale = 0.5 + 0.5 * math.sin((index + 1) / 12 * math.pi / 2)
        opacity = (index + 1) / 12
    elif clip.endswith('-fade'):
        opacity = 1.0 - index / 12
    elif clip.endswith('-transition'):
        scale = 1.0 + 0.12 * math.sin(phase)
    if scale != 1.0:
        image = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    if opacity < 1.0:
        image.putalpha(image.getchannel('A').point(lambda alpha: round(alpha * opacity)))
    center = [ROOT[0] * SCALE, (ROOT[1] - 52 - 3 * math.sin(phase)) * SCALE]
    canvas = Image.new('RGBA', (FRAME[0] * SCALE, FRAME[1] * SCALE))
    canvas.alpha_composite(image, (round(center[0] - image.width / 2), round(center[1] - image.height / 2)))
    return canvas


def main():
    generation = json.loads((HERE / 'imagegen.json').read_text())
    path = HERE / generation['output']
    assert sha(path) == generation['output_sha256']
    reference = PROTOTYPE / 'assets/production/source/2d/generated/bubble-happy.png'
    assert sha(reference) == generation['reference_sha256']
    original = Image.open(path).convert('RGBA')
    bounds = original.getchannel('A').point(lambda alpha: 255 if alpha > 8 else 0).getbbox()
    assert bounds and original.getchannel('A').getextrema() == (0, 255)
    cutout = original.crop(bounds)
    cutout = cutout.resize((82 * SCALE, round(cutout.height / cutout.width * 82 * SCALE)), Image.Resampling.LANCZOS)
    clips, atlases = {}, {}
    for clip in CLIPS:
        atlas = Image.new('RGBA', (2304, 1280))
        rects, pixels = [], []
        for index in range(12):
            frame = make_frame(cutout, clip, index)
            pixels.append(hashlib.sha256(frame.tobytes()).hexdigest())
            x, y = index % 6 * 384, index // 6 * 640
            atlas.alpha_composite(frame, (x, y))
            rects.append([x, y, 384, 640])
        assert len(set(pixels)) >= 6, clip
        relative = f'sprites/bubble-happy/{clip}-S.png'
        target = DESTINATION / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        atlas.save(target, compress_level=9)
        atlases[relative] = {'sha256': sha(target), 'bytes': target.stat().st_size, 'width': 2304, 'height': 1280, 'framePixels': pixels}
        clips[clip] = {'id': clip, 'frames': 12, 'fps': 12, 'loop': clip.endswith('-idle'), 'frameOrder': list(range(12)), 'directions': {'S': {'image': relative, 'columns': 6, 'rows': 2, 'atlasSize': [2304, 1280], 'rects': rects, 'sha256': sha(target)}}}
    publication = {'version': 1, 'pipeline': 'builtin ImageGen edit; fixed-frame 2D animation', 'source': {'file': path.name, 'sha256': sha(path), 'dimensions': list(original.size), 'alphaRange': list(original.getchannel('A').getextrema()), 'fixedAlphaRectangle': list(bounds)}, 'registration': {'frameSize': FRAME, 'root': ROOT, 'sourceScale': SCALE, 'cellSize': 128, 'frames': 12, 'fps': 12}, 'operation': 'One fixed source cutout at82logical pixels wide; authored pulse/appear/fade and3px bob on complete192x320 logical canvas. No per-pose fitting, no painted substitute, no3D geometry, no food baked into reaction.', 'atlases': atlases}
    write(HERE / 'publication.json', publication)
    object_record = {'frameSize': FRAME, 'root': ROOT, 'sourceScale': SCALE, 'projection': 'screen-space-2d', 'clips': clips}
    sources = [path, HERE / 'imagegen.json', HERE / 'pack_feedback.py', HERE / 'publication.json']
    manifest = {'version': 1, 'baseLibrarySha256': sha(PROTOTYPE / 'assets/production/library.json'), 'sourceFiles': {str(path.relative_to(PROTOTYPE)): sha(path) for path in sources}, 'objects': {'bubble-happy': object_record}}
    write(DESTINATION / 'manifest.json', manifest)
    print(f'Packed{len(CLIPS) * 12} smiling-face frames into{len(CLIPS)} fixed atlases; {sum(entry["bytes"] for entry in atlases.values()):,} bytes')


if __name__ == '__main__':
    main()
