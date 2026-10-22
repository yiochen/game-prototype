from pathlib import Path
import json,hashlib,math
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
P=Path(__file__).resolve().parents[1];O=P.parent.parent;C=O/'candidates/round-01';R=P/'resources';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();results=json.loads((R/'consumer-results.json').read_text())['cases'];audit=json.loads((P/'native-independent-audit.json').read_text())['candidate'];cross=[];inputs=[];local=[]
def diff(p,q):
 a=np.array(Image.open(p).convert('RGBA')).astype(int);b=np.array(Image.open(q).convert('RGBA')).astype(int);d=abs(a-b);return {'decodedEqual':bool((d==0).all()),'differentPixels':int((d!=0).any(2).sum()),'maxRGBA':d.reshape(-1,4).max(0).tolist(),'alphaDifferentPixels':int((d[:,:,3]!=0).sum())}
for run in results:
 checks={}
 for f in ['fixture.html','fixture.mjs','fixture.bundle.js','world-sprite-raster.js','sprite-layout.js']:checks[f]=sha(R/'consumer'/f)==run['inputHashes'][f]
 for d in 'NESW':
  for label,path in [('original',C/'atlases'/('static-'+d+'.png')),('middle',O/'source/resources/wreck-middle'/(d+'.png')),('edge',O/'source/resources/wreck-edge'/(d+'.png')),('middle-L',C/'middle-L'/(d+'.png')),('mixed-edge-L',C/'mixed-edge-L'/(d+'.png'))]:checks[d+'-'+label]=sha(path)==run['inputHashes'][d+'-'+label]
 inputs.append({'mode':run['mode'],'case':run['id'],'allInputsMatch':all(checks.values()),'checks':checks,'version':run['browserVersion'],'launch':run['launch'],'executable':run['actualBrowserExecutable'],'DPR':run['deviceScaleFactor'],'viewport':run['viewport'],'errors':run['errors'],'allNativeAndDisplayCanvasNearestAfterResize':all(not f['nativeSmoothing']and not f['displayCanvasSmoothing']for f in run['evidence']['fixtures'])})
for ident in ['logical128-integer','logical128-fractional','phone32-integer','phone32-fractional']:
 a=next(r for r in results if r['id']==ident and r['mode']=='full-chromium');b=next(r for r in results if r['id']==ident and r['mode']=='bundled-headless-shell');cross.append({'case':ident,'nativeCanvasesAllExact':all(diff(C/'consumer'/x,C/'consumer'/y)['decodedEqual']for x,y in zip(a['nativeCanvases'],b['nativeCanvases'])),'CSS':diff(C/'consumer'/a['cssScreenshot'],C/'consumer'/b['cssScreenshot'])})
 for kind in ['middle-L','mixed-edge-L']:
  for d in 'NESW':
   fixture=next(f for f in a['evidence']['fixtures']if f['kind']==kind and f['direction']==d);plan=fixture['plan'];off=a['evidence']['case']['rootOffset'];view=next(v for v in audit['views']if v['direction']==d);rot=np.array(view['rootMatrix'])[:3,:3];base=C/'consumer'/('full-chromium-'+ident+'-'+kind+'-'+d);ind=Image.open(str(base)+'-independent.png').convert('RGBA');nat=Image.open(str(base)+'-native-control.png').convert('RGBA');x=np.array(ind).astype(int);y=np.array(nat).astype(int);mask=Image.new('L',ind.size);draw=ImageDraw.Draw(mask)
   for face in view['fullCollarPolygons']:
    pts=[]
    for p in face['vertices']:
     w=rot@np.array(p);pts.append(((128*w[0]+off[0]-plan['x'])*2,(-128*w[1]-89.6*w[2]+off[1]-plan['y'])*2))
    draw.polygon(pts,fill=255)
   mask=mask.filter(ImageFilter.MinFilter(3));m=np.array(mask)>0;dd=abs(x-y);deltaAlpha=(y[:,:,3]-x[:,:,3]);local.append({'case':ident,'kind':kind,'direction':d,'maskPixels':int(m.sum()),'maxRGBAInsideErodedFiniteCollars':dd[m].max(0).tolist(),'alphaLossPixelsVsNativeControl':int(((deltaAlpha>0)&m).sum()),'opaqueControlToNonopaque':int(((y[:,:,3]==255)&(x[:,:,3]<255)&m).sum()),'scope':'Projected actual finite .08 collar polygons only; 1nativepixel erosion separates exterior coverage/raster precision. This diagnostic is separate from visible full native/CSS inspection and grants no numerical waiver.'})
recapture=[]
for kind in ['candidate-single','middle-L','mixed-edge-L']:
 for d in 'NESW':
  dest=C/'frames/static'/d/'000.png'if kind=='candidate-single'else C/kind/(d+'.png');own=P/'evidence/independent-native-L'/kind/(d+'.png');recapture.append({'kind':kind,'direction':d,**diff(own,dest)})
report={'candidatePacketSHA256':sha(R/'packet.json'),'currentHelpers':{f:sha(R/'consumer'/f)for f in ['world-sprite-raster.js','sprite-layout.js']},'all8ActualBrowserInputBindings':inputs,'crossMode':cross,'nativeFiniteCollarComparison':local,'independentNativeAssemblyReplay':recapture,'publicationIdentities':[{'direction':d,'heroNativeAtlasBytesEqual':len({sha(C/'frames/static'/d/'000.png'),sha(C/'native/static'/d/'000.png'),sha(C/'atlases'/('static-'+d+'.png'))})==1,'approvedMiddleFrameExact':sha(O/'source/resources/wreck-middle'/(d+'.png'))==sha(O/'reviews/preparation-v1/resources/canonical/wreck-middle/individual'/(d+'.png')),'approvedEdgeFrameExact':sha(O/'source/resources/wreck-edge'/(d+'.png'))==sha(O/'reviews/preparation-v1/resources/canonical/wreck-edge/individual'/(d+'.png'))}for d in 'NESW'],'interpretation':'Full native canvases and actualCSS are distinct. Both actual prescribed153 modes were inspected from their exact bound screenshots. Material/normal coherence and absence of localized visible cracks/deadspots are independently judged; raw area-light/exterior raster residuals and CSS residuals stay unmodified.'}
(P/'control-and-consumer-analysis.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'bindingsAll':all(v['allInputsMatch']for v in inputs),'crossMode':cross,'maxLocalAlphaLossPixels':max(v['alphaLossPixelsVsNativeControl']for v in local),'maxLocalOpaqueLossPixels':max(v['opaqueControlToNonopaque']for v in local),'independentNativeReplay':recapture,'publication':report['publicationIdentities']},indent=2))
