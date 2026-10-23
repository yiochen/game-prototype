"""Evidence-only round03 replay into NEW output; no native rerender is needed.

Default: verify reused96 raw frames, repack exact8 atlases temporarily, execute
the corrected36-case consumer and compare every decoded pixel to frozen images.
--native-art optionally invokes unchanged round02 saved-source native replay first.
"""
import sys,json,hashlib,argparse,subprocess,shutil
from pathlib import Path
sys.dont_write_bytecode=True
from PIL import Image
H=Path(__file__).resolve().parent;O=H.parent.parent
parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);parser.add_argument('--native-art',action='store_true');args=parser.parse_args();out=Path(args.output).resolve();assert not out.exists(),'Choose a NEW output directory';out.mkdir(parents=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();refs=json.loads((H/'resources/native-references.json').read_text());assert sha(O/refs['project']['path'])==refs['project']['sha256']
temporary=out/'repacked-native-inputs';temporary.mkdir()
if args.native_art:
 subprocess.run([sys.executable,str(H.parent/'round-02/reproduce.py'),'--output',str(out/'native')],check=True)
raw={}
for r in refs['rawFrames']:
 p=out/'native'/r['path'].split('candidates/round-02/',1)[1]if args.native_art else O/r['path']
 if not args.native_art:assert sha(p)==r['sha256']
 raw[r['clip'],r['direction'],r['index']]=p
proof=[]
for r in refs['atlases']:
 im=Image.new('RGBA',(7360,4224))
 for i in range(12):
  src=Image.open(raw[r['clip'],r['direction'],i]).convert('RGBA');assert src.size==(1472,1408);im.paste(src,(i%5*1472,i//5*1408))
 p=temporary/f'{r["clip"]}-{r["direction"]}.png';im.save(p,optimize=True);assert sha(p)==r['sha256'],'Repacked atlas differs from exact frozen native art';proof.append({'canonicalArtifact':r['path'],'canonicalSHA256':r['sha256'],'repackedSHA256':sha(p),'exactPNGBytes':True})
(out/'native-input-verification.json').write_text(json.dumps({'nativeSource':refs['project'],'nativeRerendered':args.native_art,'verifiedRawFrames':96,'repackedOriginalLayoutAtlases':8,'temporaryAtlasInputs':'Exact regenerated input bytes match canonical immutable round02 atlas hashes. Temporary duplicates removed after capture; canonical artifacts remain bound.','atlases':proof},indent=2)+'\n')
subprocess.run(['node',str(H/'capture_consumer.mjs'),'--output',str(out/'consumer'),'--atlas-dir',str(temporary)],check=True)
shutil.rmtree(temporary)
print(json.dumps({'output':str(out),'affectedConsumerCases':36,'nativeRerendered':args.native_art,'unchangedArtSHA256':refs['project']['sha256']}))
