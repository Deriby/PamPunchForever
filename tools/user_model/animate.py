"""Refine combat without editing the supplied geometry or bone rest poses.

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
from mathutils import Matrix, Vector, Euler

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from retarget import Retargeter
from hands import protect_hands

bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'assets/source/pam_usuario_rig.blend'))
rig, source, body = [bpy.data.objects[n] for n in ['PamRig', 'AnimationSource', 'PamBody']]
scene = bpy.context.scene
scene.render.fps = 30
tracks = {t.name: t.strips[0].action for t in source.animation_data.nla_tracks}
for track in source.animation_data.nla_tracks:
    track.mute = True
source.hide_viewport = False
solver = Retargeter(source, rig)
combat = json.loads((ROOT/'resources/combat_moves.tres').read_text().split('data = ',1)[1])


def fingerprint(weights=True):
    digest = hashlib.sha256()
    for vertex in body.data.vertices:
        digest.update(struct.pack('<3f', *vertex.co))
        if weights:
            for group in vertex.groups:
                digest.update(struct.pack('<If', group.group, group.weight))
    for bone in rig.data.bones:
        for row in bone.matrix_local:
            digest.update(struct.pack('<4f', *row))
    return digest.hexdigest()


geometry_rest_before = fingerprint(weights=False)
hand_weights = protect_hands(body, 1.5385457161116158)
unchanged = fingerprint()
rig.animation_data.action = None
for track in list(rig.animation_data.nla_tracks):
    rig.animation_data.nla_tracks.remove(track)
for action in list(bpy.data.actions):
    if action.name.startswith('PamUser_'):
        bpy.data.actions.remove(action)


def arm(side, wrist, direction, pole=None, stretch=1.0, fist=1.0, lead=0.0):
    s = -1 if side == 'L' else 1
    return {'wrist': wrist, 'direction': direction,
            'pole': pole or (s*.68, .06, .58),
            'upper': 1+(stretch-1)*.45, 'fore': stretch, 'fist': fist, 'lead': lead}


def guard():
    return {'L': arm('L', (-.265, -.215, .90), (.20, -.50, .86), (-.36,-.035,.48)),
            'R': arm('R', (.265, -.195, .875), (-.20, -.50, .86), (.36,-.035,.48)), 'kick': 0.0}


def punch(side, beat):
    p, s = guard(), (-1 if side == 'L' else 1)
    values = {
        'load': ((s*.30, -.105, .84), (0, -.18, 1), 1.0, .98, -.20),
        'hit': ((s*.155, -.56, .925), (0, -1, .06), 1.25, 1.135, 1.0),
        'follow': ((s*.10, -.475, .94), (-s*.22, -1, .09), 1.10, 1.045, .60),
        'recoil': ((s*.29, -.16, .865), (0, -.18, 1), 1.0, .99, 0.0),
    }
    wrist, direction, stretch, fist, lead = values[beat]
    p[side] = arm(side, wrist, direction, stretch=stretch, fist=fist, lead=lead)
    other = 'L' if side == 'R' else 'R'
    p[other] = arm(other, (-s*.235, -.19, .94), (s*.20, -.50, .86), (-s*.36,-.035,.48))
    return p


def action_punch(side, beat, strong=False):
    p = punch(side,beat)
    s = -1 if side == 'L' else 1
    if beat == 'hit':
        p[side] = arm(side,(s*.155,-.69 if strong else -.47,.925),(0,-1,.06),
                      stretch=1.34 if strong else 1.15,fist=1.15 if strong else 1.085,
                      lead=1.20 if strong else .40)
    elif beat == 'follow':
        p[side] = arm(side,(s*.10,-.54 if strong else -.41,.94),(-s*.22,-1,.09),
                      stretch=1.13 if strong else 1.045,fist=1.045,lead=.70 if strong else .25)
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
            p[side] = arm(side, (s*.72, -.035, .82+wave), (s, -.12, .08),
                          (s*.46, .30, .69), stretch=1.18, fist=1.12)
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
M = lambda beat: action_punch('R',beat)
H = lambda beat: action_punch('L',beat,True)
clips['Medium'] = [(0,0,G()),(3,4,M('load')),(5,5,between(M('load'),M('hit'),.48)),
                   (6,6,M('hit')),(8,7,M('hit')),(11,10,M('follow')),
                   (15,14,M('recoil')),(21,19,G())]
clips['Strong'] = [(0,0,G()),(5,4,H('load')),(8,5,between(H('load'),H('hit'),.48)),
                   (9,6,H('hit')),(12,7,H('hit')),(16,10,H('follow')),
                   (22,14,H('recoil')),(30,19,G())]
clips['Jump'] = [(0,0,G()),(30,30,G())]


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
    if abs(spec['lead']) > .00001:
        # Protract the striking shoulder without changing its rest attachment or
        # stretching the collar bone. This gives the punch real forward reach.
        clav = 'clavicle.'+side
        head = rig.pose.bones[clav].head.copy()
        offset = root.to_quaternion()@Vector((0,-.085*spec['lead'],0))
        direction = (rig.pose.bones[upper].head-head+offset).normalized()
        orient(clav,head,head+direction*rig.data.bones[clav].length,(1,1,1))
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
    # A uniform upper-arm scale prevents a second rotated nonuniform scale from
    # shearing the forearm, palm and fingers during the baked/exported motion.
    orient(upper, shoulder, elbow, (spec['upper'],)*3)
    orient(fore, elbow, wrist, (1,spec['fore'],1))
    fore_q = rig.pose.bones[fore].matrix.to_quaternion()
    forward = (fore_q@Vector((0,1,0))).normalized()
    direction = root.to_quaternion()@Vector(spec['direction']).normalized()
    # Follow the forearm roll, and straighten the wrist as the sleeve extends.
    # At impact this makes the inverse length compensation a pure local scale,
    # leaving the fist uniformly enlarged instead of skewing its small fingers.
    allowance = math.radians(22)*(1-min(1,max(0,(spec['fore']-1)/.06)))
    angle = forward.angle(direction)
    if angle > allowance and angle > .00001:
        direction = forward.slerp(direction,allowance/angle).normalized()
    rotation = forward.rotation_difference(direction)@fore_q
    rig.pose.bones[hand].matrix = Matrix.LocRotScale(wrist,rotation,Vector((spec['fist'],)*3))
    bpy.context.view_layer.update()


items = [(name,action) for name,action in tracks.items() if name != 'Combo']
items += [('Medium',tracks['Jab']),('Strong',tracks['Cross']),('Jump',tracks['Guard'])]
for name, original in items:
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
            # The root/body positions already provide the crouch and rebound.
            # Keep the arm ancestors free of inherited anisotropic squash.
            for ancestor in ['root','hips','spine','chest','neck','head','clavicle.L','clavicle.R']:
                rig.pose.bones[ancestor].scale = (1,1,1)
            bpy.context.view_layer.update()
            for side in ['L','R']:
                solve_arm(side,spec[side])
            if spec['kick'] > 0:
                # Applied to the striking leg only, after support IK. Never
                # scale the resting mesh, the planted leg or a bone's rest data.
                rig.pose.bones['shin.R'].scale.y *= 1+.12*spec['kick']
                rig.pose.bones['foot.R'].scale *= 1+.055*spec['kick']
                bpy.context.view_layer.update()
            if name == 'Jump':
                for limb,angles in {'thigh.R':(-30,0,0),'shin.R':(65,0,0),'foot.R':(-15,0,0),
                                    'thigh.L':(-15,0,0),'shin.L':(45,0,0),'foot.L':(-10,0,0)}.items():
                    bone = rig.pose.bones[limb]
                    rest = bone.bone.matrix_local.to_quaternion()
                    bone.rotation_quaternion = rest.inverted()@Euler(tuple(math.radians(a) for a in angles),'XYZ').to_quaternion()@rest
                    bone.location = (0,0,0)
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

# The exported Combo is the same buffered sequence the game executes. The move
# table is a native Godot resource whose JSON-compatible data is read above.
def clip_time(info,time):
    times = [0,info['windup'],info['active_end'],info['duration']]
    frames = info['clip_frames']
    for i in range(3):
        if time <= times[i+1]:
            t = max(0,min(1,(time-times[i])/(times[i+1]-times[i])))
            return (frames[i]+(frames[i+1]-frames[i])*t)/30
    return frames[-1]/30


def sample_action(name,time):
    rig.animation_data.action = bpy.data.actions['PamUser_'+name]
    frame = time*30
    scene.frame_set(math.floor(frame),subframe=frame%1)
    return {bone.name:bone.matrix_basis.copy() for bone in rig.pose.bones}


segments, total = [], 0.0
for kind in combat['order']:
    info = combat['moves'][kind]
    duration = info['duration'] if kind == combat['order'][-1] else info['chain_at']
    segments.append((total,total+duration,info))
    total += duration
poses = []
for frame in range(math.ceil(total*30)+1):
    time = min(total,frame/30)
    index = next((i for i,(_,end,_) in enumerate(segments) if time < end),len(segments)-1)
    start,end,info = segments[index]
    elapsed = time-start
    pose = sample_action(info['clip'],clip_time(info,elapsed))
    if index > 0 and elapsed < combat['blend_time']:
        pstart,pend,previous = segments[index-1]
        old = sample_action(previous['clip'],clip_time(previous,pend-pstart))
        t = elapsed/combat['blend_time']
        pose = {name:solver.interpolate_matrix(old[name],pose[name],t) for name in pose}
    poses.append(pose)
action = bpy.data.actions.new('PamUser_Combo')
rig.animation_data.action = action
for frame,pose in enumerate(poses):
    for bone in rig.pose.bones:
        bone.matrix_basis = pose[bone.name]
        for path in ['location','rotation_quaternion','scale']:
            bone.keyframe_insert(data_path=path,frame=frame,group=bone.name)
track = rig.animation_data.nla_tracks.new()
track.name = 'Combo'
track.strips.new('Combo',0,action)
track.mute = True
action.use_fake_user = True
for curve in action.fcurves:
    for key in curve.keyframe_points:
        key.interpolation = 'LINEAR'
rig.animation_data.action = None
print('PAM_SINGLE_ACTION_COMBO_BAKED',len(poses),total)

assert fingerprint() == unchanged, 'No further edits to mesh, corrected weights or rest bones'
assert fingerprint(weights=False) == geometry_rest_before, 'Original geometry and rest pose must remain identical'
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
metadata.update({'combat_revision':3,'bind_mesh_weights_rest_sha256':unchanged,
    'bind_mesh_weights_rest_unchanged':False,'hand_weight_correction':hand_weights,
    'bind_geometry_rest_sha256':geometry_rest_before,'bind_geometry_rest_unchanged':True,
    'arm_ik':'Baked wrist goals and elbow poles on user proportions; stable wrist roll',
    'animation_only_stretch':True,'peak_forearm_length':1.25,'peak_fist_scale':1.135,
    'spin_forearm_length':1.18,'straight_wrist_at_impact':True,
    'effects':'Godot CombatFlourish; separate from GLB',
    'combo_impact_frames':[6,16,30],'spin_trail_frames':[9,27]})
metadata.update({'combat_revision':4,'clips':[track.name for track in rig.animation_data.nla_tracks],
    'action_order':combat['order'],'action_config':'resources/combat_moves.tres',
    'action_combo_seconds':total,'baked_combo_seconds':math.ceil(total*30)/30,
    'strong_forearm_length':1.34,'medium_forearm_length':1.15,
    'peak_forearm_length':1.34,'peak_fist_scale':1.15,
    'bind_mesh_weights_rest_unchanged':hand_weights['changed_vertices'] == 0,
    'combo_impact_frames':[round((start+info['windup'])*30,6) for start,end,info in segments if info['clip'] in ['Medium','Strong']],
    'spin_trail_frames':[round(combat['moves']['spin'][key]*30,6) for key in ['windup','active_end']]})
meta_path.write_text(json.dumps(metadata,indent=2)+'\n')
print('PAM_USER_CARTOON_EXPORT_OK',unchanged)
