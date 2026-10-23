import pathlib,json,hashlib,shutil,math
from PIL import Image,ImageDraw,ImageChops
O=pathlib.Path(__file__).resolve().parent;E=O.parent.parent;R=O/'resources';D=O/'native-source';P=O/'previews';P.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,v):(O/n).write_text(json.dumps(v,indent=2)+'\n')
r=json.loads((O/'source-replay-audit.json').read_text());cl={};per={}
for di in 'NESW':
 frames=[Image.open(D/f'active-{di}-{i:02d}.png').convert('RGBA') for i in range(1,14)]
 cl[di]={'exactRGBA':frames[0].tobytes()==frames[12].tobytes(),'frame1SHA256':sha(D/f'active-{di}-01.png'),'frame13SHA256':sha(D/f'active-{di}-13.png')}
 per[di]={'uniqueRuntimeRGBA':len(set(im.tobytes() for im in frames[:12])),'pixelChangeBoxesFromFrame1':[ImageChops.difference(frames[0],im).getbbox() for im in frames[:12]]}
 sheet=Image.new('RGB',(12*120,172),'#73818b');dr=ImageDraw.Draw(sheet)
 for i,im in enumerate(frames[:12]):
  # Fixed crop for this facing across all phases; full registered cells are retained separately.
  lim=im.resize((192,352),Image.Resampling.LANCZOS);crop=lim.crop((24,158,168,310)).resize((114,120),Image.Resampling.LANCZOS);tile=Image.new('RGBA',crop.size,'#c5cdd0');tile.alpha_composite(crop);sheet.paste(tile.convert('RGB'),(i*120,30));dr.text((i*120+4,6),f'{di} {i+1:02d}',fill='white')
 sheet.save(P/f'active-strip-{di}.png')
 clip={'id':'sub-collector-inlet','frameSize':[192,352],'root':[96,248],'sourceScale':2,'footprint':[1,1],'directionFootprints':{k:[1,1] for k in 'NESW'},'rootCell':[.5,.5],'layer':2,'clips':[]}
 for state,count in [('idle',1),('active',12)]:
  cols=1 if count==1 else 6;rows=math.ceil(count/cols);atlas=Image.new('RGBA',(384*cols,704*rows));rects=[]
  for i in range(count):atlas.paste(Image.open(D/f'{state}-{di}-{i+1:02d}.png'),((i%cols)*384,(i//cols)*704));rects.append([(i%cols)*384,(i//cols)*704,384,704])
  out=O/'consumer-inputs'/f'collector-{state}-{di}.png';out.parent.mkdir(exist_ok=True);atlas.save(out)
# A full registered logical-scale sheet, identical global scale in all four views.
sheet=Image.new('RGB',(4*192,352+28),'#c4cdd0');dr=ImageDraw.Draw(sheet)
for idx,di in enumerate('NESW'):
 im=Image.open(D/f'idle-{di}-01.png').convert('RGBA').resize((192,352),Image.Resampling.LANCZOS);bg=Image.new('RGBA',im.size,'#c4cdd0');bg.alpha_composite(im);sheet.paste(bg.convert('RGB'),(idx*192,28));dr.text((idx*192+12,8),f'Original native idle {di}',fill='#152333')
sheet.save(P/'idle-logical-all4.png')
# Source matrix/action evaluation measurements, no alpha-bound geometry inference.
rec=[x for x in r['records'] if x['clip']=='idle' and x['direction']=='S'][0];b=rec['worldBounds'];mount=[[0,-.52,.09][i]+.4*b[j][i] for j in range(2) for i in range(3)];mb=[mount[:3],mount[3:]];reservation=[[-.425,-.275,0],[.425,.25,.4]]
conf={'sourceNeutralCanonicalBounds':b,'frozenLocalReservation':reservation,'frozenMountedReservation':[[-.17,-.63,.09],[.17,-.42,.25]],'originalAtFrozenMountBounds':mb,'forwardExcessWorld':max(0,-.63-mb[0][1]),'topExcessWorld':max(0,mb[1][2]-.25),'actualSourceMouthAtMount':[0,-.52+.4*(-.26),.09+.4*.24],'frozenProvisionalMouth':[0,-.615,.17],'legacyReference':[0,-.53,.21],'pairedLampBaseMinimumZ':.2629999816417694,'originalTopToLampBaseGap':.2629999816417694-mb[1][2],'reservationTopToLampBaseGap':.2629999816417694-.25,'allSourceRuntimeInsideLockedFrame':all(all(x['logicalBounds'][0][i]>=0 and x['logicalBounds'][1][i]<[192,352][i] for i in range(2)) for x in r['records'])}
write('source-motion-and-conflicts.json',{'nativeMechanics':'One static neutral idle frame. Active mouth scaleZ .92..1.0; scaleX/Y remain1. Three guard rotationX channels oscillate with distinct phases around ±.06 radians; rotationsY/Z remain0. No bones, translations, intake particles, projectile, cable or electrical effect channels.','runtime':{'idle':1,'active':12,'fps':12,'periodSeconds':1,'closingNativeFrame':13,'runtimeOrder':list(range(1,13))},'closurePixels':cl,'runtimeUniqueness':per,'conflicts':conf,'qualification':'Source conflicts are reconstruction requirements, not permission to move the mount, camera or root. The source height metadata .55 exceeds its measured .435 top; proposed local top .4 is the stricter assembled constraint.'})
# Freeze actual independently rendered consumer input atlases and current separate context art.
lib=json.loads((R/'library.json').read_text());objects=lib['objects'];selected=[];closure=[]
for aid in ['sub-hull-panels','sub-harpoon-mount','creature-eel']:
 a=next(x for x in objects if x['id']==aid);a=json.loads(json.dumps(a));chosen='swim' if aid=='creature-eel' else 'idle';a['clips']=[x for x in a['clips'] if x['id']==chosen]
 for c in a['clips']:
  for di,entry in c['directions'].items():
   src=pathlib.Path.cwd()/'prototypes/sushi-loop/assets/production'/entry['image'];out=O/'consumer-inputs'/f'{aid}-{c["id"]}-{di}.png';shutil.copyfile(src,out);closure.append({'source':str(src),'snapshot':str(out.relative_to(E)),'sha256':sha(out)});entry['image']=str(out.relative_to(O))
 selected.append(a)
collector={'id':'sub-collector-inlet','frameSize':[192,352],'root':[96,248],'sourceScale':2,'footprint':[1,1],'rootCell':[.5,.5],'layer':2,'clips':[]}
for state,count in [('idle',1),('active',12)]:
 collector['clips'].append({'id':state,'frames':count,'fps':12,'loop':state=='active','directions':{di:{'image':f'consumer-inputs/collector-{state}-{di}.png','columns':1 if count==1 else 6,'rows':1 if count==1 else 2,'atlasSize':[384 if count==1 else 2304,704 if count==1 else 1408],'rects':[[i%6*384,i//6*704,384,704] for i in range(count)]} for di in 'NESW'}})
selected.append(collector)
main={'id':'submarine-preparation-assembled','frameSize':[320,384],'root':[160,288],'sourceScale':2,'footprint':[1,2],'rootCell':[.5,1],'layer':2,'clips':[{'id':'upgraded-dock-ready','frames':1,'fps':12,'loop':False,'directions':{di:{'image':f'mounted-source/legacy-collector-on-frozen-body-{di}.png','columns':1,'rows':1,'atlasSize':[640,768],'rects':[[0,0,640,768]]} for di in 'NESW'}}]};selected.append(main)
write('consumer-library.json',{'cellSize':128,'objects':selected,'qualification':'Assembled sprite is an actual registered native render of static frozen body plus original neutral collector at frozen mount. Hull and harpoon on main are provisional. Collector, hull, harpoon and eel appear as separate independent sprites beside it. This is preparation/source evidence only, not approval or active integrated animation.'});write('context-sprite-snapshots.json',closure)
print(json.dumps({'conflicts':conf,'unique':{k:v['uniqueRuntimeRGBA'] for k,v in per.items()},'closure':cl},indent=2))
