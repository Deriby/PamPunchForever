"""Remove only the connected tail from the user-supplied original GLB.

Retain the original PBR images, UVs and custom corner normals outside the repair.
The rear patch samples the existing shorts/jacket material; no replacement art.
"""
import bpy
import bmesh
import math
import json
import hashlib
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.geometry import delaunay_2d_cdt, barycentric_transform, closest_point_on_tri
from mathutils.kdtree import KDTree

ROOT = Path(__file__).resolve().parents[2]
original = ROOT / 'assets/source/pam_usuario_original.glb'
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(original))
body = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
transform = body.matrix_world.copy()
normal_matrix = transform.to_3x3().inverted().transposed()
original_normals = [(normal_matrix @ n.vector).normalized() for n in body.data.corner_normals]
body.data.transform(transform)
body.matrix_world = Matrix.Identity(4)
body.name = 'Pam_Usuario_Sem_Rabo'
positions = {tuple(round(v, 6) for v in p.co) for p in body.data.vertices if p.co.z > .40}
bm = bmesh.new()
bm.from_mesh(body.data)
normal_layer = bm.loops.layers.float_vector.new('PreservedNormal')
uv = bm.loops.layers.uv.active
assert uv is not None
for face in bm.faces:
    start = body.data.polygons[face.index].loop_start
    for i, loop in enumerate(face.loops):
        loop[normal_layer] = original_normals[start+i]

# Weld position duplicates only. UVs and custom normals remain per corner.
bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=.000001)
assert not any(e.is_boundary for e in bm.edges), 'Input needs inspection: non-UV boundary found'
before_faces = len(bm.faces)

def rear(z, x):
    samples = [(.23, .115), (.25, .120), (.285, .125), (.305, .126),
               (.315, .162), (.325, .192), (.340, .200)]
    for (za, ya), (zb, yb) in zip(samples, samples[1:]):
        if za <= z <= zb:
            return ya+(yb-ya)*(z-za)/(zb-za)-2*x*x
    return .20

remove = []
for face in bm.faces:
    c = face.calc_center_median()
    if abs(c.x) < .075 and .235 < c.z < .334 and c.y > rear(c.z, c.x):
        remove.append(face)
assert 100 < len(remove) < 4000, len(remove)
candidate = set(remove)
seed = max(remove, key=lambda f: f.calc_center_median().y)
connected, stack = set(), [seed]
while stack:
    face = stack.pop()
    if face in connected:
        continue
    connected.add(face)
    stack.extend(other for edge in face.edges for other in edge.link_faces
                 if other in candidate and other not in connected)
remove = list(connected)
bmesh.ops.delete(bm, geom=remove, context='FACES')
boundary = [e for e in bm.edges if e.is_boundary]
assert boundary
adj = {}
for edge in boundary:
    for vertex in edge.verts:
        adj.setdefault(vertex, []).append(edge)
assert all(len(edges) == 2 for edges in adj.values()), 'Repair boundary must be a closed loop'
loop = []
first = next(iter(adj))
current, previous = first, None
while True:
    loop.append(current)
    edge = next(e for e in adj[current] if e != previous)
    nxt = edge.other_vert(current)
    if nxt == first:
        break
    previous, current = edge, nxt
if len(loop) != len(adj):
    print('REPAIR_BOUNDARY',len(loop),'of',len(adj), 'first bounds', [(min(v.co[i] for v in loop),max(v.co[i] for v in loop)) for i in range(3)])
    other = [v for v in adj if v not in loop]
    print('OTHER_BOUNDARY',len(other),[(min(v.co[i] for v in other),max(v.co[i] for v in other)) for i in range(3)])
assert len(loop) == len(adj), 'Unexpected second hole: inspect instead of filling unrelated geometry'

# Existing rear fabric references for UV sampling. Exclude tail geometry entirely.
references = [f for f in bm.faces if .045 < abs(f.calc_center_median().x) < .15
              and .22 < f.calc_center_median().z < .35 and f.calc_center_median().y > .07]
tree = KDTree(len(references))
for i, f in enumerate(references):
    tree.insert(f.calc_center_median(), i)
tree.balance()

def sample_uv(point):
    x = (.07+abs(point.x)*.2)*(1 if point.x >= 0 else -1)
    reference = Vector((x, rear(point.z, x), point.z))
    _, index, _ = tree.find(reference)
    face = references[index]
    points = [l.vert.co for l in face.loops]
    texcoords = [Vector((*l[uv].uv, 0)) for l in face.loops]
    reference = closest_point_on_tri(reference, *points)
    mapped = barycentric_transform(reference, *points, *texcoords)
    return mapped.xy

polygon = [(v.co.x, v.co.z) for v in loop]
def inside(x, z):
    result, previous = False, polygon[-1]
    for point in polygon:
        if (point[1] > z) != (previous[1] > z) and x < (previous[0]-point[0])*(z-point[1])/(previous[1]-point[1])+point[0]:
            result = not result
        previous = point
    return result

points = list(polygon)
xlo, xhi = min(x for x, z in polygon), max(x for x, z in polygon)
zlo, zhi = min(z for x, z in polygon), max(z for x, z in polygon)
x = xlo+.004
while x < xhi-.003:
    z = zlo+.004
    while z < zhi-.003:
        if inside(x, z):
            points.append((x, z))
        z += .004
    x += .004
edges = [(i, (i+1)%len(polygon)) for i in range(len(polygon))]
coords, _, faces, _, _, _ = delaunay_2d_cdt([Vector(p) for p in points], edges,
    [tuple(range(len(polygon)))], 1, .00000001)
mapped_vertices = []
for point in coords:
    match = next((v for v in loop if abs(v.co.x-point.x) < .0000001 and abs(v.co.z-point.y) < .0000001), None)
    mapped_vertices.append(match or bm.verts.new((point.x, rear(point.y, point.x), point.y)))
patch_faces = []
for face in faces:
    verts = [mapped_vertices[i] for i in face]
    item = bm.faces.new(verts)
    item.normal_update()
    if item.normal.y < 0:
        item.normal_flip()
    center = item.calc_center_median()
    fabric = sample_uv(center)
    for corner in item.loops:
        # Keep each repair triangle within one existing fabric UV chart. Crossing
        # unrelated atlas islands would draw white tail/sleeve texels on the back.
        delta = corner.vert.co-center
        corner[uv].uv = fabric+Vector((delta.x, delta.z))*.025
        corner[normal_layer] = item.normal
    patch_faces.append(item)
bm.normal_update()
assert not any(e.is_boundary for e in bm.edges), 'Rear repair must not leave a hole'
assert all(e.is_manifold for e in bm.edges), 'Rear repair must remain manifold'
after = {tuple(round(v, 6) for v in p.co) for p in bm.verts if p.co.z > .40}
assert positions == after, 'Head/upper body positions changed unexpectedly'
tail_region = [v.co.y for v in bm.verts if abs(v.co.x) < .075 and .235 < v.co.z < .334]
assert max(tail_region) < .205, max(tail_region)
bm.to_mesh(body.data)
bm.free()
body.data.update()
custom = body.data.attributes['PreservedNormal']
normals = [item.vector.normalized() for item in custom.data]
body.data.normals_split_custom_set(normals)
body.data.attributes.remove(custom)
for polygon in body.data.polygons:
    polygon.use_smooth = True
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'assets/source/pam_usuario_sem_rabo.blend'), compress=True)
bpy.ops.export_scene.gltf(filepath=str(ROOT / 'assets/models/pam_usuario_sem_rabo.glb'),
    export_format='GLB', export_yup=True, export_animations=False)
metadata = {'original_sha256': hashlib.sha256(original.read_bytes()).hexdigest(),
    'original_faces': before_faces, 'tail_faces_removed': len(remove),
    'repair_faces': len(patch_faces), 'result_triangles': len(body.data.polygons),
    'boundary_edges': 0, 'manifold': True, 'upper_body_positions_preserved': True,
    'original_pbr_images_preserved': True, 'repair': 'Localized rear closure with existing fabric UV samples'}
(ROOT / 'assets/source/pam_usuario_edicao.json').write_text(json.dumps(metadata, indent=2))
print('PAM_USER_TAIL_REMOVED_OK', json.dumps(metadata))
