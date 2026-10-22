from pathlib import Path
import shutil,json
H=Path(__file__).resolve().parent;E=H.parent;R=H/'resources';O=E/'candidates/round-01';D=O/'consumer';D.mkdir(exist_ok=True)
for n in ['15-sprite-layout.js','16-world-sprite-raster.js']:shutil.copy2(R/n,D/n)
shutil.copytree(R/'context-inputs',D/'context-inputs',dirs_exist_ok=True)
shutil.copy2(H/'consumer-01.html',D/'index.html')
lib=json.loads((R/'consumer-preparation-library.json').read_text());keep=['submarine-preparation-assembled','sub-collector-inlet','sub-hull-panels','sub-harpoon-mount','creature-eel'];objs=[o for o in lib['objects'] if o['id'] in keep];atlases=json.loads((O/'publication-audit.json').read_text())['atlases']
for o in objs:
 if o['id']=='sub-collector-inlet':
  for clip in o['clips']:
   for d in 'NESW':
    a=next(a for a in atlases if a['clip']==clip['id'] and a['direction']==d)
    clip['directions'][d]={'image':'../atlases/'+Path(a['path']).name,'columns':a['columns'],'rows':a['rows'],'atlasSize':a['size'],'rects':a['rects']}
 elif o['id']=='submarine-preparation-assembled':
  o['id']='submarine-candidate-assembled'
  for d in 'NESW':o['clips'][0]['directions'][d]['image']=f'../assembled/upgraded-dock-ready-{d}.png'
 else:
  for c in o['clips']:
   for a in c['directions'].values():a['image']=a['image'].replace('consumer-inputs/','context-inputs/')
  o['clips']=[c for c in o['clips'] if c['id'] in ('idle','swim')]
(D/'library.json').write_text(json.dumps({'objects':objs},indent=2)+'\n')
