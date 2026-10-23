from pathlib import Path
from PIL import Image
import json,numpy as np,hashlib,math
B=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/belt-straight-n');P=B/'candidates/round-11'
M=json.load(open(P/'feedback/feedback-metrics.json'));errors=[];count=0;clocks=[];same_relative=0
paper=np.array([255,239,207],float)/255;inkcolor=np.array([37,59,59],float)/255;dist=paper-inkcolor;bg=np.array([233,205,163],float)
for c in M['cases']:
 x0,y0,x1,y1=c['cropBox'];computed={}
 assert abs(c['candidateStroke']-max(1.4,c['pitch']*.032) if c['symbol']=='timer' else c['candidateStroke']-1.4)<1e-6
 for mode,r in c['modes'].items():
  im=Image.open(r['path']).convert('RGBA');box=im.getchannel('A').getbbox()
  if not(box[0]>=x0 and box[1]>=y0 and box[2]<=x1 and box[3]<=y1):errors.append([c['name'],mode,'content outside crop'])
  a=np.asarray(im.crop(c['cropBox']),dtype=float)/255;alpha=a[:,:,3];total=alpha.sum();yy,xx=np.indices(alpha.shape);xx=xx+x0;yy=yy+y0;centroid=np.array([((xx+.5)*alpha).sum()/total,((yy+.5)*alpha).sum()/total]);computed[mode]={'alpha':total,'centroid':centroid.tolist()}
  if abs(total-r['alphaMass'])>1e-6 or max(abs(centroid-np.array(r['alphaCentroid'])))>1e-7:errors.append([c['name'],mode,'alpha metric'])
  if c['symbol']=='clock':
   ink=np.clip(((paper*alpha[:,:,None]-a[:,:,:3])*dist).sum(2)/(dist@dist),0,1);cx,cy=c['center'];hand=(abs(xx+.5-cx)<=1.4/2+.5)&(yy+.5>=cy-c['pitch']*.05)&(yy+.5<=cy);mass=ink.sum();peak=ink[hand].max();computed[mode].update(ink=float(mass),hand=float(peak))
   if abs(mass-r['inkCoverageMass'])>1e-6 or abs(peak-r['handRegionPeakInkCoverage'])>1e-7:errors.append([c['name'],mode,'ink metric'])
  rgb=np.clip(a[:,:,:3]*255+bg*(1-a[:,:,3:]),0,255).round().astype('uint8');cropfile=P/'previews'/(c['name']+'-'+mode+'-crop.png')
  if not np.array_equal(rgb,np.asarray(Image.open(cropfile).convert('RGB'))):errors.append([c['name'],mode,'display crop'])
  count+=1
 if c['symbol']=='clock':clocks.append({'name':c['name'],'candidateInkRatio':computed['candidate']['ink']/computed['baseline']['ink'],'oldInkRatio':computed['old']['ink']/computed['baseline']['ink'],'candidateHandPeak':computed['candidate']['hand']})
 if c['symbol']=='timer' and c['pitch'] in [128,55]:
  if Path(c['modes']['old']['path']).read_bytes()!=Path(c['modes']['candidate']['path']).read_bytes():errors.append([c['name'],'relative timer changed'])
  else:same_relative+=1
# Confirm all60 new app editor sheet cells are exact documented reductions.
app_cells=0
for orient,sz,row in [('portrait',(195,422),446),('landscape',(288,200),224)]:
 sheet=Image.open(P/f'coordinator-game/all30-editor-{orient}.png').convert('RGB');files=sorted((P/f'coordinator-game/editor-{orient}').glob('*.png'))
 for i,f in enumerate(files):
  im=Image.open(f).convert('RGB');c=im.copy();c.thumbnail(sz,Image.Resampling.BICUBIC,reducing_gap=2.0);x=i%6*sz[0];y=i//6*row+24
  if not np.array_equal(np.asarray(sheet.crop((x,y,x+sz[0],y+sz[1]))),np.asarray(c)):errors.append([f.name,'app contact'])
  app_cells+=1
# Native/source/runtime dependencies and delivery are bound to this exact packet.
packet=json.load(open(P/'packet.json'));bound={str((P/r['path']).resolve()):r['sha256'] for g in ['files','candidateRenders','previews'] for r in packet[g].values()};delivery=json.load(open(P/'delivery.json'))
for r in delivery['rawFrames']+delivery['atlases']:
 q=Path(r['path']);h=hashlib.sha256(q.read_bytes()).hexdigest()
 if bound.get(str(q.resolve()))!=h:errors.append([str(q),'unbound'])
code=json.load(open(P/'coordinator-game/verification.json'))['implementation'];bindings={}
root=B.parents[5]
for n,r in code.items():
 candidate=B/r['proposal'];production=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype')/r['productionPath'];bindings[n]=hashlib.sha256(candidate.read_bytes()).hexdigest()==r['sha256']==hashlib.sha256(production.read_bytes()).hexdigest()
 if not bindings[n]:errors.append([n,'production code binding'])
result={'feedbackCases':len(M['cases']),'rawPNGsChecked':count,'rawToDisplayCropsVerified':count,'metricErrors':errors,'clockMetrics':clocks,'candidateClockInkRatioRange':[min(c['candidateInkRatio'] for c in clocks),max(c['candidateInkRatio'] for c in clocks)],'minimumCandidateHandPeak':min(c['candidateHandPeak'] for c in clocks),'relativeTimerPNGsByteUnchanged':same_relative,'newEditorContactCellsVerified':app_cells,'rawFramesExplicitlyBound':len(delivery['rawFrames']),'atlasesExplicitlyBound':len(delivery['atlases']),'installedCodeBindings':bindings}
Path('/tmp/judge_belt_round11_checks.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
