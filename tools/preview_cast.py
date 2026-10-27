"""Render actual exported game meshes, with the approved Pam preserved."""
import bpy,os,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=Path('/workspace/deliverables/style_pass');OUT.mkdir(parents=True,exist_ok=True)
keys=os.environ.get('PAM_CAST_KEYS','jaburanga,assassin,guardian,guardian_scout').split(',')
for key in keys:
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 bpy.ops.import_scene.gltf(filepath=str(ROOT/'assets/models'/f'{key}.glb'))
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=int(os.environ.get('PAM_ART_SAMPLES','48'));scene.cycles.use_denoising=False
 scene.render.resolution_x=950;scene.render.resolution_y=1150;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.film_transparent=True
 scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.77,.81,.88,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.35
 scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
 def light(name,loc,power,size,color):
  data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;data.color=color;ob=bpy.data.objects.new(name,data);scene.collection.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector((0,0,1))-ob.location).to_track_quat('-Z','Y').to_euler()
 light('Key',(-3,-4,5),260,4.5,(1,.91,.80));light('Fill',(3,-3,2.8),190,3,(.83,.89,1));light('Rim',(2,2,4),250,3,(1,.85,.73))
 data=bpy.data.cameras.new('Review');cam=bpy.data.objects.new('Review',data);scene.collection.objects.link(cam);scene.camera=cam;data.type='ORTHO';data.ortho_scale=2.15 if key in ['jaburanga','assassin'] else 1.88
 target=Vector((-.03,0,.91 if key in ['jaburanga','assassin'] else .75));cam.location=(2.6,-7,2.5);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
 scene.render.filepath=str(OUT/f'{key}.png');bpy.ops.render.render(write_still=True)
 if key=='jaburanga':
  cam.location=(2,6,2.2);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/'jaburanga_back.png');bpy.ops.render.render(write_still=True)
print('CAST_PREVIEWS_COMPLETE')
