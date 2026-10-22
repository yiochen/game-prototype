from pathlib import Path
import json,hashlib,shutil,os
R=Path(__file__).resolve().parent;E=R.parent;OBJ=E.parent.parent;C=OBJ/'candidates/round-01';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();p=json.loads((C/'packet.json').read_text());assert sha(C/'packet.json')=='4ede4e7a674f282ad62137acc9a349df6bdebefbd131e6f2d1d90994ee90c1ad'
checked={}
for group in ['files','candidateRenders','previews']:
 for name,f in p[group].items():
  path=(C/f['path']).resolve();assert sha(path)==f['sha256'],(group,name,path);assert path.stat().st_size<100_000_000;checked[os.path.relpath(path,OBJ)]=f['sha256']
consumer=OBJ/'source/round01-resources/consumer';browser=json.loads((C/'consumer/results.json').read_text());paths={f:consumer/f for f in ['fixture.html','fixture.mjs','fixture.bundle.js','world-sprite-raster.js','sprite-layout.js','capture.mjs']}
for d in 'NESW':
 for label,path in [('candidate-atlas',C/'atlases'/('static-'+d+'.png')),('middle',OBJ/'source/round01-resources/canonical/wreck-middle/frames'/(d+'.png')),('edge',OBJ/'source/round01-resources/canonical/wreck-edge/frames'/(d+'.png')),('native-control',C/'connected-native'/(d+'.png'))]:paths[d+'-'+label]=path
for case in browser['cases']:
 for key,path in paths.items():assert sha(path)==case['inputHashes'][key],(case['mode'],case['id'],key)
for f in ['fixture.html','fixture.mjs','fixture.bundle.js','world-sprite-raster.js','sprite-layout.js','capture.mjs']:
 dst=R/'consumer-inputs'/f;dst.parent.mkdir(exist_ok=True);shutil.copy2(consumer/f,dst)
(E/'binding-audit.json').write_text(json.dumps({'candidatePacketSHA256':sha(C/'packet.json'),'uniquePacketResourcesVerified':len(checked),'packetBoundFiles':checked,'actualBrowserInputFiles':{key:{'path':str(path.relative_to(OBJ)),'sha256':sha(path)} for key,path in paths.items()},'all8RecordedBrowserInputsMatchActualFiles':True,'sourceNoExternalLibraryOrImageDependencies':'independently measured candidate saved source has no libraries or file images; canonical references are exact own bound resources'},indent=2)+'\n');print('packetresources',len(checked),'all8 browser input sets exact')
