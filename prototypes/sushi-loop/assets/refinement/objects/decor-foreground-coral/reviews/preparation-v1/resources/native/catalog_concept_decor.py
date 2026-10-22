"""Translate the approved concept-derived study into stable production IDs."""
import bpy,importlib.util,math
from pathlib import Path
spec=importlib.util.spec_from_file_location('s33_concept_geometry',Path(__file__).with_name('concept_decoration_geometry.py'))
core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
MAP={'boulder-underwater':'cobalt-crags','decor-background-rock':'cobalt-shelf','decor-foreground-rock':'cobalt-shelf','column-broken':'pale-column','decor-ruin-fragment':'reef-face','decor-foreground-coral':'pink-coral','decor-midground-coral':'pink-coral','decor-kelp':'kelp-fan'}

def create(aid):
    ident=MAP[aid];design=next(x for x in core.DESIGNS if x[0]==ident)
    piece=core.Piece(bpy.context.scene,'S33 production concept',ident,design[4]);piece.build()
    root=piece.root
    def pose(clip,t):
        # Kelp/coral sway is native mesh rotation; rooted rock/footing stays still.
        for obj in piece.parts:
            if obj.get('studyRole')=='vegetation':
                obj.rotation_euler.y=.025*math.sin(t*math.tau+len(obj.name)*.23) if clip!='static' else 0
    animated=aid in ('decor-kelp','decor-foreground-coral','decor-midground-coral')
    clips={'idle':{'frames':12,'fps':12,'loop':True}} if animated else {'static':{'frames':1,'fps':12,'loop':False,'static':True}}
    a={'root':root,'collection':piece.col,'parts':{o.name:o for o in piece.parts},'footprint':[1,1],'height':design[4],'sockets':{},'clips':clips,'pose':pose,'reset':lambda:pose('static',0),'directions':['N','E','S','W'],'conceptReference':ident,'notes':[design[6]]}
    # Select by largest complete 70% silhouette, never S-facing alone.
    points=[o.matrix_world@v.co for o in piece.parts for v in o.data.vertices]
    # Newly linked transforms must be evaluated before measurement.
    bpy.context.view_layer.update();points=[o.matrix_world@v.co for o in piece.parts for v in o.data.vertices]
    rise=max(max(-p.y-.7*p.z for p in points)-min(-p.y-.7*p.z for p in points),max(-p.x-.7*p.z for p in points)-min(-p.x-.7*p.z for p in points),max(p.y-.7*p.z for p in points)-min(p.y-.7*p.z for p in points),max(p.x-.7*p.z for p in points)-min(p.x-.7*p.z for p in points))
    a['camera_elevation_degrees']=35 if rise>2 else None
    a['squareFooting']=rise>2
    return a
