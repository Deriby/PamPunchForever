"""Render the actual revision 06 GLB: combat poses, knees and landing."""
import bpy
import os
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
OUT = Path('/workspace/deliverables/pam_cartoon')
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.context.scene.render.fps = 30
bpy.ops.import_scene.gltf(filepath=str(ROOT / 'assets/models/pam_ps1_cartoon.glb'))
rig = next(ob for ob in bpy.context.scene.objects if ob.type == 'ARMATURE')
body = next(ob for ob in bpy.context.scene.objects if ob.type == 'MESH')
for owner in [rig, body.data.shape_keys]:
    if owner.animation_data:
        for track in owner.animation_data.nla_tracks:
            track.mute = True
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 8
scene.cycles.use_denoising = False
scene.render.resolution_x = 1000
scene.render.resolution_y = 1200
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.film_transparent = True
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[1].default_value = 0
scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'None'
data = bpy.data.cameras.new('CartoonReview')
camera = bpy.data.objects.new('CartoonReview', data)
scene.collection.objects.link(camera)
scene.camera = camera
data.type = 'ORTHO'
data.ortho_scale = 2.0

def pose(clip, frame):
    rig.animation_data.action = next(a for a in bpy.data.actions if a.id_root == 'OBJECT' and clip+'_' in a.name)
    action = next((a for a in bpy.data.actions if a.id_root == 'KEY' and clip+'_' in a.name), None)
    if action:
        body.data.shape_keys.animation_data.action = action
    scene.frame_set(frame)
    bpy.context.view_layer.update()

views = [
    ('guard', 'Guard', 0, (2.6, -7, 2.35)),
    ('jab', 'Combo', 6, (4.2, -5.0, 2.1)),
    ('cross', 'Combo', 17, (2.6, -7, 2.35)),
    ('kick', 'Combo', 33, (5.3, -3.3, 1.95)),
    ('coil', 'Spin', 6, (2.6, -7, 2.35)),
    ('spin', 'Spin', 9, (2.6, -7, 2.35)),
    ('landing', 'Spin', 30, (2.6, -7, 2.35)),
    ('knee', 'KneeFlex', 12, (6, -2.0, 1.65)),
    ('run', 'Run', 6, (4.3, -5.0, 2.1)),
]
requested = os.environ.get('PAM_CARTOON_SHOTS', '').split(',')
for name, clip, frame, position in views:
    if requested != [''] and name not in requested:
        continue
    pose(clip, frame)
    data.ortho_scale = 2.45 if name == 'spin' else 2.0
    camera.location = position
    camera.rotation_euler = (Vector((0, -.04, .77))-camera.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(OUT / (name+'.png'))
    bpy.ops.render.render(write_still=True)
print('PAM_CARTOON_RENDER_OK', [a.name for a in bpy.data.actions])
