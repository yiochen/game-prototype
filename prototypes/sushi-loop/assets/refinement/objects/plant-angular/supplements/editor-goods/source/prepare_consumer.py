"""Reconstruct copied-current Godot consumer from bound snapshot only."""
from pathlib import Path
import json,hashlib,shutil
from PIL import Image
HERE=Path(__file__).resolve().parent;BASE=HERE.parent
SNAP=HERE/'resources/current-consumer';CON=HERE/'consumer';OUT=BASE/'candidates/round-01';CON.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
pixelsha=lambda im:hashlib.sha256(im.convert('RGBA').tobytes()).hexdigest()
files=json.loads((SNAP/'snapshot-manifest.json').read_text())
for rel,record in files.items():
 src=SNAP/rel;dest=CON/rel;dest.parent.mkdir(parents=True,exist_ok=True)
 assert sha(src)==record['sha256'];shutil.copyfile(src,dest);assert sha(dest)==record['sha256']
shutil.copyfile(HERE/'consumer-bench.gd',CON/'bench.gd')
(CON/'project.godot').write_text('''config_version=5
[application]
config/name="Plant native goods isolated current consumer"
config/use_custom_user_dir=true
config/custom_user_dir_name="sushi-plant-goods-supplement"
[rendering]
renderer/rendering_method="gl_compatibility"
environment/defaults/default_clear_color=Color(0,0,0,0)
[importer_defaults]
texture={"mipmaps/generate": true}
''')
shutil.copyfile(BASE/'inputs/original.png',CON/'original.png');shutil.copyfile(OUT/'goods.png',CON/'candidate.png')
manifest=json.loads((CON/'assets/ui/editor-goods/manifest.json').read_text())
assert list(manifest['sprites'])==['belt-straight-e','stool-wood','plant-angular','crate-wood','barrel-wood','floor-cream']
original=Image.open(CON/'baseline-atlas.png').convert('RGBA');current=original.copy()
native=Image.open(CON/'candidate.png').convert('RGBA');x,y,w,h=manifest['sprites']['plant-angular']['region']
assert native.size==(w,h)==(384,384);current.paste(native,(x,y));current.save(CON/'assets/ui/editor-goods/atlas.png')
rect=lambda r:(r[0],r[1],r[0]+r[2],r[1]+r[3])
checks={}
for identity,v in manifest['sprites'].items():
 a=original.crop(rect(v['region']));b=current.crop(rect(v['region']))
 checks[identity]={'unchangedPixels':a.tobytes()==b.tobytes(),'baselinePixelSHA256':pixelsha(a),'candidatePixelSHA256':pixelsha(b)}
assert all(v['unchangedPixels'] for k,v in checks.items() if k!='plant-angular')
assert current.crop((x,y,x+w,y+h)).tobytes()==native.tobytes()
floor=current.crop(rect(manifest['sprites']['floor-cream']['region']))
accepted=Image.open(CON/'floor-cream.png').convert('RGBA')
assert floor.tobytes()==accepted.tobytes()
assert sha(CON/'floor-cream.png')=='6ded9330f3106d1d4941ac84e94c3e54436f098d261f5f36436d7115af239177'
masked=current.copy();masked.paste(original.crop((x,y,x+w,y+h)),(x,y));assert masked.tobytes()==original.tobytes()
report={'copiedCurrentFiles':files,'sixGoods':list(manifest['sprites']),'candidateOnlyRect':[x,y,w,h],
 'onlyCandidateRectChanged':True,'nativeToAtlasPixelsExact':True,'cellSize384Preserved':True,
 'floorSourceSHA256':sha(CON/'floor-cream.png'),'floorAtlasPixelSHA256':pixelsha(floor),
 'atlasChecks':checks,'baselineAtlasSHA256':sha(CON/'baseline-atlas.png'),
 'copiedCandidateAtlasSHA256':sha(CON/'assets/ui/editor-goods/atlas.png'),
 'consumerCodeUnchanged':all(sha(CON/'scripts'/n)==files['scripts/'+n]['sha256'] for n in ['editor_presentation.gd','ui_skin.gd','typography.gd','art_book.gd']),
 'contentJSONUnchanged':sha(CON/'content/editor.json')==files['content/editor.json']['sha256'],
 'goodsManifestUnchanged':sha(CON/'assets/ui/editor-goods/manifest.json')==files['assets/ui/editor-goods/manifest.json']['sha256'],
 'qualification':'Isolated actual current card consumer. Solid room placeholder; no world/room rendering claim. Only plant region differs in the copied atlas.'}
(OUT/'consumer-parity.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'consumer':str(CON),'filesPinned':len(files),'nativeAtlasPixelsExact':True,'otherGoodsAndFloorExact':True}))
