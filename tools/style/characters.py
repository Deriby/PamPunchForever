"""All active Fase 1 characters, using the approved Pam's faceted painted language."""
def open_coat(root,name,z=.95,color='cloth',scale=1):
 t=empty('Torso',(0,0,z),root)
 chest=loft(name,[(-.27,.20,.145,.01),(.0,.245,.17,.015),(.25,.205,.15,.02)],color,t,12)
 return t

def fighter_arms(root,z,skin='ink',sleeve='cloth',arm_scale=1,braces=False):
 for s,label in [(-1,'L'),(1,'R')]:
  a=empty('Arm'+label,(s*.27,0,z),root)
  tube('Sleeve',[(0,0,0),(s*.06,0,-.14),(s*.09,-.025,-.26)],[.13,.125,.105],sleeve,a,9)
  tube('Forearm',[(s*.09,-.025,-.22),(s*.12,-.07,-.35)],[.108,.09],skin,a,9)
  if braces:
   block('Bracer',(s*.1,-.094,-.27),(.15,.10,.17),'wood_dark',a,.03)
   for h in [-.24,-.32]:
    points=[(s*.10+math.cos(i*math.tau/12)*.108,-.05+math.sin(i*math.tau/12)*.11,h) for i in range(13)]
    tube('Binding',points,[.012]*13,'cream',a,5)
  ico('Fist',(s*.12,-.078,-.40),(.105,.10,.115),skin,a,sub=2)
  ico('Thumb',(s*.065,-.155,-.385),(.05,.045,.07),skin,a,sub=1)

def fighter_legs(root,z=.57,color='ink',boots='wood_dark'):
 for s,label in [(-1,'L'),(1,'R')]:
  leg=empty('Leg'+label,(s*.16,0,z),root)
  tube('Trousers',[(0,0,0),(s*.015,.015,-.23),(s*.02,-.02,-.43)],[.125,.11,.08],color,leg,9)
  block('Foot',(s*.025,-.075,-.49),(.24,.35,.16),boots,leg,.045)
  for dz in [-.26,-.33]:
   tube('AnkleBinding',[(-.08,-.015,dz),(0,-.11,dz),(.085,-.02,dz)],[.012]*3,'seam',leg,5)

clear()
r=empty('Jaburanga');t=empty('Torso',(0,0,.83),r)
# Anatomical torso, vest and broad domed shell.
loft('Chest',[(-.27,.22,.17,-.015),(0,.25,.18,-.01),(.27,.20,.145,0)],'skin',t)
back=ico('Shell',(0,.15,.045),(.43,.225,.50),'shell',t,sub=2)
# Planar UVs on the actual dome keep scutes attached under rotation.
uv_project(back,'face',.46)
loft('Robe',[(-.22,.24,.17,-.025),(.02,.27,.185,-.015),(.23,.21,.155,-.02)],'robe',t,10)
for s in [-1,1]:
 panel('RobeFacing',[(s*.08,-.203,.20),(s*.17,-.197,.23),(s*.19,-.207,-.23),(s*.095,-.207,-.23)],'red',t)
 panel('RobeFold',[(s*.18,-.19,-.18),(s*.25,-.09,-.19),(s*.23,-.08,-.50),(s*.11,-.17,-.48)],'robe',t)
 panel('Trim',[(s*.10,-.21,-.17),(s*.18,-.20,-.18),(s*.155,-.20,-.48),(s*.095,-.205,-.47)],'red',t)
loft('Sash',[(-.17,.257,.188,-.02),(-.09,.259,.19,-.02)],'red',t)
block('ClothKnot',(.06,-.225,-.12),(.12,.07,.10),'redlight',t,.018)
# Face has a short beak, heavy integrated brow and texture-painted wrinkles.
h=empty('Head',(0,-.055,1.24),r)
headmesh=loft('TurtleFace',[(-.20,.13,.12,-.04),(-.12,.22,.23,-.04),(-.025,.24,.235,-.04),(.10,.215,.20,0),(.23,.15,.14,.01),(.26,.06,.07,.01)],face_material('jaburanga'),h,14)
headmesh.data.materials.append(M['skin']);face_uv(headmesh,.26,-.21,.28)
for p in headmesh.data.polygons:
 if p.center.y>.015:p.material_index=1
# The beard is a continuous faceted bundle, with smaller tapered side locks.
beard=loft('Beard',[(-.12,.15,.045,-.24),(-.22,.14,.055,-.25),(-.34,.105,.05,-.25),(-.47,.025,.022,-.245),(-.51,.008,.008,-.23)],'beard',h,10)
beard.data.materials.append(M['beard_shade'])
for f in beard.data.polygons:
 if f.center.x>.03:f.material_index=1
for s in [-1,1]:
 lock=loft('BeardLock',[(-.16,.042,.035,0),(-.31,.033,.03,0),(-.43,.004,.005,0)],'beard',h,7)
 lock.location=(s*.09,-.265,0)
# Layered woven hat with radial panels and a worn edge.
vs=[];segments=16
for radius,z in [(.035,.565),(.24,.49),(.44,.365),(.575,.275),(.58,.25)]:
 for i in range(segments):
  a=i*math.tau/segments;rr=radius*(1+.025*math.sin(i*2.7));vs.append((math.cos(a)*rr,math.sin(a)*rr,z))
fs=[]
for j in range(4):
 for i in range(segments):
  a=j*segments+i;b=j*segments+(i+1)%segments;fs.append((a,b,b+segments,a+segments))
hat=mesh('WovenHat',vs,fs,'straw',h);uv_project(hat,'box',3)
tube('HatRim',[(math.cos(i*math.tau/32)*.581,math.sin(i*math.tau/32)*.581,.25) for i in range(33)],[.014]*33,'wood_dark',h,5)
# Strong forearms, fingers, claws and an agile low stance.
for s,label in [(-1,'L'),(1,'R')]:
 a=empty('Arm'+label,(s*.27,-.03,1.055),r)
 tube('VestShoulder',[(0,0,0),(s*.035,0,-.14)],[.14,.14],'cloth',a,9)
 hx=-.21 if s<0 else .075
 hy=-.34 if s<0 else -.13
 tube('MuscularArm',[(s*.035,0,-.12),(s*.12,-.11,-.23),(hx,hy+.03,-.32)],[.13,.135,.095],'skin',a,10)
 ico('TurtleHand',(hx,hy,-.34),(.12,.10,.11),'skinlight',a,sub=2)
 for j in range(3):ico('FoldedFinger',(hx+(j-1)*.055,hy-.085,-.34),(.027,.045,.030),'skin',a,sub=1)
 l=empty('Leg'+label,(s*.20,.015,.49),r)
 tube('Leg',[(0,0,0),(s*.025,-.02,-.24),(s*.035,-.04,-.34)],[.14,.13,.10],'skinshade',l,9)
 foot=ico('TurtleFoot',(s*.035,-.13,-.37),(.18,.22,.11),'skinlight',l,sub=2)
 for j in range(3):ico('Claw',((j-1)*.085+s*.035,-.31,-.375),(.033,.085,.033),'ivory',l,sub=1)
staff=empty('Staff',(-.21,-.34,-.34),bpy.data.objects['ArmL'])
tube('GnarledStaff',[(0,0,-.69),(.025,.01,-.10),(-.025,0,.55),(.02,0,.90),(.105,0,1.00)],[.032,.035,.04,.055,.075],'bark',staff,8)
spiral=[]
for i in range(16):
 a=i/15*math.tau*1.15;radius=.12*(1-i/20);spiral.append((.10+math.cos(a)*radius,0,1.0+math.sin(a)*radius))
tube('CarvedCrook',spiral,[.035]*len(spiral),'wood_dark',staff,7)
for s in [-1,1]:panel('RedStaffRibbon',[(0,-.04,.67),(.07,-.05,.69),(.09+s*.035,-.07,.38),(.035,-.08,.43)],'red',staff)
save('jaburanga',True)

# Original masked ruin guardians: two silhouettes share the physical AI contract.
for key,scout in [('guardian',False),('guardian_scout',True)]:
 clear();r=empty('SentinelaDoIgarape' if scout else 'GuardiaoDoJatoba');t=open_coat(r,'Tunic',.86,'teal' if scout else 'cloth')
 # Fabric breast wrap and layered lower panels.
 for s in [-1,1]:
  panel('TunicTail',[(s*.03,-.158,-.19),(s*.205,-.11,-.18),(s*.23,-.10,-.44),(s*.07,-.18,-.40)],'teal' if scout else 'cloth',t)
  shoulder=block('LacqueredShoulder',(s*.255,0,.17),(.23,.30,.15),'wood_dark' if scout else 'wood',t,.04);shoulder.rotation_euler[1]=s*.20
 loft('WovenBelt',[(-.20,.25,.18,0),(-.12,.25,.18,0)],'ochre' if scout else 'red',t)
 panel('SashEnd',[(-.05,-.19,-.14),(.06,-.19,-.15),(.10,-.20,-.38),(.025,-.205,-.36)],'ochre' if scout else 'red',t)
 h=empty('Head',(0,-.012,1.26),r)
 hood=ico('FabricHood',(0,.025,.065),(.25,.23,.29),'teal' if scout else 'cloth',h,sub=2)
 face=loft('CarvedMask',[(-.17,.11,.065,-.175),(-.08,.18,.09,-.17),(.06,.20,.10,-.16),(.22,.15,.075,-.145),(.26,.07,.04,-.12)],face_material(key),h,12)
 for v in face.data.vertices:
  if v.co.y<-.14:
   v.co.y-=.038*math.exp(-(v.co.x/.055)**2-((v.co.z+.005)/.14)**2)
 face.data.update()
 face_uv(face,.225,-.20,.28)
 face.data.materials.append(M['wood_dark'])
 for p in face.data.polygons:
  if p.center.y>-.14:p.material_index=1
 if scout:
  panel('FoldedHeadcloth',[(-.22,.04,.20),(.22,.04,.20),(.17,.18,-.18),(-.10,.2,-.28),(-.20,.14,-.10)],'teal',h)
 else:
  for s in [-1,1]:block('MaskTemple',(s*.18,-.145,.07),(.075,.06,.23),'wood_dark',h,.02)
 # Scarf is fitted around the neck, never a featureless cylinder.
 loft('Scarf',[(-.08,.19,.17,0),(.01,.215,.175,0),(.08,.16,.15,0)],'ochre' if scout else 'red',h,10)
 fighter_arms(r,1.04,'ink','teal' if scout else 'cloth',braces=True)
 fighter_legs(r,.55,'charcoal','wood_dark')
 save(key,True)

# The killer's identity stays hidden. The face is a carved volume inside a hood.
clear();r=empty('AssassinoSemNome');t=open_coat(r,'AssassinCoat',1.015,'ink')
for s in [-1,1]:
 panel('SplitCoattail',[(s*.02,-.15,-.2),(s*.22,-.10,-.18),(s*.24,.0,-.58),(s*.13,-.15,-.63),(s*.05,-.17,-.46)],'charcoal',t)
 panel('CrimsonLining',[(s*.10,-.169,-.22),(s*.16,-.144,-.22),(s*.14,-.18,-.54),(s*.09,-.19,-.49)],'red',t)
 panel('FoldedCollar',[(s*.03,-.19,.15),(s*.20,-.11,.30),(s*.28,-.04,.22),(s*.17,-.21,.06)],'fold',t)
 block('ShoulderFold',(s*.285,.005,.20),(.24,.31,.15),'charcoal',t,.045)
loft('Sash',[(-.18,.245,.18,0),(-.10,.25,.18,0)],'red',t)
panel('SashTail',[(.06,-.196,-.13),(.13,-.19,-.15),(.16,-.21,-.45),(.08,-.22,-.40)],'red',t)
h=empty('Head',(0,-.025,1.43),r)
hood=ico('DeepHood',(0,.045,.09),(.26,.245,.315),'ink',h,sub=2)
mask=loft('PorcelainMask',[(-.19,.08,.045,-.195),(-.10,.16,.09,-.185),(.05,.18,.11,-.18),(.23,.145,.09,-.15),(.29,.045,.045,-.11)],face_material('assassin'),h,14);face_uv(mask,.21,-.22,.30)
mask.data.materials.append(M['ink'])
for p in mask.data.polygons:
 if p.center.y>-.16:p.material_index=1
mask.location.y=-.025
# Layered hood rim gives real occlusion around the mask.
for s in [-1,1]:
 tube('HoodRim',[(s*.035,-.19,.285),(s*.16,-.22,.215),(s*.215,-.16,.025),(s*.17,-.13,-.215)],[.025,.036,.035,.02],'charcoal',h,7)
fighter_arms(r,1.18,'ink','charcoal',braces=False)
for s,label in [(-1,'L'),(1,'R')]:
 arm=bpy.data.objects['Arm'+label]
 for z in [-.25,-.30]:
  points=[(s*.105+math.cos(i*math.tau/12)*.105,-.05+math.sin(i*math.tau/12)*.108,z) for i in range(13)]
  tube('CrimsonBinding',points,[.013]*13,'red',arm,5)
fighter_legs(r,.66,'ink','ink')
save('assassin',True)
