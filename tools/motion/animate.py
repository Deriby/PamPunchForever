"""Full-body life, airborne/reaction and defeat clips on the supplied rigs.

blender -b -t 4 --python-exit-code 1 -P tools/motion/animate.py -- pam
Also accepts januri, inimigo and lar. Source art, weights/rest and combat reach
are preserved. Runtime root motion remains controlled by CharacterBody3D.
"""
import bpy
import hashlib
import json
import math
import sys
from pathlib import Path
from mathutils import Euler, Matrix, Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,str(ROOT/'tools/user_model'))
from merge import merge
from retarget import Retargeter

ROLE = sys.argv[sys.argv.index('--')+1]
PAM = ROLE == 'pam'
BLEND = ROOT/('assets/source/pam_usuario_rig.blend' if PAM else f'assets/source/npcs/{ROLE}_rig.blend')
GLB = ROOT/('assets/models/pam_usuario_rig.glb' if PAM else f'assets/models/npc_{ROLE}_rig.glb')
TEMP = ROOT/'build/motion'
TEMP.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(BLEND))
rig = bpy.data.objects['PamRig' if PAM else 'NpcRig']
source = bpy.data.objects['AnimationSource' if PAM else 'MotionReference']
body = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
scene = bpy.context.scene
scene.render.fps = 30
height = max(v.co.z for v in body.data.vertices)-min(v.co.z for v in body.data.vertices)
factor = height/1.7
solver = Retargeter(source,rig)
originals = {}
for track in rig.animation_data.nla_tracks:
    name = 'LifeBase_'+ROLE+'_'+track.name
    original = bpy.data.actions.get(name)
    if original is None:
        original = track.strips[0].action.copy()
        original.name = name
        original.use_fake_user = True
    originals[track.name] = original
    track.mute = True
for track in source.animation_data.nla_tracks: track.mute = True


def fingerprint():
    digest = hashlib.sha256()
    for vertex in body.data.vertices:
        digest.update(bytes(str((tuple(vertex.co),[(g.group,g.weight) for g in vertex.groups])),'ascii'))
    for bone in rig.data.bones:
        digest.update(bytes(str([tuple(row) for row in bone.matrix_local]),'ascii'))
    return digest.hexdigest()


unchanged = fingerprint()


def sample(name,time=0):
    action = originals[name]
    rig.animation_data.action = action
    frame = min(float(action.frame_range[1]),time*30)
    scene.frame_set(math.floor(frame),subframe=frame%1)
    bpy.context.view_layer.update()


def rotate(name,angles):
    item = rig.pose.bones[name]
    rest = item.bone.matrix_local.to_quaternion()
    turn = Euler(tuple(math.radians(a) for a in angles),'XYZ').to_quaternion()
    item.rotation_quaternion = rest.inverted()@turn@rest@item.rotation_quaternion


def shift(x=0,y=0,z=0):
    bpy.context.view_layer.update()
    matrix = rig.pose.bones['root'].matrix.copy()
    matrix.translation += Vector((x,y,z))*factor
    rig.pose.bones['root'].matrix = matrix


def keys(time,values):
    if time <= values[0][0]: return values[0][1]
    for (a,x),(b,y) in zip(values,values[1:]):
        if time <= b:
            t = (time-a)/(b-a)
            w = t*t*(3-2*t)
            return x*(1-w)+y*w
    return values[-1][1]


def plant(goals):
    bpy.context.view_layer.update()
    lower = 0
    for side,goal in goals.items():
        hip = rig.pose.bones['thigh.'+side].head
        reach = rig.data.bones['thigh.'+side].length+rig.data.bones['shin.'+side].length-.003
        horizontal = (hip.x-goal.x)**2+(hip.y-goal.y)**2
        lower = max(lower,hip.z-goal.z-math.sqrt(max(.0001,reach*reach-horizontal)))
    if lower > 0: shift(z=-lower/factor)
    for side,goal in goals.items(): solver.plant(side,goal,1)


def support():
    return {side:rig.pose.bones['foot.'+side].head.copy() for side in ['L','R']}


def ground():
    bpy.context.view_layer.update()
    evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    floor = min((evaluated.matrix_world@Vector(corner)).z for corner in evaluated.bound_box)
    shift(z=(.008-floor)/factor)
    bpy.context.view_layer.update()


def breathe(t,standing=True):
    wave = math.sin(math.tau*t/2)
    shift(x=.009*math.sin(math.tau*t/2),z=.012*wave)
    rotate('hips',(0,0,1.8*wave))
    rotate('chest',(2.2*wave,1.2*math.sin(math.tau*t/2+.4),-1.4*wave))
    rotate('head',(-1.5*math.sin(math.tau*t/2-.35),0,.8*wave))
    for sign,side in [(-1,'L'),(1,'R')]:
        rotate('clavicle.'+side,(0,0,sign*1.8*wave))
        rotate('forearm.'+side,(2.5*math.sin(math.tau*t/2-.4),0,0))


def airborne(t,fall=False):
    sample('Guard',0)
    if fall:
        wave = math.sin(math.tau*t/.8)
        rotate('spine',(-8,0,0)); rotate('chest',(5,0,3*wave))
        rotate('head',(-9,0,-2*wave))
        for sign,side in [(-1,'L'),(1,'R')]:
            rotate('upper_arm.'+side,(-8+sign*3*wave,0,sign*24))
            rotate('forearm.'+side,(-18,0,0))
            rotate('thigh.'+side,(5+sign*5*wave,0,sign*4))
            rotate('shin.'+side,(18-sign*4*wave,0,0))
            rotate('foot.'+side,(-12,0,0))
    else:
        tuck = keys(t,[(0,0),(.055,-.15),(.17,1),(.32,.82)])
        rotate('chest',(8*tuck,0,-4*tuck)); rotate('head',(-8*tuck,0,3*tuck))
        for sign,side in [(-1,'L'),(1,'R')]:
            rotate('upper_arm.'+side,(-24*tuck,0,sign*12*tuck))
            rotate('forearm.'+side,(12*tuck,0,0))
            rotate('thigh.'+side,((-38 if sign>0 else -25)*tuck,0,sign*4*tuck))
            rotate('shin.'+side,((72 if sign>0 else 52)*tuck,0,0))
            rotate('foot.'+side,(-18*tuck,0,0))


def reaction(t,heavy=False):
    sample('Guard',0)
    goals = support()
    strength = 1.0 if not heavy else 1.35
    hit = keys(t,[(0,0),(.04,1),(.12,.8),(.23,-.14),(.40,0)] if not heavy else [(0,0),(.05,1),(.16,.85),(.30,.4),(.48,-.12),(.64,0)])
    lag = keys(max(0,t-.035),[(0,0),(.04,1),(.15,.7),(.32,0),(.64,0)])
    shift(y=.055*hit*strength,z=-.055*abs(hit)*strength)
    rotate('hips',(-7*hit,0,-10*hit))
    rotate('spine',(-18*hit*strength,0,12*hit))
    rotate('chest',(-14*hit*strength,0,9*hit))
    rotate('head',(12*lag*strength,0,-14*lag))
    for sign,side in [(-1,'L'),(1,'R')]:
        rotate('clavicle.'+side,(0,0,sign*6*hit))
        rotate('upper_arm.'+side,(35*hit,0,sign*30*hit))
        rotate('forearm.'+side,(-6*lag,0,sign*8*lag))
    plant(goals)


def death(t,back):
    sample('Guard',0)
    recoil = keys(t,[(0,0),(.07,1),(.19,.7),(.45,0)])
    collapse = keys(t,[(0,0),(.12,0),(.34,.45),(.64,1),(.74,.94),(.94,1),(1.2,1)])
    settle = keys(t,[(0,0),(.44,0),(.64,1),(.79,-.3),(.98,0),(1.2,0)])
    sign = -1 if back else 1
    rotate('root',(sign*88*collapse,0,(-7 if back else 9)*collapse))
    rotate('hips',(-5*recoil-14*collapse,0,10*collapse))
    rotate('spine',(-18*recoil+12*collapse,0,-8*collapse))
    rotate('chest',(-12*recoil+10*collapse,0,5*settle))
    rotate('head',(18*recoil-12*collapse+9*settle,0,-10*collapse))
    for s,side in [(-1,'L'),(1,'R')]:
        rotate('upper_arm.'+side,((28 if back else -28)*collapse+18*recoil,0,s*(28*collapse+12*recoil)))
        rotate('forearm.'+side,((-24 if back else -38)*collapse-12*settle,0,0))
        rotate('thigh.'+side,((-22 if s>0 else -10)*collapse,0,s*9*collapse))
        rotate('shin.'+side,((52 if s>0 else 32)*collapse+10*settle,0,0))
        rotate('foot.'+side,(-12*collapse,0,0))
    shift(y=(.09 if back else -.08)*collapse,z=-.04*recoil)
    # Avoid the old straight-board fall: stagger the limbs, impact and settle.
    # Floor correction is measured on the evaluated skinned mesh.
    ground()


def secondary(clip,t,duration):
    active = clip in ['Run','Walk','Attack','Power','DeathFall','Jump','Rise','Fall']
    for bone in rig.pose.bones:
        if bone.name.startswith(('tail.','ribbon.')):
            index = int(bone.name.split('.')[-1])-1
            amplitude = 5.5 if active else 2.3
            if clip in ['Death','DeathBack','Defeat']:
                amount = keys(t,[(0,0),(.25,.2),(.65,1),(.8,.88),(1.2,.9)])
                back = PAM or ROLE=='januri' or clip=='DeathBack'
                bend = ((98 if back else -98) if index==0 else -4)*amount if bone.name.startswith('tail') else 0
                rotate(bone.name,(bend,0,math.sin(t*9-index*.7)*5*math.exp(-t*2)))
            else:
                wave = math.sin(math.tau*t/(.8 if active else 2)-index*.7)
                rotate(bone.name,(wave*amplitude*.4,0,wave*amplitude))


def pose(clip,t,duration):
    if clip in ['Guard','Idle']:
        sample('Guard',t%2)
        goals = support(); breathe(t); plant(goals)
    elif clip in ['Run','Walk']:
        sample('Run',t/duration*.8)
        goals = support()
        phase = math.tau*t/duration
        shift(z=.018*(1-math.cos(phase*2)))
        rotate('hips',(0,0,4*math.sin(phase)))
        rotate('chest',(8,0,-7*math.sin(phase)))
        rotate('head',(-6,0,4*math.sin(phase-.3)))
        for sign,side in [(-1,'L'),(1,'R')]:
            rotate('upper_arm.'+side,(sign*10*math.sin(phase),0,sign*3))
            rotate('forearm.'+side,(8*math.sin(phase+sign*.5),0,0))
        plant(goals)
    elif clip in ['Rise','JumpStart']:
        airborne(t)
    elif clip == 'Fall': airborne(t,True)
    elif clip == 'Land':
        sample('Guard',0); goals = support()
        compress = keys(t,[(0,.1),(.05,1),(.13,-.12),(.24,0)])
        lag = keys(t,[(0,0),(.085,1),(.18,-.1),(.24,0)])
        shift(z=-.105*compress)
        rotate('spine',(12*compress,0,0)); rotate('chest',(8*lag,0,0)); rotate('head',(-12*lag,0,0))
        for sign,side in [(-1,'L'),(1,'R')]:
            rotate('upper_arm.'+side,(-16*lag,0,sign*12*lag))
            rotate('forearm.'+side,(12*lag,0,0))
        plant(goals)
    elif clip in ['Hit','HitHeavy']: reaction(t,clip=='HitHeavy')
    elif clip in ['Death','DeathBack','Defeat']:
        death(t,PAM or ROLE=='januri' or clip=='DeathBack')
    elif clip == 'DeathFall':
        airborne(t,True)
        rotate('root',(-18*math.sin(t*5),0,12*math.sin(t*7)))
        rotate('head',(-15,0,8*math.sin(t*10)))
        for sign,side in [(-1,'L'),(1,'R')]:
            rotate('upper_arm.'+side,(-20,0,sign*(24+12*math.sin(t*10+sign))))
            rotate('shin.'+side,(20+sign*18*math.sin(t*10),0,0))
    elif clip == 'Jump':
        if t < .16: airborne(t*.32/.16)
        elif t < .56: airborne(t-.16,True)
        else: pose('Land',min(.24,t-.56),.24)
        if t < .56: shift(z=.8*math.sin(math.pi*t/.56))
    elif clip == 'Windup':
        sample('Windup',t/duration*.5); goals = support()
        coil = keys(t,[(0,0),(.34,1),(.48,1)])
        shift(z=-.045*coil)
        rotate('hips',(0,0,-10*coil)); rotate('chest',(6*coil,0,-5*coil)); rotate('head',(-5*coil,0,9*coil))
        plant(goals)
    elif clip in ['Attack','Power']:
        sample(clip,t)
        # The authored wrist targets remain unchanged at contact. Follow-through
        # lives in head/hips, with the arms and visible damage reach retained.
        goals = support()
        pulse = keys(t,[(0,0),(.08,.5),(.13,1),(.22,.45),(.35,-.2),(.55,0)]) if clip=='Attack' else math.sin(t/duration*math.tau)
        rotate('head',(-6*pulse,0,5*pulse))
        if clip=='Attack':
            rotate('hips',(0,0,3*pulse))
            plant(goals)
    else: raise ValueError(clip)
    secondary(clip,t,duration)
    bpy.context.view_layer.update()
    if clip in ['Death','DeathBack','Defeat']: ground()


durations = {'Guard':2.0,'Run':.8,'JumpStart':.12,'Rise':.32,'Fall':.8,'Land':.24,
    'Hit':.4,'HitHeavy':.64,'Death':1.2,'DeathBack':1.2,'DeathFall':.8,'Jump':.8}
if not PAM: durations.update({'Idle':2.0,'Walk':1.0,'Windup':.48,'Attack':17/30,'Power':1.4,'Defeat':1.2})
for clip,duration in durations.items():
    poses = []
    end = round(duration*60)
    # Bake at 60 samples/s; glTF keeps native seconds and does not depend on FPS.
    for index in range(end+1):
        pose(clip,index/60,duration)
        poses.append({bone.name:bone.matrix_basis.copy() for bone in rig.pose.bones})
    for track in list(rig.animation_data.nla_tracks):
        if track.name == clip:
            old_action = track.strips[0].action
            rig.animation_data.nla_tracks.remove(track)
            if 'Life_'+clip in old_action.name: bpy.data.actions.remove(old_action)
    prefix = 'PamUser_' if PAM else ROLE+'_'
    action = bpy.data.actions.new(prefix+'Life_'+clip)
    rig.animation_data.action = action
    for index,value in enumerate(poses):
        for bone in rig.pose.bones:
            bone.matrix_basis = value[bone.name]
            bone.rotation_mode = 'QUATERNION'
            for path in ['location','rotation_quaternion','scale']:
                bone.keyframe_insert(data_path=path,frame=index/2,group=bone.name)
    track = rig.animation_data.nla_tracks.new()
    track.name = clip
    track.strips.new(clip,0,action)
    track.mute = True
    action.use_fake_user = True
    for curve in action.fcurves:
        for key in curve.keyframe_points: key.interpolation = 'LINEAR'
    rig.animation_data.action = None
    print('LIFE_CLIP_BAKED',ROLE,clip,duration,flush=True)

assert fingerprint() == unchanged,'Only animations may change'
for bone in rig.pose.bones: bone.matrix_basis = Matrix.Identity(4)
rig.animation_data.action = None
scene.frame_set(0)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND),compress=True)
bpy.ops.object.select_all(action='DESELECT')
rig.select_set(True);body.select_set(True)
bpy.context.view_layer.objects.active = rig
animated = TEMP/(ROLE+'_animated.glb')
bpy.ops.export_scene.gltf(filepath=str(animated),export_format='GLB',export_yup=True,use_selection=True,
    export_skins=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_frame_range=False,
    export_frame_step=1)
merge(GLB,animated,durations)
metadata_path = ROOT/('assets/source/pam_usuario_rig_metadata.json' if PAM else f'assets/source/npcs/{ROLE}_rig_metadata.json')
metadata = json.loads(metadata_path.read_text())
metadata['clips'] = [track.name for track in rig.animation_data.nla_tracks]
metadata['life_revision'] = 1
metadata['life_clips_seconds'] = durations
metadata['animation_only_art_weights_rest_unchanged'] = True
metadata_path.write_text(json.dumps(metadata,indent=2)+'\n')
print('LIFE_ANIMATION_EXPORT_OK',ROLE,json.dumps(durations),flush=True)
