"""Replay approved round03 native geometry, then publish the declared whole canvas at scale2.
This evidence-only recipe does not edit any approved source or image. It requires a new output directory.
Run with the bundled Pillow Python: python round-04-recipe.py --output /absolute/new-directory --blender blender
"""
from pathlib import Path
import argparse,subprocess,json,hashlib
from PIL import Image
BASE=Path(__file__).resolve().parent.parent

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--blender',default='blender');args=ap.parse_args()
 out=args.output.resolve()
 if out.exists() and any(out.iterdir()):raise RuntimeError('Replay requires an empty output directory')
 native=out/'native';published=out/'published';native.mkdir(parents=True);published.mkdir()
 # The actual .blend and its portable native replay recipe are the immutable round03 bytes.
 subprocess.run([args.blender,'-b',str(BASE/'source/round-03.blend'),'--python',str(BASE/'source/replay-round-03.py'),'--',str(native)],check=True)
 proof={}
 for d in 'NESW':
  src=native/f'native-static-{d}.png';im=Image.open(src).convert('RGBA');assert im.size==(768,1280)
  # Uniform complete-canvas sampling: preserve registration; no fitting/recolor/edge repair.
  pub=im.resize((384,640),Image.Resampling.LANCZOS);dst=published/f'static-{d}.png';pub.save(dst)
  approved=BASE/f'candidates/round-03/static-{d}.png'
  proof[d]={'nativeResolution':[768,1280],'publishedResolution':[384,640],'exactApprovedPublishedRGBA':pub.tobytes()==Image.open(approved).convert('RGBA').tobytes(),'exactApprovedPublishedPNG':hashlib.sha256(dst.read_bytes()).hexdigest()==hashlib.sha256(approved.read_bytes()).hexdigest()}
 (out/'replay.json').write_text(json.dumps({'nativeProject':'source/round-03.blend','nativeReplay':'source/replay-round-03.py','nativeCaptureScale':4,'publishedCaptureScale':2,'method':'Pillow LANCZOS uniform whole-canvas 0.5 scale','views':proof},indent=2)+'\n')
if __name__=='__main__':main()
