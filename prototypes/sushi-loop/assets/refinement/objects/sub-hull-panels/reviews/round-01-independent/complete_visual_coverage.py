import sys,pathlib
sys.dont_write_bytecode=True
out=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(out/'resources/python'))
from PIL import Image,ImageDraw
import json,hashlib,shutil
ex=out.parents[1];c=ex/'candidates/round-01';manifest=json.loads((out/'consumer-independent-check.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
stream=Image.new('RGBA',(1536,1020),'#888888');draw=ImageDraw.Draw(stream)
for i,r in enumerate(manifest['loopStream']):
 im=Image.open(out/r['path']).convert('RGBA').resize((256,235),Image.Resampling.LANCZOS);x=i%6*256;y=i//6*255+20;stream.alpha_composite(im,(x,y));draw.text((x+4,y-16),f'playback{i:02} {r["at"]:.0f}ms',fill='white')
stream.save(out/'loop-playback-all24.png')
all4=Image.open(c/'previews/active-all4.apng');assert all4.n_frames==12
checks=[];sheet=Image.new('RGBA',(1536,1020),'#A8ADAE');draw=ImageDraw.Draw(sheet)
for i in range(12):
 im=Image.new('RGBA',(1536,704))
 for j,d in enumerate('NESW'):im.paste(Image.open(c/f'frames/active-{d}/{i:03}.png').convert('RGBA'),(j*384,0))
 all4.seek(i);equal=all4.convert('RGBA').tobytes()==im.tobytes();assert equal;checks.append({'frame':i,'exactPublishedFourViewConcatenation':equal});thumb=all4.convert('RGBA').resize((512,235),Image.Resampling.BOX);x=i%3*512;y=i//3*255+20;sheet.alpha_composite(thumb,(x,y));draw.text((x+8,y-16),f'actual active-all4.apng frame{i+1}',fill='#202020')
sheet.save(out/'declared-all4-apng-all12.png')
shutil.copy2(ex/'source/records/camera.json',out/'resources/cameraRecord.json')
source=json.loads((out/'apng-source-coverage.json').read_text());source['activeAll4']=checks;source['fullPlaybackStream']=manifest['loopStream'];source['fullPlaybackSheet']='loop-playback-all24.png';source['activeAll4FrameSheet']='declared-all4-apng-all12.png';source['uniqueBrowserRenderedLoopFrames']=manifest['uniqueLoopScreenshots'];(out/'apng-source-coverage.json').write_text(json.dumps(source,indent=2))
print('VISUAL_COVERAGE_COMPLETE',len(checks),len(manifest['loopStream']))
