"""Review the exported original PS1-oriented mesh, without remeshing or paint-over."""
import bpy,os,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];OUT=Path('/workspace/deliverables/pam_ps1');OUT.mkdir(exist_ok=True,parents=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(ROOT/'assets/models/pam_ps1_estudo.glb'))
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=8;scene.cycles.use_denoising=False
scene.render.resolution_x=1000;scene.render.resolution_y=1200;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.film_transparent=True
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[1].default_value=0
scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
camdata=bpy.data.cameras.new('Review');cam=bpy.data.objects.new('Review',camdata);scene.collection.objects.link(cam);scene.camera=cam;camdata.type='ORTHO';camdata.ortho_scale=1.85
for name,position in {'hero':(2.6,-7,2.4),'frente':(0,-6,1.5),'lado':(6,0,1.5),'costas':(0,6,1.5),'corrida':(2.6,-7,2.4),'soco':(2.6,-7,2.4)}.items():
 if os.environ.get('PAM_PS1_VIEW') and name!=os.environ['PAM_PS1_VIEW']:continue
 for node in ['ArmL','ArmR','LegL','LegR','Head','Torso']:
  ob=bpy.data.objects.get(node)
  if ob:ob.rotation_euler=(0,0,0)
 if name=='hero':
  bpy.data.objects['Head'].rotation_euler[1]=-.045
  bpy.data.objects['ArmR'].rotation_euler[0]=-.65
  bpy.data.objects['ArmL'].rotation_euler[0]=-.19
  bpy.data.objects['LegR'].rotation_euler[1]=-.08
  bpy.data.objects['LegL'].rotation_euler[1]=.10
 if name=='corrida':
  bpy.data.objects['ArmR'].rotation_euler[0]=-.85
  bpy.data.objects['ArmL'].rotation_euler[0]=.85
  bpy.data.objects['LegR'].rotation_euler[0]=.7
  bpy.data.objects['LegL'].rotation_euler[0]=-.7
  bpy.data.objects['Torso'].rotation_euler[0]=.12
 if name=='soco':
  bpy.data.objects['ArmR'].rotation_euler[0]=-1.48
  bpy.data.objects['ArmL'].rotation_euler[0]=-.6
  bpy.data.objects['Head'].rotation_euler[1]=-.09
 cam.location=position;cam.rotation_euler=(Vector((0,0,.79))-cam.location).to_track_quat('-Z','Y').to_euler()
 scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
if not os.environ.get('PAM_PS1_VIEW'):
 for name0 in ['ArmL','ArmR','LegL','LegR','Head','Torso']:
  ob=bpy.data.objects.get(name0)
  if ob:ob.rotation_euler=(0,0,0)
 wiremat=bpy.data.materials.new('TopologyReview');wiremat.use_nodes=True
 nodes=wiremat.node_tree.nodes;nodes.clear();out=nodes.new('ShaderNodeOutputMaterial');em=nodes.new('ShaderNodeEmission');em.inputs[0].default_value=(.07,.18,.20,1);wiremat.node_tree.links.new(em.outputs[0],out.inputs[0])
 for ob in list(scene.objects):
  if ob.type!='MESH':continue
  cp=ob.copy();cp.data=ob.data.copy();scene.collection.objects.link(cp);cp.data.materials.clear();cp.data.materials.append(wiremat)
  mod=cp.modifiers.new('TriangleWire','WIREFRAME');mod.thickness=.0013;mod.use_replace=True
 cam.location=(2.6,-7,2.4);cam.rotation_euler=(Vector((0,0,.79))-cam.location).to_track_quat('-Z','Y').to_euler()
 scene.render.filepath=str(OUT/'wire.png');bpy.ops.render.render(write_still=True)
print('PS1_PREVIEW_COMPLETE')
