"""Replay the saved native actions and capture all 48 registered native phases."""
import bpy,json,math,hashlib,sys,time
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent;O=H.parent;C=O/'candidates/round-01'
SOURCE=H/'round-01.blend'
assert Path(bpy.data.filepath).resolve()==SOURCE.resolve()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def mat(m):return [list(r) for r in m]
def bounds(pp):
    pp=list(pp)
    return {'min':[min(p[i] for p in pp) for i in range(3)],'max':[max(p[i] for p in pp) for i in range(3)]} if pp else None
sc=bpy.data.scenes['S33 Native Asset Library Export'];bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0]
col=bpy.data.collections['S33_PROP_portal_rim.003'];root=bpy.data.objects['portal_rim__root.003']
def enable(l):
    l.exclude=False;l.hide_viewport=False
    for x in l.children:enable(x)
enable(sc.view_layers[0].layer_collection)
col.hide_render=False;col.hide_viewport=False
for o in col.all_objects:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
sc.view_layers[0].update();sc.render.use_persistent_data=True
W,HPIX=sc.render.resolution_x,sc.render.resolution_y
def px(v):
    p=world_to_camera_view(sc,sc.camera,Vector(v));return [p.x*W,(1-p.y)*HPIX]
zero=px((0,0,0))
cal={'root':zero,'unitX':[px((1,0,0))[i]-zero[i] for i in range(2)],'unitDepth':[px((0,-1,0))[i]-zero[i] for i in range(2)],'unitHeight':[px((0,0,1))[i]-zero[i] for i in range(2)]}
assert max(abs(zero[i]-[384,1152][i]) for i in range(2))<.01
camera={'projection':'top-down-oblique-square-grid','frame':[192,384],'anchor':[96,288],'cellSize':128,'captureScale':4,'nativeCaptureScale':4,'nativeFrame':[768,1536],'fps':12,'axes':{'x':'X','depth':'-Y','height':'Z'},'camera':{'type':'orthographic','worldMatrix':mat(sc.camera.matrix_world),'projectionMatrix':mat(sc.camera.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=W,y=HPIX,scale_x=sc.render.pixel_aspect_x,scale_y=sc.render.pixel_aspect_y)),'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'worldUnitsPerCell':1,'elevationDegrees':55.00797980144134,'sensorFit':sc.camera.data.sensor_fit,'orthoScale':sc.camera.data.ortho_scale,'shift':[sc.camera.data.shift_x,sc.camera.data.shift_y]},'calibration':cal,'actualOrthoScale':sc.camera.data.ortho_scale,'shift':[sc.camera.data.shift_x,sc.camera.data.shift_y],'sourceSHA256':sha(SOURCE)}
write(C/'native-camera.json',camera)
recipe=json.loads((H/'round-01-recipe.json').read_text())
supports=recipe['supports'];rim=bpy.data.objects['portal_entry | continuous cyan rim']
own=sorted(col.all_objects,key=lambda x:x.name)
actions=[]
for o in own:
    if o.animation_data and o.animation_data.action:
        a=o.animation_data.action;fs=[f for l in a.layers for s in l.strips for cb in s.channelbags for f in cb.fcurves]
        actions.append({'owner':o.name,'action':a.name,'frameRange':list(a.frame_range),'channels':[{'dataPath':f.data_path,'arrayIndex':f.array_index,'keys':[[*k.co,k.interpolation] for k in f.keyframe_points]} for f in fs]})
write(C/'native-actions.json',{'sourceSHA256':sha(SOURCE),'actions':actions,'frames':12,'fps':12,'loop':False,'terminal':'hold frame 11','nativeSavedAssignedActions':True})
records=[]
for direction,degrees in [('N',180),('E',90),('S',0),('W',-90)]:
    folder=C/'native/enter'/direction;folder.mkdir(parents=True,exist_ok=True)
    for i in range(12):
        root.rotation_euler.z=math.radians(degrees);sc.frame_set(i+1);sc.view_layers[0].update()
        dg=bpy.context.evaluated_depsgraph_get();dg.update()
        raw_all=[];ev_all=[];canonical_raw=[];canonical_ev=[];objects=[];bvhs={};all_verts=[];all_faces=[];sections=[]
        inv=root.matrix_world.inverted()
        for o in own:
            if o.type!='MESH':continue
            e=o.evaluated_get(dg);me=e.to_mesh();ev=[e.matrix_world@v.co for v in me.vertices];raw=[o.matrix_world@v.co for v in o.data.vertices]
            faces=[tuple(p.vertices) for p in me.polygons]
            bvhs[o.name]=BVHTree.FromPolygons(ev,faces)
            offset=len(all_verts);all_verts.extend(ev);all_faces.extend(tuple(offset+v for v in f) for f in faces)
            raw_all.extend(raw);ev_all.extend(ev);canonical_raw.extend(inv@v for v in raw);canonical_ev.extend(inv@v for v in ev)
            objects.append({'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'matrixWorld':mat(e.matrix_world),'rawAuthoredWorldBounds':bounds(raw),'evaluatedWorldBounds':bounds(ev),'rawVertices':len(raw),'evaluatedVertices':len(ev),'rawPolygons':len(o.data.polygons),'evaluatedPolygons':len(me.polygons),'visible':o.visible_get(),'materials':[s.material.name for s in o.material_slots if s.material]})
            if o.name in supports:
                pts=[]
                for edge in me.edges:
                    a,b=[ev[v] for v in edge.vertices]
                    if (a.z<0<=b.z) or (b.z<0<=a.z):
                        t=-a.z/(b.z-a.z);p=a+(b-a)*t;pts.append(list(p))
                sections.append({'object':o.name,'planeZ':0,'edgeIntersections':pts,'contactSectionBounds':bounds(pts),'finiteSection':len(pts)>=3,'animatedOwner':bool(o.animation_data),'matrixWorld':mat(e.matrix_world)})
            e.to_mesh_clear()
        bvh=BVHTree.FromPolygons(all_verts,all_faces)
        center=root.matrix_world@Vector((0,0,.74));axis=root.matrix_world.to_3x3()@Vector((0,1,0))
        rays=[]
        for sign in (-1,1):
            hit=bvh.ray_cast(center,axis*sign,.6)
            rays.append({'sign':sign,'direction':list(axis*sign),'rayLength':.6,'hitLocation':list(hit[0]) if hit[0] is not None else None,'clear':hit[0] is None})
        nearest=bvh.find_nearest(center)
        cb=bounds(canonical_ev);rb=bounds(canonical_raw);limits=[(-.74,.74),(-.30,.30),(-.06,1.50)]
        within=all(cb['min'][j]>=limits[j][0]-1e-5 and cb['max'][j]<=limits[j][1]+1e-5 and rb['min'][j]>=limits[j][0]-1e-5 and rb['max'][j]<=limits[j][1]+1e-5 for j in range(3))
        assert within,(direction,i,cb,rb)
        assert all(s['finiteSection'] for s in sections)
        assert all(r['clear'] for r in rays)
        joins=[{'support':name,'rim':rim.name,'surfaceIntersectionFacePairs':len(bvhs[name].overlap(bvhs[rim.name]))} for name in supports]
        assert all(j['surfaceIntersectionFacePairs']>0 for j in joins),(direction,i,joins)
        p=folder/f'{i:03d}.png';assert not p.exists()
        sc.render.filepath=str(p);start=time.monotonic();bpy.ops.render.render(write_still=True,scene=sc.name)
        rec={'direction':direction,'clip':'enter','index':i,'frame':i+1,'nativeFrame':i+1,'rootRotationZ':root.rotation_euler.z,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'rootMatrix':mat(root.matrix_world),'cameraMatrix':mat(sc.camera.matrix_world),'rootPixel':px((0,0,0)),'entrySocketWorld':list(center),'entrySocketPixel':px(center),'rawAuthoredWorldBounds':bounds(raw_all),'evaluatedWorldBounds':bounds(ev_all),'canonicalSRawAuthoredBounds':rb,'canonicalSEvaluatedBounds':cb,'withinFrozenAllphaseBudget':within,'supportSections':sections,'supportRingConnections':joins,'opening':{'center':list(center),'centerNearestSurfaceDistance':nearest[3],'throughThicknessRays':rays,'trueOpenGeometry':all(r['clear'] for r in rays)},'objects':objects,'path':str(p.relative_to(O)),'sha256':sha(p),'seconds':time.monotonic()-start,'sourceSHA256':sha(SOURCE),'captureScriptSHA256':sha(Path(__file__))}
        records.append(rec)
        write(C/'native-validation.json',{'asset':'portal-entry','round':'round-01','source':'source/round-01.blend','sourceSHA256':sha(SOURCE),'nativeCamera':'candidates/round-01/native-camera.json','nativeActions':'candidates/round-01/native-actions.json','measurementMethod':'Actual saved native source/actions; enabled correct scene/viewlayer/own ancestry and object hide flags; dependency graph updated. Authored geometry and evaluated geometry measured separately while capturing each actual pose. BVH rays through entry socket and actual mesh intersection pairs at fixed supports. No property-only validation.','views':records})
        print('PORTAL_ROUND01_CAPTURE',direction,i,'seconds',round(rec['seconds'],2),flush=True)
write(C/'native-render-settings.json',{'sourceSHA256':sha(SOURCE),'engine':sc.render.engine,'blenderVersion':bpy.app.version_string,'nativeResolution':[W,HPIX],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'filmTransparent':sc.render.film_transparent,'imageColorMode':sc.render.image_settings.color_mode,'colorManagement':{'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma},'compositing':sc.render.use_compositing,'threads':sc.render.threads,'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'color':list(o.data.color),'size':o.data.size,'matrixWorld':mat(o.matrix_world)} for o in sc.objects if o.type=='LIGHT'],'groundGeometry':False,'horizontalLightSymmetry':4})
print('PORTAL_ROUND01_COMPLETE',len(records),flush=True)
