"""Render the edited GLB itself with the original PBR material, no paint-over."""
import bpy
import os
from pathlib import Path
from mathutils import Vector
ROOT = Path(__file__).resolve().parents[2]
OUT = Path('/workspace/deliverables/pam_usuario')
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
original = os.environ.get('PAM_USER_RENDER_ORIGINAL') == '1'
model_path = 'assets/source/pam_usuario_original.glb' if original else 'assets/models/pam_usuario_sem_rabo.glb'
bpy.ops.import_scene.gltf(filepath=str(ROOT / model_path))
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 24
scene.cycles.use_denoising = False
scene.render.resolution_x, scene.render.resolution_y = 1200, 1400
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = True
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.2, .23, .28, 1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .6
scene.view_settings.view_transform = 'AgX'
for name, position, energy, size in [('Key', (-2,-3,4), 450, 3), ('Fill',(3,-1,2),180,2), ('Rim',(0,3,3),300,2)]:
    data = bpy.data.lights.new(name, 'AREA')
    data.energy, data.shape, data.size = energy, 'DISK', size
    light = bpy.data.objects.new(name, data)
    scene.collection.objects.link(light)
    light.location = position
    light.rotation_euler = (Vector((0,0,.6))-light.location).to_track_quat('-Z','Y').to_euler()
data = bpy.data.cameras.new('Review')
camera = bpy.data.objects.new('Review', data)
scene.collection.objects.link(camera)
scene.camera = camera
data.type = 'ORTHO'
views = [('com_rabo_lado',(4,0,1.2),1.25)] if original else [('sem_rabo_lado',(4,0,1.2),1.25), ('sem_rabo_costas',(0,4,1.2),1.6)]
for name, position, scale in views:
    data.ortho_scale = scale
    camera.location = position
    camera.rotation_euler = (Vector((0,0,.52))-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath = str(OUT / (name+'.png'))
    bpy.ops.render.render(write_still=True)
print('PAM_USER_TAIL_RENDER_OK')
