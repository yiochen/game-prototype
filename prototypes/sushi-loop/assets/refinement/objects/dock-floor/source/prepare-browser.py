from pathlib import Path
import json,hashlib,shutil
from PIL import Image
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent;PROTO=OBJ.parents[3];A=OBJ.parents[2]/'production';R=HERE/'resources/browser';R.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
lib=json.loads((A/'library.json').read_text());by={o['id']:o for o in lib['objects']};report={'librarySHA256':sha(A/'library.json'),'sources':{},'objects':[]}
for aid in ['dock-floor','dock-entry','workshop-hut','submarine-yellow','dock-cover','customer-rosa']:
 o=by[aid];q={k:o[k] for k in ['id','frameSize','root','sourceScale','footprint','kind','layer','rootCell','directionRootCells','directionFootprints'] if k in o};q['clips']=[]
 clips={'dock-floor':['static'],'dock-entry':['static'],'workshop-hut':['static'],'submarine-yellow':['dock-ready'],'dock-cover':['covered','uncover'],'customer-rosa':['stand','walk']}[aid]
 for cname in clips:
  c=next(c for c in o['clips'] if c['id']==cname);dct={k:c[k] for k in ['id','frames','fps','loop']};dct['directions']={}
  for d,e in c['directions'].items():
   src=A/e['image'];dest=R/(aid+'-'+cname+'-'+d+'.png');shutil.copyfile(src,dest);report['sources'][str(dest.relative_to(OBJ))]={'sha256':sha(dest),'productionPath':str(src.relative_to(A)),'productionSHA256':sha(src)};dct['directions'][d]={**e,'image':dest.name}
  q['clips'].append(dct)
 # Include actual camera record to keep human support projection provenance clear.
 src=A/o['source']['camera'];dest=R/(aid+'-source-camera.json');shutil.copyfile(src,dest);report['sources'][str(dest.relative_to(OBJ))]={'sha256':sha(dest),'productionPath':str(src.relative_to(A))}
 report['objects'].append(q)
for d in ['N','E','S','W']:
 src=OBJ.parent/'dock-entry/candidates/round-05'/('static-'+d+'.png');dest=R/('paired-entry-'+d+'.png');shutil.copyfile(src,dest);report['sources'][str(dest.relative_to(OBJ))]={'sha256':sha(dest),'sourceObject':'dock-entry','sourceRound':'round-05','sourcePath':str(src)}
for name in ['sprite-layout.js','world-sprite-raster.js','object-review.jsx','object-review.css']:
 src=PROTO/'wireframe'/name;dest=R/name;shutil.copyfile(src,dest);report['sources'][str(dest.relative_to(OBJ))]={'sha256':sha(dest),'sourcePath':str(src)}
(R/'inputs.json').write_text(json.dumps(report,indent=2))
print('BROWSER_INPUT_BYTES',sum(p.stat().st_size for p in R.rglob('*') if p.is_file()))
