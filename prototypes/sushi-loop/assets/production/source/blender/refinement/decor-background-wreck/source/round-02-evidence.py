"""Record honest browser/native publication differences and runtime provenance."""
from pathlib import Path
from PIL import Image,ImageChops
import hashlib,json,re,sys,shutil
P=Path(__file__).resolve().parent;B=P.parent;O=B/'candidates/round-02'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
ledger=json.loads((O/'consumer-ledger.json').read_text());runs=ledger['runs'];comparisons=[]
for kind in ['cases','viewportContexts']:
 for i,(a,b) in enumerate(zip(runs[0][kind],runs[1][kind])):
  pa,pb=B/a['screenshot'],B/b['screenshot'];ia,ib=Image.open(pa).convert('RGBA'),Image.open(pb).convert('RGBA');diff=ImageChops.difference(ia,ib);hist=diff.histogram();count=sum(1 for p in diff.getdata() if any(p))
  comparisons.append({'kind':kind,'index':i,'fullChromium':a['screenshot'],'headlessShell':b['screenshot'],'size':ia.size,'nativeCanvasRGBAEqual':a['nativeCanvasRGBA256']==b['nativeCanvasRGBA256'],'screenshotByteEqual':sha(pa)==sha(pb),'decodedPixelsEqual':diff.getbbox(alpha_only=False) is None,'changedPixels':count,'maxChannelDifference':max(e[1] for e in diff.getextrema()),'differenceBounds':diff.getbbox(alpha_only=False)})
(O/'browser-mode-comparison.json').write_text(json.dumps({'asset':'decor-background-wreck','scope':'Current candidate same native canvas versus actual ordinary CSS screenshots; no defect waiver implied.','comparisons':comparisons},indent=2)+'\n')

launches=re.findall(r'<launching> (.*?) --disable-field-trial-config',(O/'consumer-capture.log').read_text())
runtime=[]
for mode,p in zip(['full-chromium','headless-shell'],launches):
 runtime.append({'mode':mode,'actualExecutable':p,'sha256':sha(p),'bytes':Path(p).stat().st_size,'source':'Exact pw:browser launch log, bound as consumer-capture.log; runtime binary deliberately not copied.'})
assert len(runtime)==2,launches
repo=B.parents[5]
packages=[]
for name in ['@playwright/test','playwright','playwright-core']:
 f=repo/'node_modules'/name/'package.json';dest=P/'round-02-resources/runtime-package-metadata'/name.replace('/','-')/'package.json';dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dest);packages.append({'name':name,'version':json.loads(f.read_text())['version'],'actualSourcePath':str(f),'frozenPath':str(dest.relative_to(B)),'sha256':sha(dest)})
env={'asset':'decor-background-wreck','pythonExecutable':sys.executable,'pythonVersion':sys.version,'pillow':Image.__version__,'node':ledger['node'],'browserRuns':[{'mode':r['mode'],'version':r['browserVersion'],'launch':r['launch'],'dpr':r['dpr'],'errors':r['errors']} for r in runs],'actualBrowserExecutables':runtime,'runtimePackageMetadata':packages,'helperSHA256':ledger['helperSHA256'],'runtimePolicy':'Only exact small authored helpers, prebuilt self-contained browser bundle, metadata and frozen art copied. Standard Blender/Python/Node/Playwright runtime and browser application trees not duplicated. No mutable project helper import in native recipe.','retainedAttempts':[{'action':'First round02 capture command before new output directory existed','result':'Shell redirection failed before Blender started; created new02 candidate directory and ran actual capture. No existing artifact overwritten.'}]}
(O/'environment.json').write_text(json.dumps(env,indent=2)+'\n')

native=json.loads((O/'native-validation.json').read_text());camera=json.loads((P/'round-02-resources/native/registered-camera.json').read_text())
measure=[]
for r in native['captureRecords']:
 projection=r['projectionMatrix'];pd=max(abs(projection[i][j]-camera['camera']['projectionMatrix'][i][j]) for i in range(4) for j in range(4))
 im=Image.open(B/r['path']);bbox=im.getchannel('A').getbbox();measure.append({'direction':r['direction'],'actualRootPixels':r['rootPixels'],'rootErrorPixels':[r['rootPixels'][0]-384,r['rootPixels'][1]-992],'projectionMaxDifference':pd,'alphaBounds':bbox,'completeCanvasSize':im.size,'clippedAlpha':bbox[0]<=0 or bbox[1]<=0 or bbox[2]>=768 or bbox[3]>=1408})
validation={'asset':'decor-background-wreck','round':'round-02','nativeValidation':'candidates/round-02/native-validation.json','sourceAudit':'candidates/round-02/source-settings-audit-v2.json','sourceProjectSHA256':native['sourceProjectSHA256'],'cameraRegistration':measure,'nativeGeometryEnvelope':{'rest':native['restBounds'],'budget':native['restEnvelope'],'tolerance':1e-6,'passedMeasuredBudget':native['restEnvelopePass']},'static':{'fps':12,'frames':1,'loop':False,'frameOrder':[0],'sampleSeconds':[0,1/12,11/12,2],'geometryEquality':native['staticHoldGeometryEqual'],'temporalOwners':len(native['effectiveTemporalOwners']),'channelEvidence':'candidates/round-02/native-validation.json'},'publicationProof':'candidates/round-02/publication-proof.json','consumerLedger':'candidates/round-02/consumer-ledger.json','browserComparison':'candidates/round-02/browser-mode-comparison.json','lighting':native['renderRecipe']['render']['lighting'],'resourceClosure':'No external image or linked library dependencies in saved source; actual used private native camera/helper/browser/art closure is object-relative and hash-bound by resource manifest.','historicalResiduals':{'sourceReplay':'reviews/preparation-v1/source-pixel-comparison.json','sourceBrowserModes':'reviews/preparation-v1/browser-mode-comparison.json','interpretation':'Historical source/native publication residuals are retained frozen preparation evidence; no claim that new native art equals historical pixels. Current candidate mode-specific CSS differences remain in the separate exact comparison ledger.'},'limits':['One standalone static background asset; no modular seam/port/family approval or collision expansion.','Bounded exact SpriteScene helper fixture, no full production React UI/Godot/device claim.','Four native views measured at render time from clean saved source; no perview fit, nudge, recolor, warp or alpha/RGB repair.','No visible quality approval asserted by this technical validation; original independent judge must inspect declared exact media.']}
(O/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
print(json.dumps({'cases':len(comparisons),'nativeCanvasAllEqual':all(x['nativeCanvasRGBAEqual'] for x in comparisons),'maxCSSChannelDifference':max(x['maxChannelDifference'] for x in comparisons),'camera':measure,'runtime':runtime},indent=2))
