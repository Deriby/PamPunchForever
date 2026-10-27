"""Assemble real Godot frames into timed cartoon/leg GIFs and a pose sheet."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageChops
import json

ROOT = Path(__file__).resolve().parents[2]
OUT = Path('/workspace/deliverables')
SRC = OUT / 'pam_cartoon'
DOC = ROOT / 'docs/captures'
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf'
REGULAR = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

def text(board, x, y, label, size=24, bold=True, color='#282c2c'):
    ImageDraw.Draw(board).text((x, y), label, fill=color,
        font=ImageFont.truetype(FONT if bold else REGULAR, size))

def sequence(prefix):
    return [Image.open(path).convert('RGB') for path in sorted(SRC.glob(prefix+'_[0-9][0-9][0-9].png'))]

combo, spin, guard, knees, run = [sequence(name) for name in ['combo', 'spin', 'guard', 'knees', 'run']]
assert [len(images) for images in [combo, spin, guard, knees, run]] == [67, 43, 49, 61, 25]

def bounds(images):
    boxes = []
    for image in images:
        background = Image.new('RGB', image.size, image.getpixel((0, 0)))
        mask = ImageChops.difference(image, background).convert('L').point(lambda v: 255 if v > 5 else 0)
        boxes.append(mask.getbbox())
    return (max(0, min(b[0] for b in boxes)-15), max(0, min(b[1] for b in boxes)-12),
            min(640, max(b[2] for b in boxes)+15), min(480, max(b[3] for b in boxes)+12))

def panel(board, image, box, x):
    image = image.crop(box)
    scale = min(550/image.width, 520/image.height)
    image = image.resize((round(image.width*scale), round(image.height*scale)), Image.Resampling.NEAREST)
    board.paste(image, (x+(550-image.width)//2, 132+(520-image.height)//2))

def gif(frames, filename):
    # A shared palette avoids frame-to-frame color flicker; 30/30/40 ms keeps
    # the authored 30 fps timing on GIF's centisecond clock.
    sample = Image.new('RGB', (160*12, 90))
    for i in range(12):
        image = frames[round(i*(len(frames)-1)/11)].resize((160, 90))
        sample.paste(image, (i*160, 0))
    palette = sample.quantize(colors=256)
    images = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    durations = [[30, 30, 40][i%3] for i in range(len(images))]
    images[0].save(OUT / filename, save_all=True, append_images=images[1:],
        duration=durations, loop=0, disposal=2, optimize=False)
    return OUT / filename

combo_box, spin_box = bounds(combo+guard), bounds(spin)
frames = []
for i in range(84):
    board = Image.new('RGB', (1280, 720), '#e6dfd0')
    text(board, 45, 23, 'PAM · COMBATE CARTUNESCO', 34)
    text(board, 45, 84, 'SOCO → CRUZADO → CHUTE', 24)
    text(board, 690, 84, 'GIRO · IMPULSO E ATERRISSAGEM', 24)
    panel(board, combo[i] if i < 67 else guard[30+i-67], combo_box, 45)
    panel(board, spin[i%42], spin_box, 690)
    text(board, 45, 675, 'Clipes reais no Godot 4.4.1 · antecipação, impacto e recuperação', 22, False, '#626a63')
    frames.append(board)
combat = gif(frames, 'Pam_Cartoon_06_Combate.gif')
(DOC / 'pam-cartoon-06-combate.gif').write_bytes(combat.read_bytes())

knee_box, run_box = bounds(knees), bounds(run)
frames = []
for i in range(72):
    board = Image.new('RGB', (1280, 720), '#e6dfd0')
    text(board, 45, 23, 'PAM · PERNAS ARTICULADAS', 34)
    text(board, 45, 84, 'JOELHOS E TORNOZELOS', 24)
    text(board, 690, 84, 'CORRIDA · CICLO COMPLETO', 24)
    panel(board, knees[min(i, 60)], knee_box, 45)
    panel(board, run[i%24], run_box, 690)
    text(board, 45, 675, 'Esqueleto e malha com pesos · movimento capturado no Godot', 22, False, '#626a63')
    frames.append(board)
legs = gif(frames, 'Pam_Cartoon_06_Pernas.gif')
(DOC / 'pam-cartoon-06-pernas.gif').write_bytes(legs.read_bytes())

board = Image.new('RGBA', (2220, 1700), '#e6dfd0')
text(board, 65, 45, 'PAM · ANIMAÇÃO CARTUNESCA 06', 52)
text(board, 70, 120, 'Braço e punho estendem no impacto · tronco acompanha · joelhos absorvem', 27, False, '#626a63')
for i, (name, label) in enumerate([('jab', '1 · SOCO'), ('cross', '2 · CRUZADO'), ('kick', '3 · CHUTE'),
        ('coil', 'PREPARAÇÃO DO GIRO'), ('landing', 'ATERRISSAGEM'), ('knee', 'JOELHO ARTICULADO')]):
    x, y = 60+(i%3)*735, 220+(i//3)*735
    text(board, x, y, label, 26)
    image = Image.open(SRC / (name+'.png')).convert('RGBA')
    image = image.crop(image.getchannel('A').getbbox())
    image.thumbnail((620, 620), Image.Resampling.LANCZOS)
    board.alpha_composite(image, (x+(620-image.width)//2, y+55))
board.convert('RGB').save(OUT / 'Pam_Cartoon_06_Poses.png')
board.convert('RGB').save(DOC / 'pam-cartoon-06-poses.png')
(DOC / 'pam-cartoon-06-verificacao.json').write_bytes((SRC / 'godot_cartoon_report.json').read_bytes())
print('PAM_CARTOON_PREVIEW_OK', combat, legs)
