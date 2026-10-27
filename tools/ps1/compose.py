"""Compose actual model renders and nearest-upscaled native Godot captures."""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = Path('/workspace/deliverables')
SRC = OUT / 'pam_ps1'
DATA = json.loads((ROOT / 'assets/source/pam_ps1_metadata.json').read_text())
board = Image.new('RGBA', (2040, 1810), '#e6dfd0')
draw = ImageDraw.Draw(board)
bold = '/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf'
regular = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
ink = '#272a2a'
muted = '#616963'

def text(x, y, label, size=24, color=ink, weight=True):
    draw.text((x, y), label, fill=color,
              font=ImageFont.truetype(bold if weight else regular, size))

def model(name, x, y, height):
    image = Image.open(SRC / (name + '.png')).convert('RGBA')
    image = image.crop(image.getchannel('A').getbbox())
    image = image.resize((round(image.width * height / image.height), height),
                         Image.Resampling.LANCZOS)
    board.alpha_composite(image, (x, y))

draw.rectangle((60, 55, 77, 171), fill='#a5322f')
text(101, 41, 'PAM', 79)
text(106, 132, 'PUNCH FOREVER', 23, '#a5322f')
text(970, 61, 'ESTUDO 04 · DIREÇÃO PS1', 35)
text(970, 114, f"{DATA['triangles']} triângulos · 1 material · atlas 128×128", 24, muted, False)
text(970, 153, 'Modelo original · nova proposta em revisão', 21, muted, False)
draw.line((60, 207, 1980, 207), fill='#b7b6a9', width=2)

text(68, 243, 'MODELO 3D EXPORTADO', 23)
model('hero', 75, 303, 820)
text(840, 243, 'TOPOLOGIA REAL', 23)
model('wire', 850, 310, 720)
text(1510, 243, 'VISTA LATERAL', 23)
model('lado', 1535, 311, 480)
text(1520, 840, 'ATLAS ORIGINAL · 128×128', 19)
atlas = Image.open(ROOT / 'assets/textures/pam_ps1_atlas.png').convert('RGBA')
board.alpha_composite(atlas.resize((256, 256), Image.Resampling.NEAREST), (1555, 881))

draw.line((60, 1173, 1980, 1173), fill='#b7b6a9', width=2)
text(60, 1196, 'NO GODOT · 320×240 NATIVOS', 28)
text(1060, 1201, 'Poses do mesmo GLB · ampliação 2× sem suavização', 21, muted, False)
for i, (name, label) in enumerate([('idle', 'REPOUSO'), ('run', 'POSE DE CORRIDA'), ('punch', 'POSE DE SOCO')]):
    image = Image.open(SRC / ('native_' + name + '.png')).convert('RGBA')
    assert image.size == (320, 240)
    board.alpha_composite(image.resize((640, 480), Image.Resampling.NEAREST), (40 + i * 660, 1254))
    text(60 + i * 660, 1752, label, 21)

board.convert('RGB').save(OUT / 'Pam_Estudo_PS1_04.png')
board.convert('RGB').save(ROOT / 'docs/captures/pam-estudo-ps1.png')
print('PS1_PREVIEW_SHEET', OUT / 'Pam_Estudo_PS1_04.png')
