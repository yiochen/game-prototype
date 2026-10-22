from pathlib import Path
import json,shutil
E=Path(__file__).resolve().parents[2];ROOT=E.parent
ids=['belt-corner-n-w','belt-corner-w-n','belt-corner-s-e','belt-corner-e-s','belt-corner-s-w','belt-corner-w-s']
for asset in ids:
 S=ROOT/asset/'source'
 if (ROOT/asset/'candidates/round-01/packet.json').exists():continue
 p=S/'package-round01.py';t=p.read_text()
 a=t.index(' for axis in [0,1]:');b=t.index(' m.save(',a)
 t=t[:a]+''' for offset,angle in SPECS:
  nx,ny=offset[:2];tx,ty=-ny,nx;pts=[]
  for cross in [-.48,.48]:
   for delta in [-.014,.014]:
    for z in [.505,.695]:
     x,y=nx*(.5+delta)+tx*cross,ny*(.5+delta)+ty*cross;xx=x*math.cos(r)-y*math.sin(r);yy=x*math.sin(r)+y*math.cos(r);pts.append((448+256*xx,752-256*yy-z*179.2))
  dr.rectangle((min(p[0] for p in pts)-1,min(p[1] for p in pts)-1,max(p[0] for p in pts)+1,max(p[1] for p in pts)+1),fill=255)
''' +t[b:]
 p.write_text(t)
 # Millisecond-accurate two-loop previews from exact published frames.
 t=(E/'source/playback-evidence.py').read_text();t=t[:t.index('# A tightly localized diagnostic')]+"(O/'playback-records.json').write_text(json.dumps({'format':'lossless animatedWebP, millisecond timing','records':rows},indent=2))\n";(S/'playback-evidence.py').write_text(t)
 # Current SpriteScene, same tested registered root assembly; only perasset source and measured module list differ.
 t=(E/'source/consumer-bench.jsx').read_text().replace('belt-corner-e-n',asset)
 a=t.index("let placements=mode===");b=t.index('\nlet bounds=',a)
 t=t[:a]+'''const spec=await fetch('./consumer-modules.json').then(r=>r.json());
let placements=mode==='independent'?spec[direction].map(c=>({object:c.kind==='frames'?base.id:family.id,x:1+(c.offset[0]-256)/256,y:1+(c.offset[1]-256)/256,direction:c.direction})):[{object:native.id,x:1,y:1,direction}];''' +t[b:]
 (S/'consumer-bench.jsx').write_text(t);shutil.copyfile(E/'source/consumer-bench.html',S/'consumer-bench.html')
