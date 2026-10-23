"""Readable evidence sheets/videos from original native and actual consumer captures.

Uniform whole-frame presentation and explicitly labelled contact crops only.
No asset edits, depth repair, alpha fitting, per-view root fitting or masks.
"""
import sys,json,math,subprocess,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;O=H.parent.parent;D=O/'candidates/round-02';P=D/'previews';P.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
fam=json.loads((D/'final-family-audit.json').read_text());con=json.loads((D/'consumer/consumer-evidence.json').read_text());modes=['dock-ready','dock-charging','upgraded-dock-ready','upgraded-dock-charging'];states=[('covered',0),('uncover',5),('uncover',11)]
def tile(sh,path,x,y,size,label,bg='#777777'):
 im=Image.open(O/path).convert('RGBA');scale=min(size[0]/im.width,size[1]/im.height);im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS)
 sh.paste(im,(x+(size[0]-im.width)//2,y+24),im);ImageDraw.Draw(sh).text((x+6,y+6),label,fill='white')
for kind in ['native','consumer']:
 sh=Image.new('RGB',(4*368,12*380),'#777777')
 for row,(mode,(clip,index))in enumerate((m,s)for m in modes for s in states):
  for col,d in enumerate('NESW'):
   if kind=='native':r=next(r for r in fam['nativeContexts']if r['mode']==mode and r['clip']==clip and r['frame']==index+1 and r['direction']==d)
   else:r=next(r for r in con['nativeFrames']if r['mode']==mode and r['clip']==clip and r['index']==index and r['direction']==d)
   tile(sh,r['path'],col*368,row*380,(368,352),f'{d} {mode} / {clip} {index+1}')
 sh.save(P/f'{kind}-family-sheet.png',optimize=True)
# All nine exact actor stances, each direction, each required visible phase.
plan=json.loads((O/'inputs/shared-world-pose-v1/plan.json').read_text())
for clip,index in states:
 sh=Image.new('RGB',(4*368,9*390),'#777777')
 for row,case in enumerate(plan['cases']):
  for col,d in enumerate('NESW'):
   r=next(r for r in con['humanCases']if r['case']==case['id']and r['clip']==clip and r['index']==index and r['direction']==d)
   tile(sh,r['path'],col*368,row*390,(368,360),f'{case["id"]} {d} / {clip} {index+1}')
 sh.save(P/f'human-{clip}-{index+1:02d}.png',optimize=True)
# Three real bearing patches, displayed on the unchanged native deck.
sh=Image.new('RGB',(3*420,4*360),'#777777');dr=ImageDraw.Draw(sh)
for row,d in enumerate('NESW'):
 a={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}[d];r=next(r for r in fam['nativeContexts']if r['mode']=='upgraded-dock-ready'and r['clip']=='uncover'and r['frame']==12 and r['direction']==d);im=Image.open(O/r['path']).convert('RGBA')
 for col,s in enumerate(fam['support']):
  poly=s['limitingFinitePolygon']['polygonXY'];x=sum(p[0]for p in poly)/len(poly);y=sum(p[1]for p in poly)/len(poly);wx=math.cos(a)*x-math.sin(a)*y;wy=math.sin(a)*x+math.cos(a)*y;px=736+256*wx;py=960-256*wy-179.2000732421875*.22
  crop=im.crop((round(px)-160,round(py)-150,round(px)+160,round(py)+150));sh.paste(crop,(col*420+50,row*360+45),crop)
  dr.text((col*420+8,row*360+6),f'{d} {s["support"].replace("dock-cover__bearing_sole_","")}',fill='white');dr.text((col*420+8,row*360+23),f'finite area {s["contactArea"]:.8f} / gap {s["minimumGapWorld"]:.2e}',fill='white')
sh.save(P/'support-contact-sheet.png',optimize=True)
# Global actual renderer repeating nine fixed assemblies; whole-frame reduction.
rep=json.loads((D/'consumer/repeated/records.json').read_text());sh=Image.new('RGB',(4*600,2*650),'#777777')
for row,clip in enumerate(['covered','uncover']):
 for col,d in enumerate('NESW'):
  r=next(r for r in rep['records']if r['clip']==clip and r['direction']==d);tile(sh,r['path'],col*600,row*650,(600,615),f'{d} nine actual assemblies / {clip}')
sh.save(P/'repeated-sheet.png',optimize=True)
# The real React scene captures on phone and desktop, retaining full UI/frame.
dom=json.loads((D/'consumer-dom/actual-SpriteScene-parity.json').read_text());assert all(r['exactDecodedNativeCanvasParity']for r in dom['records'])and not dom['errors']
for size in ['phone','desktop']:
 sh=Image.new('RGB',(4*390,3*650),'#777777')
 for row,(clip,index)in enumerate(states):
  for col,d in enumerate('NESW'):
   r=next(r for r in dom['screens']if r['size']==size and r['clip']==clip and r['index']==index and r['direction']==d);tile(sh,r['path'],col*390,row*650,(390,620),f'Actual SpriteScene {size} {d} {clip} {index+1}')
 sh.save(P/f'actual-component-{size}.png',optimize=True)
# All four modes and directions play simultaneously with their exact frame index.
videos=[]
for clip in ['covered','uncover']:
 frames=[]
 for index in range(12):
  sh=Image.new('RGB',(1280,1360),'#777777')
  for row,mode in enumerate(modes):
   for col,d in enumerate('NESW'):
    r=next(r for r in con['nativeFrames']if r['mode']==mode and r['clip']==clip and r['index']==index and r['direction']==d);tile(sh,r['path'],col*320,row*340,(320,312),f'{d} {mode} {clip} {index+1}')
  frames.append(sh.tobytes())
 f=P/f'actual-consumer-{clip}-all4modes.mp4';cmd=['/opt/homebrew/bin/ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1280x1360','-r','12','-i','-','-an','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(f)]
 proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
 for k in range(48):proc.stdin.write(frames[k%12]if clip=='covered'else frames[min(k,11)])
 proc.stdin.close();assert proc.wait()==0
 probe=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-show_streams','-of','json',str(f)]))['streams'][0];videos.append({'clip':clip,'path':str(f.relative_to(O)),'sha256':sha(f),'fps':probe['r_frame_rate'],'frames':probe['nb_frames'],'duration':probe['duration'],'meaning':'Actual authored-projection whole consumer canvases, all four Main modes and directions. Covered repeats four cycles; uncover runs once and holds for three seconds. Preview reduction only.'})
(P/'video-records.json').write_text(json.dumps(videos,indent=2)+'\n')
# Regenerate the playback page only; original atlas/raw bytes are untouched.
previews=json.loads((D/'playback-records.json').read_text());html='<html><meta charset="utf-8"><title>Dock cover round02 native candidate playback</title><style>body{background:#25282e;color:#eee;font:16px system-ui}main{display:grid;grid-template-columns:repeat(4,1fr)}video{width:100%}h2{font-size:16px}</style><h1>Round02 native candidate clips</h1><p>12fps. Covered repeats four cycles; uncover runs once and holds for three seconds. Exact final family and consumer evidence is separate. Independent review pending.</p><main>'
for r in previews:html+=f'<section><h2>{r["clip"]} {r["direction"]}</h2><video src="playback/{r["clip"]}-{r["direction"]}.mp4" controls autoplay {"loop"if r["clip"]=="covered"else ""} muted playsinline></video></section>'
(D/'playback.html').write_text(html+'</main></html>')
print('COMPLETE FINAL PREVIEWS',len(list(P.iterdir())))
