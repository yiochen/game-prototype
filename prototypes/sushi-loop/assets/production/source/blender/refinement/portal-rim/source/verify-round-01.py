"""Measured native/consumer evidence; no art approval and no shared gate edits."""
from pathlib import Path
from PIL import Image,ImageChops,ImageStat,ImageDraw
import hashlib,json,math,subprocess,io
S=Path(__file__).resolve().parent;C=S.parent/'candidates/round-01'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,indent=2)+'\n')
def difference(a,b):
    assert a.size==b.size
    d=ImageChops.difference(a,b);px=list(d.get_flattened_data())
    return {'size':list(a.size),'changedPixelsRGBA':sum(any(v) for v in px),'changedPixelsRGB':sum(any(v[:3]) for v in px),'maxPerChannel':[v[1] for v in d.getextrema()],'meanAbsRGBA':ImageStat.Stat(d).mean,'alphaExact':d.getchannel('A').getextrema()[1]==0}
native=json.loads((C/'native-measurements.json').read_text());pv=json.loads((C/'pixel-validation.json').read_text());modes={m:json.loads((C/f'consumer-{m}.json').read_text()) for m in ['full-chromium','headless-shell']}
out={'asset':'portal-rim','round':'round-01','approval':False,'layers':'Native Blender geometry/shading and whole-canvas publication; independent native nearest canvas; actual unchanged-helper native browser canvas; ordinary complete-canvas CSS display. These layers are distinguished, never repaired to match.'}
out['allPhaseNativeChecks']={}
for f,rs in native['frames'].items():
    stones=['portal_rim__support_left','portal_rim__support_right']
    out['allPhaseNativeChecks'][f]={'samplesIncludingClosure':len(rs),'captureCount':len(rs)-1,'rootRotationRadians':rs[0]['rootRotationZ'],'canonicalRawBounds':[[min(r['rawCanonicalSBounds'][0][j] for r in rs) for j in range(3)],[max(r['rawCanonicalSBounds'][1][j] for r in rs) for j in range(3)]],'canonicalEvaluatedBounds':[[min(r['evaluatedCanonicalSBounds'][0][j] for r in rs) for j in range(3)],[max(r['evaluatedCanonicalSBounds'][1][j] for r in rs) for j in range(3)]],'budgetEveryPhase':all(r['canonicalBudgetPass'] for r in rs),'stableRootMatrix':all(r['rootMatrix']==rs[0]['rootMatrix'] for r in rs),'stableSupports':{n:all(r['objects'][n]['evaluatedGeometrySHA256']==rs[0]['objects'][n]['evaluatedGeometrySHA256'] for r in rs) for n in stones},'finiteGroundSectionAreas':{n:[r['finiteGroundContacts'][n]['evaluated']['area'] for r in rs] for n in stones},'connectionWitnessesAllPhases':all(all(w['allInside'] for w in r['connectionInteriorWitnesses']) for r in rs),'entryCenterAllPhases':[r['entryOpening']['logicalRelativeToRoot'] for r in rs],'entryNearestSurfaceRange':[min(r['entryOpening']['nearestEvaluatedSurfaceDistance'] for r in rs),max(r['entryOpening']['nearestEvaluatedSurfaceDistance'] for r in rs)],'openCenterEveryPhase':all(r['entryOpening']['openCenter'] for r in rs),'closure':native['loopClosure'][f]}
out['nativeVsConsumerCanvases']={};out['browserModeNativeCanvasComparison']={};out['browserPlayback']={}
for mode,data in modes.items():
    rows=[]
    for phase in data['staticFrameRecords']:
        for r in phase['records']:
            if r['displayScale']!=1:continue
            frame=Image.open(C/'published/idle'/r['direction']/f"{phase['frame']:03d}.png").convert('RGBA');plan=r['plan'];expected=Image.new('RGBA',(plan['width'],plan['height']))
            # The helper position is exactly integral on the native scale2 grid.
            x=round((r['sprite']['x']-plan['x'])*plan['scale']);y=round((r['sprite']['y']-plan['y'])*plan['scale']);expected.paste(frame,(x,y))
            actual=Image.open(C/r['canvasPath']).convert('RGBA');diff=difference(expected,actual)
            opaque=frame.getchannel('A').point(lambda a:255 if a==255 else 0);actualcell=actual.crop((x,y,x+384,y+768));rgbdiff=ImageChops.difference(frame,actualcell).convert('RGB');opaqueDiff=ImageChops.multiply(rgbdiff,Image.merge('RGB',(opaque,opaque,opaque)))
            diff['opaqueSourcePixelsRGBExact']=not opaqueDiff.getbbox();rows.append({'direction':r['direction'],'frame':phase['frame'],'nativePlan':plan,'sourcePublished':f"published/idle/{r['direction']}/{phase['frame']:03d}.png",'actualCanvas':r['canvasPath'],'comparison':diff})
    out['nativeVsConsumerCanvases'][mode]={'all48':rows,'allAlphaExact':all(r['comparison']['alphaExact'] for r in rows),'allOpaqueSourcePixelsRGBExact':all(r['comparison']['opaqueSourcePixelsRGBExact'] for r in rows),'maxMeanRGBA':[max(r['comparison']['meanAbsRGBA'][j] for r in rows) for j in range(4)],'interpretation':'Native canvas nearest composition matches actual alpha and opaque source pixels. Nonzero RGB differences at translucent edges are recorded honestly; premultiplication/quantization is a plausible browser-layer explanation, not isolated experimentally. No pixels were changed.'}
    play=data['playback'];order=[r['frame'] for r in play];wraps=[i for i in range(1,len(order)) if order[i-1]==11 and order[i]==0]
    out['browserPlayback'][mode]={'browserVersion':data['browserVersion'],'launchOptions':data['launchOptions'],'browserProcessObserved':data['browserProcessObserved'],'viewport':data['viewport'],'deviceScaleFactor':data['deviceScaleFactor'],'playbackTiming':data['playbackTiming'],'events':play,'phaseOrder':order,'rawFramesSequential':all(play[i]['rawFrame']==play[i-1]['rawFrame']+1 for i in range(1,len(play))),'phaseOrderCorrect':all(r['frame']==r['rawFrame']%12 for r in play),'wrapEventIndices':wraps,'atLeast2Point2Seconds':data['playbackTiming']['durationMs']>=2200,'pageErrors':data['errors'],'video':data['video'],'helperHashes':data['helperSHA256']}
    assert out['browserPlayback'][mode]['rawFramesSequential'] and len(wraps)>=2 and out['browserPlayback'][mode]['atLeast2Point2Seconds'] and not data['errors']
    assert data['helperSHA256']=={'world-sprite-raster.js':'570a0d0d788ab65252724da1f0ff7d82a086eab1875ba37ed032dac34acf9545','sprite-layout.js':'099de61830564dbe0de7e3b85ffbeefcc1b80555098ed499b889b50db6074c65'}
for f in ['N','E','S','W']:
    rows=[]
    for i in range(12):
        a=Image.open(C/f'evidence/canvases-full-chromium/{f}/{i:03d}.png').convert('RGBA');b=Image.open(C/f'evidence/canvases-headless-shell/{f}/{i:03d}.png').convert('RGBA');rows.append({'phase':i,'decodedRGBAExact':a.tobytes()==b.tobytes()})
    out['browserModeNativeCanvasComparison'][f]=rows
out['browserModeCSSScreenshotResiduals']={}
for bg in ['light','gray','dark']:
    a=Image.open(C/'evidence'/f'consumer-full-chromium-{bg}.png').convert('RGBA');b=Image.open(C/'evidence'/f'consumer-headless-shell-{bg}.png').convert('RGBA');out['browserModeCSSScreenshotResiduals'][bg]=difference(a,b)
out['screenshotResidualInterpretation']='Both modes use the same exact native canvas results; actual CSS screenshots may differ in browser display/text compositing. Nonzero differences are retained, not treated as source changes or repaired. Pillow logical sheets do not certify CSS pixel equivalence.'
# Full-registered native wrap sequence, including the actual atlas 11->0 boundary.
wrap=Image.new('RGB',(768,1632),(128,128,128));draw=ImageDraw.Draw(wrap)
for row,f in enumerate(['N','E','S','W']):
    for col,i in enumerate([10,11,0,1]):
        im=Image.open(C/'published/idle'/f/f'{i:03d}.png').convert('RGBA').resize((192,384),Image.Resampling.NEAREST);x=col*192;y=row*408;wrap.paste(im,(x,y),im);draw.text((x+4,y+386),f'{f} idle {i:02d}',fill='white')
wrap.save(C/'evidence/motion-wrap-sheet.png')
# Actual finite ground polygons. Dashed placement cell is context, not an opaque floor rule.
contact=Image.new('RGB',(1536,420),'#808080');draw=ImageDraw.Draw(contact)
for j,f in enumerate(['N','E','S','W']):
    cx=j*384+192;cy=192;scale=220
    draw.rectangle((cx-110,cy-110,cx+110,cy+110),outline='#bbbbbb',width=1)
    draw.line((cx-170,cy,cx+170,cy),fill='#a0a0a0');draw.line((cx,cy-170,cx,cy+170),fill='#a0a0a0')
    for n,c in native['frames'][f][0]['finiteGroundContacts'].items():
        poly=[(cx+p[0]*scale,cy-p[1]*scale) for p in c['evaluated']['polygonXY']];draw.polygon(poly,fill='#335c91',outline='#8dc9ff');draw.text((cx-175,370+(15 if 'right' in n else 0)),f"{n.split('__')[1]} area {c['evaluated']['area']:.5f}",fill='white')
    draw.ellipse((cx-4,cy-4,cx+4,cy+4),fill='#ff5555');draw.text((cx-165,398),f'{f}: Z0 sections; square = placement context',fill='white')
contact.save(C/'evidence/ground-contact-map.png')
out['videoInspection']={}
for mode,data in modes.items():
    video=C/data['video']['path'];info=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','quiet','-print_format','json','-show_format','-show_streams',str(video)]));write(C/f'video-{mode}-info.json',info)
    duration=float(info['format']['duration']);play=data['playbackTiming'];playstart=play['startPerformanceMs']/1000
    samples=[];sheet=Image.new('RGB',(4*420,2*414),(128,128,128));d=ImageDraw.Draw(sheet)
    # Page performance start time is an approximate seek guide; visible video status and event trace establish phase order.
    for k,elapsed in enumerate([.84,.92,1.00,1.09,1.84,1.92,2.00,2.09]):
        timestamp=min(duration-.03,playstart+elapsed)
        png=subprocess.check_output(['/opt/homebrew/bin/ffmpeg','-v','error','-ss',str(timestamp),'-i',str(video),'-frames:v','1','-vf','scale=420:390','-f','image2pipe','-vcodec','png','-'])
        im=Image.open(io.BytesIO(png)).convert('RGB');x=(k%4)*420;y=(k//4)*414;sheet.paste(im,(x,y));d.text((x+4,y+392),f'{mode} video {timestamp:.3f}s | play approx {elapsed:.2f}s',fill='white');samples.append({'videoTimestampSeconds':timestamp,'approxPlaybackSeconds':elapsed})
    sheet.save(C/f'evidence/playback-{mode}-sheet.png')
    out['videoInspection'][mode]={'videoDurationSeconds':duration,'sheet':f'evidence/playback-{mode}-sheet.png','samples':samples,'limits':'Video sample times selected approximately from page performance start time; browser recording origin can differ slightly. Visible status timestamps identify the actual displayed phase. Sampling is inspection support, not complete phase evidence alone. Complete48 native/canvas phase files and sequential actual12fps event traces are separately retained. Original videos are unchanged.'}
write(C/'verification-metrics.json',out)
print(json.dumps({'nativeFailures':native['failures'],'uniqueFrames':{f:pv['facings'][f]['uniqueDecodedFrames'] for f in pv['facings']},'nativeAlphaExact':{m:out['nativeVsConsumerCanvases'][m]['allAlphaExact'] for m in modes},'nativeCanvasModeExact':all(r['decodedRGBAExact'] for rs in out['browserModeNativeCanvasComparison'].values() for r in rs),'CSSResiduals':out['browserModeCSSScreenshotResiduals'],'playbackDuration':{m:out['browserPlayback'][m]['playbackTiming']['durationMs'] for m in modes}},indent=2))
