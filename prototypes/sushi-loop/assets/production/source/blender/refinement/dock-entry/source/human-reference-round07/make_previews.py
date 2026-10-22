"""Unfitted whole-frame native sheets and labeled inspection crops; raw art unchanged."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw
import numpy as np
B=Path(__file__).resolve().parents[2];O=B/'candidates/round-07';P=O/'previews';P.mkdir(exist_ok=True);j=json.loads((O/'native-human-reference-validation.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();rows=[]
for r in j['renders']:
 p=B/r['path'];assert sha(p)==r['sha256'];im=Image.open(p).convert('RGBA');a=np.asarray(im.getchannel('A'));border=int((a[0]>0).sum()+(a[-1]>0).sum()+(a[:,0]>0).sum()+(a[:,-1]>0).sum());assert border==0;rows.append({'path':r['path'],'sha256':r['sha256'],'size':list(im.size),'alphaBounds':im.getchannel('A').getbbox(),'nontransparentBorderPixels':border})
for fixture in ['current-b176-hut','approved-hut01-additional']:
 for d in 'NESW':
  rr=[r for r in j['renders']if r['direction']==d and r['fixture']==fixture];assert len(rr)==9;sheet=Image.new('RGB',(1152,1248),'#e6e1d4');draw=ImageDraw.Draw(sheet)
  for i,r in enumerate(rr):
   im=Image.open(B/r['path']).convert('RGBA').resize((384,384),Image.Resampling.LANCZOS);x=(i%3)*384;y=(i//3)*416+28;sheet.paste(im,(x,y),im);draw.text((x+6,y-22),f'{d} {r["case"]} {r["clip"]}{r["sourceNativeFrame"]}',fill='#2d241c')
  sheet.save(P/f'native-{fixture}-{d}.png')
for d in 'NESW':
 rr=[r for r in j['renders']if r['direction']==d and r['fixture']=='current-b176-hut'];sheet=Image.new('RGB',(1080,1080),'#e6e1d4');draw=ImageDraw.Draw(sheet)
 for i,r in enumerate(rr):
  x,y,z=r['worldRoot'];px=2*(384+128*x);py=2*(440-128*y-89.60003662109375*z);im=Image.open(B/r['path']).convert('RGBA');bounds=(round(px-160),round(py-200),round(px+160),round(py+100));im=im.crop(bounds).resize((360,338),Image.Resampling.NEAREST);dx=(i%3)*360;dy=(i//3)*360+22;sheet.paste(im,(dx,dy),im);draw.text((dx+4,dy-18),f'{d} {r["case"]} / actual full shoes',fill='#2d241c')
 sheet.save(P/f'native-full-shoe-contact-{d}.png')
sheet=Image.new('RGB',(1536,832),'#e6e1d4');draw=ImageDraw.Draw(sheet)
for row,fixture in enumerate(['current-b176-hut','approved-hut01-additional']):
 for col,d in enumerate('NESW'):
  r=next(r for r in j['renders']if r['direction']==d and r['fixture']==fixture and r['case']=='exterior-stop');im=Image.open(B/r['path']).convert('RGBA').resize((384,384),Image.Resampling.LANCZOS);x=col*384;y=row*416+28;sheet.paste(im,(x,y),im);draw.text((x+4,y-22),f'{d} exterior stop / {fixture}',fill='#2d241c')
sheet.save(P/'native-exterior-stop-both-fixtures-all4.png')
(O/'native-clipping-verification.json').write_text(json.dumps({'method':'Hash-verified72 full native context frames; exact1536square common frame, no border clipping. Sheets uniformly scale complete frames; shoe-only inspection crops are labeled and not exported sprites.','all72NoBorderClipping':len(rows)==72 and all(r['nontransparentBorderPixels']==0 for r in rows),'records':rows},indent=2));print('NATIVE_PREVIEWS_READY',len(rows))
