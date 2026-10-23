import json,pathlib,hashlib,subprocess,collections
import numpy as np
from PIL import Image
B=pathlib.Path(__file__).parents[2];P=B/'candidates/round-03';O=pathlib.Path(__file__).parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=json.loads((P/'packet.json').read_text());refs=[]
def walk(x):
 if isinstance(x,dict):
  if 'path'in x and 'sha256'in x:refs.append(x)
  for y in x.values():walk(y)
 elif isinstance(x,list):
  for y in x:walk(y)
walk({k:p[k]for k in ['files','candidateRenders','previews']});bad=[x['path'] for x in refs if not(P/x['path']).is_file()or sha(P/x['path'])!=x['sha256']]
assert not bad,bad
cat=json.loads((B/'inputs/catalog-object.json').read_text());atlas=[];frames=[];pixel=[]
for c in cat['clips']:
 for d,rc in c['directions'].items():
  at=Image.open(P/f"atlases/{c['id']}-{d}.png").convert('RGBA');assert at.size==tuple(rc['atlasSize'])
  for i,(x,y,w,h) in enumerate(rc['rects']):
   n=f"{c['id']}-{d}-{i:02d}.png";im=Image.open(P/'frames'/n).convert('RGBA');assert im.size==(384,640)
   atlas.append(at.crop((x,y,x+w,y+h)).tobytes()==im.tobytes());frames.append(n)
   baseline='round-02' if c['id']in ['hold','load'] and d=='N' else 'round-01'
   a=np.array(im,dtype=np.int16);b=np.array(Image.open(B/f'candidates/{baseline}/frames'/n).convert('RGBA'),dtype=np.int16);delta=np.abs(a-b);ys,xs=np.where(np.any(delta,axis=2));r={'frame':n,'baseline':baseline,'pixels':len(xs),'maxRGBA':int(delta.max()),'alphaPixels':int(np.count_nonzero(delta[:,:,3])),'maxAlpha':int(delta[:,:,3].max()),'bbox':[int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1]if len(xs)else None,'compositeMax':{}}
   for k,rgb in {'light':(242,237,226),'gray':(105,110,116),'dark':(29,37,45)}.items():
    bg=Image.new('RGBA',im.size,(*rgb,255));ac=np.array(Image.alpha_composite(bg,im).convert('RGB'),dtype=np.int16);bc=np.array(Image.alpha_composite(bg,Image.fromarray(b.astype('uint8'),'RGBA')).convert('RGB'),dtype=np.int16);r['compositeMax'][k]=int(np.abs(ac-bc).max())
   pixel.append(r)
assert all(atlas)
probes=[]
for v in sorted(list((P/'playbacks').glob('*.mp4'))+list((P/'contexts').glob('*.mp4'))):
 q=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,r_frame_rate,nb_frames,duration','-of','json',str(v)]))['streams'][0]
 probes.append({'path':str(v.relative_to(P)),**q});assert q['r_frame_rate']=='12/1'and q['nb_frames']=='12'and float(q['duration'])==1
summary={}
for label,rows in [('idleWork',[r for r in pixel if r['frame'].split('-')[0]in['idle','work']]),('heldS',[r for r in pixel if r['frame'].split('-')[0]in['hold','load']and '-S-'in r['frame']]),('heldN',[r for r in pixel if r['frame'].split('-')[0]in['hold','load']and '-N-'in r['frame']]),('heldE',[r for r in pixel if r['frame'].split('-')[0]in['hold','load']and '-E-'in r['frame']]),('heldW',[r for r in pixel if r['frame'].split('-')[0]in['hold','load']and '-W-'in r['frame']])]:
 summary[label]={'frames':len(rows),'exact':sum(r['pixels']==0 for r in rows),'maxPixels':max(r['pixels']for r in rows),'maxRGBA':max(r['maxRGBA']for r in rows),'maxAlpha':max(r['maxAlpha']for r in rows),'maxComposite':max(max(r['compositeMax'].values())for r in rows)}
worst=sorted(pixel,key=lambda r:(r['maxRGBA'],r['pixels']),reverse=True)[:6]
out={'packetSHA256':sha(P/'packet.json'),'hashBoundReferencesChecked':len(refs),'uniquePathsChecked':len(set(r['path']for r in refs)),'hashFailures':bad,'atlasCellsRGBAExact':sum(atlas),'frameCount':len(frames),'videoProbes':probes,'pixelSummary':summary,'worstFrames':worst,'pixelRecords':pixel}
(O/'integrity-pixels.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k]for k in ['hashBoundReferencesChecked','uniquePathsChecked','atlasCellsRGBAExact','pixelSummary','worstFrames']},indent=2))
