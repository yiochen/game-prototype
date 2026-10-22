import sys, json, hashlib, shutil, platform
from pathlib import Path
sys.dont_write_bytecode=True
from PIL import Image, ImageDraw, ImageChops, ImageStat
import PIL
P=Path(__file__).resolve().parent;R=P/'resources';out=P/'packed';out.mkdir(exist_ok=True)
def save(im,n):im.save(out/n)
def info(im):
 a=im.getchannel('A');h=a.histogram();return {'alphaRange':a.getextrema(),'nonOpaque':sum(h[:-1]),'rgbExtrema':im.convert('RGB').getextrema()}
def diff(a,b):
 d=ImageChops.difference(a,b);return {'equal':not d.getbbox(alpha_only=False),'extrema':d.getextrema(),'meanAbs':ImageStat.Stat(d).mean}
stats={};sheets={}
for direction in 'NESW':
 frames=[Image.open(P/'replay-raw'/direction/(str(i).zfill(3)+'.png')).convert('RGBA') for i in range(12)]
 small=[im.resize((256,256),Image.Resampling.LANCZOS) for im in frames]
 sheet=Image.new('RGBA',(1536,512))
 for i,im in enumerate(small):sheet.paste(im,(i%6*256,i//6*256))
 save(sheet,'scroll-'+direction+'.png');sheets[direction]=sheet
 historical=Image.open(R/'historical'/('scroll-'+direction+'.png')).convert('RGBA')
 stats[direction]={'raw':[info(im) for im in frames],'packed':[info(im) for im in small],'historical':info(historical),'historicalVsReplayPacked':diff(historical,sheet),'uniquePacked':len({hashlib.sha256(im.tobytes()).hexdigest() for im in small}),'frameStepMeanAbs':[ImageStat.Stat(ImageChops.difference(small[i],small[(i+1)%12])).mean for i in range(12)]}
 contact=Image.new('RGB',(12*136,164),(238,238,238));d=ImageDraw.Draw(contact)
 for i,im in enumerate(small):contact.paste(im.resize((128,128),Image.Resampling.LANCZOS),(i*136+4,24));d.text((i*136+4,5),f'{direction} phase{i}',fill=(20,20,20))
 save(contact,'all-phases-'+direction+'.png')
 four=Image.new('RGB',(544,560),(235,235,235));d=ImageDraw.Draw(four)
 for i,(bg,label) in enumerate([((245,245,240),'light'),((128,128,128),'gray'),((20,24,30),'dark')]):
  # All backgrounds on opaque floor remain equivalent; include actual composites.
  im=Image.new('RGBA',(256,256),bg+(255,));im.alpha_composite(small[0]);four.paste(im.convert('RGB'),((i%2)*272+8,(i//2)*280+24));d.text(((i%2)*272+8,(i//2)*280+5),direction+' '+label,fill=(20,20,20))
 save(four,'contexts-'+direction+'.png')
closure=Image.open(P/'replay-raw/S-closure-13.png').convert('RGBA');first=Image.open(P/'replay-raw/S/000.png').convert('RGBA')
stats['closure13Vs1']=diff(closure,first)
(P/'pixel-audit.json').write_text(json.dumps(stats,indent=2)+'\n')
# Retain only package modules actually imported, not a duplicate runtime tree.
modules={}
for name,module in list(sys.modules.items()):
 f=getattr(module,'__file__',None)
 if name=='PIL' or name.startswith('PIL.'):
  if f and Path(f).is_file():
   f=Path(f);relative=Path('PIL')/f.relative_to(Path(PIL.__file__).parent);dest=R/'python-pillow'/relative;dest.parent.mkdir(parents=True,exist_ok=True)
   if f.resolve()!=dest.resolve():shutil.copyfile(f,dest)
   modules[name]={'relative':str(dest.relative_to(P)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
(P/'python-runtime.json').write_text(json.dumps({'executable':sys.executable,'python':platform.python_version(),'pillow':PIL.__version__,'loadedPillowClosure':modules},indent=2)+'\n')
print(json.dumps({k:{'unique':v['uniquePacked'],'rawAlpha':v['raw'][0]['alphaRange'],'packedAlpha':v['packed'][0]['alphaRange'],'historicalDifference':v['historicalVsReplayPacked']} for k,v in stats.items() if len(k)==1},indent=2));print('closure',stats['closure13Vs1'])
if (P/'consumer').exists():
 for direction in 'NESW':
  canvas=Image.new('RGB',(12*168,188),'#eee');draw=ImageDraw.Draw(canvas)
  for i in range(12):
   im=Image.open(P/'consumer'/('phone-'+direction+'-'+str(i).zfill(2)+'.png')).convert('RGB');im.thumbnail((160,160));canvas.paste(im,(i*168+4,23));draw.text((i*168+4,4),direction+' phase'+str(i),fill='black')
  canvas.save(P/'consumer'/('all-phases-'+direction+'.png'))
if (P/'native-patch').exists():
 canvas=Image.new('RGB',(4*272,2*296),'#eee');draw=ImageDraw.Draw(canvas)
 for j,direction in enumerate('NESW'):
  for row in (0,1):
   im=Image.open(P/'native-patch'/(direction+'-'+('000' if row==0 else '003')+'.png')).convert('RGB');im=im.resize((256,256),Image.Resampling.LANCZOS);canvas.paste(im,(j*272+8,row*296+26));draw.text((j*272+8,row*296+4),f'{direction} native3x3 phase{row*3}',fill='black')
 canvas.save(P/'native-patch/overview.png')
