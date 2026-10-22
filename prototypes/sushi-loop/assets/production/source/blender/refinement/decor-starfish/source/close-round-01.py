"""Bind final round01 source, frames and evidence without altering native art.
Run after build, audit, package and consumer recipes. Refuses an existing packet.
"""
from pathlib import Path
import json,hashlib,subprocess,sys
BASE=Path(__file__).resolve().parent.parent;OUT=BASE/'candidates/round-01'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not (OUT/'packet.json').exists()
assert sha(BASE/'brief.json')=='d0b8c61476100e6fc5c08c206d1530575fda19b79eb888c677c916f490df06b7'
assert sha(BASE/'reviews/proposedcriteria.json')=='402cefa562a17c93c76d7a1c76b45f503750231967654c7f4789ef70de5bd069'
old=json.loads((OUT/'validation.json').read_text());audit=json.loads((OUT/'source-audit.json').read_text())
for k in ['alpha','publishedSampling','originalSourceSHA256','originalBackupSHA256','portableReplay']:audit[k]=old[k]
audit['checks'].update({k:v for k,v in old['checks'].items() if k not in audit['checks']})
consumer=json.loads((OUT/'consumer/evidence.json').read_text());replay=json.loads((OUT/'portable-replay.json').read_text())
audit['consumer']={'evidence':'candidates/round-01/consumer/evidence.json','actualCatalogRenderer':True,'productionFilesEdited':False,'phoneViewport':[390,844],'desktopViewport':[1440,1000],'landscapeViewport':[844,390],'candidateRequestsBoundBySHA256':True,'family':'W12','errors':consumer['errors']}
audit['checks']['consumerErrorsEmpty']=not consumer['errors'];audit['checks']['consumerCodeUnchanged']=consumer['dependenciesUnchanged'];audit['checks']['consumerExactCandidateAtlases']=len(consumer['responses'])>=4 and all(r['sha256']==r['expectedSHA256'] for r in consumer['responses']);audit['checks']['publishedReplayPNGExact']=all(v['exactPublishedPNG'] for v in replay['views'].values())
audit['replayMetadataNote']='Native PNG metadata records path,Date and render timings. All four native RGBA buffers and all four published PNG files reproduce exactly.'
assert all(audit['checks'].values()),{k:v for k,v in audit['checks'].items() if not v}
assert audit['originalSourceSHA256']==audit['originalBackupSHA256']=='b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6'
(OUT/'validation.json').write_text(json.dumps(audit,indent=2)+'\n')
d=json.loads((OUT/'delivery.json').read_text());d['previews'].update({'phone-catalog-family':'candidates/round-01/consumer/phone-W12-family.png','phone-standalone':'candidates/round-01/consumer/phone-standalone-context.png','phone-thumbnail':'candidates/round-01/consumer/phone-starfish-thumbnail.png','phone-four-facings':'candidates/round-01/consumer/phone-four-facings.png','desktop-layered-scenery':'candidates/round-01/consumer/desktop-interaction.png'})
d['evidence'].update({'sourceTransformsEvaluated':'source/source-transforms-evaluated.json','portableReplays':'candidates/round-01/portable-replay.json','consumer':'candidates/round-01/consumer/evidence.json','closureRecipe':'source/close-round-01.py'})
d['reproduction']={'nativeReopenCommand':'blender -b source/round-01.blend --python source/replay-round-01.py -- /absolute/empty-output','buildCommand':'blender -b --python source/round-01-recipe.py','buildInputs':['source/round-01-recipe.py','source/replay-round-01.py','inputs/source-camera.json'],'publicationCommand':'python source/package-round-01.py','publicationDependency':'Pillow','nativeSceneExternalDependencies':[],'pixelReproduction':'Native four-view RGBA exact; published four PNG exact. Native PNG metadata path/date/timings may differ.'}
resources=[p.relative_to(BASE).as_posix() for folder in [BASE/'source',OUT] for p in sorted(folder.rglob('*')) if p.is_file() and p.name not in ['packet.json','delivery.json']]
resources+=['inputs/source-camera.json','inputs/source-assetRecord.json','inputs/source-rig.json','inputs/catalog-object.json','reviews/proposedcriteria.json']
d['resources']=resources
(OUT/'delivery.json').write_text(json.dumps(d,indent=2)+'\n')
args=[sys.executable,str(BASE/'source/candidate_packet.py'),'create','--brief',str(BASE/'brief.json'),'--project',str(BASE/'source/round-01.blend'),'--validation',str(OUT/'validation.json'),'--output',str(OUT/'packet.json')]
for direction in 'NESW':args+=['--render',f'{direction}={OUT}/static-{direction}.png']
for name,p in d['previews'].items():args+=['--preview',f'{name}={BASE/p}']
for i,p in enumerate(resources+['candidates/round-01/delivery.json']):args+=['--resource',f'{i:03d}:{Path(p).name}={BASE/p}']
subprocess.run(args,check=True)
subprocess.run([sys.executable,str(BASE/'source/candidate_packet.py'),'verify','--packet',str(OUT/'packet.json')],check=True)
for p in [OUT/'packet.json',OUT/'delivery.json',BASE/'source/round-01.blend',OUT/'validation.json']:print(p.relative_to(BASE),sha(p))
