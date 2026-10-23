"""Independently evaluate the actual saved native graph; no editor recipe imports."""
import sys,json,math
from pathlib import Path
sys.dont_write_bytecode=True
import bpy
P=Path(__file__).resolve().parent;scene=bpy.context.scene
obj=next(o for o in scene.objects if o.type=='MESH');material=obj.data.materials[0];tree=material.node_tree
phaseNode=next(n for n in tree.nodes if n.type=='VALUE' and 'phase' in n.name.lower())
output=next(n for n in tree.nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output)
def evaluate(u,v,t):
 cache={}
 def get(socket):
  if socket.is_linked:return node(socket.links[0].from_node,socket.links[0].from_socket)
  value=socket.default_value
  try:return tuple(value)
  except TypeError:return float(value)
 def node(n,socket):
  key=(n.as_pointer(),socket.as_pointer())
  if key in cache:return cache[key]
  if n.type=='TEX_COORD':assert socket.name=='UV';r=(u,v,0)
  elif n.type=='SEPXYZ':r=get(n.inputs[0])[list(n.outputs).index(socket)]
  elif n.type=='VALUE':r=t if n==phaseNode else n.outputs[0].default_value
  elif n.type=='MATH':
   a=get(n.inputs[0]);b=get(n.inputs[1]);op=n.operation
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
   if n.use_clamp:r=min(1,max(0,r))
  elif n.type=='MIX_RGB':
   assert n.blend_type=='MIX';f=min(1,max(0,get(n.inputs[0])));a=get(n.inputs[1]);b=get(n.inputs[2]);r=tuple(a[i]*(1-f)+b[i]*f for i in range(4))
   if n.use_clamp:r=tuple(min(1,max(0,x)) for x in r)
  elif n.type=='EMISSION':r=tuple(x*get(n.inputs[1]) for x in get(n.inputs[0]))
  else:raise ValueError(n.type)
  cache[key]=r;return r
 return get(output.inputs['Surface'])[:3]
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
