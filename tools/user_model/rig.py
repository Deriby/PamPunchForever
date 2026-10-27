"""Bind the user's edited T-pose and retarget our original cartoon animations.

The supplied mesh/material identity is retained. Only a uniform gameplay scale
is applied to the rigged copy; the separate tail-free T-pose keeps source scale.
"""
import bpy
import math
import json
from pathlib import Path
from mathutils import Matrix, Vector, Quaternion

ROOT = Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'assets/source/pam_usuario_sem_rabo.blend'))
body = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
body.name = 'PamBody'
scale = 1.6/max(v.co.z for v in body.data.vertices)
body.data.transform(Matrix.Scale(scale, 4))
armature = bpy.data.armatures.new('PamUserSkeleton')
rig = bpy.data.objects.new('PamRig', armature)
bpy.context.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')

def bone(name, head, tail, parent=None, deform=True):
    item = armature.edit_bones.new(name)
    item.head = Vector(head)*scale
    item.tail = Vector(tail)*scale
    item.use_deform = deform
    if parent:
        item.parent = armature.edit_bones[parent]
        item.use_connect = (item.head-item.parent.tail).length < .000001

bone('root', (0,0,.012), (0,0,.10), deform=False)
bone('hips', (0,.005,.305), (0,.005,.405), 'root')
bone('spine', (0,.005,.405), (0,.005,.49), 'hips')
bone('chest', (0,.005,.49), (0,.005,.557), 'spine')
bone('neck', (0,.005,.557), (0,.005,.615), 'chest')
bone('head', (0,.005,.615), (0,.005,.955), 'neck')
for s, side in [(-1,'L'), (1,'R')]:
    bone('clavicle.'+side, (0,.005,.545), (s*.185,.014,.542), 'chest')
    bone('upper_arm.'+side, (s*.185,.014,.542), (s*.338,.014,.538), 'clavicle.'+side)
    bone('forearm.'+side, (s*.338,.014,.538), (s*.465,.014,.54), 'upper_arm.'+side)
    bone('hand.'+side, (s*.465,.014,.54), (s*.552,.014,.545), 'forearm.'+side)
    bone('thigh.'+side, (s*.116,.010,.29), (s*.135,.006,.145), 'hips')
    bone('shin.'+side, (s*.135,.006,.145), (s*.148,.008,.075), 'thigh.'+side)
    bone('foot.'+side, (s*.148,.008,.075), (s*.148,-.082,.037), 'shin.'+side)
    bone('toe.'+side, (s*.148,-.082,.037), (s*.148,-.157,.032), 'foot.'+side)
bpy.ops.object.mode_set(mode='OBJECT')
for item in rig.pose.bones:
    item.rotation_mode = 'QUATERNION'
rig.show_in_front = True
armature.display_type = 'OCTAHEDRAL'
bpy.ops.object.select_all(action='DESELECT')
body.select_set(True)
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
modifier = next(m for m in body.modifiers if m.type == 'ARMATURE')
modifier.use_deform_preserve_volume = False  # Same linear skinning as standard glTF.

def assign(vertex, influences):
    for group in body.vertex_groups:
        group.remove([vertex.index])
    total = sum(influences.values())
    for name, value in influences.items():
        if value > .000001:
            group = body.vertex_groups.get(name) or body.vertex_groups.new(name=name)
            group.add([vertex.index], value/total, 'REPLACE')

def segment_distance(point, bone):
    a, direction = bone.head_local, bone.tail_local-bone.head_local
    t = max(0, min(1, (point-a).dot(direction)/direction.length_squared))
    return (point-(a+direction*t)).length

unweighted = 0
for vertex in body.data.vertices:
    existing = {body.vertex_groups[g.group].name: g.weight for g in vertex.groups if g.weight > .000001}
    x, y, z = vertex.co/scale
    side = 'L' if x < 0 else 'R'
    if not existing:
        unweighted += 1
        names = [b.name for b in rig.data.bones if b.use_deform]
        if abs(x) > .21 and .43 < z < .66:
            names = [n+'.'+side for n in ['clavicle','upper_arm','forearm','hand']]
        elif z < .28:
            names = [n+'.'+side for n in ['thigh','shin','foot','toe']]
        closest = sorted([(segment_distance(vertex.co, rig.data.bones[name]), name) for name in names])[:4]
        existing = {name: 1/max(.005, distance)**4 for distance, name in closest}
        assign(vertex, existing)
    # Preserve the sculpted face as one volume; do not let shoulder weights pull
    # eyebrows/ears. Keep the collar transition separate from the facial surface.
    facial = z > .66 or (z > .565 and y < -.09 and abs(x) < .31) or (
        z > .59 and y > .155 and abs(x) < .31) or (
        z > .615 and .235 < abs(x) < .31)
    if facial or (z > .56 and existing.get('head',0) > .45):
        assign(vertex, {'head': 1})
    elif abs(x) > .487 and .45 < z < .63:
        assign(vertex, {'hand.'+side: 1})
    elif z < .09:
        toe = max(0,min(.85,(-.08-y)/.075*.85))
        assign(vertex, {'foot.'+side: 1-toe, 'toe.'+side: toe})

bpy.ops.object.select_all(action='DESELECT')
body.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.object.vertex_group_limit_total(limit=4)
bpy.ops.object.vertex_group_normalize_all(lock_active=False)
for vertex in body.data.vertices:
    assert 1 <= len(vertex.groups) <= 4
    assert abs(sum(g.weight for g in vertex.groups)-1) < .0001

# Append only our earlier animation-source armature, not the rejected character mesh.
with bpy.data.libraries.load(str(ROOT / 'assets/source/pam_ps1_cartoon.blend'), link=False) as (data_from, data_to):
    data_to.objects = ['PamRig']
source = data_to.objects[0]
source.name = 'AnimationSource'
bpy.context.collection.objects.link(source)
source_tracks = {track.name: track.strips[0].action for track in source.animation_data.nla_tracks}
for track in source.animation_data.nla_tracks:
    track.mute = True
names = ['Guard','Jab','Cross','Kick','Combo','Spin','Run','ElbowFlex','KneeFlex']
assert set(source_tracks) == set(names)
scene = bpy.context.scene
scene.render.fps = 30
scene.frame_start, scene.frame_end = 0, 66

# Bone-local twist calibration keeps the front of sleeves/gloves and shoe soles
# facing correctly when mapping the earlier lowered-arm bind to this T-pose.
correction = {}
for name in source.data.bones.keys():
    world_normal = Vector((0,0,1)) if name.startswith(('foot.','toe.')) else Vector((0,-1,0))
    a = source.data.bones[name].matrix_local.to_quaternion().inverted() @ world_normal
    b = rig.data.bones[name].matrix_local.to_quaternion().inverted() @ world_normal
    a.y, b.y = 0, 0
    correction[name] = b.normalized().rotation_difference(a.normalized())

def interpolate_matrix(a, b, weight):
    a, b = a.decompose(), b.decompose()
    return Matrix.LocRotScale(a[0].lerp(b[0],weight), a[1].slerp(b[1],weight), a[2].lerp(b[2],weight))

def plant(side, goal, weight):
    if weight < .001:
        return
    thigh, shin, foot = ['%s.%s' % (name,side) for name in ['thigh','shin','foot']]
    fk = {name:rig.pose.bones[name].matrix_basis.copy() for name in [thigh,shin,foot]}
    foot_rotation, foot_scale = rig.pose.bones[foot].matrix.to_quaternion(), rig.pose.bones[foot].matrix.to_scale()
    hip = rig.pose.bones[thigh].head.copy()
    first, second = rig.data.bones[thigh].length, rig.data.bones[shin].length
    axis = (goal-hip).normalized()
    distance = max(.01,min(first+second-.0001,(goal-hip).length))
    forward = Vector((0,-1,0))
    forward = (forward-axis*forward.dot(axis)).normalized()
    along = (first*first-second*second+distance*distance)/(2*distance)
    knee = hip+axis*along+forward*math.sqrt(max(0,first*first-along*along))
    endpoint = hip+axis*distance
    for name, head, tail in [(thigh,hip,knee),(shin,knee,endpoint)]:
        rest = rig.data.bones[name]
        delta = (rest.tail_local-rest.head_local).rotation_difference(tail-head)
        rig.pose.bones[name].matrix = Matrix.LocRotScale(head,delta@rest.matrix_local.to_quaternion(),Vector((1,1,1)))
        bpy.context.view_layer.update()
    rig.pose.bones[foot].matrix = Matrix.LocRotScale(endpoint,foot_rotation,foot_scale)
    bpy.context.view_layer.update()
    if weight < .999:
        ik = {name:rig.pose.bones[name].matrix_basis.copy() for name in [thigh,shin,foot]}
        for name in [thigh,shin,foot]:
            rig.pose.bones[name].matrix_basis = interpolate_matrix(fk[name],ik[name],weight)
        bpy.context.view_layer.update()

def retarget(clip):
    for item in rig.pose.bones:
        src = source.pose.bones[item.name]
        if item.parent:
            rest_parent = rig.data.bones[item.parent.name].matrix_local
            relative_head = rest_parent.inverted() @ item.bone.head_local
            head = item.parent.matrix @ relative_head
        else:
            head = item.bone.head_local+(src.head-source.data.bones[item.name].head_local)
        item.matrix = Matrix.LocRotScale(head,src.matrix.to_quaternion()@correction[item.name],src.matrix.to_scale())
        bpy.context.view_layer.update()
    if clip in ['ElbowFlex','KneeFlex']:
        return
    goals, weights = {}, {}
    for side in ['L','R']:
        src_foot = source.pose.bones['foot.'+side].head.copy()
        src_rest = source.data.bones['foot.'+side].head_local
        goals[side] = src_foot+rig.data.bones['foot.'+side].head_local-src_rest
        if clip in ['Guard','Jab','Cross','Run'] or (clip in ['Kick','Combo'] and side == 'L'):
            weight = 1.0
        else:
            height = max(0,src_foot.z-src_rest.z)
            weight = max(0,min(1,1-height/.055))
            weight = weight*weight*(3-2*weight)
        weights[side] = weight
    lower = 0.0
    for side in ['L','R']:
        if weights[side] < .999:
            continue
        hip = rig.pose.bones['thigh.'+side].head
        goal = goals[side]
        reach = rig.data.bones['thigh.'+side].length+rig.data.bones['shin.'+side].length-.004
        horizontal = (hip.x-goal.x)**2+(hip.y-goal.y)**2
        vertical = math.sqrt(max(.0001,reach*reach-horizontal))
        lower = max(lower,hip.z-goal.z-vertical)
    if lower > 0:
        matrix = rig.pose.bones['root'].matrix.copy()
        matrix.translation.z -= lower
        rig.pose.bones['root'].matrix = matrix
        bpy.context.view_layer.update()
    for side in ['L','R']:
        plant(side,goals[side],weights[side])

rig.animation_data_create()
for clip_name in names:
    source.animation_data.action = source_tracks[clip_name]
    action = bpy.data.actions.new('PamUser_'+clip_name)
    rig.animation_data.action = action
    end = round(source_tracks[clip_name].frame_range[1])
    for frame in range(end+1):
        scene.frame_set(frame)
        retarget(clip_name)
        for item in rig.pose.bones:
            item.rotation_mode = 'QUATERNION'
            item.keyframe_insert(data_path='location',frame=frame,group=item.name)
            item.keyframe_insert(data_path='rotation_quaternion',frame=frame,group=item.name)
            item.keyframe_insert(data_path='scale',frame=frame,group=item.name)
    track = rig.animation_data.nla_tracks.new()
    track.name = clip_name
    track.strips.new(clip_name,0,action)
    track.mute = True
    action.use_fake_user = True
    for curve in action.fcurves:
        for key in curve.keyframe_points:
            key.interpolation = 'LINEAR'
    print('PAM_USER_RETARGETED',clip_name,end+1,'frames')
rig.animation_data.action = None
source.animation_data.action = None
for item in rig.pose.bones:
    item.matrix_basis = Matrix.Identity(4)
source.hide_viewport = True
source.hide_render = True
scene.frame_set(0)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'assets/source/pam_usuario_rig.blend'),compress=True)
bpy.ops.object.select_all(action='DESELECT')
rig.select_set(True)
body.select_set(True)
bpy.context.view_layer.objects.active = rig
output = ROOT / 'assets/models/pam_usuario_rig.glb'
bpy.ops.export_scene.gltf(filepath=str(output),export_format='GLB',export_yup=True,use_selection=True,
    export_skins=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_frame_range=False)
metadata = {'base': 'User-supplied GLB, tail removed', 'normalized_height':1.6,'uniform_scale':scale,
    'bones':len(rig.data.bones),'triangles':len(body.data.polygons),'clips':names,
    'max_weight_influences':4,'automatic_heat_unweighted_repaired':unweighted,
    'weight_checks':'All vertices normalized; sculpted face and glove/shoe regions protected',
    'bind_pose':'T-pose','facial_morphs_added':False,'original_pbr_images_preserved':True,
    'animation_method':'Retargeted bone orientations with twist calibration and new leg support IK'}
(ROOT / 'assets/source/pam_usuario_rig_metadata.json').write_text(json.dumps(metadata,indent=2))
print('PAM_USER_RIG_EXPORTED_OK',json.dumps(metadata))
