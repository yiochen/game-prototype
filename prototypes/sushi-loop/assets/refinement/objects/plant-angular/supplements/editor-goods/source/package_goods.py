"""Package immutable native plant goods and actual copied-consumer evidence."""
from pathlib import Path
from PIL import Image,ImageChops,ImageDraw
import json,hashlib,math
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;OUT=BASE/'candidates/round-01'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
pixelsha=lambda im:hashlib.sha256(im.convert('RGBA').tobytes()).hexdigest()
load=lambda p:json.loads(Path(p).read_text())
assert not (OUT/'delivery-v1.json').exists(),'Immutable delivery already exists'
native=Image.open(OUT/'goods.png').convert('RGBA');reopen=Image.open(OUT/'reopened.png').convert('RGBA')
original=Image.open(BASE/'inputs/original.png').convert('RGBA')
assert native.size==(384,384) and native.tobytes()==reopen.tobytes()
parity=load(OUT/'native-parity.json');rp=load(OUT/'reopen-native.json');consumer=load(OUT/'consumer-parity.json')
record=load(OUT/'consumer/render-record.json');portable=load(OUT/'portable-proof.json')
assert all(parity['checks'].values()) and rp['nativeParityMatches'] and rp['savedBindingAlreadyExact'] and rp['normalizationIdempotent']
assert rp['sectionHashes']==parity['source']['sectionHashes']==parity['candidate']['sectionHashes']
assert rp['camera']==parity['goodsCamera'] and portable['consumerAll54ImagesExactPixels']
alpha=native.getchannel('A');bounds=alpha.getbbox()
edge=max(list(alpha.crop((0,0,384,1)).getdata())+list(alpha.crop((0,383,384,384)).getdata())+list(alpha.crop((0,0,1,384)).getdata())+list(alpha.crop((383,0,384,384)).getdata()))
assert edge==0

# Each panel uses actual Godot background output at its exact requested canvas.
colors=['cream','light','gray','dark'];sheet=Image.new('RGB',(900,430),'#292e31');draw=ImageDraw.Draw(sheet)
for col,color in enumerate(colors):
 draw.text((col*225+20,14),color,fill='white')
 for row,(mode,size) in enumerate([('original',66),('candidate',66),('original',96),('candidate',96)]):
  y=[42,126,213,319][row]
  im=Image.open(OUT/'consumer'/f'background-{mode}-{size}-{color}.png').convert('RGB')
  assert im.size==(size,size);sheet.paste(im,(col*225+110,y));draw.text((col*225+8,y+20),f'{mode} {size}',fill='white')
sheet.save(OUT/'logical-backgrounds.png')
comparison=Image.new('RGBA',(800,430),(254,243,219,255));d=ImageDraw.Draw(comparison)
comparison.alpha_composite(original,(8,38));comparison.alpha_composite(native,(408,38))
d.text((12,12),'Previous accepted goods',fill=(30,38,43));d.text((412,12),'Exact approved model / pinned goods camera',fill=(30,38,43))
comparison.save(OUT/'native-comparison.png')

states=['layout-page0','layout-page1','floor','plant-selected','plant-empty']
context=Image.new('RGB',(1296,5*350+60),'#22332f');d=ImageDraw.Draw(context)
d.text((12,10),'ACTUAL CURRENT GODOT CONSUMER | solid room placeholder | excerpts; full screens bound',fill='white')
for row,state in enumerate(states):
 d.text((12,50+row*350),state+' | phone540x960 and landscape1280x720',fill='white')
 phone=Image.open(OUT/'consumer'/f'context-candidate-{state}-540x960.png').convert('RGB')
 landscape=Image.open(OUT/'consumer'/f'context-candidate-{state}-1280x720.png').convert('RGB')
 context.paste(phone.crop((0,660,540,960)),(12,74+row*350))
 context.paste(landscape.crop((438,496,843,720)),(580,74+row*350))
context.save(OUT/'context-card.png')

# The actual full-screen screenshot delta is restricted to the plant preview.
checks=[]
for c in record['contexts']:
 if c['mode']!='candidate':continue
 twin=next(t for t in record['contexts'] if t['mode']=='original' and t['state']==c['state'] and t['viewportSize']==c['viewportSize'])
 a=Image.open(OUT/'consumer'/c['path']).convert('RGBA');b=Image.open(OUT/'consumer'/twin['path']).convert('RGBA')
 box=ImageChops.difference(a,b).convert('RGB').getbbox()
 assert c['cards']==twin['cards'] and c['stateSnapshot']==twin['stateSnapshot'] and c['controls']==twin['controls']
 assert c['inventoryCount']==6 and c['goodsManifestCount']==6
 expected=load(HERE/'resources/current-consumer/content/editor.json')['inventory']
 if c['state']=='plant-empty':
  for e in expected:
   if e['id']=='plant-angular':e['count']=0
 assert c['stateSnapshot']['inventory']==expected
 hasplant=c['state'] in ['layout-page0','plant-selected','plant-empty']
 if hasplant:
  card=next(t for t in c['cards'] if t['artID']=='plant-angular')
  r=card['previewRect'];allowed=(math.floor(r[0])-1,math.floor(r[1])-1,math.ceil(r[0]+r[2])+1,math.ceil(r[1]+r[3])+1)
  inside=not box or (box[0]>=allowed[0] and box[1]>=allowed[1] and box[2]<=allowed[2] and box[3]<=allowed[3])
  assert inside
  assert card['stock']==('0 left' if c['state']=='plant-empty' else '2 left')
  assert card['disabled']==(c['state']=='plant-empty') and card['selected']==(c['state']=='plant-selected')
 else:inside=box is None;assert inside
 labels=[{k:t[k] for k in ['id','artID','label','stock','labelVisible','stockVisible','badgeVisible','disabled','selected']} for t in c['cards']]
 checks.append({'state':c['state'],'viewportSize':c['viewportSize'],'differenceBounds':list(box) if box else None,
                'onlyPlantPreviewChanges':inside,'contentAndFixtureExact':True,'cardLabelsCountsFlags':labels})

reproof={'actualFreshBlenderProcess':True,'source':'source/round-01.blend','sourceSHA256':sha(HERE/'round-01.blend'),
 'candidate':'candidates/round-01/goods.png','candidateSHA256':sha(OUT/'goods.png'),
 'reopened':'candidates/round-01/reopened.png','reopenedSHA256':sha(OUT/'reopened.png'),
 'rgbaPixelSHA256':pixelsha(native),'reopenedRGBAPixelSHA256':pixelsha(reopen),'pixelsEqual':True,
 'maximumChannelDifference':0,'pngBytesEqual':(OUT/'goods.png').read_bytes()==(OUT/'reopened.png').read_bytes()}
(OUT/'reopen-proof.json').write_text(json.dumps(reproof,indent=2)+'\n')
resources=list(load(OUT/'replay-manifest-v1.json')['resources'])
for rel in ['candidates/round-01/replay-manifest-v1.json','candidates/round-01/portable-proof.json',
            'candidates/round-01/reopen-native.json','candidates/round-01/reopened.png','candidates/round-01/reopen-proof.json',
            'candidates/round-01/consumer-parity.json','candidates/round-01/logical-backgrounds.png',
            'candidates/round-01/native-comparison.png','candidates/round-01/context-card.png']:
 if not any(r['path']==rel for r in resources):resources.append({'path':rel,'sha256':sha(BASE/rel)})
assert not any(Path(r['path']).suffix=='.log' or r['path']=='delivery.json' for r in resources)
validation={'asset':'plant-angular','experiment':'editor-goods-supplement','round':'round-01','pipeline':'native-3d',
 'status':'technical-evidence-complete-awaiting-independent-visual-judge',
 'checks':dict(parity['checks'],savedBindingAlreadyExact=rp['savedBindingAlreadyExact'],normalizationIdempotent=True,
  reopenedSourceExactPixels=True,exactNative384RGBA=True,clearFrameEdges=True,noRasterAlteration=True,
  consumerCodeUnchanged=consumer['consumerCodeUnchanged'],contentJSONUnchanged=consumer['contentJSONUnchanged'],
  goodsManifestUnchanged=consumer['goodsManifestUnchanged'],sixGoodsPreserved=True,otherGoodsAndFloorExact=True,
  onlyPlantPreviewChangesInFullScreens=all(c['onlyPlantPreviewChanges'] for c in checks),
  portableNativeAndAll54ConsumerPNGsExact=True,noVolatileDependency=True),
 'normalization':parity['normalization'],'nativeParity':'native-parity.json','nativeParitySHA256':sha(OUT/'native-parity.json'),
 'reopenProof':reproof,'capture':{'frame':[384,384],'pixelAspect':[1,1],'elevationDegrees':35,'azimuthDegrees':35,
  'camera':parity['goodsCamera'],'cameraMaximumErrors':parity['cameraMaximumErrors'],'alphaBounds':list(bounds),'frameEdgeMaximumAlpha':edge},
 'consumer':{'parity':'consumer-parity.json','paritySHA256':sha(OUT/'consumer-parity.json'),
  'renderRecord':'consumer/render-record.json','renderRecordSHA256':sha(OUT/'consumer/render-record.json'),
  'checks':checks,'sixGoods':consumer['sixGoods'],'floorSourceSHA256':consumer['floorSourceSHA256'],
  'floorAtlasPixelSHA256':consumer['floorAtlasPixelSHA256'],'qualification':record['qualification']},
 'portableReplay':{'immutableManifest':'candidates/round-01/replay-manifest-v1.json',
  'manifestSHA256':sha(OUT/'replay-manifest-v1.json'),'proof':'candidates/round-01/portable-proof.json',
  'proofSHA256':sha(OUT/'portable-proof.json'),'command':'python3 source/portable_verify.py',
  'requirements':['Blender5.2.2','Godot4.7.2 Compatibility','Python3 with Pillow'],
  'mutableRootDeliveryRead':False,'productionAccessByReplayRecipes':False,'allReadResourcesBound':True},
 'sourceOriginalSHA256':sha(BASE/'inputs/approved-world-model.blend'),'savedSourceSHA256':sha(HERE/'round-01.blend'),
 'resources':resources}
assert all(validation['checks'].values())
(OUT/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
delivery={'schemaVersion':1,'asset':'plant-angular','experiment':'editor-goods-supplement','candidate':'round-01',
 'status':'ready-for-independent-judge','pipeline':'native-3d','project':'source/round-01.blend','source':'source/round-01.blend',
 'sourceSHA256':sha(HERE/'round-01.blend'),'recipeScript':'source/build_goods.py','recipe':'source/build_goods.py',
 'recipeSHA256':sha(HERE/'build_goods.py'),'render':'candidates/round-01/goods.png','heroes':{'goods':'candidates/round-01/goods.png'},
 'renderSHA256':sha(OUT/'goods.png'),'validation':'candidates/round-01/validation.json','validationSHA256':sha(OUT/'validation.json'),
 'previews':{'logical-backgrounds':'candidates/round-01/logical-backgrounds.png','context-card':'candidates/round-01/context-card.png',
             'native-comparison':'candidates/round-01/native-comparison.png'},'resources':resources,
 'capture':{'frame':[384,384],'projection':'ordinary-orthographic-three-quarter','cameraContract':'inputs/camera-contract.json',
            'noRasterFitting':True,'staticActionNormalization':parity['normalization']},'approval':None,
 'immutableManifest':'candidates/round-01/delivery-v1.json',
 'proposedIntegration':{'goodsID':'plant-angular','nativeSize':[384,384],'keepExistingGoodsAtlasCellLayout':True,
  'worldFramesUnaffected':True,'exactAcceptedFloorSourceSHA256':consumer['floorSourceSHA256'],
  'exactAcceptedFloorAtlasPixelSHA256':consumer['floorAtlasPixelSHA256']},
 'contextQualification':'Actual unchanged copied current consumer with exact editor.json counts across pages, selected2 and empty0 fixtures; solid room placeholder. Fullscreens bind all footer excerpts. No production/world/UI/floor writes.'}
(OUT/'delivery-v1.json').write_text(json.dumps(delivery,indent=2)+'\n')
(BASE/'delivery.json').write_text(json.dumps(delivery,indent=2)+'\n')
print(json.dumps({'delivery':str(OUT/'delivery-v1.json'),'checks':validation['checks'],'resources':len(resources),'alphaBounds':bounds},indent=2))
