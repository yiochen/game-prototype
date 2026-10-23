"""Independent judge audit. Writes review evidence only; sealed files stay untouched."""
from pathlib import Path
import json, hashlib, math, tempfile, shutil, subprocess, sys
from PIL import Image

B=Path(__file__).resolve().parents[1]; C=B/'candidates/round01'; S=B/'source/round01'; R=B/'reviews'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:Image.open(p).convert('RGBA')
packet_path=C/'packet.json'; packet=json.loads(packet_path.read_text()); expected_packet='44986cda2208b148c96df31d58974dc7b9fdc5f59721bde50d619aa9e49d08ae'
assert sha(packet_path)==expected_packet
criteria=json.loads((R/'criteria.json').read_text())
assert {k:v for k,v in packet['qualityCriteria'].items()if k not in ['status','criteriaFile','criteriaFileSHA256']}=={k:v for k,v in criteria.items()if k!='status'}
assert packet['qualityCriteria']['criteriaFileSHA256']==sha(R/'criteria.json')
bindings=[]
def binding_walk(value):
    if isinstance(value,dict):
        if 'path' in value and 'sha256' in value:
            path=(C/value['path']).resolve(); assert path.is_file(),str(path); assert sha(path)==value['sha256'],str(path); bindings.append(path)
        for v in value.values():binding_walk(v)
    elif isinstance(value,list):
        for v in value:binding_walk(v)
for key in ['files','candidateRenders','previews']:binding_walk(packet[key])
d=json.loads((C/'delivery.json').read_text()); old=json.loads((B/'inputs/catalog-object.json').read_text()); main=json.loads((C/'manifest.json').read_text()); vm=json.loads((C/'runtime-variants/smile/manifest.json').read_text()); ov=json.loads((B/'inputs/runtime-variants/smile/original-manifest.json').read_text())
assert [c['id']for c in main['clips']]==['appear','idle','fade','happy-transition']
for key in old:
    if key not in ['clips','source']:assert old[key]==main[key],key
for before,after in zip(old['clips'],main['clips']):
    assert {k:v for k,v in before.items()if k!='directions'}=={k:v for k,v in after.items()if k!='directions'}
    assert set(after['directions'])==set(before['directions'])=={'S','N','E','W'}
    assert len({json.dumps(v,sort_keys=True)for v in after['directions'].values()})==1
    for direction,entry in after['directions'].items():
        assert {k:v for k,v in before['directions'][direction].items()if k!='sha256'}=={k:v for k,v in entry.items()if k!='sha256'}
assert {k:v for k,v in ov['objects']['bubble-happy'].items()if k!='clips'}=={k:v for k,v in vm['objects']['bubble-happy'].items()if k!='clips'}
for cid,before in ov['objects']['bubble-happy']['clips'].items():
    after=vm['objects']['bubble-happy']['clips'][cid]
    assert {k:v for k,v in before.items()if k!='directions'}=={k:v for k,v in after.items()if k!='directions'}
    assert set(after['directions'])=={'S'}
    assert {k:v for k,v in before['directions']['S'].items()if k!='sha256'}=={k:v for k,v in after['directions']['S'].items()if k not in ['sha256','uniqueFrames']}
assert set(vm['objects']['bubble-happy']['clips'])==set(ov['objects']['bubble-happy']['clips'])
assert len(d['rawFrames'])==192 and len(d['atlases'])==16 and len(d['runtimeVariants']['rawFrames'])==48 and len(d['runtimeVariants']['atlases'])==4
resources=set(d['resources']); allrecords=d['rawFrames']+d['atlases']+d['runtimeVariants']['rawFrames']+d['runtimeVariants']['atlases']
for record in allrecords:assert sha(B/record['path'])==record['sha256']
for rel,expected in vm['sourceFiles'].items():assert sha(B/rel)==expected
prov=json.loads((S/'provenance.json').read_text()); arts={}; original_arts={}; crops={}
for kind,rec in prov['crop'].items():
    raw=load(B/rec['raw']);box=raw.getchannel('A').point(lambda a:255 if a>8 else 0).getbbox();art=load(B/rec['canonical'])
    assert list(box)==rec['box']; assert art.size==raw.crop(box).size and art.tobytes()==raw.crop(box).tobytes()
    assert sha(B/rec['raw'])==rec['rawSHA256'];assert sha(B/rec['canonical'])==rec['canonicalSHA256']
    frozen=B/('inputs/target.png'if kind=='heart'else'inputs/runtime-variants/smile/target.png');assert sha(frozen)==sha(B/rec['raw'])
    arts[kind]=art.resize((164,round(art.height/art.width*164)),Image.Resampling.LANCZOS)
    oldart=load(S/'resources'/('original-heart-artwork.png'if kind=='heart'else'smile/original-source/bubble-happy-smile.png'));ob=oldart.getchannel('A').point(lambda a:255 if a>8 else 0).getbbox();cut=oldart.crop(ob);original_arts[kind]=cut.resize((164,round(cut.height/cut.width*164)),Image.Resampling.LANCZOS)
    crops[kind]={'alpha8Rectangle':list(box),'canonicalPixelIdentical':True,'normalizedSize':list(arts[kind].size)}
def frame(art,cid,i):
    phase=i/12*math.tau;scale=1.;opacity=1.;image=art.copy()
    if 'appear' in cid:scale=.5+.5*math.sin((i+1)/12*math.pi/2);opacity=(i+1)/12
    elif 'fade' in cid:opacity=1-i/12
    elif cid.endswith('transition'):scale=1+.12*math.sin(phase)
    if scale!=1:image=image.resize((round(image.width*scale),round(image.height*scale)),Image.Resampling.LANCZOS)
    if opacity<1:image.putalpha(image.getchannel('A').point(lambda a:round(a*opacity)))
    im=Image.new('RGBA',(384,640));im.alpha_composite(image,(round(192-image.width/2),round((248-52-3*math.sin(phase))*2-image.height/2)));return im
actual=[];clip_summary=[];original_matches=0;playback_frames=0
for kind,records,atlasrecords in [('heart',d['rawFrames'],d['atlases']),('smile',d['runtimeVariants']['rawFrames'],d['runtimeVariants']['atlases'])]:
    for cid in dict.fromkeys(r['clip']for r in records):
        seq=sorted([r for r in records if r['clip']==cid and r['facing']=='S'],key=lambda r:r['index']);assert len(seq)==12
        atlasrec=next(r for r in atlasrecords if r['clip']==cid and r['facing']=='S');atlas=load(B/atlasrec['path']);assert atlas.size==(2304,1280)
        original_path=S/'resources'/('original-heart-atlases'if kind=='heart'else'smile/original-atlases')/Path(atlasrec['path']).name;original=load(original_path)
        playback=Image.open(B/d['previews'][cid+'-S']);assert playback.n_frames==12
        pixelset=set()
        for i,rec in enumerate(seq):
            path=B/rec['path'];im=load(path);assert im.size==(384,640);assert im.tobytes()==frame(arts[kind],cid,i).tobytes()
            x,y,w,h=atlasrec['rects'][i];assert [x,y,w,h]==[i%6*384,i//6*640,384,640];assert atlas.crop((x,y,x+w,y+h)).tobytes()==im.tobytes()
            assert original.crop((x,y,x+w,y+h)).tobytes()==frame(original_arts[kind],cid,i).tobytes();original_matches+=1
            alpha=im.getchannel('A');assert alpha.getextrema()[0]==0;assert alpha.getbbox() is not None
            for box in [(0,0,384,1),(0,639,384,640),(0,0,1,640),(383,0,384,640)]:assert alpha.crop(box).getextrema()[1]==0
            playback.seek(i);assert playback.convert('RGBA').tobytes()==im.tobytes();assert abs(playback.info['duration']-1000/12)<1e-8;playback_frames+=1
            pixelset.add(hashlib.sha256(im.tobytes()).hexdigest());actual.append(path)
        assert len(pixelset)>=6
        clip_summary.append({'kind':kind,'clip':cid,'frames':12,'uniquePixelFrames':len(pixelset),'manifestLoop':cid in ['idle','happy-smile-idle'],'allFramesMatchOriginalMath':True,'atlasRectsMatch':True,'playbackRGBAAndExact12fpsMatch':True,'transparentBorders':True})
runtime=Image.open(B/d['previews']['happy-smile-runtime-playback']);assert runtime.n_frames==27;runtime_ms=0
for i in range(27):runtime.seek(i);runtime_ms+=runtime.info['duration']
assert abs(runtime_ms-2200)<1e-8
paths=resources|{d[k]for k in ['project','recipeScript','recipe','validation','manifest']}|{d['runtimeVariants']['manifest']}|set(d['previews'].values())|{r['path']for r in allrecords}
source_closure=sorted(x for x in paths if x.startswith('source/round01/'));assert all((B/x).is_file()for x in source_closure)
before={x:sha(B/x)for x in paths};replayed={}
with tempfile.TemporaryDirectory(prefix='isolated-round01-',dir=R)as td:
    clone=Path(td)/'object'
    for rel in source_closure:
        dest=clone/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(B/rel,dest)
    assert not(clone/'inputs').exists()and not(clone/'reviews').exists()
    logs=[]
    for script in ['prepare_sources.py','publish.py']:
        proc=subprocess.run([sys.executable,str(clone/'source/round01'/script)],cwd=td,capture_output=True,text=True,check=True);logs.append({'script':script,'exitCode':proc.returncode})
    for rel,expected in before.items():
        if rel.startswith('candidates/')or rel in [d['project'],d['runtimeVariants']['project'],d['recipe']]:
            assert sha(clone/rel)==expected,('relocated-replay',rel);replayed[rel]=expected
    assert sha(clone/'delivery.json')==sha(C/'delivery.json')
assert before=={x:sha(B/x)for x in paths};assert sha(packet_path)==expected_packet
report={'schemaVersion':1,'asset':'bubble-happy','candidatePacketSHA256':expected_packet,'criteriaSHA256':sha(R/'criteria.json'),'packetBindingReferencesVerified':len(bindings),'distinctBoundFiles':len(set(bindings)),'mainSlots':192,'mainAtlasEntries':16,'mainActualAtlasFiles':4,'runtimeSmileFrames':48,'runtimeActualAtlasFiles':4,'allActualFrames':96,'crops':crops,'clips':clip_summary,'originalAtlasFramesReproducedIndependently':original_matches,'submittedAPNGFramesMatchedToNativeRGBA':playback_frames,'runtimePlaybackFrames':27,'runtimePlaybackDurationMs':round(runtime_ms),'closedReplay':{'sourceClosureFiles':len(source_closure),'replayedFilesByteEqual':len(replayed),'replayedDeliveryByteEqual':True,'copiedOnlyDeclaredSourceClosure':True,'noInputsReviewsProductionDependencies':True,'commands':logs,'outputHashMapSHA256':hashlib.sha256(json.dumps(replayed,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'temporaryReplayRemoved':True},'sealedFilesUnchanged':True}
(R/'round01-technical-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
