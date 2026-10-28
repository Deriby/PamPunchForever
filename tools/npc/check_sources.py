"""Verify editable Blender sources remain self-contained and retain all clips."""
import bpy
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = Path(os.environ.get('PAM_NPC_REVIEW_OUTPUT',ROOT/'build/npc_review'))
OUTPUT.mkdir(parents=True,exist_ok=True)
reports = {}
for role,expected in [('januri',25),('inimigo',32),('lar',30)]:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/f'assets/source/npcs/{role}_rig.blend'))
    rig = bpy.data.objects['NpcRig']
    assert rig.type == 'ARMATURE' and len(rig.data.bones) == expected
    clips = [track.name for track in rig.animation_data.nla_tracks]
    assert len(clips) == 11 and 'Attack' in clips and 'KneeFlex' in clips
    images = [im for im in bpy.data.images if im.source == 'FILE']
    assert len(images) >= 3
    assert all(im.packed_file is not None and tuple(im.size) == (4096,4096) for im in images)
    assert bpy.data.objects['MotionReference'].hide_render
    reports[role] = {'bones':expected,'clips':clips,'packed_images':[im.name for im in images]}
    print('NPC_BLENDER_SOURCE_OK',role,json.dumps(reports[role]),flush=True)
(OUTPUT/'blender-sources-verification.json').write_text(json.dumps(reports,indent=2)+'\n')
