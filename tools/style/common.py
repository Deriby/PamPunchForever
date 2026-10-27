"""Shared low-poly modeling vocabulary: shaped volumes, painted UVs and coherent materials."""
import bpy,bmesh,math,random,os
from mathutils import Vector
from pathlib import Path
ROOT=PAM_ART_ROOT
random.seed(73)
M={}
def linear(c):return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4
def material(name,h,texture=None,emission=0):
 c=tuple(linear(int(h[i:i+2],16)/255) for i in [0,2,4]);m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*c,1)
 bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*c,1);bs.inputs['Roughness'].default_value=.89;bs.inputs['Specular IOR Level'].default_value=.18
 if texture:
  tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(ROOT/'assets/textures/style'/f'{texture}.png'),check_existing=True);tex.image.pack();tex.interpolation='Linear';m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
 if emission:
  bs.inputs['Emission Color'].default_value=(*c,1);bs.inputs['Emission Strength'].default_value=emission
 M[name]=m;return m
for n,h,t in [('bark','563720','bark'),('wood','8d603b','wood'),('wood_dark','533924','wood_dark'),('leaf','37743b','leaf'),('leaf_light','708e3f','leaf_light'),('leaf_dark','285b38','leaf_dark'),('blade','4a7d38','blade'),('stone','77816c','stone'),('moss','687e41','moss'),('straw','be8b3c','straw'),('cloth','353b30','cloth'),('robe','c6b193','robe'),('redwood','982d27','redwood'),('shell','67492f','shell'),('crate_stamp','8d603b','crate_stamp'),('tnt_stamp','982d27','tnt_stamp')]:material(n,h,t)
for n,h in {'ink':'1b1b24','charcoal':'292831','fold':'38313a','cream':'e4d4b3','beard':'e3dbc4','beard_shade':'bdb5a4','skin':'8e9850','skinshade':'717c3f','skinlight':'acaf67','red':'8e2925','redlight':'b24230','gold':'c49a58','teal':'456c65','ochre':'a37c42','ivory':'dfd2b6','seam':'625345','bronze':'9e7544','jade':'88b78d','orange':'dc9a3d'}.items():material(n,h)
material('crystal','9dc6a1',emission=.25)

def clear():
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def empty(name,loc=(0,0,0),parent=None):
 ob=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(ob);ob.location=loc;ob.parent=parent;return ob

def uv_project(ob,mode='box',scale=1):
 uv=ob.data.uv_layers.new(name='Paint') if not ob.data.uv_layers else ob.data.uv_layers[0]
 for p in ob.data.polygons:
  c=p.center;n=p.normal
  for li in p.loop_indices:
   v=ob.data.vertices[ob.data.loops[li].vertex_index].co
   if mode=='face':u=.5+v.x*scale;vv=.5+v.z*scale
   elif abs(n.z)>.6:u=v.x*scale;vv=v.y*scale
   elif abs(n.y)>.5:u=v.x*scale;vv=v.z*scale
   else:u=v.y*scale;vv=v.z*scale
   uv.data[li].uv=(u,vv)
 return ob

def mesh(name,v,f,mat,parent=None):
 me=bpy.data.meshes.new(name);me.from_pydata(v,[],f);me.update();ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);ob.parent=parent;ob.data.materials.append(M[mat]);uv_project(ob)
 return ob

def block(name,loc,size,mat,parent=None,bevel=.025):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);ob=bpy.context.object;ob.name=name;ob.scale=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if bevel:
  mod=ob.modifiers.new('Worn edges','BEVEL');mod.width=bevel;mod.segments=1;bpy.ops.object.modifier_apply(modifier=mod.name)
 ob.data.materials.append(M[mat]);ob.parent=parent;return ob

def ico(name,loc,size,mat,parent=None,sub=2):
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub,radius=1,location=loc);ob=bpy.context.object;ob.name=name;ob.scale=size;ob.data.materials.append(M[mat]);ob.parent=parent;uv_project(ob);return ob

def loft(name,rows,mat,parent=None,sides=12):
 v=[]
 for z,rx,ry,cy in rows:
  for i in range(sides):
   a=math.tau*i/sides-math.pi/2;v.append((rx*math.cos(a),cy+ry*math.sin(a),z))
 f=[tuple(reversed(range(sides)))]
 for j in range(len(rows)-1):
  for i in range(sides):
   a=j*sides+i;b=j*sides+(i+1)%sides;f.append((a,b,b+sides,a+sides))
 f.append(tuple(range((len(rows)-1)*sides,len(rows)*sides)))
 return mesh(name,v,f,mat,parent)

def tube(name,points,radii,mat,parent=None,sides=7):
 vs=[]
 for j,p in enumerate(points):
  tangent=Vector(points[min(j+1,len(points)-1)])-Vector(points[max(j-1,0)]);tangent.normalize();axis=tangent.cross(Vector((0,1,0)))
  if axis.length<.01:axis=tangent.cross(Vector((1,0,0)))
  axis.normalize();other=tangent.cross(axis).normalized()
  for i in range(sides):
   a=math.tau*i/sides;vs.append(tuple(Vector(p)+radii[j]*(axis*math.cos(a)+other*math.sin(a))))
 fs=[tuple(reversed(range(sides)))]
 for j in range(len(points)-1):
  for i in range(sides):
   a=j*sides+i;b=j*sides+(i+1)%sides;fs.append((a,b,b+sides,a+sides))
 fs.append(tuple(range((len(points)-1)*sides,len(points)*sides)))
 return mesh(name,vs,fs,mat,parent)

def panel(name,pts,mat,parent=None):return mesh(name,pts,[tuple(range(len(pts)))],mat,parent)

def face_material(key):
 material('face_'+key,'ffffff','face_'+key);return 'face_'+key

def face_uv(ob,rx,low,high):
 uv=ob.data.uv_layers[0]
 for p in ob.data.polygons:
  for li in p.loop_indices:
   v=ob.data.vertices[ob.data.loops[li].vertex_index].co;uv.data[li].uv=(.5+v.x/(2*rx),(v.z-low)/(high-low))

def save(name,rigged=False):
 for ob in bpy.context.scene.objects:
  if ob.type=='MESH':
   bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
   for p in ob.data.polygons:p.use_smooth=False
 if not rigged:
  bpy.ops.object.select_all(action='DESELECT');obs=[ob for ob in bpy.context.scene.objects if ob.type=='MESH']
  for ob in obs:
   matrix=ob.matrix_world.copy();ob.parent=None;ob.matrix_world=matrix;ob.select_set(True)
  bpy.context.view_layer.objects.active=obs[0];bpy.ops.object.join()
  # Remove unused duplicate material slots so the static batch remains inexpensive.
  ob=bpy.context.object
  for e in list(bpy.context.scene.objects):
   if e.type=='EMPTY':bpy.data.objects.remove(e,do_unlink=True)
 bpy.ops.object.select_all(action='SELECT')
 bpy.ops.export_scene.gltf(filepath=str(ROOT/'assets/models'/f'{name}.glb'),export_format='GLB',export_yup=True,export_animations=False)
 print('EXPORTED',name)
 clear()
