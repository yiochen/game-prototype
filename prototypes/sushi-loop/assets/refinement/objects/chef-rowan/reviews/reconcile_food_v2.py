import json,pathlib,hashlib,copy
from PIL import Image
b=pathlib.Path('prototypes/sushi-loop/assets/refinement/objects/chef-rowan').resolve()
brief=json.loads((b/'brief-v2-food.json').read_text());old=json.loads((b/'brief.json').read_text())['qualityCriteria'];dep=brief['foodDependency'];c=copy.deepcopy(old)
c['status']='proposed-awaiting-coordinator-freeze';c['version']=2
c.pop('criteriaFile',None);c.pop('criteriaFileSHA256',None)
c['revisionPurpose']='Versioned approved salmon artwork dependency only. All frozen v1 body modeling, identity, style, camera/root/height/bob, rig, contacts, state/facing/frame/timing, native knife and decision criteria remain unchanged.'
c['priorCriteria']={'path':'reviews/criteria.json','sha256':hashlib.sha256((b/'reviews/criteria.json').read_bytes()).hexdigest(),'frozenBy':'brief.json qualityCriteria version1'}
c['immutableTechnical']['heldComposition']='Use the exact new approved canonical salmon PNG SHA2564389d1e6607e6afbfb3cd03594afb4196394b14c5ee6ca6a92fb534cd3b9ebe4,731x505, as a packed2D raster texture. Replace only the old salmon texture/hash/UV/aspect restriction: use one fixed full-source UV rectangle [0,0,731,505] (top-origin pixels), equivalent normalized UV0..1 on both axes; preserve source aspect731:505 at0.35world-cell display width. Preserve original plate-bottom palm anchor and original evaluated food-root/action/visibility paths, native yaw cancellation and0.6world-cell camera-ray depth bias. No added crop, per-pose fitting, warping, repainting or fake3D food. Declared2D display plane remains excluded from physical body-footprint bounds. Keep native knife native.'
# This wording change identifies the versioned texture; it does not change the material-detail bar.
c['aesthetic']['materialDetail']['observablePass'][-1]='Metal knife remains a native prop; salmon remains explicitly the exact approved new2D canonical artwork defined by immutableTechnical.heldComposition.'
c['requiredCandidateEvidence']+=['Held/load context for every actual facing, including all indexed frames and actual12fps playback, must show the exact new canonical salmon at the fixed original palm/plate-bottom anchor. Assess coherent size, readability, alpha edge/overlap and absence of clipping or flicker within the preserved action/depth contract. This Rowan candidate may establish its own final canonical salmon dependency.','Saved/reopened native texture/UV/source-version audit must bind the packed canonical PNG hash, original approved dependency packet/review receipt hashes,731x505 dimensions, one full-source UV rectangle,731:505 plane aspect,0.35world-cell width, unchanged food-root and plate-bottom anchor, yaw cancellation,0.6depth bias and original per-state visibility/actions. Retain explicit old-to-new source/UV/aspect revision; no stale packed oldsalmon in the final candidate.']
evidence={}
for k,h in [('artwork','sha256'),('packet','packetSHA256'),('review','reviewSHA256')]:
 p=(b/dep[k]).resolve();actual=hashlib.sha256(p.read_bytes()).hexdigest()
 if actual!=dep[h]:raise ValueError('Dependency hash mismatch '+k)
 evidence[k]={'path':dep[k],'sha256':actual,'hashVerified':True}
im=Image.open((b/dep['artwork']).resolve()).convert('RGBA')
if list(im.size)!=[731,505] or list(im.getbbox())!=[0,0,731,505]:raise ValueError('Canonical image dimensions/alpha rectangle mismatch')
c['foodDependency']={**copy.deepcopy(dep),'inspectionEvidence':{'canonicalImageDirectlyViewed':True,'size':list(im.size),'fullSourceAlphaRectangleTopOrigin':list(im.getbbox()),'worldDisplayWidth':.35,'worldDisplayHeightAtCanonicalAspect':.35*505/731,'receipts':evidence,'independence':'Inspected canonical artwork and its packet source binding as dependency material. Verified approval-review bytes against coordinator receipt without reading another judge aesthetic critique. No Rowan candidate exists or has been judged.'}}
# Verify all non-food technical gates are byte-for-byte equal as JSON values.
for k,v in old['immutableTechnical'].items():
 if k!='heldComposition':assert c['immutableTechnical'][k]==v
for k,v in old['aesthetic'].items():
 if k!='materialDetail':assert c['aesthetic'][k]==v
assert c['decisionPolicy']==old['decisionPolicy']
path=b/'reviews/criteria-v2-food.json';path.write_text(json.dumps(c,indent=2)+'\n');print(path)
