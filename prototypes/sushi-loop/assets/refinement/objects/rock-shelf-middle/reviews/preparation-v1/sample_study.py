import pathlib,json,sys
sys.dont_write_bytecode=True
sys.path.insert(0,str(pathlib.Path(__file__).parent/'resources/python-library'))
from PIL import Image
BASE=pathlib.Path(__file__).parent;E=BASE/'evidence'/'study-filter05-box'
for d in 'NESW':
 out=E/'packs'/d;out.mkdir(parents=True,exist_ok=True)
 for src,dst,size in [(E/f'source-{d}-4x.png',out/'sheet.png',(384,704)),(E/f'joined-{d}-4x.png',E/f'joined-{d}-2x.png',(896,1216))]:
  Image.open(src).convert('RGBA').resize(size,Image.Resampling.BOX).save(dst)
 (out/'guide.json').write_text(json.dumps({'purpose':'Original-source-only native sampling study, no candidate art','frame':[192,352],'root':[96,248],'sourceScale':2,'sourceCaptureScale':4,'processing':'Uniform whole-canvas BOX4x->2x after native filter_size0.5; no alpha repair, fitting, warp, overlap or per-view tweak'},indent=2))
html=(BASE/'consumer.html').read_text().replace('original source only','original source only · filter0.5 BOX study').replace('./evidence/packs/','./evidence/study-filter05-box/packs/').replace('./evidence/joined-','./evidence/study-filter05-box/joined-');(BASE/'consumer-study.html').write_text(html)
js=(BASE/'capture_consumer.cjs').read_text().replace('/consumer.html','/consumer-study.html').replace("'consumer-", "'study-consumer-").replace('`consumer-nativecanvas-','`study-consumer-nativecanvas-').replace('evidence/consumer-results.json','evidence/study-consumer-results.json');(BASE/'capture_consumer_study.cjs').write_text(js)
