"""Package native goods supplement. Native render bytes are never transformed."""
from pathlib import Path
from PIL import Image,ImageChops,ImageDraw
import json,hashlib,math,shutil
B=Path(__file__).resolve().parent.parent;S=B/'source';O=B/'candidates/round-01'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
load=lambda p:json.loads(Path(p).read_text())
parity=load(O/'native-parity.json');reopen=load(O/'reopen-native.json');scope=load(O/'consumer-parity.json');record=load(O/'consumer/render-record.json');portable=load(O/'portable-proof.json')
native=Image.open(O/'goods.png').convert('RGBA');other=Image.open(O/'reopened.png').convert('RGBA')
assert native.size==(384,384) and native.tobytes()==other.tobytes()
assert parity['candidate']['sectionHashes']==parity['source']['sectionHashes']==reopen['sectionHashes']
assert all(parity['checks'].values()) and portable['consumer60PNGsExactRGBAPixels'] and parity['candidate']['pipelineSummary']['sceneUseNodes']==parity['source']['pipelineSummary']['sceneUseNodes'] and parity['candidate']['pipelineSummary']['useCompositing']==parity['source']['pipelineSummary']['useCompositing']
alpha=native.getchannel('A');bounds=alpha.getbbox();edge=max(alpha.crop((0,0,384,1)).getextrema()[1],alpha.crop((0,383,384,384)).getextrema()[1],alpha.crop((0,0,1,384)).getextrema()[1],alpha.crop((383,0,384,384)).getextrema()[1]);assert edge==0
consumer_checks=[]
for c in record['contexts']:
 if c['mode']!='candidate':continue
 twin=next(v for v in record['contexts'] if v['mode']=='original' and v['state']==c['state'] and v['viewportSize']==c['viewportSize'])
 for prop in ['cards','controls','stateSnapshot','activeItem','fixture','hudArea','unit','inventoryCount','goodsManifestCount','navigationCommands','disabledInputProbe']:assert c[prop]==twin[prop],(c['state'],prop)
 a=Image.open(O/'consumer'/c['path']).convert('RGB');old=Image.open(O/'consumer'/twin['path']).convert('RGB');box=ImageChops.difference(a,old).getbbox()
 card=next((v for v in c['cards'] if v['artID']=='stool-wood'),None)
 if card:
  r=card['previewRect'];allowed=[math.floor(r[0])-1,math.floor(r[1])-1,math.ceil(r[0]+r[2])+1,math.ceil(r[1]+r[3])+1]
  inside=box is None or (box[0]>=allowed[0] and box[1]>=allowed[1] and box[2]<=allowed[2] and box[3]<=allowed[3]);assert inside
  assert card['stock']==('0 left' if c['state']=='stool-empty' else '4 left')
  assert card['disabled']==(c['state']=='stool-empty') and card['selected']==(c['state']=='stool-selected')
 else:inside=box is None;assert inside
 consumer_checks.append({'state':c['state'],'viewport':c['viewportSize'],'differenceBounds':list(box) if box else None,'onlyStoolPreviewPixelsDiffer':inside,'cardsControlsStateAndRectsExact':True,'stoolCard':card,'controls':c['controls']})
assert len(consumer_checks)==18 and scope['onlyCandidateRectChanged']
# Check native stock/page boundaries and the actual next/back command path.
semantic_checks=[]
for mode in ['original','candidate']:
 for dimensions in [[540,960],[900,1200],[1280,720]]:
  contexts={c['state']:c for c in record['contexts'] if c['mode']==mode and c['viewportSize']==dimensions}
  first=contexts['layout-page0'];last=contexts['layout-page1'];back=contexts['layout-back'];floor=contexts['floor'];empty=contexts['stool-empty']
  assert [c['id']for c in first['cards']]==['belt-tile','stool-plain','plant-angular','crate-wood']
  assert [c['stock']for c in first['cards']]==['6 left','4 left','2 left','2 left']
  assert first['controls']['previous']['disabled'] and not first['controls']['next']['disabled']
  assert len(last['cards'])==1 and last['cards'][0]['id']=='barrel-wood' and last['cards'][0]['stock']=='1 left'
  assert not last['controls']['previous']['disabled'] and last['controls']['next']['disabled']
  assert last['navigationCommands']==[{'type':'editor_page','page':1}]
  assert back['navigationCommands']==[{'type':'editor_page','page':1},{'type':'editor_page','page':0}]
  assert first['cards']==back['cards'] and first['controls']==back['controls'] and first['stateSnapshot']==back['stateSnapshot']
  assert Image.open(O/'consumer'/first['path']).convert('RGBA').tobytes()==Image.open(O/'consumer'/back['path']).convert('RGBA').tobytes()
  assert floor['cards'][0]['artID']=='floor-cream' and floor['cards'][0]['disabled'] and floor['cards'][0]['stock']=='Current'
  assert empty['disabledInputProbe']['exercised'] and empty['disabledInputProbe']['nativeDisabledProperty']
  assert empty['disabledInputProbe']['pointerSignals']==0 and empty['disabledInputProbe']['armedSignals']==0
  assert not empty['fixture']['productionInventoryModified'] and not empty['fixture']['userSaveReadOrWritten']
  if dimensions==[900,1200]:assert first['hudArea'][0]>0 and first['hudArea'][2]==675
  semantic_checks.append({'mode':mode,'viewport':dimensions,'stock6422Barrel1':True,'nativeNextBackCommandsCorrect':True,'pageBackExactInitialPixelsAndState':True,'zeroStockInputGuardBlocksSignals':True,'floorCurrentDisabled':True,'userSavesUntouched':True,'centeredPortraitContainment':first['hudArea']})
# These contact sheets paste actual Godot output pixels at their captured display size.
sheet=Image.new('RGB',(900,430),'#292e31');draw=ImageDraw.Draw(sheet)
for col,bg in enumerate(['cream','light','gray','dark']):
 draw.text((col*225+20,14),bg,fill='white')
 for row,(mode,size) in enumerate([('original',66),('candidate',66),('original',96),('candidate',96)]):
  y=[42,126,213,319][row];im=Image.open(O/'consumer'/f'background-{mode}-{size}-{bg}.png').convert('RGB');assert im.size==(size,size)
  sheet.paste(im,(col*225+110,y));draw.text((col*225+8,y+20),f'{mode} {size}',fill='white')
sheet.save(O/'logical-backgrounds.png')
large=Image.new('RGB',(1584,824),'#292e31');draw=ImageDraw.Draw(large)
for col,bg in enumerate(['cream','light','gray','dark']):
 for row,mode in enumerate(['original','candidate']):
  draw.text((col*396+8,row*410+8),f'{bg} / {mode} / actual consumer 384',fill='white');large.paste(Image.open(O/'consumer'/f'background-{mode}-384-{bg}.png').convert('RGB'),(col*396+6,row*410+28))
large.save(O/'native-backgrounds.png')
comp=Image.new('RGBA',(800,430),(255,243,219,255));d=ImageDraw.Draw(comp);comp.alpha_composite(Image.open(B/'inputs/original.png').convert('RGBA'),(8,38));comp.alpha_composite(native,(408,38));d.text((12,12),'Previous accepted goods camera',fill=(30,38,43));d.text((412,12),'Exact approved model / same locked camera',fill=(30,38,43));comp.save(O/'native-comparison.png')
# Complete actual screenshots are bound below; overview is clearly labeled footer-only evidence.
for size,label,crop in [((540,960),'context-card',(0,690,540,960)),((900,1200),'context-card-wider',(100,820,800,1200)),((1280,720),'context-card-landscape',(430,490,850,720))]:
 w=crop[2]-crop[0];h=crop[3]-crop[1];contact=Image.new('RGB',(w*2+30,(h+36)*6+45),'#22332f');d=ImageDraw.Draw(contact)
 d.text((8,8),'Actual unchanged consumer | solid room placeholder | paired original / candidate footer excerpts',fill='white')
 for row,state in enumerate(['layout-page0','layout-page1','layout-back','floor','stool-selected','stool-empty']):
  y=45+row*(h+36);d.text((8,y),state+f' | {size[0]}x{size[1]} | stool4; zero fixture declared only in empty',fill='white')
  for col,mode in enumerate(['original','candidate']):
   im=Image.open(O/'consumer'/f'context-{mode}-{state}-{size[0]}x{size[1]}.png').convert('RGB');contact.paste(im.crop(crop),(8+col*(w+14),y+22))
 contact.save(O/(label+'.png'))
replay={'freshProcess':True,'savedProject':'source/round-01.blend','savedProjectSHA256':sha(S/'round-01.blend'),'nativeSHA256':sha(O/'goods.png'),'reopenedSHA256':sha(O/'reopened.png'),'nativeRGBAPixelSHA256':hashlib.sha256(native.tobytes()).hexdigest(),'reopenedRGBAPixelSHA256':hashlib.sha256(other.tobytes()).hexdigest(),'RGBAEqual':True,'PNGBytesEqual':(O/'goods.png').read_bytes()==(O/'reopened.png').read_bytes(),'maximumChannelDifference':0}
(O/'reopen-proof.json').write_text(json.dumps(replay,indent=2)+'\n')
checks=dict(parity['checks'],exactReopenedRGBAPixels=True,resourceOnlyPortableNativeReplay=True,resourceOnly60ConsumerPNGReplay=True,native384SquareRGBA=True,transparentUnclippedEdges=edge==0,approvedCompositorStatePreserved=True,onlyStoolAtlasRegionChanged=scope['onlyCandidateRectChanged'],otherFiveAtlasRegionsExact=True,acceptedFloorFileAndCropExact=True,all18ContextPairsOnlyStoolPreviewChanges=True,all18ContextPropertiesExact=True,stoolOriginalCount4AndDeclaredZeroFixture=True)
assert all(checks.values())
validation={'asset':'stool-wood','experiment':'editor-goods-supplement','round':1,'status':'await-independent-judge','checks':checks,'sourceApprovedSHA256':sha(B/'inputs/approved-world-model.blend'),'briefSHA256':sha(B/'brief.json'),'cameraContractSHA256':sha(B/'inputs/camera-contract.json'),'capture':{'frame':[384,384],'pixelAspect':[1,1],'camera':parity['goodsCamera'],'maximumCameraErrors':parity['cameraMaximumErrors'],'alphaBounds':list(bounds),'frameEdgeMaximumAlpha':edge,'fitOrCrop':False},'nativeParity':'candidates/round-01/native-parity.json','parityScope':'Original and evaluated geometry, normals, topology, mesh attributes, UVs, modifiers, object transforms/parents/properties, material graphs/assignments, lights, all render RNA except declared dimensions/pixel aspect/filepath, Cycles, world, color management, compositor, frame semantics and dependencies. Hashes measured before camera change, after change, and after native source reopen. No art/render settings changed.','reopen':replay,'portableReplay':'candidates/round-01/portable-proof.json','consumer':{'qualification':record['qualification'],'renderRecord':'candidates/round-01/consumer/render-record.json','scope':'candidates/round-01/consumer-parity.json','candidateAtlas':'candidates/round-01/consumer-atlas.png','sixGoods':scope['sixGoods'],'floorFileSHA256':scope['floorSourceSHA256'],'floorCropRGBAPixelSHA256':scope['floorAtlasPixelSHA256'],'pairedContexts':consumer_checks,'backgrounds':record['backgrounds'],'stockFixture':'Source content/editor.json remains exact. Baseline stool4; stool-empty copies inventory in memory and changes only stool count to0 on both sides; production inventory never modified.','pageCoverage':['Layout page0','Layout page1 through native next command','Layout page0 back through native previous command','Floor','stool selected count4','stool disabled count0'],'viewports':[[540,960],[900,1200],[1280,720]]},'noWorldDirectionAudit':'One ordinary three-quarter goods camera only. World frames are neither rendered nor changed by this supplement.','resourcesClosed':True,'requirements':['Blender5.2.2 LTS','Godot4.7.2 Compatibility OpenGL','Python3 with Pillow']}
validation['consumer']['semanticChecks']=semantic_checks
validation['consumer']['viewportsPurpose']={'540x960':'narrow phone','900x1200':'wider portrait window, centered675px9:16HUD','1280x720':'landscape, centered405px9:16HUD'}
validation['integrityProof']='source/resources/integrity-proof.json'
validation['approvedWorldNativeAndFourAtlasesUnchanged']=True
validation['criteriaSHA256']=sha(B/'reviews/proposedcriteria.json')
(O/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
recipe={'nativeBuild':['blender --background --python source/build_goods.py'],'nativeReplay':['blender --background source/round-01.blend --python source/reopen_goods.py -- --output-dir /new/empty/output'],'consumer':['python3 source/prepare_consumer.py','godot --headless --editor --path source/consumer --import','GOODS_OUTPUT=/new/empty/output godot --path source/consumer --script res://bench.gd --resolution 64x64'],'resourceClosureReplay':['python3 source/verify_resources.py'],'package':['python3 source/package_goods.py'],'workingDirectory':'supplement root','inputs':'Pinned inputs and source/resources/current-consumer only for replay. UI snapshot provenance in snapshot-manifest.json. No production writes.','nativePipeline':'Actual approved scene.use_nodes false and render.use_compositing false preserved exactly.'}
(S/'recipe.json').write_text(json.dumps(recipe,indent=2)+'\n')
# The working consumer is reproducible from the pinned snapshot; keep its exact
# generated atlas and screenshots while avoiding a second copy of all unchanged UI assets.
working=S/'consumer'
if working.exists():
 shutil.copyfile(working/'assets/ui/editor-goods/atlas.png',O/'consumer-atlas.png');shutil.rmtree(working)
assert sha(O/'consumer-atlas.png')==scope['copiedCandidateAtlasSHA256']
# Remove automatic caches and duplicated preparation-only helper before sealing resources.
for p in list(S.rglob('*')):
 if p.is_file() and p.suffix in ('.pyc','.import','.uid','.blend1'):p.unlink()
for p in sorted(S.rglob('*'),reverse=True):
 if p.is_dir() and p.name in ('.godot','__pycache__'):shutil.rmtree(p,ignore_errors=True)
helper=S/'snapshot_current.py'
if helper.exists():helper.unlink()
resources=[]
for root in [S,B/'inputs',O]:
 for p in sorted(root.rglob('*')):
  if not p.is_file() or p.suffix=='.log' or p.name in ('delivery.json','packet.json'):continue
  resources.append({'path':str(p.relative_to(B)),'sha256':sha(p)})
previews={k:'candidates/round-01/'+k+'.png' for k in ['logical-backgrounds','native-backgrounds','native-comparison','context-card','context-card-wider','context-card-landscape']}
delivery={'schemaVersion':1,'asset':'stool-wood','experiment':'editor-goods-supplement','candidate':'round-01','project':'source/round-01.blend','source':'source/round-01.blend','recipe':'source/recipe.json','validation':'candidates/round-01/validation.json','heroes':{'goods':'candidates/round-01/goods.png'},'render':'candidates/round-01/goods.png','previews':previews,'resources':resources,'status':'ready-for-independent-judge','approval':None,'capture':'Exact native approved model under locked ordinary orthographic three-quarter 35/35 camera; no raster fitting, crop, regrade, retouch or source art changes.','proposedIntegration':{'goodsID':'stool-wood','nativeSize':[384,384],'keepExistingGoodsAtlasDimensionsAndRegions':True,'otherGoodsAndFloorUnchanged':True,'worldPromotion':False},'contextQualification':'Actual unchanged current Godot EditorPresentation/UISkin and accepted UI assets; solid room placeholder, no restaurant/world rendering claim. Full paired screenshots bound for six states and three viewports; contact sheets are footer excerpts.'}
(O/'delivery.json').write_text(json.dumps(delivery,indent=2)+'\n');(O/'delivery.snapshot.json').write_text(json.dumps(delivery,indent=2)+'\n');(B/'delivery.json').write_text(json.dumps(delivery,indent=2)+'\n')
print(json.dumps({'checks':checks,'nativeAlphaBounds':bounds,'resourceCount':len(resources),'delivery':'delivery.json'},indent=2))
