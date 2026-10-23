from PIL import Image,ImageDraw,ImageChops
import numpy as np,pathlib,json,hashlib,shutil
P=pathlib.Path(__file__).resolve().parents[1];O=P/'candidates/round-08';V=json.load(open(O/'validation.json'));H=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
for sub in ['atlases','assemblies','comparisons','previews','filtered-game-scale']:(O/sub).mkdir(exist_ok=True)
BG={'light':(230,233,228),'gray':(120,125,128),'dark':(24,30,36)}
def composite(im,bg):
 x=Image.new('RGBA',im.size,(*bg,255));x.alpha_composite(im);return x.convert('RGB')
def stats(a,b,rois):
 aa=np.array(a,dtype=float);bb=np.array(b,dtype=float);alpha=abs(aa[:,:,3]-bb[:,:,3]);rgb=abs(aa[:,:,:3]*aa[:,:,3:]/255-bb[:,:,:3]*bb[:,:,3:]/255);mask=(aa[:,:,3]>0)|(bb[:,:,3]>0)
 def region(x,y,w,h):
  ma=mask[y:y+h,x:x+w];ad=alpha[y:y+h,x:x+w];rd=rgb[y:y+h,x:x+w];return {'alphaMax':float(ad.max()),'alphaMean':float(ad[ma].mean()) if ma.any() else 0,'premultipliedRGBMax':float(rd.max()),'premultipliedRGBMean':float(rd[ma].mean()) if ma.any() else 0,'alphaDifferentPixels':int(np.count_nonzero(ad)),'rgbOver8Pixels':int(np.count_nonzero(rd.max(axis=2)>8)),'rect':[x,y,w,h]}
 return {'full':region(0,0,a.width,a.height),'joins':[region(*r) for r in rois]},rgb,alpha
atlases=[];preview={};records=[];filtered=[]
for d in ['N','E','S','W']:
 frames=[Image.open(O/'frames'/f'running-{d}-{i:02d}.png').convert('RGBA') for i in range(25)]
 atlas=Image.new('RGBA',(2304,2816));rects=[]
 for i,im in enumerate(frames[:24]):
  x=(i%6)*384;y=(i//6)*704;atlas.paste(im,(x,y));rects.append({'index':i,'x':x,'y':y,'width':384,'height':704})
 ap=O/'atlases'/f'running-{d}.png';atlas.save(ap)
 assert all(ImageChops.difference(atlas.crop((r['x'],r['y'],r['x']+384,r['y']+704)),frames[i]).getbbox() is None for i,r in enumerate(rects))
 atlases.append({'clip':'running','direction':d,'path':str(ap),'sha256':H(ap),'columns':6,'rows':4,'size':[2304,2816],'rects':rects})
 sheet=Image.new('RGB',(6*192,4*376),BG['light']);draw=ImageDraw.Draw(sheet)
 for i,im in enumerate(frames[:24]):
  thumb=composite(im,BG['light']).resize((192,352),Image.Resampling.BOX);x=i%6*192;y=i//6*376;sheet.paste(thumb,(x,y+24));draw.text((x+6,y+6),f'{d} / running {i:02d}',fill=(26,35,40))
 cp=O/'previews'/f'all24-{d}.png';sheet.save(cp);preview[f'all24-{d}']=str(cp)
 # Lossless APNG has exact 12fps duration and two complete cycles, from unmodified actual native frames.
 lp=O/'previews'/f'running-{d}.png';pf=[composite(im,BG['light']).resize((192,352),Image.Resampling.BOX) for im in frames[:24]];pf[0].save(lp,save_all=True,append_images=pf[1:]+pf,loop=0,duration=1000/12,disposal=0,blend=0);preview[f'running-{d}']=str(lp)
 offsets=V['nativeAssemblyContract']['independentPixelOffsets'][d]
 rois=[[320,496,256,42],[320,752,256,42]] if d in ['N','S'] else [[316,496,8,360],[572,496,8,360]]
 pair_animation=[];filter_animation=[]
 for i,im in enumerate(frames):
  native=Image.open(O/'native-runs'/f'native-{d}-{i:02d}.png').convert('RGBA');assembled=Image.new('RGBA',(896,1216))
  for pos in offsets:assembled.alpha_composite(im,tuple(pos))
  path=O/'assemblies'/f'assembled-{d}-{i:02d}.png';assembled.save(path);st,rgb,alpha=stats(native,assembled,rois);st.update(direction=d,index=i,native=str(O/'native-runs'/f'native-{d}-{i:02d}.png'),assembled=str(path),nativeSHA256=H(O/'native-runs'/f'native-{d}-{i:02d}.png'),assembledSHA256=H(path));records.append(st)
  diff=np.zeros((1216,896,4),dtype='uint8');diff[:,:,:3]=np.clip(rgb*8,0,255).astype('uint8');diff[:,:,3]=255;dp=O/'comparisons'/f'RGBx8-{d}-{i:02d}.png';Image.fromarray(diff).save(dp)
  Image.fromarray(np.clip(alpha*8,0,255).astype('uint8')).save(O/'comparisons'/f'alpha-difference-x8-{d}-{i:02d}.png')
  # Scale EACH source sprite first using bilinear sampling, THEN alpha-compose at exact logical roots.
  logical_im=im.resize((192,352),Image.Resampling.BILINEAR);logical=Image.new('RGBA',(448,608))
  for x,y in offsets:logical.alpha_composite(logical_im,(x//2,y//2))
  logicalpath=O/'filtered-game-scale'/f'individual-bilinear-first-{d}-{i:02d}.png';logical.save(logicalpath)
  nativeLogical=native.resize((448,608),Image.Resampling.BILINEAR);nativeLogical.save(O/'filtered-game-scale'/f'native-then-bilinear-{d}-{i:02d}.png')
  r2=[[x//2,y//2,w//2,h//2] for x,y,w,h in rois];fs,frgb,fa=stats(nativeLogical,logical,r2);fs.update(direction=d,index=i,individuallyFiltered=str(logicalpath),comparison='Each raw sprite bilinear resized384x704→192x352 before independent RGBA assembly versus native3 render bilinear resized896x1216→448x608. Pillow bilinear minification approximation; source captures untouched.');filtered.append(fs)
  if i<24:
   pair=Image.new('RGB',(896,608),BG['gray']);pair.paste(composite(native,BG['gray']).resize((448,608),Image.Resampling.BOX),(0,0));pair.paste(composite(assembled,BG['gray']).resize((448,608),Image.Resampling.BOX),(448,0));pair_animation.append(pair)
   fpair=Image.new('RGB',(896,608),BG['gray']);fpair.paste(composite(nativeLogical,BG['gray']),(0,0));fpair.paste(composite(logical,BG['gray']),(448,0));filter_animation.append(fpair)
  # Complete raw RGB/alpha background comparison for all24 times + closure, both joins and full silhouette.
  panel=Image.new('RGB',(448*3,632*2),(245,245,240));draw=ImageDraw.Draw(panel)
  for col,(bn,bg) in enumerate(BG.items()):
   for row,(label,base) in enumerate([('Native3',native),('Independent RGBA3',assembled)]):
    x=col*448;y=row*632;panel.paste(composite(base,bg).resize((448,608),Image.Resampling.BOX),(x,y+24));draw.text((x+8,y+7),f'{d} frame{i:02d} {label} / {bn}',fill=(20,30,35))
  panel.save(O/'comparisons'/f'backgrounds-{d}-{i:02d}.png')
  # Enlarged local join crops include alpha side-by-side; every frame retained.
  patches=[]
  for r in rois:
   x,y,w,h=r
   for base in [native,assembled]:
    crop=base.crop((x,y,x+w,y+h));cc=composite(crop,BG['gray']);alphaimg=Image.merge('RGB',(crop.getchannel('A'),)*3);patches.append((cc,alphaimg))
  width=max(max(a.width,b.width) for a,b in patches)*2;height=sum(max(a.height,b.height) for a,b in patches)*2
  jp=Image.new('RGB',(width*2,height),(245,245,240));y=0
  for cc,al in patches:
   a=cc.resize((cc.width*2,cc.height*2),Image.Resampling.NEAREST);bim=al.resize((al.width*2,al.height*2),Image.Resampling.NEAREST);jp.paste(a,(0,y));jp.paste(bim,(width,y));y+=a.height
  jp.save(O/'comparisons'/f'join-RGB-alpha-enlarged-{d}-{i:02d}.png')
 for name,ims in [('native-vs-assembled',pair_animation),('game-filter-individual-first',filter_animation)]:
  q=O/'previews'/f'{name}-{d}.png';ims[0].save(q,save_all=True,append_images=ims[1:]+ims,loop=0,duration=1000/12,disposal=0,blend=0);preview[f'{name}-{d}']=str(q)
 # Closure check is direct pixel comparison, not just phase metadata.
 closure=ImageChops.difference(frames[0],frames[24]);V.setdefault('loopClosurePixels',{})[d]={'equal':closure.getbbox() is None,'firstSHA256':H(O/'frames'/f'running-{d}-00.png'),'closureSHA256':H(O/'frames'/f'running-{d}-24.png'),'uniqueFrameHashes':len({H(O/'frames'/f'running-{d}-{i:02d}.png') for i in range(24)})}
# Four facings comparison at logical and enlarged.
for sc in [1,2]:
 sh=Image.new('RGB',(192*4*sc,376*sc),BG['light']);dr=ImageDraw.Draw(sh)
 for j,d in enumerate(['N','E','S','W']):
  im=Image.open(O/f'hero-{d}.png').convert('RGBA');thumb=composite(im,BG['light']).resize((192*sc,352*sc),Image.Resampling.BOX if sc==1 else Image.Resampling.NEAREST);sh.paste(thumb,(192*j*sc,24*sc));dr.text((192*j*sc+8,6),d,fill=(20,30,35))
 q=O/'previews'/f'four-facing-{sc}x.png';sh.save(q);preview[f'four-facing-{sc}x']=str(q)
summary={'nativeVsIndependent':records,'individualBilinearFirst':filtered,'method':{'RGB':'Absolute difference of premultiplied sRGB color,0..255; separate alpha errors. Source/full assemblies untouched. Both local join ROIs and all occupied pixels measured.','logicalFilter':'Pillow BILINEAR applied to each full source frame before compositing at half-resolution roots; also native complete run filtered for comparison. This is a software approximation of Godot LINEAR_WITH_MIPMAPS, not an actual Godot screenshot.','rgbDiffDisplay':'Difference maps amplified8x; alpha maps amplified8x; complete background comparisons and enlarged join crops retained for every time/closure.'}}
(O/'continuity-metrics.json').write_text(json.dumps(summary,indent=2));V['continuityMetrics']=str(O/'continuity-metrics.json');V['continuitySummary']={'rawAlphaMax':max(r['full']['alphaMax'] for r in records),'rawRGBMax':max(r['full']['premultipliedRGBMax'] for r in records),'rawJoinRGBMax':max(j['premultipliedRGBMax'] for r in records for j in r['joins']),'rawJoinAlphaMax':max(j['alphaMax'] for r in records for j in r['joins']),'filteredJoinRGBMax':max(j['premultipliedRGBMax'] for r in filtered for j in r['joins']),'filteredJoinAlphaMax':max(j['alphaMax'] for r in filtered for j in r['joins'])};(O/'validation.json').write_text(json.dumps(V,indent=2))
# Review surface uses all actual image sequences and exact12fps timing, with frame scrub and backgrounds.
html='''<!doctype html><meta charset="utf-8"><title>Belt straight N — native round08</title><style>body{margin:24px;background:#d9dcd7;color:#18242c;font:15px system-ui}h1{font-size:20px}section{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}canvas{width:100%;background:#7a8083;border:1px solid #9ba2a1}label{margin-right:20px}.row{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px}img{max-width:100%}small{display:block}</style><h1>Belt straight N · native round08</h1><p>24 actual native frames per facing ·12fps · original root/cardinal convention. Candidate awaits independent judge.</p><label><input id="play" type="checkbox" checked> Play</label><label>Frame <input id="frame" type="range" min="0" max="24" value="0"><b id="value">0</b></label><label>Background <select id="bg"><option value="#7a8083">Gray</option><option value="#e6e9e4">Light</option><option value="#181e24">Dark</option></select></label><h2>Individual native playbacks at logical size</h2><section id="singles"></section><h2>Native3 / independent RGBA3 / each-sprite-bilinear-first</h2><div id="runs"></div><p>Alltime per-frame RGB/alpha measurements: <a href="../continuity-metrics.json">continuity-metrics.json</a>. Each-sprite bilinear preview approximates Godot LINEAR_WITH_MIPMAPS; it is not an actual game screenshot.</p><img src="four-facing-1x.png"><script>
const dirs=['N','E','S','W'],sets={},canvases=[];const root='../';function add(parent,title,kind,d,w,h){let wrap=document.createElement('div');wrap.innerHTML='<small>'+title+'</small>';let c=document.createElement('canvas');c.width=w;c.height=h;wrap.append(c);parent.append(wrap);canvases.push({c,kind,d});}for(let d of dirs){sets[d]={single:[],native:[],assembled:[],filtered:[]};for(let i=0;i<25;i++){let s=String(i).padStart(2,'0');for(let[k,p]of Object.entries({single:`frames/running-${d}-${s}.png`,native:`native-runs/native-${d}-${s}.png`,assembled:`assemblies/assembled-${d}-${s}.png`,filtered:`filtered-game-scale/individual-bilinear-first-${d}-${s}.png` })){let im=new Image();im.src=root+p;sets[d][k].push(im);}}add(document.querySelector('#singles'),d,'single',d,192,352);let section=document.createElement('div');section.className='row';document.querySelector('#runs').append(section);add(section,d+' native3','native',d,448,608);add(section,d+' independent RGBA3','assembled',d,448,608);add(section,d+' each raw sprite bilinear first','filtered',d,448,608);}let t0=performance.now();function tick(now){let f=document.querySelector('#play').checked?Math.floor((now-t0)*12/1000)%24:+document.querySelector('#frame').value;if(document.querySelector('#play').checked)document.querySelector('#frame').value=f;document.querySelector('#value').textContent=f===24?'24 closure':f;for(let v of canvases){let x=v.c.getContext('2d');x.fillStyle=document.querySelector('#bg').value;x.fillRect(0,0,v.c.width,v.c.height);let im=sets[v.d][v.kind][f];if(im.complete)x.drawImage(im,0,0,v.c.width,v.c.height);}requestAnimationFrame(tick);}requestAnimationFrame(tick);</script>'''
(O/'previews/review.html').write_text(html);preview['interactive-native-playback']=str(O/'previews/review.html')
delivery={'project':str(P/'source/round-08.blend'),'recipe':str(P/'source/round-08-recipe.json'),'validation':str(O/'validation.json'),'heroes':{d:str(O/f'hero-{d}.png') for d in ['N','E','S','W']},'rawFrames':json.load(open(O/'raw-frame-records.json')),'atlases':atlases,'previews':preview,'nativeRecords':{'camera':str(O/'camera.json'),'assetRecord':str(O/'assetRecord.json'),'rig':str(O/'rig.json')},'resources':[str(O/'continuity-metrics.json'),str(P/'source/capture_round08.py'),str(P/'source/pack_round08.py')],'status':'candidate-awaiting-independent-judge','candidateRound':8};(P/'delivery.json').write_text(json.dumps(delivery,indent=2));(O/'delivery.json').write_text(json.dumps(delivery,indent=2));print(json.dumps(V['continuitySummary'],indent=2));print('CLOSURE',V['loopClosurePixels'])
