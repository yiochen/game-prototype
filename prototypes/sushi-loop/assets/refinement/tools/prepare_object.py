"""Prepare immutable per-object source/reference inputs for fresh editor/judge agents."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
from PIL import Image

RUN = Path(__file__).resolve().parents[1]
PRODUCTION = RUN.parent/'production'

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('asset')
    parser.add_argument('--target',required=True)
    parser.add_argument('--prompt',help='Exact submitted ImageGen prompt; copy with target provenance')
    parser.add_argument('--family-concept',help='Additional family style reference supplied to ImageGen')
    parser.add_argument('--family-settings',help='Object-relative required native family settings path; may be supplied later')
    args=parser.parse_args()
    library=json.loads((PRODUCTION/'library.json').read_text())
    original=next(o for o in library['objects'] if o['id']==args.asset)
    folder=RUN/'objects'/args.asset
    if (folder/'brief.json').exists():raise SystemExit('Object brief already exists; do not overwrite reviewed inputs')
    for name in ['inputs','prompts','source','candidates','reviews','final']:(folder/name).mkdir(parents=True,exist_ok=True)
    source=original['source']
    project=PRODUCTION/source['blend'] if source.get('blend') else PRODUCTION/source['artwork'] if source.get('artwork') else PRODUCTION/source['godot']
    backup=RUN/'backups'/f'{digest(project)[:16]}-{project.name}'
    if not backup.exists():shutil.copy2(project,backup)
    assert digest(project)==digest(backup)
    for role in ['judge','editor']:shutil.copy2(RUN/'prompts'/f'{role}-prompt.txt',folder/'prompts'/f'{role}.txt')
    primary=next((c for c in original['clips']if c['id']=='static'),next((c for c in original['clips']if c['id']=='idle'),original['clips'][0]))
    facing='S' if 'S' in primary['directions'] else next(iter(primary['directions']))
    entry=primary['directions'][facing]
    x,y,w,h=entry['rects'][0]
    Image.open(PRODUCTION/entry['image']).convert('RGBA').crop((x,y,x+w,y+h)).save(folder/'inputs/original.png')
    shutil.copy2(Path(args.target).expanduser().resolve(),folder/'inputs/target.png')
    references=[{'role':'native-edit-source','path':'inputs/original.png','sha256':digest(folder/'inputs/original.png')}]
    style=RUN/'style/warm-soft-reference.png'
    if style.exists():references.append({'role':'style-only','path':os.path.relpath(style,folder),'sha256':digest(style)})
    if args.family_concept:
        shutil.copy2(Path(args.family_concept).expanduser().resolve(),folder/'inputs/family-concept.png')
        references.append({'role':'family-style-only','path':'inputs/family-concept.png','sha256':digest(folder/'inputs/family-concept.png')})
    record={k:v for k,v in original.items()if k!='source'}
    record['source']={k:v for k,v in source.items()if k not in ['hashes','nativeScripts','rawFrames','guides']}
    (folder/'inputs/catalog-object.json').write_text(json.dumps(record,indent=2)+'\n')
    for key in ['camera','assetRecord','rig']:
        if source.get(key) and (PRODUCTION/source[key]).exists():shutil.copy2(PRODUCTION/source[key],folder/'inputs'/f'source-{key}.json')
    views=list(primary['directions'])
    previews=['four-view-sheet','repeated']
    for clip in original['clips']:
        if clip.get('frames',1)>1:previews.extend(f'{clip["id"]}-{direction}'for direction in clip['directions'])
    brief={
        'asset':args.asset,'style':(RUN/'style/brief.txt').read_text().strip(),
        'source':{'project':os.path.relpath(project,folder),'backup':os.path.relpath(backup,folder),'projectSHA256':digest(project),'backupSHA256':digest(backup),'snapshot':'inputs/original.png','scene':'Inspect the named asset collection; do not use an unrelated active scene'},
        'target':{'image':'inputs/target.png','sha256':digest(folder/'inputs/target.png'),'provenance':'provided-target','references':references},
        'agentPrompts':{'judge':'prompts/judge.txt','editor':'prompts/editor.txt'},
        'capture':{'frame':[w,h],'views':views,'previews':previews,'logicalFrame':original['frameSize'],'logicalRoot':original['root'],'sourceScale':original.get('sourceScale',2),'cellSize':library['cellSize'],'fps':12,'projection':original['projection']},
        'constraints':{'preserve':['Every logical frame/root/sourceScale and per-clip/direction override','Original footprint, height/proportions, sockets, ports, rigs and projection','Every registered clip, facing, frame count and fps/loop behavior','Lighting without preferred horizontal direction for rotatable world objects; no directional ground cast shadow','Actual independent geometry views and native animation; no raster card or per-view image fitting/recolor'],'catalogContract':'inputs/catalog-object.json','pipeline':'native-3d'if source.get('blend')else 'existing-2d'},
        'qualityCriteria':{},
        'delivery':{'scope':'Refine this object only. Root coordinator promotes approved atlases, sources and metadata to production, publishes the PR preview, and finally updates Godot.','requiredClips':[{k:v for k,v in c.items()if k!='directions'}for c in original['clips']],'notes':'Write source/round-NN.blend or the actual native 2D source as appropriate; full native captures, original-layout atlases, previews, validation and delivery.json. Do not label 2D artwork as a Blender model.'}
    }
    policy_path=RUN/'style/modeling-policy.json'
    if policy_path.exists():
        policy=json.loads(policy_path.read_text())
        brief['modelingPolicy']=policy
        brief['constraints']['preserve']=policy['locked']
        brief['constraints']['designFreedom']=policy['allowed']
        brief['target']['interpretation']=policy['judging']
        shutil.copy2(RUN/'prompts/imagegen-target.txt',folder/'prompts/imagegen-target.txt')
    if args.prompt:
        shutil.copy2(Path(args.prompt).expanduser().resolve(),folder/'inputs/imagegen-prompt.txt')
        brief['target'].update(provenance='imagegen-builtin',prompt='inputs/imagegen-prompt.txt')
    if args.family_settings:
        brief['technicalResources']={'family-settings':args.family_settings}
    (folder/'brief.json').write_text(json.dumps(brief,indent=2)+'\n')
    print(f'Prepared {args.asset}: {len(views)} hero views, {len(previews)} previews; original project backup verified.')

if __name__=='__main__':main()
