"""Read-only structural, material and capture audit of the actual saved June candidate."""
import bpy,json,hashlib,sys,math,importlib.util
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent
MODE='runtime' if '-runtime.blend' in bpy.data.filepath else 'main';LABEL=Path(bpy.data.filepath).stem.replace('-runtime','');OUT=OBJ/'candidates'/LABEL
record=json.loads((OBJ/('inputs/runtime-variants/export/source/customer-june/rig.json' if MODE=='runtime' else 'inputs/source-rig.json')).read_text())
root=bpy.data.objects[record['groundRootObject']];sc=next(s for s in bpy.data.scenes if root.name in s.objects);bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0]
col=next(c for c in sc.collection.children if root in list(c.all_objects));arm=next(o for o in col.all_objects if o.type=='ARMATURE');cam=sc.camera
spec=importlib.util.spec_from_file_location('native_audit',HERE/'native_actions.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
def short(o):return o.name.split('customer_june__')[-1].replace('.001','')
def write(name,value): (OUT/(MODE+'-'+name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
def sha(data):return hashlib.sha256(data).hexdigest()
def signature(value):return sha(json.dumps(value,sort_keys=True,separators=(',',':')).encode())
def val(x):
    if isinstance(x,(int,float,bool,str)) or x is None:return x
    try:return [val(a) for a in x]
    except:return str(x)
def nodes(tree):
    ns=list(tree.nodes);result=[]
    for n in ns:
        r={'type':n.bl_idname,'inputs':{s.identifier:val(s.default_value) for s in n.inputs if hasattr(s,'default_value')},'properties':{}}
        for key in ['operation','blend_type','data_type','interpolation','projection','extension','distance','inside','only_local','distribution','subsurface_method']:
            if hasattr(n,key):r['properties'][key]=val(getattr(n,key))
        if hasattr(n,'image') and n.image:r['image']={'packedSHA256':sha(bytes(n.image.packed_file.data)) if n.image.packed_file else None,'size':list(n.image.size),'colorSpace':n.image.colorspace_settings.name,'alphaMode':n.image.alpha_mode}
        if hasattr(n,'node_tree') and n.node_tree:r['nested']=nodes(n.node_tree)
        result.append(r)
    return {'nodes':result,'links':[{'from':[ns.index(l.from_node),l.from_socket.identifier],'to':[ns.index(l.to_node),l.to_socket.identifier]} for l in tree.links]}
native.apply_clip({'root':root,'collection':col},record,next(iter(record['clips'])),1,'S',sc)
geo={};material_records={};weight_issues=[];texture_planes=[]
for o in sorted(col.all_objects,key=short):
    if o.type!='MESH':continue
    key=short(o);m=o.data
    weights=[sorted([(o.vertex_groups[g.group].name,g.weight) for g in v.groups]) for v in m.vertices]
    if o.vertex_groups:
        for i,w in enumerate(weights):
            if not w or abs(sum(t[1] for t in w)-1)>1e-5:weight_issues.append({'part':key,'vertex':i,'weights':w})
    mats=[]
    for mat in m.materials:
        nd=nodes(mat.node_tree) if mat.use_nodes else None;mr={'nodes':nd,'diffuse':list(mat.diffuse_color),'surfaceRenderMethod':getattr(mat,'surface_render_method',None),'useBackfaceCulling':mat.use_backface_culling,'alphaThreshold':getattr(mat,'alpha_threshold',None)};mh=signature(mr);material_records[mh]=mr;mats.append(mh)
        if mat.use_nodes and any(n.type=='TEX_IMAGE' for n in mat.node_tree.nodes):texture_planes.append(key)
    payload={'vertices':[list(v.co) for v in m.vertices],'edges':[list(e.vertices) for e in m.edges],'polygons':[{'verts':list(p.vertices),'smooth':p.use_smooth,'materialIndex':p.material_index} for p in m.polygons],'cornerNormals':[list(n.vector) for n in m.corner_normals],'weights':weights,'materials':mats,'uvs':[[list(x.uv) for x in uv.data] for uv in m.uv_layers],'modifiers':[{'type':a.type,'showRender':a.show_render,'vertexGroup':getattr(a,'vertex_group',None),'useVertexGroups':getattr(a,'use_vertex_groups',None)} for a in o.modifiers]}
    geo[key]={'sha256':signature(payload),'vertexCount':len(m.vertices),'polygonCount':len(m.polygons),'groupNames':list(o.vertex_groups.keys()),'materialSignatures':mats,'payload':payload}
rest={'bones':[{'name':b.name,'parent':b.parent.name if b.parent else None,'useDeform':b.use_deform,'head':list(b.head_local),'tail':list(b.tail_local),'matrix':[list(r) for r in b.matrix_local]} for b in arm.data.bones]}
original_static=json.loads((OBJ/'reviews'/(MODE+'-source-static.json')).read_text())
rest_same=rest['bones']==original_static['armature']['bones']
actions=[];action_baseline=json.loads((OBJ/'reviews'/(MODE+'-native-action-baseline.json')).read_text());byact={(x['clip'],x['owner'],x['action']):x for x in action_baseline}
for clip,c in record['clips'].items():
    for t in c['actions']:
        a=bpy.data.actions[t['action']];curves=[{'path':f.data_path,'index':f.array_index,'extrapolation':f.extrapolation,'keys':[{'co':list(k.co),'interpolation':k.interpolation,'handleLeft':list(k.handle_left),'handleRight':list(k.handle_right),'handleLeftType':k.handle_left_type,'handleRightType':k.handle_right_type} for k in f.keyframe_points]} for f in native._fcurves(a)];h=signature(curves)
        # Source baseline hashes use sorted keys; exact values, handle types and interpolation are included.
        old=byact[(clip,t['ownerName'],t['action'])];actions.append({'clip':clip,'owner':t['ownerName'],'action':t['action'],'sha256':h,'sourceSHA256':old['sha256'],'unchanged':h==old['sha256'],'slotIdentifier':t.get('slotIdentifier')})
def px(p):q=world_to_camera_view(sc,cam,Vector(p));return [q.x*sc.render.resolution_x,(1-q.y)*sc.render.resolution_y]
lighting=[{'type':o.data.type,'matrix':[list(r) for r in o.matrix_world],'energy':o.data.energy,'color':list(o.data.color),'shape':o.data.shape,'size':o.data.size,'useShadow':o.data.use_shadow} for o in sc.objects if o.type=='LIGHT' and not o.hide_render]
compositor=nodes(sc.compositing_node_group) if sc.compositing_node_group else None
settings={'engine':sc.render.engine,'resolution':[sc.render.resolution_x,sc.render.resolution_y,sc.render.resolution_percentage],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'filmTransparent':sc.render.film_transparent,'imageSettings':{'format':sc.render.image_settings.file_format,'mode':sc.render.image_settings.color_mode,'depth':sc.render.image_settings.color_depth,'compression':sc.render.image_settings.compression},'dither':sc.render.dither_intensity,'colorManagement':{'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma},'eevee':{'samples':sc.eevee.taa_render_samples,'raytracing':sc.eevee.use_raytracing},'worldNodes':nodes(sc.world.node_tree),'lighting':lighting,'compositingNodeGroup':compositor}
camera={'projection':'character-orthographic','frame':[192,320],'anchor':[96,248],'captureScale':2,'fps':sc.render.fps,'cellSize':128,'axes':{'x':'X','depth':'-Y','height':'Z'},'nativeFrame':[sc.render.resolution_x,sc.render.resolution_y],'camera':{'name':cam.name,'type':cam.data.type,'worldMatrix':[list(r) for r in cam.matrix_world],'projectionMatrix':[list(r) for r in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=384,y=640,scale_x=1,scale_y=1)],'orthoScale':cam.data.ortho_scale,'sensorFit':cam.data.sensor_fit,'shift':[cam.data.shift_x,cam.data.shift_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'worldUnitsPerCell':1,'elevationDegrees':35},'calibration':{'nativeRoot':px((0,0,0)),'nativeUnitX':px((1,0,0)),'nativeUnitDepth':px((0,-1,0)),'nativeUnitHeight':px((0,0,1))},'actualRenderSettings':settings}
plane=next(o for o in col.all_objects if o.get('representation')=='2D ImageGen sprite, not modeled sushi');image=next(n.image for m in plane.data.materials for n in m.node_tree.nodes if n.type=='TEX_IMAGE');food='dish-salmon' if MODE=='runtime' else 'dish-cucumber';mapping=json.loads((OBJ/'reviews/food-mapping-proposal.json').read_text())[food]['isotropicFullUVMappingByThreshold']['128']
food_record={'asset':food,'representation':plane['representation'],'canonicalPackedSHA256':sha(bytes(image.packed_file.data)),'expectedCanonicalSHA256':json.loads((OBJ/'brief.json').read_text())['foodDependencies'][food]['sha256'],'imageSize':list(image.size),'vertices':[list(v.co) for v in plane.data.vertices],'selectedMapping':mapping,'uvs':[list(v.uv) for v in plane.data.uv_layers.active.data],'depthWorld':plane['camera_ray_depth_bias_world_cells'],'drivers':[{'path':f.data_path,'index':f.array_index,'expression':f.driver.expression,'variables':[{'name':v.name,'dataPath':v.targets[0].data_path,'owner':v.targets[0].id.name} for v in f.driver.variables]} for f in plane.animation_data.drivers],'inheritedSourcePropertiesProvenance':{k:val(plane[k]) for k in plane.keys()},'currentInterpretation':'Full canonical UV0..1 uses selected map128 EDGE support convention. Inherited source fixed_alpha_rectangle/world_width_cells are unmodified provenance; current width/support comes from actual vertices and selectedMapping.'}
required={'palm_L':['hand_L'],'palm_R':['hand_R'],'thumb_L':['hand_L'],'thumb_R':['hand_R'],'minimal_foot_L':['foot_L'],'minimal_foot_R':['foot_R'],'pelvis':['pelvis'],'smile':['head'],'head':['head']}
expected_groups_ok=all(geo[k]['groupNames']==v and all(len(w)==1 and w[0][0]==v[0] and abs(w[0][1]-1)<1e-5 for w in geo[k]['payload']['weights']) for k,v in required.items())
write('native-audit',{'blenderVersion':bpy.app.version_string,'project':str(PROJECT) if (PROJECT:=Path(bpy.data.filepath)) else None,'projectSHA256':sha(PROJECT.read_bytes()),'scene':sc.name,'collection':col.name,'rootName':root.name,'rootScale':list(root.scale),'rest':rest,'restExactlyMatchesOriginal':rest_same,'actions':actions,'allActionKeysHandlesSlotsUnchanged':all(x['unchanged'] for x in actions),'weightIssues':weight_issues,'functionalPartsHaveIntendedFullWeight':expected_groups_ok,'geometry':geo,'materialGraphs':material_records,'textureBearingMeshes':texture_planes,'food':food_record,'capture':camera,'sourceBackupSHA256':sha((HERE/('original-runtime.blend' if MODE=='runtime' else 'original-library.blend')).read_bytes())})
write('camera',camera)
asset_record=json.loads((OBJ/'inputs/source-assetRecord.json').read_text());asset_record.update(scale=2,frame=[192,320],anchor=[96,248],fps=12,nativeFrame=[384,640],artStyle={'style':'Warm softly lit native cartoon','actualRenderSettings':settings,'sourceStyleIsHistoricalProvenance':True},food=food_record)
if MODE=='runtime':asset_record['clips']={k:{'frames':v['frames'],'fps':12,'loop':True} for k,v in record['clips'].items()}
write('asset',asset_record)
record.update(status='native-refined-independent-visual-review-pending',captureScale=2,nativeFrame=[384,640],canonicalFood=food_record,refinementRecipe=HERE.name+'/reproduce_round02.py')
write('rig',record)
print('JUNE_AUDIT',MODE,'rest',rest_same,'actions',all(x['unchanged'] for x in actions),'weightIssues',len(weight_issues),'expectedGroups',expected_groups_ok,'meshes',len(geo),flush=True)
