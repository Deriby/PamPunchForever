"""Review real deformations of the user's rigged GLB with its own PBR material."""
import bpy
from pathlib import Path
from mathutils import Vector
ROOT = Path(__file__).resolve().parents[2]
OUT = Path('/workspace/deliverables/pam_usuario')
OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.context.scene.render.fps = 30
bpy.ops.import_scene.gltf(filepath=str(ROOT/'assets/models/pam_usuario_rig.glb'))
rig = next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
for track in rig.animation_data.nla_tracks:
    track.mute = True
scene = bpy.context.scene
scene.render.engine='CYCLES'
scene.cycles.samples=16
scene.cycles.use_denoising=False
scene.render.resolution_x,scene.render.resolution_y=1000,1200
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.film_transparent=True
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.2,.23,.28,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.6
scene.view_settings.view_transform='AgX'
for name,position,energy,size in [('Key',(-2,-3,4),450,3),('Fill',(3,-1,2),180,2),('Rim',(0,3,3),300,2)]:
    data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.shape='DISK';data.size=size
    light=bpy.data.objects.new(name,data);scene.collection.objects.link(light);light.location=position
    light.rotation_euler=(Vector((0,0,.8))-light.location).to_track_quat('-Z','Y').to_euler()
data=bpy.data.cameras.new('Review');camera=bpy.data.objects.new('Review',data);scene.collection.objects.link(camera);scene.camera=camera;data.type='ORTHO';data.ortho_scale=2.0
for name,clip,frame,position in [('guarda','Guard',0,(2.6,-7,2.3)),('soco','Combo',17,(4.0,-5,2.0)),('joelho','KneeFlex',12,(6,-1.7,1.5))]:
    rig.animation_data.action=next(a for a in bpy.data.actions if a.id_root=='OBJECT' and a.name.startswith(clip+'_'))
    scene.frame_set(frame);bpy.context.view_layer.update()
    camera.location=position;camera.rotation_euler=(Vector((0,0,.78))-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
print('PAM_USER_RIG_RENDER_OK')
