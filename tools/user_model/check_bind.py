"""Compare two exported GLBs: animation/weights may change, source art may not."""
import json
import struct
import sys
from pathlib import Path


def read(path):
    blob = Path(path).read_bytes()
    length, kind = struct.unpack_from('<II',blob,12)
    document = json.loads(blob[20:20+length])
    start = 20+length
    size, kind = struct.unpack_from('<II',blob,start)
    return document, blob[start+8:start+8+size]


def view(document, binary, index):
    item = document['bufferViews'][index]
    start = item.get('byteOffset',0)
    return binary[start:start+item['byteLength']]


def accessor(document, binary, index):
    return view(document,binary,document['accessors'][index]['bufferView'])


before, after = [read(path) for path in sys.argv[1:3]]
a, ab = before
b, bb = after
pa, pb = [doc['meshes'][0]['primitives'][0] for doc in [a,b]]
report = {}
for name in ['POSITION','NORMAL','TEXCOORD_0']:
    assert accessor(a,ab,pa['attributes'][name]) == accessor(b,bb,pb['attributes'][name]), name
    report[name+'_identical'] = True
assert accessor(a,ab,pa['indices']) == accessor(b,bb,pb['indices'])
assert accessor(a,ab,a['skins'][0]['inverseBindMatrices']) == accessor(b,bb,b['skins'][0]['inverseBindMatrices'])
report['indices_and_inverse_bind_matrices_identical'] = True
assert len(a['images']) == len(b['images'])
for ia, ib in zip(a['images'],b['images']):
    assert view(a,ab,ia['bufferView']) == view(b,bb,ib['bufferView'])
report['all_pbr_images_identical'] = True
print('PAM_USER_BIND_ART_PRESERVED',json.dumps(report))
