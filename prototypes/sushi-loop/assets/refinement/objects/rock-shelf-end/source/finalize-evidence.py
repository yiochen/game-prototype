from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,numpy as np
B=Path(__file__).resolve().parent;E=B.parent;O=E/'candidates/round-01';C=O/'consumer'
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
# Old installed-Chrome pilot is unreviewed disposable test output; retained task records identify the final two normative modes.
for p in C.iterdir():
 if p.is_file():p.unlink()
full=C/'fullChrome';shell=C/'shell';aliases=[]
for p in sorted(shell.glob('*.png')):
 q=full/p.name
 a=np.array(Image.open(p));b=np.array(Image.open(q));eq=a.shape==b.shape and np.array_equal(a,b)
 aliases.append({'shellPath':p.relative_to(E).as_posix(),'fullChromePath':q.relative_to(E).as_posix(),'shellSHA256':h(p),'fullChromeSHA256':h(q),'decodedPixelsIdentical':bool(eq),'maxComponentDifference':int(np.max(np.abs(a.astype(int)-b.astype(int)))) if a.shape==b.shape else None})
(C/'cross-mode-comparison.json').write_text(json.dumps({'fullChrome':json.loads((full/'manifest.json').read_text())['browser'],'shell':json.loads((shell/'manifest.json').read_text())['browser'],'files':aliases,'inspectionAliasPolicy':'Pixel-identical images may reuse actual inspection with explicit verified mapping. Nonidentical images require their own actual inspection.'},indent=2)+'\n')
# Exact cross-port RGBA profiles and spatial residual diagnostics in common coordinates.
profiles=[];diagnostics=[]
for kind in ['pair','closedRun']:
 for d in 'NESW':
  a=np.array(Image.open(full/f'common-{kind}-{d}.png').convert('RGBA'));n=np.array(Image.open(O/f'family-published/{kind}-{d}.png').convert('RGBA'))
  if d in 'NS':
   centers=[(int(2*(160 if d=='S' else 288)),675)] if kind=='pair' else [(320,675),(576,675)]
  else:
   ys=[(440 if d=='E' else 312)-.43*89.6] if kind=='pair' else [312-.43*89.6,440-.43*89.6];centers=[(448,round(y*2)) for y in ys]
  for j,(cx,cy) in enumerate(centers):
   coords=[(cx+t,cy) if d in 'NS' else (cx,cy+t) for t in range(-24,25)]
   profiles.append({'kind':kind,'direction':d,'join':j,'axis':'X' if d in 'NS' else 'Y','nativePixelCoordinates':[list(p) for p in coords],'nativeRGBA':[n[y,x].tolist() for x,y in coords],'consumerRGBA':[a[y,x].tolist() for x,y in coords]})
   box=(cx-45,cy-80,cx+45,cy+110) if d in 'NS' else (cx-120,cy-45,cx+120,cy+100)
   imn=Image.fromarray(n,'RGBA').crop(box);ima=Image.fromarray(a,'RGBA').crop(box);diff=np.abs(np.array(imn).astype(int)-np.array(ima).astype(int));rgb=np.minimum(255,diff[:,:,:3]*8).astype('uint8');rgb[diff[:,:,3]>0]=(255,80,30);imd=Image.fromarray(rgb,'RGB')
   diagnostics.append((f'{kind} {d} join{j} · native / consumer / absRGB×8; orange alpha',imn,ima,imd))
(full/'cross-port-profiles.json').write_text(json.dumps(profiles,indent=2)+'\n')
canvas=Image.new('RGB',(900,240*len(diagnostics)),(238,232,220));dr=ImageDraw.Draw(canvas)
for i,(label,*ims) in enumerate(diagnostics):
 dr.text((8,i*240+4),label,fill='black')
 for j,im in enumerate(ims):
  if im.mode=='RGBA':base=Image.new('RGBA',im.size,(238,232,220,255));base.alpha_composite(im);im=base.convert('RGB')
  im.thumbnail((285,210));canvas.paste(im,(j*300+(300-im.width)//2,i*240+24))
canvas.save(O/'seam-diagnostics-sheet.png')
# Discard only non-delivered pilot render and automatic Blender save backups before round sealing.
for p in [O/'working-S.png',B/'round-01.blend1']:
 if p.exists():p.unlink()
(O/'browser-environment.json').write_text(json.dumps({'normativeModes':[{'path':p.relative_to(E).as_posix(),'browser':json.loads(p.read_text())['browser'],'launch':json.loads(p.read_text())['launch']} for p in [full/'manifest.json',shell/'manifest.json']], 'desktopPilot':{'attempt':'cua.getApp Google Chrome','result':'Mac locked; automatic unlock failed','relevance':'Discarded native desktop interpretation; fullChrome and shell mean two completed headless launch modes. No missing normative browser evidence inferred.'}},indent=2)+'\n')
print('Cross-browser aliases',len(aliases),'pixel-exact',sum(a['decodedPixelsIdentical'] for a in aliases))
