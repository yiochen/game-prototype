import bpy,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parent;P=R.parent;bpy.ops.wm.open_mainfile(filepath=str(R/'candidate.blend'));sc=bpy.context.scene;root=bpy.data.objects['wreck-corner__root.001'];owned={root.name}|{o.name for o in root.children_recursive};geometry=[];collections=[]
def visit(c,parentHidden=False):
 hidden=parentHidden or c.hide_render;collections.append({'collection':c.name,'hideRender':c.hide_render,'effectiveHidden':hidden})
 for o in c.objects:
  if o.type in ['MESH','CURVE','FONT','SURFACE','META']:geometry.append({'name':o.name,'collection':c.name,'effectiveRenderVisible':not(hidden or o.hide_render),'owned':o.name in owned})
 for v in c.children:visit(v,hidden)
visit(sc.collection)
result={'source':'resources/candidate.blend','collectionVisibility':collections,'allGeometry':geometry,'allEffectiveVisibleGeometryOwned':all(g['owned']for g in geometry if g['effectiveRenderVisible']),'visibleOwnedCount':len({g['name']for g in geometry if g['effectiveRenderVisible']}),'rootOwns30IncludingEmpty':len(owned),'note':'Generic source audit list sceneGeometryOwners was object.hide_render-only and included hidden native control collections. This recursive effective render visibility check resolves that diagnostic; source bytes/capture remain unchanged.'}
(P/'effective-render-ownership.json').write_text(json.dumps(result,indent=2)+'\n');print(result['allEffectiveVisibleGeometryOwned'],result['visibleOwnedCount'])
