"""Independent GLB checks of normalized bind geometry and original PBR pixels."""
from pathlib import Path
import io
import hashlib
import json
import os
import struct
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(os.environ.get('PAM_NPC_REVIEW_OUTPUT',ROOT/'build/npc_review'))
OUT.mkdir(parents=True,exist_ok=True)
DTYPES = {5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}
WIDTH = {'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}


def read(path):
    blob = Path(path).read_bytes()
    size,kind = struct.unpack_from('<II',blob,12)
    doc = json.loads(blob[20:20+size])
    start = 20+size
    length,kind = struct.unpack_from('<II',blob,start)
    return doc,blob[start+8:start+8+length]


def accessor(doc,blob,index):
    a = doc['accessors'][index]
    view = doc['bufferViews'][a['bufferView']]
    dtype = np.dtype(DTYPES[a['componentType']])
    columns = WIDTH[a['type']]
    start = view.get('byteOffset',0)+a.get('byteOffset',0)
    return np.ndarray((a['count'],columns),dtype,buffer=blob,offset=start,
        strides=(view.get('byteStride',dtype.itemsize*columns),dtype.itemsize)).copy()


def matrix(node):
    if 'matrix' in node:
        return np.array(node['matrix']).reshape((4,4)).T
    x,y,z,w = node.get('rotation',[0,0,0,1])
    result = np.eye(4)
    result[:3,:3] = [[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                     [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                     [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]]
    result[:3,:3] = result[:3,:3]@np.diag(node.get('scale',[1,1,1]))
    result[:3,3] = node.get('translation',[0,0,0])
    return result


def mesh_world(doc):
    parents = {child:i for i,node in enumerate(doc['nodes']) for child in node.get('children',[])}
    index = next(i for i,n in enumerate(doc['nodes']) if 'mesh' in n)
    result = matrix(doc['nodes'][index])
    while index in parents:
        index = parents[index]
        result = matrix(doc['nodes'][index])@result
    return result


def corners(doc,blob):
    primitive = doc['meshes'][0]['primitives'][0]
    indices = accessor(doc,blob,primitive['indices']).ravel()
    point = accessor(doc,blob,primitive['attributes']['POSITION']).astype(float)
    transform = mesh_world(doc)
    point = point@transform[:3,:3].T+transform[:3,3]
    return point[indices]


def attribute_corners(doc,blob,name):
    primitive = doc['meshes'][0]['primitives'][0]
    indices = accessor(doc,blob,primitive['indices']).ravel()
    values = accessor(doc,blob,primitive['attributes'][name]).astype(float)
    if name == 'NORMAL':
        values = values@np.linalg.inv(mesh_world(doc)[:3,:3])
        values /= np.linalg.norm(values,axis=1)[:,None]
    return values[indices]


def texture(doc,blob,kind):
    material = doc['materials'][0]
    location = material if kind == 'normalTexture' else material['pbrMetallicRoughness']
    image = doc['images'][doc['textures'][location[kind]['index']]['source']]
    view = doc['bufferViews'][image['bufferView']]
    start = view.get('byteOffset',0)
    return np.asarray(Image.open(io.BytesIO(blob[start:start+view['byteLength']])).convert('RGB'))


reports = {}
for role in ['januri','inimigo','lar']:
    metadata = json.loads((ROOT/f'assets/source/npcs/{role}_rig_metadata.json').read_text())
    assert hashlib.sha256((ROOT/metadata['source']).read_bytes()).hexdigest() == metadata['source_sha256']
    a,ab = read(ROOT/metadata['source'])
    b,bb = read(ROOT/f'assets/models/npc_{role}_rig.glb')
    assert not a.get('skins') and len(b['skins']) == 1
    source = corners(a,ab)
    expected = (source-np.array((0,metadata['original_min_z'],0)))*metadata['uniform_scale']
    actual = corners(b,bb)
    assert expected.shape == actual.shape
    error = float(np.max(np.abs(expected-actual)))
    assert error < .00001,(role,'Bind geometry changed',error)
    uv_error = float(np.max(np.abs(attribute_corners(a,ab,'TEXCOORD_0')-attribute_corners(b,bb,'TEXCOORD_0'))))
    normal_error = float(np.max(np.abs(attribute_corners(a,ab,'NORMAL')-attribute_corners(b,bb,'NORMAL'))))
    assert uv_error < .00001 and normal_error < .00001,(role,uv_error,normal_error)
    checks = {}
    for key,channels in [('baseColorTexture',[0,1,2]),('normalTexture',[0,1,2]),('metallicRoughnessTexture',[1,2])]:
        before,after = texture(a,ab,key),texture(b,bb,key)
        assert before.shape == after.shape and np.array_equal(before[:,:,channels],after[:,:,channels]),(role,key)
        checks[key] = list(after.shape[:2])
    clips = [clip['name'] for clip in b['animations']]
    assert set(clips) == set(metadata['clips'])
    assert len(b['skins'][0]['joints']) == metadata['bones']
    reports[role] = {'geometry_max_error':error,'uv_max_error':uv_error,'normal_max_error':normal_error,'triangles':len(actual)//3,
        'bones':metadata['bones'],'clips':clips,'original_pbr_pixel_checks':checks}
    print('NPC_ORIGINAL_ART_VERIFIED',role,json.dumps(reports[role]),flush=True)
(OUT/'original-art-verification.json').write_text(json.dumps(reports,indent=2)+'\n')
