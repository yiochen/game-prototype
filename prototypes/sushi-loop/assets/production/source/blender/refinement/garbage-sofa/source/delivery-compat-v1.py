"""Versioned measured-direction adapter only. No native source, art or original metadata mutation."""
from pathlib import Path
import json,hashlib
from PIL import Image
P=Path(__file__).resolve().parent;OBJ=P.parent;OUT=OBJ/'candidates/round-02/delivery-compat-v1'
ORIGINAL_DELIVERY=OBJ/'delivery-round02.json';ORIGINAL_VALIDATION=OBJ/'candidates/round-02/validation.json';LEDGER=OBJ/'candidates/round-02/candidate-phases.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rel(p):return str(Path(p).relative_to(OBJ))
def read(p):return json.loads(Path(p).read_text())
def write(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n')
old={rel(p):sha(p) for p in [ORIGINAL_DELIVERY,ORIGINAL_VALIDATION,LEDGER,OBJ/'delivery.json',P/'round-02.blend',P/'recipe-round02.py']}
d=read(ORIGINAL_DELIVERY);v=read(ORIGINAL_VALIDATION);ledger=read(LEDGER)
assert len(ledger)==100 and isinstance(v['nativeCaptures'],list) and len(v['nativeCaptures'])==100
# Copy actual measured fields verbatim, never derive angles or matrices from labels.
renders=[]
for e in ledger:
 for key in ['clip','direction','frame','rootRotationZ','rootMatrix']:assert key in e
 renders.append({k:e[k] for k in ['clip','direction','frame','rootRotationZ','rootMatrix']}|{'rawFrame':e['path']})
manifest={'asset':'garbage-sofa','schema':'measured-native-renders-v1','renders':renders,'sourceLedger':rel(LEDGER),'sourceLedgerSHA256':sha(LEDGER),'sourceValidation':rel(ORIGINAL_VALIDATION),'sourceValidationSHA256':sha(ORIGINAL_VALIDATION),'translation':'All rootRotationZ and rootMatrix values are verbatim from measured native ledger records; no reconstruction or expected-angle synthesis.'}
MANIFEST=OUT/'measured-phase-manifest.json';write(MANIFEST,manifest)
# Re-read every complete RGBA atlas cell and raw, with all transparent RGB included.
atlasmap={(a['clip'],a['direction']):a for a in d['atlases']};records=[]
for r in d['rawFrames']:
 a=atlasmap[(r['clip'],r['direction'])];ap=OBJ/a['path'];rp=OBJ/r['path'];raw=Image.open(rp);atlas=Image.open(ap);assert raw.mode==atlas.mode=='RGBA';assert list(raw.size)==[896,1152];assert list(atlas.size)==a['size'];assert sha(rp)==r['sha256'] and sha(ap)==a['sha256'];x,y,w,h=a['rects'][r['index']];cell=atlas.crop((x,y,x+w,y+h));assert cell.size==raw.size;exact=cell.tobytes()==raw.tobytes();assert exact
 records.append({'clip':r['clip'],'direction':r['direction'],'index':r['index'],'raw':r['path'],'rawSHA256':sha(rp),'atlas':a['path'],'atlasSHA256':sha(ap),'rect':[x,y,w,h],'rawMode':raw.mode,'atlasMode':atlas.mode,'wholeRGBACellExact':exact})
assert len(records)==100 and len(atlasmap)==12
RGBA=OUT/'rgba-atlas-audit.json';write(RGBA,{'asset':'garbage-sofa','originalDelivery':rel(ORIGINAL_DELIVERY),'originalDeliverySHA256':sha(ORIGINAL_DELIVERY),'cells':records,'cellCount':100,'atlasCount':12,'allCompleteRGBACellsExact':all(r['wholeRGBACellExact'] for r in records),'policy':'Read-only verification of all channels, complete896x1152 native regions and zero-based original index order. No conversion, resampling, crop fitting, regrade, save or image mutation.'})
ADAPTER=OUT/'validation-adapter.json';adapter={**v,'nativeValidation':rel(MANIFEST),'compatibilityAdapter':{'version':1,'scope':'Metadata pointer only; source/art/native measurements unchanged','originalValidation':rel(ORIGINAL_VALIDATION),'originalValidationSHA256':sha(ORIGINAL_VALIDATION),'originalDelivery':rel(ORIGINAL_DELIVERY),'originalDeliverySHA256':sha(ORIGINAL_DELIVERY),'measuredManifest':rel(MANIFEST),'measuredManifestSHA256':sha(MANIFEST),'originalMeasuredLedger':rel(LEDGER),'originalMeasuredLedgerSHA256':sha(LEDGER),'rgbaAudit':rel(RGBA),'rgbaAuditSHA256':sha(RGBA)}};write(ADAPTER,adapter)
new={**d,'validation':rel(ADAPTER),'deliveryAdapterVersion':'round02-compat-v1','originalDelivery':rel(ORIGINAL_DELIVERY),'originalDeliverySHA256':sha(ORIGINAL_DELIVERY),'resources':dict(d['resources'])}
new['resources'].update({'compat-v1:original-delivery':rel(ORIGINAL_DELIVERY),'compat-v1:original-delivery-alias':'delivery.json','compat-v1:original-validation':rel(ORIGINAL_VALIDATION),'compat-v1:original-ledger':rel(LEDGER),'compat-v1:measured-manifest':rel(MANIFEST),'compat-v1:rgba-audit':rel(RGBA),'compat-v1:validation-adapter':rel(ADAPTER),'compat-v1:recipe':rel(Path(__file__).resolve())})
NEW_DELIVERY=OBJ/'delivery-round02-compat-v1.json';write(NEW_DELIVERY,new)
assert old=={p:sha(OBJ/p) for p in old}
print(json.dumps({'originalsUnchanged':True,'rgbaCellsExact':len(records),'measuredRecords':len(renders),'newDelivery':{'path':rel(NEW_DELIVERY),'sha256':sha(NEW_DELIVERY)},'newValidation':{'path':rel(ADAPTER),'sha256':sha(ADAPTER)},'measuredManifest':{'path':rel(MANIFEST),'sha256':sha(MANIFEST)},'rgbaAudit':{'path':rel(RGBA),'sha256':sha(RGBA)}},indent=2))
