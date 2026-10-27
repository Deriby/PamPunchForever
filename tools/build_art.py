"""Original authored low-poly assets. Run with Blender 4.3+: blender -b -P tools/build_art.py"""
import bpy, math, random, os
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
random.seed(29)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
M={}
def mat(name, color):
 color=tuple(v**1.45 for v in color)
 m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
 bs=m.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(*color,1); bs.inputs['Roughness'].default_value=.94
 M[name]=m; return m
for n,c in {'cream':(.84,.72,.55),'ivory':(.96,.87,.69),'ink':(.045,.036,.055),'jacket':(.07,.075,.095),'edge':(.15,.17,.18),'red':(.56,.055,.045),'gold':(.92,.52,.14),'white':(1,.96,.85),'pupil':(.015,.012,.02),'green':(.29,.37,.10),'olive':(.46,.49,.16),'shell':(.18,.12,.08),'shelllight':(.33,.24,.12),'hat':(.58,.32,.065),'hatlight':(.82,.52,.14),'beard':(.75,.72,.55),'bark':(.20,.105,.065),'barklight':(.33,.19,.10),'leaf':(.12,.32,.16),'leaflight':(.32,.48,.13),'leafdark':(.055,.19,.12),'stone':(.27,.34,.31),'moss':(.27,.38,.16),'band':(.45,.18,.10),'enemy':(.20,.24,.27)}.items(): mat(n,c)
def mesh(name, verts, faces, material, parent=None):
 me=bpy.data.meshes.new(name); me.from_pydata(verts,[],faces); me.update(); o=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(o); o.data.materials.append(M[material]); o.parent=parent; return o
def ico(name,loc,scale,material,sub=1,parent=None):
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub,radius=1,location=loc); o=bpy.context.object; o.name=name; o.scale=scale; o.data.materials.append(M[material]); o.parent=parent; return o
def block(name,loc,scale,material,parent=None,bevel=.03):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=bpy.context.object; o.name=name; o.scale=scale; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if bevel:
  mod=o.modifiers.new('Hand-cut edges','BEVEL'); mod.width=bevel; mod.segments=1; bpy.context.view_layer.objects.active=o; bpy.ops.object.modifier_apply(modifier=mod.name)
 o.data.materials.append(M[material]); o.parent=parent; return o
def empty(name,loc=(0,0,0),parent=None):
 o=bpy.data.objects.new(name,None); bpy.context.collection.objects.link(o); o.location=loc; o.parent=parent; return o
def rings(name,points,radii,material,sides=7,parent=None):
 vs=[]
 for j,p in enumerate(points):
  for i in range(sides):
   a=i*math.tau/sides; vs.append((p[0]+math.cos(a)*radii[j],p[1]+math.sin(a)*radii[j],p[2]))
 fs=[tuple(reversed(range(sides)))]
 for j in range(len(points)-1):
  for i in range(sides):
   a=j*sides+i;b=j*sides+(i+1)%sides;fs.append((a,b,b+sides,a+sides))
 fs.append(tuple(range((len(points)-1)*sides,len(points)*sides)))
 return mesh(name,vs,fs,material,parent)
def save(name):
 if name not in ['pam','jaburanga','guardian','assassin']:
  bpy.ops.object.select_all(action='DESELECT')
  objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
  for o in objects:
   transform=o.matrix_world.copy();o.parent=None;o.matrix_world=transform;o.select_set(True)
  bpy.context.view_layer.objects.active=objects[0]
  bpy.ops.object.join()
  for o in list(bpy.context.scene.objects):
   if o.type=='EMPTY':bpy.data.objects.remove(o,do_unlink=True)
 bpy.ops.object.select_all(action='SELECT')
 bpy.ops.export_scene.gltf(filepath=ROOT+'/assets/models/'+name+'.glb',export_format='GLB',export_yup=True,export_animations=False)
 bpy.ops.object.delete(use_global=False)
# Concept-led Pam generator is shared with the actual-model preview.
# Keep the previous in-game Pam by default. Its earlier approval was revoked;
# the new PS1 study is generated separately by tools/ps1/model.py.
if os.environ.get('PAM_REBUILD_APPROVED_PAM')=='1':
 exec(compile(open(os.path.join(os.path.dirname(__file__), 'build_pam.py')).read(), 'build_pam.py', 'exec'), globals())
 save('pam')
exec(compile(open(os.path.join(os.path.dirname(__file__), 'build_world_art.py')).read(), 'build_world_art.py', 'exec'), globals())
