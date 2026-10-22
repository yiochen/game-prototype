"""Read-only actual native data comparison of retained crown/planar cutface progress."""
import bpy,json,hashlib,sys
from pathlib import Path
sys.dont_write_bytecode=True
B=Path(__file__).resolve().parent.parent;O=B/'candidates/round-03';N=89*79;F=88*78
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def capture(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));m=bpy.data.objects['rock-shelf-middle__sculpted_core'].data
 positions=[list(v.co) for v in list(m.vertices)[:N]];colors=[list(a.color) for a in list(m.color_attributes['rock_shelf_albedo'].data)[:N]];normals=[list(m.corner_normals[li].vector) for p in list(m.polygons)[:F] for li in p.loop_indices]
 material=next(mat for mat in m.materials if 'planar cut stone' in mat.name);g=material.node_tree
 graph={'nodes':[{'name':n.name,'type':n.bl_idname,'properties':{k:getattr(n,k) for k in ['operation','feature','voronoi_dimensions','interpolation_type','clamp'] if hasattr(n,k)},'inputs':{s.name:list(s.default_value) if hasattr(s.default_value,'__len__') and not isinstance(s.default_value,str) else s.default_value for s in n.inputs if hasattr(s,'default_value') and isinstance(s.default_value,(int,float,str)) or hasattr(s,'default_value') and type(s.default_value).__name__ in ['bpy_prop_array','Color','Vector']},'ramp':[{'position':e.position,'color':list(e.color)} for e in n.color_ramp.elements] if hasattr(n,'color_ramp') else None} for n in g.nodes],'links':[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in g.links]}
 return {'positions':positions,'colors':colors,'normals':normals,'capShader':graph}
oldpath=B/'source/round-02.blend';newpath=B/'source/round-03.blend';oldsha=sha(oldpath);newsha=sha(newpath);a=capture(oldpath);b=capture(newpath)
result={'asset':'rock-shelf-middle','round':'round-03','method':'Actual read-only reopened native meshes; first7031topgrid vertices and6864topfaces derive from exact authored grid. Caps graph compared without material label. No source saves.','priorSourceSHA256':oldsha,'newSourceSHA256':newsha,'crownVertexCount':N,'crownFaceCount':F,'crownPositionMaxResidual':max(abs(x-y) for av,bv in zip(a['positions'],b['positions']) for x,y in zip(av,bv)),'crownVertexAlbedoMaxResidual':max(abs(x-y) for av,bv in zip(a['colors'],b['colors']) for x,y in zip(av,bv)),'crownCornerNormalMaxResidual':max(abs(x-y) for av,bv in zip(a['normals'],b['normals']) for x,y in zip(av,bv)),'planarCutfaceGraphEqual':a['capShader']==b['capShader'],'planarCutfaceGraphSHA256':hashlib.sha256(json.dumps(b['capShader'],sort_keys=True).encode()).hexdigest(),'sourceBytesUnchangedAfter':sha(oldpath)==oldsha and sha(newpath)==newsha,'approval':False}
(O/'accepted-progress-preservation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
