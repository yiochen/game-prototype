from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np,json,shutil,hashlib
P=Path(__file__).resolve().parent.parent;R=P/'candidates/round-06';B=P/'candidates/round-05';D=P/'candidates/rgb-seam-diagnostics'
old=np.asarray(Image.open(B/'independent-assembled-raw.png').convert('RGBA'));cur=np.asarray(Image.open(R/'independent-assembled-raw.png').convert('RGBA'));nat=np.asarray(Image.open(R/'native-joined-raw.png').convert('RGBA'))
controls={}
for name,path in [('denoised-source05',B/'wall-context-S.png'),('denoising-disabled-control',D/'wall-no-denoise.png'),('ray-bevel-disabled-denoised-control',D/'wall-no-ray-bevel.png')]:
 dest=R/('diagnostic-'+name+'.png');shutil.copyfile(path,dest);im=Image.open(dest);controls[name]={'path':'candidates/round-06/'+dest.name,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'rows':{str(y):{str(x):list(im.getpixel((x,y))) for x in [96,97,98,100,288,477,478,479]} for y in [900,1200]}}
rows={};seams=[480,864,1248,2784,3168,3552,3936]
for y in [900,1200]:
 rr={}
 for x in seams:
  data={}
  for label,a in [('round05Independent',old),('round06Independent',cur),('round06Connected',nat)]:
   prof=a[y-24:y+25,x-16:x+17,:3].mean(axis=0)
   left=prof[:8].mean(axis=0);right=prof[-8:].mean(axis=0)
   expected=(left+right)/2;edge=prof[15:17].mean(axis=0)
   data[label]={'exactRGB':{str(dx):a[y,x+dx,:3].tolist() for dx in [-8,-3,-2,-1,0,1,2,3,8]},'alpha':a[y,x-2:x+3,3].tolist(),'averaged49RowRGBProfile':prof.tolist(),'edgeMinusInteriorAverage':(edge-expected).tolist(),'maximumAbsoluteEdgeInteriorChannelDifference':float(np.abs(edge-expected).max())}
  delta=np.abs(cur[y-24:y+25,x-2:x+2,:3].astype(float)-nat[y-24:y+25,x-2:x+2,:3].astype(float))
  data['round06IndependentVsConnectedMeanAbsoluteRGB']=float(delta.mean());rr[str(x)]=data
 rows[str(y)]=rr
oldval=json.loads((B/'validation.json').read_text());newval=json.loads((R/'validation.json').read_text());oldrecipe=json.loads((P/'source/round-05-recipe.json').read_text());newrecipe=json.loads((P/'source/round-06-recipe.json').read_text());oldfamily=json.loads((B/'family-settings.json').read_text());newfamily=json.loads((R/'family-settings.json').read_text())
checks={'materialsRecipeUnchanged':oldrecipe['materials']==newrecipe['materials'],'lightingRecipeUnchanged':oldrecipe['lighting']==newrecipe['lighting'],'cameraRecipeUnchanged':oldrecipe['camera']==newrecipe['camera'],'nativeMaterialNodesUnchanged':oldfamily['materials']==newfamily['materials'],'nativeWorldNodesUnchanged':oldfamily['world']==newfamily['world'],'nativeLightsUnchanged':oldfamily['lights']==newfamily['lights'],'nativeMeshGeometryUnchanged':all(o.get('sourceMeshSha256')==newval['assetAudit']['objects'][n].get('sourceMeshSha256') for n,o in oldval['assetAudit']['objects'].items()),'evaluatedBoundsUnchanged':all(o['bounds']==newval['assetAudit']['objects'][n]['bounds'] for n,o in oldval['assetAudit']['objects'].items()),'semanticPartNamesUnchanged':set(oldval['assetAudit']['objects'])==set(newval['assetAudit']['objects'])}
rec={'schemaVersion':1,'cause':'Denoiser RGB ringing against transparent independent-capture boundaries. Ray-bevel-disabled control retains the same dark/light lines; denoising-disabled control removes them.','sourceControlProject':'source/round-05.blend','controlRecipe':'source/diagnose_rgb_seams.py','controls':controls,'selectedFix':{'project':'source/round-06.blend','samples':256,'denoising':False,'geometryMaterialsLightingPaletteCameraRootsPitchUnchanged':all(checks.values()),'acceptedArtPreservationChecks':checks,'nativeFilter':'BOX width1 retained'},'samples':rows,'metricsNote':'RGB profiles average 49 native rows to distinguish systematic hairlines from Monte Carlo sampling noise. All comparisons use exact root registration; no alignment, recolor or seam patch is applied.'}
(R/'rgb-join-comparison.json').write_text(json.dumps(rec,indent=2))
# Native-scale image crops. The three columns expose the original issue, fix and native geometry reference.
try:font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',18)
except:font=ImageFont.load_default()
cols=[('Round05 independent',Image.fromarray(old)),('Round06 independent',Image.fromarray(cur)),('Round06 connected',Image.fromarray(nat))];pan=256;gap=24;header=42;rh=134;sheet=Image.new('RGBA',(3*pan+2*gap,header+6*rh),'#eee5d6');d=ImageDraw.Draw(sheet)
for i,(lab,im) in enumerate(cols):d.text((i*(pan+gap)+8,12),lab,font=font,fill='#302820')
for j,(x,y) in enumerate([(480,900),(1248,900),(2784,900),(480,1200),(1248,1200),(2784,1200)]):
 yy=header+j*rh
 for i,(lab,im) in enumerate(cols):
  xx=i*(pan+gap);d.text((xx+8,yy+7),'x=%d, y=%d'%(x,y),font=font,fill='#302820');crop=im.crop((x-128,y-48,x+128,y+48));sheet.alpha_composite(crop,(xx,yy+34))
sheet.save(R/'rgb-join-comparison.png')
v=json.loads((R/'validation.json').read_text());v['rgbJoinComparisons']={'report':'candidates/round-06/rgb-join-comparison.json','preview':'candidates/round-06/rgb-join-comparison.png','cause':rec['cause'],'metrics':{y:{x:{k:vv['maximumAbsoluteEdgeInteriorChannelDifference'] for k,vv in data.items() if isinstance(vv,dict) and 'maximumAbsoluteEdgeInteriorChannelDifference' in vv} for x,data in rr.items()} for y,rr in rows.items()}};(R/'validation.json').write_text(json.dumps(v,indent=2))
deliv=json.loads((P/'delivery.json').read_text());deliv['previews']['rgb-join-comparison']='candidates/round-06/rgb-join-comparison.png';deliv['resources']+=['source/compare_rgb_joins_round06.py','source/diagnose_rgb_seams.py','candidates/round-06/rgb-join-comparison.json',*[r['path'] for r in controls.values()]];(P/'delivery.json').write_text(json.dumps(deliv,indent=2))
print(json.dumps(v['rgbJoinComparisons'],indent=2))
