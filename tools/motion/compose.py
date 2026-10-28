"""Caption real Godot renders of the animation revision, with no art retouching."""
import os
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(os.environ.get('PAM_MOTION_OUTPUT',ROOT/'build/motion_review'))
OUT = ROOT/'docs/captures'
TEMP = ROOT/'build/motion_captioned'
TEMP.mkdir(parents=True,exist_ok=True)
TITLE = ImageFont.truetype(str(ROOT/'assets/fonts/title.ttf'),32)
BODY = ImageFont.truetype(str(ROOT/'assets/fonts/body.ttf'),18)
SMALL = ImageFont.truetype(str(ROOT/'assets/fonts/body.ttf'),15)


def caption(index):
    im = Image.open(SOURCE/f'motion_{index:03}.png').convert('RGB')
    draw = ImageDraw.Draw(im)
    draw.text((38,25),'PAM · ANIMAÇÕES COM MAIS VIDA',font=TITLE,fill='#f9ecd3')
    time = index/30
    phase = 'Respiração e guarda'
    if .6 <= time < 1.4: phase = 'Corrida · tronco, braços e passos'
    elif 1.4 <= time < 2.2: phase = 'Pulo · subida, queda e aterrissagem'
    elif 2.2 <= time < 2.65: phase = 'Dano · recuo e recuperação'
    elif 2.65 <= time < 3.35: phase = 'Dano forte · desequilíbrio do corpo'
    elif 3.35 <= time < 4.95: phase = 'Morte · impacto, colapso e repouso'
    elif 4.95 <= time < 5.75: phase = 'Queda no vazio'
    draw.text((40,70),phase,font=BODY,fill='#e2e8db')
    for x,name in zip([185,488,792,1095],['PAM','JABURANGA','INIMIGO','LAR']):
        draw.text((x,635),name,font=BODY,fill='#f9ecd3',anchor='mt')
    draw.text((640,690),'Revisão de clipes no Godot 4.4.1 · modelos, texturas e rig preservados',font=SMALL,fill='#e2e8db',anchor='mm')
    return im


small = []
for index in range(186):
    im = caption(index)
    if index == 26: im.save(OUT/'animacoes-vivas.png')
    im.save(TEMP/f'frame_{index:03}.png')
    if index%2 == 0: small.append(im.resize((896,504),Image.Resampling.LANCZOS))
    im.close()
subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','30','-i',str(TEMP/'frame_%03d.png'),
    '-c:v','libx264','-threads','2','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'animacoes-vivas.mp4')],check=True)
sheet = Image.new('RGB',(256,144*len(small)))
for index,im in enumerate(small): sheet.paste(im.resize((256,144)),(0,144*index))
palette = sheet.quantize(240)
gif = [im.quantize(palette=palette,dither=Image.Dither.NONE) for im in small]
gif[0].save(OUT/'animacoes-vivas.gif',save_all=True,append_images=gif[1:],
    duration=[60,70,70]*31,optimize=True,disposal=1,loop=0)
for name in ['movimento-pulo-na-fase','movimento-dano-na-fase','movimento-mortes-na-fase']:
    Image.open(SOURCE/f'{name}.png').save(OUT/f'{name}.png')
print('MOTION_PREVIEWS_COMPOSED')
