#!/usr/bin/env python3
"""Read-only structural audit for a native100/70/50/40% projection study.

Reads the study manifest, real native camera records and PNG headers. It does not
render, invoke Blender, fit/crop/resize sprites, alter any source, or grade art.
Only --report is written; previous reports are retained by their content hash.
The ordinary character-art-camera reference is checked separately and is never
required to satisfy the square-floor environment projection.
"""
import argparse
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import re
import struct

try:
    from PIL import Image
except ImportError:
    Image=None

EXPECTED_RATIOS={'100':1.,'70':.7,'50':.5,'40':.4}
HEX_SHA256=re.compile(r'^[a-f0-9]{64}$')


def sha_file(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
    return digest.hexdigest()


def json_hash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def resolve(base,value):
    path=Path(value)
    return path if path.is_absolute() else Path(base)/path


def load_record(base,value):
    if isinstance(value,dict):return value,None
    path=resolve(base,value)
    return json.loads(path.read_text()),path


def png_size(path):
    with Path(path).open('rb') as stream:data=stream.read(24)
    if len(data)!=24 or data[:8]!=b'\x89PNG\r\n\x1a\n' or data[12:16]!=b'IHDR':raise ValueError('Not a PNG IHDR: '+str(path))
    return list(struct.unpack('>II',data[16:24]))


def matrix4(value):
    if not isinstance(value,list) or len(value)!=4 or any(not isinstance(row,list) or len(row)!=4 for row in value):raise ValueError('Expected a4×4 camera matrix')
    result=[[float(x) for x in row] for row in value]
    if not all(math.isfinite(x) for row in result for x in row):raise ValueError('Nonfinite camera matrix')
    return result


def inverse4(matrix):
    rows=[row[:]+[1. if i==j else 0. for j in range(4)] for i,row in enumerate(matrix)]
    for column in range(4):
        pivot=max(range(column,4),key=lambda i:abs(rows[i][column]))
        if abs(rows[pivot][column])<1e-12:raise ValueError('Singular camera world matrix')
        rows[column],rows[pivot]=rows[pivot],rows[column]
        denominator=rows[column][column];rows[column]=[x/denominator for x in rows[column]]
        for i in range(4):
            if i==column:continue
            factor=rows[i][column]
            rows[i]=[a-factor*b for a,b in zip(rows[i],rows[column])]
    return [row[4:] for row in rows]


def multiply(matrix,vector):
    return [sum(a*b for a,b in zip(row,vector)) for row in matrix]


def measured_projection(camera):
    world=matrix4(camera['camera']['worldMatrix']);projection=matrix4(camera['camera']['projectionMatrix'])
    view=inverse4(world);width,height=[float(v)*camera['captureScale'] for v in camera['frame']]
    def pixel(point):
        clip=multiply(projection,multiply(view,[*point,1.]))
        if abs(clip[3])<1e-12:raise ValueError('Camera point projects to infinity')
        return [(clip[0]/clip[3]+1)*width/2,(1-clip[1]/clip[3])*height/2]
    root=pixel([0.,0.,0.])
    vectors={name:[value-origin for value,origin in zip(pixel(point),root)]
             for name,point in {'unitX':[1.,0.,0.],'unitDepth':[0.,-1.,0.],'unitHeight':[0.,0.,1.]}.items()}
    back=[world[i][2] for i in range(3)]
    elevation=math.degrees(math.atan2(back[2],math.hypot(back[0],back[1])))
    return {'root':root,**vectors,'matrixElevationDegrees':elevation},pixel


def distance(a,b):
    return math.sqrt(sum((float(x)-float(y))**2 for x,y in zip(a,b)))


def camera_audit(camera,k,frame,root,source_scale,cell_size=128,tolerance=.1,reference=False):
    errors=[];measured,pixel=measured_projection(camera);scale=float(camera['captureScale'])
    expected_root=[float(v)*scale for v in root]
    if list(camera['frame'])!=list(frame):errors.append('Actual native camera frame differs from the common group frame')
    if list(camera['anchor'])!=list(root):errors.append('Actual native camera anchor differs from the common group root')
    if scale!=source_scale:errors.append('Native capture scale differs from image sourceScale; the study must retain native rendered pixels without resampling')
    if camera['camera'].get('type')!='orthographic':errors.append('Camera is not orthographic')
    if distance(measured['root'],expected_root)>tolerance:errors.append('Actual matrix-projected world origin misses the common declared ground root')
    for name in ['root','unitX','unitDepth','unitHeight']:
        declared=camera.get('calibration',{}).get(name)
        if not isinstance(declared,list) or len(declared)!=2 or distance(declared,measured[name])>tolerance:
            errors.append('Recorded calibration disagrees with actual camera matrices: '+name)
    if not reference:
        q=math.sqrt(1+k*k);alpha=math.degrees(math.atan2(1,k))
        expected={'unitX':[cell_size*scale,0.],'unitDepth':[0.,cell_size*scale],'unitHeight':[0.,-cell_size*scale*k]}
        for name,vector in expected.items():
            if distance(measured[name],vector)>tolerance:errors.append('Actual native projection fails '+name+' at heightScale='+str(k))
        aspect=camera['camera'].get('pixelAspect',[])
        if len(aspect)!=2 or not aspect[1] or abs(aspect[0]/aspect[1]-q)>1e-5:errors.append('Actual pixel aspect ratio is not sqrt(1+k²)')
        if abs(measured['matrixElevationDegrees']-alpha)>1e-3:errors.append('Actual camera orientation is not atan(1/k)')
        if abs(float(camera['camera'].get('elevationDegrees',float('nan')))-alpha)>1e-3:errors.append('Recorded elevation label differs from the intended ratio')
        floor=[pixel(point) for point in ([0.,0.,0.],[1.,0.,0.],[1.,-1.,0.],[0.,-1.,0.])]
        lengths=[distance(floor[i],floor[(i+1)%4])/scale for i in range(4)]
        if max(abs(length-cell_size) for length in lengths)>tolerance:errors.append('The actual ground-plane unit square changes floor pitch')
    else:
        alpha=35.;q=1.;lengths=None
        expected={'unitX':[cell_size*scale,0.],'unitDepth':[0.,cell_size*scale*math.sin(math.radians(alpha))],
                  'unitHeight':[0.,-cell_size*scale*math.cos(math.radians(alpha))]}
        for name,vector in expected.items():
            if distance(measured[name],vector)>tolerance:errors.append('Ordinary35° reference calibration differs: '+name)
        if abs(measured['matrixElevationDegrees']-alpha)>1e-3:errors.append('Reference is not the ordinary35° character art camera')
        aspect=camera['camera'].get('pixelAspect',[])
        if len(aspect)!=2 or not aspect[1] or abs(aspect[0]/aspect[1]-1)>1e-5:errors.append('Reference pixels are not square')
    return {'ok':not errors,'errors':errors,'measuredRaw':measured,
            'measuredLogical':{name:[v/scale for v in measured[name]] for name in ['root','unitX','unitDepth','unitHeight']},
            'intendedHeightScale':None if reference else k,'intendedElevationDegrees':alpha,
            'intendedPixelAspectXOverY':q,'floorEdgeLengthsLogical':lengths},pixel


def write_report(path,report):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        data=path.read_bytes();history=path.parent/'projection-study-audit-history'/hashlib.sha256(data).hexdigest()[:16]/path.name
        history.parent.mkdir(parents=True,exist_ok=True)
        if not history.exists():history.write_bytes(data)
    temporary=path.with_name(path.name+'.audit-'+str(os.getpid())+'.tmp')
    temporary.write_text(json.dumps(report,indent=2)+'\n');os.replace(temporary,path)


def normalized_camera(raw):
    camera=dict(raw)
    if 'frame' not in camera:camera['frame']=camera.get('frameSize')
    if 'captureScale' not in camera:camera['captureScale']=camera.get('sourceScale')
    if 'anchor' not in camera:camera['anchor']=camera.get('root')
    camera['camera']=dict(camera['camera'])
    if camera['camera'].get('type')=='ORTHO':camera['camera']['type']='orthographic'
    return camera


def receipt_for(raw):
    return raw.get('png') or raw.get('receipt') or raw.get('pngReceipt') or {}


def audit_image(group,ratio,image,camera_value,base,source_scale,cell_size,reference=False,require_alpha=False):
    row={'group':group['id'],'ratio':None if reference else ratio,'reference':reference,'ok':False,'errors':[]}
    try:
        raw,record_path=load_record(base,camera_value);camera=normalized_camera(raw)
        if raw.get('groupId') not in [None,group['id']]:row['errors'].append('Camera record identifies another group')
        expected_k=EXPECTED_RATIOS.get(ratio)
        if not reference and raw.get('heightRatio',raw.get('heightScale'))!=expected_k:row['errors'].append('Native capture receipt does not identify the intended height ratio')
        if camera['camera'].get('sensorFit') not in [None,'HORIZONTAL']:row['errors'].append('Actual camera sensor fit changed from the fixed horizontal world pitch')
        if camera['camera'].get('orthoScale') is not None and abs(float(camera['camera']['orthoScale'])-group['frameSize'][0]/cell_size)>1e-5:row['errors'].append('Actual camera ortho scale was fitted to this sample')
        result,pixel=camera_audit(camera,expected_k,group['frameSize'],group['root'],source_scale,cell_size,reference=reference)
        row.update(camera=result,cameraRecord=str(record_path) if record_path else 'inline',
                   cameraRecordSHA256=sha_file(record_path) if record_path else json_hash(raw))
        row['errors'].extend(result['errors'])
        source=group.get('source',{})
        for key in ('geometryHash','placementsHash','materialsHash'):
            expected=source.get(key);actual=raw.get(key)
            row[key]=actual
            if not isinstance(expected,str) or not HEX_SHA256.fullmatch(expected):row['errors'].append('Common group '+key+' is not a retained SHA256 identity')
            if actual!=expected:row['errors'].append('Actual per-capture '+key+' differs from frozen group source')
        if raw.get('placements') is not None:
            row['actualPlacements']=raw['placements']
            if source.get('placements') is not None and raw['placements']!=source['placements']:row['errors'].append('Per-capture world placements differ from frozen group placements')
        path=resolve(base,image);dimensions=png_size(path);digest=sha_file(path)
        expected_dimensions=[round(float(value)*source_scale) for value in group['frameSize']]
        row.update(image=str(path),imageSHA256=digest,imageDimensions=dimensions)
        if dimensions!=expected_dimensions:row['errors'].append('PNG dimensions differ from the fixed native frame×sourceScale')
        if Image is not None:
            with Image.open(path) as opened:
                opened.load();alpha=opened.convert('RGBA').getchannel('A');bbox=alpha.getbbox()
            row['alphaBoundsRaw']=list(bbox) if bbox else None
            row['alphaBoundsLogical']=[value/source_scale for value in bbox] if bbox else None
            row['alphaBorderTouched']=bool(bbox and (bbox[0]==0 or bbox[1]==0 or bbox[2]==dimensions[0] or bbox[3]==dimensions[1]))
            row['minimumTransparentMarginLogical']=min(bbox[0],bbox[1],dimensions[0]-bbox[2],dimensions[1]-bbox[3])/source_scale if bbox else None
            if not bbox:row['errors'].append('Rendered comparison image has empty alpha')
            if row['alphaBorderTouched']:row['errors'].append('Actual rendered alpha touches the native frame edge; possible capture cropping')
        elif require_alpha:row['errors'].append('Pillow is required for requested actual alpha-edge inspection; use the bundled Python runtime')
        receipt=receipt_for(raw)
        if receipt.get('sha256')!=digest:row['errors'].append('Published PNG does not match the native rendered PNG receipt byte-for-byte')
        if list(receipt.get('dimensions',[]))!=dimensions:row['errors'].append('Native PNG receipt dimensions disagree with actual IHDR')
        row['rawPixelsRetained']=not any('PNG' in error or 'resampling' in error for error in row['errors'])
    except Exception as exc:row['errors'].append(type(exc).__name__+': '+str(exc))
    row['ok']=not row['errors']
    return row


def audit_projection_study(study_path,asset_root=None,expected_groups=None,require_alpha=False):
    study_path=Path(study_path);base=Path(asset_root) if asset_root else study_path.parent
    study=json.loads(study_path.read_text())
    report={'version':1,'mode':'read-only-native-projection-study-audit','ok':False,
            'createdAtUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'manifest':str(study_path),'manifestSHA256':sha_file(study_path),
            'geometryApproval':'not-established; structural comparison only',
            'alphaInspectionRequested':require_alpha,'alphaInspectionAvailable':Image is not None,
            'groupsChecked':0,'ratioImagesChecked':0,'referenceImagesChecked':0,'errors':[],'samples':[],'groups':[]}
    try:
        cell_size=study.get('cellSize');source_scale=study.get('sourceScale')
        if cell_size!=128:report['errors'].append({'case':'study','message':'Study floor pitch must remain128 logical pixels per cell'})
        if source_scale not in [2,4]:report['errors'].append({'case':'study','message':'Study sourceScale must declare the actual native2× or4× render'})
        ratios={str(row['id']):float(row.get('heightScale',row.get('heightRatio'))) for row in study.get('ratios',[])}
        if ratios!=EXPECTED_RATIOS:report['errors'].append({'case':'study','message':'Study must contain exactly100/70/50/40 height-ratio choices'})
        project=study.get('nativeProject');project_hash=study.get('nativeProjectSHA256')
        if project:
            native_project=resolve(base,project)
            if not isinstance(project_hash,str) or not HEX_SHA256.fullmatch(project_hash):report['errors'].append({'case':'study','message':'Isolated native study project lacks a SHA256 guard'})
            elif not native_project.is_file() or sha_file(native_project)!=project_hash:report['errors'].append({'case':'study','message':'Isolated native study project does not match its frozen capture identity'})
            report['nativeProjectSHA256']=project_hash
        before=study.get('productionPresentationHashBefore');after=study.get('productionPresentationHashAfter')
        if before is not None or after is not None:
            report['productionPresentationRestored']=isinstance(before,str) and HEX_SHA256.fullmatch(before) is not None and before==after
            if not report['productionPresentationRestored']:report['errors'].append({'case':'study','message':'Original production presentation changed during study isolation'})
        groups=study.get('groups',[]);ids=[group['id'] for group in groups]
        if not groups or len(ids)!=len(set(ids)):report['errors'].append({'case':'study','message':'Groups are empty or repeat stable IDs'})
        if expected_groups is not None and len(groups)!=expected_groups:report['errors'].append({'case':'study','message':'Expected '+str(expected_groups)+' fixed-pose comparison groups'})
        for group in groups:
            summary={'id':group['id'],'ok':False,'errors':[],'ratioImages':0,'references':0}
            source=group.get('source',{})
            material_values=source.get('materials')
            if material_values is None:summary['errors'].append('Actual retained native material snapshot is missing')
            else:
                summary['materialSnapshotSHA256']=json_hash(material_values)
                if summary['materialSnapshotSHA256']!=source.get('materialsHash'):summary['errors'].append('Actual retained native material snapshot does not hash to materialsHash')
            transforms=source.get('transforms')
            if transforms is not None:
                summary['worldTransformSnapshotSHA256']=json_hash(transforms)
                if summary['worldTransformSnapshotSHA256']!=source.get('placementsHash'):summary['errors'].append('Actual retained world-transform snapshot does not hash to placementsHash')
            bindings=source.get('meshBindings')
            if bindings is not None:
                summary['meshBindingsChecked']=len(bindings)
                if not bindings:summary['errors'].append('No original-to-clone native mesh bindings are retained')
                for binding in bindings:
                    original=binding.get('sourceMeshHash');clone=binding.get('cloneMeshHash')
                    if not isinstance(original,str) or not HEX_SHA256.fullmatch(original) or original!=clone:
                        summary['errors'].append('Native raw mesh changed during clone: '+str(binding.get('sourceObject')))
            images=group.get('images',{});cameras=group.get('source',{}).get('cameras',{})
            if set(images)!=set(EXPECTED_RATIOS):summary['errors'].append('Missing/extra ratio image; no candidate may be silently substituted')
            if not all(ratio in cameras for ratio in EXPECTED_RATIOS):summary['errors'].append('Every ratio needs its actual native camera record')
            for ratio in EXPECTED_RATIOS:
                if ratio not in images or ratio not in cameras:continue
                row=audit_image(group,ratio,images[ratio],cameras[ratio],base,source_scale,cell_size,require_alpha=require_alpha)
                if project_hash is not None:
                    raw,_=load_record(base,cameras[ratio])
                    if raw.get('nativeProjectSHA256')!=project_hash:row['errors'].append('Capture does not identify the frozen isolated native project');row['ok']=False
                report['samples'].append(row);summary['ratioImages']+=1;report['ratioImagesChecked']+=1
                summary['errors'].extend(ratio+': '+error for error in row['errors'])
            reference=group.get('reference')
            if reference:
                camera_value=reference.get('camera') or group.get('sourceReferenceCamera') or group.get('source',{}).get('referenceCamera')
                if not reference.get('image') or not camera_value:summary['errors'].append('Character reference needs its separate real image/camera record')
                else:
                    row=audit_image(group,None,reference['image'],camera_value,base,source_scale,cell_size,reference=True,require_alpha=require_alpha)
                    if project_hash is not None:
                        raw,_=load_record(base,camera_value)
                        if raw.get('nativeProjectSHA256')!=project_hash:row['errors'].append('Reference does not identify the same frozen isolated native project');row['ok']=False
                    report['samples'].append(row);summary['references']+=1;report['referenceImagesChecked']+=1
                    summary['errors'].extend('ordinary35 reference: '+error for error in row['errors'])
            # Each ratio must share the same real native origin and both ground
            # basis vectors; all four can change only their height projection.
            rows=[row for row in report['samples'] if row['group']==group['id'] and not row['reference'] and 'camera' in row]
            if rows:
                baseline=rows[0]['camera']['measuredLogical']
                for row in rows[1:]:
                    for key in ['root','unitX','unitDepth']:
                        if distance(row['camera']['measuredLogical'][key],baseline[key])>.025:
                            summary['errors'].append(row['ratio']+': '+key+' drifts across ratios')
            summary['ok']=not summary['errors'] and summary['ratioImages']==len(EXPECTED_RATIOS)
            report['groups'].append(summary);report['groupsChecked']+=1
            report['errors'].extend({'case':group['id'],'message':error} for error in summary['errors'])
    except Exception as exc:report['errors'].append({'case':'study','message':type(exc).__name__+': '+str(exc)})
    report['ok']=not report['errors'] and report['groupsChecked']>0 and report['ratioImagesChecked']==report['groupsChecked']*4
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('study',type=Path)
    parser.add_argument('--asset-root',type=Path,help='Base for native camera/PNG relative paths; defaults to the study manifest folder')
    parser.add_argument('--expect-groups',type=int,help='Expected complete comparison-group count, e.g7 for the initial study')
    parser.add_argument('--require-alpha',action='store_true',help='Require Pillow inspection of actual nonempty alpha and transparent frame borders')
    parser.add_argument('--report',type=Path,default=Path('/private/tmp/sushi33-projection-study-audit.json'))
    args=parser.parse_args();report=audit_projection_study(args.study,args.asset_root,args.expect_groups,args.require_alpha)
    report['report']=str(args.report);write_report(args.report,report)
    print(json.dumps({key:report[key] for key in ['ok','groupsChecked','ratioImagesChecked','referenceImagesChecked','errors','report']},indent=2))
    return 0 if report['ok'] else 1


if __name__=='__main__':raise SystemExit(main())
