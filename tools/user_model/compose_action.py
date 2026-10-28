"""Present actual Fase 1 input captures, without changing the rendered character."""
import json
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path('/workspace/deliverables/pam_action')
OUTPUT = ROOT/'docs/captures'
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf'
REGULAR = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'


def text(board, point, label, size, color='#263830', bold=True):
    ImageDraw.Draw(board).text(point,label,fill=color,
        font=ImageFont.truetype(FONT if bold else REGULAR,size))


actions = [Image.open(SOURCE/f'action_{i:03}.png').convert('RGB') for i in range(60)]
jumps = [Image.open(SOURCE/f'jump_{i:03}.png').convert('RGB') for i in range(60)]
frames = []
for i in range(60):
    board = Image.new('RGB',(1280,720),'#e6dfd0')
    text(board,(38,20),'PAM · UM BOTÃO DE AÇÃO, UM DE PULO',33)
    text(board,(38,82),'J / X · GIRO → MÉDIO → FORTE',22)
    text(board,(680,82),'ESPAÇO / A · PULO + AÇÃO',22)
    left = actions[i].crop((60,15,580,465)).resize((555,480),Image.Resampling.NEAREST)
    right = jumps[i].resize((600,450),Image.Resampling.NEAREST)
    board.paste(left,(38,136))
    board.paste(right,(660,151))
    draw = ImageDraw.Draw(board)
    for x,trigger,label in [(45,0,'1º TOQUE'),(230,7,'2º TOQUE'),(415,16,'3º TOQUE')]:
        active = trigger <= i < trigger+4
        draw.rounded_rectangle((x,622,x+155,658),radius=6,fill='#a74932' if active else '#c8c4b5')
        text(board,(x+12,629),label,17,'#fff3d7' if active else '#526158')
    text(board,(38,682),'Pressione a cada golpe. Segure o pulo para subir mais alto.',20,'#526158',False)
    frames.append(board)
sample = Image.new('RGB',(1920,180))
for i in range(24):
    sample.paste(frames[round(i*59/23)].resize((160,90)),((i%12)*160,(i//12)*90))
palette = sample.quantize(colors=256)
images = [f.quantize(palette=palette,dither=Image.Dither.NONE) for f in frames]
images[0].save(OUTPUT/'pam-combo-acao.gif',save_all=True,append_images=images[1:],
    duration=[[30,30,40][i%3] for i in range(60)],loop=0,disposal=1,optimize=True)
movie = SOURCE/'movie'
movie.mkdir(exist_ok=True)
for i,frame in enumerate(frames):
    frame.save(movie/f'{i:03}.png')
subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-framerate','30','-i',
    str(movie/'%03d.png'),'-c:v','libx264','-crf','19','-pix_fmt','yuv420p','-movflags',
    '+faststart',str(OUTPUT/'pam-combo-acao.mp4')],check=True)
board = Image.new('RGB',(1920,620),'#e6dfd0')
text(board,(35,18),'PAM · GIRO → SOCO MÉDIO → SOCO FORTE',35)
for x,label,index in [(0,'1 · GIRO',6),(640,'2 · SOCO MÉDIO',16),(1280,'3 · SOCO FORTE',27)]:
    text(board,(x+25,82),label,24)
    board.paste(actions[index],(x,125))
board.save(OUTPUT/'pam-combo-acao.png')
report = json.loads((SOURCE/'capture-report.json').read_text())
report['hand_and_reach_check'] = json.loads((SOURCE/'hands.json').read_text())
(OUTPUT/'pam-combo-acao-verificacao.json').write_text(json.dumps(report,indent=2)+'\n')
print('PAM_ACTION_PREVIEW_OK')
