from pathlib import Path
from PIL import Image,ImageChops,ImageDraw,ImageFilter
import json,hashlib,math,sys,shutil
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent.parent;EXP=BASE.parent.parent;C=EXP/'candidates/round-01';OUT=BASE/'captures'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def summary(a,b,mask=None):
 a=a.convert('RGBA');b=b.convert('RGBA');aa=list(a.getdata());bb=list(b.getdata());mm=list(mask.getdata()) if mask else [255]*len(aa);pixels=[(i,x,y) for i,(x,y,m) in enumerate(zip(aa,bb,mm)) if m]
 if not pixels:return {'pixels':0}
 rgb=[[abs(x[k]-y[k]) for k in range(3)] for i,x,y in pixels]
 maxv=[max(p[k] for p in rgb) for k in range(3)];alpha=[max(0,x[3]-y[3]) for i,x,y in pixels]
 hits=sorted([(max(d),i,x,y) for (i,x,y),d in zip(pixels,rgb)],reverse=True)[:12]
 return {'pixels':len(pixels),'differentRGBPixels':sum(any(d) for d in rgb),'maxRGB':maxv,'meanRGB':[sum(p[k] for p in rgb)/len(rgb) for k in range(3)],'alphaDeficitPixels':sum(v>0 for v in alpha),'maxAlphaDeficit':max(alpha),'maxAbsAlphaDifference':max(abs(x[3]-y[3]) for i,x,y in pixels),'largestResidualLocations':[{'xy':[i%a.width,i//a.width],'nativeRGBA':x,'independentRGBA':y,'maxRGB':dv} for dv,i,x,y in hits]}
replays={};seams={}
for d,ang in {'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}.items():
 raw=Image.open(OUT/f'reopen-{d}-4x.png').convert('RGBA');known=Image.open(C/f'native-{d}-4x.png').convert('RGBA');pub=raw.resize((384,704),Image.Resampling.BOX);pub.save(OUT/f'reopen-{d}-2x.png')
 mixed=Image.open(OUT/f'mixed3-{d}-4x.png').convert('RGBA');mixed2=mixed.resize((896,1216),Image.Resampling.BOX);mixed2.save(OUT/f'mixed3-{d}-2x.png')
 expectedMixed=Image.open(C/f'native-strip-{d}-4x.png').convert('RGBA')
 replays[d]={'heroRaw':summary(raw,known),'heroPublished':summary(pub,Image.open(C/f'frames/static/{d}/000.png')),'mixedRaw':summary(mixed,expectedMixed)}
 native=Image.new('RGBA',(898,1218));native.paste(mixed2,(1,1));ind=Image.open(OUT/f'consumer-independent-{d}.png').convert('RGBA');assert ind.size==native.size
 opaque=native.getchannel('A').point(lambda v:255 if v==255 else 0);eroded=opaque.filter(ImageFilter.MinFilter(5));outer=ImageChops.subtract(opaque,eroded)
 join=Image.new('L',native.size);dr=ImageDraw.Draw(join)
 for x in [-.5,.5]:
  points=[]
  for y,z in [(-.45,0),(.45,0),(.45,.28),(.39,.43),(-.39,.43),(-.45,.28)]:
   xx=x*math.cos(ang)-y*math.sin(ang);yy=x*math.sin(ang)+y*math.cos(ang)
   points.append((2*(224+128*xx)+1,2*(376-128*yy-89.6*z)+1))
  dr.polygon(points,fill=255);dr.line(points+[points[0]],fill=255,width=7)
 joinInside=ImageChops.multiply(join,eroded);joinInside.save(OUT/f'independent-join-mask-{d}.png')
 extentUnion=ImageChops.lighter(native.getchannel('A'),ind.getchannel('A')).point(lambda v:255 if v>0 else 0);partial=ImageChops.subtract(extentUnion,opaque)
 seams[d]={'nativeOpaqueAll':summary(native,ind,opaque),'interiorErodedTwoSourcePixels':summary(native,ind,eroded),'outerPrecisionBand':summary(native,ind,outer),'partialOrExternalExtentBand':summary(native,ind,partial),'projectedTruePortNeighborhoodInterior':summary(native,ind,joinInside)}
 # Own source-based evidence display, same registered camera and pitch; fixed blank-margin crop only after capture.
 display=Image.new('RGB',(896,480),(144,144,144));nlogical=native.resize((449,609),Image.Resampling.BOX);ilogical=ind.resize((449,609),Image.Resampling.BOX)
 for ix,im in enumerate([nlogical,ilogical]):
  cropped=im.crop((0,128,448,608));display.paste(cropped,(448*ix,0),cropped)
 display.save(OUT/f'native-v-independent-{d}-128.png')
(BASE/'independent-render-residuals.json').write_text(json.dumps({'candidatePacketSHA256':sha(C/'packet.json'),'reopenedSavedSourceReplays':replays,'mixedNativeVsActualCurrentConsumer':seams,'interpretation':'Exact coverage is separate from RGB identity. Independent reopen uses actual saved meshes, actual canonical collection, canonical shared rig, fixed camera and authored root rotations. Small stochastic/precision shading residuals and broad finite-area-light differences are retained raw and localized. Local join masks derive actual profile projection and intersect native opaque interior; two-source-pixel outer precision bands remain separately measured, not discarded as global pass. Visual inspection determines materiality; no blanket numeric seam waiver.'},indent=2)+'\n')
browser=json.loads((BASE/'browser-independent.json').read_text());deltas=[]
for launch in browser['launches']:
 for s in launch['screenshots']:
  own=Image.open(BASE/s['path']).convert('RGBA');old=Image.open(C/f"consumer-{launch['mode']}-{s['id']}.png").convert('RGBA');diff=ImageChops.difference(own,old);bbox=diff.getbbox(alpha_only=False)
  sceneEqual=ImageChops.difference(own.crop((0,32,own.width,own.height)),old.crop((0,32,old.width,old.height))).getbbox(alpha_only=False) is None
  deltas.append({'mode':launch['mode'],'id':s['id'],'exactPngBytes':s['exactPngBytes'],'differenceBounds':bbox,'allScenePixelsBelowHeadingIdentical':sceneEqual})
assert all(x['allScenePixelsBelowHeadingIdentical'] for x in deltas)
(BASE/'browser-replay-comparison.json').write_text(json.dumps({'candidatePacketSHA256':sha(C/'packet.json'),'records':deltas,'finding':'Each launch reproduces7/9 whole screenshot PNG files exactly. Only W/E control-sheet heading text differs, confined toY4..21; supplied captures say common128cell while sealed browser harness says128cell. Every screenshot scene pixel belowY32 is identical. Art/atlas/consumer bytes are unchanged. This is disclosed evidence-label drift, not a native art or join pass substitute.'},indent=2)+'\n')
# Complete registered frames at intended logical128 and phone32, no alpha fitting.
sheet=Image.new('RGB',(1040,1140),(35,40,51));dr=ImageDraw.Draw(sheet)
for row,(label,bg) in enumerate([('light',(238,242,237)),('gray',(144,144,144)),('dark',(23,37,57))]):
 yy=row*380;dr.text((8,yy+4),label+' logical cell128 then phone32; full frames',fill='white')
 for ix,d in enumerate('NESW'):
  hero=Image.open(C/f'frames/static/{d}/000.png').convert('RGBA');logical=hero.resize((192,352),Image.Resampling.BOX);phone=hero.resize((48,88),Image.Resampling.BOX)
  block=Image.new('RGB',(192,352),bg);block.paste(logical,(0,0),logical);sheet.paste(block,(ix*200,yy+24));pb=Image.new('RGB',(48,88),bg);pb.paste(phone,(0,0),phone);sheet.paste(pb,(808+ix*56,yy+200))
sheet.save(OUT/'intended-size-heroes.png')
# Unscaled crop coverage for the long phase sheets' phone blocks and a representative full128 row.
cropmap=[]
for mode in ['fullChrome','shell']:
 for phase in ['css','root','pan']:
  source=C/f'consumer-{mode}-phase-{phase}.png';im=Image.open(source).convert('RGB');box=[0,1596,1832,2096];dest=OUT/f'phase-phone-{mode}-{phase}.png';im.crop(box).save(dest);cropmap.append({'source':source.name,'sourceSHA256':sha(source),'crop':box,'path':str(dest.relative_to(BASE)),'resize':None})
for phase in ['css','root','pan']:
 source=C/f'consumer-fullChrome-phase-{phase}.png';im=Image.open(source).convert('RGB');box=[0,556,1832,1064];dest=OUT/f'phase-128-{phase}.png';im.crop(box).save(dest);cropmap.append({'source':source.name,'sourceSHA256':sha(source),'crop':box,'path':str(dest.relative_to(BASE)),'resize':None})
(BASE/'visual-crop-provenance.json').write_text(json.dumps(cropmap,indent=2)+'\n')
# All exact declared record paths, with explicit same-path alias and direct file/content inspection.
packet=json.loads((C/'packet.json').read_text());coverage=[]
for group in ['candidateRenders','previews']:
 for k,v in packet[group].items():
  coverage.append({'group':group,'name':k,'path':v['path'],'sha256':v['sha256'],'inspection':'direct actual file view, plus intended-size sheets and unscaled phase crops where applicable' if k!='repeated' else 'verified identical path and hash to fullChrome-background-gray; reuses that actual direct inspection'})
(BASE/'declared-media-coverage.json').write_text(json.dumps({'candidatePacketSHA256':sha(C/'packet.json'),'records':coverage,'uniquePaths':len({v['path'] for v in coverage}),'alias':'repeated and fullChrome-background-gray both name consumer-fullChrome-background-gray.png with identical SHA6259d4757915c399e5c41ce0e9cd688a8e6a996e0bdc8dcede8435107f26412e'},indent=2)+'\n')
loaded=[]
for n,m in sorted(sys.modules.items()):
 p=getattr(m,'__file__',None)
 if p and '/PIL/' in p:
  p=Path(p);q=BASE/'resources/python-loaded/PIL'/p.name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);loaded.append({'module':n,'source':str(p),'path':str(q.relative_to(BASE)),'sha256':sha(q)})
(BASE/'python-loaded-modules.json').write_text(json.dumps(loaded,indent=2)+'\n')
print(json.dumps({'heroPublishedMaxRGB':{d:replays[d]['heroPublished']['maxRGB'] for d in replays},'localJoins':{d:{k:v for k,v in s['projectedTruePortNeighborhoodInterior'].items() if k in ['pixels','maxRGB','alphaDeficitPixels','maxAlphaDeficit']} for d,s in seams.items()},'outerAlphaDeficit':{d:s['outerPrecisionBand']['alphaDeficitPixels'] for d,s in seams.items()},'browserAllScenePixelsIdentical':True,'declaredRecords':len(coverage),'uniqueMedia':len({v['path'] for v in coverage})},indent=2))
