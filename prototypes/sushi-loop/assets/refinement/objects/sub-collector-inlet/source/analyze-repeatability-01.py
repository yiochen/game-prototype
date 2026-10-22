from pathlib import Path
from PIL import Image
import numpy as np,json,hashlib
H=Path(__file__).resolve().parent;E=H.parent;O=E/'candidates/round-01'
def pixels(a,b,size=None):
 ia=Image.open(E/a).convert('RGBA');ib=Image.open(E/b).convert('RGBA')
 if size:ia=ia.resize(size,Image.Resampling.BOX);ib=ib.resize(size,Image.Resampling.BOX)
 aa=np.asarray(ia,dtype=np.int16);bb=np.asarray(ib,dtype=np.int16);delta=np.abs(aa-bb);mask=np.any(delta!=0,axis=2);ys,xs=np.where(mask)
 coords=[{'x':int(x),'y':int(y),'rgbaA':aa[y,x].tolist(),'rgbaB':bb[y,x].tolist()} for y,x in zip(ys,xs)]
 return {'size':list(ia.size),'changedPixels':int(mask.sum()),'maxPerChannel':delta.max(axis=(0,1)).tolist(),'sumPerChannel':delta.sum(axis=(0,1)).tolist(),'changedAlphaPixels':int((delta[:,:,3]!=0).sum()),'pixelLocations':coords}
native=json.loads((O/'native-audit.json').read_text());controls=json.loads((O/'repeatability/native-controls.json').read_text());result=[]
for di in 'NESW':
 rows={r['label']:r for r in controls['records'] if r['direction']==di};orig={r['nativeFrame']:r for r in native['records'] if r['clip']=='active' and r['direction']==di}
 pairs=[('same-source-frame1-repeat','1a','1b'),('same-source-frame13-repeat','13a','13b'),('fresh-frame1-vs13','1a','13a')]
 tests=[]
 for label,a,b in pairs:
  ra,rb=rows[a],rows[b];tests.append({'comparison':label,'paths':[ra['path'],rb['path']],'fullGeometryNormalsUVMaterialTransformsExact':ra['fullNativeResourceStateSHA256']==rb['fullNativeResourceStateSHA256'],'nativeRGBA':pixels(ra['path'],rb['path']),'publishedRGBA':pixels(ra['path'],rb['path'],(384,704)),'logicalRGBA':pixels(ra['path'],rb['path'],(192,352)),'phone473CellBOXDiagnosticOnly':pixels(ra['path'],rb['path'],(71,130))})
 tests.append({'comparison':'original-runtime-frame1-vs-closing13','paths':[orig[1]['path'],orig[13]['path']],'evaluatedPartMatricesBoundsExact':orig[1]['parts']==orig[13]['parts'],'nativeRGBA':pixels(orig[1]['path'],orig[13]['path']),'publishedRGBA':pixels(orig[1]['path'],orig[13]['path'],(384,704)),'logicalRGBA':pixels(orig[1]['path'],orig[13]['path'],(192,352)),'phone473CellBOXDiagnosticOnly':pixels(orig[1]['path'],orig[13]['path'],(71,130))})
 result.append({'direction':di,'comparisons':tests})
report={'purpose':'Empirical same-source/same-pose renderer repeatability versus genuine key13 closure. Raw captures retained; no pixel repair or quality reduction.','renderer':'Saved48sample EEVEE/filter_size.5/dither1, identical source/settings','nativeClosingPose':'Full native geometry/normals/UV/material/local transform state hashes at actual sourceframe1 and13 are compared; closing key excluded from runtime atlas.','intendedSizeQualification':'Logical and phone BOX values are diagnostic reductions of the complete raw frame. Actual runtime consumer performs native nearest composition followed by ordinary browser whole-canvas filtering and plays12 discrete phases/sec. Small numeric differences require independent judge assessment; editor does not declare aesthetic/temporal approval.','records':result,'approval':False}
p=O/'repeatability/closure-analysis.json';p.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps([{'direction':r['direction'],'counts':[(x['comparison'],x['nativeRGBA']['changedPixels'],x['nativeRGBA']['maxPerChannel'],x['logicalRGBA']['changedPixels']) for x in r['comparisons']]} for r in result],indent=2))
