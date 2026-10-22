from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib
H=Path(__file__).resolve().parent;E=H.parent;O=E/'candidates/round-02';P=O/'previews'
audit=json.loads((O/'intermediate-capture-audit.json').read_text());published=[]
for r in audit['frames']:
 im=Image.open(E/r['path']).convert('RGBA');p=O/'published-intermediates'/r['direction']/Path(r['path']).name;p.parent.mkdir(parents=True,exist_ok=True);im.resize((384,704),Image.Resampling.BOX).save(p);published.append({k:r[k] for k in ['direction','clip','nativeFrame','runtimeAtlasFrame']}|{'path':str(p.relative_to(E)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size':[384,704]})
sheet=Image.new('RGB',(768,352*4),'#9da9ae')
for row,frame in enumerate([7.5,8.5,9.5,10.5]):
 for col,d in enumerate('NESW'):
  r=next(r for r in published if r['direction']==d and r['nativeFrame']==frame);im=Image.open(E/r['path']).convert('RGBA').resize((192,352),Image.Resampling.BOX);sheet.paste(im,(col*192,row*352),im);ImageDraw.Draw(sheet).text((col*192+4,row*352+4),f'{d} native {frame}',fill='#1b3440')
sheet.save(P/'intermediates-all4-logical.png')
# Fixed source-pixel inspection window, never a fitted/runtime asset.
phases=[3,7,9,11];w,h=358,160;comparison=Image.new('RGB',(w*4,(h+24)*2),'#9da9ae')
for row,roundid in enumerate(['round-01','round-02']):
 for i,fr in enumerate(phases):
  im=Image.open(E/f'candidates/{roundid}/native/active/S/{fr-1:03d}.png').convert('RGBA').crop((205,970,563,1130));bg=Image.new('RGBA',im.size,'#9da9ae');bg.alpha_composite(im);comparison.paste(bg.convert('RGB'),(i*w,row*(h+24)+24));ImageDraw.Draw(comparison).text((i*w+4,row*(h+24)+4),f'{roundid} S native {fr} · same pixel window',fill='#17313d')
comparison.save(P/'guard-clearance-comparison-fixed-window.png')
for di in 'NESW':
 frames=[Image.open(O/f'consumer/captures/phone32-{di}-{i+1:02d}.png').convert('RGB') for i in range(12)]
 frames[0].save(P/f'consumer-phone32-{di}.webp',save_all=True,append_images=frames[1:],duration=[83,83,84]*4,loop=0,lossless=True)
 sheet=Image.new('RGB',(1170,3376),'#edf1f1')
 for i,im in enumerate(frames):sheet.paste(im,(i%3*390,i//3*844))
 sheet.save(P/f'consumer-phone32-every-phase-{di}.png')
(O/'intermediate-publication.json').write_text(json.dumps({'nativeAudit':'candidates/round-02/intermediate-capture-audit.json','publishedFrames':published,'qualification':'Supplemental actual half-frame captures, complete whole-frame BOX publication. Not additional runtime cells. Fixed-window comparison is an inspection preview only.'},indent=2)+'\n')
print('Supplemental native/published intermediates',len(published))
