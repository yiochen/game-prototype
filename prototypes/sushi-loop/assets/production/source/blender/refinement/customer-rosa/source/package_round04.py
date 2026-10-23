from pathlib import Path
import json,hashlib,shutil,subprocess,struct,zlib
from PIL import Image,ImageDraw,ImageChops
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent;OUT=OBJ/'candidates/round-04';PROD=(OBJ/'../../../production').resolve()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rel(p):return str(Path(p).relative_to(OBJ))
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n')
brief=json.loads((OBJ/'brief.json').read_text());res=HERE/'resources';res.mkdir(exist_ok=True)
for food,dep in brief['foodDependencies'].items():shutil.copyfile((OBJ/dep['artwork']).resolve(),res/(food+'.png'))
shutil.copyfile(OBJ/'inputs/source-rig.json',res/'main-rig.json');shutil.copyfile(OBJ/'inputs/runtime-variants/export/source/customer-rosa/rig.json',res/'runtime-rig.json')
shutil.copyfile(OBJ/'inputs/runtime-variants/starter-meals-project.blend',res/'original-runtime-backup.blend')
for name in ['source-contract-main.json','source-contract-runtime.json','source-samples-main.json.gz','source-samples-runtime.json.gz','semantic-food-mapping.json']:shutil.copyfile(OBJ/'reviews'/name,res/name)
context=res/'context';context.mkdir(exist_ok=True)
for d in ['N','E','S','W']:shutil.copyfile(PROD/f'sprites/stool-blue/static-{d}.png',context/f'stool-blue-{d}.png')
rects=[[i%6*384,i//6*640,384,640] for i in range(12)]
def bundle(runtime=False):
 base=OUT/'runtimeVariants' if runtime else OUT;rig=json.loads((res/('runtime-rig.json' if runtime else 'main-rig.json')).read_text());audit=json.loads((base/'validation.json').read_text());assert audit['allChecksPassed']
 b={'project':'source/round-04-runtime.blend' if runtime else 'source/round-04.blend','recipe':'source/build-runtime-round04.json' if runtime else 'source/build-main-round04.json','recipeScript':'source/build_round04.py','validation':rel(base/'validation.json'),'rawFrames':[],'atlases':[],'previews':{},'nativeRecords':{},'resources':{},'publishedSourceScale':2,'nativeCaptureScale':2}
 for clip,c in rig['clips'].items():
  cid=clip.replace('_','-');sheet=Image.new('RGB',(12*96,4*176),'#70757a');sd=ImageDraw.Draw(sheet)
  for row,d in enumerate(['N','E','S','W']):
   frames=[base/'frames'/f'{cid}-{d}'/f'{i:03d}.png' for i in range(12)];assert all(p.exists() for p in frames)
   atlas=Image.new('RGBA',(2304,1280));mini=Image.new('RGB',(12*96,176),'#70757a');md=ImageDraw.Draw(mini)
   for i,p in enumerate(frames):
    im=Image.open(p).convert('RGBA');assert im.size==(384,640);atlas.paste(im,(rects[i][0],rects[i][1]));b['rawFrames'].append(dict(clip=cid,direction=d,index=i,path=rel(p),sha256=sha(p)))
    thumb=im.resize((96,160),Image.Resampling.LANCZOS);mini.paste(thumb,(i*96,16),thumb);md.text((i*96+3,2),f'{d} {i+1:02d}',fill='white');sheet.paste(mini,(0,row*176))
   ap=base/'atlases'/f'{cid}-{d}.png';ap.parent.mkdir(exist_ok=True);atlas.save(ap)
   # Read atlas pixels back; each region is the full unmodified original native frame.
   reread=Image.open(ap).convert('RGBA')
   assert all(reread.crop((r[0],r[1],r[0]+384,r[1]+640)).tobytes()==Image.open(p).convert('RGBA').tobytes() for r,p in zip(rects,frames))
   b['atlases'].append(dict(clip=cid,direction=d,path=rel(ap),sha256=sha(ap),columns=6,rows=2,size=[2304,1280],rects=rects,fps=12,loop=c['loop'],frameOrder=list(range(12))))
   cs=base/'contact-sheets'/f'{cid}-{d}.png';cs.parent.mkdir(exist_ok=True);mini.save(cs);b['previews'][f'all-frames-{cid}-{d}']=rel(cs)
   clipout=base/'playbacks'/f'{cid}-{d}.apng';clipout.parent.mkdir(exist_ok=True)
   def chunk(typ,data):return struct.pack('>I',len(data))+typ+data+struct.pack('>I',zlib.crc32(typ+data)&0xffffffff)
   def chunks(blob):
    off=8
    while off<len(blob):
     ln=struct.unpack('>I',blob[off:off+4])[0];yield blob[off+4:off+8],blob[off+8:off+8+ln];off+=ln+12
   first=list(chunks(frames[0].read_bytes()));blob=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',first[0][1]);blob+=b''.join(chunk(t,d) for t,d in first[1:] if t not in [b'IDAT',b'IEND',b'acTL',b'fcTL',b'fdAT']);blob+=chunk(b'acTL',struct.pack('>II',12,0 if c['loop'] else 1));seq=0
   for index,frame in enumerate(frames):
    blob+=chunk(b'fcTL',struct.pack('>IIIIIHHBB',seq,384,640,0,0,1,12,0,0));seq+=1
    for typ,data in chunks(frame.read_bytes()):
     if typ==b'IDAT':
      if index==0:blob+=chunk(b'IDAT',data)
      else:blob+=chunk(b'fdAT',struct.pack('>I',seq)+data);seq+=1
   blob+=chunk(b'IEND',b'');clipout.write_bytes(blob)
   blob=clipout.read_bytes();off=8;delays=[];plays=None;counts=None
   while off<len(blob):
    ln=struct.unpack('>I',blob[off:off+4])[0];typ=blob[off+4:off+8];data=blob[off+8:off+8+ln]
    if typ==b'acTL':counts,plays=struct.unpack('>II',data)
    if typ==b'fcTL':num,den=struct.unpack('>HH',data[20:24]);delays.append([num,den])
    off+=ln+12
   assert counts==12 and len(delays)==12 and all(num/den==1/12 for num,den in delays),(clipout,delays)
   b['previews'][f'{cid}-{d}']=rel(clipout)
   write(clipout.with_suffix('.json'),{'clip':cid,'direction':d,'frames':12,'fps':12,'loop':c['loop'],'APNGplays':plays,'frameDelayFractions':delays,'sha256':sha(clipout),'sourceFrames':[sha(p) for p in frames]})
  sp=base/'contact-sheets'/f'{cid}-all48.png';sheet.save(sp);b['previews'][f'all48-{cid}']=rel(sp)
  b['resources'][f'measurements-{runtime}.json.gz']=rel(base/'measurements.json.gz')
  b['resources'][f'body-identity-{runtime}.json']=rel(base/'body-identity.json')
  nr=base/'native-records';nr.mkdir(exist_ok=True);write(nr/'camera.json',audit['camera']);shutil.copyfile(res/('runtime-rig.json' if runtime else 'main-rig.json'),nr/'rig.json')
  asset=json.loads((OBJ/'inputs/source-assetRecord.json').read_text());asset['scale']=2;asset['clips']={k:{x:c[x] for x in ['frames','fps','loop']} for k,c in rig['clips'].items()};asset['artStyle']={'refinement':'warm soft native round04','lighting':'one centered overhead + four equal cardinal area fills; neutral warm world; no ground geometry or directional ground shadows','material':'native Principled broad rounded geometry'};write(nr/'asset.json',asset)
  b['nativeRecords']={'camera':rel(nr/'camera.json'),'assetRecord':rel(nr/'asset.json'),'rig':rel(nr/'rig.json')}
 return b
main=bundle();runtime=bundle(True)
# Full-size fixed-root background/stool review composites; sprites are never fitted or moved.
pre=OUT/'previews';pre.mkdir(exist_ok=True);backgrounds={'light':'#eee9df','gray':'#70757a','dark':'#20242a'}
for kind,clip,base in [('seated','seated-wait',OUT),('cucumber','eat',OUT),('salmon','eat-salmon',OUT/'runtimeVariants'),('empty','seated-wait-empty',OUT/'runtimeVariants')]:
 for bg,col in backgrounds.items():
  panel=Image.new('RGBA',(384*4,704),col)
  for j,d in enumerate(['N','E','S','W']):
   stool=Image.open(context/f'stool-blue-{d}.png').convert('RGBA');actor=Image.open(base/'frames'/f'{clip}-{d}'/'000.png').convert('RGBA');cell=Image.new('RGBA',(384,704),col);cell.alpha_composite(stool,(0,0));cell.alpha_composite(actor,(0,0));panel.alpha_composite(cell,(384*j,0));ImageDraw.Draw(panel).text((384*j+12,12),f'{kind} {d} / fixed shared root',fill='white' if bg!='light' else 'black')
  p=pre/f'{kind}-stool-{bg}.png';panel.convert('RGB').save(p);main['previews'][f'{kind}-stool-{bg}']=rel(p)
for bg,col in backgrounds.items():
 p=pre/f'four-view-{bg}.png';im=Image.new('RGBA',(384*4,640),col)
 for i,d in enumerate(['N','E','S','W']):im.alpha_composite(Image.open(OUT/'frames'/f'stand-{d}'/'000.png').convert('RGBA'),(384*i,0))
 im.convert('RGB').save(p);main['previews'][f'four-view-{bg}']=rel(p)
main['previews']['four-view-sheet']=main['previews']['four-view-gray']
repeat=Image.new('RGBA',(6*192,2*320),'#ded7c8')
for row in range(2):
 for i,d in enumerate(['N','E','S','W','S','E']):repeat.alpha_composite(Image.open(OUT/'frames'/f'stand-{d}'/'000.png').convert('RGBA').resize((192,320),Image.Resampling.LANCZOS),(i*192,row*320))
repeat.convert('RGB').save(pre/'repeated.png');main['previews']['repeated']=rel(pre/'repeated.png')
# Same-input empirical GPU repeatability; no universal pixel identity assumption.
a=Image.open(OUT/'repeatability-0.png').convert('RGBA');b=Image.open(OUT/'repeatability-1.png').convert('RGBA');diff=ImageChops.difference(a,b);hist=diff.histogram();mx=max(max(channel.getextrema()) for channel in diff.split());changed=sum(1 for p in diff.getdata() if any(p));repeatability={'sameSavedProject':sha(HERE/'round-04.blend'),'sameNativePose':'stand-S frame1','renders':[sha(OUT/f'repeatability-{i}.png') for i in range(2)],'maximumChannelDifference8bit':mx,'changedPixels':changed,'measuredPixelTolerance':mx,'note':'Empirical same-input repeat; no source body RGB equality requirement.'};write(OUT/'repeatability.json',repeatability)
mi=json.loads((OUT/'body-identity.json').read_text());ri=json.loads((OUT/'runtimeVariants/body-identity.json').read_text());identity={'main':mi,'runtime':ri,'identicalNativeBody':mi['nativeBodySHA256']==ri['nativeBodySHA256']};assert identity['identicalNativeBody'];write(OUT/'body-identity-comparison.json',identity)
# Actual browser playback surface uses the approved candidate atlas rectangles at exactly 12fps.
entries=[]
for label,bu in [('Catalog',main),('Runtime',runtime)]:
 for a in bu['atlases']:entries.append({'group':label,'clip':a['clip'],'direction':a['direction'],'loop':a['loop'],'path':str((OBJ/a['path']).relative_to(OUT))})
write(OUT/'playback-index.json',entries)
html=(HERE/'review_template_round04.html').read_text().replace('ENTRIES',json.dumps(entries));(OUT/'review.html').write_text(html);main['previews']['browser-playback']=rel(OUT/'review.html')
resources={}
for p in HERE.rglob('*'):
 if p.is_file() and ('__pycache__' not in p.parts) and p.suffix not in ['.log','.blend1'] and ('resources' in p.parts or p.name in ['original-backup.blend','round-04.blend','round-04-runtime.blend','build_round04.py','capture_round04.py','evidence_round04.py','package_round04.py','review_template_round04.html','inspect_original.py','independent-observations.json','native-original-inspection.json','build-main-round04.json','build-runtime-round04.json']):
  resources[str(p.relative_to(HERE))]=rel(p)
# Main includes all native/runtime dependency bytes for one approval packet.
main['resources'].update(resources);runtime['resources']={k:v for k,v in resources.items() if 'runtime' in k or k.endswith(('native_actions.py','dish-salmon.png'))};runtime['resources']['body-identity']=rel(OUT/'runtimeVariants/body-identity.json')
for base,bu in [(OUT,main),(OUT/'runtimeVariants',runtime)]:
 for p in base.rglob('*.json'):
  if p.name not in ['delivery.snapshot.json']:bu['resources'][str(p.relative_to(base))]=rel(p)
complete={'asset':'customer-rosa','round':'round-04','nativeValidation':rel(OUT/'validation.json'),'sourceValidations':[rel(OUT/'validation.json'),rel(OUT/'runtimeVariants/validation.json')],'allNativeChecksPassed':all(json.loads((OBJ/p).read_text())['allChecksPassed'] for p in [main['validation'],runtime['validation']]),'mainFrames':len(main['rawFrames']),'mainAtlases':len(main['atlases']),'mainClips':40,'runtimeFrames':len(runtime['rawFrames']),'runtimeAtlases':len(runtime['atlases']),'runtimeClips':8,'totalFrames':576,'totalClips':48,'atlasWholeFramePixelCopies':True,'APNGexact12fpsFractionsVerified':True,'identicalMainRuntimeNativeBody':identity['identicalNativeBody'],'repeatability':repeatability,'resourcesPacked':True,'candidateStatus':'ready for independent review; browser evidence pending'};write(OUT/'complete-validation.json',complete)
main['resources']['complete-validation.json']=rel(OUT/'complete-validation.json');main['resources']['body-identity-comparison.json']=rel(OUT/'body-identity-comparison.json');main['resources']['repeatability.json']=rel(OUT/'repeatability.json');main['resources']['playback-index.json']=rel(OUT/'playback-index.json')
delivery=dict(schemaVersion=1,asset='customer-rosa',round='round-04',pipeline='native-3d',status='candidate-ready-for-independent-review',**main);delivery['heroes']={d:rel(OUT/'frames'/f'stand-{d}'/'000.png') for d in ['N','E','S','W']};delivery['runtimeVariants']=runtime;delivery['validation']=rel(OUT/'complete-validation.json');delivery['representation']={'body':'editable native Blender meshes/materials under the unchanged original 25-bone rig and actions','foods':'separate exact approved canonical packed 2D rasters with one frozen semantic full-UV mapping each; original .6 constant depth retained','reviewContexts':'independently assembled exact sealed stool-blue sprites and full registered native Rosa frames; no fitting or asset retouch'};delivery['notes']=['480 main native frames / 40 original-layout atlases / 40 actual exact12fps APNG clips; separate runtime96/8/8, no added catalogstates.','Source rest/actions/foot-hand-seat-mouth/foodroot trajectories retained. Native body topology, materials and construction intentionally refined.','Root coordinator seals this immutable numbered round and writes approval only after independent judge review.'];write(OBJ/'delivery-round04.json',delivery)
print(json.dumps(complete,indent=2))
