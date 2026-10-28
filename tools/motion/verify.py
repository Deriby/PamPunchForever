"""Verify animation-only exports preserve original art, skin and combat streams."""
import json
import os
from pathlib import Path
from merge import read

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = Path(os.environ.get('PAM_MOTION_OUTPUT',ROOT/'build/motion_review'))
OUTPUT.mkdir(parents=True,exist_ok=True)
report = {}
for role in ['pam','januri','inimigo','lar']:
    target = ROOT/('assets/models/pam_usuario_rig.glb' if role=='pam' else f'assets/models/npc_{role}_rig.glb')
    old,old_data = read(ROOT/f'build/motion_baseline/{role}.glb')
    new,new_data = read(target)
    assert new_data[:len(old_data)] == old_data,'Original binary data must remain intact'
    for key in ['nodes','skins','meshes','materials','images','textures','samplers']:
        assert old.get(key) == new.get(key),(role,key)
    a = {clip['name']:clip for clip in old['animations']}
    b = {clip['name']:clip for clip in new['animations']}
    if role == 'pam':
        for clip in ['Spin','Medium','Strong','Combo','Jab','Cross','Kick','ElbowFlex','KneeFlex']:
            assert a[clip] == b[clip],(role,'Protected combat stream changed',clip)
    else:
        for clip in ['ElbowFlex','KneeFlex']: assert a[clip] == b[clip]
    required = ['Guard','Run','JumpStart','Rise','Fall','Land','Hit','HitHeavy','Death','DeathBack','DeathFall','Jump']
    assert all(clip in b for clip in required)
    report[role] = {'original_binary_prefix_preserved':True,'nodes_mesh_skin_materials_images_unchanged':True,
        'clips':list(b),'original_combat_streams_preserved':role=='pam'}
    print('MOTION_ART_AND_SKIN_PRESERVED',role,flush=True)
(OUTPUT/'art-preservation-report.json').write_text(json.dumps(report,indent=2)+'\n')
