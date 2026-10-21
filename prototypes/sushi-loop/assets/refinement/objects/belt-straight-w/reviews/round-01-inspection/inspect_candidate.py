import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
OUT=Path(__file__).resolve().parent;EXP=OUT.parents[1]
PROJECT=EXP/'source/round-01.blend';FAM=json.loads((EXP/'inputs/family-settings.json').read_text())
def plain(v):
    if isinstance(v,(bool,str,int,float)) or v is None:return v
    try:return [plain(x) for x in v]
    except:return str(v)
def graph(nt):
    out={'nodes':[],'links':[]}
    for n in sorted(nt.nodes,key=lambda x:x.name):
        d={'name':n.name,'type':n.bl_idname,'inputs':[(i,s.name,plain(s.default_value)) for i,s in enumerate(n.inputs) if hasattr(s,'default_value')]}
        attrs={}
        for attr in ('operation','use_clamp','clamp','blend_type','data_type','interpolation_type','vector_type','convert_from','convert_to','distribution','noise_dimensions','noise_type','normalize','feature','distance','voronoi_dimensions','wave_type','bands_direction','wave_profile','mapping','extension','projection','use_object_space','uv_map','from_instancer'):
            if hasattr(n,attr):attrs[attr]=plain(getattr(n,attr))
        if hasattr(n,'object'):attrs['object']=n.object.name if n.object else None
        if n.type=='VALUE':attrs['outputValue']=n.outputs[0].default_value
        if hasattr(n,'color_ramp'):
            r=n.color_ramp;attrs['colorRamp']={'interpolation':r.interpolation,'colorMode':r.color_mode,'hueInterpolation':r.hue_interpolation,'elements':[(e.position,list(e.color)) for e in r.elements]}
        if hasattr(n,'mapping') and not isinstance(n.mapping,str):attrs.pop('mapping',None)
        d['attrs']=attrs;out['nodes'].append(d)
    out['links']=sorted((l.from_node.name,list(l.from_node.outputs).index(l.from_socket),l.to_node.name,list(l.to_node.inputs).index(l.to_socket)) for l in nt.links)
    return out
def clear_hide(sc):
    def lc(x):
        x.exclude=False;x.hide_viewport=False
        for c in x.children:lc(c)
    for c in bpy.data.collections:c.hide_viewport=False;c.hide_render=False
    for vl in sc.view_layers:lc(vl.layer_collection)
    for o in sc.objects:o.hide_set(False);o.hide_viewport=False;o.hide_render=False
    bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()
def snapshot(path,asset):
    bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene
    col=bpy.data.collections['S33_FB_'+asset+'.001'];root=bpy.data.objects[asset+'__root.001'];root.rotation_euler.z=0
    clear_hide(sc);sc.frame_set(1);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();dg.update()
    mats={m for o in col.all_objects if o.type=='MESH' for m in o.data.materials if m}
    graphs={('deck' if 'moving_deck' in m.name else m.name):graph(m.node_tree) for m in mats}
    meshes=[];allpts=[]
    for o in col.all_objects:
        if o.type!='MESH':continue
        eo=o.evaluated_get(dg);me=eo.to_mesh();pts=[eo.matrix_world@v.co for v in me.vertices];allpts.extend(pts)
        item={'name':o.name,'parent':o.parent.name if o.parent else None,'localBounds':[[min(v.co[i] for v in o.data.vertices),max(v.co[i] for v in o.data.vertices)] for i in range(3)],'worldBounds':[[min(v[i] for v in pts),max(v[i] for v in pts)] for i in range(3)],'endProfilesX':{str(x):[list(p) for p in pts if abs(p.x-x)<1e-6] for x in (-.5,.5)},'modifiers':[(m.name,m.type) for m in o.modifiers],'materials':[m.name for m in o.data.materials]}
        if 'connected_straight_deck' in o.name:item['UVLoops']=[{'uv':list(o.data.uv_layers.active.data[i].uv),'world':list(o.matrix_world@o.data.vertices[l.vertex_index].co)} for i,l in enumerate(o.data.loops)]
        meshes.append(item);eo.to_mesh_clear()
    cam=sc.camera
    def px(v):
        p=world_to_camera_view(sc,cam,Vector(v));return [p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y]
    origin=px((0,0,0));camera={'worldMatrix':[list(r) for r in cam.matrix_world],'projectionMatrix':[list(r) for r in cam.calc_matrix_camera(dg,x=sc.render.resolution_x,y=sc.render.resolution_y,scale_x=sc.render.pixel_aspect_x,scale_y=sc.render.pixel_aspect_y)],'frame':[sc.render.resolution_x,sc.render.resolution_y],'root':origin,'units':{k:[a-b for a,b in zip(px(v),origin)] for k,v in {'X':(1,0,0),'depth':(0,-1,0),'height':(0,0,1)}.items()},'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y]}
    deck=next(m for m in mats if 'moving_deck' in m.name);a=deck.node_tree.animation_data
    curves=[]
    if a and a.action:
        for la in a.action.layers:
            for st in la.strips:
                for cb in st.channelbags:
                    for fc in cb.fcurves:curves.append({'path':fc.data_path,'index':fc.array_index,'keys':[(k.co.x,k.co.y,k.interpolation) for k in fc.keyframe_points]})
    phases=[]
    for frame in range(1,26):sc.frame_set(frame);dg.update();phases.append(deck.node_tree.nodes['Value'].outputs[0].default_value)
    sc.frame_set(1)
    lights=sorted([{'name':o.name,'type':o.data.type,'energy':o.data.energy,'size':o.data.size,'color':list(o.data.color),'matrixWorld':[list(r) for r in o.matrix_world]} for o in sc.objects if o.type=='LIGHT'],key=lambda x:x['name'])
    return {'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'scene':sc.name,'orientation':list(bpy.data.objects[asset+'__orientation.001'].rotation_euler),'bounds':[[min(p[i] for p in allpts),max(p[i] for p in allpts)] for i in range(3)],'meshes':meshes,'graphs':graphs,'camera':camera,'lights':lights,'world':graph(sc.world.node_tree),'render':{'engine':sc.render.engine,'samples':sc.cycles.samples,'device':sc.cycles.device,'filter':sc.cycles.pixel_filter_type,'filterWidth':sc.cycles.filter_width,'scramblingDistance':sc.cycles.scrambling_distance,'samplingPattern':sc.cycles.sampling_pattern,'denoising':sc.cycles.use_denoising,'dither':sc.render.dither_intensity,'view':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure},'action':{'material':deck.name,'action':a.action.name if a and a.action else None,'slot':a.action_slot.identifier if a and a.action_slot else None,'curves':curves,'phases':phases},'resources':{'libraries':[x.filepath for x in bpy.data.libraries],'images':[{'name':x.name,'source':x.source,'filepath':x.filepath} for x in bpy.data.images],'linkedIDs':[x.name for collection in (bpy.data.objects,bpy.data.materials,bpy.data.meshes,bpy.data.node_groups) for x in collection if x.library]}}

family=snapshot(Path(FAM['project']['path']),'belt-straight-n')
candidate=snapshot(PROJECT,'belt-straight-w')
checks={'materialGraphs':{k:candidate['graphs'][k]==family['graphs'][k] for k in family['graphs']},'lightsEqual':candidate['lights']==family['lights'],'worldEqual':candidate['world']==family['world'],'renderEqual':candidate['render']==family['render'],'cameraEqual':candidate['camera']==family['camera']}
(OUT/'native-candidate-inspection.json').write_text(json.dumps({'candidate':candidate,'family':family,'checks':checks},indent=2)+'\n')
# Small independent reproduce sample, preserving saved camera/response.
sc=bpy.context.scene;root=bpy.data.objects['belt-straight-w__root.001'];rendered=[]
for facing,frame in [('N',1),('E',1),('S',1),('W',1),('W',13),('W',24),('W',25),('N',25)]:
    root.rotation_euler.z=math.radians({'S':0,'E':90,'N':180,'W':-90}[facing]);sc.frame_set(frame);bpy.context.view_layer.update()
    dest=OUT/f'judge-native-{facing}-{frame-1:02d}.png';sc.render.filepath=str(dest);bpy.ops.render.render(write_still=True)
    rendered.append(str(dest))
(OUT/'native-render-index.json').write_text(json.dumps(rendered,indent=2)+'\n')
print('JUDGE_NATIVE_CHECKS',json.dumps(checks))
