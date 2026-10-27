"""Authored forest, props and ruin modules; all original painted low-poly meshes."""
def leaf(name,origin,direction,length,width,mat='blade',parent=None,segments=5,lift=.22):
 d=Vector(direction).normalized();side=Vector((-d.y,d.x,0)).normalized();v=[]
 for j in range(segments+1):
  t=j/segments;center=Vector(origin)+d*(t*length)+Vector((0,0,math.sin(t*math.pi)*lift-t*t*.06))
  w=math.sin(math.pi*t)**.70*width
  v.extend([tuple(center-side*w),tuple(center+Vector((0,0,w*.17))),tuple(center+side*w)])
 fs=[]
 for j in range(segments):
  k=j*3;fs.extend([(k,k+3,k+4,k+1),(k+1,k+4,k+5,k+2)])
 ob=mesh(name,v,fs,mat,parent)
 uv=ob.data.uv_layers[0]
 for p in ob.data.polygons:
  for li in p.loop_indices:
   i=ob.data.loops[li].vertex_index;uv.data[li].uv=((i%3)/2,(i//3)/segments)
 return ob

def crown(pos,radius,height,mat,parent):
 # Irregular scalloped leaf masses, with a convex crown and lumpy outer contour.
 n=13;vs=[]
 for z,r in [(-.22,.65),(0,1),(.42,.72),(.67,.18)]:
  for i in range(n):
   a=i*math.tau/n;rr=radius*r*(1+.10*math.sin(i*2.7+pos[0]));vs.append((pos[0]+math.cos(a)*rr,pos[1]+math.sin(a)*rr,pos[2]+z*height))
 fs=[]
 for j in range(3):
  for i in range(n):
   a=j*n+i;b=j*n+(i+1)%n;fs.append((a,b,b+n,a+n))
 fs += [tuple(reversed(range(n))),tuple(range(n*3,n*4))]
 ob=mesh('FoliageCrown',vs,fs,mat,parent);uv_project(ob,'box',.6)

for variant in range(3):
 clear();r=empty('RainforestTree');height=[6.5,7.6,5.3][variant]
 if variant<2:
  trunk=[(0,0,0),(.05,.04,1.4),(-.17,.09,height*.52),(.15,.09,height*.82),(.31,.02,height)]
  tube('SculptedTrunk',trunk,[.48,.32,.24,.15,.055],'bark',r,10)
  for i in range(6):
   a=i*math.tau/6+.2
   tube('ButtressRoot',[(0,0,1.3),(math.cos(a)*.48,math.sin(a)*.48,.38),(math.cos(a)*1.2,math.sin(a)*1.2,.035)],[.20,.22,.025],'bark',r,6)
  for i in range(6):
   a=i*2.4;end=(math.cos(a)*1.65,math.sin(a)*1.65,height-.6+random.random()*.7)
   tube('Branch',[(.02,.08,height*.63),(math.cos(a)*.8,math.sin(a)*.8,height-.9),end],[.13,.075,.02],'bark',r,7)
   crown(end,1.1+random.random()*.38,1.3,'leaf' if i%3 else 'leaf_dark',r)
   for j in range(4):
    aa=a+j*1.5;org=(end[0]+math.cos(aa)*.6,end[1]+math.sin(aa)*.6,end[2]+.1)
    leaf('OuterCanopyLeaf',org,(math.cos(aa),math.sin(aa),0),.9,.16,'leaf_light' if j%3==0 else 'blade',r,3,.15)
  crown((.1,.1,height+.12),1.35,1.3,'leaf',r)
  for i in range(4):
   a=i*1.8
   pts=[(math.cos(a)*1.15,math.sin(a)*1.15,height-.3),(math.cos(a)*1.25,math.sin(a)*1.25,height-2.0),(math.cos(a)*1.12,math.sin(a)*1.12,height-3.1)]
   tube('HangingLiana',pts,[.027,.021,.012],'leaf_dark',r,5)
   if i%2==0:
    for j in range(4):leaf('VineLeaf',(pts[1][0],pts[1][1],height-1.2-j*.3),(math.cos(a+j),math.sin(a+j),0),.26,.10,'blade',r,2,.05)
 else:
  tube('LeaningPalm',[(0,0,0),(.1,0,1.4),(.35,.04,3.6),(.44,.1,height)],[.29,.22,.17,.10],'bark',r,10)
  for z in [.6,1.3,2,2.7,3.4,4.1]:
   tube('OldLeafScar',[(.02+z*.075-.14,0,z),(.02+z*.075,-.16,z+.01),(.02+z*.075+.14,0,z)],[.018]*3,'wood_dark',r,5)
  for i in range(11):
   a=i*2.4;leaf('BroadPalmFrond',(.43,.1,height-.2),(math.cos(a),math.sin(a),-.05),2.2,.38,'blade' if i%3 else 'leaf_light',r,7,.45)
 save('tree'+str(variant))

clear();r=empty('Fern')
for i in range(7):
 a=i*2.4;d=Vector((math.cos(a),math.sin(a),0));side=Vector((-d.y,d.x,0));L=.75+random.random()*.3
 points=[]
 for j in range(6):
  t=j/5;points.append(tuple(d*L*t+Vector((0,0,.08+math.sin(t*math.pi)*.46))))
 tube('FrondStem',points,[.012]*6,'leaf_light',r,4)
 for j in range(1,6):
  t=j/6;center=d*L*t+Vector((0,0,.08+math.sin(t*math.pi)*.46))
  for s in [-1,1]:
   direction=(side*s+d*.35).normalized();leaf('FernLeaflet',center,direction,.23*(1-t*.65),.055*(1-t*.6),'blade' if i%2 else 'leaf_light',r,2,.025)
save('fern')

clear();r=empty('GingerLeaves')
for i in range(9):
 a=i*2.4;length=.70+random.random()*.6
 leaf('TropicalBlade',(0,0,.035),(math.cos(a),math.sin(a),.16),length,.18,'blade' if i%3 else 'leaf_light',r,6,.45)
 tube('Stem',[(0,0,0),(math.cos(a)*.15,math.sin(a)*.15,.2)],[.018,.011],'leaf_dark',r,5)
save('broadleaf')

clear();r=empty('Bromeliad')
for i in range(11):
 a=i*2.4;leaf('RosetteLeaf',(0,0,.04),(math.cos(a),math.sin(a),0),.6,.09,'blade',r,5,.28)
for i in range(5):
 a=i*math.tau/5;leaf('FlowerBract',(0,0,.24),(math.cos(a),math.sin(a),.4),.20,.045,'redlight',r,3,.12)
tube('FlowerStem',[(0,0,0),(0,0,.43)],[.025,.018],'orange',r,6)
save('bromeliad')

clear();r=empty('MossyStone')
rock=ico('WeatheredRock',(0,0,.32),(.78,.62,.60),'stone',r,sub=2)
for v in rock.data.vertices:
 v.co*=random.uniform(.91,1.10)
 if v.co.z<-.45:v.co.z=-.50
rock.data.update();rock.data.materials.append(M['moss'])
for p in rock.data.polygons:
 if p.normal.z>.45 and random.random()<.8:p.material_index=1
for i in range(3):ico('FootStone',(.55-i*.38,.35,.10),(.26,.20,.18),'stone',r,sub=1)
save('rock')

clear();r=empty('FallenRoot')
tube('ExposedRoot',[(-.9,0,0),(-.3,.05,.2),(.2,-.04,.27),(.8,.07,.10),(1.2,.3,0)],[.11,.16,.18,.12,.02],'bark',r,8)
for i in range(3):
 x=-.5+i*.5;tube('RootFinger',[(x,0,.16),(x+.2,.4,.09),(x+.5,.6,0)],[.07,.05,.015],'bark',r,6)
save('root')

# Detailed props: real frame construction, inset planks, painted stamps and bindings.
for key in ['crate','tnt']:
 clear();r=empty('BreakableCrate')
 for x in [-.25,0,.25]:
  for y in [-.34,.34]:block('Plank',(x,y,.38),(.24,.055,.69),'wood' if key=='crate' else 'redwood',r,.012)
 for y in [-.25,0,.25]:
  for x in [-.34,.34]:block('SidePlank',(x,y,.38),(.055,.24,.69),'wood',r,.012)
 for y in [-.37,.37]:
  for x in [-.31,.31]:block('CornerPost',(x,y,.38),(.085,.075,.76),'wood_dark',r,.012)
  for z in [.055,.705]:block('Frame',(0,y,z),(.71,.075,.08),'wood',r,.012)
 # Painted face inset into the timber instead of a floating label.
 stamp=block('PaintedFront',(0,-.376,.39),(.52,.006,.52),'crate_stamp' if key=='crate' else 'tnt_stamp',r,.0)
 uv_project(stamp,'face',1/.52)
 for i in range(4):block('LidSlat',(-.27+i*.18,0,.744),(.173,.67,.045),'wood',r,.008)
 for s in [-1,1]:
  ob=block('DiagonalBrace',(s*.01,.375,.38),(.065,.055,.88),'wood_dark',r,.008);ob.rotation_euler[1]=s*.76
 for x in [-.30,.30]:
  for z in [.08,.68]:ico('WoodPeg',(x,-.414,z),(.018,.012,.018),'bronze',r,sub=1)
 if key=='tnt':
  tube('BraidedFuse',[(.03,0,.77),(.03,-.01,.91),(.13,-.02,1.0),(.19,-.04,.98)],[.018]*4,'cream',r,6)
  ico('FuseTip',(.19,-.04,.98),(.025,.018,.025),'ink',r,sub=1)
 save(key)

clear();r=empty('AltarDasRaizes')
for z,rx,ry in [(.07,.53,.48),(.20,.43,.40),(.32,.34,.32)]:
 loft('CarvedBase',[(z-.06,rx,ry,0),(z+.06,rx*.98,ry*.98,0)],'stone',r,8)
loft('Pillar',[(.33,.22,.22,0),(.72,.235,.205,0),(1.16,.20,.195,0),(1.23,.29,.24,0)],'stone',r,8)
for s in [-1,1]:
 tube('RaisedCarving',[(s*.13,-.205,.48),(s*.13,-.215,.8),(s*.06,-.218,.87),(s*.06,-.218,1.08)],[.02]*4,'bronze',r,5)
 panel('EngravedEye',[(s*.06,-.24,.93),(s*.155,-.22,.98),(s*.14,-.22,.91)],'ink',r)
 tube('RootWrapping',[(s*.45,.15,.04),(s*.31,-.23,.24),(s*.22,-.23,.46)],[.055,.04,.015],'bark',r,6)
loft('CrystalMount',[(1.23,.16,.15,0),(1.32,.19,.18,0),(1.36,.12,.11,0)],'bronze',r,8)
loft('JadeFlame',[(1.32,.04,.035,0),(1.48,.15,.13,0),(1.65,.08,.075,0),(1.83,.008,.01,.02)],'crystal',r,7)
for i in range(3):leaf('AltarMoss',(.18,.12,.31),(math.cos(i*2),math.sin(i*2),0),.28,.09,'blade',r,3,.05)
save('shrine')

clear();r=empty('MentorAmulet')
loft('BronzeRim',[(-.18,.02,.025,0),(-.12,.15,.05,0),(.10,.16,.05,0),(.18,.035,.03,0)],'bronze',r,10)
ico('CarvedJade',(0,-.045,0),(.12,.035,.15),'jade',r,sub=2)
spiral=[(.072*math.cos(t)*(1-t/9),-.084,.085*math.sin(t)*(1-t/9)) for t in [i*.20 for i in range(34)]]
tube('ShellSpiral',spiral,[.008]*len(spiral),'gold',r,5)
save('amulet')

clear();r=empty('GoldenSeed')
seed=loft('Seed',[(-.17,.018,.018,0),(-.10,.09,.08,0),(.05,.105,.09,0),(.16,.035,.03,0),(.19,.012,.012,0)],'orange',r,9)
for s in [-1,1]:tube('SeedRidge',[(s*.01,-.02,-.15),(s*.05,-.083,0),(s*.01,-.03,.16)],[.009]*3,'gold',r,5)
leaf('SeedLeaf',(0,0,.15),(.9,.2,.2),.18,.05,'blade',r,3,.04)
save('seed')

# Modular carved ruins use distinctive silhouette and a consistent fictional glyph.
clear();r=empty('RuinedPillar')
for z,rx,ry in [(.11,.59,.55),(.30,.47,.45),(2.85,.53,.50),(3.06,.63,.56)]:
 loft('StoneCourse',[(z-.10,rx,ry,0),(z+.10,rx*.97,ry*.97,0)],'stone',r,8)
loft('Shaft',[(.35,.39,.38,0),(1.55,.36,.355,0),(2.80,.39,.37,0)],'stone',r,8)
for z in [.72,1.18,1.65,2.11,2.5]:
 panel('Recess', [(-.19,-.382,z-.085),(.18,-.382,z-.085),(.18,-.382,z+.085),(-.19,-.382,z+.085)],'wood_dark',r)
 tube('Glyph',[(-.12,-.39,z),(-.02,-.39,z+.045),(.10,-.39,z),(.0,-.39,z-.045)],[.014]*4,'gold',r,5)
for i in range(3):leaf('StoneVine',(.33,.15,2.3+i*.2),(.4,-.5,-.5),.30,.07,'blade',r,3,.04)
# Exposed root curls around the pedestal, integrated with the forest.
tube('PillarRoot',[(-.54,.23,.05),(-.40,-.29,.24),(-.32,-.35,.65)],[.065,.05,.015],'bark',r,7)
save('ruin_pillar')

clear();r=empty('CarvedLintel')
block('LintelCore',(0,0,0),(6.5,.90,.46),'stone',r,.10)
for x in range(-3,4):
 block('UpperStone',(x,0,.26),(.95,.96,.15),'moss' if x%2 else 'stone',r,.035)
for x in [-2.4,-1.6,-.8,0,.8,1.6,2.4]:
 panel('Recess',[(x-.20,-.456,-.12),(x+.20,-.456,-.12),(x+.20,-.456,.12),(x-.20,-.456,.12)],'wood_dark',r)
 tube('LintelGlyph',[(x-.12,-.465,0),(x,-.47,.075),(x+.12,-.465,0),(x,-.47,-.075)],[.018]*4,'gold',r,5)
save('ruin_lintel')

clear();r=empty('TimberGate')
for x in [-2.6,-1.75,-.9,0,.9,1.75,2.6]:
 plank=block('UnevenSlat',(x,0,1.3),(.24,.22,2.6),'wood_dark',r,.025)
 if x in [-2.6,2.6]:
  for z in [.35,2.2]:tube('RopeWrap',[(x-.14,-.15,z),(x+.14,-.15,z),(x+.14,.14,z),(x-.14,.14,z),(x-.14,-.15,z)],[.023]*5,'cream',r,5)
for z in [.35,2.2]:block('CrossBeam',(0,-.08,z),(5.8,.28,.18),'wood',r,.025)
for s in [-1,1]:
 p=block('DiagonalSupport',(s*1.1,.08,1.25),(.13,.13,2.5),'wood',r,.014);p.rotation_euler[1]=s*.8
save('gate')

clear();r=empty('RiverRaft')
for x in [-.95,-.48,0,.48,.95]:
 block('WornDeckPlank',(x,0,.035),(.44,2.1,.18),'wood',r,.028)
for y in [-.68,.68]:
 tube('FloatingLog',[(-1.15,y,-.13),(1.15,y,-.13)],[.15,.15],'bark',r,10)
 for x in [-.85,.85]:
  tube('Lashing',[(x,y-.18,-.10),(x,y-.18,.13),(x,y+.18,.13),(x,y+.18,-.1)],[.018]*4,'cream',r,5)
save('raft')

clear();r=empty('WornBridgeBoard')
block('BridgeBoard',(0,0,0),(2.3,.42,.18),'wood',r,.025)
for s in [-1,1]:
 for y in [-.13,.13]:ico('Peg',(s*.92,y,.095),(.02,.02,.008),'wood_dark',r,sub=1)
save('bridge_board')

clear();r=empty('RopeBridgeRails')
for s in [-1,1]:
 for y in [-1.38,1.38]:tube('CornerPost',[(s*1.17,y,-.18),(s*1.17,y,.9)],[.055,.045],'bark',r,8)
 points=[(s*1.17,-1.4+i*2.8/12,.78-.20*math.sin(i/12*math.pi)) for i in range(13)]
 tube('SaggingRope',points,[.026]*len(points),'cream',r,6)
save('bridge_rails')
clear();r=empty('FallenLeaves')
for i in range(5):
 a=i*2.4;leaf('DryLeaf',(math.cos(a)*.18,math.sin(a)*.15,.009),(math.cos(a),math.sin(a),0),.24,.075,'wood' if i%2 else 'leaf_dark',r,3,.01)
save('leaf_litter')
clear();r=empty('DenseUnderstory')
for i in range(6):
 a=i*2.4;cx=math.cos(a)*.33;cy=math.sin(a)*.33;height=.9+(i%3)*.35
 tube('GreenStem',[(cx,cy,0),(cx+.1,cy,height)],[.025,.012],'leaf_dark',r,5)
 for j in range(4):
  b=a+j*2.3;z=.25+j*height/4
  leaf('BroadUnderstoryLeaf',(cx,cy,z),(math.cos(b),math.sin(b),.15),.85,.24,'blade' if j%2 else 'leaf_dark',r,5,.22)
save('thicket')
