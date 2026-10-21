from pathlib import Path
import hashlib,json,shutil
from PIL import Image
P=Path(__file__).resolve().parents[1];R=P.parents[7];G=R/'prototypes/sushi-loop/godot';O=P/'candidates/round-01';C=P/'source/consumer';C.mkdir(exist_ok=True);H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert (G/'scripts/editor_presentation.gd').is_file(),G
files=[]
W=P.parent.parent
for base in [W/'source',W/'candidates/round-01',W/'reviews',G/'scripts',G/'assets/ui',G/'assets/fonts']:
 for f in base.rglob('*'):
  if f.is_file() and '.godot' not in f.parts:files.append(f)
protected={str(f):H(f) for f in files};(O/'scope-before.json').write_text(json.dumps(protected,indent=2))
for rel in ['assets/ui','assets/fonts']:
 shutil.copytree(G/rel,C/rel,dirs_exist_ok=True)
for name in ['editor_presentation.gd','typography.gd','art_book.gd','ui_skin.gd']:
 (C/'scripts').mkdir(exist_ok=True);shutil.copyfile(G/'scripts'/name,C/'scripts'/name)
for rel in ['assets/catalog/manifest.json','assets/recipe-variants/manifest.json','assets/chef-variants/manifest.json','assets/feedback-variants/manifest.json']:
 (C/rel).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(G/rel,C/rel)
shutil.copyfile(G/'assets/ui/editor-goods/atlas.png',C/'baseline-atlas.png')
# Exact unchanged UI/assets copied; only E sprite is substituted in a temporary copied atlas, within existing384rect and existing6item manifest.
manifest=json.loads((C/'assets/ui/editor-goods/manifest.json').read_text());atlas=Image.open(C/'assets/ui/editor-goods/atlas.png').convert('RGBA');floor=manifest['sprites']['floor-cream'];x,y,w,h=floor['region'];floorbefore=atlas.crop((x,y,x+w,y+h)).tobytes();accepted=R/'prototypes/sushi-loop/assets/ui/editor/goods-v1/renders/floor-cream.png';a=Image.open(accepted).convert('RGBA');assert a.tobytes()==floorbefore
x,y,w,h=manifest['sprites']['belt-straight-e']['region'];candidate=Image.open(O/'goods.png').convert('RGBA');assert candidate.size==(w,h);atlas.paste(candidate,(x,y));atlas.save(C/'assets/ui/editor-goods/atlas.png');x,y,w,h=floor['region'];floorafter=atlas.crop((x,y,x+w,y+h)).tobytes();assert floorbefore==floorafter
codehashes={name:{'production':str(G/'scripts'/name),'copy':str((C/'scripts'/name).relative_to(P)),'productionSHA256':H(G/'scripts'/name),'copySHA256':H(C/'scripts'/name),'equal':H(G/'scripts'/name)==H(C/'scripts'/name)} for name in ['editor_presentation.gd','typography.gd','art_book.gd','ui_skin.gd']}
record={'method':'Disposable minimalGodotproject uses exact current EditorPresentation/UISkin/ArtBook/Typography and exact UI/font assets. Existing goods manifest and all6entries unchanged. Only E384rect of copied goods atlas contains new nativegoods capture; floor rawRGBA remains exact. No UI/layoutcode alteration.','code':codehashes,'goodsManifestSHA256':H(G/'assets/ui/editor-goods/manifest.json'),'copiedGoodsManifestSHA256':H(C/'assets/ui/editor-goods/manifest.json'),'sixGoodsPreserved':len(manifest['sprites'])==6,'spriteIDs':list(manifest['sprites']),'floor':{'acceptedRenderSHA256':H(accepted),'expectedAcceptedRenderSHA256':'6ded9330f3106d1d4941ac84e94c3e54436f098d261f5f36436d7115af239177','productionCropRGBA_SHA256':hashlib.sha256(floorbefore).hexdigest(),'copiedCandidateAtlasCropRGBA_SHA256':hashlib.sha256(floorafter).hexdigest(),'acceptedRenderRGBA_SHA256':hashlib.sha256(a.tobytes()).hexdigest(),'cropPixelEqual':floorbefore==floorafter==a.tobytes()},'protectedBefore':str((O/'scope-before.json').relative_to(P))};(O/'consumer-binding.json').write_text(json.dumps(record,indent=2))
(C/'project.godot').write_text('''config_version=5
[application]
config/name="E goods isolated current card consumer"
config/use_custom_user_dir=true
config/custom_user_dir_name="sushi-e-goods-supplement"
[rendering]
renderer/rendering_method="gl_compatibility"
environment/defaults/default_clear_color=Color(0,0,0,0)
[importer_defaults]
texture={"mipmaps/generate": true}
''')
(C/'candidate.png').write_bytes((O/'goods.png').read_bytes());(C/'original.png').write_bytes((P/'inputs/original.png').read_bytes());print('CONTEXT_READY',C)
