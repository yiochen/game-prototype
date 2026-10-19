"""Compare new native crate/belt captures with the exact approved material study.
Only the audit JSON is written. Region masks originate from native polygons;
fixed canvases/roots are compared directly without fitting or resizing pixels.
"""
import argparse,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[4]
sys.path.insert(0,str(HERE.parent/'environment-lighting-study'))
from measure_pair import measure,rgba,erode
import numpy as np

def main(args):
 study=REPO/'prototypes/sushi-loop/assets/faceted-material-refinement';report={'issues':[],'subjects':{}}
 for aid,sid,clip in [('crate-wood','crate-wood','idle'),('belt-straight-e','belt-straight','running')]:
  entry={}
  for direction in ['N','E','S','W']:
   reference=study/'sprites'/sid/('faceted-tuned-'+direction+'.png');candidate=args.raw/aid/(clip+'-'+direction)/'000.png';mask=study/'validation'/(sid+'-'+direction+'.png')
   if not candidate.exists():report['issues'].append(str(candidate)+': missing');continue
   item=measure(reference,candidate,mask,{'top':[255,0,0],'side':[0,0,255]});a,b=rgba(reference),rgba(candidate);common=erode((a[:,:,3]>=250)&(b[:,:,3]>=250));difference=np.abs(a[:,:,:3].astype(int)-b[:,:,:3].astype(int))[common]
   item['commonOpaqueRGBMeanByteDifference']=float(difference.mean());item['commonOpaqueRGB95PercentileByteDifference']=float(np.quantile(difference,.95))
   # EEVEE32 production vs64study differ at sampled surface/edge pixels. Broad
   # opaque regions should preserve the user's selected color/brightness.
   if item['commonOpaqueRGBMeanByteDifference']>3:report['issues'].append(aid+'/'+direction+': approved-study mean opaque RGB differs by >3/255')
   entry[direction]=item
  report['subjects'][aid]=entry
 report['passed']=not report['issues'];args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':report['passed'],'issues':report['issues'],'output':str(args.output)}))
 if not report['passed']:sys.exit(1)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);p.add_argument('--output',type=Path,required=True);main(p.parse_args())
