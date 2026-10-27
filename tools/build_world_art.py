"""Rebuild all Fase 1 supporting art; preserves the approved Pam asset byte-for-byte.
Run: python tools/style/paint.py && blender -b -t 4 -P tools/build_world_art.py
"""
from pathlib import Path
import os
PAM_ART_ROOT=Path(__file__).resolve().parents[1]
exec(compile((PAM_ART_ROOT/'tools/style/common.py').read_text(),'style/common.py','exec'),globals())
if os.environ.get('PAM_ART_SCOPE','all') in ['all','characters']:
 exec(compile((PAM_ART_ROOT/'tools/style/characters.py').read_text(),'style/characters.py','exec'),globals())
if os.environ.get('PAM_ART_SCOPE','all') in ['all','environment']:
 exec(compile((PAM_ART_ROOT/'tools/style/environment.py').read_text(),'style/environment.py','exec'),globals())
print('WORLD_ART_COMPLETE')
