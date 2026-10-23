import PIL,sys,json,shutil,subprocess,re
from PIL import Image,ImageDraw,ImageChops,ImageSequence
from pathlib import Path
BASE=Path(__file__).resolve().parent;OUT=BASE.parent/'evidence';root=Path(PIL.__file__).parent.parent
im=Image.open(BASE/'object/inputs/original.png');im.load();small=im.convert('RGBA').resize((96,240));ImageDraw.Draw(small).text((0,0),'source',fill='white');ImageChops.difference(small,small);small.save(OUT/'dependency-smoke.png');Image.open(OUT/'historical-playback.gif').seek(1)
files=[];native=[]
for name,module in list(sys.modules.items()):
 p=getattr(module,'__file__',None)
 if p and name.startswith('PIL'):
  p=Path(p)
  if p.suffix=='.pyc':continue
  if p.is_file():
   rel=p.relative_to(root);dst=BASE/'python-modules-used'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst);files.append(str(dst.relative_to(BASE)))
   if p.suffix=='.so':native.append(p)
visited=set()
while native:
 p=native.pop()
 if p in visited:continue
 visited.add(p)
 for line in subprocess.check_output(['otool','-L',str(p)],text=True).splitlines()[1:]:
  dep=line.strip().split(' (')[0]
  if dep.startswith('@loader_path/'):
   source=(p.parent/dep[len('@loader_path/'):]).resolve()
   if source.is_file():
    rel=source.relative_to(root);dst=BASE/'python-modules-used'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dst);files.append(str(dst.relative_to(BASE)));native.append(source)
(OUT/'python-module-closure.json').write_text(json.dumps({'python':sys.version,'executable':sys.executable,'Pillow':PIL.__version__,'method':'Actually imported Pillow modules for PNG/GIF opening, resizing, text drawing, differences, PNG save and sequence inspection; recursive otool @loader_path native dylib closure. Python stdlib/system frameworks remain environment prerequisites.','files':sorted(set(files))},indent=2)+'\n')
