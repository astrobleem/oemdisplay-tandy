"""Read numeric FON contracts without extracting or rendering private glyphs."""
import argparse
import hashlib
import json
import struct
from pathlib import Path


def word(data, at):
    return struct.unpack_from('<H', data, at)[0]


def dword(data, at):
    return struct.unpack_from('<I', data, at)[0]


def cstring(data, at):
    end = data.index(0, at)
    return data[at:end].decode('ascii')


def resources(data):
    if data[:2] != b'MZ':
        raise ValueError('Missing MZ header')
    ne = dword(data, 60)
    if data[ne:ne + 2] != b'NE':
        raise ValueError('Missing NE header')
    p = ne + word(data, ne + 36)
    shift = word(data, p)
    p += 2
    result = []
    while word(data, p):
        kind, count = struct.unpack_from('<HH', data, p)
        p += 8
        for _ in range(count):
            off, size, flags, rid = struct.unpack_from('<HHHH', data, p)
            off, size = off << shift, size << shift
            if off + size > len(data):
                raise ValueError('Resource outside file')
            result.append((kind, rid, flags, off, size))
            p += 12
    resident = ne + word(data, ne + 38)
    module = data[resident + 1:resident + 1 + data[resident]].decode('ascii')
    return module, result


def fontinfo(data):
    version = word(data, 0)
    if version != 0x200:
        raise ValueError('Expected real-mode 2.x FNT')
    fields = {'version': version, 'size': dword(data, 2),
              'type': word(data, 66), 'points': word(data, 68),
              'vert_res': word(data, 70), 'horiz_res': word(data, 72),
              'ascent': word(data, 74), 'internal': word(data, 76),
              'external': word(data, 78), 'italic': data[80],
              'underline': data[81], 'strikeout': data[82],
              'weight': word(data, 83), 'charset': data[85],
              'pix_width': word(data, 86), 'height': word(data, 88),
              'pitch_family': data[90], 'avg_width': word(data, 91),
              'max_width': word(data, 93), 'first': data[95],
              'last': data[96], 'default': data[97], 'break': data[98],
              'width_bytes': word(data, 99), 'face': cstring(data, dword(data, 105))}
    widths = [word(data, 118 + 4 * i)
              for i in range(fields['last'] - fields['first'] + 1)]
    fields['widths'] = widths
    return fields


def inspect(path):
    data = path.read_bytes()
    module, entries = resources(data)
    return {'filename': path.name.upper(), 'sha256': hashlib.sha256(data).hexdigest(),
            'size': len(data), 'module': module,
            'resources': [{'type': kind, 'id': rid & 0x7fff, 'flags': flags,
                           'size': size,
                           **({'font': fontinfo(data[off:off + size])}
                              if kind == 0x8008 else {})}
                          for kind, rid, flags, off, size in entries]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--private', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    names = ('CGASYS', 'CGAFIX', 'CGAOEM', 'EGASYS', 'EGAFIX', 'EGAOEM')
    result = [inspect(args.private / (name + '.FON')) for name in names]
    args.out.write_bytes((json.dumps(result, indent=2) + '\r\n').replace(
        '\r\n', '\n').replace('\n', '\r\n').encode('ascii'))
    for item in result:
        print(item['filename'], item['module'], item['sha256'])
        for r in item['resources']:
            if 'font' in r:
                print(r['id'], {k: v for k, v in r['font'].items() if k != 'widths'})


if __name__ == '__main__':
    main()
