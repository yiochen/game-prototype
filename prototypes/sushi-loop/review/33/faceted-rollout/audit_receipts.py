"""Verify every native receipt belongs to the frozen project/helpers/metadata.
Reads complete capture batches only; writes one audit JSON, never source files.
"""
import argparse,hashlib,json,sys
from pathlib import Path

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def main(args):
 records=args.export/'source';raw=args.export/'raw-frames';workers=args.export/'capture-workers';report={'projectSHA256':sha(args.project),'helpers':{},'workers':{},'assets':{},'issues':[],'frames':0};expected=set();cache={};check=lambda ok,msg:report['issues'].append(msg) if not ok else None
 scripts={'runtime':'capture_runtime.py','nativeActions':'native_actions.py','worker':'capture_worker.py','catalogStyle':'catalog_style.py','catalogFaceted':'catalog_faceted.py','conceptFooting':'concept_decoration_geometry.py'}
 report['helpers']={name:sha(args.helpers/file) for name,file in scripts.items()}
 for folder in sorted(records.glob('*/asset.json')):
  aid=folder.parent.name;asset=json.loads(folder.read_text());rigpath=folder.with_name('rig.json');rig=json.loads(rigpath.read_text());hashes={'assetJson':sha(folder),'rigJson':sha(rigpath),'assetId':aid};frames=0;versions=set()
  for clip,c in rig['clips'].items():
   for direction in asset.get('directions',['N','E','S','W']):
    for index in range(c['frames']):
     path=raw/aid/(clip+'-'+direction)/(str(index).zfill(3)+'.png');expected.add(path);receipt=path.with_suffix('.capture.json')
     if not receipt.exists():check(False,str(receipt)+': missing');continue
     r=json.loads(receipt.read_text());worker=r['worker'];versions.add(r['nativeVersion'])
     if worker not in cache:
      status=json.loads((workers/(worker+'.status.json')).read_text());source=status['nativeSource'];report['workers'][worker]={'source':source,'state':status['state'],'rawRoot':status['rawRoot']};cache[worker]=source
      check(source['blend']==report['projectSHA256'],worker+': stale project identity')
      for key,value in report['helpers'].items():check(source.get(key)==value,worker+': stale helper '+key)
      check(source['samples']==32 and source['sourceScale']=='authored' and source['blenderVersion']=='5.2.2 LTS',worker+': wrong native sampling/runtime')
     check(r['nativeVersion']==digest({**cache[worker],**hashes}),str(path)+': stale/mixed nativeVersion')
     check(r['state']=='complete' and r['index']==index and r['assetId']==aid and r['clip']==clip and r['direction']==direction and r['fps']==12,str(path)+': receipt identity/timing mismatch');frames+=1
  check(len(versions)==1,aid+': multiple source versions');report['assets'][aid]={'frames':frames,'nativeVersions':sorted(versions)};report['frames']+=frames
 extras=set(raw.rglob('*.png'))-expected;report['extraPNGs']=[str(p) for p in sorted(extras)];check(not extras,'Unexpected PNGs in frozen native batch');check(len(report['assets'])==104 and report['frames']==9390,'Object/frame count differs104/9390');report['passed']=not report['issues'];args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':report['passed'],'frames':report['frames'],'issues':report['issues'],'output':str(args.output)}))
 if not report['passed']:sys.exit(1)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--export',type=Path,required=True);p.add_argument('--project',type=Path,required=True);p.add_argument('--helpers',type=Path,required=True);p.add_argument('--output',type=Path,required=True);main(p.parse_args())
