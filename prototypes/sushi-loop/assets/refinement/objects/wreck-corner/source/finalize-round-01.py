from pathlib import Path
import json,hashlib,sys,platform,subprocess
import PIL,numpy as np
S=Path(__file__).resolve().parent;B=S.parent;O=B/'candidates/round-01'
def load(p):return json.loads(Path(p).read_text())
def write(p,d):Path(p).write_text(json.dumps(d,indent=2)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def relative(p):return Path(p).relative_to(B).as_posix()
# Preserve exact measured supplements generated after baseline analysis without any new art rendering.
f=load(O/'finite-contract-proof.json');ports=load(S/'resources/root-native-contract.json')['nativeContract']['finitePorts']['sourceOrderedCaps']
for x in f['wholeFiniteCollarChecks']:
 kind=x['object'].split('__')[1].split('_')[0];expected=next(z['sourceOrderedCap'] for z in ports if z['side']==x['side'] and z['rail']==kind)
 if x['side']=='N':expected=[[v[1],-v[0],v[2]] for v in expected]
 error=max(min(float(np.linalg.norm(np.array(p)-q)) for q in expected) for p in x['orderedFiniteCap']);x.update(sourceOrderedFiniteCap=expected,maxOrderedContourDistance=error,sourceContourEquivalent=error<1e-6)
write(O/'finite-contract-proof.json',f)
v=load(O/'validation.json');g=load(O/'active-graph-correspondence.json');v['technicalChecks'].update(exactCanonicalMaterialGraphs=all(m['actualFullGraphIdentical'] for m in g['materialComparisons']),exactCanonicalRigWorldCompositor=g['worldGraphIdentical'] and g['compositorGraphIdentical'] and g['actualLightDataGraphsMatricesIdentical'],actualOrderedPortContours=all(x['sourceContourEquivalent'] for x in f['wholeFiniteCollarChecks']));v['evidence']['actualActiveGraphCorrespondence']='candidates/round-01/active-graph-correspondence.json';v['replayPrecision']={'decodedEqualDirections':['N','E','W'],'S':{'differentPixels':1,'maxRGBA':[0,1,0,0]},'interpretation':'Second saved-source EEVEE recapture is retained exactly as measured: one green-channel LSB residual at S. First inspection had decoded equality in all4; no cherry-picked rerender replaces these current report bytes.'};write(O/'validation.json',v)
node=json.loads(subprocess.check_output(['node','-e',"console.log(JSON.stringify({node:process.version,nodeExecutable:process.execPath,playwright:require('@playwright/test/package.json').version,esbuild:require('esbuild/package.json').version,react:require('react/package.json').version}))"],cwd=B.parents[5],text=True))
write(S/'consumer/tooling-requirements.json',{'browserTooling':node,'python':{'executable':sys.executable,'version':platform.python_version(),'pillow':PIL.__version__,'numpy':np.__version__},'blender':{'executable':'/opt/homebrew/bin/blender','version':'5.2.2 LTS','build':'d13f752e3b9c'},'assetRuntimeDependencies':'No external image textures or linked Blender libraries. The standalone browser fixture.bundle.js includes its actual imported React code; source helpers remain exact unchanged570/099. Tool installations are recorded, not copied as application trees.'})
results=load(O/'consumer/results.json');inputs=[]
for p in sorted((S/'resources').rglob('*')):
 if p.is_file():inputs.append({'path':relative(p),'sha256':sha(p)})
write(O/'consumer-input-binding.json',{'pathBase':'object-root','sourceSHA256':sha(S/'round-01.blend'),'browserResults':'candidates/round-01/consumer/results.json','browserResultsSHA256':sha(O/'consumer/results.json'),'fixturesAndCatalogsAndAuthorities':inputs,'fixtureCode':[{ 'path':relative(p),'sha256':sha(p)} for p in sorted((S/'consumer').iterdir()) if p.is_file()],'nativeControlsAndIndividualAtlasHashes':'Every run retains actual fixture/helper/native-control/individual-frame hashes in results.json; all catalog JSON and exact approved source/individual art are additionally bound here.'})
# Actual portable delivery files; source provenance/initial remain immutable and are also bound.
manifest=S/'resource-manifest-round-01.json';delivery=O/'delivery.json';excluded={manifest.resolve(),delivery.resolve()}
files=[]
for directory in [S,O]:
 for p in sorted(directory.rglob('*')):
  if not p.is_file() or p.resolve() in excluded:continue
  assert '__pycache__' not in p.parts, f'Unexpected bytecode cache {p}'
  assert p.stat().st_size<100_000_000,f'File above100MB {p}'
  files.append({'path':relative(p),'sha256':sha(p),'bytes':p.stat().st_size})
write(manifest,{'asset':'wreck-corner','round':'round-01','pathBase':'object-root','scope':'Private actual-used portable native/consumer evidence closure plus retained independent initial/source-inspection provenance; no application/runtime trees','files':files,'externalTooling':'source/consumer/tooling-requirements.json','externalAssetResources':[],'candidateProjectSHA256':sha(S/'round-01.blend'),'excludesToAvoidHashCycle':['source/resource-manifest-round-01.json','candidates/round-01/delivery.json'],'approval':'pending original independent judge'})
heroes={d:'candidates/round-01/frames/static/'+d+'/000.png' for d in 'NESW'}
deliver={'asset':'wreck-corner','round':'round-01','project':'source/round-01.blend','recipeScript':'source/round-01-recipe.py','validation':'candidates/round-01/validation.json','nativeRecords':{'camera':'candidates/round-01/published-camera.json','assetRecord':'candidates/round-01/assetRecord.json','rig':'candidates/round-01/rig.json'},'heroes':heroes,'previews':{'four-view-sheet':'candidates/round-01/four-view-sheet.png','repeated':'candidates/round-01/native-assemblies-logical128.png','consumer-logical128':'candidates/round-01/consumer-assemblies-logical128.png','phone':'candidates/round-01/phone32-actual-css.png'},'rawFrames':[{'clip':'static','direction':d,'index':0,'path':heroes[d]} for d in 'NESW'],'nativeRawFrames':[{'clip':'static','direction':d,'index':0,'path':'candidates/round-01/native/static/'+d+'/000.png'} for d in 'NESW'],'atlases':[{'clip':'static','direction':d,'path':'candidates/round-01/atlases/static-'+d+'.png','columns':1,'rows':1,'size':[384,704],'rects':[[0,0,384,704]],'sha256':sha(O/'atlases'/('static-'+d+'.png'))} for d in 'NESW'],'resources':[{k:x[k] for k in ['path','sha256']} for x in files]+[{'path':relative(manifest),'sha256':sha(manifest)}],'resourceManifest':{'path':relative(manifest),'sha256':sha(manifest),'pathBase':'object-root'},'changeNotes':['Continuous native soft blue L rails with canonical contact collars and exact lowest support.','Rounded interior turn, two rear timber courses, open iron framing, pale fasteners and restrained shallow crafted details.','All4 exact native2x publication, true native and mixed L controls, actual current-consumer comparisons in eight prescribed Chromium153 runs.'],'technicalLimits':['No editor approval. Original independent judge must inspect every declared hero/preview and localized contact evidence.','Current clean saved-source replay retains one green-channel LSB difference in one S pixel; N/E/W decode exactly.','Native-vs-independent contacts retain alpha equality with at most2-level RGB differences; full raw, finite collar/contact masks, exterior and CSS residuals are separately retained.'],'publication':'Exact direct native2x full PNG identity; atlas pixels identical; no reduction/fit/paint/repair','sourceSHA256':sha(S/'round-01.blend')}
write(delivery,deliver)
for row in files:
 p=B/row['path'];assert sha(p)==row['sha256'];p.chmod(0o444)
manifest.chmod(0o444);delivery.chmod(0o444)
print(json.dumps({'delivery':str(delivery),'deliverySHA256':sha(delivery),'project':str(S/'round-01.blend'),'projectSHA256':sha(S/'round-01.blend'),'resourceManifest':str(manifest),'resourceManifestSHA256':sha(manifest),'files':len(files),'largestFileBytes':max(x['bytes'] for x in files),'sourceAndRoundMode':'0444','noPacketSeal':True},indent=2))
