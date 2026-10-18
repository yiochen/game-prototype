#!/usr/bin/env python3
"""Read-only issue-33 native capture preflight; no PNG or source modifications.

Checks only the planned stable objects and each native asset.json clip/direction's
exact numeric frames. Partial renders and unrelated files are ignored. Every
existing completed numeric PNG receives dimensions/alpha/border checks, even
while its asset is pending; uniqueness is checked only for complete clip/facing
groups. Runtime-2x whole-frame RGBA/visible-pixel diagnostics never fit art. Prior reports and failed attempts stay
retained. A structural result is not a visual/contact/loop-quality approval.
"""
import argparse
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import sys
from PIL import Image

DIRECTIONS=['N','E','S','W']
NUMERIC_PNG=re.compile(r'^\d+\.png$')
VERSION=1


def sha_bytes(value):return hashlib.sha256(value).hexdigest()


def sha_file(path):
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
    return digest.hexdigest()


def normalized_clip(value):return value.replace('_','-')


def allowed_empty_indices(clip,recipe,count):
    """Only explicit metadata or the requested appear-start/fade-end exceptions."""
    result=set()
    for value in recipe.get('allowEmptyFrames',[]):
        if isinstance(value,int) and 0<=value<count:result.add(value)
        elif value=='first':result.add(0)
        elif value=='last':result.add(count-1)
    if normalized_clip(clip)=='appear':result.add(0)
    if normalized_clip(clip)=='fade':result.add(count-1)
    return result


def border_touched(bbox,size):
    return bool(bbox and (bbox[0]==0 or bbox[1]==0 or bbox[2]==size[0] or bbox[3]==size[1]))


def inspect_frame(path,expected_size,runtime_size,old_cache=None):
    stat=path.stat()
    key={'size':stat.st_size,'mtimeNs':stat.st_mtime_ns,'nativeSize':list(expected_size),'runtimeSize':list(runtime_size),'version':VERSION}
    if old_cache and old_cache.get('fileIdentity')==key:
        return dict(old_cache),True
    with Image.open(path) as opened:
        opened.load();rgba=opened.convert('RGBA')
    native_size=rgba.size;native_bbox=rgba.getchannel('A').getbbox()
    sampled=rgba.resize(runtime_size,Image.Resampling.LANCZOS) if rgba.size!=runtime_size else rgba.copy()
    runtime_bbox=sampled.getchannel('A').getbbox()
    result={'path':str(path),'fileIdentity':key,'sourceSHA256':sha_file(path),
            'nativeSize':list(native_size),'runtimeSize':list(sampled.size),
            'nativeAlphaBounds':list(native_bbox) if native_bbox else None,
            'runtimeAlphaBounds':list(runtime_bbox) if runtime_bbox else None,
            'nativeBorderAlpha':border_touched(native_bbox,native_size),
            'runtimeBorderAlpha':border_touched(runtime_bbox,sampled.size),
            'runtimeRGBASHA256':sha_bytes(sampled.tobytes()),
            'runtimeVisibleSHA256':sha_bytes(sampled.convert('RGBa').tobytes())}
    after=path.stat()
    result['changedDuringRead']=(stat.st_size,stat.st_mtime_ns)!=(after.st_size,after.st_mtime_ns)
    return result,False


def write_report(path,report):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        digest=sha_file(path)
        archive=path.parent/'preflight-report-history'/(path.stem+'-'+digest[:16]+'.json')
        archive.parent.mkdir(parents=True,exist_ok=True)
        if not archive.exists():shutil.copy2(path,archive)
    temporary=path.with_name(path.name+'.preflight-tmp')
    temporary.write_text(json.dumps(report,indent=2)+'\n');os.replace(temporary,path)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native',type=Path,default=Path('/private/tmp/sushi33-production/export'))
    parser.add_argument('--plan',type=Path,default=Path('/private/tmp/sushi33-production/coverage-plan.json'))
    parser.add_argument('--report',type=Path,default=Path('/private/tmp/sushi33-production/native-capture-preflight.json'))
    parser.add_argument('--ids',nargs='+',help='Optional selected stable IDs; default all117 planned objects')
    parser.add_argument('--belt-raw-root',type=Path,help='Alternate raw root containing belt-ID/clip-direction/000.png')
    parser.add_argument('--raw-roots',type=Path,help='JSON map of stable IDs to alternate raw roots; paths relative to JSON file are accepted')
    parser.add_argument('--no-cache',action='store_true')
    parser.add_argument('--strict',action='store_true',help='Exit nonzero for any existing-frame failure; missing captures alone are not failures')
    args=parser.parse_args();native=args.native.resolve();plan=json.loads(args.plan.read_text())
    planned={item['id']:item for item in plan['objects']}
    selected=args.ids or list(planned)
    if set(selected)-set(planned):raise ValueError('Unknown planned IDs: '+', '.join(sorted(set(selected)-set(planned))))
    raw_roots={}
    if args.belt_raw_root:
        raw_roots.update({aid:args.belt_raw_root.resolve() for aid in selected if aid.startswith('belt-')})
    if args.raw_roots:
        configured=json.loads(args.raw_roots.read_text())
        if 'objects' in configured:configured=configured['objects']
        for aid,value in configured.items():
            raw=Path(value['path'] if isinstance(value,dict) else value)
            raw_roots[aid]=(args.raw_roots.parent/raw).resolve() if not raw.is_absolute() else raw.resolve()
    previous={}
    if not args.no_cache and args.report.exists():
        try:previous=json.loads(args.report.read_text()).get('frameCache',{})
        except (ValueError,OSError):previous={}
    report={'version':VERSION,'mode':'read-only-native-capture-preflight','startedAtUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'nativeRoot':str(native),'inspectPendingAssetPNGs':True,'rawRootOverrides':{aid:str(path) for aid,path in raw_roots.items()},'planSHA256':sha_file(args.plan),'runtimeSourceScale':2,'minimumUniqueAnimatedDrawings':6,
            'visualApproval':'not-established-by-structural-preflight','objects':[],'frameCache':{},'failedIDs':[],'pendingIDs':[]}
    inspected_frames=0;cached_frames=0
    for aid in selected:
        result={'id':aid,'status':'pending','captureComplete':False,'rawRoot':str(raw_roots.get(aid,native/'raw-frames')),'clips':[],'issues':[],'missingFrames':[],'unexpectedNumericFrames':[]}
        report['objects'].append(result);record=native/'source'/aid/'asset.json'
        if not record.exists():
            result['missingMetadata']=str(record);report['pendingIDs'].append(aid);continue
        try:
            raw_record=record.read_bytes();info=json.loads(raw_record)
            frame=info['frame'];scale=info.get('scale',4)
            if len(frame)!=2 or not all(isinstance(v,(int,float)) and math.isfinite(v) and v>0 for v in frame):raise ValueError('invalid frame')
            native_size=tuple(int(v*scale) for v in frame);runtime_size=tuple(int(v*2) for v in frame)
            result['assetRecordSHA256']=sha_bytes(raw_record);result['expectedNativeSize']=list(native_size)
            if not info.get('clips'):raise ValueError('no native clips')
        except Exception as exc:
            result['status']='failed';result['issues'].append({'code':'invalid-native-metadata','path':str(record),'message':str(exc)});report['failedIDs'].append(aid);continue
        ready_frames=[]
        for cid,recipe in info['clips'].items():
            count=recipe.get('frames');clip={'id':cid,'normalizedId':normalized_clip(cid),'directions':{}}
            result['clips'].append(clip)
            if not isinstance(count,int) or count<1:
                result['issues'].append({'code':'invalid-native-frame-count','clip':cid,'value':count});continue
            if recipe.get('fps',12)!=12:result['issues'].append({'code':'invalid-fps','clip':cid,'value':recipe.get('fps')})
            for direction in DIRECTIONS:
                folder=raw_roots.get(aid,native/'raw-frames')/aid/(cid+'-'+direction)
                expected=[f'{index:03d}.png' for index in range(count)]
                available={path.name for path in folder.glob('*.png') if NUMERIC_PNG.fullmatch(path.name) and not path.name.endswith('.partial.png')}
                missing=[str(folder/name) for name in expected if name not in available]
                extra=[str(folder/name) for name in sorted(available-set(expected))]
                result['missingFrames'].extend(missing);result['unexpectedNumericFrames'].extend(extra)
                clip['directions'][direction]={'expectedFrames':count,'presentExpectedFrames':count-len(missing),'missingFrames':len(missing),'unexpectedNumericFrames':extra,'frameSetComplete':not missing,'exactFrameSetComplete':not missing and not extra}
                existing=[(int(Path(name).stem),folder/name,name in set(expected)) for name in sorted(available)]
                if existing:ready_frames.append((cid,recipe,direction,existing,clip['directions'][direction]))
        if result['unexpectedNumericFrames']:
            result['issues'].append({'code':'unexpected-numeric-frame-names','paths':result['unexpectedNumericFrames']})
        result['captureComplete']=not result['missingFrames']
        # Existing numeric PNGs are immutable completed frames. Inspect them now,
        # but reserve motion uniqueness for groups with every expected frame.
        allow_border=bool(info.get('allowOpaqueBorder')) or aid.startswith('floor-')
        for cid,recipe,direction,frames,clip_result in ready_frames:
            rgba_hashes=[];visible_hashes=[];allowed_empty=allowed_empty_indices(cid,recipe,recipe['frames'])
            clip_result['allowedEmptyFrames']=sorted(allowed_empty);clip_result['frames']=[]
            for index,path,is_expected in frames:
                key=str(path)
                try:
                    observation,cached=inspect_frame(path,native_size,runtime_size,previous.get(key))
                    report['frameCache'][key]=observation
                    inspected_frames+=1;cached_frames+=int(cached)
                    clip_result['frames'].append({'index':index,'path':key,'sourceSHA256':observation['sourceSHA256'],'runtimeRGBASHA256':observation['runtimeRGBASHA256'],'runtimeVisibleSHA256':observation['runtimeVisibleSHA256']})
                    if is_expected:
                        rgba_hashes.append(observation['runtimeRGBASHA256']);visible_hashes.append(observation['runtimeVisibleSHA256'])
                    if observation.get('changedDuringRead'):
                        result['issues'].append({'code':'frame-changed-during-read','clip':cid,'direction':direction,'frame':index,'path':key})
                    if observation['nativeSize']!=list(native_size):
                        result['issues'].append({'code':'native-dimensions-mismatch','clip':cid,'direction':direction,'frame':index,'path':key,'actual':observation['nativeSize'],'expected':list(native_size)})
                    empty=not observation['nativeAlphaBounds'] or not observation['runtimeAlphaBounds']
                    if empty and index not in allowed_empty:
                        result['issues'].append({'code':'unexpected-empty-frame','clip':cid,'direction':direction,'frame':index,'path':key})
                    if not allow_border and (observation['nativeBorderAlpha'] or observation['runtimeBorderAlpha']):
                        result['issues'].append({'code':'alpha-touches-panel-boundary','clip':cid,'direction':direction,'frame':index,'path':key,'nativeBorder':observation['nativeBorderAlpha'],'runtimeBorder':observation['runtimeBorderAlpha'],'nativeAlphaBounds':observation['nativeAlphaBounds']})
                except Exception as exc:
                    result['issues'].append({'code':'unreadable-complete-png','clip':cid,'direction':direction,'frame':index,'path':key,'message':str(exc)})
            unique_rgba=len(set(rgba_hashes));unique_visible=len(set(visible_hashes))
            clip_result.update(uniqueRuntimeRGBAFrames=unique_rgba,uniqueVisibleRuntimeFrames=unique_visible,uniquenessEvaluated=bool(clip_result['frameSetComplete']))
            static=bool(recipe.get('static'))
            if clip_result['frameSetComplete'] and not static and min(unique_rgba,unique_visible)<6:
                result['issues'].append({'code':'insufficient-unique-runtime-drawings','clip':cid,'direction':direction,'paths':[str(path) for index,path,is_expected in frames if is_expected],'uniqueRGBA':unique_rgba,'uniqueVisible':unique_visible,'required':6})
        result['status']='failed' if result['issues'] else 'complete-structural-pass' if result['captureComplete'] else 'pending'
        if result['issues']:report['failedIDs'].append(aid)
        elif not result['captureComplete']:report['pendingIDs'].append(aid)
        print(json.dumps({'id':aid,'status':result['status'],'issues':len(result['issues'])}),flush=True)
    report['finishedAtUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    report['summary']={'plannedIDs':len(selected),'completeIDs':sum(o.get('captureComplete',False) for o in report['objects']),
                       'structuralPassIDs':sum(o['status']=='complete-structural-pass' for o in report['objects']),
                       'failedIDs':len(report['failedIDs']),'partialFailedIDs':[o['id'] for o in report['objects'] if o['status']=='failed' and not o.get('captureComplete')],'pendingIDs':len(report['pendingIDs']),
                       'inspectedFrames':inspected_frames,'cachedFrames':cached_frames,
                       'issueCount':sum(len(o['issues']) for o in report['objects'])}
    write_report(args.report,report)
    print(json.dumps({'summary':report['summary'],'failedIDs':report['failedIDs'],'report':str(args.report)},indent=2))
    return int(bool(args.strict and report['failedIDs']))


if __name__=='__main__':sys.exit(main())
