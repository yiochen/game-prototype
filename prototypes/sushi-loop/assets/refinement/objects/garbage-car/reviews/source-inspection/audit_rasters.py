from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib
ROOT=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype')
P=ROOT/'prototypes/sushi-loop/assets/refinement/objects/garbage-car'
OUT=P/'reviews/source-inspection';OUT.mkdir(exist_ok=True,parents=True)
catalog=json.loads((P/'inputs/catalog-object.json').read_text())
BASE=ROOT/'prototypes/sushi-loop/assets/production'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
records=[];sheets=[];playbacks=[];allframes={}
for clip in catalog['clips']:
 for direction,record in clip['directions'].items():
  path=BASE/record['image'];im=Image.open(path).convert('RGBA');frames=[]
  for i,rect in enumerate(record['rects']):
   x,y,w,h=rect;f=im.crop((x,y,x+w,y+h));frames.append(f)
   a=f.getchannel('A');records.append({'clip':clip['id'],'direction':direction,'runtimeIndex':i,'atlas':str(path.relative_to(ROOT)),'atlasSHA256':sha(path),'rectXYWH':rect,'RGBABytesSHA256':hashlib.sha256(f.tobytes()).hexdigest(),'alphaBBoxAny':a.getbbox(),'alphaBBox128':a.point(lambda x:255 if x>=128 else 0).getbbox(),'alphaSum':sum(a.getdata()),'alphaExtrema':a.getextrema()})
  allframes[clip['id'],direction]=frames
  cols=6 if len(frames)>1 else 1;rows=(len(frames)+cols-1)//cols
  sheet=Image.new('RGB',(cols*288,rows*440),'#808080');d=ImageDraw.Draw(sheet)
  for i,f in enumerate(frames):
   sm=f.resize((288,416),Image.Resampling.LANCZOS);sheet.paste(sm,(i%cols*288,i//cols*440+24),sm);d.text((i%cols*288+8,i//cols*440+6),f'{clip["id"]} {direction} runtime{i:02d}',fill='white')
  output=OUT/f'original-{clip["id"]}-{direction}-all.png';sheet.save(output);sheets.append({'path':str(output.relative_to(P)),'atlasSHA256':sha(path),'frames':len(frames),'resize':'Uniform full frame to 288x416, gray composite, no subject fitting'})
  if len(frames)>1:
   gifframes=[]
   for f in frames:
    bg=Image.new('RGBA',f.size,'#808080');bg.alpha_composite(f);gifframes.append(bg.convert('RGB').resize((288,416),Image.Resampling.LANCZOS))
   output=OUT/f'original-{clip["id"]}-{direction}-12fps.gif'
   kwargs={'save_all':True,'append_images':gifframes[1:],'duration':[83,83,84]*4,'disposal':2}
   if clip['loop']:kwargs['loop']=0
   gifframes[0].save(output,**kwargs);playbacks.append(str(output.relative_to(P)))
idle=Image.new('RGB',(4*288,440),'#808080');d=ImageDraw.Draw(idle)
for j,direction in enumerate(['N','E','S','W']):
 sm=allframes['idle',direction][0].resize((288,416),Image.Resampling.LANCZOS);idle.paste(sm,(288*j,24),sm);d.text((288*j+8,6),f'Idle {direction}',fill='white')
idle.save(OUT/'original-idle-four-view.png')
# Full-source registration comparison and intended-size diagnostic. No imagegen fitting.
comparison=Image.new('RGB',(2*576,856),'#808080');d=ImageDraw.Draw(comparison)
for col,name in enumerate(['original','target']):
 im=Image.open(P/f'inputs/{name}.png').convert('RGBA');scale=min(576/im.width,832/im.height);sm=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS);comparison.paste(sm,(col*576,24),sm);d.text((col*576+8,6),name+' uniform canvas scale',fill='white')
comparison.save(OUT/'original-target-registered-canvases.png')
size=Image.new('RGB',(1120,980),'#303030');d=ImageDraw.Draw(size)
for j,direction in enumerate(['N','E','S','W']):
 for k,cell in enumerate([128,55]):
  f=allframes['idle',direction][0];sm=f.resize((round(f.width*cell/256),round(f.height*cell/256)),Image.Resampling.LANCZOS);x=10+j*280;y=30 if k==0 else 500
  for xx,back in enumerate(['#f5f2e9','#808080','#202028']):
   mini=Image.new('RGBA',sm.size,back);mini.alpha_composite(sm)
   # Each direction gets a complete logical image followed below by phone size; backgrounds in separate panels saved too.
   panel=OUT/f'original-idle-{direction}-cell{cell}-{back[1:]}.png';mini.convert('RGB').save(panel)
  if k==1:size.paste(mini.convert('RGB'),(x,y));d.text((x,y-20),f'{direction} cell{cell}px dark',fill='white')
size.save(OUT/'original-phone-four-view.png')
summary={'inputOriginalSHA256':sha(P/'inputs/original.png'),'inputTargetSHA256':sha(P/'inputs/target.png'),'inputSizes':{name:Image.open(P/f'inputs/{name}.png').size for name in ['original','target']},'publishedFrameCount':len(records),'clips':{clip:{di:{'count':len(fs),'uniqueRGBA':len({hashlib.sha256(f.tobytes()).hexdigest() for f in fs})} for (cl,di),fs in allframes.items() if cl==clip} for clip in ['idle','highlighted','clearance']},'frames':records,'contactSheets':sheets,'playbacks':playbacks}
(OUT/'raster-audit.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k not in ['frames','contactSheets','playbacks']},indent=2))
