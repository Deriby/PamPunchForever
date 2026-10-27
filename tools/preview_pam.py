"""Build/export Pam v3 and render the actual mesh for concept review."""
import bpy,os,math,json
from mathutils import Vector
HERE=os.path.dirname(os.path.abspath(__file__))
ROOT=os.path.dirname(HERE)
base=open(os.path.join(HERE,'build_art.py')).read().split('# Concept-led Pam generator')[0]
exec(compile(base,'build_art.py','exec'),globals())
exec(compile(open(os.path.join(HERE,'build_pam.py')).read(),'build_pam.py','exec'),globals())
os.makedirs(ROOT+'/assets/source',exist_ok=True)
os.makedirs('/workspace/deliverables/pam_v3',exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/assets/source/pam_v3.blend')
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=ROOT+'/assets/models/pam.glb',export_format='GLB',export_yup=True,export_animations=False)
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=int(os.environ.get('PAM_PREVIEW_SAMPLES','64'))
scene.cycles.use_denoising=False
scene.render.resolution_x=1000;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
scene.render.film_transparent=True
scene.world.color=(.28,.28,.28)
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.75,.79,.88,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.30
scene.view_settings.view_transform='Standard'
scene.view_settings.look='Medium High Contrast' if 'Medium High Contrast' in [] else 'None'
scene.view_settings.exposure=0;scene.view_settings.gamma=1

def light(name,loc,power,size,color):
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;data.color=color
 ob=bpy.data.objects.new(name,data);scene.collection.objects.link(ob);ob.location=loc
 ob.rotation_euler=(Vector((0,0,.95))-ob.location).to_track_quat('-Z','Y').to_euler()
light('Large softbox',(-3,-4,5),235,4.5,(1,.89,.78))
light('Soft fill',(3,-2,2.3),125,3,(.80,.87,1))
light('Rim',(1.8,2.2,3.8),200,3,(1,.83,.72))
camdata=bpy.data.cameras.new('ModelReview');cam=bpy.data.objects.new('ModelReview',camdata);scene.collection.objects.link(cam);scene.camera=cam
camdata.type='ORTHO';camdata.ortho_scale=1.98
views={'hero':(2.5,-6,2.0),'frente':(0,-6,1.45),'lado':(6,0,1.45),'costas':(0,6,1.45)}
for name,location in views.items():
 if os.environ.get('PAM_PREVIEW_VIEW') and name!=os.environ['PAM_PREVIEW_VIEW']:continue
 # Same mesh, one expressive pose for the hero and neutral orthographic views.
 for name0 in ['ArmL','ArmR','LegL','LegR','Head','Torso']:
  ob=bpy.data.objects.get(name0)
  if ob:ob.rotation_euler=(0,0,0)
 if name=='hero':
  bpy.data.objects['Head'].rotation_euler[1]=-.06
  bpy.data.objects['ArmR'].rotation_euler[0]=-.72
  bpy.data.objects['ArmL'].rotation_euler[0]=-.18
  bpy.data.objects['LegR'].rotation_euler[1]=-.07
  bpy.data.objects['LegL'].rotation_euler[1]=.09
 cam.location=location;cam.rotation_euler=(Vector((0,0,.86))-cam.location).to_track_quat('-Z','Y').to_euler()
 scene.render.filepath='/workspace/deliverables/pam_v3/'+name+'.png'
 bpy.ops.render.render(write_still=True)
print('PAM_V3_COMPLETE')
