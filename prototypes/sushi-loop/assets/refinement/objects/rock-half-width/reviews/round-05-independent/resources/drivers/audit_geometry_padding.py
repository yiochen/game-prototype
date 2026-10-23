import bpy,json,hashlib
from pathlib import Path
B=Path(__file__).resolve().parents[2];R=B/'resources';O=B/'evidence'
def geom():
 m=bpy.data.objects['rock-half-width__relief_core'].data
 return json.dumps({'vertices':[list(v.co) for v in m.vertices],'polygons':[list(p.vertices) for p in m.polygons]},separators=(',',':')).encode()
current=geom();bpy.ops.wm.open_mainfile(filepath=str(R/'previous-candidate.blend'));prior=geom()
x={'actualVertexPolygonBytesIdentical':current==prior,'round05GeometrySHA256':hashlib.sha256(current).hexdigest(),'round02GeometrySHA256':hashlib.sha256(prior).hexdigest(),'method':'Direct actual float coordinates and polygon index order from own frozen current and previous source copies. Neither scene saved. Prior own finite geometry/support facts reused only with this exact equality and current independent geometry/collar audit.'}
(O/'geometry-sameness.json').write_text(json.dumps(x,indent=2)+'\n');print(json.dumps(x))
