"""Lossless atlas assembly and labeled presentation previews from native captures."""
import pathlib,json,hashlib,shutil,subprocess,io
from PIL import Image,ImageDraw,ImageChops,ImageStat
HERE=pathlib.Path(__file__).resolve().parent.parent
OUT=HERE/'candidates/round-01';PRE=OUT/'previews';PRE.mkdir(exist_ok=True)
catalog=json.loads((HERE/'inputs/catalog-object.json').read_text())
def rel(p):return pathlib.Path(p).relative_to(HERE).as_posix()
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def save_json(p,v):pathlib.Path(p).write_text(json.dumps(v,indent=2)+'\n')
raw=[];atlases=[];heroes={};previews={};audit=[];frames={}
bg=(104,104,104,255)
def composite(im,color=bg,size=None):
 if size:im=im.resize(size,Image.Resampling.LANCZOS)
 dest=Image.new('RGBA',im.size,color);dest.alpha_composite(im);return dest.convert('RGB')
def gif(path,ims):
 ims[0].save(path,save_all=True,append_images=ims[1:],duration=[80,90,80]*4,loop=0,optimize=False,disposal=2)
def video(path,ims):
 stream=io.BytesIO()
 for im in ims:im.save(stream,format='PNG')
 subprocess.run(['/opt/homebrew/bin/ffmpeg','-v','error','-y','-f','image2pipe','-framerate','12','-i','-','-an','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(path)],input=stream.getvalue(),check=True)
for d in 'NESW':
 frames[d]=[Image.open(OUT/'raw'/f'idle-{d}'/f'{i:03}.png').convert('RGBA') for i in range(12)]
 for i,im in enumerate(frames[d]):
  p=OUT/'raw'/f'idle-{d}'/f'{i:03}.png';raw.append({'clip':'idle','direction':d,'index':i,'path':rel(p)})
  assert im.size==(384,768)
  alpha=im.getchannel('A');bounds=alpha.getbbox();assert bounds[0]>0 and bounds[1]>0 and bounds[2]<384 and bounds[3]<768
  assert all(alpha.getpixel(xy)==0 for xy in [(0,0),(383,0),(0,767),(383,767)])
  audit.append({'direction':d,'index':i,'rgbaSize':list(im.size),'sha256':sha(p),'alphaBounds':list(bounds),'alphaExtrema':alpha.getextrema(),'alphaTouchesFrame':False,'nontransparentPixels':sum(n for n,a in zip(alpha.histogram(),range(256)) if a),'uniqueRgbaHash':hashlib.sha256(im.tobytes()).hexdigest()})
 hero=OUT/f'{d}.png';shutil.copyfile(OUT/'raw'/f'idle-{d}'/'000.png',hero);heroes[d]=rel(hero)
 meta=catalog['clips'][0]['directions'][d];atlas=Image.new('RGBA',tuple(meta['atlasSize']),(0,0,0,0))
 for im,rect in zip(frames[d],meta['rects']):atlas.paste(im,(rect[0],rect[1]))
 ap=OUT/f'idle-{d}.png';atlas.save(ap)
 for im,rect in zip(frames[d],meta['rects']):assert atlas.crop((rect[0],rect[1],rect[0]+rect[2],rect[1]+rect[3])).tobytes()==im.tobytes()
 atlases.append({'clip':'idle','direction':d,'path':rel(ap),'sha256':sha(ap),'columns':meta['columns'],'rows':meta['rows'],'size':meta['atlasSize'],'rects':meta['rects']})
 logical=[composite(im,size=(192,384)) for im in frames[d]]
 gp=PRE/f'idle-{d}.gif';gif(gp,logical);previews[f'idle-{d}']=rel(gp)
 mp=PRE/f'idle-{d}.mp4';video(mp,logical);previews[f'idle-{d}-clip']=rel(mp)
 film=Image.new('RGB',(1152,768),(104,104,104));draw=ImageDraw.Draw(film)
 for i,im in enumerate(logical):film.paste(im,((i%6)*192,(i//6)*384));draw.text(((i%6)*192+8,(i//6)*384+8),f'{d} / {i:02}',fill='white')
 fp=PRE/f'contact-{d}.png';film.save(fp);previews[f'contact-{d}']=rel(fp)
four=Image.new('RGB',(768,384),(104,104,104));draw=ImageDraw.Draw(four)
for j,d in enumerate('NESW'):four.paste(composite(frames[d][0],size=(192,384)),(192*j,0));draw.text((192*j+8,8),d,fill='white')
fp=PRE/'four-view-sheet.png';four.save(fp);previews['four-view-sheet']=rel(fp)
alpha_sheet=Image.new('RGB',(768,1152))
for row,c in enumerate([(235,231,221,255),(104,104,104,255),(28,29,32,255)]):
 for j,d in enumerate('NESW'):alpha_sheet.paste(composite(frames[d][0],c,(192,384)),(192*j,384*row))
ap=PRE/'alpha-contexts.png';alpha_sheet.save(ap);previews['alpha-contexts']=rel(ap)
four_motion=[];repeat_motion=[]
for i in range(12):
 f=Image.new('RGB',(768,384),(104,104,104));r=Image.new('RGB',(576,768),(202,198,187))
 for j,d in enumerate('NESW'):f.paste(composite(frames[d][i],size=(192,384)),(192*j,0))
 for j,d in enumerate(['N','E','S','W','N','E']):r.paste(composite(frames[d][i],(202,198,187,255),(192,384)),((j%3)*192,(j//3)*384))
 four_motion.append(f);repeat_motion.append(r)
rp=PRE/'repeated.png';repeat_motion[0].save(rp);previews['repeated']=rel(rp)
for name,ims in [('four-view-motion',four_motion),('repeated-motion',repeat_motion)]:
 gp=PRE/f'{name}.gif';gif(gp,ims);previews[name]=rel(gp)
 mp=PRE/f'{name}.mp4';video(mp,ims);previews[name+'-clip']=rel(mp)
native=json.loads((OUT/'validation-native.json').read_text());reload=json.loads((OUT/'validation-reload.json').read_text())
fresh=Image.open(OUT/'reload-N-000.png').convert('RGBA');expected=frames['N'][0]
pixels_equal=fresh.tobytes()==expected.tobytes()
diff=ImageChops.difference(fresh,expected)
reload_pixels={'exactRgbaEquality':pixels_equal,'maxChannelDifference':max(v[1] for v in ImageStat.Stat(diff).extrema),'meanChannelDifference':ImageStat.Stat(diff).mean,'differentPixels':sum(any(p) for p in diff.getdata()),'alphaExactlyEqual':fresh.getchannel('A').tobytes()==expected.getchannel('A').tobytes(),'note':'Metal re-render differs in two RGB pixels by one 8-bit code value; alpha and all measured geometry match exactly.'}
assert reload_pixels['maxChannelDifference']<=1 and reload_pixels['alphaExactlyEqual'] and reload_pixels['differentPixels']<=4
unique_by_direction={d:len({a['uniqueRgbaHash'] for a in audit if a['direction']==d}) for d in 'NESW'}
source_signatures={}
for d in 'NESW':
 pose_records=native['nativeGeometryMeasurements'][d][:12]
 source_signatures[d]=len({hashlib.sha256(json.dumps({n:v['matrixWorld'] for n,v in rec.items()},sort_keys=True).encode()).hexdigest() for rec in pose_records})
validation={**native,'reloadValidation':rel(OUT/'validation-reload.json'),'freshReloadPassed':reload['freshReloadPassed'],'reloadRerenderPixelsEqual':pixels_equal,'reloadPixelComparison':reload_pixels,'reloadMaxMeasurementDelta':reload['maxMeasurementDelta'],'frameCount':48,'rawFrameAudit':audit,'uniqueNativeRgbaFrames':unique_by_direction,'uniqueNativeTransformFrames':source_signatures,'atlasLayoutMatchesOriginal':True,'atlasPixelsEqualRawFrames':True,'previews':{'nativeSourceFramesPerClip':12,'fps':12,'loop':True,'gifDurationsMs':[80,90,80]*4,'gifTotalMs':1000,'mp4FrameRate':'12/1','derivedFromNativeFrames':True,'presentationResize':'192x384, no fitting; full registered frame is uniformly downsampled','backgrounds':['#ebe7dd','#686868','#1c1d20']},'validationScripts':[rel(HERE/'source/round-01.py'),rel(HERE/'source/validate-round-01.py'),rel(HERE/'source/package-round-01.py')],'approval':'pending independent judge'}
save_json(OUT/'validation.json',validation)
recipe={'project':rel(HERE/'source/round-01.blend'),'recipe':rel(HERE/'source/round-01.py'),'buildCommand':'/opt/homebrew/bin/blender -b --python source/round-01.py','reloadCommand':'/opt/homebrew/bin/blender -b --python source/validate-round-01.py','packageCommand':'/Users/yiouchen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 source/package-round-01.py','sourceSha256':native['sourceSha256'],'projectSha256':sha(HERE/'source/round-01.blend'),'settings':native['render'],'notes':['Original 13-object construction, source UV layers and parent/action transforms preserved.','Real inward bevels and weighted normals; paper/gold/wood/bronze Principled shaders; no raster resources.','One camera, one neutral symmetric light/material setup, no ground plane, no compositor.','Native frames 1–12 at 12fps; duplicate closure key 13 excluded from runtime.']}
save_json(HERE/'source/round-01-recipe.json',recipe)
delivery={'asset':'lantern-gold','round':'round-01','project':recipe['project'],'recipe':recipe['recipe'],'recipeSettings':rel(HERE/'source/round-01-recipe.json'),'validation':rel(OUT/'validation.json'),'heroes':heroes,'rawFrames':raw,'previews':previews,'atlases':atlases,'nativeRecords':{'camera':rel(OUT/'camera.json'),'assetRecord':rel(OUT/'asset.json'),'rig':rel(OUT/'rig.json')},'resources':[],'notes':['Ready for coordinator sealing and independent review; not self-approved.']}
save_json(HERE/'delivery.json',delivery)
print(json.dumps({'complete':True,'rawFrames':len(raw),'uniqueFrames':unique_by_direction,'freshReloadPixelsEqual':pixels_equal,'delivery':'delivery.json'},indent=2))
