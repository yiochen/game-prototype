"""Exact whole-canvas native4x -> published2x, original atlases and review media."""
from pathlib import Path
import json,hashlib,copy
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;O=H.parent;C=O/'candidates/round-01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
    assert not p.exists(),p
    p.write_text(json.dumps(v,indent=2)+'\n')
def rel(p):return str(p.relative_to(O))
catalog=json.loads((H/'round-01-inputs/catalog-object.json').read_text());clip=catalog['clips'][0]
native=json.loads((C/'native-validation.json').read_text());nc=json.loads((C/'native-camera.json').read_text())
assert len(native['views'])==48
records=[];atlases=[];frames={};pixelrows=[]
for direction in 'NESW':
    frames[direction]=[];entry=clip['directions'][direction]
    atlas=Image.new('RGBA',tuple(entry['atlasSize']),(0,0,0,0))
    for i in range(12):
        src=C/'native/enter'/direction/f'{i:03d}.png';dst=C/'frames/enter'/direction/f'{i:03d}.png';dst.parent.mkdir(parents=True,exist_ok=True)
        assert not dst.exists()
        with Image.open(src) as im:
            assert im.mode=='RGBA' and im.size==(768,1536)
            pub=im.resize((384,768),Image.Resampling.LANCZOS)
            bbox=im.getchannel('A').getbbox()
            transparent_border=all(im.getchannel('A').crop(box).getextrema()[1]==0 for box in [(0,0,768,1),(0,1535,768,1536),(0,0,1,1536),(767,0,768,1536)])
            assert transparent_border
            pub.save(dst)
        x,y,w,h=entry['rects'][i];assert (w,h)==pub.size
        atlas.paste(pub,(x,y));frames[direction].append(pub)
        records.append({'clip':'enter','direction':direction,'index':i,'frame':i,'nativeFrame':i+1,'path':rel(dst),'dimensions':list(pub.size),'sha256':sha(dst)})
        pixelrows.append({'direction':direction,'index':i,'nativePath':rel(src),'publishedPath':rel(dst),'nativeSHA256':sha(src),'publishedSHA256':sha(dst),'nativeAlphaBounds':list(bbox),'nativeFullBorderTransparent':transparent_border,'publishedAlphaBounds':list(pub.getchannel('A').getbbox()),'wholeCanvasReduction':'Pillow LANCZOS 768x1536 ->384x768; no crop, fit, shifts, pixel repair or palette changes'})
    ap=C/'atlases'/f'{direction}.png';assert not ap.exists();atlas.save(ap)
    for i,frame in enumerate(frames[direction]):
        x,y,w,h=entry['rects'][i];assert atlas.crop((x,y,x+w,y+h)).tobytes()==frame.tobytes()
    assert len({hashlib.sha256(im.tobytes()).hexdigest() for im in frames[direction]})>=6
    atlases.append({'clip':'enter','direction':direction,'path':rel(ap),'columns':6,'rows':2,'frames':12,'fps':12,'loop':False,'size':[2304,1536],'atlasSize':[2304,1536],'dimensions':[2304,1536],'rects':entry['rects'],'frameOrder':list(range(12)),'sha256':sha(ap)})

# Every cell contains a complete published full frame at exact published pixels.
sheet=Image.new('RGB',(384*12,788*4),'#777777');draw=ImageDraw.Draw(sheet);cells=[]
for row,direction in enumerate('NESW'):
    for i,frame in enumerate(frames[direction]):
        x=i*384;y=row*788;sheet.paste(frame,(x,y+20),frame);draw.text((x+8,y+3),f'{direction} enter {i:02d}',fill='white')
        cells.append({'path':records[row*12+i]['path'],'direction':direction,'index':i,'sheetRect':[x,y+20,384,768],'sourceFullFrame':[384,768],'sampling':'none; exact published pixel size, alpha composited to gray'})
sheet.save(C/'previews/all48-published-fullframe.png')
write(C/'previews/all48-path-cell-map.json',{'sheet':rel(C/'previews/all48-published-fullframe.png'),'sheetSize':list(sheet.size),'cells':cells})
hero=Image.new('RGB',(1536,788),'#777777');draw=ImageDraw.Draw(hero)
for k,d in enumerate('NESW'):
    hero.paste(frames[d][5],(k*384,20),frames[d][5]);draw.text((k*384+8,3),f'{d} native enter phase 5',fill='white')
hero.save(C/'previews/four-view-sheet.png')
# Native phase APNGs are useful motion aliases; actual compositor playback is separate browser evidence.
for d in 'NESW':
    frames[d][0].save(C/'previews'/f'enter-{d}.png',save_all=True,append_images=frames[d][1:],duration=1000/12,loop=1,disposal=0,blend=0)
combined=[]
for i in range(12):
    im=Image.new('RGBA',(768,384),(0,0,0,0))
    for k,d in enumerate('NESW'):im.paste(frames[d][i].resize((192,384),Image.Resampling.LANCZOS),(k*192,0))
    combined.append(im)
combined[0].save(C/'previews/motion.png',save_all=True,append_images=combined[1:],duration=1000/12,loop=1,disposal=0,blend=0)
# Diagnostic crops are explicitly preview-only, mapped to full native parent pixels.
details=Image.new('RGB',(768,800),'#777777');draw=ImageDraw.Draw(details);detailmap=[]
for k,(d,i,box,label) in enumerate([('S',5,(150,920,620,1250),'S5 support/rim seats'),('N',5,(150,920,620,1250),'N5 support/rim seats'),('E',5,(235,690,540,1080),'E5 physical depth'),('W',11,(235,690,540,1080),'W11 terminal depth')]):
    parent=C/'native/enter'/d/f'{i:03d}.png';src=Image.open(parent).convert('RGBA');crop=src.crop(box)
    # Aspect-preserving diagnostic contain into384x380, not a published sprite operation.
    factor=min(374/crop.width,370/crop.height);size=(round(crop.width*factor),round(crop.height*factor));im=crop.resize(size,Image.Resampling.LANCZOS)
    x=(k%2)*384+(384-size[0])//2;y=(k//2)*400+20
    details.paste(im,(x,y),im);draw.text(((k%2)*384+5,(k//2)*400+4),label,fill='white')
    detailmap.append({'parentPath':rel(parent),'nativeCropBox':list(box),'previewRect':[x,y,*size],'sampling':'diagnostic aspect-preserving LANCZOS only; full native parent retained'})
details.save(C/'previews/connection-depth-details.png');write(C/'previews/connection-depth-path-map.json',{'sheet':rel(C/'previews/connection-depth-details.png'),'crops':detailmap})

pc=copy.deepcopy(nc);pc.update(captureScale=2,publishedFrame=[384,768],nativeCaptureScale=4,nativeFrame=[768,1536],nativeRecord='candidates/round-01/native-camera.json',publication='uniform full canvas LANCZOS2x reduction, no fit/shift/crop/recolor/alpha repair')
pc['calibration']={key:[x/2 for x in value] for key,value in nc['calibration'].items()}
write(C/'published-camera.json',pc)
actions=json.loads((C/'native-actions.json').read_text())
asset={'id':'portal-entry','projection':catalog['projection'],'frame':[192,384],'anchor':[96,288],'scale':2,'nativeCaptureScale':4,'nativeFrame':[768,1536],'clips':{'enter':{'frames':12,'fps':12,'loop':False}},'footprint':[1,1],'height':1.48,'sockets':{'entry':[0,0,.74]},'directions':list('NESW'),'artStyle':{'revision':'warm-soft-native-portal-entry-round-01','lighting':'One centered warm overhead and four equal broad cardinal fills; no ground receiver','material':'Native cyan enamel, blue cut stone/cobalt, restrained brass','contrastSpace':'Standard native view transform, no compositor contrast','viewTransform':'Standard'},'nativeValidation':'candidates/round-01/native-validation.json','sourceSHA256':native['sourceSHA256']}
write(C/'assetRecord.json',asset)
rig={'assetId':'portal-entry','fps':12,'source':'build-round-01.py','static':False,'clips':{'enter':{'frames':12,'fps':12,'loop':False,'static':False,'firstFrame':1,'lastUniqueFrame':12,'closingKeyFrame':None,'terminalPolicy':'consumer holds frame11','actions':[{'ownerType':'Object','ownerName':a['owner'],'action':a['action'],'keyframeCount':sum(len(c['keys']) for c in a['channels'])} for a in actions['actions']]}},'armatures':[],'footprint':[1,1],'projection':catalog['projection'],'groundRootObject':'portal_rim__root.003','sockets':{'entry':[0,0,.74]},'actionCount':len(actions['actions']),'sourceProject':'source/round-01.blend','sourceSHA256':native['sourceSHA256'],'nativeActionEvidence':'candidates/round-01/native-actions.json','status':'native-saved-assigned-actions-pending-independent-visual-review'}
write(C/'rig.json',rig)
write(C/'publication-validation.json',{'asset':'portal-entry','nativeFrame':[768,1536],'nativeScale':4,'publishedFrame':[384,768],'publishedScale':2,'wholeCanvasSampling':'Pillow LANCZOS','pillowVersion':__import__('PIL').__version__,'rawFrames':records,'atlases':atlases,'pixelRecords':pixelrows,'decodedUniqueFrames':{d:len({hashlib.sha256(im.tobytes()).hexdigest() for im in frames[d]}) for d in 'NESW'},'allAtlasCellsExactlyMatchPublishedFrames':True,'nativePixelsUnchanged':True,'publicationDoesNotCertifyAppearance':True})
print('PORTAL_PUBLICATION_COMPLETE',len(records),len(atlases))
