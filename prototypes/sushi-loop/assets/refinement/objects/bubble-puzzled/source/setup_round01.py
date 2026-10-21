"""One-time immutable resource snapshot. Requires repository source; not a replay dependency."""
from pathlib import Path
import json,shutil,copy,hashlib
P=Path(__file__).resolve().parent.parent;S=P/'source/round01';R=S/'resources';ROOT=P.parents[3]
def cp(src,dst):dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
S.mkdir(parents=True,exist_ok=True)
for name in ['original.png','target.png','imagegen-prompt.txt','approved-feedback-family-heart.png','approved-feedback-family-smile.png','catalog-object.json']:
 cp(P/'inputs'/name,R/name)
cp(P/'brief.json',R/'frozen-brief.json');cp(P/'reviews/proposedcriteria.json',R/'frozen-criteria.json')
for p in (P/'inputs/original-2d-pipeline').iterdir():
 if p.is_file():cp(p,R/'original-2d-pipeline'/p.name)
production=P.parents[2]/'production'
cp(production/'source/2d/generated/bubble-puzzled.png',R/'original-source/bubble-puzzled.png')
for p in (production/'sprites/bubble-puzzled').glob('*.png'):cp(p,R/'original-atlases'/p.name)
style=P.parents[1]/'style/warm-soft-reference.png';cp(style,R/'warm-soft-reference.png')
godot=ROOT/'godot';assert godot.exists(),godot
ctx={'objects':{}}
manifest=json.loads((godot/'assets/catalog/manifest.json').read_text())
for ident,clips in [('customer-rosa',['stand','seated-wait']),('stool-wood',['static'])]:
 obj=copy.deepcopy(manifest['objects'][ident]);obj['clips']={k:v for k,v in obj['clips'].items() if k in clips}
 for clip in obj['clips'].values():
  clip['directions']={'S':clip['directions']['S']}
  for entry in clip['directions'].values():
   src=godot/'assets/catalog'/entry['image'];resource='context/catalog/'+entry['image'];cp(src,R/resource);entry['resource']=resource
 ctx['objects'][ident]=obj
(R/'context/manifest.json').write_text(json.dumps(ctx,indent=2)+'\n')
for name in ['restaurant_view.gd','art_book.gd','typography.gd']:cp(godot/'scripts'/name,R/'context/runtime-scripts'/name)
# Original publisher can be imported against this unchanged generated source.
cp(R/'original-source/bubble-puzzled.png',R/'original-2d-pipeline/generated/bubble-puzzled.png')
resources=[{'path':p.relative_to(P).as_posix(),'sha256':sha(p)}for p in sorted(R.rglob('*'))if p.is_file()]
provenance={'asset':'bubble-puzzled','representation':'existing generated raster native2D plus deterministic publisher','frozenBriefSHA256':sha(R/'frozen-brief.json'),'frozenCriteriaSHA256':sha(R/'frozen-criteria.json'),'generation':json.loads((R/'frozen-brief.json').read_text())['target']['generation'],'rawTarget':{'path':'source/round01/resources/target.png','sha256':sha(R/'target.png')},'operations':'Declared original publisher alpha>8 support bounds rectangle crop once; no alpha threshold applied to pixels, uniform 82logical width normalization, original animation and packing. No painting/warping or per-frame fit.','resources':resources}
(S/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
print('snapshot',len(resources),'files')
