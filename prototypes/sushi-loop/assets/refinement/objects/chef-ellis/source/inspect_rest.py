import bpy,json
arm=bpy.data.objects['chef_ellis__armature.001'];arm.data.pose_position='REST'
for o in bpy.data.collections['S33_CHARACTER_chef_ellis.001'].all_objects:
 if o.type=='MESH' and '__image_plane' not in o.name:
  vs=[v.co for v in o.data.vertices];print(o.name,[[round(min(v[i] for v in vs),5),round(max(v[i] for v in vs),5)] for i in range(3)],[(g.name,round(sum(next((w.weight for w in v.groups if w.group==g.index),0) for v in o.data.vertices)/len(vs),3)) for g in o.vertex_groups])
