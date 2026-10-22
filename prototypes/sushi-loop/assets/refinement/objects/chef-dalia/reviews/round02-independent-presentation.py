import bpy,pathlib,json,hashlib
b=pathlib.Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/chef-dalia')
def value(x):
 if x is None or isinstance(x,(float,int,str,bool)):return x
 try:return list(x)
 except:return str(x)
def graph(nt):
 if not nt:return None
 return {'nodes':[{'name':n.name,'type':n.bl_idname,'mute':n.mute,'inputs':{s.identifier:value(s.default_value) for s in n.inputs if hasattr(s,'default_value')},'outputs':{s.identifier:value(s.default_value) for s in n.outputs if hasattr(s,'default_value')},'image':n.image.name if getattr(n,'image',None) else None} for n in nt.nodes],'links':[(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in nt.links]}
r={}
for kind,path in [('source',b/'source/round-02-food/dependencies/approved-body.blend'),('candidate',b/'source/round-02.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(path));s=bpy.context.scene;c=s.camera
 r[kind]={'world':{'name':s.world.name,'color':list(s.world.color),'useNodes':s.world.use_nodes,'graph':graph(s.world.node_tree)},'lights':[{'name':o.name,'matrixWorld':[list(z) for z in o.matrix_world],'hideRender':o.hide_render,'data':{k:value(getattr(o.data,k)) for k in ['type','color','energy','shape','size','size_y','use_shadow','diffuse_factor','specular_factor','volume_factor','normalize'] if hasattr(o.data,k)}} for o in sorted(s.objects,key=lambda o:o.name) if o.type=='LIGHT'],'camera':{'name':c.name,'matrixWorld':[list(z) for z in c.matrix_world],'data':{k:value(getattr(c.data,k)) for k in ['type','ortho_scale','lens','shift_x','shift_y','clip_start','clip_end']},'dof':c.data.dof.use_dof},'render':{k:value(getattr(s.render,k)) for k in ['resolution_x','resolution_y','resolution_percentage','pixel_aspect_x','pixel_aspect_y','engine','film_transparent','use_compositing','use_sequencer']},'cycles':{k:value(getattr(s.cycles,k)) for k in ['samples','seed','use_animated_seed','device','use_denoising','max_bounces','diffuse_bounces','glossy_bounces','transmission_bounces','transparent_max_bounces']},'view':{k:value(getattr(s.view_settings,k)) for k in ['view_transform','look','exposure','gamma','use_curve_mapping']},'displayDevice':s.display_settings.display_device,'compositor':graph(getattr(s,'node_tree',None)),'libraries':[l.filepath for l in bpy.data.libraries]}
r['exactMatch']=r['source']==r['candidate'];r['packetSHA256']=hashlib.sha256((b/'candidates/round-02/packet.json').read_bytes()).hexdigest();(b/'reviews/round02-independent-presentation.json').write_text(json.dumps(r,indent=2)+'\n');print('FULL PRESENTATION EXACT MATCH',r['exactMatch'])
