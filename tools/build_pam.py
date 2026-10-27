"""Pam v3: continuous sculpted face with painted eyes and expressive articulated silhouette."""
import bmesh
from mathutils import Vector

def pam_mat(name,h):
 c=tuple(int(h[i:i+2],16)/255 for i in (0,2,4));c=tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in c)
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True
 bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*c,1);bs.inputs['Roughness'].default_value=.9;bs.inputs['Specular IOR Level'].default_value=.16
 M[name]=m;return m
for n,h in {'p_fur':'EAD7C0','p_cream':'F0DFC8','p_warm':'D6BCAE','p_lilac':'AFA1B6','p_ruff':'D2BEC8','p_black':'18161F','p_blacklit':'28232E','p_jacket':'17151C','p_fold':'242029','p_edge':'312834','p_red':'A62626','p_redlight':'B72D28','p_reddark':'761B25','p_sole':'64566D'}.items():pam_mat(n,h)

def loft(name,rows,material,parent,sides=12):
 v=[]
 for z,rx,ry,cy in rows:
  for i in range(sides):
   a=math.tau*i/sides-math.pi/2;v.append((rx*math.cos(a),cy+ry*math.sin(a),z))
 f=[tuple(reversed(range(sides)))]
 for j in range(len(rows)-1):
  for i in range(sides):
   a=j*sides+i;b=j*sides+(i+1)%sides
   f += [(a,b,b+sides),(a,b+sides,a+sides)] if (i+j)%2 else [(a,b,a+sides),(b,b+sides,a+sides)]
 f.append(tuple(range((len(rows)-1)*sides,len(rows)*sides)))
 return mesh(name,v,f,material,parent)

def flat(name,coords,material,parent):return mesh(name,coords,[tuple(range(len(coords)))],material,parent)

def limb(name,points,radii,material,parent,sides=10):
 v=[]
 for j,p in enumerate(points):
  tangent=Vector(points[min(j+1,len(points)-1)])-Vector(points[max(0,j-1)])
  tangent.normalize();u=tangent.cross(Vector((0,1,0))).normalized();w=tangent.cross(u).normalized()
  for i in range(sides):
   a=math.tau*i/sides;v.append(tuple(Vector(p)+u*math.cos(a)*radii[j][0]+w*math.sin(a)*radii[j][1]))
 f=[tuple(reversed(range(sides)))]
 for j in range(len(points)-1):
  for i in range(sides):
   a=j*sides+i;b=j*sides+(i+1)%sides;f.append((a,b,b+sides,a+sides))
 f.append(tuple(range((len(points)-1)*sides,len(points)*sides)))
 return mesh(name,v,f,material,parent)

root=empty('Pam');body=empty('Torso',(0,0,.77),root)
# Compact child torso; continuous cream fur rather than a rectangular shirt panel.
torso=loft('BodyFur',[(-.23,.15,.105,0),(-.17,.185,.135,0),(.02,.195,.135,0),(.20,.17,.12,0),(.25,.11,.095,0)],'p_black',body,12)
torso.data.materials.append(M['p_cream']);torso.data.materials.append(M['p_warm'])
for f in torso.data.polygons:
 c=f.center
 if c.y<-.035 and abs(c.x)<.155:f.material_index=1 if c.x<.02 else 2
ico('Tail',(0,.175,-.19),(.09,.085,.085),'p_fur',2,body)
# The jacket is an open, continuous curved shell; opening follows the chest.
verts=[];rows=[(-.17,.24,.15,.05,.51),(-.04,.25,.17,.035,.49),(.105,.245,.17,.035,.47),(.23,.205,.145,.025,.64)]
N=15
for z,rx,ry,cy,gap in rows:
 for i in range(N):
  a=-math.pi+gap+(math.tau-2*gap)*i/(N-1)
  zz=z+(math.cos(a)*.008 if z<0 else 0)
  verts.append((math.sin(a)*rx,math.cos(a)*ry+cy,zz))
faces=[]
for j in range(len(rows)-1):
 for i in range(N-1):
  a=j*N+i;faces.append((a,a+1,a+1+N,a+N))
jacket=mesh('Jacket',verts,faces,'p_jacket',body);jacket.data.materials.append(M['p_fold']);jacket.data.materials.append(M['p_edge'])
for f in jacket.data.polygons:
 f.material_index=1 if f.index%7==2 else 0
solid=jacket.modifiers.new('Leather edge thickness','SOLIDIFY');solid.thickness=.012;solid.offset=0
bpy.context.view_layer.objects.active=jacket;bpy.ops.object.modifier_apply(modifier=solid.name)
# Folded collar follows the shoulders, with restrained red inner lining.
for s in [-1,1]:
 vs=[(s*.092,-.115,.235),(s*.16,-.09,.30),(s*.26,-.045,.245),(s*.18,-.17,.15),(s*.14,-.19,.195)]
 flat('CollarLining',vs,'p_red',body)
 flat('CollarFold',[(s*.155,-.103,.29),(s*.263,-.056,.24),(s*.218,-.175,.125),(s*.176,-.186,.18)],'p_blacklit',body)
 flat('Lapel',[(s*.135,-.153,.23),(s*.193,-.172,.17),(s*.17,-.176,.04),(s*.108,-.151,.115)],'p_jacket',body)
 # Fine seam tucked into the curved surface, no rectangular metal pocket plates.
 flat('PocketSeam',[(s*.165,-.114,-.045),(s*.211,-.075,-.023),(s*.213,-.077,-.029),(s*.166,-.116,-.051)],'p_edge',body)
# One continuous head: cheeks, brow and short muzzle are sculpted in the hull.
head=empty('Head',(0,-.015,1.195),root)
hull=loft('HeadShape',[(-.275,.15,.12,.015),(-.235,.275,.19,.01),(-.145,.38,.24,.015),(-.025,.421,.265,.025),(.10,.399,.272,.035),(.225,.34,.235,.045),(.31,.23,.18,.055),(.35,.10,.09,.055),(.36,.025,.035,.055)],'p_fur',head,16)
for v in hull.data.vertices:
 x,y,z=v.co
 front=max(0,min(1,(-y+.02)/.22))
 # A broad but very short anatomical muzzle, flowing into the jaw.
 muzzle=.052*math.exp(-((x/.28)**4)-((z+.115)/.14)**4)
 brow=.022*math.exp(-((abs(x)-.19)/.12)**2-((z-.13)/.07)**2)
 v.co.y-=(muzzle+brow)*front
hull.data.update()
face=bpy.data.materials.new('Pam painted fur');face.use_nodes=True
bs=face.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.92;bs.inputs['Specular IOR Level'].default_value=.14
tex=face.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(ROOT+'/assets/textures/pam_face.png',check_existing=True);tex.interpolation='Linear';tex.image.pack()
face.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);hull.data.materials.clear();hull.data.materials.append(face)
uv=hull.data.uv_layers.new(name='FaceAtlas')
for poly in hull.data.polygons:
 front=poly.center.y<.025
 for li in poly.loop_indices:
  p=hull.data.vertices[hull.data.loops[li].vertex_index].co
  u=(p.x+.48)/.96*.5+(0 if front else .5)
  vv=(p.z+.30)/.70
  uv.data[li].uv=(u,vv)
# Surface-fitted tiny faceted panda nose, no floating rectangular muzzle or mouth.
from mathutils.bvhtree import BVHTree
bvh=BVHTree.FromPolygons([v.co.copy() for v in hull.data.vertices],[list(f.vertices) for f in hull.data.polygons])
def front_y(x,z):
 hit,_,_,_=bvh.ray_cast(Vector((x,-2,z)),Vector((0,1,0)));return hit.y if hit is not None else -.27
nv=[]
for x,z in [(-.060,-.033),(-.035,-.026),(.035,-.026),(.061,-.036),(.037,-.077),(0,-.098),(-.04,-.074)]:
 nv.append((x,front_y(x,z)-.008,z))
nv.append((0,front_y(0,-.052)-.028,-.052))
nose=mesh('Nose',nv,[(i,(i+1)%7,7) for i in range(7)],'p_black',head)
nose.data.materials.append(M['p_blacklit']);nose.data.polygons[0].material_index=1
# Chunky rounded ears, with actual thickness and curved volume instead of flat coins.
for s in [-1,1]:
 ear=ico('Ear',(s*.334,.06,.292),(.155,.10,.165),'p_black',2,head)
 ear.rotation_euler[1]=s*.24
 ear.data.materials.append(M['p_blacklit'])
 for p in ear.data.polygons:
  if p.center.y<-.40 and p.center.z>-.05:p.material_index=1
 # Low, swept scalp clumps do not intersect the ears as pink horns.
 for i,(xx,zz,yy,w) in enumerate([(-.105,.305,.095,.11),(.005,.326,.12,.12),(.105,.295,.16,.11)]):
  if s<0:continue
  vs=[(xx-w*.65,yy-.09,zz-.025),(xx+w*.65,yy-.07,zz-.02),(xx+.045,yy+.06,zz+.082),(xx+.015,yy+.13,zz-.025)]
  tuft=mesh('SweptTuft',vs,[(0,1,2),(1,3,2),(0,2,3),(0,3,1)],'p_fur',head);tuft.data.materials.append(M['p_warm']);tuft.data.polygons[1].material_index=1
 # Broad asymmetric fur clumps grow out of the rear cheek, not a row of blades.
 for k,(z,tipx,tipz,back_y) in enumerate([(.015,.478,-.025,.085),(-.095,.455,-.155,.105),(-.17,.365,-.232,.115)]):
  x=.36 if k<2 else .29
  vs=[(s*x,-.075,z+.07),(s*(x-.035),-.11,z-.035),(s*tipx,back_y-.035,tipz),(s*(x+.005),.17,z-.035),(s*(x+.015),.145,z+.045)]
  ob=mesh('CheekRuff',vs,[(0,1,2),(0,2,4),(1,3,2),(2,3,4),(0,4,3,1)],'p_ruff' if k<2 else 'p_lilac',head)
  ob.data.materials.append(M['p_fur']);ob.data.polygons[0].material_index=1
# Articulated arms have a real elbow bend and an open readable silhouette.
for s,label in [(-1,'L'),(1,'R')]:
 p=empty('Arm'+label,(s*.246,.02,.959),root)
 points=[(0,0,0),(s*.065,.005,-.12),(s*.12,-.005,-.235),(s*.15,-.065,-.305)]
 sleeve=limb('Sleeve',points,[(.12,.135),(.124,.13),(.10,.11),(.093,.108)],'p_jacket',p)
 sleeve.data.materials.append(M['p_fold'])
 for f in sleeve.data.polygons:
  if f.index%8 in [1,2]:f.material_index=1
 # A narrow dark cuff; the thumb wraps into the palm.
 cuff=limb('Cuff',[(s*.145,-.06,-.287),(s*.155,-.075,-.32)],[(.096,.109),(.094,.107)],'p_blacklit',p)
 hand=ico('Fist',(s*.16,-.082,-.375),(.112,.10,.115),'p_black',2,p)
 ico('FoldedThumb',(s*.10,-.145,-.36),(.049,.041,.07),'p_blacklit',1,p)
 # Closed knuckles remain part of the fist silhouette rather than extruded buttons.
 for j in range(3):
  flat('KnuckleCrease',[(s*(.115+j*.033),-.166,-.355),(s*(.137+j*.033),-.165,-.355),(s*(.137+j*.033),-.166,-.36),(s*(.115+j*.033),-.168,-.36)],'p_blacklit',p)
 # Looser shorts with a clear crotch and angular red fabric folds.
 leg=empty('Leg'+label,(s*.145,0,.575),root)
 shorts=loft('Shorts',[(.02,.14,.15,0),(-.10,.15,.153,.005),(-.21,.14,.14,-.002)],'p_red',leg,10)
 shorts.data.materials.append(M['p_redlight']);shorts.data.materials.append(M['p_reddark'])
 for f in shorts.data.polygons:
  f.material_index=2 if f.center.y>.04 else (1 if f.index%9 in [2,3] else 0)
 shin=limb('Shin',[(0,.015,-.20),(s*.012,.015,-.34),(s*.025,-.005,-.43)],[(.08,.085),(.079,.083),(.095,.09)],'p_black',leg,9)
 # Panda paws: cream toe planes flow into dark ankles, without sneaker bumpers.
 foot=loft('Paw',[(-.55,.142,.18,-.066),(-.515,.151,.18,-.07),(-.44,.135,.155,-.06),(-.385,.087,.10,-.005)],'p_black',leg,12)
 for n in ['p_cream','p_fur','p_warm','p_sole']:foot.data.materials.append(M[n])
 for f in foot.data.polygons:
  c=f.center
  if c.z<-.525:f.material_index=4
  elif c.y<-.12:f.material_index=1 if c.x<.03 else 2
  elif c.y<-.07 and c.z<-.445:f.material_index=3
  else:f.material_index=0
# The waistband tucks under the curved jacket rather than protruding as a belt plate.
loft('Waistband',[(.55,.23,.14,0),(.59,.228,.138,0)],'p_reddark',root,12)
# Consistent flat normals maintain a deliberate low-poly sculpture across all views.
for ob in bpy.context.scene.objects:
 if ob.type=='MESH':
  bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
  for f in ob.data.polygons:f.use_smooth=False
