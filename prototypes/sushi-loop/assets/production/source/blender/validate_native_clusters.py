"""Read-only evaluated native audit for the eight organic clusters and wide entry.

ROOT executes in the live production Blender after native actions are baked:
    ns={'__file__':'/private/tmp/sushi33-production/validate_native_clusters.py'}
    exec(compile(open(ns['__file__']).read(),ns['__file__'],'exec'),ns)
    report=ns['validate_native_clusters'](r,N,report_path='.../native-clusters.json')

No pose callback, custom sampled vertices, rendering, or geometry edits run.
Presentation/action bindings are temporarily evaluated and restored. This is
structural evidence; sprite alpha/visual composition are separately reviewed.
"""
import contextlib
import hashlib
import json
import math
import os
from pathlib import Path
import time
import bpy
from mathutils import Vector

BASE=Path('/private/tmp/sushi33-production')
CLUSTERS={
 'restaurant-border-garden-a':(2,4),'restaurant-border-garden-b':(2,4),
 'restaurant-corner-garden-a':(3,3),'restaurant-corner-garden-b':(3,3),
 'underwater-reef-garden-a':(2,4),'underwater-reef-garden-b':(2,4),
 'underwater-coral-garden-a':(3,3),'underwater-coral-garden-b':(3,3),
}
ANGLES={'S':0.,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}


def _record(runtime,aid):
    record=getattr(runtime,'native_records',{}).get(aid)
    return record if record is not None else json.loads((BASE/'export/source'/aid/'rig.json').read_text())


@contextlib.contextmanager
def _presentation(runtime,native,ids):
    window=bpy.context.window;old_scene=window.scene if window else bpy.context.scene
    old_layer=window.view_layer if window else bpy.context.view_layer
    old_active=old_layer.objects.active;selected=list(bpy.context.selected_objects)
    scene=bpy.data.scenes.get(getattr(runtime,'SCENE_NAME','Sushi33 Production'))
    if scene is None:raise ValueError('Production scene is not loaded')
    old_frame=(scene.frame_current,scene.frame_subframe)
    settings=(scene.render.fps,scene.render.fps_base,scene.frame_start,scene.frame_end,scene.camera)
    owners={};objects={};nodes={};shapes={}
    try:
        if window:window.scene=scene;window.view_layer=scene.view_layers[0]
        elif bpy.context.scene!=scene:raise ValueError('Current scene is not production')
        for aid in ids:
            asset=runtime.assets[aid];objs=native._all_objects(asset)
            sockets=native._node_sockets(objs);shape_meshes=native._shape_meshes(objs)
            for obj in objs:
                objects.setdefault(obj.as_pointer(),(obj,obj.matrix_basis.copy(),obj.rotation_mode,obj.hide_render,obj.hide_viewport))
            for key,(_,_,socket,_,_) in sockets.items():
                value=socket.default_value
                nodes.setdefault(key,(socket,value.copy() if hasattr(value,'copy') else tuple(value) if hasattr(value,'__len__') else value))
            for obj in shape_meshes.values():
                for block in obj.data.shape_keys.key_blocks:shapes.setdefault(block.as_pointer(),(block,block.value))
            for owner in native._animation_owners(objs,sockets,shape_meshes):
                if owner.as_pointer() in owners:continue
                ad=owner.animation_data
                owners[owner.as_pointer()]=(owner,ad is not None,ad.action if ad else None,getattr(getattr(ad,'action_slot',None),'identifier',None) if ad else None,[(track,track.mute) for track in ad.nla_tracks] if ad else [])
        yield scene
    finally:
        # No scene/object/collection is created or deleted by this audit.
        for owner,had_ad,action,slot,tracks in owners.values():
            if had_ad:
                native._assign(owner,action,slot)
                for track,mute in tracks:track.mute=mute
            elif owner.animation_data:owner.animation_data_clear()
        fps,fps_base,start,end,camera=settings
        scene.render.fps=fps;scene.render.fps_base=fps_base;scene.frame_start=start;scene.frame_end=end;scene.camera=camera
        scene.frame_set(old_frame[0],subframe=old_frame[1])
        for obj,matrix,mode,render,viewport in objects.values():
            obj.rotation_mode=mode;obj.matrix_basis=matrix;obj.hide_render=render;obj.hide_viewport=viewport
        for socket,value in nodes.values():socket.default_value=value
        for block,value in shapes.values():block.value=value
        if window:window.scene=old_scene;window.view_layer=old_layer
        if set(bpy.context.selected_objects)!=set(selected):
            for obj in list(bpy.context.selected_objects):obj.select_set(False)
            for obj in selected:obj.select_set(True)
        old_layer.objects.active=old_active;bpy.context.view_layer.update()


def _geometry(asset,graph):
    """Actual evaluated mesh vertices in world space; hidden render pieces excluded."""
    result=[]
    for obj in asset['collection'].all_objects:
        if obj.type!='MESH' or obj.hide_render:continue
        evaluated=obj.evaluated_get(graph)
        if evaluated.hide_render:continue
        mesh=evaluated.to_mesh()
        try:
            if not mesh.vertices:continue
            points=[evaluated.matrix_world@v.co for v in mesh.vertices]
            low=Vector(tuple(min(v[i] for v in points) for i in range(3)))
            high=Vector(tuple(max(v[i] for v in points) for i in range(3)))
            result.append({'object':obj,'evaluated':evaluated,'name':obj.name,'points':points,'low':low,'high':high,'center':(low+high)/2})
        finally:evaluated.to_mesh_clear()
    if not result:raise ValueError('No visible evaluated native meshes')
    return result


def _signature(meshes,origin,detailed=False):
    # Names are deliberately excluded: renaming a duplicate cannot pass A/B.
    pieces=[]
    for mesh in meshes:
        if detailed:
            value=sorted(tuple(round((point-origin)[i],4) for i in range(3)) for point in mesh['points'])
        else:
            value=[[round(v,5) for v in mesh['low']-origin],[round(v,5) for v in mesh['high']-origin],len(mesh['points'])]
        pieces.append(hashlib.sha256(json.dumps(value,separators=(',',':')).encode()).hexdigest())
    return hashlib.sha256(''.join(sorted(pieces)).encode()).hexdigest()


def _bounds(meshes,origin):
    return {'minimum':[min(m['low'][i] for m in meshes)-origin[i] for i in range(3)],
            'maximum':[max(m['high'][i] for m in meshes)-origin[i] for i in range(3)]}


def _dense_evidence(meshes,origin,footprint):
    occupied=set();fractional=[];groups={}
    for mesh in meshes:
        ident=mesh['object'].get('cluster_component_id')
        if ident:groups.setdefault(str(ident),[]).append(mesh)
    elevated=0
    for ident,pieces in groups.items():
        low=Vector(tuple(min(m['low'][i] for m in pieces) for i in range(3)))
        high=Vector(tuple(max(m['high'][i] for m in pieces) for i in range(3)))
        if high.z-origin.z<.18:continue
        elevated+=1;center=(low+high)/2-origin
        cell=(math.floor(center.x+footprint[0]/2),math.floor(-center.y+footprint[1]/2))
        if 0<=cell[0]<footprint[0] and 0<=cell[1]<footprint[1]:occupied.add(cell)
        if max(abs(2*center.x-round(2*center.x)),abs(2*center.y-round(2*center.y)))>.12:
            fractional.append({'component':ident,'actualMeshBoundsCenter':[round(center.x,4),round(center.y,4),round(center.z,4)]})
    return {'visibleMeshes':len(meshes),'actualComponentGroups':len(groups),'elevatedComponents':elevated,
            'occupiedComponentCells':sorted([list(c) for c in occupied]),
            'minimumOccupiedCells':max(4,math.ceil(footprint[0]*footprint[1]*.5)),
            'fractionalComponentCenters':fractional,'minimumFractionalCenters':4}


def _entry_clearance(meshes,origin):
    # Ray-test actual polygons through the two-cell center of the doorway at
    # human/sub-height, rather than inferring clearance from support names.
    hits=[];rays=0
    for ix in range(21):
        x=-.95+1.9*ix/20
        for iz in range(11):
            z=.08+1.42*iz/10
            start=origin+Vector((x,-.65,z));delta=Vector((0.,1.,0.));length=1.3;rays+=1
            for mesh in meshes:
                low,high=mesh['low'],mesh['high']
                if not low.x<=start.x<=high.x or not low.z<=start.z<=high.z:continue
                obj=mesh['evaluated'];inverse=obj.matrix_world.inverted()
                a=inverse@start;b=inverse@(start+delta*length);local_delta=b-a
                hit,point,normal,index=obj.ray_cast(a,local_delta.normalized(),distance=local_delta.length)
                if hit:
                    world=obj.matrix_world@point
                    if -.5-1e-5<world.y-origin.y<.5+1e-5:
                        hits.append({'object':mesh['name'],'point':[round(v,5) for v in world-origin]});break
    return {'rays':rays,'passageWidth':2.,'testedX':[-.95,.95],'testedHeight':[.08,1.5],'obstructions':hits[:20],'obstructionCount':len(hits)}


def validate_native_clusters(runtime,native,report_path=None,include_entry=True,tolerance=.005):
    if getattr(runtime,'job_status',{}).get('state')=='rendering':raise RuntimeError('Wait for live MCP capture before temporary native evaluation')
    ids=list(CLUSTERS)
    missing=[aid for aid in ids if aid not in runtime.assets]
    if missing:raise ValueError('Native models are not registered yet: '+', '.join(missing))
    output=Path(report_path) if report_path else BASE/'export/validation/native-clusters.json'
    report={'version':1,'ok':False,'createdAtUnix':time.time(),'source':'actual evaluated native world-space mesh vertices and baked actions; no pose callback',
      'blendPath':bpy.data.filepath,'blenderVersion':bpy.app.version_string,'selectedIds':ids,'directions':['S','E','N','W'],
      'toleranceWorldUnits':tolerance,'assetsChecked':0,'casesChecked':0,'samplesChecked':0,'errors':[],'cases':[],
      'variationChecks':[],'report':str(output)}
    signatures={}
    try:
        with _presentation(runtime,native,ids) as scene:
            for aid in ids:
                asset=runtime.assets[aid];root=asset['root'];record=_record(runtime,aid)
                footprint=CLUSTERS.get(aid,(4,1));asset_errors=[]
                if list(asset.get('footprint',[]))!=list(footprint):asset_errors.append('Declared native footprint does not match required '+str(footprint))
                if aid in CLUSTERS:
                    if asset.get('ports'):asset_errors.append('Decorative cluster unexpectedly exposes seam ports')
                    if asset.get('nonblocking') is not True and asset.get('blocking') is not False:asset_errors.append('Cluster must explicitly declare nonblocking decoration')
                    for clip,count in [('static',1),('ambient',12)]:
                        cfg=record.get('clips',{}).get(clip,{})
                        if cfg.get('frames')!=count or cfg.get('fps')!=12:asset_errors.append('Required '+clip+' is not '+str(count)+' native frames at12fps')
                report['errors'].extend({'case':aid,'message':error} for error in asset_errors)
                # Native entry keeps its original single-frame clip ID (idle).
                # Publisher normalization may expose it as static; inspect the
                # actual baked recipe rather than assuming the runtime alias.
                static_recipes=[name for name,recipe in record.get('clips',{}).items()
                                if int(recipe.get('frames',0))==1 and recipe.get('static')]
                clip='ambient' if aid in CLUSTERS else ('static' if 'static' in static_recipes else next(iter(static_recipes),None))
                if clip not in record.get('clips',{}):
                    report['errors'].append({'case':aid,'message':'Missing actual baked ambient clip' if aid in CLUSTERS else 'Missing actual baked one-frame static recipe'});continue
                count=int(record['clips'][clip]['frames']);origin=root.matrix_world.translation.copy()
                with native._sampling_visibility(asset):
                    for direction in report['directions']:
                        row={'id':aid,'clip':clip,'direction':direction,'samples':count,'ok':False,'errors':[]}
                        try:
                            native.apply_clip(asset,record,clip,frame=1,direction=direction,scene=scene)
                            limits=footprint[::-1] if direction in ['E','W'] else footprint
                            minimum=[float('inf')]*3;maximum=[-float('inf')]*3;max_root_error=0.;max_heading_error=0.;drawings=set();footprint_offenders=[]
                            density=None;detailed=None
                            for frame in range(1,count+1):
                                scene.frame_set(frame);bpy.context.view_layer.update();graph=bpy.context.evaluated_depsgraph_get()
                                evaluated_root=root.evaluated_get(graph);actual_origin=evaluated_root.matrix_world.translation.copy()
                                max_root_error=max(max_root_error,(actual_origin-origin).length)
                                expected=Vector((math.sin(ANGLES[direction]),-math.cos(ANGLES[direction]),0))
                                front=(evaluated_root.matrix_world.to_3x3()@Vector((0,-1,0))).normalized()
                                max_heading_error=max(max_heading_error,(front-expected).length)
                                meshes=_geometry(asset,graph);bounds=_bounds(meshes,actual_origin)
                                roof_names=set(asset.get('four_tile_native_entry',{}).get('nativeRoofObjects',[]))
                                for mesh in meshes:
                                    for axis in range(2):
                                        # The native pitched entry roof deliberately overhangs
                                        # its depth; support geometry receives no allowance.
                                        allowance=.12 if aid=='entry-finished' and mesh['name'] in roof_names and axis==(0 if direction in ['E','W'] else 1) else 0.
                                        lo=mesh['low'][axis]-actual_origin[axis];hi=mesh['high'][axis]-actual_origin[axis]
                                        if lo < -limits[axis]/2-allowance-tolerance or hi > limits[axis]/2+allowance+tolerance:
                                            offender={'mesh':mesh['name'],'frame':frame,'axis':axis,'actual':[lo,hi],'allowedHalfExtent':limits[axis]/2+allowance}
                                            if len(footprint_offenders)<20:footprint_offenders.append(offender)
                                for i in range(3):minimum[i]=min(minimum[i],bounds['minimum'][i]);maximum[i]=max(maximum[i],bounds['maximum'][i])
                                drawings.add(_signature(meshes,actual_origin))
                                if frame==1 and direction=='S':
                                    detailed=_signature(meshes,actual_origin,True);signatures[aid]=detailed
                                    if aid in CLUSTERS:density=_dense_evidence(meshes,actual_origin,footprint)
                                    else:
                                        row['clearance']=_entry_clearance(meshes,actual_origin)
                                        entry_meta=asset.get('four_tile_native_entry',{})
                                        roofs=[m for m in meshes if m['name'] in set(entry_meta.get('nativeRoofObjects',[]))]
                                        supports=[m for m in meshes if m['name'] in set(entry_meta.get('nativeSupportObjects',[]))]
                                        row['roofDepthOverhangAllowance']=.12
                                        row['roofBounds']=_bounds(roofs,actual_origin) if roofs else None
                                        row['supportBounds']=_bounds(supports,actual_origin) if supports else None
                                        row['supportMeshes']=[m['name'] for m in supports]
                                report['samplesChecked']+=1
                            row.update(rotatedFootprint=list(limits),bounds={'minimum':minimum,'maximum':maximum},maximumRootDisplacement=max_root_error,
                                       maximumFacingVectorError=max_heading_error,uniqueEvaluatedGeometrySamples=len(drawings))
                            if max_root_error>1e-5:row['errors'].append('Ground root moves during native clip')
                            if max_heading_error>1e-5:row['errors'].append('Evaluated root facing does not match selected atlas direction')
                            if minimum[2]<-tolerance:row['errors'].append('Geometry extends below ground: '+str(minimum[2]))
                            row['footprintOffenders']=footprint_offenders
                            if footprint_offenders:row['errors'].append('Actual world-space mesh vertices leave the allocated rotated footprint (entry roof-only depth overhang allowance .12)')
                            if maximum[2]>float(asset['height'])+tolerance:row['errors'].append('Actual geometry exceeds declared native height')
                            if aid in CLUSTERS:
                                if len(drawings)<6:row['errors'].append('Ambient has fewer than6 unique evaluated native geometry samples')
                                if density is not None:
                                    row['density']=density
                                    if density['actualComponentGroups']<12 or density['elevatedComponents']<8:row['errors'].append('Assembly lacks at least12 real component groups and8 elevated decorative components')
                                    if len(density['occupiedComponentCells'])<density['minimumOccupiedCells']:row['errors'].append('Organic composition occupies too few distinct allocated cells')
                                    if len(density['fractionalComponentCenters'])<density['minimumFractionalCenters']:row['errors'].append('Component centers remain an overly regular half-cell lattice')
                            elif direction=='S':
                                width=maximum[0]-minimum[0];row['actualWidth']=width
                                if not 3.7<=width<=4.+2*tolerance:row['errors'].append('Entry does not physically span four cells')
                                if row['clearance']['obstructionCount']:row['errors'].append('Actual mesh obstructs the two-cell-wide center passage')
                                roof_bounds=row['roofBounds'];support_bounds=row['supportBounds']
                                if not roof_bounds or roof_bounds['maximum'][0]-roof_bounds['minimum'][0]<3.7:row['errors'].append('Native roof does not span the four-cell assembly')
                                if not support_bounds or support_bounds['minimum'][0]>=-1. or support_bounds['maximum'][0]<=1.:row['errors'].append('Native supports do not occupy both outer cells around the two-cell passage')
                            row['ok']=not row['errors']
                        except Exception as exc:row['errors'].append(type(exc).__name__+': '+str(exc))
                        report['cases'].append(row);report['casesChecked']+=1
                        report['errors'].extend({'case':aid+'/'+clip+'/'+direction,'message':error} for error in row['errors'])
                report['assetsChecked']+=1
            for aid in CLUSTERS:
                if not aid.endswith('-a'):continue
                other=aid[:-1]+'b';same=signatures.get(aid)==signatures.get(other)
                row={'a':aid,'b':other,'canonicalGeometrySHA256':[signatures.get(aid),signatures.get(other)],'different':not same and aid in signatures and other in signatures}
                report['variationChecks'].append(row)
                if not row['different']:report['errors'].append({'case':aid+' vs '+other,'message':'A/B actual canonical mesh geometry is identical or unavailable'})
    except Exception as exc:report['errors'].append({'case':'audit-or-restoration','message':type(exc).__name__+': '+str(exc)})
    report['expectedSamples']=len(CLUSTERS)*4*12+(4 if include_entry else 0)
    report['ok']=not report['errors'] and report['assetsChecked']==len(ids) and report['samplesChecked']==report['expectedSamples']
    output.parent.mkdir(parents=True,exist_ok=True)
    if output.exists():
        prior=output.read_bytes();history=output.parent/'history'/hashlib.sha256(prior).hexdigest()[:16]/output.name
        history.parent.mkdir(parents=True,exist_ok=True)
        if not history.exists():history.write_bytes(prior)
    temporary=output.with_name(output.name+'.'+str(os.getpid())+'.tmp')
    temporary.write_text(json.dumps(report,indent=2)+'\n');os.replace(temporary,output)
    return report
