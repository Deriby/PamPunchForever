"""Restore the supplied float normals after Blender's custom-normal quantization.

This copies source art data into the edited file, not commercial motion/code.
Any vertex split copies all skin/UV attributes, preserving the actual rig.
"""
import json
import struct
import numpy as np

DTYPES = {5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}
WIDTH = {'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}


def read(path):
    blob = path.read_bytes()
    size,kind = struct.unpack_from('<II',blob,12)
    doc = json.loads(blob[20:20+size])
    start = 20+size
    size,kind = struct.unpack_from('<II',blob,start)
    return doc,bytearray(blob[start+8:start+8+size])


def array(doc,binary,index):
    a = doc['accessors'][index]
    view = doc['bufferViews'][a['bufferView']]
    dtype = np.dtype(DTYPES[a['componentType']])
    cols = WIDTH[a['type']]
    return np.ndarray((a['count'],cols),dtype,buffer=binary,
        offset=view.get('byteOffset',0)+a.get('byteOffset',0),
        strides=(view.get('byteStride',dtype.itemsize*cols),dtype.itemsize)).copy()


def node_matrix(node):
    if 'matrix' in node:
        return np.array(node['matrix']).reshape((4,4)).T
    x,y,z,w = node.get('rotation',[0,0,0,1])
    m = np.eye(4)
    m[:3,:3] = [[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]]
    m[:3,:3] = m[:3,:3]@np.diag(node.get('scale',[1,1,1]))
    m[:3,3] = node.get('translation',[0,0,0])
    return m


def mesh_matrix(doc):
    parents = {child:i for i,node in enumerate(doc['nodes']) for child in node.get('children',[])}
    i = next(i for i,node in enumerate(doc['nodes']) if 'mesh' in node)
    result = node_matrix(doc['nodes'][i])
    while i in parents:
        i = parents[i]
        result = node_matrix(doc['nodes'][i])@result
    return result


def restore(source,output):
    a,ab = read(source)
    b,bb = read(output)
    pa,pb = [doc['meshes'][0]['primitives'][0] for doc in [a,b]]
    ia,ib = array(a,ab,pa['indices']).ravel(),array(b,bb,pb['indices']).ravel()
    assert ia.size == ib.size and not pb.get('targets')
    original = array(a,ab,pa['attributes']['NORMAL']).astype(float)
    original = original@np.linalg.inv(mesh_matrix(a)[:3,:3])
    original /= np.linalg.norm(original,axis=1)[:,None]
    original = original@mesh_matrix(b)[:3,:3]
    original /= np.linalg.norm(original,axis=1)[:,None]
    # Rebuild the vertex mapping only where import/export merged source corners.
    lookup,old_vertices,normals,new_indices = {},[],[],[]
    for old,source_index in zip(ib,ia):
        key = (int(old),int(source_index))
        if key not in lookup:
            lookup[key] = len(old_vertices)
            old_vertices.append(int(old))
            normals.append(original[source_index])
        new_indices.append(lookup[key])
    selected = np.asarray(old_vertices,dtype=int)

    def append(values,kind,component,minimum=False):
        bb.extend(b'\x00'*((-len(bb))%4))
        offset = len(bb)
        raw = np.ascontiguousarray(values).tobytes()
        bb.extend(raw)
        view = len(b['bufferViews'])
        b['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':len(raw)})
        accessor = {'bufferView':view,'componentType':component,'count':len(values),'type':kind}
        if minimum:
            accessor['min'],accessor['max'] = values.min(axis=0).tolist(),values.max(axis=0).tolist()
        index = len(b['accessors'])
        b['accessors'].append(accessor)
        return index

    attributes = {}
    # Gather all old arrays before extending the bytearray (numpy reads copies).
    saved = {name:array(b,bb,index)[selected] for name,index in pb['attributes'].items() if name not in ['NORMAL','TANGENT']}
    for name,values in saved.items():
        old = b['accessors'][pb['attributes'][name]]
        attributes[name] = append(values,old['type'],old['componentType'],name == 'POSITION')
    attributes['NORMAL'] = append(np.asarray(normals,dtype='<f4'),'VEC3',5126)
    pb['attributes'] = attributes
    pb['indices'] = append(np.asarray(new_indices,dtype='<u4').reshape(-1,1),'SCALAR',5125)
    # Godot computes tangents from these original normals and original UVs.
    bb.extend(b'\x00'*((-len(bb))%4))
    b['buffers'][0]['byteLength'] = len(bb)
    payload = json.dumps(b,separators=(',',':')).encode()
    payload += b' '*((-len(payload))%4)
    data = struct.pack('<II',len(payload),0x4e4f534a)+payload+struct.pack('<II',len(bb),0x004e4942)+bb
    output.write_bytes(struct.pack('<III',0x46546c67,2,len(data)+12)+data)
    return {'original_float_normals_restored':True,'skin_attributes_preserved':True,'export_vertices':len(selected)}


if __name__ == '__main__':
    import sys
    from pathlib import Path
    print(restore(Path(sys.argv[1]),Path(sys.argv[2])))
