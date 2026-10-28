"""Bind the original NPC meshes, then bake native glTF FK animation clips.

Blender 4.3.2. No add-on, runtime IK dependency or changes to the supplied art.
Run per character: blender -b -t 4 -P tools/npc/build.py -- januri
"""
import bpy
import hashlib
import json
import math
import sys
import numpy as np
from pathlib import Path
from mathutils import Matrix, Vector, Euler

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,str(ROOT/'tools/user_model'))
from profiles import PROFILES
from retarget import Retargeter
from preserve_normals import restore

ROLE = sys.argv[sys.argv.index('--')+1]
cfg = PROFILES[ROLE]
SOURCE = ROOT/f'assets/source/npcs/{ROLE}_original.glb'
OUT = ROOT/f'assets/source/npcs/{ROLE}_rig.blend'
GLB = ROOT/f'assets/models/npc_{ROLE}_rig.glb'
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(SOURCE))
body = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
body.name = ROLE.capitalize()+'Body'
body.data.transform(body.matrix_world)
body.matrix_world = Matrix.Identity(4)
original_positions = [v.co.copy() for v in body.data.vertices]
minimum = min(v.co.z for v in body.data.vertices)
height = max(v.co.z for v in body.data.vertices)-minimum
factor = cfg['height']/height
body.data.transform(Matrix.Translation((0,0,-minimum)))
body.data.transform(Matrix.Scale(factor,4))
rest_positions = [v.co.copy() for v in body.data.vertices]
triangles = len(body.data.polygons)
armature = bpy.data.armatures.new(ROLE.capitalize()+'Skeleton')
rig = bpy.data.objects.new('NpcRig',armature)
bpy.context.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')


def bone(name,head,tail,parent=None,deform=True):
    item = armature.edit_bones.new(name)
    item.head = (Vector(head)-Vector((0,0,minimum)))*factor
    item.tail = (Vector(tail)-Vector((0,0,minimum)))*factor
    item.use_deform = deform
    if parent:
        item.parent = armature.edit_bones[parent]
        item.use_connect = (item.head-item.parent.tail).length < .000001


bone('root',(0,0,.012),(0,0,.10),deform=False)
bone('hips',(0,.005,cfg['hips']),(0,.005,cfg['spine']),'root')
bone('spine',(0,.005,cfg['spine']),(0,.005,cfg['chest']),'hips')
bone('chest',(0,.005,cfg['chest']),(0,.005,cfg['neck']),'spine')
bone('neck',(0,.005,cfg['neck']),(0,.005,cfg['head']),'chest')
bone('head',(0,.005,cfg['head']),(0,.005,cfg['head_tip']),'neck')
for sign,side in [(-1,'L'),(1,'R')]:
    def point(key):
        x,y,z = cfg[key]
        return (sign*x,y,z)
    bone('clavicle.'+side,(0,.005,cfg['neck']-.015),point('shoulder'),'chest')
    bone('upper_arm.'+side,point('shoulder'),point('elbow'),'clavicle.'+side)
    bone('forearm.'+side,point('elbow'),point('wrist'),'upper_arm.'+side)
    bone('hand.'+side,point('wrist'),point('hand_end'),'forearm.'+side)
    bone('thigh.'+side,point('thigh'),point('knee'),'hips')
    bone('shin.'+side,point('knee'),point('ankle'),'thigh.'+side)
    bone('foot.'+side,point('ankle'),point('toe'),'shin.'+side)
    bone('toe.'+side,point('toe'),point('toe_end'),'foot.'+side)
chains = {}
for prefix,points in cfg['tails']:
    chains[prefix] = []
    parent = 'hips'
    for i in range(len(points)-1):
        name = '%s.%02d' % (prefix,i+1)
        bone(name,points[i],points[i+1],parent,False)
        chains[prefix].append(name)
        parent = name
if cfg.get('ribbon'):
    chains['ribbon'] = []
    points = cfg['ribbon']
    parent = 'head'
    for i in range(len(points)-1):
        name = 'ribbon.%02d' % (i+1)
        bone(name,points[i],points[i+1],parent,False)
        chains['ribbon'].append(name)
        parent = name
for name,(head,tail,parent) in cfg['extras'].items():
    bone(name,head,tail,parent,False)
bpy.ops.object.mode_set(mode='OBJECT')
for item in rig.pose.bones:
    item.rotation_mode = 'QUATERNION'
rig.show_in_front = True
armature.display_type = 'OCTAHEDRAL'
bpy.ops.object.select_all(action='DESELECT')
body.select_set(True)
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
try:
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
except RuntimeError as error:
    print('NPC_HEAT_FALLBACK',str(error),flush=True)
body.parent = rig
body.matrix_parent_inverse = Matrix.Identity(4)
modifier = next((m for m in body.modifiers if m.type == 'ARMATURE'),None)
if modifier is None:
    modifier = body.modifiers.new('NpcSkin','ARMATURE')
modifier.object = rig
modifier.use_deform_preserve_volume = False
for item in armature.bones:
    if item.name != 'root':
        item.use_deform = True
    if body.vertex_groups.get(item.name) is None:
        body.vertex_groups.new(name=item.name)


def assign(vertex,values):
    values = {name:weight for name,weight in values.items() if weight > .000001}
    total = sum(values.values())
    assert total > 0
    for group in list(vertex.groups):
        body.vertex_groups[group.group].remove([vertex.index])
    for name,weight in values.items():
        body.vertex_groups[name].add([vertex.index],weight/total,'REPLACE')


def distance(point,item):
    a,d = item.head_local,item.tail_local-item.head_local
    t = max(0,min(1,(point-a).dot(d)/d.length_squared))
    return (point-a-d*t).length,t


def closest(vertex,names):
    candidates = sorted((distance(vertex.co,armature.bones[n])[0],n) for n in names)[:3]
    return {name:1/max(.008,d)**4 for d,name in candidates}


def chain_weights(vertex,names):
    d,index,t = min((distance(vertex.co,armature.bones[name])[0],i,distance(vertex.co,armature.bones[name])[1]) for i,name in enumerate(names))
    if index == len(names)-1:
        return {names[index]:1}
    return {names[index]:1-t,names[index+1]:t}


# Sample the original albedo to distinguish rigid shell/hat/beard surfaces from
# adjacent robe/skin. Sampling does not edit, resave or replace any texture.
material = body.data.materials[0]
image = next(n.image for n in material.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image and n.image.colorspace_settings.name == 'sRGB')
width,height_pixels = image.size
pixels = np.empty(width*height_pixels*4,dtype=np.float32)
image.pixels.foreach_get(pixels)
colors = {}
uv = body.data.uv_layers.active.data
for index,loop in enumerate(body.data.loops):
    if loop.vertex_index not in colors:
        u,v = uv[index].uv
        offset = (min(height_pixels-1,max(0,int(v*height_pixels)))*width+min(width-1,max(0,int(u*width))))*4
        colors[loop.vertex_index] = tuple(pixels[offset:offset+3])
counts = {'heat_unweighted_repaired':0,'protected_hands':0,'shell':0,'hat':0,'beard':0,'tails':0,'ribbon':0,'sheath':0}
base_names = [b.name for b in armature.bones if b.name not in cfg['extras'] and not b.name.startswith(('tail','ribbon')) and b.name != 'root']
for vertex in body.data.vertices:
    x,y,z = original_positions[vertex.index]
    side = 'L' if x < 0 else 'R'
    existing = {body.vertex_groups[g.group].name:g.weight for g in vertex.groups if g.weight > .000001}
    if not existing:
        counts['heat_unweighted_repaired'] += 1
        assign(vertex,closest(vertex,base_names))
    # Body sectors prevent opposite limbs or a nearby accessory stealing weights.
    if abs(x) > .20 and abs(z-cfg['shoulder'][2]) < .13 and abs(y) < .14:
        names = [n+'.'+side for n in ['clavicle','upper_arm','forearm','hand']]
        values = {n:w for n,w in existing.items() if n in names}
        assign(vertex,values if values else closest(vertex,names))
    elif z < cfg['knee'][2]+.06 and y < .105:
        names = [n+'.'+side for n in ['thigh','shin','foot','toe']]
        values = {n:w for n,w in existing.items() if n in names}
        assign(vertex,values if values else closest(vertex,names))
    r,g,b = colors[vertex.index]
    shell = ROLE == 'januri' and .225 < z < .81 and abs(x) < .29 and (y > .14 or (y > .065 and (x/.285)**2+((z-.51)/.31)**2 < 1.12 and r > g*1.04))
    hat = 'hat' in cfg['extras'] and z > (.815 if ROLE == 'januri' else .70) and r > g*1.04 and g > b*1.06
    beard = ROLE == 'januri' and abs(x) < .065 and y < -.125 and .435 < z < .705 and min(r,g,b) > max(r,g,b)*.72 and max(r,g,b) > .15
    if shell:
        assign(vertex,{'shell':1}); counts['shell'] += 1
    elif hat:
        assign(vertex,{'hat':1}); counts['hat'] += 1
    elif beard:
        assign(vertex,{'beard':1}); counts['beard'] += 1
    elif z > cfg['head_full'] or (ROLE == 'lar' and z > .55 and y < -.16) or (ROLE == 'januri' and z > .65 and y < -.17):
        assign(vertex,{'head':1})
    elif abs(x) > cfg['hand_blend'] and abs(z-cfg['shoulder'][2]) < .13 and abs(y) < .14:
        t = max(0,min(1,(abs(x)-cfg['hand_blend'])/(cfg['hand_full']-cfg['hand_blend'])))
        t = t*t*(3-2*t)
        assign(vertex,{'hand.'+side:t,'forearm.'+side:1-t})
        if t == 1:
            counts['protected_hands'] += 1
    elif z < cfg['ankle'][2]+.012 and y < .105:
        t = max(0,min(.85,(-y-.055)/.10))
        assign(vertex,{'foot.'+side:1-t,'toe.'+side:t})
    if ROLE in ['inimigo','lar'] and y > .115 and z < .32 and (ROLE == 'inimigo' or x > .005):
        prefix = 'tail.L' if ROLE == 'inimigo' and x < 0 else ('tail.R' if ROLE == 'inimigo' else 'tail')
        assign(vertex,chain_weights(vertex,chains[prefix])); counts['tails'] += 1
    if cfg.get('ribbon') and y > (.12 if ROLE == 'inimigo' else .10) and z > (.54 if ROLE == 'inimigo' else .60):
        if ROLE == 'inimigo' or (r > g*1.5 and r > b*1.3):
            assign(vertex,chain_weights(vertex,chains['ribbon'])); counts['ribbon'] += 1
    if ROLE == 'lar' and .29 < z < .45 and distance(vertex.co,armature.bones['sheath'])[0] < .062*factor:
        assign(vertex,{'sheath':1}); counts['sheath'] += 1
bpy.ops.object.select_all(action='DESELECT')
body.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.object.vertex_group_limit_total(limit=4)
bpy.ops.object.vertex_group_normalize_all(lock_active=False)
for vertex in body.data.vertices:
    assert 1 <= len(vertex.groups) <= 4
    assert abs(sum(g.weight for g in vertex.groups)-1) < .0001
    assert (vertex.co-rest_positions[vertex.index]).length < .0000001
print('NPC_WEIGHTED',ROLE,json.dumps(counts),flush=True)

# Reuse only our original motion armature. None of the old character geometry
# or material replaces the supplied NPC. Exported files contain only the new skin.
with bpy.data.libraries.load(str(ROOT/'assets/source/pam_ps1_cartoon.blend'),link=False) as (data_from,data_to):
    data_to.objects = ['PamRig']
source = data_to.objects[0]
source.name = 'MotionReference'
bpy.context.collection.objects.link(source)
source_tracks = {t.name:t.strips[0].action for t in source.animation_data.nla_tracks}
for track in source.animation_data.nla_tracks:
    track.mute = True
solver = Retargeter(source,rig)
scene = bpy.context.scene
scene.render.fps = 30
scene.frame_start,scene.frame_end = 0,60
rig.animation_data_create()


def set_source(action,frame):
    source.animation_data.action = source_tracks[action]
    scene.frame_set(math.floor(frame),subframe=frame%1)


def body_pose(action,frame):
    set_source(action,frame)
    solver.retarget(action)
    # NPCs retain rigid accessories and anatomy; no inherited cartoon scale.
    for item in rig.pose.bones:
        item.scale = (1,1,1)
    bpy.context.view_layer.update()


def delta(name,angles):
    item = rig.pose.bones[name]
    rest = item.bone.matrix_local.to_quaternion()
    q = Euler(tuple(math.radians(a) for a in angles),'XYZ').to_quaternion()
    item.rotation_quaternion = rest.inverted()@q@rest@item.rotation_quaternion


def aim_punch(weight):
    if weight <= .00001:
        return
    names = ['upper_arm.R','forearm.R','hand.R']
    old = {name:rig.pose.bones[name].matrix_basis.copy() for name in names}
    shoulder = rig.pose.bones[names[0]].head.copy()
    root = rig.pose.bones['root'].matrix@rig.data.bones['root'].matrix_local.inverted()
    # Aim at the opposing fighter's torso. The original arm lengths are kept;
    # solve the elbow rather than enlarging a distant invisible damage box.
    goal = root@Vector((.12,-.56,.90+(cfg['height']-1.6)*.25))
    pole = root@Vector((.60,.02,cfg['shoulder'][2]*factor-.32))
    a,b = [rig.data.bones[name].length for name in names[:2]]
    axis = (goal-shoulder).normalized()
    reach = max(.025,min(a+b-.002,(goal-shoulder).length))
    bend = pole-shoulder
    bend = (bend-axis*bend.dot(axis)).normalized()
    along = (a*a-b*b+reach*reach)/(2*reach)
    elbow = shoulder+axis*along+bend*math.sqrt(max(0,a*a-along*along))
    wrist = shoulder+axis*reach
    for name,head,tail in [(names[0],shoulder,elbow),(names[1],elbow,wrist),(names[2],wrist,wrist+(wrist-elbow).normalized()*.15)]:
        rest = rig.data.bones[name]
        turn = (rest.tail_local-rest.head_local).rotation_difference(tail-head)
        rig.pose.bones[name].matrix = Matrix.LocRotScale(head,turn@rest.matrix_local.to_quaternion(),Vector((1,1,1)))
        bpy.context.view_layer.update()
    if weight < .999:
        posed = {name:rig.pose.bones[name].matrix_basis.copy() for name in names}
        for name in names:
            rig.pose.bones[name].matrix_basis = solver.interpolate_matrix(old[name],posed[name],weight)
        bpy.context.view_layer.update()


def pose(clip,t):
    if clip in ['Idle','Guard']:
        body_pose('Guard',t*60)
    elif clip in ['Walk','Run']:
        body_pose('Run',t*24)
    elif clip == 'Windup':
        body_pose('Jab',t*4)
    elif clip == 'Attack':
        # Contact near .12 s, matching the enemy's existing active window.
        keys = [(0,4),(.12,6),(.18,7),(.30,10),(.43,14),(.55,19)]
        seconds = t*.55
        i = next((i for i in range(len(keys)-1) if seconds <= keys[i+1][0]),len(keys)-2)
        a,b = keys[i],keys[i+1]
        body_pose('Jab',a[1]+(b[1]-a[1])*max(0,min(1,(seconds-a[0])/(b[0]-a[0]))))
        strength = min(1,seconds/.12) if seconds <= .18 else max(0,1-(seconds-.18)/.25)
        aim_punch(strength*strength*(3-2*strength))
    elif clip == 'Hit':
        body_pose('Guard',0)
        kick = math.sin(math.pi*min(1,t*1.8))*math.exp(-t*3)
        delta('chest',(-15*kick,0,8*kick))
        delta('head',(10*kick,0,-6*kick))
        delta('upper_arm.L',(-15*kick,0,-10*kick))
        delta('upper_arm.R',(-15*kick,0,10*kick))
    elif clip == 'Defeat':
        body_pose('Guard',0)
        w = min(1,t/.7); w = w*w*(3-2*w)
        delta('hips',(0,0,-12*w))
        delta('spine',(-12*w,0,8*w))
        delta('upper_arm.L',(25*w,0,-35*w))
        delta('upper_arm.R',(18*w,0,35*w))
        delta('root',((-78 if ROLE == 'januri' else 76)*w,0,0))
    elif clip == 'Power':
        body_pose('Spin',t*42)
    elif clip == 'ElbowFlex':
        body_pose('ElbowFlex',t*48)
    elif clip == 'KneeFlex':
        body_pose('KneeFlex',t*60)
    for prefix,names in chains.items():
        for index,name in enumerate(names):
            item = rig.pose.bones[name]
            item.matrix_basis = Matrix.Identity(4)
            amplitude = (2.0+index*1.5) if prefix.startswith('tail') else 2.5
            wave = math.sin(t*math.tau*2-index*.65)
            if clip in ['ElbowFlex','KneeFlex']:
                wave = 0
            item.rotation_quaternion = Euler((math.radians(wave*amplitude*.35),0,math.radians(wave*amplitude)),'XYZ').to_quaternion()
            if clip == 'Defeat' and prefix.startswith('tail') and index == 0:
                delta(name,(-58*min(1,t/.7),0,0))
    bpy.context.view_layer.update()
    if clip == 'Defeat':
        # Bake contact with the ground into the pose, rather than allowing a
        # fallen head, shell or tail to pass below the floor in the death shot.
        evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
        floor = min(v.co.z for v in evaluated.data.vertices)
        matrix = rig.pose.bones['root'].matrix.copy()
        matrix.translation.z += .004-floor
        rig.pose.bones['root'].matrix = matrix
        bpy.context.view_layer.update()


durations = {'Idle':60,'Guard':60,'Walk':30,'Run':24,'Windup':15,'Attack':17,'Hit':15,'Defeat':30,'Power':42,'ElbowFlex':48,'KneeFlex':60}
for clip,end in durations.items():
    action = bpy.data.actions.new(ROLE+'_'+clip)
    rig.animation_data.action = None
    values = []
    for frame in range(end+1):
        pose(clip,frame/end)
        values.append({b.name:b.matrix_basis.copy() for b in rig.pose.bones})
    rig.animation_data.action = action
    for frame,value in enumerate(values):
        for item in rig.pose.bones:
            item.matrix_basis = value[item.name]
            for channel in ['location','rotation_quaternion','scale']:
                item.keyframe_insert(data_path=channel,frame=frame,group=item.name)
    track = rig.animation_data.nla_tracks.new()
    track.name = clip
    track.strips.new(clip,0,action)
    track.mute = True
    action.use_fake_user = True
    for curve in action.fcurves:
        for key in curve.keyframe_points:
            key.interpolation = 'LINEAR'
    rig.animation_data.action = None
    print('NPC_ANIMATED',ROLE,clip,end+1,flush=True)
source.animation_data.action = None
source.hide_viewport = True
source.hide_render = True
for item in rig.pose.bones:
    item.matrix_basis = Matrix.Identity(4)
scene.frame_set(0)
bpy.context.view_layer.update()
assert len(body.data.polygons) == triangles
assert all((v.co-rest_positions[v.index]).length < .0000001 for v in body.data.vertices)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
bpy.ops.object.select_all(action='DESELECT')
rig.select_set(True)
body.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=str(GLB),export_format='GLB',export_yup=True,use_selection=True,
    export_skins=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_frame_range=False)
normal_preservation = restore(SOURCE,GLB)
metadata = {'source':str(SOURCE.relative_to(ROOT)),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'name':ROLE,'role':cfg['role'],'bones':len(armature.bones),'triangles':triangles,'clips':list(durations),
    'uniform_scale':factor,'original_min_z':minimum,'height':cfg['height'],'weights':counts,
    'max_influences':4,'geometry_edited':False,'rest_pose':'Supplied T-pose','tail_chains':{p:len(n) for p,n in chains.items() if p.startswith('tail')},
    'rigid_accessories':list(cfg['extras']),'original_pbr_preserved':True,'normal_preservation':normal_preservation}
(ROOT/f'assets/source/npcs/{ROLE}_rig_metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
print('NPC_RIG_EXPORTED_OK',json.dumps(metadata),flush=True)
