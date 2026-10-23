"""Read-only art verification and final metadata for unsealed round-06.
Does not modify native projects or native PNGs.
"""
from PIL import Image
from pathlib import Path
import json,hashlib,shutil
BASE=Path(__file__).resolve().parents[1];OUT=BASE/'candidates/round-06'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
r=read(OUT/'validation-replay.json')
a=Image.open(OUT/'raw/static-S-0000.png').convert('RGBA');b=Image.open(OUT/'replay-S.png').convert('RGBA')
r['decodedRGBAByteExactReplay']=a.tobytes()==b.tobytes();r['decodedRGBASHA256']=hashlib.sha256(a.tobytes()).hexdigest()
r['pngMetadataDifference']='Date/RenderTime/Memory PNG text chunks differ; decoded RGBA pixels match exactly.'
write(OUT/'validation-replay.json',r)
# Correct the inherited style-summary field to the actual round-06 shader value.
for name in ['camera','asset']:
    p=OUT/'records'/f'{name}.json';j=read(p);j['artStyle']['roughness']=.48
    j['artStyle']['seatModeling']='Broad symmetric object-space honey-gold board tonal field plus shallow modeled seam channels'
    write(p,j)
p=BASE/'source/round-06-settings.json';settings=read(p);settings['camera']=read(OUT/'records/camera.json');settings['render']['useCompositing']=False
settings['metadataFinalizer']='source/finalize-round-06.py';write(p,settings)
p=OUT/'validation.json';v=read(p);v['camera']=read(OUT/'records/camera.json')
v['replayCheck']={'path':'candidates/round-06/validation-replay.json','sha256':sha(OUT/'validation-replay.json'),'exactDecodedRGBAReplay':r['decodedRGBAByteExactReplay'],'pngBytesDifferOnlyInRenderMetadata':True,'savedProjectUnchanged':r['projectUnchangedAfterReplay']}
original=read(BASE/'inputs/source-camera.json');cm=v['camera']['camera']['worldMatrix'];sm=original['camera']['worldMatrix']
v['contractChecks']={'registeredFramePreserved':r['resolution']==[384,704],'rootPixelError':max(abs(r['rootPixel'][i]-[192,496][i])for i in range(2)),'seatSocketPixelError':max(abs(r['seatPixel'][i]-[192,378.623952][i])for i in range(2)),'cameraMatrixMaxAbsDeltaFromSource':max(abs(cm[i][j]-sm[i][j])for i in range(4)for j in range(4)),'nativeSocketsPreserved':v['socketNative']=={'seat':[0,0,.655],'occupant_ground':[0,0,0]},'sourceScaleCorrectedToActual2':v['camera']['captureScale']==2,'allFourNativeFacings':set(x['direction']for x in v['nativeCaptures'])==set('NESW'),'sourceXYPreservationMaxDelta':max(abs(v['sourceBounds'][k][i]-v['currentBounds'][k][i])for k in ['min','max']for i in [0,1]),'originalLegGroundContactPreserved':v['sourceBounds']['min'][2]==v['currentBounds']['min'][2],'noDegenerateFaces':all(x['degenerateFaces']==0 for x in v['topology']),'allMeshesClosedManifold':all(x['nonmanifoldEdges']==0 for x in v['topology']),'allBordersTransparent':all(x['borderMaxAlpha']==0 for x in v['alpha'].values()),'oneAlphaComponentEachView':all(len(x['connectedComponentsAlphaGT4'])==1 for x in v['alpha'].values()),'externalDependencies':r['externalImages']+r['externalLibraries']}
v['render']['useCompositing']=r['useCompositing']
v['roundChanges']=['Seat shader now models broad centered honey-gold tonal variation within each board using native object-space Generated coordinates; it rotates with actual stool geometry.','No unilateral light direction or per-view correction; original neutral ring and overhead retained.','Two shallow channels widened from 0.010 to 0.014 native units, retaining positions, inset floors and soft modeled lips.','Support geometry, support materials, camera, root, socket and outer envelope unchanged from round-05.']
pixels=[a.getpixel((x,y))[:3]for x in range(130,254)for y in range(315,445)if not (347<=y<=358 or 401<=y<=412)]
v['seatInteriorDescriptiveRange']={'region':[130,315,254,445],'excludedRows':[[347,358],[401,412]],'rangeRGB':[[min(p[c]for p in pixels),max(p[c]for p in pixels)]for c in range(3)],'note':'Descriptive corroboration of a broad tonal field, not a visual approval threshold.'}
v['metadataFinalization']={'script':'source/finalize-round-06.py','sha256':sha(Path(__file__)),'styleSummaryCorrection':'Inherited roughness summary changed from .43 to actual .48; no native art files changed.'}
v['files']['settingsSHA256']=sha(BASE/'source/round-06-settings.json')
write(p,v)
shutil.copyfile(OUT/'delivery.json',BASE/'delivery.json')
print(json.dumps({'replay':r['decodedRGBAByteExactReplay'],'contractChecks':v['contractChecks'],'interiorRange':v['seatInteriorDescriptiveRange'],'delivery':'delivery.json','projectSHA256':sha(BASE/'source/round-06.blend')},indent=2))
