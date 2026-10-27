"""An original PS1-oriented Pam study. Hand-landmarked facial topology, no commercial meshes."""
import bpy,bmesh,math,os,json
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
# One atlas, one unlit vertex-colored material: the preview uses the exported mesh itself.
mat=bpy.data.materials.new('Pam_PS1_128');mat.use_nodes=True;nodes=mat.node_tree.nodes;nodes.clear()
out=nodes.new('ShaderNodeOutputMaterial');em=nodes.new('ShaderNodeEmission');em.inputs['Strength'].default_value=1
tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(ROOT/'assets/textures/pam_ps1_atlas.png'));tex.image.pack();tex.interpolation='Closest'
col=nodes.new('ShaderNodeVertexColor');col.layer_name='PS1Light';mul=nodes.new('ShaderNodeMixRGB');mul.blend_type='MULTIPLY';mul.inputs[0].default_value=1
mat.node_tree.links.new(tex.outputs['Color'],mul.inputs[1]);mat.node_tree.links.new(col.outputs['Color'],mul.inputs[2]);mat.node_tree.links.new(mul.outputs[0],em.inputs[0]);mat.node_tree.links.new(em.outputs[0],out.inputs[0])
COLORS={'black':0,'dark':1,'fold':2,'lining':3,'red':4,'cream':5,'warm':6,'pink':7,'lilac':8,'light':9,'pupil':10,'sole':11,'seam':12,'redlight':13,'shadow':14,'toe':15}
PARTS=[]
def empty(name,pos=(0,0,0),parent=None):
 ob=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(ob);ob.location=pos;ob.parent=parent;return ob

def make(name,v,f,parent,region='black',regions=None):
 me=bpy.data.meshes.new(name);me.from_pydata(v,[],f);me.update();ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);ob.parent=parent;me.materials.append(mat)
 uv=me.uv_layers.new(name='Atlas128')
 mins=[min(p[k] for p in v) for k in range(3)];maxs=[max(p[k] for p in v) for k in range(3)]
 for i,poly in enumerate(me.polygons):
  r=regions[i] if regions else region
  for li in poly.loop_indices:
   p=me.vertices[me.loops[li].vertex_index].co
   if r=='face':u=(p.x+.42)/.84*.5;vv=1-(.37-p.z)/.65*.5
   elif r=='back':u=.5+(p.x+.42)/.84*.25;vv=.75-(.37-p.z)/.65*.25
   elif r in ['jacket','shorts','paw']:
    x=(p.x-mins[0])/max(.001,maxs[0]-mins[0]);z=(p.z-mins[2])/max(.001,maxs[2]-mins[2])
    tile={'jacket':(64,0),'shorts':(96,0),'paw':(96,32)}[r];u=(tile[0]+1+x*30)/128;vv=1-(tile[1]+31-z*30)/128
   else:u=(COLORS[r]*8+4)/128;vv=1-88/128
   uv.data[li].uv=(u,vv)
 PARTS.append(ob);return ob

def tube(name,rows,parent,region='black',sides=6):
 vs=[]
 for x,y,z,rx,ry in rows:
  for i in range(sides):
   a=math.tau*i/sides-math.pi/2;vs.append((x+math.cos(a)*rx,y+math.sin(a)*ry,z))
 fs=[tuple(reversed(range(sides)))]
 for j in range(len(rows)-1):
  for i in range(sides):
   a=j*sides+i;b=j*sides+(i+1)%sides;fs.append((a,b,b+sides,a+sides))
 fs.append(tuple(range((len(rows)-1)*sides,len(rows)*sides)))
 return make(name,vs,fs,parent,region)

def wedge(name,pts,parent,region):return make(name,pts,[(0,1,2),(0,2,3),(0,3,1),(1,3,2)],parent,region)
root=empty('Pam_PS1_Estudo');torso=empty('Torso',(0,0,.735),root)
body=tube('CompactTorso',[(0,0,-.235,.15,.10),(0,-.005,-.07,.18,.12),(0,.005,.19,.17,.115),(0,.005,.24,.105,.085)],torso,'black',6)
# Cream chest is anatomical fur, visible in the short open jacket.
for i,p in enumerate(body.data.polygons):
 if p.center.y<-.045:
  for li in p.loop_indices:body.data.uv_layers[0].data[li].uv=((COLORS['cream']*8+4)/128,1-88/128)
# Deliberately angular jacket shell with an actual front opening.
v=[];N=9
for z,rx,ry,gap in [(-.205,.225,.14,.47),(.09,.25,.155,.49),(.24,.19,.13,.58)]:
 for i in range(N):
  a=-math.pi+gap+(math.tau-2*gap)*i/(N-1);v.append((math.sin(a)*rx,math.cos(a)*ry+.02,z))
f=[]
for j in range(2):
 for i in range(N-1):a=j*N+i;f.append((a,a+1,a+1+N,a+N))
make('OpenJacket',v,f,torso,'jacket')
for s in [-1,1]:
 make('TurnedCollar',[(s*.09,-.10,.23),(s*.14,-.09,.31),(s*.27,-.035,.25),(s*.18,-.17,.135)],[(0,1,2),(0,2,3)],torso,'black')
 make('RedLining',[(s*.10,-.11,.235),(s*.16,-.125,.255),(s*.16,-.18,.11)],[(0,1,2)],torso,'lining')
 make('Lapel',[(s*.145,-.14,.235),(s*.218,-.14,.18),(s*.17,-.166,.035),(s*.12,-.148,.10)],[(0,1,2),(0,2,3)],torso,'dark')
# Facial landmarks and eye contours constrain the mesh instead of using uniform latitude rings.
head=empty('Head',(0,-.005,1.18),root)
head.scale=(.92,.95,.86)
outer=[(0,-.28),(.17,-.265),(.31,-.20),(.385,-.08),(.405,.05),(.374,.19),(.285,.30),(.14,.354),(0,.365),(-.14,.354),(-.285,.30),(-.374,.19),(-.405,.05),(-.385,-.08),(-.31,-.20),(-.17,-.265)]
points=list(outer);edges=[]
for i in range(len(outer)):edges.append((i,(i+1)%len(outer)))
patch_outline=[(.068,.134),(.24,.21),(.298,.15),(.32,.025),(.245,-.055),(.13,-.03),(.073,.035)]
eye_outline=[(.087,.045),(.108,.105),(.24,.145),(.282,.083),(.231,.018),(.142,.006)]
for s in [-1,1]:
 start=len(points);points += [(s*x,z) for x,z in patch_outline]
 for i in range(len(patch_outline)):edges.append((start+i,start+(i+1)%len(patch_outline)))
 eye=[(.087,.045),(.108,.105),(.24,.145),(.282,.083),(.231,.018),(.142,.006)]
 start=len(points);points += [(s*x,z) for x,z in eye]
 for i in range(len(eye)):edges.append((start+i,start+(i+1)%len(eye)))
 points += [(s*.16,.27),(s*.285,.18),(s*.075,.14),(s*.21,-.12),(s*.12,-.18),(s*.075,-.055),(s*.31,-.025)]
points += [(0,.285),(0,.145),(0,.02),(0,-.045),(0,-.14),(0,-.223)]
coords,ed,faces,_,_,_=delaunay_2d_cdt([Vector(p) for p in points],edges,[tuple(range(len(outer)))],1,1e-6)
def depth(x,z):
 q=(x/.425)**2+((z-.045)/.39)**2
 d=.025-.294*math.sqrt(max(0,1-q))
 d-=.066*math.exp(-((x/.24)**4)-((z+.125)/.11)**4)
 d-=.030*math.exp(-((abs(x)-.185)/.12)**2-((z-.135)/.06)**2)
 if abs(x)<.02 and abs(z+.045)<.01:d-=.045
 return d
vs=[(p.x,depth(p.x,p.y),p.y) for p in coords];fs=list(faces)
def inside(x,z,polygon):
 hit=False;j=len(polygon)-1
 for i,(xx,zz) in enumerate(polygon):
  ox,oz=polygon[j]
  if (zz>z)!=(oz>z) and x<(ox-xx)*(z-zz)/(oz-zz)+xx:hit=not hit
  j=i
 return hit
regions=[]
for f in fs:
 x=sum(vs[i][0] for i in f)/len(f);z=sum(vs[i][2] for i in f)/len(f);x=abs(x)
 regions.append('light' if inside(x,z,eye_outline) else ('black' if inside(x,z,patch_outline) else 'face'))
boundary=[]
for p in outer:boundary.append(min(range(len(coords)),key=lambda i:(coords[i]-Vector(p)).length_squared))
last=boundary
for y,scale in [(.14,1.0),(.265,.67)]:
 row=[]
 for x,z in outer:row.append(len(vs));vs.append((x*scale,y,(z-.04)*scale+.04))
 for i in range(len(row)):
  a=last[i];b=last[(i+1)%len(row)];c=row[(i+1)%len(row)];d=row[i];fs.append((a,b,c,d));regions.append('back')
 last=row
center=len(vs);vs.append((0,.305,.045))
for i in range(len(last)):fs.append((last[i],last[(i+1)%len(last)],center));regions.append('back')
head_mesh=make('SculptedHead',vs,fs,head,regions=regions)
from mathutils.bvhtree import BVHTree
bvh=BVHTree.FromPolygons([v.co.copy() for v in head_mesh.data.vertices],[list(f.vertices) for f in head_mesh.data.polygons])
def surface_y(x,z):
 hit,_,_,_=bvh.ray_cast(Vector((x,-2,z)),Vector((0,1,0)))
 return hit.y if hit is not None else depth(x,z)
for s in [-1,1]:
 pv=[]
 for i in range(8):
  a=i*math.tau/8;x=s*(.181+math.cos(a)*.042);z=.074+math.sin(a)*.058;pv.append((x,surface_y(x,z)-.006,z))
 pv.append((s*.181,surface_y(s*.181,.074)-.009,.074))
 make('Pupil',pv,[(8,i,(i+1)%8) for i in range(8)],head,'pupil')
 gp=[]
 for x,z in [(s*.156,.083),(s*.172,.083),(s*.172,.105),(s*.156,.105)]:gp.append((x,surface_y(x,z)-.012,z))
 make('EyeCatchlight',gp,[(0,1,2),(0,2,3)],head,'light')
nose_points=[(-.062,-.036),(-.035,-.026),(.035,-.026),(.062,-.036),(.036,-.077),(0,-.098),(-.039,-.075)]
nv=[(x,surface_y(x,z)-.007,z) for x,z in nose_points]
nv.append((0,surface_y(0,-.05)-.036,-.05))
make('Nose',nv,[(7,i,(i+1)%7) for i in range(7)],head,'black')
line=[(-.098,-.151),(-.035,-.171),(.045,-.163),(.12,-.135),(.136,-.146)]
curve=[]
for j in range(len(line)-1):
 for k in range(4):
  t=k/4;curve.append((line[j][0]*(1-t)+line[j+1][0]*t,line[j][1]*(1-t)+line[j+1][1]*t))
curve.append(line[-1]);mv=[]
for x,z in curve:
 for zz in [z+.0025,z-.0025]:mv.append((x,surface_y(x,zz)-.005,zz))
make('Smirk',mv,[(i*2,i*2+1,i*2+3,i*2+2) for i in range(len(curve)-1)],head,'seam')
# Ears are beveled polygon volumes, with clear black silhouettes.
for s in [-1,1]:
 outline=[(-.12,-.035),(-.105,.075),(-.04,.13),(.075,.12),(.13,.035),(.105,-.09),(.035,-.12),(-.08,-.105)]
 ear=empty('EarPivot',(s*.318,.045,.302),head);ear.rotation_euler[1]=s*.22
 ev=[(s*x,-.075,z) for x,z in outline]+[(s*x,.065,z) for x,z in outline]+[(0,-.10,0)]
 ef=[(16,i,(i+1)%8) for i in range(8)]+[(i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8)]+[tuple(reversed(range(8,16)))]
 make('Ear',ev,ef,ear,regions=['dark' if i in [0,1,2] else 'black' for i in range(len(ef))])
 for k,(z,tipx,tipz) in enumerate([(.015,.495,-.005),(-.10,.47,-.165),(-.18,.36,-.25)]):
  x=.35 if k<2 else .275
  wedge('CheekFur',[(s*x,-.075,z+.055),(s*(x-.025),-.11,z-.035),(s*tipx,.065,tipz),(s*(x+.01),.15,z-.025)],head,'pink' if k<2 else 'lilac')
for i,(x,y,z) in enumerate([(-.11,.045,.32),(.015,.10,.34),(.12,.155,.30)]):
 wedge('CrownFur',[(x-.06,y-.065,z-.018),(x+.06,y-.05,z-.025),(x+.04,y+.075,z+.10),(x-.005,y+.13,z-.035)],head,'cream' if i==0 else 'warm')
# A fist uses broad knuckle planes and a folded thumb, not a sphere.
for s,label in [(-1,'L'),(1,'R')]:
 arm=empty('Arm'+label,(s*.24,.005,.925),root)
 tube('UpperSleeve',[(0,0,0,.12,.12),(s*.055,0,-.14,.115,.12),(s*.10,-.03,-.24,.095,.10)],arm,'jacket',6)
 tube('LowerSleeve',[(s*.10,-.03,-.21,.096,.10),(s*.135,-.07,-.31,.085,.09)],arm,'black',6)
 palm=empty('Hand',(s*.14,-.075,-.36),arm)
 outline=[(-.085,-.045),(-.075,.065),(-.02,.105),(.075,.08),(.10,-.025),(.04,-.10)]
 hv=[(s*x,-.085,z) for x,z in outline]+[(s*x,.07,z) for x,z in outline]
 hf=[tuple(reversed(range(6))),tuple(range(6,12))]+[(i,(i+1)%6,(i+1)%6+6,i+6) for i in range(6)]
 make('ClosedFist',hv,hf,palm,'black')
 wedge('Thumb',[(s*-.045,-.08,.055),(s*-.10,-.05,.015),(s*-.055,-.12,-.045),(s*-.025,-.07,-.02)],palm,'dark')
 leg=empty('Leg'+label,(s*.133,0,.48),root)
 tube('Shorts',[(0,0,.028,.14,.135),(s*.01,0,-.09,.147,.14),(s*.018,0,-.18,.125,.13)],leg,'shorts',6)
 tube('Shin',[(s*.02,.005,-.18,.076,.077),(s*.035,-.01,-.34,.08,.08)],leg,'black',5)
 # Low paws with a broad cream toe: no white spikes or platform-shoe bumper.
 fv=[(-.13,-.23,-.455),(.13,-.23,-.455),(.145,-.045,-.48),(.09,.095,-.46),(-.09,.095,-.46),(-.145,-.045,-.48),(-.11,-.21,-.375),(.11,-.21,-.375),(.11,-.045,-.36),(.075,.075,-.35),(-.075,.075,-.35),(-.11,-.045,-.36)]
 ff=[tuple(reversed(range(6))),tuple(range(6,12))]+[(i,(i+1)%6,(i+1)%6+6,i+6) for i in range(6)]
 regions=['sole','black']+['paw' if i in [0,1,5] else 'black' for i in range(6)]
 foot=make('PandaPaw',fv,ff,leg,regions=regions);foot.location.x=s*.035
# Bake a restrained per-vertex diffuse term into the lightweight preview material.
key=Vector((-.38,-.72,.57)).normalized()
for ob in PARTS:
 bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free();ob.data.update()
 for p in ob.data.polygons:p.use_smooth=True
 color=ob.data.color_attributes.new(name='PS1Light',type='BYTE_COLOR',domain='CORNER')
 normalmat=ob.matrix_world.to_3x3().inverted().transposed()
 for li,l in enumerate(ob.data.loops):
  n=(normalmat@ob.data.vertices[l.vertex_index].normal).normalized();shade=.52+.48*max(0,n.dot(key))
  color.data[li].color=(shade,shade*.98,shade*.99,1)
# Rest-pose asset, with the same gameplay pivot names as the original project.
OUT=ROOT/'assets/models/pam_ps1_estudo.glb'
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=str(OUT),export_format='GLB',export_yup=True,export_animations=False,export_vertex_color='ACTIVE',export_all_vertex_colors=False)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets/source/pam_ps1_estudo.blend'))
print('PS1_MODEL_EXPORTED',OUT)
# Emit the spec-defined unlit material explicitly: glTF's vertex COLOR_0 then
# multiplies the atlas, preserving the original low-cost Gouraud-style preview.
import struct
blob=OUT.read_bytes();chunks=[];offset=12
while offset<len(blob):
 length,kind=struct.unpack_from('<II',blob,offset);chunks.append((kind,blob[offset+8:offset+8+length]));offset+=8+length
asset=json.loads(next(data for kind,data in chunks if kind==0x4E4F534A))
m=asset['materials'][0]
m.pop('emissiveFactor',None);m.pop('emissiveTexture',None)
m['pbrMetallicRoughness']={'baseColorFactor':[1,1,1,1],'baseColorTexture':{'index':0},'metallicFactor':0,'roughnessFactor':1}
m['extensions']={'KHR_materials_unlit':{}}
asset['extensionsUsed']=sorted(set(asset.get('extensionsUsed',[])+['KHR_materials_unlit']))
for sampler in asset.get('samplers',[]):sampler['magFilter']=9728;sampler['minFilter']=9728
payload=json.dumps(asset,separators=(',',':')).encode();payload+=b' '*((-len(payload))%4)
packed=[(0x4E4F534A,payload)]+[(k,d) for k,d in chunks if k!=0x4E4F534A]
body=b''.join(struct.pack('<II',len(d),k)+d for k,d in packed)
OUT.write_bytes(struct.pack('<III',0x46546C67,2,len(body)+12)+body)
triangles=sum(asset['accessors'][p['indices']]['count']//3 for mesh in asset['meshes'] for p in mesh['primitives'])
(ROOT/'assets/source/pam_ps1_metadata.json').write_text(json.dumps({'triangles':triangles,'materials':len(asset['materials']),'atlas':[128,128],'commercial_models_used':False,'runtime_format':'glTF 2.0','evidence':'Design budget; no claim of matching Crash binary/model measurements.'},indent=2))
print('PS1_METADATA',triangles,'triangles, 1 material, 128 x 128 atlas')
