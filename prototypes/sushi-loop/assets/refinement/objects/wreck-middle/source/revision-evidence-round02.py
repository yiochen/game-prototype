"""Round02 native negative-space revision evidence; no grading or pixel repair."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib
import numpy as np
B=Path(__file__).resolve().parent.parent;O=B/'candidates/round-02';OLD=B/'candidates/round-01';S=B/'source';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(OLD/'packet.json')=='0ca09743115d91b4267be78f73d6fe1e9349d5629508fc17d77c2f0f8d702d77'
assert sha(B/'reviews/round-01.json')=='2efd50a7f4c92c16c1e1a554efea3b49762b0c681f0636a492a03f678b79b352'
font=ImageFont.load_default(size=16);small=ImageFont.load_default(size=14)
def runs(values,start=0):
 result=[];begin=None
 for i,v in enumerate(list(values)+[False]):
  if v and begin is None:begin=i
  if not v and begin is not None:result.append([start+begin,start+i-1]);begin=None
 return result
measure=[]
for roundName,folder in [('round-01',OLD),('round-02',O)]:
 hero=np.array(Image.open(folder/'native/static/N/000.png').convert('RGBA'));repeat=np.array(Image.open(folder/'connected-native/N.png').convert('RGBA'))
 measure.append({'round':roundName,'heroNGeometricOpeningRuns':{str(y):runs(hero[y,64:320,3]==0,64) for y in [412,413]},'nativeThreeNGeometricOpeningRuns':{str(y):runs(repeat[y,64:832,3]==0,64) for y in [412,413]},'interpretation':'Actual alpha0 intervals, including legitimate negative space; not a sampling-loss or approval test.'})
oldFields=json.loads((OLD/'canonical-endpoint-fields.json').read_text());newFields=json.loads((O/'canonical-endpoint-fields.json').read_text());oldFinite=json.loads((OLD/'finite-native-validation.json').read_text());newFinite=json.loads((O/'finite-native-validation.json').read_text())
unchanged={'completeFiniteCanonicalGeometryAndCornerFields':oldFields['fields']==newFields['fields'],'activeMaterialGraphs':oldFields['activeMaterials']==newFields['activeMaterials'],'actualLights':oldFinite['actualNativeRig']['lights']==newFinite['actualNativeRig']['lights'],'actualWorld':oldFinite['actualNativeRig']['worldNodes']==newFinite['actualNativeRig']['worldNodes'],'finiteSupportArea':oldFinite['support']['area']==newFinite['support']['area']}
assert all(unchanged.values()),unchanged
# Consistent registered before/after use-size presentation. Every source frame
# is retained whole; only review display scales and backgrounds are changed.
sheet=Image.new('RGB',(940,870),(57,68,81));dr=ImageDraw.Draw(sheet);dr.text((12,8),'N native three-module repeat: round01 / round02 at logical128',font=font,fill='white')
for col,(label,folder) in enumerate([('Round01',OLD),('Round02',O)]):
 im=Image.open(folder/'connected-native/N.png').convert('RGBA');comp=Image.alpha_composite(Image.new('RGBA',im.size,(238,238,238,255)),im).resize((448,352),Image.Resampling.LANCZOS).convert('RGB');sheet.paste(comp,(12+col*468,58));dr.text((12+col*468,34),label,font=font,fill='white')
 dr.text((12+col*468,424),'N / phone32; light / gray / dark',font=small,fill='white')
 for j,bg in enumerate([(238,238,238,255),(128,128,128,255),(21,25,35,255)]):
  comp=Image.alpha_composite(Image.new('RGBA',im.size,bg),im).resize((112,88),Image.Resampling.LANCZOS).convert('RGB');sheet.paste(comp,(12+col*468+j*148,452))
# Show the same unchanged capture of S, plus E/W in smaller whole-frame panels.
dr.text((12,558),'Round02 native S / E / W at logical128, full registered frames',font=small,fill='white')
for i,d in enumerate(['S','E','W']):
 im=Image.open(O/'native/static'/d/'000.png').convert('RGBA');comp=Image.alpha_composite(Image.new('RGBA',im.size,(128,128,128,255)),im).resize((192,352),Image.Resampling.LANCZOS).convert('RGB');sheet.paste(comp,(12+i*310,588));dr.text((12+i*310,568),d,font=small,fill='white')
# Extend the sheet rather than crop a source/asset frame.
canvas=Image.new('RGB',(940,952),(57,68,81));canvas.paste(sheet,(0,0))
for i,d in enumerate(['S','E','W']):
 im=Image.open(O/'native/static'/d/'000.png').convert('RGBA');comp=Image.alpha_composite(Image.new('RGBA',im.size,(128,128,128,255)),im).resize((192,352),Image.Resampling.LANCZOS).convert('RGB');canvas.paste(comp,(12+i*310,588))
canvas.save(O/'revision-comparison.png')
style=Image.new('RGB',(880,400),(57,68,81));dr=ImageDraw.Draw(style)
for i,(label,path,scale) in enumerate([('Original snapshot',B/'inputs/original.png',.5),('Fixed target / style only',B/'inputs/target.png',min(192/900,352/1710)),('Round02 S',O/'native/static/S/000.png',.5),('Round02 N',O/'native/static/N/000.png',.5)]):
 im=Image.open(path).convert('RGBA')
 if i==1:scale=min(192/im.width,352/im.height)
 size=(round(im.width*scale),round(im.height*scale));im=im.resize(size,Image.Resampling.LANCZOS);bg=Image.new('RGBA',(192,352),(128,128,128,255));bg.alpha_composite(im,((192-size[0])//2,0));style.paste(bg.convert('RGB'),(12+i*220,34));dr.text((12+i*220,8),label,font=small,fill='white')
style.save(O/'style-reference-comparison.png')
inputs=[OLD/'packet.json',B/'reviews/round-01.json',OLD/'connected-native/N.png',OLD/'native/static/N/000.png',OLD/'canonical-endpoint-fields.json',OLD/'finite-native-validation.json',B/'inputs/original.png',B/'inputs/target.png']
report={'asset':'wreck-middle','round':'round-02','criterion':'Original round01 single ranked blocker: isolated N bright slits must read as coherent intentional rail/bay construction.','nativeMethod':'Rear-set lower timber centerY=.10/depth.28; upper timber centerY=.15/depth.14/centerZ=.4695/height.141. Native grain/wear follows relocated top surfaces. Exact rails/collars, uprights/hardware, active normal/material fields, support, capture and rig remain unchanged.','unchangedMeasuredCanonicalResources':unchanged,'actualGeometricOpeningRuns':measure,'visualHypothesis':'The open reveal now extends through permitted interior bays and is interrupted by physical uprights, rather than appearing only around the module endpoints. This remains a hypothesis for the original independent judge; no opacity/geometry equality score grants visible acceptance.','sourceViews':'All registered source PNG bytes retained unchanged; comparison images are presentation only. Target canvas retains its independent aesthetic role, not registration authority.','inputs':[{'pathBase':'object','path':str(p.relative_to(B)),'sha256':sha(p)} for p in inputs],'approval':None}
(O/'revision-evidence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'unchanged':unchanged,'openingRuns':measure},indent=2))
