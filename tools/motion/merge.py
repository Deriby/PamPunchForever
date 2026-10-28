"""Replace animation streams while keeping the distributed skin/art bytes intact."""
import copy
import json
import struct
from pathlib import Path


def read(path):
    blob = Path(path).read_bytes()
    length,kind = struct.unpack_from('<II',blob,12)
    assert kind == 0x4e4f534a
    doc = json.loads(blob[20:20+length])
    start = 20+length
    length,kind = struct.unpack_from('<II',blob,start)
    assert kind == 0x004e4942
    return doc,bytearray(blob[start+8:start+8+length])


def merge(target, animated, names):
    old, binary = read(target)
    new, data = read(animated)
    lookup = {}
    for index,node in enumerate(old['nodes']):
        name = node.get('name')
        assert name not in lookup,('ambiguous target node',name)
        lookup[name] = index
    accessors,views = {},{}

    def accessor(index):
        if index in accessors: return accessors[index]
        item = copy.deepcopy(new['accessors'][index])
        original_view = item['bufferView']
        if original_view not in views:
            view = copy.deepcopy(new['bufferViews'][original_view])
            begin = view.get('byteOffset',0)
            binary.extend(b'\0'*((-len(binary))%4))
            view['buffer'],view['byteOffset'] = 0,len(binary)
            binary.extend(data[begin:begin+view['byteLength']])
            views[original_view] = len(old['bufferViews'])
            old['bufferViews'].append(view)
        item['bufferView'] = views[original_view]
        accessors[index] = len(old['accessors'])
        old['accessors'].append(item)
        return accessors[index]

    replacements = []
    for animation in new['animations']:
        if animation['name'] not in names: continue
        animation = copy.deepcopy(animation)
        for sampler in animation['samplers']:
            for key in ['input','output']: sampler[key] = accessor(sampler[key])
        for channel in animation['channels']:
            name = new['nodes'][channel['target']['node']]['name']
            assert name in lookup,('missing target bone',name)
            channel['target']['node'] = lookup[name]
        replacements.append(animation)
    assert {a['name'] for a in replacements} == set(names)
    old['animations'] = [a for a in old.get('animations',[]) if a['name'] not in names]+replacements
    binary.extend(b'\0'*((-len(binary))%4))
    old['buffers'][0]['byteLength'] = len(binary)
    payload = json.dumps(old,separators=(',',':')).encode()
    payload += b' '*((-len(payload))%4)
    chunks = struct.pack('<II',len(payload),0x4e4f534a)+payload+struct.pack('<II',len(binary),0x004e4942)+binary
    Path(target).write_bytes(struct.pack('<III',0x46546c67,2,len(chunks)+12)+chunks)
