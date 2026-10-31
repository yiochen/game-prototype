"""Copy the approved native cover clip and extract its exact completed pose.

Run with the workspace Python/Pillow runtime. This preserves original pixels,
camera, frame, root and timing; it never renders or resizes the approved model.
"""
from pathlib import Path
import hashlib
import json
import shutil
from PIL import Image


def prepare(project: Path) -> None:
    prototype = project.parent
    runtime = project / 'assets/expansion'
    manifest_path = runtime / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    library = json.loads((prototype / 'assets/production/library.json').read_text())
    cover = next(o for o in library['objects'] if o['id'] == 'dock-cover')
    source_clip = next(c for c in cover['clips'] if c['id'] == 'uncover')
    entry = source_clip['directions']['S'].copy()
    source = prototype / 'assets/production' / entry['image']
    image = 'sprites/dock-cover-uncover-S.png'
    shutil.copy2(source, runtime / image)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    entry.update(image=image, frames=source_clip['frames'], frameSize=cover['frameSize'],
                 root=cover['root'], sourceScale=cover['sourceScale'], sha256=digest)
    clips = manifest['objects']['dock-cover']['clips']
    clips['uncover'] = {'frames':source_clip['frames'], 'fps':source_clip['fps'],
                        'loop':False, 'directions':{'S':entry}}
    manifest['sources'][image] = {'path':source.relative_to(prototype).as_posix(),
                                  'sha256':digest, 'registration':'dock-cover/uncover/S'}
    region = entry['rects'][-1]
    image = 'sprites/dock-cover-uncovered-S.png'
    with Image.open(source) as atlas:
        atlas.crop((region[0], region[1], region[0]+region[2], region[1]+region[3])).save(runtime / image)
    final_hash = hashlib.sha256((runtime / image).read_bytes()).hexdigest()
    clips['uncovered'] = {'frames':1, 'fps':1, 'loop':False, 'directions':{'S':{
        'image':image, 'frames':1, 'rects':[[0,0,region[2],region[3]]],
        'frameSize':cover['frameSize'], 'root':cover['root'],
        'sourceScale':cover['sourceScale'], 'sha256':final_hash}}}
    manifest['sources'][image] = {'path':source.relative_to(prototype).as_posix(),
                                  'source_sha256':digest, 'sha256':final_hash,
                                  'crop_xywh':region, 'registration':'dock-cover/uncovered/S'}
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')


if __name__ == '__main__':
    prepare(Path(__file__).resolve().parents[1])
