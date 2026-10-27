"""Before/after and motion previews, made only from the actual GLB renders."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageChops

ROOT=Path(__file__).resolve().parents[2]
OUT=Path('/workspace/deliverables')
SRC=OUT/'pam_usuario'
MOTION=OUT/'pam_cartoon_v3'
DOC=ROOT/'docs/captures'
BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf'
REGULAR='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

def text(board,x,y,label,size=24,bold=True,color='#282c2c'):
    ImageDraw.Draw(board).text((x,y),label,fill=color,font=ImageFont.truetype(BOLD if bold else REGULAR,size))

board=Image.new('RGBA',(1900,1370),'#e6dfd0')
text(board,65,44,'PAM · SEU MODELO SEM O RABINHO',48)
text(board,70,120,'Edição localizada da malha · texturas originais preservadas',26,False,'#626a63')
for i,(name,label) in enumerate([('com_rabo_lado','ANTES'),('sem_rabo_lado','DEPOIS · REGIÃO FECHADA')]):
    text(board,70+i*925,210,label,28)
    image=Image.open(SRC/(name+'.png')).convert('RGBA').resize((840,980),Image.Resampling.LANCZOS)
    board.alpha_composite(image,(65+i*925,270))
text(board,70,1300,'Renders dos arquivos 3D · mesma câmera e iluminação',24,False,'#626a63')
board.convert('RGB').save(OUT/'Pam_Usuario_Sem_Rabo.png')
board.convert('RGB').save(DOC/'pam-usuario-sem-rabo.png')

board=Image.new('RGBA',(2040,1430),'#e6dfd0')
text(board,65,44,'PAM · MODELO FORNECIDO POR VOCÊ',45)
text(board,70,120,'Sem rabinho · rig completo · combo e giro adaptados às suas proporções',25,False,'#626a63')
for i,(name,label) in enumerate([('guarda','GUARDA'),('soco','SOCO'),('joelho','JOELHO ARTICULADO')]):
    text(board,65+i*675,210,label,26)
    image=Image.open(SRC/(name+'.png')).convert('RGBA')
    image=image.crop(image.getchannel('A').getbbox())
    image.thumbnail((600,1050),Image.Resampling.LANCZOS)
    board.alpha_composite(image,(65+i*675+(600-image.width)//2,280))
board.convert('RGB').save(OUT/'Pam_Usuario_Rig.png')
board.convert('RGB').save(DOC/'pam-usuario-rig.png')

def sequence(prefix):
    return [Image.open(p).convert('RGB') for p in sorted(MOTION.glob(prefix+'_[0-9][0-9][0-9].png'))]

combo,spin,guard,knees,run,elbows=[sequence(name) for name in ['combo','spin','guard','knees','run','elbows']]
assert [len(s) for s in [combo,spin,guard,knees,run,elbows]]==[67,43,19,61,25,49]

def bounds(images):
    boxes=[]
    for image in images:
        background=Image.new('RGB',image.size,image.getpixel((0,0)))
        mask=ImageChops.difference(image,background).convert('L').point(lambda v:255 if v>5 else 0)
        boxes.append(mask.getbbox())
    return (max(0,min(b[0] for b in boxes)-15),max(0,min(b[1] for b in boxes)-12),
        min(640,max(b[2] for b in boxes)+15),min(480,max(b[3] for b in boxes)+12))

def panel(board,image,box,x,width=550):
    image=image.crop(box)
    scale=min(width/image.width,520/image.height)
    image=image.resize((round(image.width*scale),round(image.height*scale)),Image.Resampling.NEAREST)
    board.paste(image,(x+(width-image.width)//2,132+(520-image.height)//2))

def gif(frames,name):
    sample=Image.new('RGB',(1920,90))
    for i in range(12):
        sample.paste(frames[round(i*(len(frames)-1)/11)].resize((160,90)),(i*160,0))
    palette=sample.quantize(colors=256)
    images=[f.quantize(palette=palette,dither=Image.Dither.NONE) for f in frames]
    durations=[[30,30,40][i%3] for i in range(len(images))]
    path=OUT/name
    images[0].save(path,save_all=True,append_images=images[1:],duration=durations,loop=0,disposal=2,optimize=False)
    return path

a,b=bounds(combo+guard),bounds(spin)
frames=[]
for i in range(84):
    frame=Image.new('RGB',(1280,720),'#e6dfd0')
    text(frame,45,23,'PAM · SEU MODELO COM RIG',34)
    text(frame,45,84,'COMBO CARTUNESCO',24)
    text(frame,690,84,'GIRO E ATERRISSAGEM',24)
    panel(frame,combo[i] if i<67 else guard[i-67],a,45)
    panel(frame,spin[i%42],b,690)
    text(frame,45,675,'Modelo enviado por você · sem rabinho · capturas reais no Godot',22,False,'#626a63')
    frames.append(frame)
path=gif(frames,'Pam_Usuario_Combate.gif')
(DOC/'pam-usuario-combate.gif').write_bytes(path.read_bytes())

a,b,c=bounds(knees),bounds(elbows),bounds(run)
frames=[]
for i in range(96):
    frame=Image.new('RGB',(1536,720),'#e6dfd0')
    text(frame,35,23,'PAM · ARTICULAÇÕES DO SEU MODELO',34)
    for x,label in [(35,'JOELHOS E TORNOZELOS'),(545,'COTOVELO'),(1055,'CORRIDA')]:
        text(frame,x,84,label,23)
    panel(frame,knees[min(i,60)],a,30,460)
    panel(frame,elbows[i%48],b,540,460)
    panel(frame,run[i%24],c,1050,460)
    text(frame,35,675,'Esqueleto de 22 ossos · pesos na malha · GLB reproduzido no Godot 4.4.1',22,False,'#626a63')
    frames.append(frame)
path=gif(frames,'Pam_Usuario_Articulacoes.gif')
(DOC/'pam-usuario-articulacoes.gif').write_bytes(path.read_bytes())
(DOC/'pam-usuario-verificacao.json').write_bytes((MOTION/'godot_user_report.json').read_bytes())
print('PAM_USER_PREVIEWS_OK')
