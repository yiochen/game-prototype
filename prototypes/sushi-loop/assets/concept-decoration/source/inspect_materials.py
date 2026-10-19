"""Inspect the exact isolated Blender scene without changing it. Run through Blender MCP or CLI."""
import bpy,json
from pathlib import Path

def inspect(root):
 root=Path(root);man=json.loads((root/'study.json').read_text());scene=bpy.data.scenes[man['scene']]
 materials={mat for obj in scene.objects if obj.type=='MESH' for mat in obj.data.materials}
 report={'nativeProjectSHA256':man['nativeProjectSHA256'],'sourceHash':man['sourceHash'],'lightCount':sum(obj.type=='LIGHT' for obj in scene.objects),'worldStrength':next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND').inputs['Strength'].default_value,'materialCount':len(materials),'emissionSurfaces':True,'worldPositionUsesOnlyZ':True,'heightGradientCount':0}
 for mat in materials:
  nodes=mat.node_tree.nodes;out=next(n for n in nodes if n.type=='OUTPUT_MATERIAL');assert out.inputs['Surface'].links[0].from_node.type=='EMISSION'
  ramps=[n for n in nodes if n.type=='VALTORGB']
  if ramps:
   pos=next(n for n in nodes if n.type=='NEW_GEOMETRY');xyz=pos.outputs['Position'].links[0].to_node;assert xyz.type=='SEPXYZ' and [v.name for v in xyz.outputs if v.is_linked]==['Z']
   assert sum(ramps[0].color_ramp.elements[0].color[:3])<sum(ramps[0].color_ramp.elements[1].color[:3]);report['heightGradientCount']+=1
 assert report['lightCount']==0 and report['worldStrength']==0
 (root/'material-audit.json').write_text(json.dumps(report,indent=2)+'\n');return report
