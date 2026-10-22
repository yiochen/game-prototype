from pathlib import Path
from PIL import Image,ImageChops,ImageStat,ImageDraw
import json,hashlib,math
O=Path(__file__).parents[3];B=Path(__file__).parents[1];C=O/'candidates/round-02';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def compare(a,b):
 a=a.convert('RGBA');b=b.convert('RGBA');assert a.size==b.size;diff=ImageChops.difference(a,b);return {'samePixels':all(mx==0 for mn,mx in diff.getextrema()),'maxDiff':[mx for mn,mx in diff.getextrema()],'meanDiff':ImageStat.Stat(diff).mean}
def openimage(p):return Image.open(p).convert('RGBA')
recaptures=[{'direction':d,**compare(openimage(B/f'recapture/{d}-003.png'),openimage(C/f'native/{d}/003.png'))}for d in 'NESW']
phase=[];gif=[]
for d in 'NESW':
 atlas=openimage(C/f'atlases/idle-{d}.png');sheet=Image.open(C/f'phases-{d}.png').convert('RGB');g=Image.open(C/f'idle-{d}.gif');times=[];decoded=[];previewErrors=[]
 for i in range(12):
  native=openimage(C/f'native/{d}/{i:03}.png');published=openimage(C/f'frames/idle/{d}/{i:03}.png');resized=native.resize((384,768),Image.Resampling.LANCZOS);packed=atlas.crop(((i%6)*384,(i//6)*768,(i%6+1)*384,(i//6+1)*768));back=Image.new('RGBA',published.size,(35,55,69,255));back.alpha_composite(published);back=back.convert('RGB');panel=sheet.crop(((i%4)*384,(i//4)*800+28,(i%4+1)*384,(i//4)*800+28+768));g.seek(i);times.append(g.info.get('duration'));gf=g.convert('RGB');decoded.append(gf);previewErrors.append(compare(gf,back))
  alpha=published.getchannel('A');edge=max(alpha.crop((0,0,384,1)).getextrema()[1],alpha.crop((0,767,384,768)).getextrema()[1],alpha.crop((0,0,1,768)).getextrema()[1],alpha.crop((383,0,384,768)).getextrema()[1])
  phase.append({'direction':d,'index':i,'nativeToPublished':compare(resized,published),'atlasCell':compare(packed,published),'phaseSheetCell':compare(back,panel),'edgeAlpha':edge,'nativeBounds':native.getchannel('A').getbbox(),'publishedBounds':alpha.getbbox()})
 closure=compare(openimage(C/f'native/{d}/000.png'),openimage(C/f'closure/{d}/012.png'))
 # Decode every actual GIF frame visibly, retaining delay labels; actual browser display sequence is separate.
 ps=Image.new('RGB',(4*192,3*408),(35,55,69));dr=ImageDraw.Draw(ps)
 for i,im in enumerate(decoded):
  ps.paste(im.resize((192,384),Image.Resampling.LANCZOS),((i%4)*192,(i//4)*408+24));dr.text(((i%4)*192+5,(i//4)*408+4),f'{d} GIF {i} · {times[i]}ms',fill='white')
 ps.save(B/f'gif-decoded-{d}.png')
 gif.append({'direction':d,'gifPath':f'candidates/round-02/idle-{d}.gif','frames':g.n_frames,'delaysMs':times,'totalMs':sum(times),'loop':g.info.get('loop'),'maxTimingErrorMs':max(abs(t-1000/12)for t in times),'previewQuantizationMaxChannelDifference':max(max(r['maxDiff'])for r in previewErrors),'previewQuantizationMaxMean':max(max(r['meanDiff'])for r in previewErrors),'nativeClosure':closure,'decodedUniquePublishedFrames':len({openimage(C/f'frames/idle/{d}/{i:03}.png').tobytes()for i in range(12)})})
consumer=[]
for mode in ('chromium','shell'):
 for width in (1200,390):
  for kind in ('hero','context','repeat'):
   for suffix in ('','-native'):
    name=f'{mode}-{width}-{kind}{suffix}.png';consumer.append({'path':f'browser/{name}',**compare(openimage(B/'browser'/name),openimage(C/'browser'/name))})
# Inspect real playback screen samples across three successive loops, preserving full logical canvases.
pb=json.loads((B/'playback-observation.json').read_text());playback=[]
for row in range(3):
 ps=Image.new('RGB',(4*192,4*408),(35,55,69));draw=ImageDraw.Draw(ps)
 for cell,n in enumerate([row*12+0,row*12+3,row*12+6,row*12+9]):
  r=pb['records'][n];im=Image.open(O/r['path']).convert('RGB');ps.paste(im,(0,cell*408+24));draw.text((4,cell*408+4),f"Actual browser GIFs N/E/S/W · sample{n} · t{r['beforeMs']:.1f}..{r['afterMs']:.1f}ms",fill='white')
 p=B/f'playback-observed-loop-{row}.png';ps.save(p);playback.append(str(p.relative_to(O)))
result={'candidatePacketSHA256':sha(C/'packet.json'),'savedSourceRecaptures':recaptures,'all48FullFrameAndAtlasAndPhaseSheetChecks':phase,'gifPlayback':gif,'actualBrowserPlaybackSheets':playback,'consumerReplay':consumer,'exactHelpers':[{'path':str((B/'resources/consumer'/n).relative_to(O)),'sha256':sha(B/'resources/consumer'/n)}for n in ('sprite-layout.js','world-sprite-raster.js')],'interpretation':'GIF previews use12 actual ordered frames on slate and centisecond80/80/90 timing totalling1second. Palette quantization is diagnostic only. Actual PNG publication is exact whole-frame LANCZOS and atlas copy. Actual browser playback display samples are separate from decoded source phase evidence.'}
(B/'raster-proof.json').write_text(json.dumps(result,indent=2)+'\n')
print('recaptures',recaptures);print('native/published/atlas/sheet',all(r['nativeToPublished']['samePixels']and r['atlasCell']['samePixels']and r['phaseSheetCell']['samePixels']and r['edgeAlpha']==0 for r in phase));print('consumerexact',sum(r['samePixels']for r in consumer),'of',len(consumer),'maxdiff',max(max(r['maxDiff'])for r in consumer));print('GIF',gif)
