from pathlib import Path
import json,hashlib,subprocess,sys
from PIL import Image,ImageDraw
BASE=Path(__file__).resolve().parents[1];OUT=BASE/'candidates/round-01';m=json.loads((OUT/'frame-atlas-manifest.json').read_text());audit=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for r in m['rawFrames']+m['nativeRawFrames']:
    p=BASE/r['path'];assert sha(p)==r['sha256'];im=Image.open(p).convert('RGBA');bb=im.getchannel('A').getbbox();assert bb is not None and bb[0]>0 and bb[1]>0 and bb[2]<im.width and bb[3]<im.height,(p,bb);audit.append({'path':r['path'],'sha256':r['sha256'],'size':im.size,'alphaBounds':bb,'alphaTouchesBorder':False})
(OUT/'allphase-alpha-audit.json').write_text(json.dumps({'records':audit,'nativeAndPublishedCount':len(audit),'method':'Unmodified saved PNG alpha bounds checked against complete authored canvases. No alpha/RGB repair.'},indent=2)+'\n')
clips=['shimmer','attract','collect','b-shimmer','b-attract','b-collect','c-shimmer','c-attract','c-collect'];dirs=['N','E','S','W'];dest=OUT/'family-playback';dest.mkdir(exist_ok=True);records=[]
for index in range(24):
    canvas=Image.new('RGBA',(3456,2816),(136,142,146,255));draw=ImageDraw.Draw(canvas);sources=[]
    for n,(clip,d) in enumerate((c,d) for c in clips for d in dirs):
        phase=min(index,11) if clip.endswith('collect') else index%12;x=n%9*384;y=n//9*704;bg=[(248,246,240,255),(136,142,146,255),(23,39,54,255)][(n//9+n%9)%3];draw.rectangle((x,y,x+383,y+703),fill=bg);p=OUT/'frames'/clip/d/f'{phase:03}.png';im=Image.open(p).convert('RGBA');canvas.alpha_composite(im,(x,y));sources.append({'clip':clip,'direction':d,'index':phase,'path':p.relative_to(BASE).as_posix(),'sha256':sha(p)})
    canvas=canvas.resize((778,634),Image.Resampling.LANCZOS).convert('RGB');draw=ImageDraw.Draw(canvas)
    for n,(clip,d) in enumerate((c,d) for c in clips for d in dirs):draw.text((round(n%9*86.4)+1,round(n//9*158.4)+1),clip+' '+d,fill=(22,39,53),stroke_width=0)
    p=dest/f'{index:03}.png';canvas.save(p);records.append({'frame':index,'seconds':index/12,'path':p.relative_to(BASE).as_posix(),'sha256':sha(p),'sources':sources})
video=OUT/'native-family-playback.webm';cmd=['/opt/homebrew/bin/ffmpeg','-y','-framerate','12','-i',str(dest/'%03d.png'),'-c:v','libvpx-vp9','-lossless','1','-pix_fmt','yuv444p',str(video)];result=subprocess.run(cmd,capture_output=True,text=True);(OUT/'family-playback/ffmpeg.log').write_text(result.stderr);assert result.returncode==0
(OUT/'family-playback/manifest.json').write_text(json.dumps({'pathBase':'object-root','kind':'Deterministic synchronized native-render-derived family playback. This is offline phase reconstruction, separate from actual browser realRAF compositor evidence.','fps':12,'frames':24,'durationSeconds':2,'coverage':'All9clips/all4facings. Six loops repeat at frame12; three collect one-shots hold their terminal11 through frame23.','sampling':'Original published registered full canvases combined9x4 at2x, common complete canvas uniformly LANCZOS reduced to778x634; labels/backgrounds presentation only.','frames':records,'video':{'path':video.relative_to(BASE).as_posix(),'sha256':sha(video)},'encoder':{'executable':cmd[0],'sha256':sha(Path(cmd[0])),'command':cmd,'version':subprocess.check_output([cmd[0],'-version'],text=True).splitlines()[0]}},indent=2)+'\n')
print('ALPHA_ALL864_FAMILY24_COMPLETE',sha(video))
