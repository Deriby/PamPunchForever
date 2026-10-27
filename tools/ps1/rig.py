"""Build an actual skinned Pam armature; keep the original PS1 study as history.

Run after model.py. Original model/atlas only; no commercial character data.
The glTF exporter uses linear skinning, also used by the review renders.
"""
import bpy
import bmesh
import json
import math
import struct
from pathlib import Path
from mathutils import Matrix, Vector, Euler

ROOT = Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'assets/source/pam_ps1_estudo.blend'))
material = bpy.data.materials['Pam_PS1_128']
meshes = []

def weights(ob, values):
    for vertex, influences in enumerate(values):
        total = sum(influences.values())
        assert abs(total - 1) < .00001, (ob.name, vertex, total)
        for bone, weight in influences.items():
            if weight > .000001:
                group = ob.vertex_groups.get(bone) or ob.vertex_groups.new(name=bone)
                group.add([vertex], weight, 'REPLACE')

def blend(a, b, t):
    t = max(0, min(1, t))
    return {a: 1-t, b: t}

def ancestry(ob):
    result = []
    while ob:
        result.append(ob.name)
        ob = ob.parent
    return result

# Bake the previous rigid parts into bind space, then assign actual bone weights.
for ob in list(bpy.context.scene.objects):
    if ob.type != 'MESH':
        continue
    parents = ancestry(ob)
    if any(name in parents for name in ['ArmL', 'ArmR']) or ob.name.startswith('Shin'):
        bpy.data.objects.remove(ob, do_unlink=True)
        continue
    transform = ob.matrix_world.copy()
    ob.parent = None
    ob.matrix_world = Matrix.Identity(4)
    ob.data.transform(transform)
    if 'Head' in parents:
        values = [{'head': 1} for v in ob.data.vertices]
    elif 'Torso' in parents:
        values = [blend('spine', 'chest', (v.co.z-.69)/.22) for v in ob.data.vertices]
    else:
        side = 'L' if 'LegL' in parents else 'R'
        if ob.name.startswith('Shorts'):
            values = [{'thigh.'+side: 1} for v in ob.data.vertices]
        else:
            values = [blend('foot.'+side, 'toe.'+side, (-v.co.y-.08)/.15*.7)
                      for v in ob.data.vertices]
    weights(ob, values)
    meshes.append(ob)

for ob in list(bpy.context.scene.objects):
    if ob.type == 'EMPTY':
        bpy.data.objects.remove(ob, do_unlink=True)

PALETTE = {'black': 0, 'dark': 1, 'fold': 2, 'lining': 3, 'cream': 5}

def mesh(name, vertices, faces, influences, region='black'):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    ob = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(ob)
    data.materials.append(material)
    uv = data.uv_layers.new(name='Atlas128')
    lo = [min(v[k] for v in vertices) for k in range(3)]
    hi = [max(v[k] for v in vertices) for k in range(3)]
    for polygon in data.polygons:
        for index in polygon.loop_indices:
            point = data.vertices[data.loops[index].vertex_index].co
            if region == 'jacket':
                x = (point.x-lo[0])/max(.001, hi[0]-lo[0])
                z = (point.z-lo[2])/max(.001, hi[2]-lo[2])
                uv.data[index].uv = ((65+x*30)/128, 1-(31-z*30)/128)
            else:
                uv.data[index].uv = ((PALETTE[region]*8+4)/128, 1-88/128)
    bm = bmesh.new()
    bm.from_mesh(data)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(data)
    bm.free()
    data.update()
    color = data.color_attributes.new(name='PS1Light', type='BYTE_COLOR', domain='CORNER')
    key = Vector((-.38, -.72, .57)).normalized()
    for polygon in data.polygons:
        polygon.use_smooth = True
    for i, loop in enumerate(data.loops):
        shade = .52+.48*max(0, data.vertices[loop.vertex_index].normal.dot(key))
        color.data[i].color = (shade, shade*.98, shade*.99, 1)
    weights(ob, influences)
    meshes.append(ob)
    return ob

def ring_mesh(name, rows, side, bone_a, bone_b, transition, region='black'):
    vertices, faces, influences = [], [], []
    sides = 8
    for x, y, z, rx, ry in rows:
        for i in range(sides):
            angle = math.tau*i/sides-math.pi/2
            vertices.append((x+math.cos(angle)*rx, y+math.sin(angle)*ry, z))
            influences.append(blend(bone_a, bone_b, (transition[0]-z)/transition[1]))
    faces.append(tuple(reversed(range(sides))))
    for row in range(len(rows)-1):
        for i in range(sides):
            a = row*sides+i
            b = row*sides+(i+1)%sides
            faces.append((a, b, b+sides, a+sides))
    faces.append(tuple(range((len(rows)-1)*sides, len(rows)*sides)))
    return mesh(name, vertices, faces, influences, region)

for s, side in [(-1, 'L'), (1, 'R')]:
    # Continuous sleeve: deliberate upper arm, elbow loops, forearm and narrow wrist.
    ring_mesh('Sleeve.'+side, [
        (s*.255, .005, .975, .088, .091),
        (s*.282, .003, .905, .108, .105),
        (s*.318, -.007, .810, .094, .089),
        (s*.337, -.012, .755, .076, .080),
        (s*.345, -.014, .720, .075, .086),
        (s*.350, -.017, .685, .075, .080),
        (s*.359, -.023, .625, .090, .087),
        (s*.368, -.028, .555, .075, .074),
        (s*.370, -.030, .515, .059, .060),
    ], side, 'upper_arm.'+side, 'forearm.'+side, (.765, .09), 'jacket')
    # Black cuff overlaps the hand slightly in bind space, avoiding a floating fist.
    ring_mesh('Cuff.'+side, [
        (s*.370, -.030, .545, .075, .073),
        (s*.372, -.032, .508, .061, .063),
    ], side, 'forearm.'+side, 'hand.'+side, (.535, .045), 'black')
    outline = [(-.079, -.040), (-.068, .059), (-.020, .088),
               (.066, .070), (.084, -.022), (.036, -.086)]
    vertices = [(s*(.379+x), y-.065, .456+z)
                for y in [-.071, .058] for x, z in outline]
    faces = [tuple(reversed(range(6))), tuple(range(6, 12))]
    faces += [(i, (i+1)%6, (i+1)%6+6, i+6) for i in range(6)]
    mesh('Fist.'+side, vertices, faces, [{'hand.'+side: 1}]*len(vertices))
    thumb = [(s*.338, -.137, .506), (s*.294, -.105, .469),
             (s*.332, -.168, .427), (s*.362, -.128, .441)]
    mesh('Thumb.'+side, thumb, [(0, 1, 2), (0, 2, 3), (0, 3, 1), (1, 3, 2)],
         [{'hand.'+side: 1}]*4, 'dark')
    ring_mesh('Leg.'+side, [
        (s*.150, -.008, .320, .075, .077),
        (s*.152, -.012, .276, .076, .077),
        (s*.155, -.015, .245, .072, .078),
        (s*.158, -.012, .215, .065, .069),
        (s*.164, -.004, .145, .070, .072),
        (s*.166, .000, .094, .069, .073),
    ], side, 'thigh.'+side, 'shin.'+side, (.285, .08))

armature = bpy.data.armatures.new('PamSkeleton')
rig = bpy.data.objects.new('PamRig', armature)
bpy.context.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')

def bone(name, head, tail, parent=None):
    item = armature.edit_bones.new(name)
    item.head, item.tail = head, tail
    if parent:
        item.parent = armature.edit_bones[parent]
    return item

bone('root', (0, 0, .02), (0, 0, .18))
bone('hips', (0, 0, .49), (0, 0, .62), 'root')
bone('spine', (0, 0, .62), (0, 0, .80), 'hips')
bone('chest', (0, 0, .80), (0, 0, .95), 'spine')
bone('neck', (0, 0, .95), (0, -.005, 1.06), 'chest')
bone('head', (0, -.005, 1.06), (0, -.005, 1.43), 'neck')
for s, side in [(-1, 'L'), (1, 'R')]:
    bone('clavicle.'+side, (0, 0, .94), (s*.255, .005, .95), 'chest')
    bone('upper_arm.'+side, (s*.255, .005, .95), (s*.345, -.014, .72), 'clavicle.'+side)
    bone('forearm.'+side, (s*.345, -.014, .72), (s*.370, -.030, .515), 'upper_arm.'+side)
    bone('hand.'+side, (s*.370, -.030, .515), (s*.379, -.065, .415), 'forearm.'+side)
    bone('thigh.'+side, (s*.133, 0, .49), (s*.155, -.015, .245), 'hips')
    bone('shin.'+side, (s*.155, -.015, .245), (s*.166, 0, .094), 'thigh.'+side)
    bone('foot.'+side, (s*.166, 0, .094), (s*.166, -.13, .057), 'shin.'+side)
    bone('toe.'+side, (s*.166, -.13, .057), (s*.166, -.225, .040), 'foot.'+side)
bpy.ops.object.mode_set(mode='OBJECT')
rig.show_in_front = True
armature.display_type = 'OCTAHEDRAL'

bpy.ops.object.select_all(action='DESELECT')
for ob in meshes:
    ob.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.object.join()
body = bpy.context.object
body.name = 'PamBody'
body.parent = rig
modifier = body.modifiers.new('LinearSkin', 'ARMATURE')
modifier.object = rig
modifier.use_deform_preserve_volume = False  # Match glTF linear skinning, including renders.

for vertex in body.data.vertices:
    assert 1 <= len(vertex.groups) <= 2
    assert abs(sum(group.weight for group in vertex.groups)-1) < .00001

# Animate bones; there are no parent-empty rotations standing in for elbow motion.
scene = bpy.context.scene
scene.render.fps = 30
scene.frame_start = 0
scene.frame_end = 48
rig.animation_data_create()

def rest():
    for p in rig.pose.bones:
        p.rotation_mode = 'QUATERNION'
        p.rotation_quaternion = (1, 0, 0, 0)
        p.location = (0, 0, 0)
        p.scale = (1, 1, 1)

def turn(name, xyz):
    q = rig.data.bones[name].matrix_local.to_quaternion()
    delta = Euler(tuple(math.radians(v) for v in xyz), 'XYZ').to_quaternion()
    rig.pose.bones[name].rotation_quaternion = q.inverted() @ delta @ q

def guard():
    turn('hips', (0, 0, -3))
    turn('spine', (0, 0, 3))
    turn('chest', (0, 0, 2))
    for s, side in [(-1, 'L'), (1, 'R')]:
        turn('upper_arm.'+side, (-34, -s*9, s*4))
        turn('forearm.'+side, (-112, 0, 0))
        turn('hand.'+side, (9, 0, s*6))

def action(name, keyframes, loop=False):
    clip = bpy.data.actions.new(name)
    rig.animation_data.action = clip
    for frame, pose in keyframes:
        rest()
        pose()
        for p in rig.pose.bones:
            p.keyframe_insert(data_path='rotation_quaternion', frame=frame-1, group=p.name)
            p.keyframe_insert(data_path='location', frame=frame-1, group=p.name)
    track = rig.animation_data.nla_tracks.new()
    track.name = name
    track.strips.new(name, keyframes[0][0]-1, clip)
    track.mute = True
    clip.use_fake_user = True
    # Linear interpolation avoids overshoot through the head at recovery.
    for curve in clip.fcurves:
        for key in curve.keyframe_points:
            key.interpolation = 'LINEAR'
    return clip

def guard_breathe():
    guard()
    rig.pose.bones['hips'].location.y = .008
    turn('forearm.L', (-116, 0, 0))
    turn('forearm.R', (-109, 0, 0))

action('Guard', [(1, guard), (25, guard_breathe), (49, guard)])

def punch(side, stage):
    guard()
    s = -1 if side == 'L' else 1
    if stage == 'windup':
        turn('upper_arm.'+side, (-20, -s*10, s*5))
        turn('forearm.'+side, (-128, 0, 0))
        turn('chest', (0, 0, -s*8))
    elif stage == 'hit':
        turn('upper_arm.'+side, (-92, s*10, -s*9))
        turn('forearm.'+side, (-12, 0, 0))
        turn('hand.'+side, (-5, -s*18, 0))
        turn('chest', (0, 0, s*14))
        turn('head', (0, 0, -s*9))

for side, name in [('R', 'Jab'), ('L', 'Cross')]:
    action(name, [(1, guard), (4, lambda s=side: punch(s, 'windup')),
                  (7, lambda s=side: punch(s, 'hit')), (10, lambda s=side: punch(s, 'hit')),
                  (16, guard), (22, guard)])

def flex(angle):
    turn('forearm.R', (-angle, 0, 0))

action('ElbowFlex', [(1, lambda: flex(0)), (13, lambda: flex(90)),
                     (25, lambda: flex(125)), (37, lambda: flex(90)), (49, lambda: flex(0))])

def run(phase):
    wave = math.sin(phase)
    for s, side in [(-1, 'L'), (1, 'R')]:
        turn('upper_arm.'+side, (s*wave*38-8, -s*5, 0))
        turn('forearm.'+side, (-65-s*wave*20, 0, 0))
        turn('thigh.'+side, (-s*wave*34, 0, 0))
        turn('shin.'+side, (max(0, s*wave)*72+8, 0, 0))
        turn('foot.'+side, (-max(0, s*wave)*20, 0, 0))
    turn('spine', (7, 0, wave*4))
    rig.pose.bones['hips'].location.y = .015*abs(wave)

action('Run', [(frame, lambda p=phase: run(p))
               for frame, phase in [(1, 0), (7, math.pi/2), (13, math.pi),
                                    (19, 3*math.pi/2), (25, 2*math.pi)]])

rig.animation_data.action = None
rest()
scene.frame_set(0)
bpy.context.view_layer.update()

# Verify evaluated skin deformation: isolated right forearm rotates while shoulder stays put.
indices = [v.index for v in body.data.vertices if any(
    body.vertex_groups[g.group].name == 'hand.R' and g.weight > .99 for g in v.groups)]
assert indices
deps = bpy.context.evaluated_depsgraph_get()
def hand_center():
    bpy.context.view_layer.update()
    evaluated = body.evaluated_get(deps)
    return sum((evaluated.data.vertices[i].co for i in indices), Vector())/len(indices)
straight = hand_center()
flex(90)
bent = hand_center()
assert (straight-bent).length > .22, (straight, bent)
assert bent.z > straight.z+.15
rest()

source = ROOT / 'assets/source/pam_ps1_rig.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(source))
bpy.ops.object.select_all(action='SELECT')
output = ROOT / 'assets/models/pam_ps1_rig.glb'
bpy.ops.export_scene.gltf(
    filepath=str(output), export_format='GLB', export_yup=True,
    export_animations=True, export_animation_mode='NLA_TRACKS',
    export_frame_range=False, export_skins=True, export_all_influences=False,
    export_vertex_color='ACTIVE', export_all_vertex_colors=False,
)

# Preserve the same original atlas/unlit vertex-color treatment as revision 04.
blob = output.read_bytes()
offset, chunks = 12, []
while offset < len(blob):
    length, kind = struct.unpack_from('<II', blob, offset)
    chunks.append((kind, blob[offset+8:offset+8+length]))
    offset += 8+length
asset = json.loads(next(data for kind, data in chunks if kind == 0x4E4F534A))
assert len(asset['materials']) == 1
for mat in asset['materials']:
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
packed = [(0x4E4F534A, payload)]+[(k, d) for k, d in chunks if k != 0x4E4F534A]
binary = b''.join(struct.pack('<II', len(d), k)+d for k, d in packed)
output.write_bytes(struct.pack('<III', 0x46546C67, 2, len(binary)+12)+binary)

assert len(asset['skins']) == 1
assert len(asset['skins'][0]['joints']) == 22
assert {a['name'] for a in asset['animations']} == {'Guard', 'Jab', 'Cross', 'ElbowFlex', 'Run'}
triangles = sum(asset['accessors'][p['indices']]['count']//3
                for m in asset['meshes'] for p in m['primitives'])
metadata = {'revision': 5, 'triangles': triangles, 'bones': 22, 'skins': 1,
            'materials': 1, 'atlas': [128, 128], 'max_vertex_influences': 2,
            'animations': [a['name'] for a in asset['animations']],
            'elbow_flex_test_hand_travel': round((straight-bent).length, 4),
            'commercial_models_used': False}
(ROOT / 'assets/source/pam_ps1_rig_metadata.json').write_text(json.dumps(metadata, indent=2))
print('PAM_SKINNED_RIG_OK', json.dumps(metadata))
