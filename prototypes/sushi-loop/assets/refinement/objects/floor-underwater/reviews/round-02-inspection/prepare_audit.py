import sys,json,hashlib,shutil,difflib,os
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent; O=P.parent.parent; RUN=O.parent.parent; REPO=RUN.parents[4]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def desc(p):return {'path':os.path.relpath(p,O),'sha256':sha(p),'bytes':p.stat().st_size,'relativeTo':'object','pathBase':str(O)}
old=P.parent/'round-01-inspection'; previous=read(old/'manifest.json'); seal=read(old/'seal.json')
for k in ['review','manifest']:
 r=seal[k];assert sha(O/r['path'])==r['sha256']
for r in previous['files']:
 p=Path(r['pathBase'])/r['path'];assert p.stat().st_size==r['bytes']<100_000_000;assert sha(p)==r['sha256'],p
packet=O/'candidates/round-02/packet.json'; d=read(packet); d0=read(O/'candidates/round-01/packet.json'); checked={}
for group in ['files','candidateRenders','previews']:
 for name,r in d[group].items():
  p=(packet.parent/r['path']).resolve();assert p.is_file(),p;assert sha(p)==r['sha256'],p;assert p.stat().st_size<100_000_000
  checked[str(p)]=desc(p)
coverage=[]; oldcoverage={(x['packetGroup'],x['name']):x for x in read(old/'coverage-map.json')['coverage']}
for group in ['candidateRenders','previews']:
 for name,r in d[group].items():
  p=(packet.parent/r['path']).resolve(); item={'packetGroup':group,'name':name,'packetPath':r['path'],'source':desc(p)}
  if name in d0[group]:
   r0=d0[group][name];p0=(O/'candidates/round-01'/r0['path']).resolve()
   assert p==p0 and r['sha256']==r0['sha256']==oldcoverage[(group,name)]['source']['sha256']
   item.update({'method':'Reused original judge actual visual/APNG inspection, with independently verified exact byte/path identity; no new native render.', 'priorPacketPath':r0['path'],'priorCoverageReceipt':desc(old/'coverage-map.json'),'priorReview':desc(O/'reviews/round-01.json'),'priorInspectionMethod':oldcoverage[(group,name)]['method']})
  else:
   item['method']='Exact new declared browser screenshot directly opened and independently visually inspected in round02. Continuous water, pale ridges, legible actor/rock, no fine transparent grid.'
  coverage.append(item)
assert len(coverage)==39 and len(oldcoverage)==37
b0=read(O/'brief.json');b2=read(O/'brief-v2-runtime-grid.json')
changed=[k for k in b0.keys()|b2.keys() if b0.get(k)!=b2.get(k)];assert set(changed)=={'technicalResources','consumerRevision'}
for k in ['qualityCriteria','capture','style']:assert d0[k]==d[k]
resources=P/'resources'
for name in ['node-loaded']:
 shutil.copytree(old/'resources'/name,resources/name,dirs_exist_ok=True)
renderer=O/'../../../../wireframe/world-sprite-raster.js';current=renderer.read_text();assert sha(renderer)=='570a0d0d788ab65252724da1f0ff7d82a086eab1875ba37ed032dac34acf9545'
(resources/'world-sprite-raster.js').write_bytes(renderer.read_bytes())
excerpt=current[current.index('export function worldRasterPlan'):current.index('export function useWorldSpriteRaster')]
(resources/'world-raster-functions.js').write_text(excerpt)
oldrenderer=O/'reviews/preparation-v1/resources/world-sprite-raster.js';assert sha(oldrenderer)=='4ddc7495ade39f75adcce7d5400fc54326d588270b6fad9a5cca133f7df34bb0'
(resources/'world-sprite-raster-old.js').write_bytes(oldrenderer.read_bytes())
oldtext=oldrenderer.read_text();(resources/'world-raster-functions-old.js').write_text(oldtext[oldtext.index('export function worldRasterPlan'):oldtext.index('export function useWorldSpriteRaster')])
(resources/'renderer.diff').write_text(''.join(difflib.unified_diff(oldtext.splitlines(True),current.splitlines(True),fromfile='original-4ddc7495',tofile='current-570a0d0d')))
for src,name in [(RUN/'preparation/floor-underwater/publish-consumer-v2.py','publish-consumer-v2.py'),(RUN/'tools/acceptance_contract.py','acceptance_contract.py')]:shutil.copyfile(src,resources/name)
write(P/'coverage-map.json',{'candidatePacket':desc(packet),'declaredCount':39,'reusedExactPriorInspections':37,'newDirectInspections':2,'coverage':coverage})
write(P/'reuse-audit.json',{'oldReview':desc(O/'reviews/round-01.json'),'oldManifest':desc(old/'manifest.json'),'oldSeal':desc(old/'seal.json'),'oldManifestFilesRehashed':len(previous['files']),'newPacket':desc(packet),'uniquePacketResourcesRehashed':len(checked),'packetGroupsHashVerified':['files','candidateRenders','previews'],'versionBriefChangedKeys':changed,'nativeTargetCriteriaCaptureReuse':True,'exactUnchangedBindings':[desc(O/x) for x in ['source/round-01.blend','inputs/target.png','inputs/root-native-contract.json','reviews/proposedcriteria.json','reviews/source-contract-proposal.json']],'priorFailureRetained':{'cases':1476,'failedCases':264,'aggregateMinAlpha':128,'reviewRemains':'needs_evidence'},'packetResources':list(checked.values())})
print(json.dumps({'oldClosureFilesRehashed':len(previous['files']),'newPacketUniqueResourcesRehashed':len(checked),'mediaCoverage':len(coverage),'exactOldMediaReused':37,'newDirectMedia':2,'rendererSHA256':sha(renderer)}))
