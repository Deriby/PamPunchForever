"""Compose real Godot captures; no generated/painted character imagery."""
from pathlib import Path
import json
import subprocess
from PIL import Image, ImageDraw, ImageFont, ImageChops

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path('/workspace/deliverables/pam_cartoon_v3')
OUTPUT = ROOT/'docs/captures'
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf'
REGULAR = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'


def label(canvas, xy, text, size, color='#263830', bold=True):
    ImageDraw.Draw(canvas).text(xy,text,fill=color,
        font=ImageFont.truetype(FONT if bold else REGULAR,size))


def sequence(name, count):
    return [Image.open(SOURCE/f'{name}_{i:03}.png').convert('RGB') for i in range(count)]


combo, spin, guard = sequence('combo',67), sequence('spin',43), sequence('guard',19)


def bounds(frames):
    boxes = []
    for frame in frames:
        diff = ImageChops.difference(frame,Image.new('RGB',frame.size,frame.getpixel((0,0))))
        box = diff.convert('L').point(lambda v: 255 if v > 5 else 0).getbbox()
        if box:
            boxes.append(box)
    return (max(0,min(b[0] for b in boxes)-18),max(0,min(b[1] for b in boxes)-12),
            min(640,max(b[2] for b in boxes)+18),min(480,max(b[3] for b in boxes)+12))


def paste(canvas, frame, box, x, width=555, height=520, y=135):
    image = frame.crop(box)
    scale = min(width/image.width,height/image.height)
    image = image.resize((round(image.width*scale),round(image.height*scale)),Image.Resampling.NEAREST)
    canvas.paste(image,(x+(width-image.width)//2,y+(height-image.height)//2))


combo_box, spin_box = bounds(combo+guard), bounds(spin)
frames = []
for i in range(84):
    board = Image.new('RGB',(1280,720),'#e6dfd0')
    label(board,(42,22),'PAM · MAIS ALCANCE, MÃOS CORRIGIDAS',34)
    label(board,(42,85),'SOCO → CRUZADO → CHUTE',24)
    label(board,(688,85),'GIRO MARCIAL',24)
    paste(board,combo[i] if i<67 else guard[i-67],combo_box,42)
    paste(board,spin[i%42],spin_box,688)
    label(board,(42,675),'Mais extensão no impacto · mãos estáveis · proporções recuperadas',22,'#526158',False)
    frames.append(board)

sample = Image.new('RGB',(1920,180))
for i in range(24):
    image = frames[round(i*(len(frames)-1)/23)].resize((160,90))
    sample.paste(image,((i%12)*160,(i//12)*90))
palette = sample.quantize(colors=256)
gif_frames = [frame.quantize(palette=palette,dither=Image.Dither.NONE) for frame in frames]
gif_frames[0].save(OUTPUT/'pam-usuario-cartoon-v3.gif',save_all=True,
    append_images=gif_frames[1:],duration=[[30,30,40][i%3] for i in range(84)],
    loop=0,disposal=2,optimize=False)

board = Image.new('RGB',(1536,720),'#e6dfd0')
label(board,(35,23),'PAM · ANTECIPAÇÃO, IMPACTO E RECUPERAÇÃO',33)
for x,title,index in [(24,'ANTECIPAÇÃO',4),(536,'IMPACTO',6),(1048,'GUARDA RECUPERADA',66)]:
    label(board,(x+10,85),title,22)
    paste(board,combo[index],combo_box,x,464,510)
label(board,(35,675),'Mesmo modelo e texturas · poses reais do GLB no Godot 4.4.1',21,'#526158',False)
board.save(OUTPUT/'pam-usuario-cartoon-v3.png')

# Same camera and identical crop/scale in both panels: the comparison must not
# fake the extra reach by enlarging the new character.
previous = Path('/workspace/deliverables/pam_cartoon_v2/combo_006.png')
if previous.exists():
    before = Image.open(previous).convert('RGB')
    shared_box = bounds([before,combo[6]])
    comparison = Image.new('RGB',(1280,720),'#e6dfd0')
    label(comparison,(42,22),'PAM · EXTENSÃO NO INSTANTE DO SOCO',33)
    for x,title,image in [(42,'ANTES',before),(688,'AGORA · MAIS ALCANCE',combo[6])]:
        label(comparison,(x,85),title,24)
        paste(comparison,image,shared_box,x)
    label(comparison,(42,675),'Mesma câmera e escala · geometria de repouso e texturas preservadas',21,'#526158',False)
    comparison.save(OUTPUT/'pam-usuario-alcance-v3.png')

hands = Image.new('RGB',(1280,620),'#e6dfd0')
label(hands,(40,20),'PAM · MÃOS E POLEGARES ESTÁVEIS',32)
for x,title,name in [(30,'GUARDA','hand_guard'),(670,'SOCO NO IMPACTO','hand_impact')]:
    label(hands,(x,78),title,22)
    image = Image.open(SOURCE/(name+'.png')).convert('RGB').resize((580,435),Image.Resampling.LANCZOS)
    hands.paste(image,(x,122))
label(hands,(40,580),'Detalhes reais no Godot · mesmos dedos esculpidos no modelo original',21,'#526158',False)
hands.save(OUTPUT/'pam-usuario-maos-v3.png')

movie_frames = SOURCE/'movie'
movie_frames.mkdir(exist_ok=True)
for i, frame in enumerate(frames):
    frame.save(movie_frames/f'{i:03}.png')
subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-framerate','30',
    '-i',str(movie_frames/'%03d.png'),'-c:v','libx264','-crf','19','-pix_fmt','yuv420p',
    '-movflags','+faststart',str(OUTPUT/'pam-usuario-cartoon-v3.mp4')],check=True)
report = json.loads((SOURCE/'godot_user_report.json').read_text())
report['hand_skinning_and_reach'] = json.loads((SOURCE/'hands.json').read_text())
(OUTPUT/'pam-usuario-cartoon-v3-verificacao.json').write_text(json.dumps(report,indent=2)+'\n')
print('PAM_CARTOON_V3_PREVIEWS_OK')
