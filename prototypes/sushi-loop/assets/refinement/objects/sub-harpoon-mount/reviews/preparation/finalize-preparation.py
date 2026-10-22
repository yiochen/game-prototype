from pathlib import Path
import json,hashlib,datetime,shutil
B=Path(__file__).resolve().parents[1];P=B/'preparation';R=P/'resources'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=json.loads((P/'native-source-audit.json').read_text());mounted=json.loads((P/'mounted-source-audit.json').read_text());consumer=json.loads((P/'consumer-evidence.json').read_text());tech=json.loads((P/'technical-reconciliation.json').read_text())
# Preserve dispatch byte authority alongside all data/code used.
dispatch=B.parents[2]/'preparation/sub-harpoon-mount/judge-dispatch.txt'
if dispatch.exists():shutil.copy2(dispatch,R/'contracts/judge-dispatch.txt')
# No transient diagnostic image differences are needed in the retained packet.
for p in P.glob('mounted-diff-*.png'):p.unlink()
contract=B/'source-contract-proposal.json';d=json.loads(contract.read_text());d['approval']='None. No saved source model edited or candidate built; only transient native replay/diagnostic scenes. No production change, Git, deployment, live Blender, device action or additional agents.';contract.write_text(json.dumps(d,indent=2)+'\n')
observations={
 'asset':'sub-harpoon-mount','stage':'preparation-complete-pending-root-freeze','verdict':'NO CANDIDATE VERDICT OR MAIN APPROVAL',
 'criteria':'proposedcriteria.json','sourceContract':'source-contract-proposal.json','initialIndependentObservations':'initial.json',
 'actuallyInspected':{
  'references':['inputs/original.png','inputs/target.png','inputs/family-concept.png','../../style/warm-soft-reference.png'],
  'nativeSourceVisual':['preparation/source-representative-all4.png','preparation/source-all48-phone-phases.png','preparation/source-replay-comparison.png'],
  'nativeMountedVisual':['preparation/mounted-source-representative-all4.png'],
  'browserScreenshotsDirect':['preparation/consumer-S-6-128.png','preparation/consumer-N-6-128.png','preparation/consumer-E-6-128.png','preparation/consumer-W-6-128.png','preparation/consumer-N-6-47.3.png','preparation/consumer-S-6-32.png','preparation/consumer-E-6-32.png'],
  'nativeRecords':['preparation/own-native-inventory.json','preparation/native-source-audit.json','preparation/own-resource-closure.json','preparation/independent-frozen-main-audit.json','preparation/mounted-source-audit.json','preparation/technical-reconciliation.json','preparation/consumer-evidence.json']},
 'sourceVisualFindings':['The source is a functional sparse slab/rail/barrel/muzzle assembly. Its S/N barrel reads, but E/W expose large uninterrupted red base faces and a thin pale rail. Target-inspired rounded side mass, a raised cradle and purposeful junction detail should improve the native construction in all facings.','Native source gesture is a subtle coherent barrel/muzzle +Y retraction, largest at source frame6. Source phase sheets retain the pale muzzle and dark barrel at logical and half-logical phone studies; the low-amplitude movement needs playback evaluation in the eventual candidate.','Mounted diagnostic shows the source launcher adjacent to the glass instead of covering its center. Its broad base is visibly foreign to the warmer crafted body, and actual triangles prove hull intersection. Rebuild the support; do not infer fit from the plausible front view.','Browser images from the exact saved current registration/raster functions show separate own sprite, legacy assembled upgraded Sub and eel at common scene scale. At32px cells the harpoon becomes a tiny red/cool-metal symbol; construction hierarchy matters more than screw detail. This is independent-sprite context, not native attachment proof.'],
 'measuredTechnicalFindings':{
  'sourceCaptures':len(source['frames']),'sourceIdle':4,'sourceActive':48,'mountedRepresentativeRenders':len(mounted['renders']),'mountedPhasesAudited':len(mounted['phases']),'browserCases':len(consumer['cases']),'browserErrors':consumer['errors'],
  'cameraMatrixMaxErrorAgainstSaved':tech['sourceCaptureComparison']['cameraComparison']['matrixMaxError'],'projectionMatrixMaxErrorAgainstSaved':tech['sourceCaptureComparison']['cameraComparison']['projectionMaxError'],'historicalAtlasExactRGBA':False,
  'sourceNeutralBounds':tech['sourceNeutralBounds'],'sourceFootSupportedFraction':tech['sourceContact'][0]['supportedFraction'],'all12OldBaseHullOverlap':all(any(y['own']=='harpoon_mount__base.001' and y['main']=='body__hull' for y in x['nativeTriangleOverlaps']) for x in mounted['phases']),
  'frozenMainTransformMaxError':max(x['frozenMainTransformMaxError'] for x in mounted['phases']),'frozenSeatLocal':tech['finiteSeatLocalRect']},
 'rootFreezeItems':['Approve proposed observable outcomes and source-contract reconciliation before the fresh editor.','Make rear fully supported foot/raised forward clearance explicit; old source base fails despite source function being retained.','Freeze or reconcile provisional derived neutral mouth[.31,-.444,.683], without overwriting legacy[.24,-.4,.37].','Keep native12-frame nonloop phase table including +.003 residual. Preserve canonical neutral resources unchanged for later main import at exact frozen transform.'],
 'limits':['No candidate has been constructed, judged or approved. Frozen main body and provisional other upgrades are technical context only.','Historical source atlas and native replay have identical camera/projection and alpha bounds but minor RGB/raster residuals; both bytes are retained.','Mounted active captures are source diagnostics under static neutral main; they do not authorize an active-main animation mapping.','The36 browser cases use exact snapshotted actual registration/raster functions in a standalone bench, not a claim that the full live React review page was visually approved.','Final candidate must add complete active native/consumer evidence, material/geometry resource identity and exact reopened candidate replay under frozen criteria.'],
 'reproduction':{
  'blenderExecutable':'/opt/homebrew/bin/blender','pythonExecutable':'/Users/yiouchen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3',
  'nativeSource':'blender -b preparation/resources/own-original-library.blend --python preparation/replay-own.py',
  'frozenMainSeatAudit':'blender -b preparation/resources/inputs/frozen-main-v1/project.blend --python preparation/audit-main.py',
  'mountedSource':'blender -b preparation/resources/inputs/frozen-main-v1/project.blend --python preparation/mounted-source.py',
  'publicationAndMeasurements':'python preparation/summarize-preparation.py',
  'browser':'Serve preparation/ at127.0.0.1:4186 with ordinary HTTP; saved consumer-bundle.js needs no changing publication data. Run preparation/capture-consumer.mjs. Browser screenshots use exact snapshotted layout/raster functions.',
  'closure':'preparation/resources/snapshot-manifest.json plus preparation/evidence-manifest.json and preparation/runtime-record.json'},
 'scope':'Only new files under this own experiment reviews/. No saved model edits, production, Git, live Blender, device work or additional agents.',
 'savedAtUTC':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(B/'preparation-review.json').write_text(json.dumps(observations,indent=2)+'\n')
files=[]
for f in B.rglob('*'):
 if f.is_file() and f.name!='evidence-manifest.json' and '__pycache__' not in str(f):files.append({'path':str(f.relative_to(B)),'sha256':sha(f),'bytes':f.stat().st_size})
manifest={'asset':'sub-harpoon-mount','stage':'preparation only','files':files,'bytes':sum(f['bytes'] for f in files),'fileCount':len(files),'under100MB':sum(f['bytes'] for f in files)<100000000,'qualification':'Hash-bound source/context/criteria/proposed contract and native/browser evidence. No candidate approval.'}
(P/'evidence-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({k:v for k,v in manifest.items() if k!='files'}))
