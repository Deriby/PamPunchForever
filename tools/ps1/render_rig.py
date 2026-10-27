"""Review the exported, skinned GLB and its actual animation channels."""
import bpy
import math
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
OUT = Path('/workspace/deliverables/pam_ps1_rig')
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
# glTF import converts seconds to Blender frames using the current scene rate.
bpy.context.scene.render.fps = 30
bpy.ops.import_scene.gltf(filepath=str(ROOT / 'assets/models/pam_ps1_rig.glb'))
rig = next(ob for ob in bpy.context.scene.objects if ob.type == 'ARMATURE')
body = next(ob for ob in bpy.context.scene.objects if ob.type == 'MESH')
for track in rig.animation_data.nla_tracks:
    track.mute = True
actions = {name: next(a for a in bpy.data.actions if name in a.name)
           for name in ['Guard', 'Jab', 'Cross', 'ElbowFlex', 'Run']}
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
camera_data = bpy.data.cameras.new('RigReview')
camera = bpy.data.objects.new('RigReview', camera_data)
scene.collection.objects.link(camera)
scene.camera = camera
camera_data.type = 'ORTHO'

def pose(clip, frame):
    rig.animation_data.action = actions[clip]
    scene.frame_set(frame)
    bpy.context.view_layer.update()

def shot(name, location, focus=(0, 0, .79), scale=1.85):
    camera.location = location
    camera.rotation_euler = (Vector(focus)-camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera_data.ortho_scale = scale
    scene.render.filepath = str(OUT / (name+'.png'))
    bpy.ops.render.render(write_still=True)

pose('Guard', 0)
shot('guard', (2.6, -7, 2.35))
pose('Jab', 6)
shot('jab', (6.0, -1.3, 1.85))
pose('Cross', 6)
shot('cross', (2.6, -7, 2.35))
pose('ElbowFlex', 12)
shot('elbow90', (5, -2.0, 1.65), (.36, -.11, .70), .72)
pose('ElbowFlex', 24)
shot('elbow125', (5, -2.0, 1.65), (.36, -.11, .70), .72)

# Skeleton drawn from the imported bone transforms over the actual posed mesh.
pose('Guard', 0)
bone_material = bpy.data.materials.new('ReviewBonesOnly')
bone_material.use_nodes = True
nodes = bone_material.node_tree.nodes
nodes.clear()
output = nodes.new('ShaderNodeOutputMaterial')
emission = nodes.new('ShaderNodeEmission')
emission.inputs[0].default_value = (.12, .72, .63, 1)
bone_material.node_tree.links.new(emission.outputs[0], output.inputs[0])
for bone in rig.pose.bones:
    a, b = rig.matrix_world @ bone.head, rig.matrix_world @ bone.tail
    # Move review lines towards the frontal camera so hidden joints are visible.
    a.y -= .36
    b.y -= .36
    curve = bpy.data.curves.new('Bone_'+bone.name, 'CURVE')
    curve.dimensions = '3D'
    curve.bevel_depth = .004
    curve.bevel_resolution = 0
    poly = curve.splines.new('POLY')
    poly.points.add(1)
    poly.points[0].co = (*a, 1)
    poly.points[1].co = (*b, 1)
    ob = bpy.data.objects.new('Bone_'+bone.name, curve)
    scene.collection.objects.link(ob)
    curve.materials.append(bone_material)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=.012, location=a)
    bpy.context.object.data.materials.append(bone_material)
shot('skeleton', (0, -7, 1.7))
print('PAM_RIG_RENDERS_OK', [a.name for a in actions.values()])
