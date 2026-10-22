import bpy, json, os
from mathutils import Vector

OUT = os.path.dirname(__file__)
def props(x):
    return {k: str(x[k]) for k in x.keys() if k != '_RNA_UI'}
def matrix(x): return [list(r) for r in x]
def obj(o):
    return {'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,
            'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),
            'matrixWorld':matrix(o.matrix_world),'hideRender':o.hide_render,'hideViewport':o.hide_viewport,
            'collections':[c.name for c in o.users_collection],'properties':props(o)}
data={'blender':bpy.app.version_string,'file':bpy.data.filepath,
      'scenes':[{'name':s.name,'camera':s.camera.name if s.camera else None,'properties':props(s),
                 'frame':s.frame_current,'frameStart':s.frame_start,'frameEnd':s.frame_end,
                 'resolution':[s.render.resolution_x,s.render.resolution_y,s.render.resolution_percentage],
                 'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y]} for s in bpy.data.scenes],
      'collections':[{'name':c.name,'properties':props(c),'objects':[o.name for o in c.objects],
                      'children':[x.name for x in c.children],'hideRender':c.hide_render,'hideViewport':c.hide_viewport}
                     for c in bpy.data.collections if 'cobalt' in c.name.lower() or 'background' in c.name.lower()],
      'objects':[obj(o) for o in bpy.data.objects if 'cobalt' in o.name.lower() or 'background' in o.name.lower()],
      'cameras':[obj(o)|{'orthoScale':o.data.ortho_scale,'shift':[o.data.shift_x,o.data.shift_y],
                         'typeCamera':o.data.type,'clip':[o.data.clip_start,o.data.clip_end]}
                 for o in bpy.data.objects if o.type=='CAMERA'],
      'texts':[t.name for t in bpy.data.texts],
      'libraries':[l.filepath for l in bpy.data.libraries],
      'images':[{'name':i.name,'path':i.filepath,'packed':bool(i.packed_file),'source':i.source} for i in bpy.data.images]}
with open(os.path.join(OUT,'native-inventory.json'),'w') as f: json.dump(data,f,indent=2)
print('WROTE_NATIVE_INVENTORY',len(data['collections']),len(data['objects']))
