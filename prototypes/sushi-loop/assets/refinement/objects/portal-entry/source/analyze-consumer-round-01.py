"""Keep native-canvas, browser-mode and CSS/reference residuals separate and honest."""
from pathlib import Path
from PIL import Image,ImageChops,ImageStat,ImageDraw
import json,subprocess,hashlib
H=Path(__file__).resolve().parent;O=H.parent;C=O/'candidates/round-01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
report=json.loads((C/'consumer-report.json').read_text());pairs=[];css=[];videos=[]
for x,y in zip(report['browserModes'][0]['screenshots'],report['browserModes'][1]['screenshots']):
    a=Image.open(C/'consumer'/x['file']).convert('RGBA');b=Image.open(C/'consumer'/y['file']).convert('RGBA');d=ImageChops.difference(a,b)
    pairs.append({'first':x['file'],'second':y['file'],'size':list(a.size),'decodedExact':a.tobytes()==b.tobytes(),'maxRGBA':[v[1] for v in d.getextrema()],'meanRGBA':ImageStat.Stat(d).mean})
for mode in report['browserModes']:
    for item in mode['screenshots']:
        if 'all48' in item['file']:continue
        actual=Image.open(C/'consumer'/item['file']).convert('RGB');scale=item['evidence']['scale'];bg=item['evidence']['bg'];w=int(192*scale);hh=int(384*scale)
        stats=[]
        for row,index in enumerate((0,5,11)):
            for col,direction in enumerate('NESW'):
                # Independent whole published-canvas LANCZOS reference. Actual consumer
                # uses the native nearest shared canvas and browser CSS filter; this
                # reference deliberately does not pretend to be its exact raster.
                f=Image.open(C/'frames/enter'/direction/f'{index:03d}.png').convert('RGBA').resize((w,hh),Image.Resampling.LANCZOS)
                expected=Image.new('RGB',(w,hh),bg);expected.paste(f,(0,0),f)
                x=col*w;y=row*(hh+20)+20;a=actual.crop((x,y,x+w,y+hh));diff=ImageChops.difference(a,expected)
                stats.append({'direction':direction,'index':index,'browserViewportRect':[x,y,w,hh],'sourcePath':f'candidates/round-01/frames/enter/{direction}/{index:03d}.png','maxRGB':[v[1] for v in diff.getextrema()],'meanRGB':ImageStat.Stat(diff).mean,'changedPixelBounds':list(diff.getbbox()) if diff.getbbox() else None})
        css.append({'browserMode':mode['id'],'screenshot':item['file'],'scale':scale,'background':bg,'referenceMethod':'Independent whole published fullframe Pillow LANCZOS resize and alpha composition. Actual browser: shared native nearest composition THEN whole-canvas CSS filtering with guard pixels and fractional placement. Nonzero residuals are reported, never repaired or asserted to be exact equivalence.','frames':stats})
    video=C/'consumer'/mode['video'];probe=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(video)],text=True))
    videos.append({'browserMode':mode['id'],'path':str(video.relative_to(O)),'sha256':sha(video),'ffprobe':probe,'actualFullPhaseCoverage':mode['playbackCoverage'],'terminalCurrentFrames':mode['playbackFinal']['currentFrames'],'terminalWallSeconds':mode['playbackFinal']['elapsed']})
sheet=Image.new('RGB',(6*195,2*442),'#777777');draw=ImageDraw.Draw(sheet)
for row,mode in enumerate(report['browserModes']):
    for i,item in enumerate(mode['playback']):
        im=Image.open(C/'consumer'/item['file']).convert('RGB').resize((195,422),Image.Resampling.LANCZOS);sheet.paste(im,(i*195,row*442));draw.text((i*195+2,row*442+423),f"{mode['id']} {item['evidence']['elapsed']:.3f}s",fill='white')
sheet.save(C/'previews/playback-samples-sheet.png')
http=(C/'logs/consumer-http.log').read_text();notfound=[line for line in http.splitlines() if '404' in line]
out={'asset':'portal-entry','round':'round-01','pathBase':'object-root','browserModePairs':pairs,'cssVersusIndependentNativeFullframeReference':css,'nativeCanvasReadbackSummary':[{'id':m['id'],'records':len(m['nativeCanvasReadback']),'allAlphaExact':all(r['alphaExact'] for r in m['nativeCanvasReadback']),'maxRGBA':[max(r['maxRGBA'][k] for r in m['nativeCanvasReadback']) for k in range(4)],'opaqueMaxRGBA':[max(r['opaqueMaxRGBA'][k][1] for r in m['nativeCanvasReadback']) for k in range(4)],'meaning':'Opaque pixels and alpha match native nearest composition exactly; non-opaque RGB readback has browser premultiplication quantization. No RGB/alpha repair. Full per-frame values in consumer-report.json.'} for m in report['browserModes']],'playbackVideos':videos,'consoleErrors':[{'mode':m['id'],'errors':m['errors']} for m in report['browserModes']],'http404LogLines':notfound,'scope':'Both actual Chromium153 launch modes, actual DPR1/executables/options/version/errors, all48 current-consumer native-canvas readbacks and all48sheet, all0/5/11facings at logical/.5phone on lightgraydark, real requestAnimationFrame12fps one-shot followed by terminalhold and retained videos. Does not certify full product/Godot/device integration.'}
p=C/'consumer-analysis.json';assert not p.exists();p.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'browserModePairs':[(p['first'],p['decodedExact'],p['maxRGBA']) for p in pairs],'nativeCanvas':out['nativeCanvasReadbackSummary'],'http404':notfound,'videoFrames':[(v['browserMode'],v['ffprobe']['streams'][0].get('nb_read_frames')) for v in videos]}))
