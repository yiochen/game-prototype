import bpy,json
from pathlib import Path
out={}
for o in bpy.data.collections['S33_PROP_uniform35-gate'].objects:
 if o.type=='MESH' and any(n in o.name for n in ['noren_panel_1','left_paper_lantern','inner_pillar_-1','flat_roof_tile_00_-1_0','side_-1_plain_wood_field','blue_fascia']):
  out[o.name]={'vertices':[list(v.co) for v in o.data.vertices],'polygons':[list(p.vertices) for p in o.data.polygons],'matidx':[p.material_index for p in o.data.polygons],'modifiers':[{'type':m.type,**{k:getattr(m,k) for k in ['width','segments','limit_method','thickness','offset'] if hasattr(m,k)}} for m in o.modifiers],'scale':list(o.scale)}
Path(__file__).with_name('source-geometry.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out))
