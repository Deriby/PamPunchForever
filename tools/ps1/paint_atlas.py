"""Original 128x128 character atlas. Budget is a design choice, not a measured Crash value."""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np
R=Path(__file__).resolve().parents[2];S=512
im=Image.new('RGB',(128,128),'#25202b');d=ImageDraw.Draw(im)
# Face panel: warm cream with lavender peripheral fur, designed as a 64px texture.
a=np.zeros((64,64,3),dtype=float)
for y in range(64):
 for x in range(64):
  xx=x/64*.84-.42;zz=.37-y/64*.65
  edge=max(0,min(1,(abs(xx)-.24)/.18));low=max(0,min(1,(.05-zz)/.33))
  a[y,x]=np.array([236,214,189])*(1-edge*low*.48)+np.array([159,144,174])*edge*low*.48
im.paste(Image.fromarray(np.uint8(a)),(0,0));d=ImageDraw.Draw(im)
def p(v):return ((v[0]+.42)/.84*64,(.37-v[1])/.65*64)
def poly(pts,c):d.polygon([p(v) for v in pts],fill=c)
poly([(-.29,-.11),(-.17,-.035),(0,-.03),(.18,-.04),(.30,-.13),(.17,-.25),(0,-.275),(-.18,-.24)],'#f2dcc0')
# Eyes, panda patches and nose use colored mesh faces in this study. Their
# boundaries are geometry, so a 64px facial panel never becomes a pixelated sticker.
# The face panel is reserved for broad fur/muzzle color transitions.
# Small garment panels, with broad painted planes rather than dense PBR grain.
d.rectangle((64,0,95,31),fill='#211b26');d.polygon([(64,0),(77,0),(69,31),(64,31)],fill='#38303b');d.line((88,2,89,28),fill='#130f18',width=1)
d.rectangle((96,0,127,31),fill='#a92c29');d.polygon([(122,1),(127,1),(127,31),(120,31)],fill='#77212c');d.polygon([(97,1),(104,1),(100,21)],fill='#bc3a30')
d.rectangle((64,32,95,63),fill='#ccb5b8');d.polygon([(64,32),(95,32),(95,45),(70,41)],fill='#e8cbb0');d.polygon([(64,50),(95,53),(95,63),(64,63)],fill='#a393ac')
d.rectangle((96,32,127,63),fill='#e8cbae');d.line((105,50,106,59),fill='#ae96a2',width=1);d.line((117,49,117,60),fill='#b59eab',width=1)
colors=['#1a1620','#2b2330','#453344','#8e262c','#b6352e','#e9d1b4','#d7b4aa','#b8a0b2','#90829f','#f5e4c6','#18151c','#695970','#251b24','#c34132','#74667d','#d7bca5']
for i,c in enumerate(colors):d.rectangle((i*8,80,i*8+7,95),fill=c)
d.rectangle((0,98,127,127),fill='#211b27')
OUT=R/'assets/textures/pam_ps1_atlas.png';im.save(OUT)
print('Atlas original:',OUT,'128 x 128')
