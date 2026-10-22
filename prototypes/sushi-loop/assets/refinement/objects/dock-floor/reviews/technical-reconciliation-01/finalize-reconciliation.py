from pathlib import Path
import json,hashlib
O=Path(__file__).resolve().parent;R=O.parent;ENTRY=R.parents[1]/'dock-entry/reviews';GAME=R.parents[4]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def item(p):return {'path':str(p),'sha256':sha(p)}
def save(n,x):(O/n).write_text(json.dumps(x,indent=2)+'\n')
analysis=json.loads((O/'analytic-evidence.json').read_text());entry=json.loads((ENTRY/'source-contract-proposal.json').read_text())
retained=[]
for f in analysis['unchangedOriginalReviewHashes']:
 actual=sha(R/f['path']);assert actual==f['sha256'],f['path'];retained.append(f)
verified=[]
# Only technical evidence is verified/read; no entry aesthetic criteria or initial visual assessment opened.
for n in ['source-contract-proposal.json','own-interface-measurements.json','own-consumer-order.json','own-saved-source-semantics.json']:
 verified.append(item(ENTRY/n))
record={
 'asset':'dock-floor',
 'stage':'Technical reconciliation only; no editor or candidate',
 'status':'Sufficient shared interface contract in principle; coordinator may freeze with the boundary-tolerance clarification below',
 'candidateApprovalIssued':False,
 'artApprovalIssued':False,
 'newNativeConstructionOrRenderPerformed':False,
 'scope':'Read entry technical proposal and raw technical records only; independently evaluated source floor geometry/profile, registered projection, actual consumer ordering and bounded interface feasibility. No entry aesthetics/editor rationale read. No Git/live Blender/source/brief/production/promotion edits.',
 'entryTechnicalProposalRead':item(ENTRY/'source-contract-proposal.json'),
 'technicalReferences':verified+[item(R/'contract-measurements.json'),item(R/'native-inspection.json'),item(GAME/'wireframe/sprite-layout.js'),item(GAME/'wireframe/world-sprite-raster.js'),item(O/'analytic-evidence.json')],
 'unchangedOriginalReviews':retained,
 'supersession':'After coordinator freeze, this new shared structural contract supersedes the earlier technical recommendation for a connected-entry visibility variant. Original proposals remain unchanged as historical source audit. A connected masking/capture variant is not part of the accepted current direction.',
 'sharedInterface':{
  'entryRelativeRoot':[0,-1.5,0],
  'rootAndScale':'All registered roots/canvases/facing rotations and world scale stay unchanged. One static frame per N/E/S/W at12fps. Dock3x3, entry1x1; no new clip/gameplay or Godot rollout.',
  'contact':{'entryLocal':{'planeY':0,'topZ':.22,'tangent':[1,0,0],'outwardFaceNormal':[0,1,0]},'floorLocal':{'planeY':-1.5,'topZ':.22,'tangent':[1,0,0],'outwardFaceNormal':[0,-1,0]},'topNormal':[0,0,1],'travelTowardDeck':[0,1,0],'terminalWidthW':{'minimum':.76,'maximum':.96,'centerX':0},'nativeFaceClosure':'Terminal flight is a solid native structure ending atY0; its horizontal top and nonzero-thickness end face meet the floor edge, with no run gap or bevel dip in the centered clear corridor. Top/face correspondence is measured from evaluated surfaces, not inferred from AABBs or alpha opacity.'},
  'entrySolidEnvelope':{'localY':[-.5,0],'localXMaximum':[-.51,.51],'localZ':[0,.49],'note':'Entry technical proposal correctly retains original cap maximum X±.51; it is not an instruction to expand. Visible posts/caps/side structure stay wholly exterior Y<=0. Empty semantic markers are exempt from the solid envelope.'},
  'entryWalkingRole':'Usable centered flight rises monotonically over the exterior halfcell to terminalZ0.22 atY0. Tread count and native construction are editor-owned. The floor supplies the inboard halfcell. Posts/caps leave continuous centered clear width>=0.76, with no trim/fastener/relief obstacle across it.',
  'floorBroadSurface':{'topZ':.22,'allowedReliefAbs':.002,'maxHeight':.25,'footprint':[3,3],'preserve':'Broad support regions and roots/clear volume of existing workshop/submarine/cover. No notch, stair recess, global height change, root shift or footprint expansion.'},
  'floorFunctionalRepairPermission':{'maximumBounds':{'x':[-.50,.50],'y':[-1.50,-1.48]},'surfaceZ':.22,'continuousSupportAcrossX':[-.48,.48],'depth':.02,'purpose':'Close native plank through-gaps at the contact and remove the old0.008 end-bevel run/dip only within this band. Terminate the new surface exactly at the shared plane; merge it into existing support without a lip, open sliver or coplanar duplicate. This is a maximum repair box, not a prescribed threshold beam/topology.','whySufficient':'Measured native bevel top0.212 atY-1.5 returns to0.22 byY-1.49. The0.02 inward band covers that bevel and allows a native transition. Its1.0world maximum width contains all declared terminal widths<=0.96 and preserves clear width>=0.76. No floor geometry must reach exterior toY-1.5.'},
  'semanticMarkers':{'entryLocalApproach':[0,-.5,0],'entryLocalDock':[0,.5,.23],'meaning':'Retain exact semantic coordinates. The inboard dock marker is not the actual transfer plane or a physical0.23walking surface. Future human-contact evidence must use the actual0.22support profile; do not create a false0.01float by interpreting this marker as deck top.'},
  'neighborScope':'Keep existing hut/submarine/cover roots and clearance. Pre-existing hut0.035/submarine0.055support gaps are explicitly assigned to their own later native family support repairs; this floor/entry review makes no zero-gap certification for those neighbors.'
 },
 'tolerancesToFreeze':[
  {'quantity':'Root/facing/semantic socket values and shared boundary Y plane','absoluteTolerance':1e-5,'units':'world units/radians','reason':'Machine-defined registration; this is0.00128logical ground pixels.'},
  {'quantity':'Shared contact boundary top Z nominal0.22, and mutual entry/floor top-profile mismatch','absoluteTolerance':1e-5,'units':'world units','reason':'Use an exact common modeled boundary. Keep decorative broad-surface relief separate; the looser0.002allowance must not permit a mismatch/lip at the actual seam. This is0.000896logical vertical pixels.'},
  {'quantity':'Broad floor top/native walking-surface relief away from common seam','absoluteTolerance':.002,'units':'world units from0.22','reason':'Retains the accepted broad support envelope with0.1792logical vertical pixels of modeling relief. Interface boundary is a stricter exception.'},
  {'quantity':'Entry terminal width W and floor closure width','law':'0.76<=W<=0.96; centered X0. Floor continuous contact support acrossX[-0.48,0.48]. Clear walking width>=0.76. Report actual evaluated W and endpoints; numerical boundary/width checks use1e-5world.'},
  {'quantity':'Floor functional repair bounds','law':'Only X[-0.50,0.50],Y[-1.50,-1.48]; no outward extension, notch or global-height change. Envelope numerical noise<=1e-5world.'},
  {'quantity':'Registered projection/calibration','law':'Exact logical/native frames, sourceScale and atlas layout. Root and basis calibration within0.02logicalpx; one camera/light/material recipe across facings, no subject fitting or individual nudges.'},
  {'quantity':'Consumer seam/visibility evidence','law':'All four native joins and independent actual-order sprite composites must show no sustained visible gap, black crack, hidden cap, ghost tread or alpha fringe at logical/phone sizes on light/gray/dark. Projected geometry-boundary discrepancy<=0.25logicalpx is diagnostic only; it does not excuse a visibly bad seam. No continuous accidental coverage seam>=0.5logicalpx. Physical no-gap check remains1e-5world and cannot be replaced by opacity.'}
 ],
 'entryProposalToleranceClarification':{'entryCurrentText':'Entry proposal permits top0.22±0.002 and profile mismatch<=0.002 at terminal support.','requiredSharedInterpretation':'Use±0.002for the broad/decorative support surface only. Tighten actual common boundary top and mutual mismatch to1e-5world. This is the only contract wording change recommended before freeze.','feasibility':'No construction conflict: a constant terminal boundary atZ0.22 and floor native closure strip atZ0.22 are straightforward while all other free surfaces remain editable.'},
 'consumerOrderingAssessment':{
  'N':'Current order is entry then floor. New exterior caps above deck level project outside the rear deck frontier; floor may correctly occlude lower base portions. Source old inboard posts could be hidden incorrectly; relocating complete solids exterior removes that source contradiction.',
  'S':'Current order is floor then entry. Exterior entry is nearer to camera and may correctly occlude deck where tall caps/posts project over it.',
  'E_and_W':'Current order is floor then entry, but exterior-only native solids occupy the other side of the common screen-X boundary. Height does not change screenX. They should be side-by-side apart from shared antialias coverage.',
  'certificationLimit':'This is a geometric sufficiency argument, not observed candidate success. Bevels, decorative silhouettes, internal holes, native shadows, antialiasing and consumer filtering still need actual proof.'
 },
 'filteringRiskAndRequiredResponse':{'analysis':'Independent touching alpha edges can produce a trough under source-over; with alpha a and1-a, combined alpha is1-a(1-a), as low as0.75. Exact matching solids therefore do not by themselves certify sprite seam coverage.','requiredProof':'Compare actual complete native joined renders against independently assembled exact candidate atlas bytes using current per-facing order, common world phase and ordinary catalog/native-pixel consumer sampling. Inspect quarter-logical-pixel phases and phone reduction, with RGB and alpha together on all three backgrounds. Include standalone source atlases so no assembly patch conceals bad captures.','failureDisposition':'If a visible seam/order conflict persists after correct native geometry/capture, stop for shared technical reconciliation. Do not silently add masks, per-facing fitting, pixel patches or alter the frozen exterior-only geometry. A later alternative would need explicit coordinator reconciliation.'},
 'laterMandatoryEvidence':[
  'Hash-bound paired floor/entry native source geometries or exact evaluated shared profiles; both editors acknowledge this same plane,width,strip and tolerance contract before construction.',
  'Evaluated native Y/Z contact cross-sections across the entire centered terminal width; prove continuous flight/support and no source gaps/slivers, matched normals/tangent and clear corridor. Verify entry solids allY<=0, posts/caps external, capZ<=0.49; floor broadtop/maxheight/footprint unchanged.',
  'All4native standalone captures/exact atlases and all4native depth-tested joins. Independently compose actual candidate floor+entry atlases at unchanged roots with actual current consumer order, then inspect enlarged contact/post/underside crops.',
  'Actual consumer/filtering/phase evidence at logical and phone scales/light-gray-dark backgrounds, including fixed registered human traversal/landing context; no masks or presentation tweaks hide defects.',
  'Native geometry/visibility/material/resource closure and shared hashes. No camera-facing painted card or claim of candidacy/approval from this analytic review.'
 ],
 'baselineAuditClarification':analysis['honestBaselineCorrection'],
 'feasibilityConflicts':[],
 'remainingAction':'Coordinator incorporates the exact shared-boundary tolerance clarification and freezes matching briefs. Fresh editors may then construct. This review authorizes no source edit/promotion and issues no candidate/art approval.'
}
save('shared-interface-contract.json',record)
manifest={'scope':'New technical reconciliation only','originalReviewsRetainedUnchanged':retained,'newFiles':[item(p) for p in sorted(O.iterdir()) if p.is_file() and p.name!='evidence-manifest.json'],'technicalInputHashes':record['technicalReferences'],'candidateApprovalIssued':False}
save('evidence-manifest.json',manifest)
print(json.dumps({'result':record['status'],'contactWorldTolerance':1e-5,'functionalFloorRepairBounds':record['sharedInterface']['floorFunctionalRepairPermission']['maximumBounds'],'entryTechnicalProposalSHA256':sha(ENTRY/'source-contract-proposal.json'),'originalReviewHashesUnchanged':True,'artApprovalIssued':False,'output':str(O/'shared-interface-contract.json')},indent=2))
