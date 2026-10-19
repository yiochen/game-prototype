"""Independent saved-project audit; run with background Blender, never live MCP.

Blender -b PROJECT --python audit_native.py -- --records SOURCE_RECORD_ROOT
  --output REPORT [--reference BASELINE_REPORT] [--baseline]
Only REPORT is written. Geometry, native action curves, UVs, representative
native poses, linked surface graphs and selected Faceted settings are inspected.
"""
import argparse, hashlib, importlib.util, json, math, sys
from pathlib import Path
import bpy

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[4]
BASE=REPO/'prototypes/sushi-loop/assets/production/source/blender'

def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def plain(value):
 if isinstance(value,(bool,str,int)) or value is None:return value
 if isinstance(value,float):return round(value,7)
 try:return [plain(v) for v in value]
 except TypeError:return str(value)
def socket(s):return plain(s.default_value) if hasattr(s,'default_value') else None

def graph(node):
 pending=[node] if node else [];seen={};links=[]
 while pending:
  current=pending.pop()
  if current.name in seen:continue
  value={'type':current.type,'operation':getattr(current,'operation',None),'blendType':getattr(current,'blend_type',None),'inputs':[socket(s) if not s.is_linked else '<linked>' for s in current.inputs]}
  if current.type=='VALUE':value['value']='<native-deck-phase>' if current.label=='Deck travel phase' else socket(current.outputs[0])
  if current.type=='TEX_IMAGE':
   image=current.image;value['image']={'name':image.name,'size':list(image.size),'packedSHA256':hashlib.sha256(image.packed_file.data).hexdigest() if image.packed_file else None} if image else None
  if current.type=='VALTORGB':value['ramp']={'interpolation':current.color_ramp.interpolation,'elements':[[plain(e.position),plain(e.color)] for e in current.color_ramp.elements]}
  seen[current.name]=value
  for index,s in enumerate(current.inputs):
   for link in s.links:
    links.append([current.name,index,link.from_node.name,list(link.from_node.outputs).index(link.from_socket)]);pending.append(link.from_node)
 return {'nodes':seen,'links':sorted(links)}

def lower_node(material):
 return next((n for n in material.node_tree.nodes if n.type=='MIX_RGB' and n.blend_type=='MULTIPLY' and n.inputs[2].is_linked and n.inputs[2].links[0].from_node.type=='VALTORGB'),None)

def reachable_shader(material):
 output=next(n for n in material.node_tree.nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output)
 active=graph(output);types=[n['type'] for n in active['nodes'].values()]
 principle=[n for n in material.node_tree.nodes if n.type=='BSDF_PRINCIPLED' and n.name in active['nodes']]
 return active,types,principle

def material_record(m):
 active,types,principled=reachable_shader(m);lower=lower_node(m)
 out={'name':m.name,'flatImageGen':bool(m.get('sprite_source')),'surfaceTypes':sorted(types),'activeGraphSHA256':digest(active),'activeGraph':active,'lowerGraph':graph(lower),'lowerGraphSHA256':digest(graph(lower)) if lower else None,'baseColor':socket(lower.inputs[1]) if lower else None,'principled':[]}
 for n in principled:
  base=n.inputs['Base Color'];upstream=graph(base.links[0].from_node) if base.is_linked else None
  out['principled'].append({'name':n.name,'roughness':socket(n.inputs['Roughness']),'specular':socket(n.inputs['Specular IOR Level']),'metallic':socket(n.inputs['Metallic']),'emission':socket(n.inputs['Emission Strength']),'lowerDirect':bool(lower and base.is_linked and base.links[0].from_node==lower),'baseGraphSHA256':digest(upstream),'baseConstant':socket(base),'obsoleteViewToneActive':bool(upstream and any(n['type']=='VECT_MATH' and n.get('operation')=='DOT_PRODUCT' for n in upstream['nodes'].values()))})
 return out

def fcurves(action):
 result=[]
 for layer in action.layers:
  for strip in layer.strips:
   for bag in getattr(strip,'channelbags',[]):result.extend(bag.fcurves)
 if not result:result=list(getattr(action,'fcurves',[]))
 return result

def action_hash(action):
 return digest([{'path':c.data_path,'index':c.array_index,'extrapolation':c.extrapolation,'keys':[[plain(k.co),k.interpolation,plain(k.handle_left),plain(k.handle_right),k.handle_left_type,k.handle_right_type] for k in c.keyframe_points]} for c in sorted(fcurves(action),key=lambda c:(c.data_path,c.array_index))])

def mesh_hash(o):
 mesh=o.data
 data={'v':[plain(v.co) for v in mesh.vertices],'faces':[list(p.vertices) for p in mesh.polygons],'materials':[p.material_index for p in mesh.polygons],'uv':{layer.name:[plain(v.uv) for v in layer.data] for layer in mesh.uv_layers},'shapes':{key.name:[plain(v.co) for v in key.data] for key in mesh.shape_keys.key_blocks} if mesh.shape_keys else {}}
 return digest(data)

def lighting(scene):
 return sorted([{'name':o.name,'type':o.data.type,'energy':plain(o.data.energy),'size':plain(o.data.size),'shape':o.data.shape,'color':plain(o.data.color),'location':plain(o.location),'rotation':plain(o.rotation_euler),'matrix':plain(o.matrix_world)} for o in scene.objects if o.type=='LIGHT'],key=lambda v:v['name'])

def grade(scene):
 ng=scene.compositing_node_group
 if ng is None:return None
 layers=[n for n in ng.nodes if n.type=='R_LAYERS'];combine=next((n for n in ng.nodes if n.bl_idname=='CompositorNodeCombineColor'),None)
 alpha=combine.inputs['Alpha'].links[0] if combine and combine.inputs['Alpha'].is_linked else None
 return {'enabled':scene.render.use_compositing,'factor':ng.get('contrastFactor'),'owners':[n.scene.name if n.scene else None for n in layers],'ownerCorrect':all(n.scene==scene for n in layers),'alphaBypassesRGB':bool(alpha and alpha.from_node in layers and alpha.from_socket.name=='Alpha'),'math':[{'operation':n.operation,'factor':socket(n.inputs[1]),'offset':socket(n.inputs[2]),'clamp':n.use_clamp} for n in ng.nodes if n.type=='MATH']}

def close(a,b,tol=1e-6):return len(a)==len(b) and all(abs(x-y)<tol for x,y in zip(a,b))
def same(a,b,tol=2e-6):
 if isinstance(a,(int,float)) and isinstance(b,(int,float)):return abs(a-b)<=tol
 if isinstance(a,dict) and isinstance(b,dict):return set(a)==set(b) and all(same(a[k],b[k],tol) for k in a)
 if isinstance(a,list) and isinstance(b,list):return len(a)==len(b) and all(same(x,y,tol) for x,y in zip(a,b))
 return a==b
def srgb(color):
 vals=[int(color[i:i+2],16)/255 for i in (1,3,5)];return [v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in vals]+[1]

def main(args):
 worker=load('s33_independent_faceted_worker',BASE/'capture_worker.py');native=load('s33_independent_faceted_actions',BASE/'native_actions.py');scene=worker.native_scene()
 ids=sorted(json.loads((args.records/'index.json').read_text())['assetIds']) if (args.records/'index.json').exists() else sorted(p.parent.name for p in args.records.glob('*/asset.json'))
 old=json.loads(args.reference.read_text()) if args.reference else None
 report={'project':str(Path(bpy.data.filepath)),'projectSHA256':sha(bpy.data.filepath),'baseline':args.baseline,'floorAlbedoCalibration':args.floor_calibration,'blenderVersion':bpy.app.version_string,'issues':[],'assets':{},'materials':{},'actions':{},'scenes':[s.name for s in bpy.data.scenes],'grade':grade(scene),'lights':lighting(scene),'worldStrength':[socket(n.inputs['Strength']) for n in scene.world.node_tree.nodes if n.type=='BACKGROUND']}
 check=lambda ok,msg:report['issues'].append(msg) if not ok else None
 check(report['grade'] and report['grade']['factor']==1.35 and report['grade']['ownerCorrect'] and report['grade']['alphaBypassesRGB'],'Bad native135 compositor/owner/alpha')
 check(len(report['grade']['math'])==3 and all(n['operation']=='MULTIPLY_ADD' and abs(n['factor']-1.35)<1e-6 and abs(n['offset']+.175)<1e-6 and n['clamp'] for n in report['grade']['math']),'Actual compositor channel math differs')
 check(report['worldStrength']==[0.],'Nonzero world strength')
 if not args.baseline:
  lamps=[l for l in report['lights'] if l['energy']>0];check(len(lamps)==5,'Expected exactly five enabled Faceted lamps')
  expected=[([0,0,4.5],140,3.5),([3,0,1.8],100,4),([0,3,1.8],100,4),([-3,0,1.8],100,4),([0,-3,1.8],100,4)]
  for position,power,size in expected:
   matches=[l for l in lamps if close(l['location'],position)];check(len(matches)==1,'Missing/duplicate lamp at '+str(position))
   if matches:
    l=matches[0];check(l['type']=='AREA' and l['shape']=='DISK' and l['energy']==power and l['size']==size and close(l['color'],[1,1,1]),'Wrong lamp '+l['name'])
    from mathutils import Vector
    aim=(Vector((0,0,.8))-Vector(position)).normalized();forward=Vector((0,0,-1));from mathutils import Euler
    forward.rotate(Euler(l['rotation']));check((aim-forward).length<1e-5,'Wrong lamp direction '+l['name'])
 for aid in ids:
  asset,rig,_=worker.reconstruct(aid,args.records,{},scene);worker.show_only(scene,asset);objects=list(asset['collection'].all_objects)
  spatial={k:asset[k] for k in ('id','frame','anchor','scale','projection','footprint','height','squareFooting','camera_elevation_degrees','directions','facingPolicy','sockets','ports','flow','locomotion','variants','supportLayout','depth_layer','composition_context') if k in asset}
  entry={'spatialMetadata':spatial,'rigSHA256':sha(args.records/aid/'rig.json'),'objects':{},'poses':{},'deckPhaseSamples':{},'materialSlots':{},'cameraSpatial':{k:v for k,v in json.loads((args.records/aid/'camera.json').read_text()).items() if k not in ('artStyle','name')}}
  for o in objects:
   entry['objects'][o.name]={'type':o.type,'parent':o.parent.name if o.parent else None,'geometrySHA256':mesh_hash(o) if o.type=='MESH' else None,'bonesSHA256':digest([{'name':b.name,'head':plain(b.head_local),'tail':plain(b.tail_local),'matrix':plain(b.matrix_local),'parent':b.parent.name if b.parent else None} for b in o.data.bones]) if o.type=='ARMATURE' else None}
   for index,slot in enumerate(o.material_slots if o.type=='MESH' else []):
    m=slot.material
    if not m:continue
    key=o.name+':'+str(index);entry['materialSlots'][key]=m.name
    if m.name not in report['materials']:report['materials'][m.name]=material_record(m)
  for clip,recipe in rig['clips'].items():
   for owner in recipe['actions']:
    action=bpy.data.actions.get(owner['action']);check(action is not None,aid+': missing action '+owner['action'])
    if action:report['actions'][action.name]=action_hash(action)
   count=int(recipe['frames']);check(count==1 or count>=6,aid+'/'+clip+': too few frames')
   for frame in sorted({1,1+count//2,count}):
    for facing in asset.get('directions',['N','E','S','W']):
     native.apply_clip(asset,rig,clip,frame=frame,direction=facing,scene=scene)
     with worker.capture_footing(asset):
      dg=bpy.context.evaluated_depsgraph_get();pose=[]
      for o in sorted(objects,key=lambda o:o.name):
       if o.type!='MESH' or o.hide_render:continue
       ev=o.evaluated_get(dg);mesh=ev.to_mesh()
       try:pose.append([o.name,[plain(ev.matrix_world@v.co) for v in mesh.vertices]])
       finally:ev.to_mesh_clear()
      entry['poses'][clip+'/'+facing+'/'+str(frame)]=digest(pose)
  if aid.startswith('belt-'):
   used={slot.material for o in objects if o.type=='MESH' for slot in o.material_slots if slot.material}
   decks=[(m,n) for m in used for n in m.node_tree.nodes if n.type=='VALUE' and n.label=='Deck travel phase']
   check(len(decks)==1,aid+': expected exact one animated deck owner')
   for clip,recipe in rig['clips'].items():
    count=int(recipe['frames']);samples=[]
    for frame in range(1,count+2):
     native.apply_clip(asset,rig,clip,frame=frame,direction='S',scene=scene)
     values=[socket(n.outputs[0]) for m,n in decks];samples.append(values)
     check(all(abs(value+7*(frame-1)/count)<2e-6 for value in values),aid+'/'+clip+': wrong native deck phase at '+str(frame))
    entry['deckPhaseSamples'][clip]=samples
  report['assets'][aid]=entry
  if old:
   before=old['assets'].get(aid);check(before is not None,aid+': not in baseline')
   if before:
    for key in ('spatialMetadata','rigSHA256','objects','poses','cameraSpatial'):
     check(entry[key]==before[key],aid+': changed '+key)
    check(set(entry['materialSlots'])==set(before['materialSlots']),aid+': material slot set differs')
    for slot,name in entry['materialSlots'].items():
     old_name=before['materialSlots'].get(slot)
     if old_name is None:continue
     m=report['materials'][name];previous=old['materials'][old_name];prefix=aid+'/'+slot
     if previous['flatImageGen']:
      check(m['flatImageGen'] and m['activeGraphSHA256']==previous['activeGraphSHA256'],prefix+': changed flat held-food shader');continue
     check(len(m['principled'])==1,prefix+': expected one active Principled')
     if not m['principled']:continue
     shader=m['principled'][0];iswood=aid=='crate-wood' and 'wood' in old_name.lower();israil=aid.startswith('belt-') and 'S33_FB_red' in old_name
     check(shader['metallic']==0 and shader['emission']==0 and not shader['obsoleteViewToneActive'],prefix+': metallic/emission/old view-tone remains')
     check(shader['roughness']==(1 if iswood or israil else .85) and shader['specular']==(0 if iswood or israil else .03),prefix+': wrong matte finish')
     if previous['lowerGraphSHA256']:
      check(shader['lowerDirect'],prefix+': lower graph is not active Base Color')
      expected=json.loads(json.dumps(previous['lowerGraph']));lower=lower_node(bpy.data.materials[name])
      if iswood or israil:
       for node in expected['nodes'].values():
        if node['type']=='MIX_RGB' and node['blendType']=='MULTIPLY' and node['inputs'][2]=='<linked>':
         value=node['inputs'][1]
         if isinstance(value,list):node['inputs'][1]=[round(c*.42,7) for c in value[:3]]+[1] if iswood else plain(srgb('#966B60'))
      check(same(m['lowerGraph'],expected),prefix+': unexpected lower/base graph changes')
     else:
      emissions=[(name,node) for name,node in previous['activeGraph']['nodes'].items() if node['type']=='EMISSION']
      if len(emissions)==1:
       emission_name,emission=emissions[0];old_color=emission['inputs'][0]
       floor=aid.startswith('floor-') or aid=='dock-floor'
       if old_color!='<linked>':
        if floor:old_color=[round(v*args.floor_calibration,7) for v in old_color[:3]]+[old_color[3]]
        check(shader['baseGraphSHA256']==digest(None) and same(shader['baseConstant'],old_color),prefix+': floor/base constant changed')
       else:
        links=previous['activeGraph']['links'];source=next(l[2] for l in links if l[0]==emission_name and l[1]==0);pending=[source];upstream={}
        while pending:
         node=pending.pop()
         if node in upstream:continue
         upstream[node]=previous['activeGraph']['nodes'][node];pending.extend(l[2] for l in links if l[0]==node)
        subgraph={'nodes':upstream,'links':[l for l in links if l[0] in upstream]}
        check(shader['baseGraphSHA256']==digest(subgraph),prefix+': floor/base procedural graph changed')
  print('FACETED_AUDIT '+aid,flush=True)
 if old:
  check(set(report['assets'])==set(old['assets']),'Native asset set changed')
  check(report['actions']==old['actions'],'Native action curves changed')
 report['summary']={'assets':len(report['assets']),'materials':len(report['materials']),'independentActions':len(report['actions']),'poseFacingSamples':sum(len(a['poses']) for a in report['assets'].values()),'geometryAndActionsComparedToBaseline':bool(old)}
 report['passed']=not report['issues'];args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':report['passed'],'summary':report['summary'],'issues':report['issues'],'output':str(args.output)}),flush=True)
 if not report['passed']:sys.exit(1)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--records',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--reference',type=Path);p.add_argument('--baseline',action='store_true');p.add_argument('--floor-calibration',type=float,default=1);args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []);main(args)
