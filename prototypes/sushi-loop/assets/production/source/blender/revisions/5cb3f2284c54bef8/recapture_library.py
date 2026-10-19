#!/usr/bin/env python3
"""Render selected saved native actions using the repository's editable project.
Example: python recapture_library.py --ids chef-lena --out /tmp/sushi-art-recapture
No rebuilding, pose fitting, sprite editing or source project writes occur.
"""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys

BASE=Path(__file__).resolve().parent

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ids',nargs='+',required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--project',type=Path,default=BASE/'sushi-loop-world-library.blend')
    parser.add_argument('--blender',default=shutil.which('blender') or '/Applications/Blender.app/Contents/MacOS/Blender')
    parser.add_argument('--clips',nargs='+')
    parser.add_argument('--directions',nargs='+',default=['N','E','S','W'])
    parser.add_argument('--frames')
    parser.add_argument('--samples',type=int,default=32)
    parser.add_argument('--dry-run',action='store_true')
    args=parser.parse_args()
    out=args.out.expanduser().resolve();out.mkdir(parents=True,exist_ok=True)
    records=BASE.parent/'native-records'
    source=out/'source'
    if source.is_symlink():
        if source.resolve()!=records.resolve():raise ValueError('Output source points to another native record set')
    elif source.exists():raise ValueError('Use a fresh output directory, or an earlier recapture directory')
    else:source.symlink_to(records,target_is_directory=True)
    for aid in [aid for argument in args.ids for aid in argument.split(',')]:
        if not (records/aid/'rig.json').is_file():raise ValueError('Not a saved native object: '+aid)
    command=[args.blender,'--background',str(args.project.resolve()),'--python',str(BASE/'capture_worker.py'),'--',
             '--ids',*args.ids,'--export-root',str(out),'--worker','repository-recapture','--mcp-idle-confirmed',
             '--directions',*args.directions,'--samples',str(args.samples)]
    if args.clips:command+=['--clips',*args.clips]
    if args.frames:command+=['--frames',args.frames]
    if args.dry_run:command+=['--dry-run']
    return subprocess.call(command)

if __name__=='__main__':sys.exit(main())
