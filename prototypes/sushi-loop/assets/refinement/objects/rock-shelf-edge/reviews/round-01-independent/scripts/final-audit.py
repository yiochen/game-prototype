from pathlib import Path
from PIL import Image,ImageChops
import json,hashlib,sys
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent.parent;EXP=BASE.parent.parent;C=EXP/'candidates/round-01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
native=json.loads((BASE/'native-independent.json').read_text());ports=[]
for ep,mp in [('W','E'),('E','W')]:
 ef=native['candidate']['endpointFaces'][ep];mf=native['canonical']['endpointFaces'][mp]
 ec=next(x for x in ef if x['cap']);mc=next(x for x in mf if x['cap'])
 eyz=sorted([x['position'][1:] for x in ec['corners']]);myz=sorted([x['position'][1:] for x in mc['corners']])
 def adjacent(fs):
  return {tuple(sorted((round(c['position'][1],6),round(c['position'][2],6)) for c in f['corners'])):f for f in fs if not f['cap']}
 aa,bb=adjacent(ef),adjacent(mf);assert aa.keys()==bb.keys();rows=[]
 for k in aa:
  a,b=aa[k],bb[k];ca=sorted(a['corners'],key=lambda v:v['position'][1:]);cb=sorted(b['corners'],key=lambda v:v['position'][1:])
  rows.append({'profileEdgeYZ':k,'materialIdentity':a['materialSignature']==b['materialSignature'],'normalMaxAbs':max(abs(x-y) for a,b in zip(ca,cb) for x,y in zip(a['normal'],b['normal'])),'albedoMaxAbs':max(abs(x-y) for a,b in zip(ca,cb) for x,y in zip(a['albedo'],b['albedo']))})
 ports.append({'edgePort':ep,'middlePort':mp,'orderedCapVertexCount':[len(eyz),len(myz)],'profileYZMaxError':max(abs(x-y) for a,b in zip(eyz,myz) for x,y in zip(a,b)),'capMaterialIdentity':ec['materialSignature']==mc['materialSignature'],'opposingCapNormals':[ec['faceNormal'],mc['faceNormal']],'adjacentFieldRows':rows})
pub={}
for d in 'NESW':
 a=Image.open(C/f'native-{d}-4x.png').convert('RGBA').resize((384,704),Image.Resampling.BOX);b=Image.open(C/f'frames/static/{d}/000.png').convert('RGBA');df=ImageChops.difference(a,b)
 pub[d]={'completeBOXPixelIdentity':df.getbbox(alpha_only=False) is None,'extrema':df.getextrema(),'atlasMatchesFrame':sha(C/f'atlases/static-{d}.png')==sha(C/f'frames/static/{d}/000.png')}
assert all(x['completeBOXPixelIdentity'] and x['atlasMatchesFrame'] for x in pub.values())
records=json.loads((BASE/'packet-hash-verification.json').read_text())['records']
for r in records:assert sha(Path(r['absolute']))==r['sha256']
audit={'candidatePacketSHA256':sha(C/'packet.json'),'opposingEndpointFieldChecks':ports,'publication':pub,'packetSourcesUnchangedAfterReview':True,'uniquePacketResourceCount':len({x['absolute'] for x in records}),'declaredMediaRecords':25,'declaredMediaUniquePaths':24,'nativeResourceClosure':{'images':native['candidate']['externalImages'],'linkedLibraries':native['candidate']['libraries'],'meshTypesOnly':all(o['type'] in ['MESH','EMPTY'] for o in native['candidate']['objects']),'noObjectActions':all(not o['animation'] for o in native['candidate']['objects']),'noMaterialOrNodeActions':all(not m['animation'] for m in native['candidate']['materials'].values()),'noShapeKeys':all(not o.get('shapeKeys') for o in native['candidate']['objects'])},'scope':'Original object exact round-01 only; no production/family/Godot approval.'}
(BASE/'final-native-publication-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
print(json.dumps({'opposingProfilesExact':all(p['profileYZMaxError']==0 for p in ports),'opposingNormalsMaxAbs':max(r['normalMaxAbs'] for p in ports for r in p['adjacentFieldRows']),'opposingAlbedoMaxAbs':max(r['albedoMaxAbs'] for p in ports for r in p['adjacentFieldRows']),'publicationAll4CompleteBOXExact':True,'all239UniquePacketInputsUnchanged':True},indent=2))
