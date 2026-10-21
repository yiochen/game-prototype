from pathlib import Path
from PIL import Image
import hashlib,json,math,importlib.util,sys,tempfile,shutil,subprocess
sys.dont_write_bytecode=True
E=Path(__file__).resolve().parent.parent;C=E/'candidates/round01';S=E/'source/round01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pix(p):return Image.open(p).convert('RGBA')
d=json.loads((E/'delivery.json').read_text());packet=json.loads((C/'packet.json').read_text());report={'packetSHA256':sha(C/'packet.json'),'sourceOnlyReplay':{},'coverage':{},'alphaAudit':{},'originalMath':{},'runtimeScripts':{}}
assert report['packetSHA256']=='7591ed424691f2f27a764e1d4c2d056621d998bb784c438f2549c2287e5ab316'
for name,r in packet['files'].items():assert sha((C/r['path']).resolve())==r['sha256'],name
report['packetBoundFilesVerified']=len(packet['files'])
# Verify the crop independently, without accepting publisher's own claims.
raw=pix(E/'inputs/target.png');bb=raw.getchannel('A').point(lambda a:255 if a>8 else 0).getbbox();canonical=pix(S/'bubble-panic.png');assert canonical.tobytes()==raw.crop(bb).tobytes();assert canonical.size==(645,599)
a=raw.getchannel('A');outside=a.copy();outside.paste(0,bb);hist=outside.histogram();report['alphaAudit']={'rawTargetSHA256':sha(E/'inputs/target.png'),'boundsThreshold':8,'bounds':bb,'canonicalIsExactRawRGBARectangle':True,'omittedOutsideNonzero':sum(hist[1:]),'omittedOutsideMaxAlpha':outside.getextrema()[1],'omittedOutsideTotalAlpha':sum(i*n for i,n in enumerate(hist))}
assert report['alphaAudit']['omittedOutsideNonzero']==346 and report['alphaAudit']['omittedOutsideMaxAlpha']==6
norm=canonical.resize((164,round(canonical.height/canonical.width*164)),Image.Resampling.LANCZOS)
spec=importlib.util.spec_from_file_location('originalJudgeMath',E/'inputs/original-2d-pipeline/publish_2d.py');orig=importlib.util.module_from_spec(spec);spec.loader.exec_module(orig)
orig.cutout=lambda ident,w:norm.copy()
original=json.loads((E/'inputs/catalog-object.json').read_text());manifest=json.loads((C/'manifest.json').read_text());frames=[];bordermax=0;records=[]
for k in ['frameSize','root','sourceScale','footprint','rootCell','directionFootprints','directionRootCells','projection','facingPolicy','registration']:assert original[k]==manifest[k],k
for clip in manifest['clips']:
 ident=clip['id'];assert clip['fps']==12 and clip['frames']==12 and clip['frameOrder']==list(range(12)) and clip['loop']==(ident=='idle')
 assert len({json.dumps(e,sort_keys=True)for e in clip['directions'].values()})==1
 atlas=pix(C/'atlases'/f'2d-{ident}-S.png');assert atlas.size==(2304,1280)
 anim=Image.open(C/'previews'/f'{ident}-S.png');assert anim.n_frames==12 and anim.info['loop']==(0 if ident=='idle' else 1)
 hashes=[]
 for i in range(12):
  f=C/'raw'/f'{ident}-S-{i:04d}.png';im=pix(f);expected=orig.generated_frame(original,{'id':ident},i);assert im.size==(384,640) and im.tobytes()==expected.tobytes()
  x,y,w,h=clip['directions']['S']['rects'][i];assert [x,y,w,h]==[i%6*384,i//6*640,384,640];assert atlas.crop((x,y,x+w,y+h)).tobytes()==im.tobytes()
  anim.seek(i);assert abs(anim.info['duration']-1000/12)<1e-8 and anim.convert('RGBA').tobytes()==im.tobytes()
  a=im.getchannel('A');bm=max(a.crop(rect).getextrema()[1]for rect in [(0,0,384,1),(0,639,384,640),(0,0,1,640),(383,0,384,640)]);bordermax=max(bordermax,bm);assert bm==0
  h=hashlib.sha256(im.tobytes()).hexdigest();hashes.append(h);frames.append(str(f.relative_to(E)));records.append({'clip':ident,'index':i,'pixelSHA256':h,'alphaBounds':a.getbbox(),'maxAlpha':a.getextrema()[1]})
 report['originalMath'][ident]={'all12FramesEqualUnchangedOriginalPublisher':True,'uniqueImages':len(set(hashes)),'atlasRectPixelsEqual':True,'apngFramesPixelsAnd1Over12SecondDurationsEqual':True}
assert len(d['rawFrames'])==144 and len({r['path']for r in d['rawFrames']})==36 and len(d['atlases'])==12 and len({r['path']for r in d['atlases']})==3
for r in d['rawFrames']+d['atlases']:assert sha(E/r['path'])==r['sha256']
report['coverage']={'uniqueFrames':36,'logicalFacingSlots':144,'atlasFiles':3,'atlasEntries':12,'sameDirectionAliases':True,'allBordersAlphaZero':bordermax==0,'frameRecords':records}
# Exact current methods must be copied byte for byte, not a recreated imitation.
root=E.parents[3]
for name in ['restaurant_view.gd','art_book.gd','typography.gd']:
 current=root/'godot/scripts'/name;resource=S/'resources/context/runtime-scripts'/name;harness=C/'native-context/scripts'/name
 assert current.read_bytes()==resource.read_bytes()==harness.read_bytes(),name
 report['runtimeScripts'][name]={'currentSHA256':sha(current),'copyBytesEqual':True}
# Rebuild with source only, no adjacent input/review/production tree, no sealed mutations.
paths=set(d['resources']+[d['project'],d['recipeScript'],d['recipe'],d['validation'],d['manifest']]+list(d['heroes'].values())+list(d['previews'].values())+[r['path']for r in d['rawFrames']+d['atlases']])
before={p:sha(E/p)for p in paths};replayed={}
with tempfile.TemporaryDirectory(prefix='judge-round01-',dir=E/'reviews')as td:
 clone=Path(td)/'isolated-object';(clone/'source').mkdir(parents=True);shutil.copytree(S,clone/'source/round01',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 assert not(clone/'inputs').exists() and not(clone/'reviews').exists() and not(clone/'production').exists()
 outputs=[]
 for script in ['prepare_sources.py','publish.py']:
  result=subprocess.run([sys.executable,str(clone/'source/round01'/script)],cwd=td,capture_output=True,text=True,check=True);outputs.append(result.stdout.strip())
 for p,h in before.items():
  if p.startswith('candidates/')or p in[d['project'],d['recipe'],'source/round01/crop.json']:
   assert(clone/p).is_file(),p;assert sha(clone/p)==h,('byte mismatch',p);replayed[p]=h
 for p in set(r['path']for r in d['rawFrames']+d['atlases']):assert pix(clone/p).tobytes()==pix(E/p).tobytes()
 assert sha(clone/'delivery.json')==sha(E/'delivery.json')
 report['sourceOnlyReplay']={'sourceClosureRelocatedAlone':True,'noAdjacentInputsReviewsProduction':True,'comparedOutputBytes':len(replayed),'deliveryBytesEqual':True,'all36FramesAnd3AtlasesPixelsEqual':True,'publisherStdout':outputs}
assert before=={p:sha(E/p)for p in paths}
assert sha(C/'packet.json')==report['packetSHA256']
report['sealedBytesUnchanged']=True
(E/'reviews/round01-independent-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items()if k!='coverage'},indent=2))
