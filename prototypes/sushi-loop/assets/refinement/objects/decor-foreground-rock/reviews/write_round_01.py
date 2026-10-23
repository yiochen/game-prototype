from pathlib import Path
import json,hashlib
from PIL import Image,ImageChops
P=Path(__file__).resolve().parents[1];C=P/'candidates/round-01';Q=C/'packet.json';q=json.loads(Q.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
for group in ['files','candidateRenders','previews']:
 for name,r in q[group].items():
  f=(C/r['path']).resolve();checks.append({'group':group,'name':name,'path':str(f),'sha256':sha(f),'matchesPacket':sha(f)==r['sha256']})
hashcheck={'packetSHA256':sha(Q),'referenceCount':len(checks),'uniqueFileCount':len(set(x['path']for x in checks)),'allMatch':all(x['matchesPacket']for x in checks),'checks':checks}
(P/'reviews/round-01-hash-verification.json').write_text(json.dumps(hashcheck,indent=2)+'\n')
a=json.loads((P/'reviews/round-01-native-summary.json').read_text());c=json.loads((P/'reviews/round-01-compositing-check.json').read_text());a['effectiveRenderUseCompositing']=c['renderUseCompositing'];a['compositorNodes']=c['compositorNodes'];a['deprecatedSceneUseNodesIsNotEffectiveCompositingFlag']=True;(P/'reviews/round-01-native-summary.json').write_text(json.dumps(a,indent=2)+'\n')
# Every declared preview was inspected at its exact bound path; phone and phone-context intentionally alias the same image.
inspected=sorted(set(str((C/r['path']).resolve())for group in ['candidateRenders','previews']for r in q[group].values()))
additional=[str(C/f'raw/static-{d}/000.png')for d in 'NESW']+[str(C/'consumer/desktop-four-facings.png'),str(P/'inputs/original.png'),str(P/'inputs/target.png'),str(P/'reviews/initial-use-size-sheet.png')]+[str(P/f'reviews/round-01-native-replay/static-{d}.png')for d in 'NESW']
review={
 'schemaVersion':1,'asset':'decor-foreground-rock','round':1,'verdict':'revise','candidatePacketSHA256':sha(Q),'candidateProjectSHA256':sha(P/'source/round-01.blend'),'frozenBriefSHA256':sha(P/'brief.json'),'fixedTargetSHA256':sha(P/'inputs/target.png'),
 'inspectedFiles':inspected,'additionalInspectedFiles':additional,'previewCoverage':{name:str((C/r['path']).resolve())for name,r in q['previews'].items()},
 'scores':{'shapeVolume':5,'color':7,'lightingHighlights':6,'materialDetail':5,'artifactFreeReadability':8},
 'scoreInterpretation':'Comparative1-10 observations against the original source and fixed target; no numeric pass threshold. Geometry is more varied and lower planes are clearer than the original, but the broad weighty rock identity remains unresolved.',
 'observations':[
  'The new native object materially improves the source blank slab problem: N and W now show multiple intentional turning faces and secondary masses, and lower planes stay visibly blue instead of falling to near-black. All four directions are coherent views of the same rebuilt3D object.',
  'The cobalt family is preserved, with clean bright cyan upward planes and richer mid-blue lower areas. The asset stays readable in the light/gray/dark background sheets, logical192x352 frames and smaller browser placements.',
  'The dominant shape language is still a cut crystal cluster. E has a prominent arrowhead crown with a pointed apex and large triangular front facets; W has a long inverted-point lower face on the main mass; N ends in a central shield-like lower point. Several small stones also taper strongly toward their visible bases. These persist at logical size and in the repeated phone preview.',
  'Those sharp converging triangular faces and narrow-looking bearing bases reduce the heavy grounded-bank impression established in the fixed target, despite every mesh technically touching Z0. The issue is the visible natural-stone construction, not a failed root or physical-contact measurement.',
  'The narrow zigzag cyan crests around the N/S lower supports read like collars around the main stone. They reinforce the geometric-crystal grouping rather than the target broad worn boulder shoulders. This is part of the same unresolved mass/facet hierarchy, not a demand for the old four-piece layout.',
  'Surface treatment is clean and somewhat softened at edges, with no glare or dark dead spots. It is simpler and flatter than the target painted/worn edge treatment; extra microtexture or exact target cracks are not required. Material face breakup should support the revised broad stone forms rather than preserve the current giant triangular reading.',
  'The inspected full underwater browser fixture shows candidate E/W/S placements beside the banks, eel and submarine. Actors, bubbles and direction/warning silhouettes remain distinct on phone, desktop and landscape. The fixture inserts three representative placements in a browser-only module response; the production scene and this object production static-S image remain original.',
  'No visible alpha halo, isolated speckle, clipping, cast ground shadow, open mesh end, black patch or broken face was found in the four raw frames or declared previews. Native source and technical evidence are complete for this candidate.'
 ],
 'blockers':[
  {'rank':1,'category':'shapeVolume / material identity','location':'E main crown; N central lower silhouette; W main lower face and support stones. Visible in raw static-E/N/W, logical-four-view-sheet, backgrounds and repeated phone preview.','effect':'Pointed crowns, large converging triangular facets and shield-like tapered bottoms make the foreground scenery read as a crystal/ore cluster rather than the frozen compact, broad, weighty, lightly worn cobalt rock bank. This is a material identity/style gap at intended size.','desiredVisibleOutcome':'Give the crown and support stones broad, blunt, irregular stone planes and convincing visual bearing at their bases. Keep an intentional major-to-minor mass hierarchy and clear stone creases around every facing, while preventing arrowheads, inverted points and narrow bright collars from dominating the read. Preserve the improved all-view face breakup, blue palette, grounded root and measured envelope. Native redesign and changed part counts remain allowed; no exact source or generated-target contour is required.'}
 ],
 'remainingDifferences':[
  'Different stone count and arrangement from both the source and single-view target are acceptable within the frozen role/envelope contract.',
  'Less fine painted surface texture and fewer warm cream edge accents than the generated target are not separate blockers; the required improvement is the broad natural-stone mass and facet hierarchy.',
  'Target canvas scale/registration drift, exterior cyan fringe and one-sided warm rim are correctly omitted and are not requirements.',
  'The fixed target provides no exact reverse views; N/E/W are judged for coherent quality and identity, not invented pixel matching.'
 ],
 'technicalEvidence':{
  'allRequiredEvidenceAvailable':True,'technicalContractPass':True,
  'packetClosure':{'checkedReferences':hashcheck['referenceCount'],'uniqueFiles':hashcheck['uniqueFileCount'],'allHashesMatch':hashcheck['allMatch'],'record':'reviews/round-01-hash-verification.json'},
  'independentNativeInspection':{'projectOpenedDirectly':str(P/'source/round-01.blend'),'projectSHA256':a['projectSHA256'],'sourceBytesUnchanged':a['sourceFileUnchanged'],'script':'reviews/round-01-independent-audit.py','audit':'reviews/round-01-native-audit.json','summary':'reviews/round-01-native-summary.json','recipeImported':False},
  'cameraRegistration':{'type':'ORTHO','elevationDegrees':a['cameraElevationDegrees'],'orthoScale':1.5,'sensorFit':'HORIZONTAL','pixelAspect':a['pixelAspect'],'publicationResolution':a['resolution'],'nativeCaptureScale':2,'reduction':'none; native source-scale2 frames are direct publication pixels','logicalFrame':[192,352],'logicalRoot':[96,256],'calibration':a['calibration'],'intrinsicRootIdentity':a['savedRootMatrix']==[[1.,0.,0.,0.],[0.,1.,0.,0.],[0.,0.,1.,0.],[0.,0.,0.,1.]],'facingPhasesDegrees':{'N':180,'E':90,'S':0,'W':-90}},
  'functionalGeometry':{'rootLocalBounds':a['bounds'],'allSevenMeshesHaveMinimumZ0':all(abs(m['evaluatedBounds']['min'][2])<1e-7 for m in a['meshEvidence']),'allMeshesClosedManifold':all(m['nonManifoldEdges']==0 and m['boundaryEdges']==0 and m['looseVertices']==0 for m in a['meshEvidence']),'noOldPartCountLock':True,'sockets':{},'ports':{},'modularJoinsRequired':False,'footprint':[1,1]},
  'staticState':{'framesPerFacing':1,'frameCurrent':a['frameCurrent'],'fps':a['fps'],'fpsBase':a['fpsBase'],'actions':a['actions'],'armatures':a['armatures'],'shapeKeys':a['shapeKeys']},
  'nativeOutputAndClosure':{'images':a['images'],'externalLibraries':a['externalLibraries'],'noRasterCards':True,'effectiveCompositing':c['renderUseCompositing'],'compositorNodes':c['compositorNodes'],'noGroundReceiver':True,'sameCameraLightMaterialsEveryFacing':a['sameAppearanceAllFacings'],'lighting':'Centered warm overhead plus eight equal radial cool fills. Surface color varies with normalZ and worldZ, with no horizontal coordinate or camera-vector shading input. No preferred horizontal light direction.','independentReplayRGBA':a['independentReplay'],'allFourFreshRendersExactlyMatchSealedRawPixels':all(v['equalRGBA']for v in a['independentReplay'].values()),'rawFrameAtlasIdentity':'Every publication frame, raw capture and atlas hash is equal per facing; no post-render repair or reduction.'},
  'consumer':{'evidence':'candidates/round-01/consumer/evidence.json','sourceChecks':'reviews/round-01-consumer-source-check.json','allDeclaredPreviewImagesInspected':True,'candidatePayloadHashesVerified':True,'layouts':['desktop1440x1000','phone390x844','landscape844x390'],'representativeUnderwaterFixture':'Browser-only inserted candidate E/W/S placements use the actual shared world renderer and exact candidate payloads. This is preview evidence, not production integration.','productionStaticSStillOriginal':True,'applicationSourceHashesStillMatchBoundEvidence':True,'godotIntegrationEvidence':'Not part of this sealed candidate review.'},
  'limits':['This review binds the supplied candidate bytes and browser preview fixture only.','Closed/manifold topology and ground bounds do not certify the desired visual bearing; that remains the explicit visual blocker.','No source/model/brief/candidate/production changes were made; all independent outputs were written under reviews/.']
 }
}
assert review['candidatePacketSHA256']=='f96ac159ece32d65c4e14c3cc8e2daf31b681ab558e90acbbe749e16cef59535'
assert review['frozenBriefSHA256']=='dc28411f7d85a9c577001b4fcd096ea9ed2174606175617c834587d6b4b90a3d'
assert hashcheck['allMatch']
(P/'reviews/round-01.json').write_text(json.dumps(review,indent=2)+'\n')
print(json.dumps({'review':str(P/'reviews/round-01.json'),'verdict':review['verdict'],'packetSHA256':review['candidatePacketSHA256'],'blockers':len(review['blockers']),'technicalContractPass':True,'declaredPreviewEntries':len(q['previews']),'uniqueCandidateRenderAndPreviewPaths':len(inspected)},indent=2))
