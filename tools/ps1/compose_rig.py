"""Review sheet and GIFs from the actual rigged GLB, with no character paint-over."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageChops

ROOT = Path(__file__).resolve().parents[2]
OUT = Path('/workspace/deliverables')
SRC = OUT / 'pam_ps1_rig'
DOC = ROOT / 'docs/captures'
DATA = json.loads((ROOT / 'assets/source/pam_ps1_rig_metadata.json').read_text())
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf'
REGULAR = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

def text(board, x, y, label, size=24, color='#282c2c', bold=True):
    ImageDraw.Draw(board).text((x, y), label, fill=color,
        font=ImageFont.truetype(BOLD if bold else REGULAR, size))

def model(board, key, x, y, height):
    image = Image.open(SRC / (key+'.png')).convert('RGBA')
    image = image.crop(image.getchannel('A').getbbox())
    image = image.resize((round(image.width*height/image.height), height), Image.Resampling.LANCZOS)
    board.alpha_composite(image, (x, y))

board = Image.new('RGBA', (2040, 1570), '#e6dfd0')
draw = ImageDraw.Draw(board)
draw.rectangle((60, 50, 77, 153), fill='#a5322f')
text(board, 102, 43, 'PAM · RIG 05', 65)
text(board, 1040, 60, 'COTOVELOS E PUNHOS ARTICULADOS', 29)
text(board, 1040, 112, f"{DATA['bones']} ossos · {DATA['triangles']} triângulos · malha com pesos", 24, '#626a63', False)
draw.line((60, 190, 1980, 190), fill='#b7b6a9', width=2)
text(board, 70, 220, 'GUARDA', 24)
text(board, 760, 220, 'EXTENSÃO DO SOCO · VISTA LATERAL', 24)
text(board, 1470, 220, 'ESQUELETO DO ARQUIVO', 24)
model(board, 'guard', 70, 280, 790)
model(board, 'jab', 750, 280, 790)
model(board, 'skeleton', 1430, 280, 790)
draw.line((60, 1120, 1980, 1120), fill='#b7b6a9', width=2)
for i, (key, label) in enumerate([('elbow90', 'COTOVELO · 90°'), ('elbow125', 'COTOVELO · 125°')]):
    image = Image.open(SRC / (key+'.png')).convert('RGBA').crop((20, 100, 960, 730))
    image.thumbnail((560, 340), Image.Resampling.LANCZOS)
    board.alpha_composite(image, (70+i*640, 1200))
    text(board, 70+i*640, 1150, label, 25)
text(board, 1430, 1170, 'VERIFICADO NO GODOT 4.4.1', 25)
text(board, 1430, 1230, 'Cotovelo a 90° com ombro parado.', 23, bold=False)
text(board, 1430, 1272, 'Mão acompanha o antebraço.', 23, bold=False)
text(board, 1430, 1314, '5 clipes importados no GLB.', 23, bold=False)
text(board, 1430, 1400, 'Estudo separado da fase atual.', 22, '#626a63', False)
board.convert('RGB').save(OUT / 'Pam_Rig_05.png')
board.convert('RGB').save(DOC / 'pam-rig-05.png')

# Tight framing is derived from all native frames, so no moving limb is cropped.
def load_sequence(prefix):
    images = [Image.open(path).convert('RGB') for path in sorted(SRC.glob(prefix+'_[0-9][0-9].png'))]
    assert len(images) >= 32
    boxes = []
    for image in images:
        background = Image.new('RGB', image.size, image.getpixel((0, 0)))
        mask = ImageChops.difference(image, background).convert('L').point(lambda value: 255 if value > 5 else 0)
        boxes.append(mask.getbbox())
    box = (max(0, min(b[0] for b in boxes)-20), max(0, min(b[1] for b in boxes)-10),
           min(640, max(b[2] for b in boxes)+20), min(480, max(b[3] for b in boxes)+10))
    return [image.crop(box) for image in images]

punches, flexes = load_sequence('punch'), load_sequence('flex')
frames = []
for i in range(64):
    frame = Image.new('RGB', (1280, 720), '#e6dfd0')
    text(frame, 45, 24, 'PAM · COTOVELOS E RIG', 35)
    text(frame, 45, 83, 'GUARDA → SOCO → RECUPERAÇÃO', 23)
    text(frame, 690, 83, 'DOBRA ISOLADA DO COTOVELO', 23)
    for x, image in [(45, punches[i % len(punches)]), (690, flexes[i//2])]:
        image = image.copy()
        image.thumbnail((540, 525), Image.Resampling.NEAREST)
        # Enlarge with integer pixels only; retain the real Godot image.
        scale = min(540/image.width, 525/image.height)
        image = image.resize((round(image.width*scale), round(image.height*scale)), Image.Resampling.NEAREST)
        frame.paste(image, (x+(540-image.width)//2, 130))
    text(frame, 45, 675, 'Capturas do GLB no Godot 4.4.1 · esqueleto e skin reais', 22, '#626a63', False)
    frames.append(frame)
frames[0].save(OUT / 'Pam_Rig_05_Movimento.gif', save_all=True, append_images=frames[1:],
               duration=50, loop=0, disposal=2, optimize=False)
(DOC / 'pam-rig-05-movimento.gif').write_bytes((OUT / 'Pam_Rig_05_Movimento.gif').read_bytes())
print('PAM_RIG_PREVIEW_OK', OUT / 'Pam_Rig_05.png', OUT / 'Pam_Rig_05_Movimento.gif')
