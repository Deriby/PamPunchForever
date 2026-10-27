"""Contact sheet of unretouched renders of the actual Pam v3 mesh."""
from PIL import Image,ImageDraw,ImageFont,ImageFilter
from pathlib import Path
import numpy as np
root=Path(__file__).resolve().parents[1];src=Path('/workspace/deliverables/pam_v3')
w,h=2200,1500
rng=np.random.default_rng(9)
a=np.full((h,w,3),(232,223,208),dtype=np.int16)+rng.integers(-1,2,(h,w,1),dtype=np.int16)
board=Image.fromarray(np.uint8(a)).convert('RGBA');d=ImageDraw.Draw(board)
font='/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf';body='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
ink='#352c30';muted='#7d6e68';red='#9e2928'
def text(x,y,s,n=22,color=ink,f=font):d.text((x,y),s,fill=color,font=ImageFont.truetype(f,n))
def centered(x,y,s,n=20,color=muted):
 f=ImageFont.truetype(font,n);d.text((x-d.textlength(s,font=f)/2,y),s,fill=color,font=f)
d.rectangle((68,62,84,190),fill=red);text(109,53,'PAM',104);text(115,165,'PUNCH FOREVER',25,red)
text(1640,92,'MODELO 3D / ESTUDO 03',22,muted)
d.line((105,224,2095,224),fill='#c4b6a3',width=2)
def load(name):
 im=Image.open(src/(name+'.png')).convert('RGBA');return im.crop(im.getchannel('A').getbbox())
def place(im,center,baseline,size,shadow=True):
 im=im.copy();ratio=min(size[0]/im.width,size[1]/im.height);im=im.resize((round(im.width*ratio),round(im.height*ratio)),Image.Resampling.LANCZOS)
 x=round(center-im.width/2);y=round(baseline-im.height)
 if shadow:
  sh=Image.new('RGBA',board.size);sd=ImageDraw.Draw(sh)
  sd.ellipse((center-im.width*.32,baseline-8,center+im.width*.32,baseline+12),fill=(50,40,35,25));board.alpha_composite(sh.filter(ImageFilter.GaussianBlur(15)))
 board.alpha_composite(im,(x,y))
place(load('hero'),470,1400,(800,1120))
# Actual front render, cropped only to show the newly modeled face at review scale.
front=load('frente');face=front.crop((0,0,front.width,round(front.height*.45)))
place(face,1510,795,(780,470),False)
centered(1510,270,'ROSTO E EXPRESSÃO',19)
d.line((935,848,2095,848),fill='#c5b9a8',width=1)
for name,x,label in [('frente',1110,'FRENTE'),('lado',1510,'LADO'),('costas',1910,'COSTAS')]:
 place(load(name),x,1385,(330,490));centered(x,1415,label,19)
text(113,1431,'PRÉVIA DO MODELO',17,muted,body)
out=Path('/workspace/deliverables/Pam_Modelo_Previa_03.png');board.convert('RGB').save(out)
board.convert('RGB').save(root/'docs/captures/pam-modelo-v3.png')
print(out)
