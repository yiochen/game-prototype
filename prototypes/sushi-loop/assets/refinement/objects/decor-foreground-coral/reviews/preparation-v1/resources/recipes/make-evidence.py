import json,hashlib,math
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops,ImageStat
P=Path(__file__).resolve().parent;R=P/'resources';E=P/'evidence';ledger=json.loads((E/'native-capture-ledger.json').read_text());cat=json.loads((R/'inputs/catalog-object.json').read_text())
replays=[]
for rec in ledger['records']:
 clip,d,f=rec['clip'],rec['direction'],rec['frame'];src=E/'native'/clip/d/f'{f:03d}.png';im=Image.open(src).convert('RGBA');reduced=im.resize((384,768),Image.Resampling.LANCZOS);out=E/'published-replay'/clip/d/f'{f:03d}.png';out.parent.mkdir(parents=True,exist_ok=True);reduced.save(out)
 c=next(c for c in cat['clips'] if c['id']==clip);entry=c['directions'][d];ix=(f-1)%c['frames'];x,y,w,h=entry['rects'][ix];original=Image.open(R/'original-atlases'/f'{clip}-{d}.png').convert('RGBA').crop((x,y,x+w,y+h));diff=ImageChops.difference(reduced,original);union=ImageChops.lighter(reduced.getchannel('A'),original.getchannel('A')).point(lambda a:255 if a else 0);stats=ImageStat.Stat(diff,mask=union)
 replays.append({'clip':clip,'direction':d,'nativeFrame':f,'originalPublishedIndex':ix,'decodedIdentical':diff.getbbox(alpha_only=False) is None,'meanAbsoluteRGBAonUnionAlpha':stats.mean,'maxRGBA':list(diff.getextrema()),'path':str(out.relative_to(P.parent.parent)),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'alphaBBox':reduced.getchannel('A').getbbox()})
# Labeled whole-frame sheets; display only, art never cropped/fitted.
def sheet(rows,path,scale=1,bg='#7d8792',cols=4):
 w,h=round(192*scale),round(384*scale);out=Image.new('RGB',(cols*(w+16)+16,math.ceil(len(rows)/cols)*(h+34)+16),bg);dr=ImageDraw.Draw(out)
 for i,(label,im) in enumerate(rows):
  x=16+(i%cols)*(w+16);y=16+(i//cols)*(h+34);dr.text((x,y),label,fill='white');im=im.convert('RGBA').resize((w,h),Image.Resampling.LANCZOS);out.paste(im,(x,y+20),im)
 out.save(path)
statics=[(d,Image.open(E/'published-replay/static'/d/'001.png')) for d in ['N','E','S','W']]
sheet(statics,E/'four-view-logical-gray.png',1);sheet(statics,E/'four-view-phone-gray.png',.5)
for bg,code in [('light','#eee7d9'),('dark','#13202d')]:sheet(statics,E/f'four-view-logical-{bg}.png',1,bg=code)
rows=[(f'idle S frame{f}',Image.open(E/'published-replay/idle/S'/f'{f:03d}.png')) for f in range(1,14)]
sheet(rows,E/'idle-S-all-phases.png',.66)
frames=[]
for f in range(1,13):
 im=Image.open(E/'published-replay/idle/S'/f'{f:03d}.png').convert('RGBA').resize((192,384),Image.Resampling.LANCZOS);bg=Image.new('RGBA',im.size,'#657482');bg.alpha_composite(im);frames.append(bg.convert('RGB'))
frames[0].save(E/'idle-S-source-playback.gif',save_all=True,append_images=frames[1:],duration=[83,83,84]*4,loop=0)
frames[0].save(E/'idle-S-source-playback.webp',save_all=True,append_images=frames[1:],duration=[83,83,84]*4,loop=0,lossless=True)
# Fixed target is art guide only; whole canvases here cannot establish registration.
rows=[('original S',Image.open(R/'inputs/original.png')),('registered replay S',Image.open(E/'published-replay/static/S/001.png')),('fixed target (art only)',Image.open(R/'inputs/target.png')),('warm style (art only)',Image.open(R/'inputs/warm-soft-reference.png'))]
sheet(rows,E/'independent-reference-comparison.png',1.5)
closure=ImageChops.difference(Image.open(E/'native/idle/S/001.png').convert('RGBA'),Image.open(E/'native/idle/S/013.png').convert('RGBA'))
(E/'pixel-replay-report.json').write_text(json.dumps({'method':'Complete native4x frames reduced once with Pillow LANCZOS to published2x, exact production packer operation; no crop/fitting/alphaRGB edits.','PillowVersion':Image.__version__,'records':replays,'idleSFrame1vs13DecodedIdentical':closure.getbbox(alpha_only=False) is None,'presentationNotes':'Contact sheets rescale complete frames only. GIF/WebP are presentation previews, not source atlases.','limits':'Historical replay can differ in EEVEE sampling/noise from old PNGs; every measured difference retained, not repaired.'},indent=2)+'\n')
print('replay pixel exact',sum(r['decodedIdentical'] for r in replays),'/',len(replays));print('max meanRGBA',max(max(r['meanAbsoluteRGBAonUnionAlpha']) for r in replays));print('closure',closure.getbbox(alpha_only=False));print('All23native ->23published replay + bounded sheets/playback')
