"""Exact alpha audit and non-retouched sprite assembly. Requires Pillow/numpy bundled runtime."""
from PIL import Image,ImageDraw
import json,hashlib,shutil
from pathlib import Path
import numpy as np
BASE=Path(__file__).resolve().parent.parent;OUT=BASE/'candidates/round-03';PD=OUT/'previews';PD.mkdir(exist_ok=True);AD=OUT/'atlases';AD.mkdir(exist_ok=True)
v=json.loads((OUT/'validation.json').read_text());directions=['N','E','S','W']
frames={d:Image.open(OUT/(d+'.png')).convert('RGBA') for d in directions}
logical={d:im.resize((192,352),Image.Resampling.LANCZOS) for d,im in frames.items()}
alpha={}
for d,im in frames.items():
 ar=np.asarray(im);a=ar[:,:,3];bbox=im.getbbox()
 edge=np.concatenate([a[0,:],a[-1,:],a[:,0],a[:,-1]])
 alpha[d]={'size':list(im.size),'mode':im.mode,'alphaBounds':list(bbox),'transparentPixels':int((a==0).sum()),'opaquePixels':int((a==255).sum()),'antialiasedPixels':int(((a>0)&(a<255)).sum()),'nontransparentBorderPixels':int((edge>0).sum()),'clipped':bool((edge>0).any()),'nativeRenderSHA256':hashlib.sha256((OUT/(d+'.png')).read_bytes()).hexdigest()}
 assert im.size==(384,704) and not alpha[d]['clipped']
# Four full-frame logical sprites share native registration, with transparent pixels composited only for QA.
sheet=Image.new('RGBA',(768,386),(238,234,220,255));dr=ImageDraw.Draw(sheet)
for i,d in enumerate(directions):
 sheet.alpha_composite(logical[d],(i*192,24));dr.text((i*192+12,8),d,fill=(35,41,49,255))
dr.text((12,372),'Actual native rotations | logical size 192 x 352 | common camera/root',fill=(35,41,49,255))
sheet.convert('RGB').save(PD/'four-view-sheet.png')
# One common fixed crop is used only to make a repeated QA preview, never for production atlases.
common=(64,240,320,600)
repeated=Image.new('RGBA',(632,610),(225,222,204,255));dr=ImageDraw.Draw(repeated)
for row in range(3):
 for col in range(4):
  d=directions[(row+col)%4];sprite=frames[d].crop(common).resize((128,180),Image.Resampling.LANCZOS)
  repeated.alpha_composite(sprite,(16+col*154,32+row*188));dr.text((20+col*154,20+row*188),d,fill=(48,57,62,255))
repeated.convert('RGB').save(PD/'repeated.png')
backgrounds=[('light',(246,242,226)),('gray',(128,128,128)),('dark',(21,29,42))]
bg=Image.new('RGBA',(768,1044),(255,255,255,255));dr=ImageDraw.Draw(bg)
for row,(label,color) in enumerate(backgrounds):
 for col,d in enumerate(directions):
  panel=Image.new('RGBA',(192,348),color+(255,));panel.alpha_composite(logical[d],(0,-24));ImageDraw.Draw(panel).text((10,10),label+' / '+d,fill=(245,245,245,255) if label=='dark' else (25,31,37,255));bg.alpha_composite(panel,(col*192,row*348))
bg.convert('RGB').save(PD/'background-readability.png')
atlases=[]
for d in directions:
 path=AD/('static-'+d+'.png');shutil.copyfile(OUT/(d+'.png'),path)
 atlases.append({'clip':'static','direction':d,'path':str(path.relative_to(BASE)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'columns':1,'rows':1,'size':[384,704],'rects':[[0,0,384,704]]})
v['alpha']=alpha
v['geometrySummary']={'meshes':len(v['geometry']),'evaluatedVertices':sum(o['evaluatedVertices'] for o in v['geometry']),'evaluatedFaces':sum(o['evaluatedFaces'] for o in v['geometry']),'boundaryEdges':sum(o['boundaryEdges'] for o in v['geometry']),'nonManifoldEdges':sum(o['nonManifoldEdges'] for o in v['geometry']),'negativeScaleObjects':[o['name'] for o in v['geometry'] if o['negativeScale']]}
v['boundsDelta']={k:[v['evaluatedBounds'][k][i]-v['sourceBounds'][k][i] for i in range(3)] for k in ('min','max')}
v['previewMethod']='RGBA composition of exact native renders; LANCZOS half-size for intended-size QA only. Atlas bytes copied verbatim. No production recoloring, retouching, fitting or painting.'
v['checks']={'frame':all(a['size']==[384,704] for a in alpha.values()),'root':all(abs(a-b)<.01 for a,b in zip(v['camera']['calibration']['root'],[192,496])),'scaleMetadata':v['camera']['captureScale']==2,'nativeRotations':len({x['rootRotationZ'] for x in v['views'].values()})==4,'alphaNoClipping':not any(a['clipped'] for a in alpha.values()),'closedEvaluatedMeshes':v['geometrySummary']['nonManifoldEdges']==0,'noExternalDependencies':v['projectReopenAudit']['externalDependencyCount']==0,'sourceBoundsPreservedWithin008':all(abs(x)<.008 for a in v['boundsDelta'].values() for x in a)}
assert all(v['checks'].values()),v['checks']
(OUT/'validation.json').write_text(json.dumps(v,indent=2)+'\n')
recipe={'asset':'barrel-wood','round':3,'commands':[{'executable':'/opt/homebrew/bin/blender','arguments':['--background','--python','source/round-03.py']},{'executable':'/opt/homebrew/bin/blender','arguments':['--background','source/round-03.blend','--python','source/audit-round-03.py']},{'executable':'/Users/yiouchen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3','arguments':['source/package-round-03.py']}],'workingDirectory':'object root','scripts':['source/round-03.py','source/audit-round-03.py','source/package-round-03.py'],'notes':'First script rebuilds actual editable 3D source and four native captures from frozen original source. Second independently reopens and audits saved project. Third copies exact atlas bytes and makes QA-only composites.'}
(BASE/'source/round-03-recipe.json').write_text(json.dumps(recipe,indent=2)+'\n')
delivery={'asset':'barrel-wood','round':3,'project':'source/round-03.blend','recipe':'source/round-03-recipe.json','validation':'candidates/round-03/validation.json','heroes':{d:'candidates/round-03/'+d+'.png' for d in directions},'rawFrames':['candidates/round-03/'+d+'.png' for d in directions],'previews':{k:'candidates/round-03/previews/'+k+'.png' for k in ['four-view-sheet','repeated','background-readability']},'atlases':atlases,'nativeRecords':{'camera':'candidates/round-03/records/camera.json','assetRecord':'candidates/round-03/records/asset.json','rig':'candidates/round-03/records/rig.json'},'proposedSourceMetadata':{'productionStage':'Native Blender · warm soft cartoon · pending independent review','sourceScale':2,'registration':{'sourceCaptureScale':2,'completeFrame':[192,352],'anchor':[96,248],'method':'authored-3d-projection','poseFitting':False},'artStyle':{'revision':'warm-soft-cartoon-barrel-v1','lighting':'centered broad overhead plus four equal cardinal fills and neutral ambient','horizontalSymmetry':4,'roughnessWood':.62,'roughnessNavy':.5,'nativeModel':True,'directionalGroundShadow':False,'plankCount':5,'staveCount':14,'hoopCount':2}},'changeNotes':['Honey wood with readable lower staves, navy hoops, symmetric soft physical lighting.','Inward thickness on original 14 stave meshes, shallow inner recess backing, gentle native bevel geometry.','Original lid perimeter and four seam positions retained as five real beveled plank solids.','Original native camera projection, dimensions, root and four static 12 fps captures retained; metadata reports actual sourceScale 2.','No external scene dependencies, source editable in Blender 5.2.2.'],'approval':'pending independent judge'}
(BASE/'delivery.json').write_text(json.dumps(delivery,indent=2)+'\n')
print(json.dumps({'delivery':'delivery.json','checks':v['checks'],'geometry':v['geometrySummary'],'boundsDelta':v['boundsDelta']},indent=2))
