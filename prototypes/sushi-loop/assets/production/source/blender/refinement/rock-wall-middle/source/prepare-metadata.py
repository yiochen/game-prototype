from pathlib import Path
import hashlib,json
B=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
b=json.loads((B/'brief.json').read_text());c=json.loads((B/'inputs/source-camera.json').read_text());orig=json.loads(json.dumps(c))
c['captureScale']=2;c['calibration']={k:[v/2 for v in vals] for k,vals in c['calibration'].items()};c['nativeCaptureScale']=4;c['nativeFrame']=[768,1408];c['nativeRecord']='../candidates/round-03/native-audit.json';c['artStyle']={'revision':'rock-family-soft-cobalt-round03','source':'round-03-recipe.json','perViewFit':False,'perViewRecolor':False}
(B/'source/published-camera.json').write_text(json.dumps(c,indent=2))
a=json.loads((B/'inputs/source-assetRecord.json').read_text());a['scale']=2;a['nativeScale']=4;a['artStyle']=c['artStyle'];(B/'source/published-assetRecord.json').write_text(json.dumps(a,indent=2))
r=json.loads((B/'inputs/source-rig.json').read_text());r['groundRootObject']='rock-wall-middle__root';r['source']='round-03.py';r['status']='native-static-no-rig';r['sourceFiles']={'round-03.py':sha(B/'source/round-03.py')};(B/'source/rig.json').write_text(json.dumps(r,indent=2))
proj=(B/b['source']['project']).resolve();backup=(B/b['source']['backup']).resolve()
(B/'source/original-hashes.json').write_text(json.dumps({'source':{'path':str(proj),'sha256':sha(proj)},'untouchedBackup':{'path':str(backup),'sha256':sha(backup)},'expected':b['source']['projectSHA256'],'snapshot':sha(B/'inputs/original.png'),'target':sha(B/'inputs/target.png'),'brief':sha(B/'brief.json'),'criteria':sha(B/'reviews/criteria.json')},indent=2))
rec=json.loads((B/'source/round-03-recipe.json').read_text());rec['implementationScript']='round-03.py';rec['implementationScriptSHA256']=sha(B/'source/round-03.py');rec['scope']='Reusable common native rock-wall family material, symmetric lighting, registered camera, root and exact connector profile; only middle is modeled/reviewed here. Fresh independent pairs required for future objects.';rec['approval']='Pending independent candidate-specific judge; no family approval inferred.'
(B/'source/family-settings.json').write_text(json.dumps(rec,indent=2))
(B/'source/resource-closure.json').write_text(json.dumps({'project':'round-03.blend','projectSHA256':sha(B/'source/round-03.blend'),'usedResources':[],'textures':[],'linkedLibraries':[],'closure':'Native geometry, point-color albedo, shader, lights and camera stored inside the blend. No external image resources and no target plane.','relocatedCopySHA256':sha(B/'source/relocated/round-03.blend'),'relocatedCopyMatches':sha(B/'source/round-03.blend')==sha(B/'source/relocated/round-03.blend')},indent=2))
print('metadata ready')
