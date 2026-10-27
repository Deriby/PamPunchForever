"""Refine combat on the supplied mesh; never edit vertices, weights or bone rest poses.

Run with Blender after rig.py, or on the distributed pam_usuario_rig.blend.
The hidden original AnimationSource is immutable, making this pass repeatable.
"""
import bpy
import hashlib
import json
import math
import struct
import sys
from pathlib import Path
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from retarget import Retargeter

bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'assets/source/pam_usuario_rig.blend'))
rig, source, body = [bpy.data.objects[n] for n in ['PamRig', 'AnimationSource', 'PamBody']]
scene = bpy.context.scene
scene.render.fps = 30
tracks = {t.name: t.strips[0].action for t in source.animation_data.nla_tracks}
for track in source.animation_data.nla_tracks:
    track.mute = True
source.hide_viewport = False
solver = Retargeter(source, rig)


def fingerprint():
    digest = hashlib.sha256()
    for vertex in body.data.vertices:
        digest.update(struct.pack('<3f', *vertex.co))
        for group in vertex.groups:
            digest.update(struct.pack('<If', group.group, group.weight))
    for bone in rig.data.bones:
        for row in bone.matrix_local:
            digest.update(struct.pack('<4f', *row))
    return digest.hexdigest()


unchanged = fingerprint()
rig.animation_data.action = None
for track in list(rig.animation_data.nla_tracks):
    rig.animation_data.nla_tracks.remove(track)
for action in list(bpy.data.actions):
    if action.name.startswith('PamUser_'):
        bpy.data.actions.remove(action)


def arm(side, wrist, direction, pole=None, stretch=1.0, fist=1.0):
    s = -1 if side == 'L' else 1
    return {'wrist': wrist, 'direction': direction,
            'pole': pole or (s*.68, .06, .58),
            'upper': 1+(stretch-1)*.30, 'fore': stretch, 'fist': fist}


def guard():
    return {'L': arm('L', (-.265, -.215, .90), (0, -.28, 1)),
            'R': arm('R', (.265, -.195, .875), (0, -.28, 1)), 'kick': 0.0}


def punch(side, beat):
    p, s = guard(), (-1 if side == 'L' else 1)
    values = {
        'load': ((s*.30, -.105, .84), (0, -.18, 1), 1.0, .98),
        'hit': ((s*.155, -.445, .925), (0, -1, .06), 1.135, 1.135),
        'follow': ((s*.10, -.402, .94), (-s*.22, -1, .09), 1.055, 1.045),
        'recoil': ((s*.29, -.16, .865), (0, -.18, 1), 1.0, .99),
    }
    wrist, direction, stretch, fist = values[beat]
    p[side] = arm(side, wrist, direction, stretch=stretch, fist=fist)
    other = 'L' if side == 'R' else 'R'
    p[other] = arm(other, (-s*.235, -.19, .94), (0, -.22, 1))
    return p


def kick(beat):
    p = guard()
    if beat in ['hit', 'follow']:
        p['R'] = arm('R', (.45, .035, .79), (.9, -.3, .2))
        p['L'] = arm('L', (-.23, -.21, .97), (0, -.28, 1))
    p['kick'] = {'load': 0.0, 'hit': 1.0, 'follow': .18, 'fold': 0.0}[beat]
    return p


def spin(beat):
    p = guard()
    if beat in ['open', 'turn1', 'turn2']:
        for s, side in [(-1, 'L'), (1, 'R')]:
            wave = .018*s if beat == 'turn1' else -.018*s
            p[side] = arm(side, (s*.64, -.035, .82+wave), (s, -.12, .08),
                          (s*.46, .30, .69), stretch=1.105, fist=1.12)
    elif beat == 'load':
        p['L'] = arm('L', (-.22, -.14, .86), (0, -.2, 1))
        p['R'] = arm('R', (.25, -.12, .82), (0, -.2, 1))
    elif beat == 'land':
        p['L'] = arm('L', (-.38, -.11, .79), (-.5, -.5, .6))
        p['R'] = arm('R', (.38, -.11, .79), (.5, -.5, .6))
    return p


def mix(a, b, t):
    w = t*t*(3-2*t)
    if isinstance(a, dict):
        return {key: mix(a[key], b[key], t) for key in a}
    if isinstance(a, tuple):
        return tuple(x*(1-w)+y*w for x, y in zip(a, b))
    return a*(1-w)+b*w


def between(a, b, weight):
    return mix(a, b, weight)


# Key time, original source time, wrist/scale breakdown. Source sampling retains
# the planted feet, torso lead, head follow-through and folded knees.
G = guard
P = punch
K = kick
S = spin
clips = {
    'Jab': [(0,0,G()), (3,4,P('R','load')), (5,5,between(P('R','load'),P('R','hit'),.48)),
            (6,6,P('R','hit')), (7,7,P('R','hit')), (10,10,P('R','follow')),
            (14,14,P('R','recoil')), (19,19,G()), (21,19,G())],
    'Cross': [(0,0,G()), (4,4,P('L','load')), (6,5,between(P('L','load'),P('L','hit'),.48)),
              (7,6,P('L','hit')), (8,7,P('L','hit')), (11,10,P('L','follow')),
              (16,14,P('L','recoil')), (22,19,G()), (23,19,G())],
    'Kick': [(0,0,G()), (6,6,K('load')), (8,8,between(K('load'),K('hit'),.45)),
             (9,9,K('hit')), (11,11,K('hit')), (15,14,K('follow')),
             (20,19,K('fold')), (27,26,G()), (30,30,G())],
    'Combo': [(0,0,G()), (4,4,P('R','load')), (5,5,between(P('R','load'),P('R','hit'),.48)),
              (6,6,P('R','hit')), (7,7,P('R','hit')), (9,10,P('R','follow')),
              (12,14,P('L','load')), (15,16,between(P('L','load'),P('L','hit'),.48)),
              (16,17,P('L','hit')), (17,18,P('L','hit')), (20,22,P('L','follow')),
              (25,29,K('load')), (29,32,between(K('load'),K('hit'),.45)),
              (30,33,K('hit')), (32,35,K('hit')), (36,39,K('follow')),
              (42,45,K('fold')), (52,53,G()), (60,59,G()), (66,66,G())],
    'Spin': [(0,0,G()), (6,6,S('load')), (9,9,S('open')), (15,15,S('turn1')),
             (21,21,S('turn2')), (27,27,S('open')), (30,30,S('land')),
             (35,35,G()), (42,42,G())],
}


def orient(name, head, tail, scale):
    rest = rig.data.bones[name]
    delta = (rest.tail_local-rest.head_local).rotation_difference(tail-head)
    rig.pose.bones[name].matrix = Matrix.LocRotScale(
        head, delta @ rest.matrix_local.to_quaternion(), Vector(scale))
    bpy.context.view_layer.update()


def solve_arm(side, spec):
    # All goals live in character space, then follow the root through the spin.
    root = rig.pose.bones['root'].matrix @ rig.data.bones['root'].matrix_local.inverted()
    upper, fore, hand = [name+'.'+side for name in ['upper_arm','forearm','hand']]
    shoulder = rig.pose.bones[upper].head.copy()
    goal, pole = [root @ Vector(spec[name]) for name in ['wrist','pole']]
    a = rig.data.bones[upper].length*spec['upper']
    b = rig.data.bones[fore].length*spec['fore']
    axis = (goal-shoulder).normalized()
    distance = max(.025, min(a+b-.002, (goal-shoulder).length))
    bend = pole-shoulder
    bend = (bend-axis*bend.dot(axis)).normalized()
    along = (a*a-b*b+distance*distance)/(2*distance)
    elbow = shoulder+axis*along+bend*math.sqrt(max(0,a*a-along*along))
    wrist = shoulder+axis*distance
    orient(upper, shoulder, elbow, (1,spec['upper'],1))
    orient(fore, elbow, wrist, (1,spec['fore'],1))
    direction = root.to_quaternion() @ Vector(spec['direction']).normalized()
    orient(hand, wrist, wrist+direction*.13, (spec['fist'],)*3)


for name, original in tracks.items():
    source.animation_data.action = original
    action = bpy.data.actions.new('PamUser_'+name)
    rig.animation_data.action = None
    keys = clips.get(name)
    end = keys[-1][0] if keys else round(original.frame_range[1])
    baked = []
    for frame in range(end+1):
        spec = None
        source_time = float(frame)
        if keys:
            left = next(i for i in range(len(keys)-1) if keys[i][0] <= frame <= keys[i+1][0])
            a, b = keys[left], keys[left+1]
            t = (frame-a[0])/(b[0]-a[0])
            source_time = a[1]+(b[1]-a[1])*t
            spec = mix(a[2],b[2],t)
        elif name == 'Guard':
            spec = G()
        scene.frame_set(math.floor(source_time), subframe=source_time%1)
        solver.retarget(name)
        if spec:
            for side in ['L','R']:
                solve_arm(side,spec[side])
            if spec['kick'] > 0:
                # Applied to the striking leg only, after support IK. Never
                # scale the resting mesh, the planted leg or a bone's rest data.
                rig.pose.bones['shin.R'].scale.y *= 1+.075*spec['kick']
                rig.pose.bones['foot.R'].scale *= 1+.055*spec['kick']
                bpy.context.view_layer.update()
        baked.append({bone.name: bone.matrix_basis.copy() for bone in rig.pose.bones})
    rig.animation_data.action = action
    for frame, pose in enumerate(baked):
        for bone in rig.pose.bones:
            bone.matrix_basis = pose[bone.name]
            bone.rotation_mode = 'QUATERNION'
            for path in ['location','rotation_quaternion','scale']:
                bone.keyframe_insert(data_path=path,frame=frame,group=bone.name)
    track = rig.animation_data.nla_tracks.new()
    track.name = name
    track.strips.new(name,0,action)
    track.mute = True
    action.use_fake_user = True
    for curve in action.fcurves:
        for key in curve.keyframe_points:
            key.interpolation = 'LINEAR'
    rig.animation_data.action = None
    print('PAM_USER_CARTOON_BAKED',name,end+1)

assert fingerprint() == unchanged, 'Bind mesh, weights and rest bones must remain identical'
source.animation_data.action = None
source.hide_viewport = True
source.hide_render = True
for bone in rig.pose.bones:
    bone.matrix_basis = Matrix.Identity(4)
scene.frame_set(0)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets/source/pam_usuario_rig.blend'),compress=True)
bpy.ops.object.select_all(action='DESELECT')
rig.select_set(True)
body.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=str(ROOT/'assets/models/pam_usuario_rig.glb'),
    export_format='GLB',export_yup=True,use_selection=True,export_skins=True,
    export_animations=True,export_animation_mode='NLA_TRACKS',export_frame_range=False)
meta_path = ROOT/'assets/source/pam_usuario_rig_metadata.json'
metadata = json.loads(meta_path.read_text())
metadata.update({'combat_revision':2,'bind_mesh_weights_rest_sha256':unchanged,
    'bind_mesh_weights_rest_unchanged':True,'arm_ik':'Baked wrist goals and elbow poles on user proportions',
    'animation_only_stretch':True,'peak_forearm_length':1.135,'peak_fist_scale':1.135,
    'effects':'Godot CombatFlourish; separate from GLB',
    'combo_impact_frames':[6,16,30],'spin_trail_frames':[9,27]})
meta_path.write_text(json.dumps(metadata,indent=2)+'\n')
print('PAM_USER_CARTOON_EXPORT_OK',unchanged)
