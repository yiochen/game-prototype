import pathlib,shutil,json,hashlib
out=pathlib.Path(__file__).resolve().parent
root=out.parents[7]
# Find explicit workspace without depending on cwd.
root=next(p for p in out.parents if (p/'prototypes.json').is_file())
ex=out.parents[1];res=out/'resources';res.mkdir(exist_ok=True)
records=[]
def copy(src,dst):
 src=pathlib.Path(src);dst=res/dst;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
 records.append({'source':str(src),'snapshot':str(dst.relative_to(out)),'sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'bytes':dst.stat().st_size})
for name in ['brief.json','prompts/judge.txt','inputs/catalog-object.json','inputs/snapshot.json','inputs/source-camera.json','inputs/source-rig.json','inputs/source-assetRecord.json','inputs/original.png','inputs/target.png','inputs/family-concept.png','inputs/imagegen-prompt.txt']:
 copy(ex/name,'experiment/'+name)
for p in (ex/'inputs/frozen-main-v1').iterdir():
 if p.is_file():copy(p,'frozen-main-v1/'+p.name)
copy(root/'AGENTS.md','instructions/root-AGENTS.md');copy(root/'prototypes/sushi-loop/AGENTS.md','instructions/sushi-loop-AGENTS.md')
copy('/Users/yiouchen/.codex/skills/refine-3d-model/SKILL.md','instructions/refine-3d-model-SKILL.md')
copy(root/'prototypes/sushi-loop/assets/refinement/style/warm-soft-reference.png','style/warm-soft-reference.png')
copy(root/'prototypes/sushi-loop/assets/refinement/style/modeling-policy.json','style/modeling-policy.json')
production=root/'prototypes/sushi-loop/assets/production'
copy(production/'source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend','source-library.blend')
for name in ['capture_runtime.py','native_actions.py','catalog_style.py','catalog_faceted.py','capture_worker.py','publish_captures.py']:
 copy(production/'source/blender'/name,'blender/'+name)
copy(production/'source/blender/revisions/46d7e4eeabce858f/prop_builders.py','blender/original-prop_builders.py')
for name in ['sprite-layout.js','world-sprite-raster.js']:
 copy(root/'prototypes/sushi-loop/wireframe'/name,'consumer/'+name)
copy(production/'library.json','consumer/library.json')
lib=json.loads((production/'library.json').read_text());objects=lib['objects']
selected=[]
for aid,clips in [('sub-hull-panels',['idle','active']),('creature-eel',['swim']),('submarine-yellow',['upgraded-dock-ready'])]:
 ob=next(o for o in objects if o['id']==aid);selected.append(ob)
 for clip in ob['clips']:
  if clip['id'] not in clips:continue
  for d,entry in clip['directions'].items():
   copy(production/entry['image'],'consumer/'+entry['image'])
(res/'consumer/selected-objects.json').write_text(json.dumps(selected,indent=2))
(out/'input-snapshot-manifest.json').write_text(json.dumps({'scope':'Exact mutable inputs read or used by this preparation; evidence scripts bind this closure','files':records},indent=2))
print('snapshots',len(records),'bytes',sum(r['bytes'] for r in records))
