"""Finish outward normals of the sole round02 mouth revision before handoff."""
import bpy,json,hashlib
from pathlib import Path
P=Path(__file__).parent;C=P.parent/'candidates/round-02';sc=bpy.data.scenes['Lena warm soft round02'];bpy.context.window.scene=sc;o=bpy.data.objects['chef_lena__R01_gentle_smile']
def volume(me):return sum(me.vertices[p.vertices[0]].co.dot(me.vertices[p.vertices[i]].co.cross(me.vertices[p.vertices[i+1]].co))/6 for p in me.polygons for i in range(1,len(p.vertices)-1))
before=volume(o.data)
if before<0:o.data.flip_normals();o.data.update()
after=volume(o.data);assert after>0
bpy.ops.wm.save_as_mainfile(filepath=str(P/'round-02.blend'))
p=C/'smile-native-construction.json';v=json.loads(p.read_text());v['sourceSHA256']=hashlib.sha256((P/'round-02.blend').read_bytes()).hexdigest();v['signedVolume']=after;v['outwardNormals']=True;p.write_text(json.dumps(v,indent=2));print('OUTWARD_SMILE_NORMALS',after)
