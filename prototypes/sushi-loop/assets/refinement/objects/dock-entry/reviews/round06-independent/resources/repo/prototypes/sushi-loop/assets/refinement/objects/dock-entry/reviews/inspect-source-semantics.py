import bpy,json
from pathlib import Path
OUT=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/dock-entry/reviews')
c=bpy.data.collections['S33_PROP_dock-entry.001'];sc=bpy.context.scene
r={'blend':bpy.data.filepath,'scene':sc.name,'originalSavedCollectionVisibility':{'name':c.name,'hideRender':c.hide_render,'hideViewport':c.hide_viewport},'originalSavedLayerVisibility':[],'ownedObjects':[],'ownedMaterials':[]}
def layer(lc):
 if lc.collection==c:r['originalSavedLayerVisibility'].append({'viewLayer':vl.name,'exclude':lc.exclude,'hideViewport':lc.hide_viewport})
 for child in lc.children:layer(child)
for vl in sc.view_layers:layer(vl.layer_collection)
mats=set()
for o in c.all_objects:
 ad=o.animation_data;r['ownedObjects'].append({'name':o.name,'type':o.type,'savedHideRender':o.hide_render,'savedHideViewport':o.hide_viewport,'scale':list(o.scale),'animation':None if ad is None else {'action':ad.action.name if ad.action else None,'drivers':len(ad.drivers),'nlaTracks':len(ad.nla_tracks)},'constraints':[{'name':x.name,'type':x.type} for x in o.constraints],'uvLayers':[uv.name for uv in o.data.uv_layers] if o.type=='MESH' else []})
 if o.type=='MESH':mats.update(m for m in o.data.materials if m)
for m in mats:
 r['ownedMaterials'].append({'name':m.name,'textures':[{'node':n.name,'image':n.image.name if n.image else None,'packed':bool(n.image.packed_file) if n.image else None} for n in m.node_tree.nodes if n.type=='TEX_IMAGE'],'shaderOperations':[{'name':n.name,'type':n.type,'operation':getattr(n,'operation',None),'dataType':getattr(n,'data_type',None),'blendType':getattr(n,'blend_type',None),'interpolation':getattr(n,'interpolation_type',None)} for n in m.node_tree.nodes],'links':[{'from':[l.from_node.name,l.from_socket.name],'to':[l.to_node.name,l.to_socket.name]} for l in m.node_tree.links]})
(OUT/'own-saved-source-semantics.json').write_text(json.dumps(r,indent=2)+'\n')
