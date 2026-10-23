import pathlib,json,hashlib,numpy as np
from PIL import Image,ImageDraw
b=pathlib.Path('prototypes/sushi-loop/assets/refinement/objects/chef-rowan').resolve();c=b/'candidates/round-02';prior=b/'candidates/round-01';r=b/'reviews/round02-independent';packet=json.loads((c/'packet.json').read_text());hashfails=[];count=0
for sec in ['files','candidateRenders','previews']:
 for v in packet[sec].values():
  count+=1
  if hashlib.sha256((c/v['path']).read_bytes()).hexdigest()!=v['sha256']:hashfails.append(v['path'])
parity=[]
for clip,facing,ix in [('idle','S',0),('work','N',5),('hold','N',0),('hold','W',0),('load','W',5),('load','S',5)]:
 a=np.array(Image.open(r/f'reopened-{clip}-{facing}-{ix:02}.png').convert('RGBA'));z=np.array(Image.open(c/f'frames/{clip}-{facing}-{ix:02}.png').convert('RGBA'));d=np.abs(a.astype(int)-z.astype(int));parity.append({'path':f'frames/{clip}-{facing}-{ix:02}.png','sameRGBA':bool(np.array_equal(a,z)),'changedPixels':int(np.any(d,axis=-1).sum()),'maxChannelError':int(d.max())})
matches=[];pixeldiffs=[]
for facing in ['N','E','S','W']:
 sheet=Image.new('RGB',(768,1792),(146,150,155));d=ImageDraw.Draw(sheet)
 for ci,clip in enumerate(['idle','work','hold','load']):
  atlas=Image.open(c/f'atlases/{clip}-{facing}.png').convert('RGBA')
  for ix in range(12):
   im=Image.open(c/f'frames/{clip}-{facing}-{ix:02}.png').convert('RGBA');x=(ix%6)*384;y=(ix//6)*640;matches.append(np.array_equal(np.array(im),np.array(atlas.crop((x,y,x+384,y+640)))))
   if clip in ['idle','work']:
    old=np.array(Image.open(prior/f'frames/{clip}-{facing}-{ix:02}.png').convert('RGBA'));new=np.array(im);delta=np.abs(old.astype(int)-new.astype(int))
    if np.any(delta):
     coords=np.argwhere(delta);pixeldiffs.append({'path':f'frames/{clip}-{facing}-{ix:02}.png','changedComponents':[{'yxChannel':co.tolist(),'prior':int(old[tuple(co)]),'new':int(new[tuple(co)])} for co in coords],'maxError':int(delta.max()),'alphaChanges':int(np.count_nonzero(delta[:,:,3]))})
   im=im.resize((192,320),Image.Resampling.LANCZOS).crop((32,64,160,272));x=(ix%6)*128;y=(ci*2+ix//6)*224;sheet.paste(im,(x,y+16),im);d.text((x+2,y+2),f'{clip} {facing} {ix:02}',fill=(25,30,35))
 sheet.save(r/f'all48-{facing}-logical-crops.png')
old=json.loads((b/'reviews/round01-independent/source_native_audit.json').read_text());new=json.loads((r/'source_native_audit.json').read_text());contact=[];bounds=[];proj=[];cam=np.array(new['summary']['camera']['matrix']);right=cam[:3,0];up=cam[:3,1];local=np.array([[-.14,0,0,1],[.14,0,0,1],[.14,.19343365728855133,0,1],[-.14,.19343365728855133,0,1],[0,0,0,1]])
for a,z in zip(old['frames'],new['frames']):
 for k in ['rootLocation','rootScale','rootYaw','handsWorld','foodRootWorld','foodVisible','knifeVisible','feetBoneWorld','headBoneWorld','knifeBounds']:
  if a[k]!=z[k]:contact.append([a['clip'],a['facing'],a['index'],k])
 if a['bodyBounds']!=z['bodyBounds']:bounds.append([a['clip'],a['facing'],a['index']])
 wa=(np.array(a['foodPlaneWorldMatrix'])@local.T).T[:,:3];wz=(np.array(z['foodPlaneWorldMatrix'])@local.T).T[:,:3];delta=wz-wa
 pe=np.array([delta@right*256,-delta@up*256]).T
 expected=np.array([0,.15*np.cos(np.deg2rad(35)),-.15*np.sin(np.deg2rad(35))]);proj.append({'clip':a['clip'],'direction':a['facing'],'index':a['index'],'maxPixelError':float(np.max(np.abs(pe))),'rayDisplacementError':float(np.max(np.abs(delta-expected)))})
a=json.loads((r/'round-01-semantics.json').read_text());z=json.loads((r/'round-02-semantics.json').read_text());diff=[]
def walk(x,y,p=''):
 if type(x)!=type(y):diff.append([p,x,y]);return
 if isinstance(x,dict):
  for k in sorted(x.keys()|y.keys()):
   if k not in x or k not in y:diff.append([p+'/'+k,x.get(k),y.get(k)])
   else:walk(x[k],y[k],p+'/'+k)
 elif isinstance(x,list):
  if len(x)!=len(y):diff.append([p+'/length',len(x),len(y)])
  else:
   for i,(u,v) in enumerate(zip(x,y)):walk(u,v,p+'/'+str(i))
 elif x!=y:diff.append([p,x,y])
walk(a,z)
extra=json.loads((r/'native_extra.json').read_text());oldextra=json.loads((b/'reviews/round01-independent/native_extra.json').read_text())
summary={'packetSHA256':hashlib.sha256((c/'packet.json').read_bytes()).hexdigest(),'hashReferencesChecked':count,'hashFailures':hashfails,'rerenderParity':parity,'all192AtlasCellsExact':all(matches),'idleWorkDifferences':pixeldiffs,'nativeContactStateDifferences':contact,'nativeBodyBoundsDifferences':bounds,'restSkeletonEqual':old['rest']['bones']==new['rest']['bones'],'all24ActionSignaturesEqual':oldextra['actions']==extra['actions'],'projectionCount':len(proj),'maximumProjectedCornerAnchorErrorNativePixels':max(x['maxPixelError'] for x in proj),'maximumRayDisplacementErrorWorld':max(x['rayDisplacementError'] for x in proj),'semanticDifferences':diff,'uv':extra['uv'],'foodTexture':extra['foodTexture']}
(r/'independent-checks.json').write_text(json.dumps(summary,indent=2));(r/'projection-checks.json').write_text(json.dumps(proj,indent=2));print(json.dumps(summary,indent=2))
