"""Arrange renders of the actual Pam mesh; does not retouch character artwork."""
from PIL import Image,ImageDraw,ImageFont,ImageFilter
from pathlib import Path
import numpy as np
root=Path(__file__).resolve().parents[1]
src=Path('/workspace/deliverables/pam_v2')
w,h=2200,1400
rng=np.random.default_rng(8)
base=np.full((h,w,3),(231,221,203),dtype=np.int16)
base+=rng.integers(-2,3,(h,w,1),dtype=np.int16)
board=Image.fromarray(np.uint8(np.clip(base,0,255))).convert('RGBA')
d=ImageDraw.Draw(board)
ink='#352d30';muted='#7c6c65';red='#9d2b28'
font='/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf'
regular='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
def txt(x,y,t,size=22,color=ink,fontpath=font):
 d.text((x,y),t,fill=color,font=ImageFont.truetype(fontpath,size))
d.rectangle((64,58,81,194),fill=red)
txt(105,53,'PAM',105)
txt(111,167,'PUNCH FOREVER',25,red)
txt(1580,91,'MODELO 3D  /  REVISÃO 02',23,muted)
d.line((95,227,2105,227),fill='#bdb09c',width=2)
txt(943,296,'VISTAS DO MODELO',25)
d.line((943,340,2105,340),fill='#c6b9a4',width=1)

def place(name,center,baseline,maxsize):
 im=Image.open(src/(name+'.png')).convert('RGBA')
 box=im.getchannel('A').getbbox();im=im.crop(box)
 im.thumbnail(maxsize,Image.Resampling.LANCZOS)
 x=int(center-im.width/2);y=int(baseline-im.height)
 shadow=Image.new('RGBA',board.size)
 sd=ImageDraw.Draw(shadow)
 sd.ellipse((center-im.width*.30,baseline-8,center+im.width*.30,baseline+14),fill=(63,46,37,30))
 board.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(13)))
 board.alpha_composite(im,(x,y))
place('hero',450,1292,(760,1015))
for name,c,label in [('frente',1110,'FRENTE'),('lado',1510,'LADO'),('costas',1910,'COSTAS')]:
 place(name,c,1185,(390,640))
 f=ImageFont.truetype(font,21);width=d.textlength(label,font=f)
 txt(c-width/2,1230,label,21,muted)
txt(108,1324,'ESTUDO DE PERSONAGEM',17,muted,regular)
out=Path('/workspace/deliverables/Pam_Modelo_Previa_02.png')
board.convert('RGB').save(out)
(root/'docs/captures').mkdir(exist_ok=True)
board.convert('RGB').save(root/'docs/captures/pam-modelo-v2.png')
print(out)
