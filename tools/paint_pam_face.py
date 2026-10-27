"""Paint an original UV face atlas for the actual low-poly mesh. No reference pixels used."""
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1]
S=512
yy,xx=np.mgrid[0:S,0:S]
x=xx/S*.96-.48;z=.40-yy/S*.70
front=np.zeros((S,S,3),dtype=float);front[:]=[238,220,200]
side=np.clip((np.abs(x)-.22)/.23,0,1)*.85
low=np.clip((-.02-z)/.27,0,1)
blend=np.clip(side*(.24+.5*low),0,.85)
front=front*(1-blend[...,None])+np.array([188,170,190])*blend[...,None]
warm=np.exp(-((x-.03)/.31)**2-((z-.27)/.15)**2)*.18
front=front*(1-warm[...,None])+np.array([233,198,180])*warm[...,None]
back=np.zeros_like(front);back[:]=[231,210,193]
b=np.clip((.17-z)/.43,0,1)[...,None]*.78
back=back*(1-b)+np.array([181,169,187])*b
im=Image.fromarray(np.uint8(np.clip(np.hstack([front,back]),0,255)))
d=ImageDraw.Draw(im)
def point(p):return ((p[0]+.48)/.96*S,(.40-p[1])/.70*S)
def curve(p0,p1,p2,p3):
 return [tuple((1-t)**3*np.array(p0)+3*(1-t)**2*t*np.array(p1)+3*(1-t)*t*t*np.array(p2)+t**3*np.array(p3)) for t in np.linspace(0,1,18)]
def path(start,segments):
 out=[start];last=start
 for a,b,c in segments:out+=curve(last,a,b,c);last=c
 return out
def poly(points,c):d.polygon([point(p) for p in points],fill=c)
# Cream muzzle is painted into a single continuous cheek/face surface.
p=path((-.30,-.105),[((-.19,-.028),(-.08,-.030),(0,-.045)),((.12,-.025),(.26,-.065),(.31,-.13)),((.25,-.24),(-.22,-.27),(-.30,-.105))])
poly(p,(246,229,205))
right=path((.077,.129),[((.09,.168),(.17,.236),(.238,.218)),((.29,.20),(.325,.13),(.312,.055)),((.305,-.018),(.254,-.063),(.20,-.054)),((.13,-.046),(.075,-.005),(.077,.129))])
white=path((.117,.074),[((.16,.073),(.21,.106),(.262,.132)),((.27,.087),(.25,.031),(.236,.020)),((.19,.010),(.145,.016),(.125,.028)),((.118,.037),(.116,.054),(.117,.074))])
for s in [-1,1]:
 mirror=lambda ps:[(s*a,b) for a,b in ps]
 poly(mirror(right),(29,26,34))
 # A restrained cool black facet under the outer corner.
 poly(mirror([(.256,-.032),(.296,.013),(.31,.060),(.29,-.008),(.25,-.05),(.20,-.054)]),(40,34,44))
 eye=Image.new('RGB',(S*2,S),(0,0,0));ed=ImageDraw.Draw(eye)
 ed.polygon([point(p) for p in mirror(white)],fill=(248,236,213))
 mask=Image.new('L',(S*2,S));md=ImageDraw.Draw(mask);md.polygon([point(p) for p in mirror(white)],fill=255)
 def ellipse(cx,cz,rx,rz,c):
  a=point((s*(cx-rx),cz+rz));b=point((s*(cx+rx),cz-rz))
  box=(min(a[0],b[0]),min(a[1],b[1]),max(a[0],b[0]),max(a[1],b[1]));ed.ellipse(box,fill=c)
 ellipse(.181,.061,.045,.060,(108,94,80))
 ellipse(.176,.064,.033,.055,(24,22,28))
 ellipse(.166,.075,.010,.011,(255,246,227))

 im.paste(eye,(0,0),mask)
 d=ImageDraw.Draw(im)
# Small nose bedding and an asymmetric confident mouth; painted, never floating.
poly([(-.062,-.032),(.063,-.032),(0,-.096)],(31,27,35))
smile=path((-.102,-.156),[((-.055,-.186),(.012,-.190),(.093,-.143))])
d.line([point(p) for p in smile],fill=(69,45,47),width=4)
d.line([point((.09,-.143)),point((.113,-.151))],fill=(69,45,47),width=3)
# Match the texture resolution and crisp painted detail of a retro character.
# Keep the 512-pixel face panel for clean review and mipmapped game import.
im.save(R/'assets/textures/pam_face.png')
print('Original face atlas:',im.size)
