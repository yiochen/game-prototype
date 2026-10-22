from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,struct,itertools,numpy as np
O=Path(__file__).resolve().parent;E=O.parent.parent;C=E/'candidates/round-02'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def gray(im):
 b=Image.new('RGBA',im.size,'#9da9ae');b.alpha_composite(im);return b.convert('RGB')
webps=[]
for name in [f'active-{d}.webp' for d in 'NESW']+['all4-logical-playback.webp']+[f'consumer-phone{s}-{d}.webp' for s in ['','32'] for d in 'NESW']:
 p=C/'previews'/name;im=Image.open(p);raw=p.read_bytes();pos=12;dur=[]
 while pos+8<=len(raw):
  kind=raw[pos:pos+4];n=int.from_bytes(raw[pos+4:pos+8],'little');body=raw[pos+8:pos+8+n]
  if kind==b'ANMF':dur.append(int.from_bytes(body[12:15],'little'))
  pos+=8+n+n%2
 matches=[]
 for i in range(im.n_frames):
  im.seek(i);frame=im.convert('RGB')
  if name.startswith('active-'):
   d=name.split('-')[1].split('.')[0];src=C/f'frames/active/{d}/{i:03d}.png';expected=gray(Image.open(src).convert('RGBA').resize((192,352),Image.Resampling.BOX));qualification=str(src.relative_to(E))+' whole-frame BOX logical over gray'
  elif name.startswith('consumer'):
   d=name.split('-')[-1].split('.')[0];stem='phone32' if name.startswith('consumer-phone32') else 'phone';src=C/f'consumer/captures/{stem}-{d}-{i+1:02d}.png';expected=Image.open(src).convert('RGB');qualification=str(src.relative_to(E))
  else:
   expected=Image.new('RGB',(768,352),'#9da9ae')
   for j,d in enumerate('NESW'):
    f=Image.open(C/f'frames/active/{d}/{i:03d}.png').convert('RGBA').resize((192,352),Image.Resampling.BOX);expected.paste(f,(j*192,0),f);ImageDraw.Draw(expected).text((j*192+6,6),f'{d} · {i+1}/12',fill='#17323e')
   qualification='All four sealed whole-frame BOX logical cells with fixed labels'
  matches.append({'frame':i+1,'exactRGBContent':frame.tobytes()==expected.tobytes(),'mappedContent':qualification})
 webps.append({'path':'previews/'+name,'sha256':sha(p),'size':list(im.size),'frameCount':im.n_frames,'durationMilliseconds':dur,'totalMilliseconds':sum(dur),'loop':im.info.get('loop'),'mappedFrames':matches})
intermediates=[]
for p in sorted((C/'published-intermediates').rglob('*.png')):
 n=C/'native-intermediates'/p.relative_to(C/'published-intermediates')
 if not n.exists():
  audit=json.loads((C/'intermediate-capture-audit.json').read_text());rr=next(x for x in audit['frames'] if x['direction']==p.parent.name and Path(x['path']).name==p.name);n=E/rr['path']
 intermediates.append({'published':str(p.relative_to(E)),'native':str(n.relative_to(E)),'wholeBOXExact':Image.open(n).convert('RGBA').resize((384,704),Image.Resampling.BOX).tobytes()==Image.open(p).convert('RGBA').tobytes()})
# Exact final browser pixels: fixed complete registered own sprite windows, no resize.
r=json.loads((O/'phone32-motion.json').read_text());small=Image.new('RGB',(648,480),'#dfe8e8');dr=ImageDraw.Draw(small)
for row,d in enumerate('NESW'):
 for i in range(12):
  rec=next(x for x in r['records'] if x.get('direction')==d and x.get('frame')==i and 'capture'in x);im=Image.open(O/rec['capture']);small.paste(im,(i*54,row*120+20));dr.text((i*54+2,row*120+3),f'{d}{i+1}',fill='#234')
small.save(O/'phone32-every-phase-1to1.png')
# Make bounded inspection sheets of exact complete final consumer canvases (fixed canvas-content UI origin y228 on phone, y166 on wide).
rr=json.loads((O/'consumer-reproduction.json').read_text())['records']
for cell in [32,47.3,128]:
 selected=[x for x in rr if x['cell']==cell and x['pan']==[.125,.875]]
 if cell==128:
  for d in 'NESW':
   recs=[x for x in selected if x['direction']==d];w,h=recs[0]['canvas'];out=Image.new('RGB',(w*3,h+22),'#dfe8e8');dr=ImageDraw.Draw(out)
   for j,bg in enumerate(['light','gray','dark']):
    x=next(x for x in recs if x['bg']==bg);im=Image.open(O/x['capture']);out.paste(im.crop((13,166,13+w,166+h)),(j*w,22));dr.text((j*w+4,4),f'{d} 768 viewport128cell {bg}',fill='#234')
   out.save(O/f'wide-context-{d}.png')
 else:
  w=366;h=max(x['canvas'][1] for x in selected);out=Image.new('RGB',(w*3,(h+22)*4),'#dfe8e8');dr=ImageDraw.Draw(out)
  for row,d in enumerate('NESW'):
   for j,bg in enumerate(['light','gray','dark']):
    x=next(x for x in selected if x['direction']==d and x['bg']==bg);im=Image.open(O/x['capture']);ww,hh=x['canvas'];out.paste(im.crop((13,228,13+ww,228+hh)),(j*w,row*(h+22)+22));dr.text((j*w+4,row*(h+22)+4),f'{d} phone{cell} {bg}',fill='#234')
  out.save(O/f'phone-context-{cell}.png')
old=json.loads((E/'reviews/round-01-independent/identity-contact-lamps-v2.json').read_text());new=json.loads((O/'identity-contact-lamps-v2.json').read_text())
result={'webpAll13ContentMappings':webps,'all156WebPFramesExact':all(all(y['exactRGBContent'] for y in x['mappedFrames']) for x in webps),'all13OneSecond12FrameLoops':all(x['frameCount']==12 and x['totalMilliseconds']==1000 and x['loop']==0 for x in webps),'intermediatePublication':intermediates,'allIntermediateWholeBOXExact':all(x['wholeBOXExact'] for x in intermediates),'priorSignedRound01NeutralResourcesExact':old['canonicalResourceHashes']==new['canonicalResourceHashes'],'priorIndependentIdentityFileSHA256':sha(E/'reviews/round-01-independent/identity-contact-lamps-v2.json'),'phoneSheetQualification':'Exact display pixels from independent actual consumer; fixed registered window crop used only for inspection; no resizing or alpha fitting. Full scene captures retained. Context sheets are inspection crops; originals full screenshots are retained.'}
(O/'media-content-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['webpAll13ContentMappings','intermediatePublication']},indent=2))
