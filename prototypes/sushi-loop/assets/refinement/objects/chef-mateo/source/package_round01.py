"""Lossless atlas assembly and clearly labeled review-only composites/playback."""
import json, hashlib, subprocess, shutil, html
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent;OUT=OBJ/'candidates/round01'
catalog=json.loads((OBJ/'inputs/catalog-object.json').read_text());validation=json.loads((OUT/'validation.json').read_text())
PRE=OUT/'previews';PRE.mkdir(exist_ok=True);ATL=OUT/'atlases';ATL.mkdir(exist_ok=True)
def rel(p):return str(p.relative_to(OBJ))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def composite(im,color,size=None):
 if size:im=im.resize(size,Image.Resampling.LANCZOS)
 bg=Image.new('RGBA',im.size,color);bg.alpha_composite(im);return bg.convert('RGB')
raw=[];atlases=[];playbacks={};pixelQA=[];sheets=[]
allframes=Image.new('RGB',(192*12,344*16),'#b6bbc0');draw=ImageDraw.Draw(allframes)
row=0
for clip in catalog['clips']:
 for direction,layout in clip['directions'].items():
  key=clip['id']+'-'+direction
  frames=[OUT/'raw-frames'/key/(str(i).zfill(3)+'.png') for i in range(12)]
  atlas=Image.new('RGBA',layout['atlasSize'],(0,0,0,0))
  for i,(f,rect) in enumerate(zip(frames,layout['rects'])):
   im=Image.open(f).convert('RGBA');assert im.size==(384,640)
   x,y,w,h=rect;atlas.paste(im,(x,y));assert atlas.crop((x,y,x+w,y+h)).tobytes()==im.tobytes()
   raw.append({'clip':clip['id'],'direction':direction,'index':i,'path':rel(f),'sha256':sha(f)})
   alpha=im.getchannel('A');bounds=alpha.getbbox();border=Image.new('L',im.size,0)
   ed=ImageDraw.Draw(border);ed.rectangle((0,0,383,639),outline=255,width=2)
   import PIL.ImageChops
   edge=PIL.ImageChops.multiply(alpha,border).getextrema()[1]
   pixelQA.append({'clip':clip['id'],'direction':direction,'index':i,'alphaBounds':bounds,'outer2pxMaxAlpha':edge})
   allframes.paste(composite(im,'#b6bbc0',(192,320)),(i*192,row*344+24))
   draw.text((i*192+6,row*344+6),key+' '+str(i),fill='#18212b')
  ap=ATL/(key+'.png');atlas.save(ap)
  atlases.append({'clip':clip['id'],'direction':direction,'path':rel(ap),'size':layout['atlasSize'],'columns':layout['columns'],'rows':layout['rows'],'rects':layout['rects'],'sha256':sha(ap)})
  # MP4 retains exact12/1 timing. Gray is a review background, raw PNGs unchanged.
  video=PRE/(key+'.mp4')
  command=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','lavfi','-i','color=c=0xb6bbc0:s=384x640:r=12:d=1','-framerate','12','-i',str(frames[0].parent/'%03d.png'),'-filter_complex','[0:v][1:v]overlay=shortest=1:format=auto,format=yuv420p','-frames:v','12','-r','12','-c:v','libx264','-preset','fast','-crf','18','-movflags','+faststart',str(video)]
  subprocess.run(command,check=True)
  probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=width,height,r_frame_rate,nb_frames,duration','-of','json',str(video)]))
  stream=probe['streams'][0];assert stream['r_frame_rate']=='12/1' and stream['nb_frames']=='12'
  playbacks[key]={'path':rel(video),'clip':clip['id'],'direction':direction,'fps':12,'frames':12,'loop':clip['loop'],'probe':stream}
  row+=1
allpath=PRE/'all192-native-frames-logical.png';allframes.save(allpath)
# Copy heroes from exact captures; no new render or grading.
heroes={}
for d in ['N','E','S','W']:
 path=OUT/('hero-'+d+'.png');shutil.copyfile(OUT/'raw-frames'/('idle-'+d)/'000.png',path);heroes[d]=rel(path)
four=Image.new('RGB',(384*4,672),'#b6bbc0');fd=ImageDraw.Draw(four)
for i,d in enumerate(['N','E','S','W']):
 four.paste(composite(Image.open(OBJ/heroes[d]),'#b6bbc0'),(384*i,32));fd.text((384*i+12,10),d+' actual native384x640',fill='#18212b')
fourpath=PRE/'four-view-sheet.png';four.save(fourpath)
backgrounds=Image.new('RGB',(192*4,344*3),'white');bd=ImageDraw.Draw(backgrounds)
for j,(name,col) in enumerate([('light','#f6efe3'),('gray','#b6bbc0'),('dark','#202733')]):
 for i,d in enumerate(['N','E','S','W']):
  backgrounds.paste(composite(Image.open(OBJ/heroes[d]),col,(192,320)),(i*192,j*344+24));bd.rectangle((i*192,j*344,i*192+191,j*344+23),fill=col);bd.text((i*192+8,j*344+7),name+' '+d,fill='#202733' if j<2 else '#f6efe3')
bgpath=PRE/'logical-light-gray-dark.png';backgrounds.save(bgpath)
enlarged=backgrounds.resize((1536,2064),Image.Resampling.NEAREST);edgepath=PRE/'enlarged-edge-contact-views.png';enlarged.save(edgepath)
rep=Image.new('RGB',(192*8,344),'#ddd7cb');rd=ImageDraw.Draw(rep)
for i,d in enumerate(['N','E','S','W']*2):rep.paste(composite(Image.open(OBJ/heroes[d]),'#ddd7cb',(192,320)),(i*192,24));rd.text((i*192+8,7),d+' registered frame',fill='#202733')
reppath=PRE/'repeated.png';rep.save(reppath)
# Representative contact poses retain the complete registered native frame.
contacts=Image.new('RGB',(384*4,672*4),'#b6bbc0');cd=ImageDraw.Draw(contacts)
for j,clip in enumerate(['idle','work','hold','load']):
 for i,d in enumerate(['N','E','S','W']):
  index=11 if clip=='load' else 3
  image=Image.open(OUT/'raw-frames'/(clip+'-'+d)/(str(index).zfill(3)+'.png'))
  contacts.paste(composite(image,'#b6bbc0'),(i*384,j*672+32));cd.text((i*384+8,j*672+10),clip+' '+d+' frame'+str(index),fill='#202733')
contactpath=PRE/'native-contact-states.png';contacts.save(contactpath)
previews={'four-view-sheet':rel(fourpath),'repeated':rel(reppath),'all192-native-frames':rel(allpath),'logical-backgrounds':rel(bgpath),'enlarged-edge-contact-views':rel(edgepath),'native-contact-states':rel(contactpath)}
for key,pb in playbacks.items():previews[key]=pb['path']
review=PRE/'playback.html'
cards=''.join('<article><h2>'+html.escape(k)+'</h2><video controls muted playsinline preload="metadata" '+('loop' if v['loop'] else '')+' src="'+Path(v['path']).name+'"></video><p>12 native frames at12fps; '+('loop' if v['loop'] else 'nonlooping source load')+'</p></article>' for k,v in playbacks.items())
review.write_text('<!doctype html><meta charset="utf-8"><title>Mateo round01 native playback</title><style>body{font:14px system-ui;background:#dadde1;color:#18212b}main{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}article{background:#b6bbc0;padding:12px}h2{font-size:16px}video{width:100%;max-width:384px}p{font-size:12px}</style><h1>Mateo round01 native playback</h1><p>Source timing and registration. Gray compositing is review evidence; raw PNGs and atlases retain original alpha.</p><main>'+cards+'</main>')
previews['playback-index']=rel(review)
for clip in ['work','hold','load']:
 path=PRE/('native-serving-context-'+clip+'.png')
 assert path.exists();previews['native-serving-context-'+clip]=rel(path)
qa={'all192RawFramesAndAtlasCellsExact':True,'all16ClipsActual12fps':True,'playbacks':playbacks,'pixelQA':pixelQA,'cleanOuter2px':all(p['outer2pxMaxAlpha']==0 for p in pixelQA)}
(OUT/'pixel-playback-validation.json').write_text(json.dumps(qa,indent=2)+'\n')
validation['pixelAndPlaybackEvidence']=rel(OUT/'pixel-playback-validation.json');validation['pixelChecksPass']=qa['cleanOuter2px'];validation['atlasCellsExact']=True
validation['servingContextEvidence']=rel(OUT/'serving-context-validation.json')
validation['sourcePropAndLoopEvidence']=rel(OUT/'supplemental-native-validation.json')
topologyCheck=json.loads((OUT/'topology-cleanup.json').read_text())
assert topologyCheck['allClosedManifoldPositiveVolume']
validation['newGeometryManifoldEvidence']=rel(OUT/'topology-cleanup.json')
clearances={}
for clip in ['idle','work','hold','load']:
 rows=[r for r in validation['renders'] if r['clip']==clip]
 def bounds(key):return {'min':[min(r[key]['min'][i] for r in rows) for i in range(3)],'max':[max(r[key]['max'][i] for r in rows) for i in range(3)]}
 old,new=bounds('sourceBodyBounds'),bounds('bodyBounds')
 clearances[clip]={'sourceActionBounds':old,'candidateActionBounds':new,'withinOriginalActionClearance':all(new['min'][i]>=old['min'][i]-1e-6 and new['max'][i]<=old['max'][i]+1e-6 for i in range(3))}
assert all(r['withinOriginalActionClearance'] for r in clearances.values())
validation['functionalActionClearances']=clearances
(OUT/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
delivery={'asset':'chef-mateo','round':'round01','pipeline':'native-3d','project':'source/round01.blend','recipe':'source/build_round01.py','recipeManifest':'source/round01-recipe.json','captureRecipe':'source/capture_round01.py','packagingRecipe':'source/package_round01.py','validation':rel(OUT/'validation.json'),'heroes':heroes,'previews':previews,'rawFrames':raw,'atlases':atlases,'nativeRecords':validation['nativeRecords'],'food2DDisclosure':'Original packed dish-salmon.png on source four-vertex plane; source bytes, UV, native action visibility/orientation/depth bias retained. Body is native geometry; no painted sprite replacement.','notes':'Native rest-space remodeled hair/folded bandana/apron/straps/tie/smile, baked rounded/subdivision topology; source skeleton/actions/feet/palm centers/props retained. Independent judge has not reviewed this delivery.'}
delivery['technicalVerification']='candidates/round01/delivery-verification.json'
(OBJ/'delivery.json').write_text(json.dumps(delivery,indent=2)+'\n')
print(json.dumps({'frames':len(raw),'atlases':len(atlases),'clips':len(playbacks),'pixelChecksPass':qa['cleanOuter2px'],'delivery':str(OBJ/'delivery.json')}))
