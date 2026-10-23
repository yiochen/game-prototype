"""Independently evaluate the actual saved native graph; no editor recipe imports."""
import sys,json,math
from pathlib import Path
sys.dont_write_bytecode=True
import bpy
P=Path(__file__).resolve().parent;scene=bpy.context.scene
obj=next(o for o in scene.objects if o.type=='MESH');material=obj.data.materials[0];tree=material.node_tree
phaseNode=next(n for n in tree.nodes if n.type=='VALUE' and 'phase' in n.name.lower())
output=next(n for n in tree.nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output)
compiled={};links={l.to_socket.as_pointer():(l.from_node.as_pointer(),list(l.from_node.outputs).index(l.from_socket)) for l in tree.links}
for n in tree.nodes:
 inputs=[]
 for s in n.inputs:
  if s.as_pointer() in links:inputs.append(('link',links[s.as_pointer()]))
  elif hasattr(s,'default_value'):
   try:v=tuple(s.default_value)
   except TypeError:v=float(s.default_value)
   inputs.append(('value',v))
  else:inputs.append(('value',None))
 compiled[n.as_pointer()]={'type':n.type,'operation':getattr(n,'operation',None),'clamp':getattr(n,'use_clamp',False),'blend':getattr(n,'blend_type',None),'inputs':inputs,'default':n.outputs[0].default_value if n.type=='VALUE' else None}
phaseKey=phaseNode.as_pointer();surface=links[output.inputs['Surface'].as_pointer()]
def evaluate(u,v,t):
 cache={}
 def get(entry):return node(*entry[1]) if entry[0]=='link' else entry[1]
 def node(nid,index):
  key=(nid,index)
  if key in cache:return cache[key]
  n=compiled[nid];kind=n['type'];inputs=n['inputs']
  if kind=='TEX_COORD':r=(u,v,0)
  elif kind=='SEPXYZ':r=get(inputs[0])[index]
  elif kind=='VALUE':r=t if nid==phaseKey else n['default']
  elif kind=='MATH':
   a=get(inputs[0]);b=get(inputs[1]);op=n['operation']
   if op=='ADD':r=a+b
   elif op=='SUBTRACT':r=a-b
   elif op=='MULTIPLY':r=a*b
   elif op=='DIVIDE':r=a/b if b else 0
   elif op=='SINE':r=math.sin(a)
   elif op=='COSINE':r=math.cos(a)
   elif op=='MAXIMUM':r=max(a,b)
   elif op=='MINIMUM':r=min(a,b)
   elif op=='SQRT':r=math.sqrt(max(a,0))
   elif op=='POWER':r=a**b if a>=0 else 0
   elif op=='EXPONENT':r=math.exp(a)
   else:raise ValueError(op)
   if n['clamp']:r=min(1,max(0,r))
  elif kind=='MIX_RGB':
   assert n['blend']=='MIX';f=min(1,max(0,get(inputs[0])));a=get(inputs[1]);b=get(inputs[2]);r=tuple(a[i]*(1-f)+b[i]*f for i in range(4))
   if n['clamp']:r=tuple(min(1,max(0,x)) for x in r)
  elif kind=='EMISSION':r=tuple(x*get(inputs[1]) for x in get(inputs[0]))
  else:raise ValueError(kind)
  cache[key]=r;return r
 return node(*surface)[:3]
def error(a,b):return max(abs(x-y) for x,y in zip(a,b))
edges={'u':0,'v':0,'corner':0};worst={};sampleCount=0
for ti in range(25):
 t=ti/24
 for i in range(33):
  z=i/32
  for axis,a,b in [('u',(0,z),(1,z)),('v',(z,0),(z,1))]:
   e=error(evaluate(*a,t),evaluate(*b,t));sampleCount+=1
   if e>edges[axis]:edges[axis]=e;worst[axis]={'coordinate':z,'phase':t,'error':e}
 corners=[evaluate(u,v,t) for u,v in [(0,0),(1,0),(1,1),(0,1)]];edges['corner']=max(edges['corner'],*(error(corners[0],c) for c in corners[1:]))
temporal=0
for x in range(17):
 for y in range(17):temporal=max(temporal,error(evaluate(x/16,y/16,0),evaluate(x/16,y/16,1)))
drivers=[]
if tree.animation_data:
 for f in tree.animation_data.drivers:drivers.append({'path':f.data_path,'index':f.array_index,'expression':f.driver.expression,'type':f.driver.type,'variables':[{'name':v.name,'type':v.type} for v in f.driver.variables]})
report={'method':'Recursive evaluation of actual saved Blender node/socket links, Math operations, MixRGB and Emission values using Python double precision; no editor recipe imported. The native graph owns UV→toroidal distances/periodic coordinate and phase warps→connected ridges/body→radiance. This tests scalar analytical values, not raster consumer success.','material':material.name,'phaseNode':phaseNode.name,'drivers':drivers,'uv':[list(loop.uv) for loop in obj.data.uv_layers.active.data],'localGeometry':[list(v.co) for v in obj.data.vertices],'evaluatedEdgeComparisons':sampleCount,'sampledPhases':25,'edgeAndCornerMaxLinearRGBError':edges,'worst':worst,'temporalPhase0Vs1MaxLinearRGBError':temporal,'limits':'Double precision graph evaluation differs from GPU float arithmetic. Actual native replay and full48 frames separately establish raster behavior. No rendered pixel patch, extra overlap or source mutation.'}
(P/'periodicity-probe.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
