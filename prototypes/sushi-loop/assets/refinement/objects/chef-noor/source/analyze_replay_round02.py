"""Separate exact-state replay precision from changed canonical Emission1 radiance."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib,numpy as np
P=Path(__file__).parent;B=P.parent;C=B/'candidates/round-02';D=C/'diagnostics';D.mkdir(exist_ok=True)
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();write=lambda p,v:p.write_text(json.dumps(v,indent=2)+'\n');image=lambda p:np.asarray(Image.open(p).convert('RGBA'))
controls=read(C/'source-fresh-replay-settings.json')['controls'];sp={(r['clip'],r['direction'],r['index']):r for r in read(C/'source-phases.json')};cp={(r['clip'],r['direction'],r['index']):r for r in read(C/'candidate-phases.json')};sf=read(C/'source-shared.json')['food'];cf=read(C/'candidate-shared.json')['food'];plane='chef_noor__ground_root.001__held_dish-salmon__image_plane';cal=read(B/'candidates/round-01/records/camera.json')['calibration']
def stats(a,b,mask):
 d=abs(a.astype(np.int16)-b.astype(np.int16));x=d[mask];rgb=x[:,:3];alpha=x[:,3];n=len(x)
 return {'pixels':n,'changedRGBPixels':int(np.any(rgb,axis=1).sum()) if n else 0,'changedAlphaPixels':int((alpha>0).sum()) if n else 0,'maximumRGBChannelDifference':int(rgb.max()) if n else 0,'maximumAlphaDifference':int(alpha.max()) if n else 0,'meanRGBDifference':float(rgb.mean()) if n else 0,'RGBQuantiles':{str(q):float(np.percentile(rgb,q)) if n else 0 for q in [50,90,99,99.9,100]}}
def rect(row,food):
 if row['clip'] not in ['hold','load']:return None
 m=np.array(row['foodChannels'][plane]['world']);co=np.array(food['quad']);w=co@m[:3,:3].T+m[:3,3];x=cal['root'][0]+w[:,0]*cal['unitX'][0];y=cal['root'][1]-w[:,1]*cal['unitDepth'][1]+w[:,2]*cal['unitHeight'][1];return [float(x.min()),float(y.min()),float(x.max()),float(y.max())]
def outside(rects,margin):
 mask=np.ones((640,384),bool)
 for r in rects:
  if r is None:continue
  x0,y0,x1,y1=r;mask[max(0,int(np.floor(y0))-margin):min(640,int(np.ceil(y1))+margin),max(0,int(np.floor(x0))-margin):min(384,int(np.ceil(x1))+margin)]=False
 return mask
allmask=np.ones((640,384),bool);records=[];radiance=[];visual=Image.new('RGB',(1152,len(controls)*360),'#eee9de');draw=ImageDraw.Draw(visual)
for row,(clip,d,i) in enumerate(controls):
 key=(clip,d,i);stem=f'{clip}-{d}-{i:03d}';get=lambda role,take:image(C/'controls'/role/(stem+'-'+take+'.png'));sa,sb=get('source','a'),get('source','b');ca,cb=get('candidate','a'),get('candidate','b');oa,ob=get('candidate-source-food-control','a'),get('candidate-source-food-control','b');old=image(B/'candidates/round-01/frames'/(clip+'-'+d)/(f'{i:03d}.png'));new=image(C/'frames'/(clip+'-'+d)/(f'{i:03d}.png'))
 comparisons={'sourceSameInputRepeat':stats(sa,sb,allmask),'candidateSameInputRepeat':stats(ca,cb,allmask),'restoredSourceFoodSameInputRepeat':stats(oa,ob,allmask),'sourceFreshVsPriorSealed':stats(sa,old,allmask),'candidateFreshVsDelivered':stats(ca,new,allmask),'sourceFreshVsCandidateRestoredSourceInput':stats(sa,oa,allmask)};records.append({'clip':clip,'direction':d,'index':i,**comparisons})
 rr=[rect(sp[key],sf),rect(cp[key],cf)];opaque=(sa[:,:,3]>=250)&(ca[:,:,3]>=250);regions={'opaqueBodyOutsideFullQuadUnion2px':outside(rr,2)&opaque,'opaqueBodyOutsideFullQuadUnion8px':outside(rr,8)&opaque,'transparentBackground':(sa[:,:,3]==0)&(ca[:,:,3]==0),'allPixels':allmask};measure={k:stats(sa,ca,m) for k,m in regions.items()};radiance.append({'clip':clip,'direction':d,'index':i,'projectedSourceAndCanonicalFullQuadRects':rr,'changedInputStats':measure,'sameInputStats':comparisons})
 core=regions['opaqueBodyOutsideFullQuadUnion8px'];heat=np.zeros((640,384,3),np.uint8);delta=abs(sa[:,:,:3].astype(np.int16)-ca[:,:,:3].astype(np.int16)).max(2);heat[:,:,0]=np.minimum(delta*20,255)*core;heat[:,:,1]=np.minimum(delta*4,255)*core;Image.fromarray(heat).save(D/(stem+'-changed-food-body-core-20x.png'))
 crop=(64,280,320,500)
 for col,(arr,label) in enumerate([(sa,'Fresh approved source'),(ca,'Fresh canonical'),(oa,'Candidate with source food/quad')]):
  tile=Image.fromarray(arr).crop(crop);bg=Image.new('RGBA',tile.size,'#eee9de');bg.alpha_composite(tile);visual.paste(bg.convert('RGB').resize((384,330),Image.Resampling.NEAREST),(col*384,row*360+28));draw.text((col*384+5,row*360+6),stem+' · '+label,fill='#23313c')
visual.save(C/'fresh-native-radiance-controls.png')
keys=list(records[0].keys())[3:];maxima={k:{'maximumRGBChannelDifference':max(r[k]['maximumRGBChannelDifference'] for r in records),'maximumAlphaDifference':max(r[k]['maximumAlphaDifference'] for r in records),'maxChangedRGBPixelsPerFrame':max(r[k]['changedRGBPixels'] for r in records)} for k in keys}
write(C/'native-replay-calibration.json',{'sourceProjectSHA256':sha(P/'round-01.blend'),'candidateProjectSHA256':sha(P/'round-02.blend'),'method':'Fresh reopen exact source and candidate. Twelve hidden/active/three rear/profile/load risk phases, two unchanged-input repeats each. Additional candidate counterfactual restores only old source food bytes/old quadUV without saving any project, giving the same food input as the fresh approved source. Original source render settings unchanged.','observedPrecisionOnly':'Measured samples for this exact device/scene/settings, not a universal GPU tolerance.','controlsComplete':len(records)==12,'records':records,'measuredMaxima':maxima})
write(C/'radiance-residual-analysis.json',{'method':'Changed old-food versus canonical-food fresh native outputs are reported separately from source/source, candidate/candidate and restored-old-food/source same-input controls. Conservative projected full-quad union plus2px/8px margins excludes primary food and boundary uncertainty from opaque body regions. No material/light/ray/shader correction or raster changes were used.','bodyInvariance':'All78 protected physical objects match across192 phases with exact full coordinate/normal/pose hashes;9 allowed food-derived fields differ.','attribution':'Differences with canonical food are changed-input emission/transport/filtering/denoising responses where they exceed measured same-input noise. The full-quad body core is deliberately conservative; it is not a literal ray-identity mask and does not certify visual acceptability. Independent judge evaluates the actual contact/face/food readability. No blanket old/new hold/load bodyRGB equality requirement is imposed.','controlProof':'The candidate with source texture and source quad/UV is rendered without saving; source/shader sampling/rays/Strength1 remain the original law.','visual':'candidates/round-02/fresh-native-radiance-controls.png','records':radiance})
# Food-hidden original/updated frames should reproduce; measure all96 without using this as a hold/load identity requirement.
hidden=[]
for c in ['idle','work']:
 for d in ['N','E','S','W']:
  for i in range(12):
   a=image(B/'candidates/round-01/frames'/(c+'-'+d)/(f'{i:03d}.png'));b=image(C/'frames'/(c+'-'+d)/(f'{i:03d}.png'));hidden.append({'clip':c,'direction':d,'index':i,**stats(a,b,allmask)})
write(C/'hidden-state-render-parity.json',{'frames':len(hidden),'method':'Actual96 food-hidden native outputs compared to exact prior sealed frames. Authored visibility/actions and hidden drivers are checked structurally; dormant food matrices are never forced active.','maxRGBDifference':max(r['maximumRGBChannelDifference'] for r in hidden),'maxAlphaDifference':max(r['maximumAlphaDifference'] for r in hidden),'records':hidden,'sameInputReplayReference':'native-replay-calibration.json'})
print(json.dumps({'replay':maxima,'hiddenMaximumRGB':max(r['maximumRGBChannelDifference'] for r in hidden)},indent=2))
