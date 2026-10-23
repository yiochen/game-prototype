#!/usr/bin/env python3
"""Pack complete registered captures; never infer or fit a subject silhouette."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil

from PIL import Image
from extract_registered_sheet import _validate_guide, _border_max


def pack(captures, camera_path, output, kind='animation', columns=4, gutter=24, sheet_scale=1):
    captures=Path(captures).resolve();camera_path=Path(camera_path).resolve();output=Path(output).resolve()
    if output==captures or captures in output.parents:
        raise ValueError('Output must be separate from the original capture directory')
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError('Output must be new or empty; preserve earlier attempts')
    if type(columns)!=int or columns<1 or type(gutter)!=int or gutter<0 or type(sheet_scale)!=int or not 1<=sheet_scale<=4:
        raise ValueError('Use positive columns, nonnegative gutter and sheet scale 1..4')
    meta=json.loads(camera_path.read_text());frame=meta['frame'];anchor=meta['anchor']
    original_scale=meta['captureScale']
    if len(frame)!=2 or any(type(v)!=int or v<1 for v in frame) or not isinstance(original_scale,(int,float)) or not math.isfinite(original_scale) or original_scale<=0:
        raise ValueError('Camera metadata must declare the complete frame and positive captureScale')
    if meta.get('fps',12)!=12:raise ValueError('Capture at 12 fps; the packer does not retime motion')
    files=sorted(captures.glob('*.png'))
    if not files:raise ValueError('No PNG captures; use zero-padded filenames in playback order')
    w,h=[v*sheet_scale for v in frame];cols=min(columns,len(files));rows=math.ceil(len(files)/cols)
    size=[cols*w+(cols+1)*gutter,rows*h+(rows+1)*gutter]
    cells=[];images=[];records=[]
    for index,path in enumerate(files):
        with Image.open(path) as opened:
            opened.load();image=opened.convert('RGBA')
        if list(image.size)!=[v*original_scale for v in frame]:
            raise ValueError('Capture dimensions differ from fixed frame times captureScale; no fitting')
        alpha=image.getchannel('A')
        if not alpha.getbbox() or _border_max(alpha):
            raise ValueError('Capture is empty or art touches its boundary; clipping risk')
        image=image.resize((w,h),Image.Resampling.LANCZOS) if image.size!=(w,h) else image
        if _border_max(image.getchannel('A')):raise ValueError('Sampled art reaches panel boundary; choose more capture clearance')
        images.append(image)
        x=gutter+(index%cols)*(w+gutter);y=gutter+(index//cols)*(h+gutter)
        cell={'index':index,'rect':[x,y,x+w,y+h]}
        if kind=='animation':cell['durationMs']=1000/12
        if kind=='directions':cell['direction']=meta.get('directions',[])[index] if index<len(meta.get('directions',[])) else None
        cells.append(cell)
        records.append({'path':f'source-captures/{path.name}','sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    guide={'version':1,'kind':'rendered-3d-sheet','assetKind':kind,'size':size,'frame':frame,
        'anchor':anchor,'cellSize':meta['cellSize'],'captureScale':sheet_scale,'gutter':gutter,
        'columns':cols,'rows':rows,'cells':cells,'groundAnchorAlignment':'center',
        'projection':meta['projection'],'camera':meta.get('camera'),
        'occupiedCells':meta.get('occupiedCells',[[0,0]]),'elevationPx':meta.get('elevationPx',0),
        'sourceCaptures':records,'sourceCaptureScale':original_scale,
        'processing':'Uniform whole-frame LANCZOS only; no subject fitting or clipping'}
    _validate_guide(guide,kind)
    sheet=Image.new('RGBA',size)
    for image,cell in zip(images,cells):sheet.paste(image,tuple(cell['rect'][:2]))
    output.mkdir(parents=True,exist_ok=True);(output/'source-captures').mkdir()
    for path in files:shutil.copy2(path,output/'source-captures'/path.name)
    sheet.save(output/'sheet.png')
    (output/'guide.json').write_text(json.dumps(guide,indent=2)+'\n')
    return guide


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('captures',type=Path);parser.add_argument('camera',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--kind',choices=['animation','directions','object'],default='animation')
    parser.add_argument('--columns',type=int,default=4);parser.add_argument('--gutter',type=int,default=24)
    parser.add_argument('--sheet-scale',type=int,default=1)
    args=parser.parse_args();guide=pack(args.captures,args.camera,args.output,args.kind,args.columns,args.gutter,args.sheet_scale)
    print(json.dumps({'frames':len(guide['cells']),'size':guide['size'],'output':str(args.output.resolve())}))


if __name__=='__main__':main()
