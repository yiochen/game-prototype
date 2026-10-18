"""Register queued native clusters without altering any published object record."""
import copy, hashlib, json, os
from pathlib import Path
HERE=Path('/private/tmp/sushi33-production')
REPO=Path('/Users/yiouchen/.codex/worktrees/sushi-loop-33-art-catalog/game-prototype')
SPECS=[
('restaurant-border-garden-a','Restaurant border garden A','W02',[2,4]),
('restaurant-border-garden-b','Restaurant border garden B','W02',[2,4]),
('restaurant-corner-garden-a','Restaurant corner garden A','W02',[3,3]),
('restaurant-corner-garden-b','Restaurant corner garden B','W02',[3,3]),
('underwater-reef-garden-a','Underwater reef garden A','W12',[2,4]),
('underwater-reef-garden-b','Underwater reef garden B','W12',[2,4]),
('underwater-coral-garden-a','Underwater coral garden A','W12',[3,3]),
('underwater-coral-garden-b','Underwater coral garden B','W12',[3,3]),
]
DIRECTIONS=['N','E','S','W']
def write(path,data):
    old=path.read_bytes();digest=hashlib.sha256(old).hexdigest()
    backup=HERE/'integration-history'/'queued-clusters'/digest[:16]/path.name
    backup.parent.mkdir(parents=True,exist_ok=True)
    if not backup.exists():backup.write_bytes(old)
    tmp=path.with_name(path.name+'.cluster-seed-tmp')
    tmp.write_text(json.dumps(data,indent=2)+'\n');os.replace(tmp,path)
def note(family):
    setting='restaurant' if family=='W02' else 'underwater'
    return f'Dense organic {setting} scenery authored as one reusable multi-cell native assembly. A and B are distinct component arrangements. Nonblocking decoration with no seam ports; static snapshot and twelve unique ambient samples in all four facings. Native capture determines the final frame and root; queued entries contain no generated sprite images.'
def seed(ident,name,family,footprint):
    actor='chef-lena' if family=='W02' else 'submarine-yellow'
    return {'id':ident,'name':name,'family':family,'status':'queued','kind':'prop','footprint':footprint,
      'projection':'top-down-oblique-square-grid','frameSize':[192,320],'root':[96,248],
      'sourceScale':2,'clips':[],'interactions':[],'layer':2,'blocking':False,
      'directionFootprints':{d:list(reversed(footprint)) if d in ['E','W'] else footprint[:] for d in DIRECTIONS},
      'directionRootCells':{d:[v/2 for v in (list(reversed(footprint)) if d in ['E','W'] else footprint)] for d in DIRECTIONS},
      'rootCell':[v/2 for v in footprint],
      'requirements':{'directions':DIRECTIONS[:],'states':['static','ambient'],'variants':['default'],
        'animated':True,'fps':12,'minimumUniqueFrames':6,'targetLoopFrames':12,
        'stateFrames':{'static':1,'ambient':12},'interactionObjectIds':[actor],
        'notes':note(family)},'productionStage':'Queued native Blender cluster · awaiting capture and art approval'}
for path in [HERE/'library-planned.json',REPO/'prototypes/sushi-loop/assets/production/library.json']:
    data=json.loads(path.read_text());original=copy.deepcopy(data['objects']);ids={o['id'] for o in original}
    for spec in SPECS:
        if spec[0] not in ids:data['objects'].append(seed(*spec))
    assert data['objects'][:len(original)]==original
    assert len({o['id'] for o in data['objects']})==len(data['objects'])
    write(path,data);print(path,len(data['objects']),'original records unchanged')
path=HERE/'coverage-plan.json';data=json.loads(path.read_text());original=copy.deepcopy(data['objects']);ids={o['id'] for o in original}
for ident,name,family,footprint in SPECS:
    if ident in ids:continue
    actor='chef-lena' if family=='W02' else 'submarine-yellow'
    data['objects'].append({'id':ident,'family':family,'label':name,'directions':DIRECTIONS[:],
      'states':['static','ambient'],'variants':['default'],'footprintCells':footprint,'animated':True,
      'animation':{'fps':12,'minimumUniqueFrames':6,'defaultLoopFrames':12,'excludeDuplicateClosingFrame':True},
      'review':{'isolatedFourDirections':True,'repeatedPlacement':[3,3],'interactionObjectIds':[actor],'allStatesAllDirections':True},
      'status':'planned','blocking':False,'notes':note(family)})
if not any(r.get('id')=='dense-organic-clusters-v1' for r in data.get('contractRevisions',[])):
    data.setdefault('contractRevisions',[]).append({'id':'dense-organic-clusters-v1','date':'2026-10-18',
      'objects':[s[0] for s in SPECS],'rationale':'User requested reusable dense organic restaurant and underwater garden assemblies in 2×4 and 3×3 footprints. Eight separate native arrangements, each with a static view and 12-frame ambient loop in four directions. These decorative assemblies add no seam ports, blocking rules, gameplay, or additional species.'})
assert data['objects'][:len(original)]==original
write(path,data);print(path,len(data['objects']),'original requirements unchanged')
