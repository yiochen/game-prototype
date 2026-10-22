import json,hashlib,pathlib,subprocess
from PIL import Image
P=pathlib.Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/chef-ama');C=P/'candidates/round-02';d=json.loads((C/'packet.json').read_text());errors=[];checked=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for group in ['files','candidateRenders','previews']:
 for name,r in d[group].items():
  p=C/r['path'];actual=sha(p) if p.exists() else None
  checked.append({'group':group,'name':name,'path':r['path'],'matches':actual==r['sha256']})
  if actual!=r['sha256']:errors.append(r['path'])
raw=json.loads((C/'complete-validation.json').read_text())['rawNativeFrameRecords']

frames=raw if isinstance(raw,list) else raw.get('frames',raw.get('records',[]))
for r in frames:
 path=P/r['path']
 if sha(path)!=r['sha256']:errors.append(r['path'])
print('hashes',len(checked),'frameRecords',len(frames),'errors',errors)
probes=[]
for clip in ['idle','work','hold','load']:
 for direction in ['N','E','S','W']:
  p=C/'playbacks'/f'{clip}-{direction}.mp4'
  j=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,r_frame_rate,avg_frame_rate,nb_frames,duration','-of','json',str(p)]))
  probes.append({'path':str(p.relative_to(C)),**j['streams'][0]})
  with Image.open(C/'atlases'/f'{clip}-{direction}.png') as atlas:
   assert atlas.size==(2304,1280)
   for i in range(12):
    frame=Image.open(C/'frames'/f'{clip}-{direction}'/f'{i:03}.png').convert('RGBA');assert frame.size==(384,640)
    assert atlas.crop((i%6*384,i//6*640,i%6*384+384,i//6*640+640)).convert('RGBA').tobytes()==frame.tobytes()
(P/'reviews/round02-independent-packet-check.json').write_text(json.dumps({'packetSHA256':sha(C/'packet.json'),'allBoundFilesMatch':not errors,'checked':checked,'frameRecords':len(frames),'errors':errors,'ffprobe':probes,'atlasPixelsMatchAll192Frames':True},indent=2)+'\n')
print('ffprobe16',all(x['r_frame_rate']=='12/1' and x['nb_frames']=='12' and x['duration']=='1.000000' for x in probes),'atlasPixelsMatch192',True)
