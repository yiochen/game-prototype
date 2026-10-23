"""Lossless original atlases, actual12fps playback, native review composites only."""
import sys,json,hashlib,subprocess,shutil,html,math
sys.dont_write_bytecode=True
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent;OUT=OBJ/'candidates/round03';PRE=OUT/'previews';ATL=OUT/'atlases';PRE.mkdir(exist_ok=True);ATL.mkdir(exist_ok=True)
cat=json.loads((OBJ/'inputs/catalog-object.json').read_text());v=json.loads((OUT/'validation.json').read_text());assert not v['auditOnly'] and v['nativeChecksPass'];brief=OBJ/'brief-v3-held-food-semantic-contact.json'
def rel(p):return str(p.relative_to(OBJ))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,o):p.write_text(json.dumps(o,indent=2)+'\n')
def comp(im,col,size=None):
 im=im.convert('RGBA')
 if size:im=im.resize(size,Image.Resampling.LANCZOS)
 bg=Image.new('RGBA',im.size,col);bg.alpha_composite(im);return bg.convert('RGB')
raw=[];atlases=[];playbacks={};qa=[];previews={};allframes=Image.new('RGB',(2304,344*16),'#b6bbc0');ad=ImageDraw.Draw(allframes);row=0
for clip in cat['clips']:
 state=Image.new('RGB',(2304,1376),'#b6bbc0');sd=ImageDraw.Draw(state)
 for dn,(d,layout) in enumerate(clip['directions'].items()):
  key=clip['id']+'-'+d;files=[OUT/'raw-frames'/key/(str(i).zfill(3)+'.png') for i in range(12)];atlas=Image.new('RGBA',layout['atlasSize'])
  assert layout['atlasSize']==[2304,1280] and layout['columns']==6 and layout['rows']==2
  for i,(f,rect) in enumerate(zip(files,layout['rects'])):
   im=Image.open(f).convert('RGBA');assert im.size==(384,640);x,y,w,h=rect;atlas.paste(im,(x,y));assert atlas.crop((x,y,x+w,y+h)).tobytes()==im.tobytes();a=im.getchannel('A');border=Image.new('L',im.size);ImageDraw.Draw(border).rectangle((0,0,383,639),outline=255,width=2);edge=ImageChops.multiply(a,border).getextrema()[1];qa.append({'clip':clip['id'],'direction':d,'index':i,'alphaBounds':a.getbbox(),'outer2pxMaxAlpha':edge});raw.append({'clip':clip['id'],'direction':d,'index':i,'path':rel(f),'sha256':sha(f)})
   pic=comp(im,'#b6bbc0',(192,320));allframes.paste(pic,(i*192,row*344+24));ad.text((i*192+6,row*344+6),key+' '+str(i),fill='#18212b');state.paste(pic,(i*192,dn*344+24));sd.text((i*192+6,dn*344+6),key+' '+str(i),fill='#18212b')
  ap=ATL/(key+'.png');atlas.save(ap);atlases.append({'clip':clip['id'],'direction':d,'path':rel(ap),'size':layout['atlasSize'],'columns':6,'rows':2,'rects':layout['rects'],'sha256':sha(ap)})
  video=PRE/(key+'.mp4');subprocess.run(['/opt/homebrew/bin/ffmpeg','-hide_banner','-loglevel','error','-y','-f','lavfi','-i','color=c=0xb6bbc0:s=384x640:r=12:d=1','-framerate','12','-i',str(files[0].parent/'%03d.png'),'-filter_complex','[0:v][1:v]overlay=shortest=1:format=auto,format=yuv420p','-frames:v','12','-r','12','-c:v','libx264','-preset','fast','-crf','18','-movflags','+faststart',str(video)],check=True)
  probe=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-show_entries','stream=width,height,r_frame_rate,nb_frames,duration','-of','json',str(video)]))['streams'][0];assert probe['r_frame_rate']=='12/1' and probe['nb_frames']=='12';playbacks[key]={'path':rel(video),'clip':clip['id'],'direction':d,'fps':12,'frames':12,'loop':clip['loop'],'probe':probe};previews[key]=rel(video);row+=1
 statepath=PRE/(clip['id']+'-all48-native-frames-logical.png');state.save(statepath);previews[clip['id']+'-all48-frames']=rel(statepath)
allpath=PRE/'all192-native-frames-logical.png';allframes.save(allpath);previews['all192-native-frames']=rel(allpath)
heroes={}
for d in ['N','E','S','W']:
 p=OUT/('hero-'+d+'.png');shutil.copyfile(OUT/'raw-frames'/('hold-'+d)/'000.png',p);heroes[d]=rel(p)
four=Image.new('RGB',(1536,672),'#b6bbc0');fd=ImageDraw.Draw(four)
for i,d in enumerate(heroes):four.paste(comp(Image.open(OBJ/heroes[d]),'#b6bbc0'),(i*384,32));fd.text((i*384+8,10),d+' hold0 exact native384x640',fill='#18212b')
p=PRE/'four-view-sheet.png';four.save(p);previews['four-view-sheet']=rel(p)
bgs=Image.new('RGB',(768,1032));bd=ImageDraw.Draw(bgs)
for j,(name,col) in enumerate([('light','#f6efe3'),('gray','#b6bbc0'),('dark','#202733')]):
 for i,d in enumerate(heroes):
  bd.rectangle((i*192,j*344,i*192+191,j*344+343),fill=col);bgs.paste(comp(Image.open(OBJ/heroes[d]),col,(192,320)),(i*192,j*344+24));bd.text((i*192+6,j*344+6),name+' '+d+' logical192x320',fill='#18212b' if j<2 else '#f6efe3')
p=PRE/'logical-light-gray-dark.png';bgs.save(p);previews['logical-backgrounds']=rel(p);p=PRE/'enlarged-edge-contact-views.png';bgs.resize((1536,2064),Image.Resampling.NEAREST).save(p);previews['enlarged-edge-contact-views']=rel(p)
rep=Image.new('RGB',(1536,344),'#ddd7cb');rd=ImageDraw.Draw(rep)
for i,d in enumerate(list(heroes)*2):rep.paste(comp(Image.open(OBJ/heroes[d]),'#ddd7cb',(192,320)),(i*192,24));rd.text((i*192+6,6),d+' registered logical frame',fill='#18212b')
p=PRE/'repeated.png';rep.save(p);previews['repeated']=rel(p)
contacts=Image.new('RGB',(1536,2688),'#b6bbc0');cd=ImageDraw.Draw(contacts)
for j,c in enumerate(['idle','work','hold','load']):
 for i,d in enumerate(heroes):
  n=11 if c=='load' else 3;im=Image.open(OUT/'raw-frames'/(c+'-'+d)/(str(n).zfill(3)+'.png'));contacts.paste(comp(im,'#b6bbc0'),(i*384,j*672+32));cd.text((i*384+8,j*672+10),c+' '+d+' frame'+str(n),fill='#18212b')
p=PRE/'native-contact-states.png';contacts.save(p);previews['native-contact-states']=rel(p)
# All visible contacts in one globally registered crop; no individual fitting.
for c in ['hold','load']:
 sheet=Image.new('RGB',(3072,896),'#b6bbc0');dd=ImageDraw.Draw(sheet)
 for j,d in enumerate(heroes):
  for i in range(12):
   im=Image.open(OUT/'raw-frames'/(c+'-'+d)/(str(i).zfill(3)+'.png')).crop((64,280,320,480));sheet.paste(comp(im,'#b6bbc0'),(i*256,j*224+24));dd.text((i*256+6,j*224+6),c+' '+d+' '+str(i),fill='#18212b')
 p=PRE/(c+'-all48-contact-crops.png');sheet.save(p);previews[c+'-all48-contact-crops']=rel(p)
phone=Image.new('RGB',(414,1800),'#f5efe4');pd=ImageDraw.Draw(phone);pd.text((20,20),'Mateo / canonical salmon / logical phone review',fill='#18212b')
for i,d in enumerate(heroes):
 y=60+i*420;pd.rounded_rectangle((18,y,396,y+400),radius=18,fill='#d9dde0');pd.text((32,y+14),d+' hold0 / exact192x320 logical display',fill='#18212b');phone.paste(comp(Image.open(OBJ/heroes[d]),'#d9dde0',(192,320)),(111,y+52))
p=PRE/'phone-logical-four-view.png';phone.save(p);previews['phone-logical-four-view']=rel(p)
for c in ['work','hold','load']:
 p=PRE/('native-serving-context-'+c+'.png');assert p.exists();previews['native-serving-context-'+c]=rel(p)
for name,p in [('calibrated-radiance-comparison',PRE/'calibrated-radiance-comparison.png')]:assert p.exists();previews[name]=rel(p)
review=PRE/'playback.html';cards=''.join('<article><h2>'+html.escape(k)+'</h2><video controls muted playsinline preload="metadata" '+('loop' if x['loop'] else '')+' src="'+Path(x['path']).name+'"></video><p>12frames /12fps. '+('Source loop.' if x['loop'] else 'Source nonlooping load.')+'</p></article>' for k,x in playbacks.items());review.write_text('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Mateo round03 canonical food playback</title><style>body{font:14px system-ui;background:#ece6da;color:#18212b;margin:16px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(192px,1fr));gap:16px}article{background:#b6bbc0;padding:12px;border-radius:12px}h2{font-size:16px}video{width:192px;height:320px;max-width:100%}p{font-size:12px}</style><h1>Mateo canonical food / native playback</h1><p>Exact approved native body. Canonical2D salmon on one fixed native quad. Gray is review compositing; raw frames and atlases retain alpha.</p><main>'+cards+'</main>');previews['playback-index']=rel(review)
assert len(raw)==192 and len(atlases)==16 and len(playbacks)==16
save(OUT/'pixel-playback-validation.json',{'rawFrames':192,'exactAtlasCells':192,'atlases':16,'atlasSize':[2304,1280],'originalLayoutsExact':True,'actual12fpsClips':16,'playbacks':playbacks,'cleanOuter2px':all(x['outer2pxMaxAlpha']==0 for x in qa),'pixelQA':qa})
v.update({'pixelChecksPass':all(x['outer2pxMaxAlpha']==0 for x in qa),'atlasCellsExact':True,'pixelAndPlaybackEvidence':rel(OUT/'pixel-playback-validation.json'),'servingContextEvidence':rel(OUT/'serving-context-validation.json'),'calibratedRadianceEvidence':rel(OUT/'calibrated-radiance-validation.json')});save(OUT/'validation.json',v)
delivery={'asset':'chef-mateo','round':'round03','pipeline':'native-3d','referenceBrief':str(brief.relative_to(OBJ)),'referenceBriefSHA256':sha(brief),'project':'source/round03.blend','recipe':'source/build_round03.py','recipeManifest':'source/round03-recipe.json','captureRecipe':'source/capture_round03.py','packagingRecipe':'source/package_round03.py','validation':rel(OUT/'validation.json'),'heroes':heroes,'previews':previews,'rawFrames':raw,'atlases':atlases,'nativeRecords':v['nativeRecords'],'technicalVerification':'candidates/round03/delivery-verification.json','food2DDisclosure':'Exact canonical731x505 RGBA salmon4389d1...be4, packed and portable, mapped with fullUV onto one fixed native food quad. Held display remains explicitly2D inside approved native3D body. Original prop/plane matrices, actions, visibility, yaw and0.6visible camera-toward law preserved.','notes':'Dependency-only round03; all approved nonfood native definitions/settings and all192 actual body/rig/knife/contact evaluations exact. Honest canonical-food radiance deltas reported separately from calibrated same-input controls. Coordinator seals; independent judge decision pending.','recipeResources':{'common':'source/round03_common.py','baseline':'source/round03-baseline.json','approvedBody':'source/round02.blend','nativeActions':'source/native_actions.py','canonicalSalmon':'source/round03-resources/canonical-salmon.png','historicalControlSalmon':'source/round03-resources/historical-salmon.png','controlRecipe':'source/control_round03.py','radianceRecipe':'source/compare_radiance_round03.py','contextRecipe':'source/context_round03.py','contextNeighborSource':'source/original-library.blend','contextNeighborRig':'source/context-customer-rosa-rig.json','verificationRecipe':'source/verify_delivery_round03.py'},'resources':['source/round03-resources/canonical-salmon.png','source/round03-resources/historical-salmon.png'],'supplementalEvidence':{'dependencyChange':'candidates/round03/dependency-change.json','calibratedRadiance':'candidates/round03/calibrated-radiance-validation.json','all192Audit':'candidates/round03/audit-validation.json'}}
save(OBJ/'delivery-round03.json',delivery);print(json.dumps({'delivery':str(OBJ/'delivery-round03.json'),'frames':192,'atlases':16,'clips':16,'cleanOuter2px':v['pixelChecksPass']}))
