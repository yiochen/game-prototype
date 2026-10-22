"""Reproduce actual endpoint/graph comparisons and the retained residual location diagnostic."""
from pathlib import Path
import sys,json
sys.dont_write_bytecode=True
B=Path(__file__).resolve().parent.parent;E=B/'candidates/round-01';sys.path.insert(0,str(B/'source/round-01-resources/python-library'))
from PIL import Image,ImageDraw,ImageChops
a=json.loads((E/'endpoint-evidence.json').read_text());c=json.loads((E/'canonical-endpoint-evidence.json').read_text());rows=[]
for side,other in [('W','E'),('E','W')]:
 for aa,cc in zip(a['orderedTrueEndpointSurfaceEvidence'][side],c['orderedTrueEndpointSurfaceEvidence'][other]):
  rr={'edgeEnd':side,'middleEnd':other,'profileEdge':aa['profileEdge'],'materialIdentity':aa['material']==cc['material']};rr['maxResidual']={key:max(abs(av[key][i]-cv[key][i]) for av,cv in zip(aa['endpointCorners'],cc['endpointCorners']) for i in range(len(av[key]))) for key in ['YZ','normal','albedo']};rows.append(rr)
neighbor=[]
for aa,cc in zip(a['orderedSamples'],c['orderedSamples']):
 rr={k:aa[k] for k in ['inset','surface','transverse']}
 for end in ['W','E']:rr[end]={key:max(abs(aa[end][key][i]-cc[end][key][i]) for i in range(len(aa[end][key]))) for key in ['position','normal','albedo']}
 neighbor.append(rr)
v=json.loads((E/'native-validation.json').read_text());cv=json.loads((E/'canonical-native-validation.json').read_text())
def graph(m):return {k:m[k] for k in ['nodes','links','action','nodeAction']}
mats=[]
for m in v['materials']:
 if m['name'].startswith('rock-shelf-middle canonical'):
  mm=next(m0 for m0 in cv['materials'] if m0['name']==m['name']);mats.append({'name':m['name'],'actualGraphEqual':graph(m)==graph(mm)})
proof={'actualOrderedEndpointComparisons':rows,'actualNeighborBandsComparisons':neighbor,'materialGraphs':mats,'actualLightsEqual':v['lights']==cv['lights'],'settingsEqual':v['settings']==cv['settings'],'finiteGroundSupport':v['finiteGroundSupport'],'elevatedAllowance':v['elevatedDecorativeAllowance'],'method':'Two fresh Blender processes measuring exact candidate and exact approved middle source. Actual evaluated corner normals and authored albedo plus triangular ray sampling; exact material node graphs and light settings, not IDs or AABB inference.'}
(E/'canonical-continuity-proof.json').write_text(json.dumps(proof,indent=2)+'\n')
out=Image.new('RGB',(1280,1280),'#243044');dr=ImageDraw.Draw(out);locations={}
for i,d in enumerate('NESW'):
 a=Image.open(E/f'consumer-nativecanvas-independent-{d}.png').convert('RGBA');n=Image.open(E/f'consumer-nativecanvas-joined-{d}.png').convert('RGBA');box=(280,500,618,904) if d in 'EW' else (280,540,618,894)
 dr.text((0,i*320),d+' connected / independent / absolute RGB residual x8 (diagnostic only)',fill='white')
 for j,im in enumerate([n,a]):
  im=im.crop(box);back=Image.new('RGBA',im.size,'#909090');back.alpha_composite(im);back.thumbnail((410,290));out.paste(back.convert('RGB'),(420*j,i*320+22))
 delta=ImageChops.difference(a,n);rgb=Image.merge('RGB',delta.split()[:3]).crop(box).point(lambda v:min(255,v*8));rgb.thumbnail((410,290));out.paste(rgb,(840,i*320+22))
 hotspots=[]
 for yy in range(a.height):
  for xx in range(a.width):
   av=a.getpixel((xx,yy));nv=n.getpixel((xx,yy))
   if nv[3]==255 and max(abs(av[k]-nv[k]) for k in range(3))>=8:hotspots.append([xx,yy,*[av[k]-nv[k] for k in range(4)]])
 locations[d]={'opaqueRGBResidualAtLeast8Count':len(hotspots),'first100CoordinatesAndDeltaRGBA':hotspots[:100],'coordinateBounds':[[min(r[k] for r in hotspots),max(r[k] for r in hotspots)] for k in range(2)] if hotspots else None}
out.save(E/'seam-detail-sheet.png');(E/'residual-locations.json').write_text(json.dumps(locations,indent=2)+'\n')
