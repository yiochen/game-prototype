from PIL import Image,ImageDraw
import numpy as np,json,pathlib,hashlib,shutil
P=pathlib.Path(__file__).resolve().parents[1];O=P/'candidates/round-01';C=O/'consumer';PRE=O/'previews';A=O/'atlases';IN=O/'independent-runs'
for p in [PRE,A,IN,C/'inputs',C/'runtime']:p.mkdir(parents=True,exist_ok=True)
H=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest();V=json.loads((O/'validation.json').read_text());F=json.loads((P/'inputs/family-settings.json').read_text());N=P.parent/'belt-straight-n/candidates/round-08';E=P.parent/'belt-straight-e/candidates/round-01';S=P.parent/'belt-straight-s/candidates/round-01';dirs='NESW';mapping=V['nativeAssemblyContract']['sameFlowMappings'];patterns=V['nativeAssemblyContract']['patterns']
for d in dirs:
 atlas=Image.new('RGBA',(2304,2816))
 for i in range(24):atlas.paste(Image.open(O/'frames'/f'running-{d}-{i:02d}.png'),((i%6)*384,(i//6)*704))
 atlas.save(A/f'running-{d}.png');shutil.copyfile(A/f'running-{d}.png',C/'inputs'/f'W-running-{d}.png');shutil.copyfile(N/'atlases'/f'running-{d}.png',C/'inputs'/f'N-running-{d}.png');shutil.copyfile(E/'atlases'/f'running-{d}.png',C/'inputs'/f'E-running-{d}.png');shutil.copyfile(S/'atlases'/f'running-{d}.png',C/'inputs'/f'S-running-{d}.png')
for name,r in F['runtimeConsumer']['files'].items():shutil.copyfile(r['path'],C/'runtime'/name)
(C/'project.godot').write_text('''config_version=5
[application]
config/name="West belt exact native family consumer"
config/use_custom_user_dir=true
config/custom_user_dir_name="sushi-refinement-west-native-01"
[rendering]
renderer/rendering_method="gl_compatibility"
environment/defaults/default_clear_color=Color(0,0,0,0)
[importer_defaults]
texture={"mipmaps/generate": true}
''')
(C/'config.json').write_text(json.dumps({'objectRoot':str(P),'nativeReferenceDirectory':str(O/'native-runs'),'offsets':V['nativeAssemblyContract']['independentPixelOffsets'],'mapping':mapping,'coverage':V['nativeAssemblyContract']['coverageByPattern'],'requiredFullPatterns':V['nativeAssemblyContract']['requiredFullPatterns']},indent=2))
metrics=[];nativeFrames=[]
for pattern in patterns:
 for d in dirs:
  for i in V['nativeAssemblyContract']['coverageByPattern'][pattern]:
   canvas=Image.new('RGBA',(896,1216));offsets=V['nativeAssemblyContract']['independentPixelOffsets'][d]
   for identity,(x,y) in zip(pattern,offsets):
    directory={'W':O,'N':N,'E':E,'S':S}[identity];di=mapping[identity][d];idx=i if identity=='W' else i%24
    src=Image.open(directory/'frames'/f'running-{di}-{idx:02d}.png')
    canvas.alpha_composite(src,(x,y))
   path=IN/f'independent-{pattern}-{d}-{i:02d}.png';canvas.save(path);native=Image.open(O/'native-runs'/f'native-{pattern}-{d}-{i:02d}.png');a=np.asarray(canvas,dtype=np.int16);b=np.asarray(native,dtype=np.int16);delta=np.abs(a-b)
   rects=[[316,496,8,360],[572,496,8,360]] if d in 'NS' else [[320,496,256,42],[320,752,256,42]]
   joins=[]
   for x,y,w,h in rects:
    e=delta[y:y+h,x:x+w];joins.append({'rect':[x,y,w,h],'maxRGBA':e.reshape(-1,4).max(0).tolist(),'alphaPixels':int(np.count_nonzero(e[:,:,3])),'rgbOver1Pixels':int(np.count_nonzero(e[:,:,:3].max(2)>1))})
   loc=np.argwhere(delta.max(2)>1);metrics.append({'pattern':pattern,'direction':d,'index':i,'path':str(path),'sha256':H(path),'fullMaxRGBA':delta.reshape(-1,4).max(0).tolist(),'fullResidualBoundsOver1':[int(loc[:,1].min()),int(loc[:,0].min()),int(loc[:,1].max()+1),int(loc[:,0].max()+1)] if len(loc) else None,'joins':joins})
  print('PACKAGED',pattern,d)
(O/'native-vs-independent-metrics.json').write_text(json.dumps(metrics,indent=2))
# Native art: original layout, all24 contacts, actual two-second12fps APNG/GIF playback. Derived only by ordinary resize/background composition.
for d in dirs:
 frames=[Image.open(O/'frames'/f'running-{d}-{i:02d}.png').convert('RGBA') for i in range(24)]
 ims=[im.resize((192,352),Image.Resampling.BOX) for im in frames];ims[0].save(PRE/f'running-{d}.png',save_all=True,append_images=ims[1:],loop=0,duration=1000/12,disposal=0,blend=0)
 sheet=Image.new('RGB',(6*192,4*376),(225,228,222));dr=ImageDraw.Draw(sheet)
 for i,im in enumerate(ims):
  x=i%6*192;y=i//6*376;bg=Image.new('RGBA',im.size,(120,125,128,255));bg.alpha_composite(im);sheet.paste(bg.convert('RGB'),(x,y+24));dr.text((x+5,y+6),f'{d} / {i:02d}',fill=(20,30,36))
 sheet.save(PRE/f'all24-{d}.png')
 for pattern in patterns:
  runs=[]
  for i in V['nativeAssemblyContract']['coverageByPattern'][pattern]:
   if i==24:continue
   im=Image.open(IN/f'independent-{pattern}-{d}-{i:02d}.png').resize((448,608),Image.Resampling.BOX);bg=Image.new('RGBA',im.size,(120,125,128,255));bg.alpha_composite(im);runs.append(bg.convert('RGB'))
  runs[0].save(PRE/f'repeated-{pattern}-{d}.png',save_all=True,append_images=runs[1:],loop=0,duration=1000/12,disposal=0,blend=0)
# Same registered scale, no bounds-fitting.
view=Image.new('RGB',(4*192,376),(225,228,222));draw=ImageDraw.Draw(view)
for j,d in enumerate(dirs):
 im=Image.open(O/f'hero-{d}.png').resize((192,352),Image.Resampling.BOX);bg=Image.new('RGBA',im.size,(120,125,128,255));bg.alpha_composite(im);view.paste(bg.convert('RGB'),(j*192,24));draw.text((j*192+8,6),d,fill=(20,30,36))
view.save(PRE/'four-view-sheet.png')
shutil.copyfile(P/'source/round-01.blend',P/'source/main.blend')
print('NATIVE_PACKAGE_COMPLETE',len(metrics))

# Self-contained actual-consumer bench fixtures for a fresh experiment rebuild.
shutil.copyfile(P/'source/bench_round01.gd',C/'bench.gd');shutil.copyfile(P/'source/bench_floor_round01.gd',C/'bench-floor.gd');shutil.copyfile(P/'../../../production/sprites/floor-cream/static-S.png',C/'inputs/game-floor-cream.png')
