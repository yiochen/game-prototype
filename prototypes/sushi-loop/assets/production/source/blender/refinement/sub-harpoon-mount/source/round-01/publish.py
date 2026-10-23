"""Whole-frame publication and review-only sheets. No pixel repair or fitted crops."""
from PIL import Image,ImageDraw,ImageFont
import pathlib,json,hashlib,subprocess
P=pathlib.Path(__file__).resolve().parent;E=P.parent.parent;C=E/'candidates/round-01'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
raw=[];native=[];atlases=[];previews={}
for clip,count in [('idle',1),('active',12)]:
 for d in 'NESW':
  cols,rows=(1,1) if clip=='idle' else (6,2)
  atlas=Image.new('RGBA',(384*cols,704*rows))
  rects=[]
  for i in range(count):
   src=C/'native'/f'{clip}-{d}'/f'{i:03}.png';dst=C/'published'/f'{clip}-{d}'/f'{i:03}.png';dst.parent.mkdir(parents=True,exist_ok=True)
   im=Image.open(src).convert('RGBA');assert im.size==(768,1408)
   published=im.resize((384,704),Image.Resampling.BOX);published.save(dst)
   r=[(i%cols)*384,(i//cols)*704,384,704];rects.append(r);atlas.paste(published,(r[0],r[1]))
   raw.append({'clip':clip,'direction':d,'index':i,'sourceFrame':i+1,'path':str(dst.relative_to(E)),'dimensions':[384,704],'sha256':sha(dst)})
   native.append({'clip':clip,'direction':d,'index':i,'sourceFrame':i+1,'path':str(src.relative_to(E)),'dimensions':[768,1408],'sha256':sha(src)})
  a=C/'atlases'/f'{clip}-{d}.png';a.parent.mkdir(exist_ok=True);atlas.save(a)
  atlases.append({'clip':clip,'direction':d,'path':str(a.relative_to(E)),'sha256':sha(a),'columns':cols,'rows':rows,'size':list(atlas.size),'rects':rects,'fps':12,'loop':False,'static':clip=='idle','frameOrder':list(range(count))})
# All complete published frames retained in four sheets, both idle and all12 phases.
for d in 'NESW':
 sheet=Image.new('RGB',(384*7,730*2),'#dce1df');draw=ImageDraw.Draw(sheet)
 files=[C/'published'/f'idle-{d}'/'000.png']+[C/'published'/f'active-{d}'/f'{i:03}.png' for i in range(12)]
 for j,f in enumerate(files):
  x=(j%7)*384;y=(j//7)*730;draw.text((x+10,y+8),f'{d} '+('IDLE neutral' if j==0 else f'ACTIVE source frame {j:02}/12'),fill='#233341');sheet.paste(Image.open(f),(x,y+26),Image.open(f))
 path=C/'previews'/f'all13-{d}.png';path.parent.mkdir(exist_ok=True);sheet.save(path);previews['active-'+d]=str(path.relative_to(E))
 # Real12fps encoded once. Phase12 is the source residual endpoint; no closing frame.
 vid=C/'previews'/f'active-{d}-12fps.mp4'
 subprocess.run(['ffmpeg','-loglevel','error','-y','-framerate','12','-i',str(C/'published'/f'active-{d}'/'%03d.png'),'-frames:v','12','-vf','format=yuv420p','-c:v','libx264','-crf','18',str(vid)],check=True)
 previews['playback-'+d]=str(vid.relative_to(E))
# Four registered neutral frames on light/gray/dark, whole-frame reduced to logical size.
sheet=Image.new('RGB',(192*4,378*3),'white');draw=ImageDraw.Draw(sheet)
for row,bg in enumerate(['#f5f0e6','#9ca7ac','#1c2732']):
 for col,d in enumerate('NESW'):
  x=col*192;y=row*378;draw.rectangle((x,y,x+191,y+377),fill=bg);draw.text((x+8,y+8),d+' IDLE ·128px cell',fill='white' if row==2 else '#243645');im=Image.open(C/'published'/f'idle-{d}'/'000.png').resize((192,352),Image.Resampling.LANCZOS);sheet.paste(im,(x,y+26),im)
path=C/'previews/four-view-sheet.png';sheet.save(path);previews['four-view-sheet']=str(path.relative_to(E))
# Intended-size phase sweeps retain the same full frame at three common pitches.
for pitch in [128,47.3,32]:
 scale=pitch/128;fw=round(192*scale);fh=round(352*scale);cw=fw+14;ch=fh+24
 sheet=Image.new('RGB',(cw*13,ch*12),'#9ca7ac');draw=ImageDraw.Draw(sheet)
 for bi,bg in enumerate(['#f5f0e6','#9ca7ac','#1c2732']):
  for di,d in enumerate('NESW'):
   row=bi*4+di
   for i in range(13):
    x=i*cw;y=row*ch;draw.rectangle((x,y,x+cw,y+ch),fill=bg);draw.text((x+3,y+3),d+(' idle' if i==0 else f' {i}'),fill='white' if bi==2 else '#243645');f=C/'published'/(f'idle-{d}' if i==0 else f'active-{d}')/('000.png' if i==0 else f'{i-1:03}.png');im=Image.open(f).resize((fw,fh),Image.Resampling.LANCZOS);sheet.paste(im,(x+7,y+22),im)
 sheet.save(C/'previews'/f'intended-size-sweep-{pitch}.png')
# Mounted native assembly images are already actual640x768 main camera renders.
for d in 'NESW':
 sheet=Image.new('RGB',(320*7,406*2),'#dce1df');draw=ImageDraw.Draw(sheet)
 files=[C/'mounted'/f'idle-{d}'/'000.png']+[C/'mounted'/f'active-{d}'/f'{i:03}.png' for i in range(12)]
 for j,f in enumerate(files):
  x=j%7*320;y=j//7*406;draw.text((x+5,y+5),f'{d} '+('neutral' if j==0 else f'phase{j}')+' · other gear PROVISIONAL',fill='#263743');im=Image.open(f).resize((320,384),Image.Resampling.LANCZOS);sheet.paste(im,(x,y+22),im)
 sheet.save(C/'previews'/f'mounted-all13-{d}.png')
 # Whole mounted native capture is used directly by real sprite consumer at sourceScale2.
 dst=C/'assembled'/f'upgraded-dock-ready-{d}.png';dst.parent.mkdir(exist_ok=True);Image.open(files[0]).save(dst)
dump(C/'publication.json',{'method':'Complete native4x768x1408 frames BOX reduced2x384x704. Atlases paste complete frames unchanged at original1x1 and6x2 layout. Review sheets/MP4 are presentation composites only.','rawFrames':raw,'nativeRawFrames':native,'atlases':atlases,'previews':previews})
print('PUBLICATION_COMPLETE',len(raw),len(atlases))
