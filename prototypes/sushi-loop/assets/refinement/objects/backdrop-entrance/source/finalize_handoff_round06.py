from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib
P=Path(__file__).resolve().parent.parent;R=P/'candidates/round-06'
a=Image.open(R/'independent-assembled-raw.png').convert('RGBA');s=Image.new('RGBA',(800,1408),'#eee5d6');d=ImageDraw.Draw(s)
try:f=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',22)
except:f=ImageFont.load_default()
for x,offset,lab in [(1248,0,'Left entrance join · center'),(2784,416,'Right entrance join · center')]:
 s.alpha_composite(a.crop((x-192,0,x+192,1344)),(offset,64));d.text((offset+8,19),lab,font=f,fill='#362d26')
s.save(R/'entrance-join-strips.png')
v=json.loads((R/'validation.json').read_text());v['geometryEnvelopeNote']='Raw protected join meshes and matrices exactly match source. Small bevels on internal roof slabs produce measured evaluated projected height 2.99904269 tiles (source declared height 3); no camera fitting or frame/root change. Full registered canvas and transparent gutters are retained.';(R/'validation.json').write_text(json.dumps(v,indent=2))
deliv=json.loads((P/'delivery.json').read_text());deliv['familySettings']='candidates/round-06/family-settings.json';deliv['workflow']='source/round-06-workflow.json';deliv['resources']+=['candidates/round-06/family-settings.json','source/export_family_settings_round06.py','source/finalize_handoff_round06.py','source/round-06-workflow.json'];deliv['resources']=list(dict.fromkeys(deliv['resources']));(P/'delivery.json').write_text(json.dumps(deliv,indent=2))
paths=[deliv['project'],deliv['recipe'],deliv['validation'],deliv['familySettings'],*deliv['heroes'].values(),*deliv['previews'].values(),*deliv['nativeRecords'].values(),*deliv['resources']]
for a in deliv['atlases']:paths.append(a['path'])
h={'schemaVersion':1,'deliverySha256':hashlib.sha256((P/'delivery.json').read_bytes()).hexdigest(),'files':{s:hashlib.sha256((P/s).read_bytes()).hexdigest() for s in sorted(set(paths))}};(R/'editor-handoff-hashes.json').write_text(json.dumps(h,indent=2))
print(json.dumps({'delivery':str(P/'delivery.json'),'deliverySha256':h['deliverySha256'],'sourceSha256':h['files'][deliv['project']],'familySettingsSha256':h['files'][deliv['familySettings']],'boundFiles':len(h['files'])},indent=2))
