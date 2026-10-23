import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,hashlib,math,shutil
from PIL import Image,ImageChops,ImageDraw
B=Path(__file__).resolve().parents[1];E=B/'evidence';R=B/'resources'
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
a=json.loads((E/'derivative-native-audit.json').read_text());c=json.loads((E/'canonical-native-audit.json').read_text())
records=[]
for d in ['N','E','S','W']:
 p=E/'historical-replay'/('native4x-'+d+'.png');im=Image.open(p).convert('RGBA');out=im.resize((384,704),Image.Resampling.LANCZOS);op=p.with_name('published2x-'+d+'.png');out.save(op)
 records.append({'facing':d,'nativeSize':list(im.size),'publishedSize':list(out.size),'nativeSHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'publishedSHA256':hashlib.sha256(op.read_bytes()).hexdigest(),'operation':'Pillow12.3.0 RGBA resize to384x704 LANCZOS; historical baseline only'})
orig=Image.open(R/'object/original.png').convert('RGBA');replay=Image.open(E/'historical-replay/published2x-S.png').convert('RGBA')
pixels=list(zip(orig.getdata(),replay.getdata()));diff=[(p,q) for p,q in pixels if p!=q]
report={'records':records,'snapshotComparisonS':{'originalSize':list(orig.size),'differentRGBApixels':len(diff),'maximumChannelDelta':[max((abs(p[i]-q[i]) for p,q in pixels),default=0) for i in range(4)],'exactDecodedRGBA':not diff},'interpretation':'Preparation source replay only; neither source appearance nor cross-asset joins are approved.'}
write(E/'historical-replay/summary.json',report)
sheet=Image.new('RGB',(4*192,3*352+120),'white');draw=ImageDraw.Draw(sheet)
for row,(label,bg) in enumerate([('light','#f6f0e5'),('gray','#80878f'),('dark','#13243a')]):
 for col,d in enumerate(['N','E','S','W']):
  im=Image.open(E/'historical-replay'/('published2x-'+d+'.png')).convert('RGBA').resize((192,352),Image.Resampling.LANCZOS)
  tile=Image.new('RGBA',im.size,bg);tile.alpha_composite(im);sheet.paste(tile.convert('RGB'),(col*192,row*352));draw.text((col*192+6,row*352+6),label+' '+d,fill='white' if row else 'black')
for col,d in enumerate(['N','E','S','W']):
 im=Image.open(E/'historical-replay'/('published2x-'+d+'.png')).convert('RGBA').resize((48,88),Image.Resampling.LANCZOS);tile=Image.new('RGBA',im.size,'#80878f');tile.alpha_composite(im);sheet.paste(tile.convert('RGB'),(col*192+72,3*352+20));draw.text((col*192+6,3*352+4),'phone cell32 '+d,fill='black')
sheet.save(E/'historical-replay/use-size-sheet.png')
profile=[[v[1],v[2]] for v in a['ports']['W']['vertices']]
normals=[]
for j,(pa,pb) in enumerate(zip(profile,profile[1:]+profile[:1])):
 dy=pb[0]-pa[0];dz=pb[1]-pa[1];n=[0,dz,-dy];mag=math.sqrt(sum(x*x for x in n));n=[x/mag for x in n]
 normals.append({'sectionEdge':j,'orderedYZ':[pa,pb],'normalXYZ':n,'material':'reef cyan stone planes' if j in [2,3,4,5] else 'reef blue stone'})
materials={}
for name in ['reef blue stone','reef cyan stone planes']:
 m=c['materials'][name];r=next(n['ramp'] for n in m['nodes'] if n['type']=='VALTORGB');bs=next(n for n in m['nodes'] if n['type']=='BSDF_PRINCIPLED');vals={i['name']:i['value'] for i in bs['inputs']};e0,e1=r['elements']
 samples=[]
 for z in [0,.1,.2,.3,.35,.4,.44,.68]:
  t=max(0,min(1,(z-e0['position'])/(e1['position']-e0['position'])));samples.append({'worldZ':z,'linearRGBA':[x*(1-t)+y*t for x,y in zip(e0['color'],e1['color'])]})
 materials[name]={'nativeGraphLinks':m['links'],'heightRamp':r,'evaluatedFromActualLinearRamp':samples,'roughness':vals['Roughness'],'specularIORLevel':vals['Specular IOR Level'],'IOR':vals['IOR'],'metallic':vals['Metallic'],'alpha':vals['Alpha'],'emissionStrength':vals['Emission Strength']}
checks={'derivativePortsEqualCanonical':{side:a['ports'][side]['vertices']==c['ports'][side]['vertices'] for side in ['W','E']},'canonicalEndpointBands':{},'assetBounds':a['bounds'],'declaredHeight':.68,'finiteGroundArea':a['ground']['totalArea'],'noElevatedGeometryOutsideNominalCell':len(a['elevatedGeometryBeyondNominalCell'])==0}
for side in ['W','E']:
 ts=[t for t in c['ports'][side]['adjacentTrianglesIncludingCaps'] if not t['cap']]
 checks['canonicalEndpointBands'][side]={'minX':min(v[0] for t in ts for v in t['vertices']),'maxX':max(v[0] for t in ts for v in t['vertices']),'allCornerNormalsFlatToTriangle':all(max(abs(x-y) for x,y in zip(t['normal'],n))<1e-6 for t in ts for n in t['cornerNormals']),'triangles':len(ts)}
write(E/'finite-native-summary.json',{'checks':checks,'orderedYZ':profile,'canonicalSectionFields':normals,'canonicalEndpointMaterials':materials,'canonicalLights':c['lighting'],'canonicalSavedCapture':c['savedCapture'],'rotatedDerivativePorts':a['rotatedPorts'],'canonicalBinding':{'sourceSHA256':'51d515119c1a229f57f3b242fdf040b28ef00121692cb3d40d8821dab70ff3c5','packetSHA256':'d60ff36edc6006a0d4082692e7c115be23e1fc1e9d674f8bdc5c2f8ccc447ca8','reviewSHA256':'f60dabe7a9e2ff5f0460f0e63a16fcd98a849415b21277cab7eb87ac1ec1a71e'}})
print(json.dumps(report['snapshotComparisonS']));print('SUMMARY_COMPLETE')
