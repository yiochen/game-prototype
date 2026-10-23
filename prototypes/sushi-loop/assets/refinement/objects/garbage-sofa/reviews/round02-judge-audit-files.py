from pathlib import Path
import json,hashlib
from PIL import Image,ImageChops
O=Path(__file__).resolve().parents[1];R=O/'reviews';P=O/'candidates/round-02';packet=json.loads((P/'packet.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
out={'packetSHA256':sha(P/'packet.json'),'hashChecks':[],'atlases':[],'nativeFrames':[],'inspectionCrops':[]}
for cohort in ['files','candidateRenders','previews']:
 for name,v in packet[cohort].items():
  p=(P/v['path']).resolve();actual=sha(p)if p.exists()else None
  out['hashChecks'].append({'cohort':cohort,'name':name,'path':v['path'],'expected':v['sha256'],'actual':actual,'pass':actual==v['sha256']})
for p in [O/'delivery-round02.json',P/'delivery.snapshot.json',P/'validation.json',O/'source/round-02.blend',O/'brief.json']:
 out.setdefault('selectedEvidence',[]).append({'path':str(p.relative_to(O)),'sha256':sha(p)})
atlas_manifest=json.loads((P/'atlas-manifest.json').read_text())
for a in atlas_manifest:
 atlas=Image.open(O/a['path']).convert('RGBA');record={'path':a['path'],'sha256':sha(O/a['path']),'size':list(atlas.size),'manifestSize':a['size'],'matches':[]}
 for i,rect in enumerate(a['rects']):
  x,y,w,h=rect;p=P/'frames'/f'{a["clip"]}-{a["direction"]}'/f'{i:03}.png';im=Image.open(p).convert('RGBA');tile=atlas.crop((x,y,x+w,y+h));same=im.tobytes()==tile.tobytes();record['matches'].append(same)
  alpha=im.getchannel('A');hist=alpha.histogram();out['nativeFrames'].append({'path':str(p.relative_to(O)),'sha256':sha(p),'size':list(im.size),'alphaBounds':alpha.getbbox(),'opaquePixels':hist[255],'partialPixels':sum(hist[1:255]),'empty':alpha.getbbox()is None,'atlasPixelsEqual':same})
 out['atlases'].append(record)
for clip in ['highlighted','clearance']:
 for direction in ['N','E','S','W']:
  for size in ['phone','logical']:
   source=P/'previews'/f'{clip}-{direction}-{size}-three-backgrounds.png';im=Image.open(source)
   for b in range(3):
    row_h=im.height//3
    if size=='phone':
     rect=(0,b*row_h,im.width,(b+1)*row_h);name=f'round02-inspect-{clip}-{direction}-{size}-bg{b}.png';im.crop(rect).save(R/name);out['inspectionCrops'].append({'source':str(source.relative_to(O)),'sourceSHA256':sha(source),'rect':rect,'crop':name,'cropSHA256':sha(R/name)})
    else:
     for half in range(2):
      rect=(half*(im.width//2),b*row_h,(half+1)*(im.width//2),(b+1)*row_h);name=f'round02-inspect-{clip}-{direction}-{size}-bg{b}-half{half}.png';im.crop(rect).save(R/name);out['inspectionCrops'].append({'source':str(source.relative_to(O)),'sourceSHA256':sha(source),'rect':rect,'crop':name,'cropSHA256':sha(R/name)})
out['allPacketHashesMatch']=all(r['pass']for r in out['hashChecks']);out['allAtlasPixelsMatch']=all(all(a['matches'])for a in out['atlases'])
# Independent fresh-session witness comparison, not a claim of all-frame replay identity.
w=R/'round02-judge-witness-clearance-E-005.png'
if w.exists():
 original=P/'frames/clearance-E/005.png';ia=Image.open(w).convert('RGBA');ib=Image.open(original).convert('RGBA');out['witnessReplay']={'witness':w.name,'sha256':sha(w),'shipping':str(original.relative_to(O)),'shippingSHA256':sha(original),'pixelsEqual':ia.tobytes()==ib.tobytes(),'differenceExtrema':ImageChops.difference(ia,ib).getextrema(),'scope':'One fresh background Blender replay at native clearance/E/frame6; no generalization to allframes.'}
(R/'round02-judge-file-audit.json').write_text(json.dumps(out,indent=2)+'\n')
print('HASH',out['allPacketHashesMatch'],'ATLAS',out['allAtlasPixelsMatch'],'FRAMES',len(out['nativeFrames']),'CROPS',len(out['inspectionCrops']))
