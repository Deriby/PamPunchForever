"""Author original cartoon combat clips on the real Pam skin/armature.

Run after rig.py. Fight feet use baked two-bone IK, while the runtime file only
needs ordinary glTF bones, scales and one facial blend shape. No runtime plugin.
"""
import bpy
import bmesh
import json
import math
import struct
from pathlib import Path
from mathutils import Vector, Matrix, Euler, Quaternion

ROOT = Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'assets/source/pam_ps1_rig.blend'))
rig = bpy.data.objects['PamRig']
body = bpy.data.objects['PamBody']
rig.animation_data_clear()
for old in list(bpy.data.actions):
    bpy.data.actions.remove(old)
scene = bpy.context.scene
scene.render.fps = 30
scene.frame_start, scene.frame_end = 0, 72

# A weighted fur bridge under the collar keeps the neck covered when the chest
# and head counter-rotate in the exaggerated kick/recovery poses.
vertices, faces = [], []
for z, rx, ry in [(.918, .096, .076), (.973, .089, .071), (1.035, .082, .066)]:
    for i in range(6):
        angle = math.tau*i/6
        vertices.append((math.cos(angle)*rx, math.sin(angle)*ry-.005, z))
for row in range(2):
    for i in range(6):
        a, b = row*6+i, row*6+(i+1)%6
        faces.append((a, b, b+6, a+6))
faces += [tuple(reversed(range(6))), tuple(range(12, 18))]
data = bpy.data.meshes.new('NeckBridge')
data.from_pydata(vertices, [], faces)
data.materials.append(body.data.materials[0])
bm = bmesh.new()
bm.from_mesh(data)
bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
bm.to_mesh(data)
bm.free()
data.update()
uv = data.uv_layers.new(name='Atlas128')
color = data.color_attributes.new(name='PS1Light', type='BYTE_COLOR', domain='CORNER')
light = Vector((-.38, -.72, .57)).normalized()
for i, loop in enumerate(data.loops):
    uv.data[i].uv = (44/128, 1-88/128)
    shade = .52+.48*max(0, data.vertices[loop.vertex_index].normal.dot(light))
    color.data[i].color = (shade, shade*.98, shade*.99, 1)
neck = bpy.data.objects.new('NeckBridge', data)
bpy.context.collection.objects.link(neck)
for row, name in enumerate(['chest', 'neck', 'head']):
    neck.vertex_groups.new(name=name).add(list(range(row*6, row*6+6)), 1, 'REPLACE')
bpy.ops.object.select_all(action='DESELECT')
body.select_set(True)
neck.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()

# A small geometric blink: the eye contours and pupils close together. The black
# panda patches remain in place. This is a morph on the exported body, not a decal.
body.shape_key_add(name='Basis')
blink = body.shape_key_add(name='Blink')
eye = [(.087, .045), (.108, .105), (.24, .145), (.282, .083), (.231, .018), (.142, .006)]

def inside(x, z):
    result, last = False, eye[-1]
    for point in eye:
        a, b = point, last
        if (a[1] > z) != (b[1] > z) and x < (b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0]:
            result = not result
        segment = Vector(b)-Vector(a)
        t = max(0, min(1, (Vector((x, z))-Vector(a)).dot(segment)/segment.length_squared))
        if (Vector((x, z))-(Vector(a)+segment*t)).length < .003:
            return True
        last = point
    return result

head_group = body.vertex_groups['head'].index
blink_vertices = 0
for vertex in body.data.vertices:
    if not any(g.group == head_group for g in vertex.groups):
        continue
    x, y, z = abs(vertex.co.x/.92), (vertex.co.y+.005)/.95, (vertex.co.z-1.18)/.86
    if y < -.17 and inside(x, z):
        mid = .073+.12*(x-.18)
        blink.data[vertex.index].co.z = 1.18+.86*(mid+(z-mid)*.055)
        blink_vertices += 1
assert blink_vertices >= 20

def turn(name, angles):
    rotation = rig.data.bones[name].matrix_local.to_quaternion()
    delta = Euler(tuple(math.radians(v) for v in angles), 'XYZ').to_quaternion()
    rig.pose.bones[name].rotation_quaternion = rotation.inverted() @ delta @ rotation

def reset():
    for bone in rig.pose.bones:
        bone.rotation_mode = 'QUATERNION'
        bone.rotation_quaternion = (1, 0, 0, 0)
        bone.location = (0, 0, 0)
        bone.scale = (1, 1, 1)

def base():
    return {
        'rot': {'spine': (5, 0, 0), 'chest': (-2, 0, -3), 'head': (-2, 0, 3),
                'upper_arm.L': (-27, 10, -5), 'upper_arm.R': (-35, -10, 5),
                'forearm.L': (-107, 0, 0), 'forearm.R': (-108, 0, 0),
                'hand.L': (6, 0, -7), 'hand.R': (6, 0, 7)},
        'loc': (0, 0, -.032), 'scale': {}, 'blink': 0,
        'feet': {'L': (-.205, -.045, .094), 'R': (.205, .045, .094)},
        'ik': 1.0, 'foot_roll': {'L': 0, 'R': 0},
    }

def neutral():
    p = base()
    p['rot'] = {}
    p['loc'] = (0, 0, 0)
    p['ik'] = 0
    return p

def update(p, rot=None, loc=None, scale=None, blink=None):
    if rot:
        p['rot'].update(rot)
    if loc is not None:
        p['loc'] = loc
    if scale:
        p['scale'].update(scale)
    if blink is not None:
        p['blink'] = blink
    return p

def punch(side, beat):
    p, s = base(), (-1 if side == 'L' else 1)
    if beat == 'load':
        update(p, {'hips': (0, 0, -s*9), 'chest': (-5, 0, -s*17),
                   'head': (3, 0, s*11), 'upper_arm.'+side: (-10, -s*14, s*4),
                   'forearm.'+side: (-128, 0, 0)},
               (s*-.014, .015, -.048), {'spine': (1.025, 1.025, .965),
                                        'hand.'+side: (1.025, .94, 1.025)})
    elif beat == 'hit':
        update(p, {'hips': (0, 0, s*7), 'spine': (9, 0, s*4),
                   'chest': (3, 0, s*21), 'head': (-5, 0, -s*16),
                   'upper_arm.'+side: (-94, s*7, -s*12),
                   'forearm.'+side: (-8, 0, 0), 'hand.'+side: (-3, -s*22, 0)},
               (s*.025, -.043, -.017),
               {'upper_arm.'+side: (1, 1.035, 1), 'forearm.'+side: (1, 1.095, 1),
                'hand.'+side: (1.12, 1.06, 1.10), 'spine': (.99, .99, 1.025)})
    elif beat == 'follow':
        update(p, {'hips': (0, 0, s*10), 'chest': (6, 0, s*28),
                   'head': (-3, 0, -s*20), 'upper_arm.'+side: (-87, s*11, -s*15),
                   'forearm.'+side: (-22, 0, 0), 'hand.'+side: (6, -s*10, 0)},
               (s*.032, -.032, -.028))
    elif beat == 'recoil':
        update(p, {'hips': (0, 0, -s*4), 'chest': (-4, 0, -s*8),
                   'head': (3, 0, s*9), 'forearm.'+side: (-119, 0, 0)},
               (-s*.008, .007, -.038))
    return p

def kick(beat):
    p = base()
    p['ik'] = .5  # Only the support leg is planted; the right leg is posed freely.
    if beat == 'load':
        update(p, {'hips': (0, -5, -13), 'spine': (-4, 0, -10), 'chest': (0, 0, -12),
                   'head': (3, 0, 14), 'thigh.R': (-64, -10, 8), 'shin.R': (122, 0, 0),
                   'foot.R': (-24, 0, 0), 'upper_arm.R': (-50, -22, 18)},
               (-.035, .015, -.045), {'spine': (1.025, 1.025, .97)})
    elif beat == 'hit':
        update(p, {'hips': (-10, -10, 22), 'spine': (-9, 0, 8),
                   'chest': (-7, 0, 14), 'head': (8, 0, -20),
                   'thigh.R': (-93, -12, -10), 'shin.R': (10, 0, 0), 'foot.R': (13, 0, 0),
                   'upper_arm.R': (12, -38, 17), 'forearm.R': (-55, 0, 0),
                   'upper_arm.L': (-46, 19, -15), 'forearm.L': (-95, 0, 0)},
               (-.048, -.012, .006), {'shin.R': (1, 1.06, 1), 'foot.R': (1.06, 1.06, 1.04)})
    elif beat == 'follow':
        update(p, {'hips': (-8, -7, 28), 'spine': (-7, 0, 8), 'chest': (-4, 0, 17),
                   'head': (8, 0, -22), 'thigh.R': (-82, -13, -13),
                   'shin.R': (26, 0, 0), 'foot.R': (7, 0, 0),
                   'upper_arm.R': (5, -32, 17), 'forearm.R': (-67, 0, 0)},
               (-.042, -.008, -.006))
    elif beat == 'fold':
        update(p, {'hips': (0, -4, 8), 'chest': (-3, 0, -7), 'head': (5, 0, 2),
                   'thigh.R': (-52, -5, 3), 'shin.R': (116, 0, 0), 'foot.R': (-15, 0, 0)},
               (-.025, .012, -.032))
    else:
        p['ik'] = 1.0
    return p

def spin(beat, yaw):
    p = base()
    update(p, {'root': (0, 0, yaw)})
    if beat == 'load':
        update(p, {'hips': (4, 0, -18), 'spine': (14, 0, -16), 'chest': (5, 0, -17),
                   'head': (-6, 0, 16), 'upper_arm.L': (-16, 16, -20),
                   'upper_arm.R': (-20, -12, 22), 'forearm.L': (-128, 0, 0),
                   'forearm.R': (-130, 0, 0)},
               (0, .006, -.088), {'spine': (1.04, 1.04, .94)})
    elif beat in ['open', 'turn1', 'turn2']:
        p['ik'] = 0
        tilt = 1 if beat != 'turn2' else -1
        update(p, {'hips': (0, tilt*4, 0), 'spine': (4, tilt*5, 10),
                   'chest': (-3, 0, 17), 'head': (-3, 0, -13),
                   'upper_arm.L': (-10, 81, -9), 'upper_arm.R': (-12, -82, 10),
                   'forearm.L': (-18, 0, 0), 'forearm.R': (-13, 0, 0),
                   'hand.L': (0, 0, -16), 'hand.R': (0, 0, 16),
                   'thigh.L': (-tilt*17, 13, 0), 'thigh.R': (tilt*13, -12, 0),
                   'shin.L': (46+tilt*18, 0, 0), 'shin.R': (46-tilt*18, 0, 0),
                   'foot.L': (-12, 0, 0), 'foot.R': (-12, 0, 0)},
               (0, 0, .055 if beat == 'open' else .095),
               {'upper_arm.L': (1, 1.025, 1), 'upper_arm.R': (1, 1.025, 1),
                'forearm.L': (1, 1.045, 1), 'forearm.R': (1, 1.045, 1),
                'hand.L': (1.08, 1.035, 1.08), 'hand.R': (1.08, 1.035, 1.08)})
    elif beat == 'land':
        update(p, {'spine': (16, 0, -8), 'chest': (3, 0, -7), 'head': (-5, 0, 8),
                   'upper_arm.L': (-12, 38, -8), 'upper_arm.R': (-15, -39, 9),
                   'forearm.L': (-70, 0, 0), 'forearm.R': (-70, 0, 0)},
               (0, 0, -.082), {'spine': (1.04, 1.04, .94)})
    elif beat == 'settle':
        update(p, {'spine': (2, 0, 2), 'head': (4, 0, -4)},
               (0, .003, -.015), {'spine': (.99, .99, 1.02)})
    return p

def mix(a, b, t):
    # Ease ordinary breakdowns; rapid hit spacing is authored explicitly in frames.
    w = t*t*(3-2*t)
    def vector(x, y):
        return tuple(v*(1-w)+u*w for v, u in zip(x, y))
    result = {'loc': vector(a['loc'], b['loc']), 'rot': {}, 'scale': {}, 'feet': {},
              'blink': a['blink']*(1-w)+b['blink']*w, 'ik': a['ik']*(1-w)+b['ik']*w,
              'foot_roll': {}}
    for group, default in [('rot', (0, 0, 0)), ('scale', (1, 1, 1))]:
        for name in set(a[group]) | set(b[group]):
            result[group][name] = vector(a[group].get(name, default), b[group].get(name, default))
    for side in ['L', 'R']:
        result['feet'][side] = vector(a['feet'][side], b['feet'][side])
        result['foot_roll'][side] = a['foot_roll'][side]*(1-w)+b['foot_roll'][side]*w
    return result

def orient(name, position, direction):
    bone = rig.data.bones[name]
    delta = (bone.tail_local-bone.head_local).rotation_difference(direction)
    rig.pose.bones[name].matrix = Matrix.LocRotScale(position, delta @ bone.matrix_local.to_quaternion(), Vector((1, 1, 1)))
    bpy.context.view_layer.update()

def plant(side, target, foot_roll=0, weight=1.0):
    thigh, shin, foot = ('thigh.'+side, 'shin.'+side, 'foot.'+side)
    fk = {name: rig.pose.bones[name].matrix_basis.copy() for name in [thigh, shin, foot]}
    hip = rig.pose.bones[thigh].head.copy()
    target = Vector(target)
    first, second = rig.data.bones[thigh].length, rig.data.bones[shin].length
    direction = target-hip
    distance = max(.02, min(first+second-.0001, direction.length))
    axis = direction.normalized()
    forward = Vector((0, -1, 0))
    forward = (forward-axis*forward.dot(axis)).normalized()
    along = (first*first-second*second+distance*distance)/(2*distance)
    height = math.sqrt(max(0, first*first-along*along))
    knee = hip+axis*along+forward*height
    endpoint = hip+axis*distance
    orient(thigh, hip, knee-hip)
    orient(shin, knee, endpoint-knee)
    q = Quaternion((1, 0, 0), math.radians(foot_roll)) @ rig.data.bones[foot].matrix_local.to_quaternion()
    rig.pose.bones[foot].matrix = Matrix.LocRotScale(endpoint, q, Vector((1, 1, 1)))
    bpy.context.view_layer.update()
    if weight < .999:
        ik = {name: rig.pose.bones[name].matrix_basis.copy() for name in [thigh, shin, foot]}
        for name in [thigh, shin, foot]:
            a, b = fk[name].decompose(), ik[name].decompose()
            rig.pose.bones[name].matrix_basis = Matrix.LocRotScale(
                a[0].lerp(b[0], weight), a[1].slerp(b[1], weight), a[2].lerp(b[2], weight))
        bpy.context.view_layer.update()

def apply(p):
    reset()
    for name, rotation in p['rot'].items():
        turn(name, rotation)
    for name, scale in p['scale'].items():
        rig.pose.bones[name].scale = scale
    # The root's local Y axis points up in this armature.
    q = rig.data.bones['root'].matrix_local.to_quaternion()
    rig.pose.bones['root'].location = q.inverted() @ Vector(p['loc'])
    bpy.context.view_layer.update()
    # Keep fully supporting legs within reach instead of stretching them or
    # letting an ankle lift above the authored floor during a weight transfer.
    lower = 0.0
    for side, weight in [('L', min(1, p['ik']*2)), ('R', max(0, p['ik']*2-1))]:
        if weight < .999:
            continue
        hip = rig.pose.bones['thigh.'+side].head
        goal = Vector(p['feet'][side])
        reach = rig.data.bones['thigh.'+side].length+rig.data.bones['shin.'+side].length-.004
        horizontal = (hip.x-goal.x)**2+(hip.y-goal.y)**2
        vertical = math.sqrt(max(.001, reach*reach-horizontal))
        lower = max(lower, hip.z-goal.z-vertical)
    if lower > 0:
        offset = Vector(p['loc'])-Vector((0, 0, lower))
        rig.pose.bones['root'].location = q.inverted() @ offset
        bpy.context.view_layer.update()
    if p['ik'] > .01:
        plant('L', p['feet']['L'], p['foot_roll']['L'], min(1, p['ik']*2))
    if p['ik'] > .50:
        plant('R', p['feet']['R'], p['foot_roll']['R'], max(0, p['ik']*2-1))
    blink.value = p['blink']

def action(name, keys=None, duration=None, sampler=None):
    rig.animation_data_create()
    body.data.shape_keys.animation_data_create()
    bones_action = bpy.data.actions.new(name+'_Bones')
    face_action = bpy.data.actions.new(name+'_Face')
    rig.animation_data.action = bones_action
    body.data.shape_keys.animation_data.action = face_action
    end = duration if duration is not None else keys[-1][0]
    for frame in range(end+1):
        if sampler:
            p = sampler(frame/end)
        else:
            left = next((i for i in range(len(keys)-1) if keys[i][0] <= frame <= keys[i+1][0]), len(keys)-2)
            a, b = keys[left], keys[left+1]
            p = mix(a[1], b[1], (frame-a[0])/(b[0]-a[0]))
        apply(p)
        for bone in rig.pose.bones:
            bone.keyframe_insert(data_path='rotation_quaternion', frame=frame, group=bone.name)
            bone.keyframe_insert(data_path='location', frame=frame, group=bone.name)
            bone.keyframe_insert(data_path='scale', frame=frame, group=bone.name)
        blink.keyframe_insert(data_path='value', frame=frame)
    for owner, clip in [(rig, bones_action), (body.data.shape_keys, face_action)]:
        track = owner.animation_data.nla_tracks.new()
        track.name = name
        track.strips.new(name, 0, clip)
        track.mute = True
        clip.use_fake_user = True
        for curve in clip.fcurves:
            for key in curve.keyframe_points:
                key.interpolation = 'LINEAR'
        owner.animation_data.action = None

def breathing(t):
    p = base()
    wave = math.sin(t*math.tau)
    p['loc'] = (wave*.004, 0, -.032+wave*.006)
    update(p, {'head': (-2+wave*1.3, wave*.6, 3-wave*1.2),
               'forearm.L': (-107-wave*2.5, 0, 0), 'forearm.R': (-108+wave*2, 0, 0)})
    p['blink'] = max(0, 1-abs(t-.62)/.035)
    return p

action('Guard', duration=60, sampler=breathing)
for side, name in [('R', 'Jab'), ('L', 'Cross')]:
    action(name, [(0, base()), (4, punch(side, 'load')), (6, punch(side, 'hit')),
                  (7, punch(side, 'hit')), (10, punch(side, 'follow')),
                  (14, punch(side, 'recoil')), (19, base())])

kick_keys = [(0, base()), (6, kick('load')), (9, kick('hit')), (11, kick('hit')),
             (14, kick('follow')), (19, kick('fold')), (26, base()), (30, base())]
action('Kick', kick_keys)
action('Combo', [(0, base()), (4, punch('R', 'load')), (6, punch('R', 'hit')),
                 (7, punch('R', 'hit')), (10, punch('R', 'follow')),
                 (14, punch('L', 'load')), (17, punch('L', 'hit')), (18, punch('L', 'hit')),
                 (22, punch('L', 'follow')), (29, kick('load')), (33, kick('hit')),
                 (35, kick('hit')), (39, kick('follow')), (45, kick('fold')),
                 (53, update(base(), {'head': (4, 0, -3)}, (0, 0, -.047))),
                 (59, base()), (66, base())])
action('Spin', [(0, spin('guard', 0)), (6, spin('load', -36)),
                (9, spin('open', 0)), (15, spin('turn1', 225)),
                (21, spin('turn2', 495)), (27, spin('open', 720)),
                (30, spin('land', 726)), (35, spin('settle', 717)), (42, spin('guard', 720))])

def running(t):
    p = base()
    p['loc'] = (0, 0, -.015+.008*math.cos(t*math.tau*2))
    wave = math.sin(t*math.tau)
    update(p, {'spine': (11, 0, wave*5), 'chest': (-3, 0, -wave*5),
               'head': (-6, 0, wave*3),
               'upper_arm.L': (wave*38-8, 8, -3), 'upper_arm.R': (-wave*38-8, -8, 3),
               'forearm.L': (-67+wave*18, 0, 0), 'forearm.R': (-67-wave*18, 0, 0)})
    for side, offset, x in [('L', 0, -.17), ('R', .5, .17)]:
        phase = (t+offset) % 1
        if phase < .5:
            p['feet'][side] = (x, -.13+.26*phase/.5, .094)
        else:
            s = (phase-.5)/.5
            p['feet'][side] = (x, .13-.26*s, .094+.14*math.sin(math.pi*s))
            p['foot_roll'][side] = -12*math.sin(math.pi*s)
    return p

action('Run', duration=24, sampler=running)
action('ElbowFlex', [(0, neutral()), (12, update(neutral(), {'forearm.R': (-90, 0, 0)})),
                     (24, update(neutral(), {'forearm.R': (-125, 0, 0)})), (48, neutral())])
action('KneeFlex', [(0, neutral()), (12, update(neutral(), {'shin.R': (90, 0, 0)})),
                    (18, update(neutral(), {'shin.R': (110, 0, 0), 'foot.R': (-25, 0, 0)})),
                    (30, neutral()), (42, update(neutral(), {'shin.L': (90, 0, 0)})),
                    (48, update(neutral(), {'shin.L': (110, 0, 0), 'foot.L': (-25, 0, 0)})),
                    (60, neutral())])

rig.animation_data.action = None
body.data.shape_keys.animation_data.action = None
apply(base())
scene.frame_set(0)
# Save with the default guard as a readable editing pose; clips remain separate.
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'assets/source/pam_ps1_cartoon.blend'))
bpy.ops.object.select_all(action='SELECT')
output = ROOT / 'assets/models/pam_ps1_cartoon.glb'
bpy.ops.export_scene.gltf(filepath=str(output), export_format='GLB', export_yup=True,
    export_animations=True, export_animation_mode='NLA_TRACKS', export_frame_range=False,
    export_skins=True, export_all_influences=False, export_morph=True,
    export_vertex_color='ACTIVE', export_all_vertex_colors=False)

blob, offset, chunks = output.read_bytes(), 12, []
while offset < len(blob):
    length, kind = struct.unpack_from('<II', blob, offset)
    chunks.append((kind, blob[offset+8:offset+8+length]))
    offset += 8+length
asset = json.loads(next(data for kind, data in chunks if kind == 0x4E4F534A))
assert len(asset['materials']) == 1
mat = asset['materials'][0]
mat.pop('emissiveFactor', None)
mat.pop('emissiveTexture', None)
mat['pbrMetallicRoughness'] = {'baseColorFactor': [1, 1, 1, 1], 'baseColorTexture': {'index': 0},
                              'metallicFactor': 0, 'roughnessFactor': 1}
mat['extensions'] = {'KHR_materials_unlit': {}}
asset['extensionsUsed'] = sorted(set(asset.get('extensionsUsed', [])+['KHR_materials_unlit']))
for sampler in asset.get('samplers', []):
    sampler['magFilter'] = sampler['minFilter'] = 9728
payload = json.dumps(asset, separators=(',', ':')).encode()
payload += b' '*((-len(payload))%4)
packed = [(0x4E4F534A, payload)]+[(kind, data) for kind, data in chunks if kind != 0x4E4F534A]
binary = b''.join(struct.pack('<II', len(data), kind)+data for kind, data in packed)
output.write_bytes(struct.pack('<III', 0x46546C67, 2, len(binary)+12)+binary)
names = {clip['name'] for clip in asset['animations']}
assert names == {'Guard', 'Jab', 'Cross', 'Kick', 'Combo', 'Spin', 'Run', 'ElbowFlex', 'KneeFlex'}, names
assert len(asset['skins']) == 1 and len(asset['skins'][0]['joints']) == 22
assert len(asset['meshes'][0]['primitives'][0]['targets']) == 1
triangles = sum(asset['accessors'][p['indices']]['count']//3 for m in asset['meshes'] for p in m['primitives'])
metadata = {'revision': 6, 'bones': 22, 'triangles': triangles, 'materials': 1, 'atlas': [128, 128],
    'clips': sorted(names), 'blink_vertices': blink_vertices, 'authored_fps': 30,
    'arm_scale_peak': {'upper_arm_y': 1.035, 'forearm_y': 1.095, 'hand_xyz': [1.12, 1.06, 1.10]},
    'foot_placement': 'Baked two-bone IK for fight support feet',
    'commercial_animation_data_used': False}
(ROOT / 'assets/source/pam_ps1_cartoon_metadata.json').write_text(json.dumps(metadata, indent=2))
print('PAM_CARTOON_EXPORT_OK', json.dumps(metadata))
