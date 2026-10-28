"""Measure actual skinned reach and hand shape; run with Blender, no rendering."""
import bpy
import json
import math
import os
from pathlib import Path
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/source/pam_usuario_rig.blend'))
rig, body = bpy.data.objects['PamRig'], bpy.data.objects['PamBody']
scale = 1.5385457161116158
scene = bpy.context.scene
rig.animation_data.action = None
for track in rig.animation_data.nla_tracks:
    track.mute = True
hands = {side: [v for v in body.data.vertices if s*v.co.x/scale >= .455 and .43 < v.co.z/scale < .66]
         for side,s in [('L',-1),('R',1)]}
mixed = {}
for side, vertices in hands.items():
    mixed[side] = sum(1 for v in vertices if len(v.groups) != 1 or
        body.vertex_groups[v.groups[0].group].name != 'hand.'+side)
worst = 1.0
worst_pose = None
for clip in ['Guard','Jab','Cross','Kick','Combo','Spin','Run','Medium','Strong','Jump']:
    action = bpy.data.actions['PamUser_'+clip]
    rig.animation_data.action = action
    # Include the transitions between baked keys, where inherited scale can shear.
    for half in range(round(action.frame_range[1])*2+1):
        scene.frame_set(half//2,subframe=(half%2)*.5)
        for side in ['L','R']:
            bone = rig.pose.bones['hand.'+side]
            transform = bone.matrix@bone.bone.matrix_local.inverted()
            singular = np.linalg.svd(np.array(transform.to_3x3()))[1]
            anisotropy = float(max(singular)/min(singular))
            if anisotropy > worst:
                worst, worst_pose = anisotropy, [clip,half/2,side]

metrics = {}
for clip,frame,side in [('Jab',6,'R'),('Cross',7,'L'),('Kick',9,'R'),('Spin',15,'R'),('Medium',6,'R'),('Strong',9,'L')]:
    rig.animation_data.action = bpy.data.actions['PamUser_'+clip]
    scene.frame_set(frame)
    if clip == 'Kick':
        vertices = [v for v in body.data.vertices if v.co.x > 0 and v.co.z/scale < .09]
    else:
        vertices = hands[side]
    transforms = {b.name: b.matrix@b.bone.matrix_local.inverted() for b in rig.pose.bones}
    points = []
    for vertex in vertices:
        point = Vector((0,0,0))
        for group in vertex.groups:
            name = body.vertex_groups[group.group].name
            point += (transforms[name]@vertex.co)*group.weight
        points.append(point)
    metrics[clip] = {'forward_mesh_reach': max(-p.y for p in points),
                     'radial_mesh_reach': max(math.hypot(p.x,p.y) for p in points)}
report = {'hand_vertices': {s:len(v) for s,v in hands.items()},
          'hand_vertices_mixed_with_forearm': mixed,
          'maximum_hand_anisotropy': worst,'worst_pose': worst_pose,'reach': metrics}
baseline = os.environ.get('PAM_HAND_BASELINE')
if baseline:
    before = json.loads(Path(baseline).read_text())
    report['reach_increase_percent'] = {clip:
        (metrics[clip]['radial_mesh_reach' if clip == 'Spin' else 'forward_mesh_reach']/
         before['reach'][clip]['radial_mesh_reach' if clip == 'Spin' else 'forward_mesh_reach']-1)*100
        for clip in metrics if clip in before['reach']}
path = Path(os.environ.get('PAM_HAND_REPORT','/workspace/deliverables/pam_cartoon_v3/hands.json'))
path.parent.mkdir(parents=True,exist_ok=True)
path.write_text(json.dumps(report,indent=2)+'\n')
print('PAM_HAND_REACH_MEASURED',json.dumps(report),flush=True)
if not os.environ.get('PAM_HAND_CAPTURE_BASELINE'):
    assert not any(mixed.values()), mixed
    assert worst < 1.04, ('Hand must keep its shape through stretch',worst,worst_pose)
    assert metrics['Strong']['forward_mesh_reach'] > metrics['Medium']['forward_mesh_reach']+.10
    if baseline:
        assert report['reach_increase_percent']['Jab'] > 10
        assert report['reach_increase_percent']['Cross'] > 10
print('PAM_HAND_REACH_CHECK_OK',json.dumps(report))
