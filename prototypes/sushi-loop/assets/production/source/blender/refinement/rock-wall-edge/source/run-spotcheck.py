from pathlib import Path
from PIL import Image
import json,subprocess,os,hashlib,numpy as np
B=Path(__file__).resolve().parents[1];O=B/'candidates/round-01';C=O/'consumer';out=O/'editor-spotcheck';out.mkdir(exist_ok=True)
for p in out.glob('*.png'):p.unlink()
m=json.loads((O/'metrics.json').read_text());data=json.loads((C/'retained-dom-evidence.json').read_text());chosen=[]
for d in 'NESW':chosen.append(next(e['case'] for e in data if e['mode']=='independent' and e['direction']==d and e['pitch']==32))
chosen=list(dict.fromkeys(chosen+[m['consumer']['worstWhole']['case']]))
env=dict(os.environ,CAPTURE_OUT=str(out),CASE_IDS=','.join(chosen));r=subprocess.run(['node',str(B/'source/consumer-check.mjs')],env=env,capture_output=True,text=True);(B/'source/consumer-spotcheck.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr
rows=[]
for stem in chosen:
 for mode in ['independent','connected']:
  name=stem+'-'+mode+'.png';a=np.asarray(Image.open(C/name).convert('RGBA'));b=np.asarray(Image.open(out/name).convert('RGBA'));rows.append({'case':stem,'mode':mode,'exactRGBA':bool(np.array_equal(a,b)),'maxChannelDelta':int(abs(a.astype(int)-b.astype(int)).max()),'savedSHA256':hashlib.sha256((C/name).read_bytes()).hexdigest(),'spotcheckSHA256':hashlib.sha256((out/name).read_bytes()).hexdigest()})
e=json.loads((out/'cases.json').read_text());result={'method':'Fresh current browser run in a separate output directory after final art/evidence capture, using exact same consumer script with CASE_IDS filtering; no saved candidate screenshots overwritten.','cases':chosen,'comparisons':rows,'sourceHashes':e['dependencies'],'dependenciesUnchanged':e['dependenciesUnchanged'],'errors':e['errors']};(out/'comparison.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
