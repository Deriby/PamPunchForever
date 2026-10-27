"""Original hand-directed painted atlases shared by the Fase 1 art library."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageFilter
import numpy as np,random,math
OUT=Path(__file__).resolve().parents[2]/'assets/textures/style';OUT.mkdir(parents=True,exist_ok=True)
random.seed(33);rng=np.random.default_rng(33)
S=256

def base(rgb,variation=6):
 noise=rng.normal(0,variation,(S,S,1));a=np.full((S,S,3),rgb,dtype=float)+noise
 return Image.fromarray(np.uint8(np.clip(a,0,255)))
def save(im,n):im.save(OUT/(n+'.png'))
# Materials are deliberately painted at low resolution, without photogrammetry.
for name,c in [('bark',(78,48,35)),('wood',(137,93,54)),('wood_dark',(93,57,37))]:
 im=base(c,4);d=ImageDraw.Draw(im)
 for i in range(70):
  x=random.randrange(S);y=random.randrange(S);l=random.randrange(8,100)
  v=random.choice([-25,-17,15,22]);color=tuple(max(0,min(255,k+v)) for k in c)
  d.line([(x,y),(x+random.randrange(-4,5),min(255,y+l//2)),(x+random.randrange(-5,6),min(255,y+l))],fill=color,width=random.choice([1,1,2]))
 for i in range(5):
  x=random.randrange(S);y=random.randrange(S)
  d.ellipse((x-7,y-15,x+7,y+15),outline=tuple(max(0,k-25) for k in c),width=2)
  d.arc((x-4,y-10,x+4,y+10),60,320,fill=tuple(k+12 for k in c),width=1)
 if name=='bark':
  for i in range(60):
   x=random.randrange(256);y=random.randrange(256);d.ellipse((x,y,x+random.randrange(2,12),y+random.randrange(2,9)),fill=random.choice(['#58633b','#41472e','#62734a']))
 save(im,name)
for name,c in [('leaf',(49,100,50)),('leaf_light',(91,132,53)),('leaf_dark',(28,70,46))]:
 im=base(c,3);d=ImageDraw.Draw(im)
 for j in range(9):
  for i in range(7):
   x=i*39+(j%2)*15-20;y=j*32-10
   d.polygon([(x,y+8),(x+15,y),(x+32,y+12),(x+17,y+27)],fill=tuple(min(255,k+random.randrange(-12,16)) for k in c))
   d.line((x+2,y+8,x+29,y+14),fill=tuple(k+20 for k in c),width=1)
 save(im,name)
# Longitudinal leaf blade texture with a midrib and diagonal veins.
im=base((62,117,54),3);d=ImageDraw.Draw(im)
for x in range(256):
 v=int(24*math.exp(-((x-128)/55)**2));d.line((x,0,x,255),fill=(54+v,104+v,42+v//2))
d.line((128,0,128,255),fill='#b4c167',width=3)
for y in range(-30,280,23):
 d.line((128,y,5,y+75),fill='#698e49',width=2);d.line((128,y,251,y+75),fill='#698e49',width=2)
save(im,'blade')
for name,c in [('stone',(113,127,112)),('moss',(87,109,57)),('cloth',(53,57,48)),('robe',(199,179,147)),('straw',(176,121,51)),('redwood',(147,46,37)),('earth',(217,204,177))]:
 im=base(c,3);d=ImageDraw.Draw(im)
 if name in ['stone','moss','earth']:
  for i in range(170):
   x=random.randrange(256);y=random.randrange(256);r=random.randrange(1,9);v=random.randrange(-20,20)
   color=tuple(max(0,min(255,k+v)) for k in c)
   d.polygon([(x,y),(x+r,y-2),(x+r+2,y+r),(x+2,y+r+2)],fill=color)
  if name=='earth':
   for i in range(50):
    x=random.randrange(256);y=random.randrange(256)
    d.ellipse((x,y,x+3,y+1),fill='#a99473')
    if i%3==0:d.line((x,y,x+5,y+4),fill='#eee2c8',width=1)
 elif name in ['cloth','robe']:
  for y in range(0,256,4):d.line((0,y,255,y),fill='#3b3f34' if name=='cloth' else '#c9b596',width=1)
  for x in range(0,256,5):d.line((x,0,x,255),fill='#303329' if name=='cloth' else '#bba483',width=1)
 elif name=='straw':
  for y in range(0,256,7):d.line((0,y,255,y),fill='#c89546',width=2)
  for x in range(0,256,9):d.line((x,0,x+18,255),fill='#8b5b2f',width=1)
 else:
  for x in range(0,256,21):d.line((x,0,x-3,255),fill='#742d28',width=2)
 save(im,name)
# Shell scutes, based on the supplied Jaburanga concept, painted into real UVs.
im=base((72,48,32),3);d=ImageDraw.Draw(im)
for cx,cy,r in [(128,128,68)]+[(128+math.cos(a*math.tau/6)*94,128+math.sin(a*math.tau/6)*91,46) for a in range(6)]:
 pts=[(cx+math.cos(a*math.tau/6+.2)*r,cy+math.sin(a*math.tau/6+.2)*r) for a in range(6)]
 d.polygon(pts,fill='#60452d',outline='#2e251d',width=5)
 spiral=[]
 for t in np.linspace(0,math.tau*1.7,45):
  rr=r*.67*(1-t/(math.tau*2));spiral.append((cx+math.cos(t)*rr,cy+math.sin(t)*rr))
 d.line(spiral,fill='#a07743',width=5)
 d.line([(x+2,y+3) for x,y in spiral],fill='#3e3022',width=2)
save(im,'shell')
# Three expressive masks and a stern old turtle face, all original paint.
font='/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf'
for name in ['jaburanga','guardian','guardian_scout','assassin']:
 colors={'jaburanga':(125,139,65),'guardian':(153,103,51),'guardian_scout':(157,163,113),'assassin':(218,207,183)}
 im=base(colors[name],2);d=ImageDraw.Draw(im)
 if name=='jaburanga':
  for i in range(95):
   x=random.randrange(256);y=random.randrange(256)
   d.arc((x,y,x+random.randrange(5,14),y+8),10,170,fill='#6c783b',width=1)
  for s in [-1,1]:
   mirror=lambda ps:[(128+s*(x-128),y) for x,y in ps]
   d.polygon(mirror([(143,115),(211,99),(211,124),(146,131)]),fill='#f0dfb0')
   d.polygon(mirror([(163,113),(177,109),(177,129),(163,130)]),fill='#242723')
   d.line(mirror([(140,109),(165,97),(216,94)]),fill='#48532b',width=8)
   d.line(mirror([(146,141),(195,137)]),fill='#8b8e4b',width=2)
   d.ellipse((128+s*20-3,166,128+s*20+3,172),fill='#46502c')
  d.line((92,190,128,196,170,185),fill='#50532b',width=3)
 else:
  if name!='assassin':
   for x in range(5,256,16):d.line((x,0,x+random.randrange(-7,8),255),fill='#765b3f' if name=='guardian' else '#80805d',width=1)
  # Set-back dark eye sockets with narrow bright eyes.
  for s in [-1,1]:
   pts=[(128+s*(x-128),y) for x,y in [(143,103),(211,82),(208,111),(144,126)]]
   d.polygon(pts,fill='#20282a' if name!='assassin' else '#252331')
   d.line([(128+s*29,111),(128+s*65,99)],fill='#b8d69f' if name!='assassin' else '#bb5543',width=4)
  d.polygon([(128,116),(111,166),(128,176),(142,165)],fill='#a18153' if name!='assassin' else '#b8aa98')
  d.line((102,205,128,196,155,205),fill='#4b4938' if name!='assassin' else '#8b8176',width=3)
  if name=='assassin':
   d.polygon([(173,0),(153,66),(167,82),(146,142),(164,124),(153,168),(190,104),(173,80),(195,11)],fill='#8d3533')
  else:
   d.line((85,27,128,46,170,24),fill='#d4c694',width=5)
   d.polygon([(109,46),(128,64),(146,46),(128,87)],fill='#455b4a' if name=='guardian' else '#536d68')
 save(im,'face_'+name)
# Crate stencil, not copied from Crash or a real cultural symbol.
im=base((137,93,54),4);d=ImageDraw.Draw(im)
for x in range(0,256,64):d.line((x,0,x,255),fill='#59432d',width=4)
for i in range(70):
 x=random.randrange(256);y=random.randrange(256);d.line((x,y,x+2,min(255,y+random.randrange(5,35))),fill='#a77745',width=1)
d.ellipse((87,76,169,162),outline='#dcc18b',width=7);d.line((107,138,149,100),fill='#dcc18b',width=6)
d.polygon([(118,130),(110,108),(125,115),(138,87),(140,111),(153,109),(135,132)],fill='#dcc18b')
save(im,'crate_stamp')
im=base((147,46,37),3);d=ImageDraw.Draw(im)
d.polygon([(128,51),(204,187),(52,187)],fill='#e3c388',outline='#6d302b',width=6)
d.text((104,91),'!',font=ImageFont.truetype(font,85),fill='#6c302c')
save(im,'tnt_stamp')
print('Painted original world atlases:',len(list(OUT.glob('*.png'))))
