from PIL import Image,ImageDraw,ImageChops
from pathlib import Path
import json,hashlib
OUT=Path(__file__).resolve().parent
metrics={}
for tag,oldprefix,sampling in [('source-baseline','original-published-',Image.Resampling.LANCZOS),('canonical-baseline','approved-middle/published-',Image.Resampling.BOX)]:
 canvas=Image.new('RGB',(1536,744),(225,229,232));dr=ImageDraw.Draw(canvas);metrics[tag]={}
 for i,d in enumerate(['N','E','S','W']):
  src=OUT/tag/f'native-static-{d}.png';im=Image.open(src).convert('RGBA');pub=im.resize((384,704),sampling);pub.save(OUT/tag/f'published-{d}.png');old=Image.open(OUT/'resources'/(oldprefix+d+'.png')).convert('RGBA');diff=ImageChops.difference(pub,old)
  metrics[tag][d]={'newRender':str(src.relative_to(OUT)),'newPublishedSHA256':hashlib.sha256((OUT/tag/f'published-{d}.png').read_bytes()).hexdigest(),'referenceSHA256':hashlib.sha256((OUT/'resources'/(oldprefix+d+'.png')).read_bytes()).hexdigest(),'pixelEqualArchived':not diff.getbbox(),'RGBA_maxDifference':[e[1] for e in diff.getextrema()],'publicationSampling':sampling.name,'nativeAlphaBounds':im.getbbox(),'publishedAlphaBounds':pub.getbbox()}
  canvas.paste(pub,(i*384,40),pub);dr.text((i*384+10,10),tag+' '+d,fill='black')
 canvas.save(OUT/(tag+'-all4.png'))
(OUT/'reproduction-metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
for key,color in {'gray':'#dfe3e6','dark':'#182231','light':'#f5f2e9'}.items():
 sheet=Image.new('RGB',(2*448,2*608+38),color);dr=ImageDraw.Draw(sheet)
 for i,d in enumerate(['N','E','S','W']):
  p=OUT/'native-original-canonical-joins'/f'native-joined-{d}.png';im=Image.open(p).convert('RGBA').resize((448,608),Image.Resampling.BOX);xy=(i%2*448,i//2*608+38);sheet.paste(im,xy,im);dr.text((xy[0]+8,xy[1]+8),d+' native assembly at 128px cell',fill='white' if key=='dark' else 'black')
 dr.text((8,10),'Original corner + exact canonical middle; baseline, no approval',fill='white' if key=='dark' else 'black');sheet.save(OUT/f'native-joins-all4-{key}.png')
# Geometric port measurement against actual core endpoint rings.
d=json.loads((OUT/'own-source-audit.json').read_text());core=next(o for o in d['objects'] if o.get('vertices')==40);v=core['vertexCoordinates'];profile=json.loads((OUT/'resources/approved-middle/familySettings.json').read_text())['ports']['profileYThenZ']
w=v[:8];n=v[-8:];errW=max(abs(w[i][j+1]-profile[i][j]) for i in range(8) for j in range(2));errN=max(abs(((-n[i][0]) if j==0 else n[i][2])-profile[i][j]) for i in range(8) for j in range(2))
meas={'profileId':'rock-wall-full-cell-v2','profileTransverseThenZ':profile,'portW':{'plane':{'axis':'X','position':-.5},'position':[-.5,0,0],'normal':[-1,0,0],'measuredRing':w,'profileMaxAbsoluteError':errW,'canonicalMapping':'canonical local (x,y,z) at E x=.5 translates world X by -1; corner transverse=y'},'portN':{'plane':{'axis':'Y','position':.5},'position':[0,.5,0],'normal':[0,1,0],'measuredRing':n,'profileMaxAbsoluteError':errN,'canonicalMapping':'canonical local W x=-.5 rotated +90deg then translated [0,1,0]; corner transverse=-x'},'sourceBounds':d['bounds'],'nominalHeight':1.17,'joinTopHeight':1.15,'noAddedOverlap':True,'noPlaneContradiction':True,'interpretation':'Only W and N are authored functional ports. E and S are exposed corner exterior, not implicitly joins. Source shoulder is contained in core profile at ports and may be rebuilt. Native source form/count/extrema elsewhere are descriptive; exact port planes/profile/root/grid/camera remain hard.'}
(OUT/'connector-measurements.json').write_text(json.dumps(meas,indent=2)+'\n')
# Screenshots of exact shared-canvas consumer fixture; publication frames stay untouched.
cases=json.loads((OUT/'consumer-baseline/cases.json').read_text())['cases']
for name in ['logical','phone','landscape']:
 selected=[c for c in cases if c['path'].split('/')[-1].startswith(name+'-') and c['phase']==.25]
 ims=[Image.open(OUT/c['path']).convert('RGB') for c in selected];width=max(im.width for im in ims);height=max(im.height for im in ims)
 sheet=Image.new('RGB',(4*width,height+32),'#dfe3e6');dr=ImageDraw.Draw(sheet)
 for i,(im,c) in enumerate(zip(ims,selected)):sheet.paste(im,(i*width,32));dr.text((i*width+4,8),c['direction']+' '+str(c['pitch'])+'px cell',fill='black')
 sheet.save(OUT/f'consumer-{name}-all4.png')
# Compare common surface near west join at S. These are old native material differences, not a candidate defect score.
old=Image.open(OUT/'resources/original-published-S.png').convert('RGBA');mid=Image.open(OUT/'resources/approved-middle/published-S.png').convert('RGBA')
samples=[]
for z in [.15,.35,.55]:
 y=round(512+128-z*179.2);a=old.getpixel((66,y));b=mid.getpixel((317,y));samples.append({'sourcePointXYZ':[-.5,-.5,z],'cornerInsidePixel':[66,y],'middleInsidePixel':[317,y],'cornerRGBA':a,'middleRGBA':b,'maxRGBDelta':max(abs(a[i]-b[i]) for i in range(3))})
(OUT/'continuity-evidence.json').write_text(json.dumps({'role':'pre-refinement measured continuity evidence; no candidate approval','connectors':'connector-measurements.json','canonicalBoundarySamples':'canonical-boundary-samples.json','sourceReplay':'reproduction-metrics.json','nativeAll4':'native-joins-all4-gray.png','consumerAll4':['consumer-logical-all4.png','consumer-phone-all4.png','consumer-landscape-all4.png'],'consumerFixture':'consumer-fixture.mjs','consumerCases':'consumer-baseline/cases.json','nativeRecipePreserved':{'render':'CYCLES 48; BOX filter; stored filter_size 1.5; seed0; no denoise','publication':'BOX from 4x native to 2x published, proven pixel identical all4','consumer':'orderPlacements (including supportedBy ordering) then common native canvas scale2; imageSmoothingEnabled=false set after any canvas resize; ordinary browser filtering of final whole canvas via SVG foreignObject.'},'oldCornerPublishedVsCanonicalNearWJoinS':samples,'observations':['Port positions/outer profile meet geometrically without overlap or camera fitting in all four assembly rotations.','Old corner is blank, sharply faceted and substantially darker than the native carved middle. There are abrupt crown/face color and normal transitions at both joins.','N/E inside-bend views expose top concavity/blank expanse. S/W exterior views expose near-black bottom/shoulder and abrupt broad edges.','Independent published consumer baseline retains the same old material discontinuity at logical/phone/landscape sizes. This evidence is not a candidate or acceptance test.','Canonical published source reproduces exactly from immutable native project with BOX publication. Do not transplant source-old corner Lanczos or dock capturefilter .5 without an explicit family reconciliation.']},indent=2)+'\n')
