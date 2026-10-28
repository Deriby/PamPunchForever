"""Caption actual Godot frames; no character synthesis or image retouching."""
import os
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(os.environ.get('PAM_NPC_REVIEW_OUTPUT',ROOT/'build/npc_review'))
OUT = ROOT/'docs/captures'
OUT.mkdir(parents=True,exist_ok=True)
TITLE = ImageFont.truetype(str(ROOT/'assets/fonts/title.ttf'),32)
BODY = ImageFont.truetype(str(ROOT/'assets/fonts/body.ttf'),19)
SMALL = ImageFont.truetype(str(ROOT/'assets/fonts/body.ttf'),15)
NAMES = [('JABURANGA','Januri.glb · 25 ossos'),('INIMIGO','Inimigo.glb · 32 ossos'),('LAR','Lar.glb · 30 ossos')]


def caption(path):
    im = Image.open(path).convert('RGB')
    draw = ImageDraw.Draw(im)
    draw.text((40,28),'PAM · NOVO ELENCO',font=TITLE,fill='#f9ecd3')
    draw.text((40,72),'Rigs e animações · captura real do Godot 4.4.1',font=BODY,fill='#dae5d8')
    for x,(name,detail) in zip([225,640,1055],NAMES):
        draw.text((x,620),name,font=BODY,fill='#f9ecd3',anchor='mt')
        draw.text((x,650),detail,font=SMALL,fill='#dae5d8',anchor='mt')
    draw.text((640,692),'Malhas e texturas fornecidas pelo usuário · cotovelos, joelhos e caudas articulados',font=SMALL,fill='#dae5d8',anchor='mm')
    return im


frames = [caption(SOURCE/f'showcase_{i:03}.png') for i in range(90)]
frames[0].save(OUT/'npcs-rig.png')
small = [im.resize((896,504),Image.Resampling.LANCZOS) for im in frames]
palette_source = Image.new('RGB',(320,180*len(small)))
for i,frame in enumerate(small):
    palette_source.paste(frame.resize((320,180)),(0,i*180))
palette = palette_source.quantize(240)
gif = [im.quantize(palette=palette,dither=Image.Dither.NONE) for im in small]
gif[0].save(OUT/'npcs-rig.gif',save_all=True,append_images=gif[1:],
    duration=[30,30,40]*30,loop=0,optimize=True,disposal=1)
# Encode the same unmodified 30-fps renders with their presentation captions.
temp = ROOT/'build/npc_captioned'
temp.mkdir(parents=True,exist_ok=True)
for i,im in enumerate(frames): im.save(temp/f'frame_{i:03}.png')
subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','30','-i',str(temp/'frame_%03d.png'),
    '-c:v','libx264','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'npcs-rig.mp4')],check=True)
for name in ['npc-prologo','npc-trilha','npc-ossos']:
    im = Image.open(SOURCE/f'{name}.png')
    im.save(OUT/f'{name}.png')
print('NPC_PREVIEWS_COMPOSED')
