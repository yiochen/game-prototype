"""Read actual final artifacts and verify technical handoff closure.
This is a technical check, never an editor visual approval.
"""
import json,hashlib,subprocess
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent;OUT=OBJ/'candidates/round01'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
d=read(OBJ/'delivery.json');brief=read(OBJ/'brief.json');v=read(OBJ/d['validation']);catalog=read(OBJ/'inputs/catalog-object.json')
assert d['round']=='round01' and d['asset']=='chef-mateo'
project=OBJ/d['project'];projectsha=sha(project)
assert projectsha==v['candidateProjectSHA256']
assert projectsha==read(OUT/'supplemental-native-validation.json')['reopenedExactCandidateSHA256']
assert projectsha==read(OUT/'topology-cleanup.json')['candidateSHA256']
assert projectsha==read(OBJ/d['recipeManifest'])['candidateSHA256']
assert sha(HERE/'original-library.blend')==brief['source']['projectSHA256']==v['sourceProjectSHA256']
assert v['nativeChecksPass'] and not v['errors'] and v['pixelChecksPass'] and v['atlasCellsExact']
assert all(x['withinOriginalActionClearance'] for x in v['functionalActionClearances'].values())
assert len(v['renders'])==192 and len(d['rawFrames'])==192 and len(d['atlases'])==16
assert set(brief['capture']['previews'])<=set(d['previews'])
camera=read(OBJ/d['nativeRecords']['camera']);asset=read(OBJ/d['nativeRecords']['assetRecord'])
assert camera['captureScale']==2 and asset['scale']==2
assert camera['frame']==asset['frame']==[192,320] and camera['anchor']==asset['anchor']==[96,248]
assert abs(camera['calibration']['root'][0]-192)<.01 and abs(camera['calibration']['root'][1]-496)<.01
expected={(c['id'],direction,index) for c in catalog['clips'] for direction in c['directions'] for index in range(12)}
actual={(f['clip'],f['direction'],f['index']) for f in d['rawFrames']};assert actual==expected
frames={(f['clip'],f['direction'],f['index']):f for f in d['rawFrames']}
for a in d['atlases']:
 c=next(c for c in catalog['clips'] if c['id']==a['clip']);original=c['directions'][a['direction']]
 assert a['size']==original['atlasSize']==[2304,1280] and a['rects']==original['rects'] and (a['columns'],a['rows'])==(6,2)
 path=OBJ/a['path'];assert sha(path)==a['sha256'];atlas=Image.open(path);assert atlas.mode=='RGBA' and atlas.size==(2304,1280)
 for index,(x,y,w,h) in enumerate(a['rects']):
  f=frames[(a['clip'],a['direction'],index)];p=OBJ/f['path'];assert sha(p)==f['sha256'];im=Image.open(p);assert im.mode=='RGBA' and im.size==(384,640)
  assert atlas.crop((x,y,x+w,y+h)).tobytes()==im.tobytes()
for key,pb in read(OUT/'pixel-playback-validation.json')['playbacks'].items():
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=r_frame_rate,nb_frames,width,height','-of','json',str(OBJ/pb['path'])]))['streams'][0]
 assert probe['r_frame_rate']=='12/1' and probe['nb_frames']=='12' and (probe['width'],probe['height'])==(384,640)
paths=[project,OBJ/d['recipe'],OBJ/d['recipeManifest'],OBJ/d['validation'],*(OBJ/x for x in d['nativeRecords'].values()),*(OBJ/x for x in d['heroes'].values()),*(OBJ/x for x in d['previews'].values()),*(OBJ/x['path'] for x in d['atlases']),*(OBJ/x['path'] for x in d['rawFrames'])]
hashes={str(p.relative_to(OBJ)):sha(p) for p in paths}
result={'asset':'chef-mateo','round':'round01','technicalHandoffVerified':True,'visualVerdict':'Independent judge pending; no editor approval','projectSHA256':projectsha,'nativeFrames':192,'exactOriginalLayoutAtlases':16,'actual12fpsPlaybacks':16,'requiredPreviewsPresent':True,'nativeCameraAndScale2Verified':True,'hashes':hashes}
(OUT/'delivery-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='hashes'}))
